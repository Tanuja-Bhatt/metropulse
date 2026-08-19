from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor


# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = (
    PROJECT_ROOT
    / "data"
    / "metropulse.duckdb"
)


# =============================================================================
# DATABASE
# =============================================================================

def connect_database():

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"DuckDB database not found: {DB_PATH}"
        )

    return duckdb.connect(
        str(DB_PATH),
        read_only=True,
    )


def load_data(con):

    df = con.execute("""
        SELECT
            pickup_hour,
            taxi_trip_count,
            temperature_2m,
            relative_humidity_2m,
            precipitation,
            rain,
            wind_speed_10m,
            cloud_cover,
            subway_ridership,
            subway_transfers,
            hour_of_day,
            is_weekend,
            month_start,
            EXTRACT(DOW FROM pickup_hour) AS day_of_week
        FROM marts.hourly_mobility_summary
        ORDER BY pickup_hour
    """).df()

    if df.empty:
        raise RuntimeError(
            "Hourly mobility summary is empty."
        )

    return df


# =============================================================================
# FEATURE ENGINEERING
# =============================================================================

def prepare_features(df):

    df = df.copy()

    # -------------------------------------------------------------------------
    # Rain indicator
    # -------------------------------------------------------------------------

    df["rain_flag"] = (
        df["precipitation"] > 0
    ).astype(int)

    # -------------------------------------------------------------------------
    # Weekend indicator
    # -------------------------------------------------------------------------

    df["is_weekend"] = (
        df["is_weekend"].astype(int)
    )

    # -------------------------------------------------------------------------
    # Day of week
    #
    # DuckDB EXTRACT(DOW):
    # 0 = Sunday
    # 1 = Monday
    # ...
    # 6 = Saturday
    #
    # We treat day of week as categorical rather than numeric.
    # -------------------------------------------------------------------------

    df["day_of_week"] = (
        df["day_of_week"].astype(int)
    )

    day_dummies = pd.get_dummies(
        df["day_of_week"],
        prefix="day",
        drop_first=True,
        dtype=float,
    )

    # -------------------------------------------------------------------------
    # Hour of day
    #
    # Treat hour as categorical.
    # This avoids imposing a false linear relationship between 23:00 and 00:00.
    # -------------------------------------------------------------------------

    hour_dummies = pd.get_dummies(
        df["hour_of_day"],
        prefix="hour",
        drop_first=True,
        dtype=float,
    )

    # -------------------------------------------------------------------------
    # Month
    # -------------------------------------------------------------------------

    month_dummies = pd.get_dummies(
        df["month_start"],
        prefix="month",
        drop_first=True,
        dtype=float,
    )

    # -------------------------------------------------------------------------
    # Combine engineered features
    # -------------------------------------------------------------------------

    df = pd.concat(
        [
            df,
            day_dummies,
            hour_dummies,
            month_dummies,
        ],
        axis=1,
    )

    return df


# =============================================================================
# BASIC VALIDATION
# =============================================================================

def validate_data(df):

    print("=" * 80)
    print("METROPULSE — MOBILITY REGRESSION ANALYSIS")
    print("=" * 80)

    print("\n")
    print("=" * 80)
    print("1. DATA VALIDATION")
    print("=" * 80)

    print(f"Rows:          {len(df):,}")
    print(
        f"Unique hours:  "
        f"{df['pickup_hour'].nunique():,}"
    )

    if len(df) != 2184:
        raise RuntimeError(
            f"Expected 2,184 observations, "
            f"found {len(df):,}"
        )

    if df["pickup_hour"].nunique() != 2184:
        raise RuntimeError(
            "Duplicate hourly observations detected."
        )

    required = [
        "taxi_trip_count",
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "wind_speed_10m",
        "cloud_cover",
        "subway_ridership",
        "subway_transfers",
        "day_of_week",
    ]

    missing = [
        column
        for column in required
        if df[column].isna().any()
    ]

    if missing:
        raise RuntimeError(
            "Missing values found in: "
            + ", ".join(missing)
        )

    print(
        "\n[SUCCESS] Regression dataset validated."
    )


# =============================================================================
# DESCRIPTIVE ANALYSIS
# =============================================================================

def analyze_demand_distribution(df):

    print("\n")
    print("=" * 80)
    print("2. TAXI DEMAND DISTRIBUTION")
    print("=" * 80)

    result = df["taxi_trip_count"].describe()

    print(result.to_string())

    print(
        f"\nSkewness: "
        f"{df['taxi_trip_count'].skew():.3f}"
    )

    print(
        f"Coefficient of variation: "
        f"{df['taxi_trip_count'].std() / df['taxi_trip_count'].mean():.3f}"
    )


