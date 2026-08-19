from pathlib import Path

import duckdb
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import acorr_ljungbox


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

def load_data(con):

    df = con.execute("""
        SELECT
            pickup_hour,
            taxi_trip_count,
            temperature_2m,
            relative_humidity_2m,
            precipitation,
            wind_speed_10m,
            cloud_cover,
            subway_ridership,
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
    # Day of week
    #
    # DuckDB:
    # 0 = Sunday
    # 1 = Monday
    # ...
    # 6 = Saturday
    # -------------------------------------------------------------------------

    df["day_of_week"] = (
        df["day_of_week"].astype(int)
    )

    # -------------------------------------------------------------------------
    # Hour dummies
    # -------------------------------------------------------------------------

    hour_dummies = pd.get_dummies(
        df["hour_of_day"],
        prefix="hour",
        drop_first=True,
        dtype=float,
    )

    # -------------------------------------------------------------------------
    # Month dummies
    # -------------------------------------------------------------------------

    month_dummies = pd.get_dummies(
        df["month_start"],
        prefix="month",
        drop_first=True,
        dtype=float,
    )

    # -------------------------------------------------------------------------
    # Day-of-week dummies
    # -------------------------------------------------------------------------

    day_dummies = pd.get_dummies(
        df["day_of_week"],
        prefix="day",
        drop_first=True,
        dtype=float,
    )

    # -------------------------------------------------------------------------
    # Combine features
    # -------------------------------------------------------------------------

    df = pd.concat(
        [
            df,
            hour_dummies,
            month_dummies,
            day_dummies,
        ],
        axis=1,
    )

    return df


# =============================================================================
# MODEL
# =============================================================================

def fit_model(df):

    df = df.copy()

    # =========================================================================
    # TAXI DEMAND LAGS
    # =========================================================================

    df = df.sort_values(
        "pickup_hour"
    ).reset_index(drop=True)

    df["taxi_trip_count_lag_1"] = (
        df["taxi_trip_count"].shift(1)
    )

    df["taxi_trip_count_lag_2"] = (
        df["taxi_trip_count"].shift(2)
    )

    df["taxi_trip_count_lag_24"] = (
        df["taxi_trip_count"].shift(24)
    )

    df["taxi_trip_count_lag_168"] = (
        df["taxi_trip_count"].shift(168)
    )

    # =========================================================================
    # PREDICTORS
    # =========================================================================

    predictors = [
        "rain_flag",
        "subway_ridership",
        "temperature_2m",
        "relative_humidity_2m",
        "wind_speed_10m",
        "cloud_cover",
        "taxi_trip_count_lag_1",
        "taxi_trip_count_lag_2",
        "taxi_trip_count_lag_24",
        "taxi_trip_count_lag_168",
    ]

    # Day-of-week controls
    predictors += [
        column
        for column in df.columns
        if column.startswith("day_")
        and column != "day_of_week"
    ]

    # Hour-of-day controls
    predictors += [
        column
        for column in df.columns
        if column.startswith("hour_")
        and column != "hour_of_day"
    ]

    # Month controls
    predictors += [
        column
        for column in df.columns
        if column.startswith("month_")
        and column != "month_start"
    ]

    # =========================================================================
    # REMOVE ROWS LOST TO LAGS
    # =========================================================================

    required_columns = [
        "taxi_trip_count"
    ] + predictors

    model_df = df.dropna(
        subset=required_columns
    ).copy()

    # =========================================================================
    # DESIGN MATRIX
    # =========================================================================

    X = model_df[
        predictors
    ].astype(float)

    X = sm.add_constant(
        X,
        has_constant="add",
    )

    y = model_df[
        "taxi_trip_count"
    ].astype(float)

    # =========================================================================
    # FIT MODEL
    # =========================================================================

    model = sm.OLS(
        y,
        X,
    ).fit(
        cov_type="HAC",
        cov_kwds={
            "maxlags": 168,
        },
    )

    return model, model_df


# =============================================================================
# RESIDUAL DIAGNOSTICS
# =============================================================================

def main():

    print("=" * 80)
    print("METROPULSE — LAGGED DEMAND RESIDUAL DIAGNOSTIC")
    print("=" * 80)

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"DuckDB database not found: {DB_PATH}"
        )

    con = duckdb.connect(
        str(DB_PATH),
        read_only=True,
    )

    try:

        df = load_data(con)

    finally:

        con.close()

    df = prepare_features(df)

    # -------------------------------------------------------------------------
    # Validate temporal features
    # -------------------------------------------------------------------------

    day_columns = [
        column
        for column in df.columns
        if column.startswith("day_")
        and column != "day_of_week"
    ]

    print("\n")
    print("=" * 80)
    print("1. FEATURE VALIDATION")
    print("=" * 80)

    print(
        f"Day-of-week column: "
        f"{'day_of_week' in df.columns}"
    )

    print(
        f"Day dummy columns: "
        f"{day_columns}"
    )

    if len(day_columns) != 6:
        raise RuntimeError(
            f"Expected 6 day-of-week dummy columns, "
            f"found {len(day_columns)}"
        )

    # -------------------------------------------------------------------------
    # Fit model
    # -------------------------------------------------------------------------

    model, model_df = fit_model(df)

    residuals = pd.Series(
       model.resid
    ).reset_index(
    drop=True
    )

    # -------------------------------------------------------------------------
    # Model validation
    # -------------------------------------------------------------------------

    print("\n")
    print("=" * 80)
    print("2. MODEL VALIDATION")
    print("=" * 80)

    print(
        f"Observations:     {len(residuals):,}"
    )

    print(
    f"Original observations: {len(df):,}"
)

    print(
    f"Observations lost to lags: "
    f"{len(df) - len(model_df):,}"
    )

    print(
        f"R-squared:        {model.rsquared:.4f}"
    )

    print(
        f"Adjusted R²:      {model.rsquared_adj:.4f}"
    )

    print(
        "[SUCCESS] Model fitted successfully."
    )

    print("\n")
    print("=" * 80)
    print("3. MODEL COEFFICIENTS")
    print("=" * 80)

    key_coefficients = [
    "subway_ridership",
    "taxi_trip_count_lag_1",
    "taxi_trip_count_lag_2",
    "taxi_trip_count_lag_24",
    "taxi_trip_count_lag_168",
]

    coefficient_result = pd.DataFrame(
    {
        "coefficient": model.params[
            key_coefficients
        ],
        "p_value": model.pvalues[
            key_coefficients
        ],
        "ci_lower": model.conf_int().loc[
            key_coefficients,
            0,
        ],
        "ci_upper": model.conf_int().loc[
            key_coefficients,
            1,
        ],
    }
)

    print(
    coefficient_result.round(6).to_string()
)
    # -------------------------------------------------------------------------
    # Residual summary
    # -------------------------------------------------------------------------


    print("\n")
    print("=" * 80)
    print("4. RESIDUAL SUMMARY")
    print("=" * 80)

    print(
        residuals.describe()
    )

    # -------------------------------------------------------------------------
    # Residual autocorrelation
    # -------------------------------------------------------------------------

    print("\n")
    print("=" * 80)
    print("5. RESIDUAL AUTOCORRELATION")
    print("=" * 80)

    for lag in [
        1,
        2,
        3,
        6,
        12,
        24,
        48,
        168,
    ]:

        correlation = residuals.autocorr(
            lag=lag
        )

        print(
            f"Lag {lag:>3}: "
            f"autocorrelation = "
            f"{correlation:.4f}"
        )

    # -------------------------------------------------------------------------
    # Ljung-Box test
    # -------------------------------------------------------------------------

    print("\n")
    print("=" * 80)
    print("6. LJUNG-BOX TEST")
    print("=" * 80)

    result = acorr_ljungbox(
        residuals,
        lags=[
            1,
            6,
            12,
            24,
            48,
            168,
        ],
        return_df=True,
    )

    print(
        result
    )

    # -------------------------------------------------------------------------
    # Interpretation guide
    # -------------------------------------------------------------------------

    print("\n")
    print("=" * 80)
    print("7. INTERPRETATION GUIDE")
    print("=" * 80)

    print(
        "Lag 1–3  : short-term residual dependence"
    )

    print(
        "Lag 6–24 : intraday/daily residual dependence"
    )

    print(
        "Lag 48   : multi-day residual dependence"
    )

    print(
        "Lag 168  : weekly residual dependence"
    )

    print("\n")
    print(
        "[SUCCESS] Residual diagnostic complete."
    )


if __name__ == "__main__":

    main()