def analyze_hourly_pattern(df):

    print("\n")
    print("=" * 80)
    print("3. HOURLY DEMAND PATTERN")
    print("=" * 80)

    result = (
        df.groupby("hour_of_day", as_index=False)
        .agg(
            observations=("taxi_trip_count", "size"),
            avg_taxi_trips=("taxi_trip_count", "mean"),
            median_taxi_trips=("taxi_trip_count", "median"),
        )
        .sort_values("hour_of_day")
    )

    result["avg_taxi_trips"] = result["avg_taxi_trips"].round(2)
    result["median_taxi_trips"] = result["median_taxi_trips"].round(2)

    print(result.to_string(index=False))

    peak = result.loc[
        result["avg_taxi_trips"].idxmax()
    ]

    trough = result.loc[
        result["avg_taxi_trips"].idxmin()
    ]

    print(
        f"\nPeak average demand hour: "
        f"{int(peak['hour_of_day']):02d}:00 "
        f"({peak['avg_taxi_trips']:,.2f} trips)"
    )

    print(
        f"Lowest average demand hour: "
        f"{int(trough['hour_of_day']):02d}:00 "
        f"({trough['avg_taxi_trips']:,.2f} trips)"
    )


def analyze_weekend_effect(df):

    print("\n")
    print("=" * 80)
    print("4. WEEKDAY VS WEEKEND")
    print("=" * 80)

    result = (
        df.groupby("is_weekend", as_index=False)
        .agg(
            hours=("taxi_trip_count", "size"),
            avg_taxi_trips=("taxi_trip_count", "mean"),
            median_taxi_trips=("taxi_trip_count", "median"),
        )
    )

    result["avg_taxi_trips"] = result["avg_taxi_trips"].round(2)
    result["median_taxi_trips"] = result["median_taxi_trips"].round(2)

    print(result.to_string(index=False))


def analyze_weather_conditions(df):

    print("\n")
    print("=" * 80)
    print("5. WEATHER CONDITIONS")
    print("=" * 80)

    df = df.copy()

    df["weather_condition"] = "dry"

    df.loc[
        df["rain"] > 0,
        "weather_condition"
    ] = "rain"

    df.loc[
        df["precipitation"] > 0,
        "weather_condition"
    ] = "precipitation"

    result = (
        df.groupby("weather_condition", as_index=False)
        .agg(
            hours=("taxi_trip_count", "size"),
            avg_taxi_trips=("taxi_trip_count", "mean"),
            median_taxi_trips=("taxi_trip_count", "median"),
            avg_precipitation=("precipitation", "mean"),
        )
    )

    result["avg_taxi_trips"] = result["avg_taxi_trips"].round(2)
    result["median_taxi_trips"] = result["median_taxi_trips"].round(2)
    result["avg_precipitation"] = result["avg_precipitation"].round(3)

    print(result.to_string(index=False))


# =============================================================================
# MODEL BUILDER
# =============================================================================

def fit_model(df, predictor_columns):

    X = df[predictor_columns].copy()

    non_numeric_columns = [
        column
        for column in X.columns
        if not pd.api.types.is_numeric_dtype(
            X[column]
        )
    ]

    if non_numeric_columns:
        raise TypeError(
            "Non-numeric predictors detected: "
            + ", ".join(non_numeric_columns)
        )

    X = X.astype(float)

    X = sm.add_constant(
        X,
        has_constant="add",
    )

    X = X.astype(float)

    y = df["taxi_trip_count"].astype(float)

    model = sm.OLS(
        y,
        X,
    ).fit(
        cov_type="HAC",
        cov_kwds={
            "maxlags": 24,
        },
    )

    return model


# =============================================================================
# HELPER — TEMPORAL DUMMY COLUMNS
# =============================================================================

def get_temporal_columns(df):

    day_columns = [
        column
        for column in df.columns
        if column.startswith("day_")
        and column != "day_of_week"
    ]

    hour_columns = [
        column
        for column in df.columns
        if column.startswith("hour_")
        and column != "hour_of_day"
    ]

    month_columns = [
        column
        for column in df.columns
        if column.startswith("month_")
        and column != "month_start"
    ]

    return (
        day_columns,
        hour_columns,
        month_columns,
    )


# =============================================================================
# MODEL 1 — RAW SUBWAY ASSOCIATION
# =============================================================================

def model_raw_subway(df):

    print("\n")
    print("=" * 80)
    print("2. MODEL 1 — RAW SUBWAY ASSOCIATION")
    print("=" * 80)

    model = fit_model(
        df,
        [
            "subway_ridership",
        ],
    )

    print(
        model.summary()
    )

    return model


# =============================================================================
# MODEL 2 — SUBWAY + TIME CONTROLS
# =============================================================================

def model_subway_time_controls(df):

    print("\n")
    print("=" * 80)
    print("3. MODEL 2 — SUBWAY + TEMPORAL CONTROLS")
    print("=" * 80)

    day_columns, hour_columns, month_columns = (
        get_temporal_columns(df)
    )

    predictors = [
        "subway_ridership",
    ]

    predictors += day_columns
    predictors += hour_columns
    predictors += month_columns

    model = fit_model(
        df,
        predictors,
    )

    print(
        model.summary()
    )

    return model


# =============================================================================
# MODEL 3 — WEATHER + SUBWAY + TIME
# =============================================================================

def model_full(df):

    print("\n")
    print("=" * 80)
    print("4. MODEL 3 — WEATHER + SUBWAY + TEMPORAL CONTROLS")
    print("=" * 80)

    day_columns, hour_columns, month_columns = (
        get_temporal_columns(df)
    )

    predictors = [
        "subway_ridership",
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "wind_speed_10m",
        "cloud_cover",
    ]

    predictors += day_columns
    predictors += hour_columns
    predictors += month_columns

    model = fit_model(
        df,
        predictors,
    )

    print(
        model.summary()
    )

    return model


# =============================================================================
# RAIN FLAG MODEL
# =============================================================================

def model_rain_flag(df):

    print("\n")
    print("=" * 80)
    print("5. MODEL 4 — RAIN OCCURRENCE + CONTROLS")
    print("=" * 80)

    day_columns, hour_columns, month_columns = (
        get_temporal_columns(df)
    )

    predictors = [
        "rain_flag",
        "subway_ridership",
        "temperature_2m",
        "relative_humidity_2m",
        "wind_speed_10m",
        "cloud_cover",
    ]

    predictors += day_columns
    predictors += hour_columns
    predictors += month_columns

    model = fit_model(
        df,
        predictors,
    )

    print(
        model.summary()
    )

    return model


# =============================================================================
# LAGGED SUBWAY ANALYSIS
# =============================================================================

def run_lagged_subway_analysis(df):

    print("\n")
    print("=" * 80)
    print("LAGGED SUBWAY ANALYSIS")
    print("=" * 80)

    analysis_df = df.copy()

    analysis_df = analysis_df.sort_values(
        "pickup_hour"
    ).reset_index(drop=True)

    for lag in [1, 2, 3]:

        analysis_df[
            f"subway_ridership_lag_{lag}"
        ] = (
            analysis_df["subway_ridership"]
            .shift(lag)
        )

    analysis_df = analysis_df.dropna(
        subset=[
            "subway_ridership_lag_1",
            "subway_ridership_lag_2",
            "subway_ridership_lag_3",
        ]
    )

    day_columns, hour_columns, month_columns = (
        get_temporal_columns(analysis_df)
    )

    predictors = [
        "subway_ridership",
        "subway_ridership_lag_1",
        "subway_ridership_lag_2",
        "subway_ridership_lag_3",
    ]

    predictors += day_columns
    predictors += hour_columns
    predictors += month_columns

    X = analysis_df[predictors].astype(float)

    X = sm.add_constant(
        X,
        has_constant="add",
    )

    y = analysis_df[
        "taxi_trip_count"
    ].astype(float)

    model = sm.OLS(
        y,
        X,
    ).fit(
        cov_type="HAC",
        cov_kwds={
            "maxlags": 24,
        },
    )

    coefficients = pd.DataFrame(
        {
            "coefficient": model.params[
                [
                    "subway_ridership",
                    "subway_ridership_lag_1",
                    "subway_ridership_lag_2",
                    "subway_ridership_lag_3",
                ]
            ],
            "p_value": model.pvalues[
                [
                    "subway_ridership",
                    "subway_ridership_lag_1",
                    "subway_ridership_lag_2",
                    "subway_ridership_lag_3",
                ]
            ],
            "ci_lower": model.conf_int().loc[
                [
                    "subway_ridership",
                    "subway_ridership_lag_1",
                    "subway_ridership_lag_2",
                    "subway_ridership_lag_3",
                ],
                0,
            ],
            "ci_upper": model.conf_int().loc[
                [
                    "subway_ridership",
                    "subway_ridership_lag_1",
                    "subway_ridership_lag_2",
                    "subway_ridership_lag_3",
                ],
                1,
            ],
        }
    )

    print(
        coefficients.round(6).to_string()
    )

    print(
        f"\nObservations used: {len(analysis_df):,}"
    )

    print(
        f"Adjusted R-squared: "
        f"{model.rsquared_adj:.4f}"
    )

    print(
        "\n[SUCCESS] Lagged subway analysis complete."
    )

    return model

# =============================================================================
# TAXI DEMAND LAG ANALYSIS
# =============================================================================

def run_taxi_demand_lag_analysis(df):

    print("\n")
    print("=" * 80)
    print("TAXI DEMAND LAG ANALYSIS")
    print("=" * 80)

    analysis_df = df.copy()

    analysis_df = analysis_df.sort_values(
        "pickup_hour"
    ).reset_index(drop=True)

    # -------------------------------------------------------------------------
    # Create historical taxi-demand variables
    #
    # lag_1   = previous hour
    # lag_2   = two hours earlier
    # lag_24  = same hour previous day
    # lag_168 = same hour previous week
    # -------------------------------------------------------------------------

    analysis_df["taxi_trip_count_lag_1"] = (
        analysis_df["taxi_trip_count"].shift(1)
    )

    analysis_df["taxi_trip_count_lag_2"] = (
        analysis_df["taxi_trip_count"].shift(2)
    )

    analysis_df["taxi_trip_count_lag_24"] = (
        analysis_df["taxi_trip_count"].shift(24)
    )

    analysis_df["taxi_trip_count_lag_168"] = (
        analysis_df["taxi_trip_count"].shift(168)
    )

    # -------------------------------------------------------------------------
    # Temporal controls
    # -------------------------------------------------------------------------

    day_columns, hour_columns, month_columns = (
        get_temporal_columns(analysis_df)
    )

    # -------------------------------------------------------------------------
    # Model A
    #
    # Current subway + weather + temporal controls
    #
    # This is the baseline against which the lagged models are compared.
    # -------------------------------------------------------------------------

    baseline_predictors = [
        "subway_ridership",
        "rain_flag",
        "temperature_2m",
        "relative_humidity_2m",
        "wind_speed_10m",
        "cloud_cover",
    ]

    baseline_predictors += day_columns
    baseline_predictors += hour_columns
    baseline_predictors += month_columns

    baseline_df = analysis_df.dropna(
        subset=baseline_predictors
    ).copy()

    X_baseline = baseline_df[
        baseline_predictors
    ].astype(float)

    X_baseline = sm.add_constant(
        X_baseline,
        has_constant="add",
    )

    y_baseline = baseline_df[
        "taxi_trip_count"
    ].astype(float)

    baseline_model = sm.OLS(
        y_baseline,
        X_baseline,
    ).fit(
        cov_type="HAC",
        cov_kwds={
            "maxlags": 24,
        },
    )

    # -------------------------------------------------------------------------
    # Model B
    #
    # Add short-term demand history:
    # lag 1 + lag 2
    # -------------------------------------------------------------------------

    short_lag_predictors = (
        baseline_predictors
        + [
            "taxi_trip_count_lag_1",
            "taxi_trip_count_lag_2",
        ]
    )

    short_lag_df = analysis_df.dropna(
        subset=short_lag_predictors
    ).copy()

    X_short = short_lag_df[
        short_lag_predictors
    ].astype(float)

    X_short = sm.add_constant(
        X_short,
        has_constant="add",
    )

    y_short = short_lag_df[
        "taxi_trip_count"
    ].astype(float)

    short_lag_model = sm.OLS(
        y_short,
        X_short,
    ).fit(
        cov_type="HAC",
        cov_kwds={
            "maxlags": 24,
        },
    )

    # -------------------------------------------------------------------------
    # Model C
    #
    # Add short-term, daily, and weekly demand history.
    # -------------------------------------------------------------------------

    full_lag_predictors = (
        baseline_predictors
        + [
            "taxi_trip_count_lag_1",
            "taxi_trip_count_lag_2",
            "taxi_trip_count_lag_24",
            "taxi_trip_count_lag_168",
        ]
    )

    full_lag_df = analysis_df.dropna(
        subset=full_lag_predictors
    ).copy()

    X_full = full_lag_df[
        full_lag_predictors
    ].astype(float)

    X_full = sm.add_constant(
        X_full,
        has_constant="add",
    )

    y_full = full_lag_df[
        "taxi_trip_count"
    ].astype(float)

    full_lag_model = sm.OLS(
        y_full,
        X_full,
    ).fit(
        cov_type="HAC",
        cov_kwds={
            "maxlags": 168,
        },
    )

    # -------------------------------------------------------------------------
    # Model comparison
    # -------------------------------------------------------------------------

    print("\n")
    print(
        "MODEL COMPARISON"
    )

    comparison = pd.DataFrame(
        [
            {
                "model": "Baseline",
                "observations": len(baseline_df),
                "r_squared": baseline_model.rsquared,
                "adjusted_r_squared": baseline_model.rsquared_adj,
                "aic": baseline_model.aic,
                "bic": baseline_model.bic,
            },
            {
                "model": "Short lags (1,2)",
                "observations": len(short_lag_df),
                "r_squared": short_lag_model.rsquared,
                "adjusted_r_squared": short_lag_model.rsquared_adj,
                "aic": short_lag_model.aic,
                "bic": short_lag_model.bic,
            },
            {
                "model": "Full lags (1,2,24,168)",
                "observations": len(full_lag_df),
                "r_squared": full_lag_model.rsquared,
                "adjusted_r_squared": full_lag_model.rsquared_adj,
                "aic": full_lag_model.aic,
                "bic": full_lag_model.bic,
            },
        ]
    )

    print(
        comparison.round(4).to_string(
            index=False
        )
    )

    # -------------------------------------------------------------------------
    # Lag coefficients
    # -------------------------------------------------------------------------

    print("\n")
    print(
        "LAGGED DEMAND COEFFICIENTS"
    )

    lag_columns = [
        "taxi_trip_count_lag_1",
        "taxi_trip_count_lag_2",
        "taxi_trip_count_lag_24",
        "taxi_trip_count_lag_168",
    ]

    available_lags = [
        column
        for column in lag_columns
        if column in full_lag_model.params.index
    ]

    lag_result = pd.DataFrame(
        {
            "coefficient": full_lag_model.params[
                available_lags
            ],
            "p_value": full_lag_model.pvalues[
                available_lags
            ],
            "ci_lower": full_lag_model.conf_int().loc[
                available_lags,
                0,
            ],
            "ci_upper": full_lag_model.conf_int().loc[
                available_lags,
                1,
            ],
        }
    )

    print(
        lag_result.round(6).to_string()
    )

    # -------------------------------------------------------------------------
    # Current subway coefficient stability
    # -------------------------------------------------------------------------

    print("\n")
    print(
        "SUBWAY COEFFICIENT STABILITY"
    )

    subway_result = pd.DataFrame(
        {
            "model": [
                "Baseline",
                "Short lags (1,2)",
                "Full lags (1,2,24,168)",
            ],
            "subway_coefficient": [
                baseline_model.params[
                    "subway_ridership"
                ],
                short_lag_model.params[
                    "subway_ridership"
                ],
                full_lag_model.params[
                    "subway_ridership"
                ],
            ],
            "p_value": [
                baseline_model.pvalues[
                    "subway_ridership"
                ],
                short_lag_model.pvalues[
                    "subway_ridership"
                ],
                full_lag_model.pvalues[
                    "subway_ridership"
                ],
            ],
        }
    )

    print(
        subway_result.round(6).to_string(
            index=False
        )
    )

    print("\n")
    print(
        "[SUCCESS] Taxi demand lag analysis complete."
    )

    return {
        "baseline": baseline_model,
        "short_lag": short_lag_model,
        "full_lag": full_lag_model,
    }

# ==============================================================================
# HAC SENSITIVITY ANALYSIS
# ==============================================================================

def run_hac_sensitivity(df):

    """
    Test whether the subway coefficient remains stable
    across different HAC lag specifications.
    """

    day_columns, hour_columns, month_columns = (
        get_temporal_columns(df)
    )

    predictors = [
        "subway_ridership",
    ]

    predictors += day_columns
    predictors += hour_columns
    predictors += month_columns

    X = df[predictors].copy()

    X = sm.add_constant(
        X,
        has_constant="add",
    )

    X = X.astype(float)

    y = df["taxi_trip_count"].astype(float)

    lag_values = [6, 12, 24, 48, 168]

    print("\n")
    print("=" * 80)
    print("HAC SENSITIVITY ANALYSIS")
    print("=" * 80)

    print(
        "\nModel: Subway + day/hour/month controls"
    )

    print(
        "Testing HAC lag specifications:"
    )

    print()

    for lag in lag_values:

        model = sm.OLS(
            y,
            X,
        ).fit(
            cov_type="HAC",
            cov_kwds={
                "maxlags": lag,
            },
        )

        coefficient = model.params[
            "subway_ridership"
        ]

        p_value = model.pvalues[
            "subway_ridership"
        ]

        ci = model.conf_int().loc[
            "subway_ridership"
        ]

        print(
            f"HAC lag {lag:>3}: "
            f"coefficient={coefficient:.6f}, "
            f"p-value={p_value:.6f}, "
            f"CI=({ci[0]:.6f}, {ci[1]:.6f})"
        )

    print()

    print(
        "[SUCCESS] HAC sensitivity analysis complete."
    )


# =============================================================================
# MODEL COMPARISON
# =============================================================================

def compare_models(models):

    print("\n")
    print("=" * 80)
    print("6. MODEL COMPARISON")
    print("=" * 80)

    rows = []

    for name, model in models.items():

        rows.append(
            {
                "model": name,
                "r_squared": model.rsquared,
                "adjusted_r_squared": model.rsquared_adj,
                "aic": model.aic,
                "bic": model.bic,
            }
        )

    result = pd.DataFrame(rows)

    print(
        result.round(4).to_string(
            index=False
        )
    )


# =============================================================================
# KEY COEFFICIENTS
# =============================================================================

def print_key_coefficients(models):

    print("\n")
    print("=" * 80)
    print("7. KEY COEFFICIENTS")
    print("=" * 80)

    for name, model in models.items():

        print(
            f"\n{name}"
        )

        interesting = [
            column
            for column in [
                "subway_ridership",
                "precipitation",
                "rain_flag",
                "temperature_2m",
                "relative_humidity_2m",
                "wind_speed_10m",
                "cloud_cover",
            ]
            if column in model.params.index
        ]

        result = pd.DataFrame(
            {
                "coefficient": model.params[
                    interesting
                ],
                "p_value": model.pvalues[
                    interesting
                ],
                "ci_lower": model.conf_int().loc[
                    interesting,
                    0
                ],
                "ci_upper": model.conf_int().loc[
                    interesting,
                    1
                ],
            }
        )

        print(
            result.round(4).to_string()
        )


# =============================================================================
# MULTICOLLINEARITY CHECK
# =============================================================================

def check_vif(df):

    print("\n")
    print("=" * 80)
    print("8. MULTICOLLINEARITY CHECK")
    print("=" * 80)

    variables = [
        "subway_ridership",
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "wind_speed_10m",
        "cloud_cover",
    ]

    X = df[variables].astype(float)

    X = sm.add_constant(
        X,
        has_constant="add",
    )

    vif_rows = []

    for i, column in enumerate(X.columns):

        if column == "const":
            continue

        vif_rows.append(
            {
                "variable": column,
                "VIF": variance_inflation_factor(
                    X.values,
                    i,
                ),
            }
        )

    result = pd.DataFrame(
        vif_rows
    )

    print(
        result.round(3).to_string(
            index=False
        )
    )


# =============================================================================
# MAIN
# =============================================================================

def main():

    con = connect_database()

    try:

        df = load_data(con)

        validate_data(df)

        df = prepare_features(df)

        # Verify categorical temporal features before modeling.
        print(
            "\nDay-of-week dummy columns:",
            [
                column
                for column in df.columns
                if column.startswith("day_")
            ],
        )

        analyze_demand_distribution(df)

        analyze_hourly_pattern(df)

        analyze_weekend_effect(df)

        analyze_weather_conditions(df)

        model_1 = model_raw_subway(
            df
        )

        model_2 = model_subway_time_controls(
            df
        )

        model_3 = model_full(
            df
        )

        model_4 = model_rain_flag(
            df
        )

        run_lagged_subway_analysis(
            df
        )

        run_taxi_demand_lag_analysis(
           df
)
        run_hac_sensitivity(
            df
        )

        models = {
            "Model 1 — Raw subway": model_1,
            "Model 2 — Subway + day/hour/month": model_2,
            "Model 3 — Full + day/hour/month": model_3,
            "Model 4 — Rain flag + day/hour/month": model_4,
        }

        compare_models(
            models
        )

        print_key_coefficients(
            models
        )

        check_vif(
            df
        )

    finally:

        con.close()


if __name__ == "__main__":
    main()
