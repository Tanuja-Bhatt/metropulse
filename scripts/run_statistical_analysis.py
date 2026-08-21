from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "metropulse.duckdb"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "statistical_analysis"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------

TARGET = "taxi_trip_count"

BASELINE_FEATURES = [
    "taxi_trip_count_lag_1",
    "taxi_trip_count_lag_2",
    "taxi_trip_count_lag_24",
    "taxi_trip_count_lag_168",
]

TRANSIT_FEATURES = [
    "subway_ridership",
    "subway_ridership_lag_1",
    "subway_ridership_lag_2",
    "subway_ridership_lag_24",
]

WEATHER_FEATURES = [
    "temperature_2m",
    "precipitation",
    "rain_flag",
]

REDUCED_FEATURES = [
    "taxi_trip_count_lag_1",
    "taxi_trip_count_lag_24",
    "taxi_trip_count_lag_168",
    "subway_ridership",
    "temperature_2m",
    "precipitation",
    "rain_flag",
    "hour_of_day",
    "day_of_week",
    "regression_month",
]

TIME_FEATURES = [
    "hour_of_day",
    "day_of_week",
    "regression_month",
]


# ---------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------

def load_data():
    print("=" * 80)
    print("LOADING STATISTICAL ANALYSIS DATA")
    print("=" * 80)

    con = duckdb.connect(str(DB_PATH), read_only=True)

    query = """
        SELECT *
        FROM marts.statistical_analysis
        ORDER BY pickup_hour
    """

    df = con.execute(query).df()
    con.close()

    print(f"Rows loaded: {len(df):,}")
    print(f"Columns loaded: {len(df.columns):,}")

    if df.empty:
        raise RuntimeError("Statistical analysis mart is empty.")

    return df


# ---------------------------------------------------------------------
# PREPARATION
# ---------------------------------------------------------------------

def prepare_data(df):
    print("\n" + "=" * 80)
    print("PREPARING REGRESSION DATA")
    print("=" * 80)

    required_columns = (
        [TARGET]
        + BASELINE_FEATURES
        + TRANSIT_FEATURES
        + WEATHER_FEATURES
        + TIME_FEATURES
        + ["pickup_hour"]
    )

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise RuntimeError(
            f"Required columns missing from statistical mart: {missing}"
        )

    df = df.copy()

    # Ensure chronological ordering.
    df["pickup_hour"] = pd.to_datetime(df["pickup_hour"])
    df = df.sort_values("pickup_hour").reset_index(drop=True)

    # Complete analytical sample for the full specification.
    complete_columns = (
        [TARGET]
        + BASELINE_FEATURES
        + TRANSIT_FEATURES
        + WEATHER_FEATURES
        + TIME_FEATURES
    )

    before = len(df)

    df = df.dropna(subset=complete_columns).copy()

    after = len(df)

    print(f"Rows before complete-case filtering: {before:,}")
    print(f"Rows after complete-case filtering:  {after:,}")
    print(f"Rows removed:                       {before - after:,}")

    if after < 500:
        raise RuntimeError(
            "Too few complete observations for regression analysis."
        )

    return df


# ---------------------------------------------------------------------
# DESIGN MATRIX
# ---------------------------------------------------------------------

def build_design_matrix(df, features):
    """
    Build regression matrix.

    Continuous variables remain numeric.

    Temporal categorical variables are one-hot encoded:
        hour_of_day
        day_of_week
        regression_month

    The first category is dropped to avoid perfect multicollinearity.
    """

    continuous_features = [
        feature
        for feature in features
        if feature not in TIME_FEATURES
    ]

    temporal_features = [
        feature
        for feature in features
        if feature in TIME_FEATURES
    ]

    X = df[continuous_features].copy()

    if temporal_features:
        categorical = pd.get_dummies(
            df[temporal_features].astype(int).astype(str),
            columns=temporal_features,
            drop_first=True,
            dtype=float,
        )

        X = pd.concat([X, categorical], axis=1)

    X = sm.add_constant(X, has_constant="add")

    return X.astype(float)


# ---------------------------------------------------------------------
# CHRONOLOGICAL SPLIT
# ---------------------------------------------------------------------

def chronological_split(df, X, test_size=0.20):
    n = len(df)

    split_index = int(n * (1 - test_size))

    train_df = df.iloc[:split_index].copy()
    test_df = df.iloc[split_index:].copy()

    X_train = X.iloc[:split_index].copy()
    X_test = X.iloc[split_index:].copy()

    y_train = train_df[TARGET].astype(float)
    y_test = test_df[TARGET].astype(float)

    print(f"Training observations: {len(train_df):,}")
    print(f"Testing observations:  {len(test_df):,}")
    print(
        f"Training period:       "
        f"{train_df['pickup_hour'].min()} → "
        f"{train_df['pickup_hour'].max()}"
    )
    print(
        f"Testing period:        "
        f"{test_df['pickup_hour'].min()} → "
        f"{test_df['pickup_hour'].max()}"
    )

    return (
        X_train,
        X_test,
        y_train,
        y_test,
        train_df,
        test_df,
    )


# ---------------------------------------------------------------------
# MODEL METRICS
# ---------------------------------------------------------------------

def calculate_metrics(y_true, y_pred):
    residuals = y_true - y_pred

    mae = np.mean(np.abs(residuals))
    rmse = np.sqrt(np.mean(residuals ** 2))

    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    r2 = 1 - (ss_res / ss_tot)

    return {
        "MAE": float(mae),
        "RMSE": float(rmse),
        "R2": float(r2),
    }


# ---------------------------------------------------------------------
# MODEL FITTING
# ---------------------------------------------------------------------

def fit_model(model_name, df, features):
    print("\n" + "=" * 80)
    print(f"FITTING {model_name.upper()}")
    print("=" * 80)

    X = build_design_matrix(df, features)
    y = df[TARGET].astype(float)

    (
        X_train,
        X_test,
        y_train,
        y_test,
        train_df,
        test_df,
    ) = chronological_split(df, X)

    model = sm.OLS(y_train, X_train).fit()

    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)

    train_metrics = calculate_metrics(y_train, train_pred)
    test_metrics = calculate_metrics(y_test, test_pred)

    print("\nTRAINING METRICS")
    print("-" * 40)

    for metric, value in train_metrics.items():
        print(f"{metric:<10}: {value:,.4f}")

    print("\nTEST METRICS")
    print("-" * 40)

    for metric, value in test_metrics.items():
        print(f"{metric:<10}: {value:,.4f}")

    print("\nMODEL SUMMARY")
    print("-" * 40)
    print(f"R-squared:          {model.rsquared:.6f}")
    print(f"Adjusted R-squared: {model.rsquared_adj:.6f}")
    print(f"F-statistic:        {model.fvalue:.6f}")
    print(f"F-test p-value:     {model.f_pvalue:.6e}")
    print(f"AIC:                {model.aic:.2f}")
    print(f"BIC:                {model.bic:.2f}")

    coefficients = pd.DataFrame(
        {
            "feature": model.params.index,
            "coefficient": model.params.values,
            "std_error": model.bse.values,
            "t_stat": model.tvalues.values,
            "p_value": model.pvalues.values,
            "ci_lower": model.conf_int()[0].values,
            "ci_upper": model.conf_int()[1].values,
        }
    )

    coefficients["significant_05"] = (
        coefficients["p_value"] < 0.05
    )

    output_prefix = OUTPUT_DIR / model_name

    coefficients.to_csv(
        f"{output_prefix}_coefficients.csv",
        index=False,
    )

    metrics = pd.DataFrame(
        [
            {
                "model": model_name,
                "sample": "train",
                **train_metrics,
            },
            {
                "model": model_name,
                "sample": "test",
                **test_metrics,
            },
        ]
    )

    metrics.to_csv(
        f"{output_prefix}_metrics.csv",
        index=False,
    )

    predictions = test_df[
        ["pickup_hour", TARGET]
    ].copy()

    predictions["prediction"] = test_pred.values
    predictions["residual"] = (
        predictions[TARGET] - predictions["prediction"]
    )

    predictions.to_csv(
        f"{output_prefix}_test_predictions.csv",
        index=False,
    )

    return {
        "name": model_name,
        "model": model,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "train_metrics": train_metrics,
        "test_metrics": test_metrics,
        "coefficients": coefficients,        "test_predictions": predictions,
    }


def error_diagnostics(result):
    print("\n" + "=" * 80)
    print("TEST ERROR DIAGNOSTICS")
    print("=" * 80)

    predictions = result["test_predictions"].copy()

    predictions["abs_error"] = (
        predictions[TARGET] - predictions["prediction"]
    ).abs()

    predictions["squared_error"] = (
        predictions[TARGET] - predictions["prediction"]
    ) ** 2

    predictions["hour_of_day"] = (
        predictions["pickup_hour"].dt.hour
    )

    predictions["day_of_week"] = (
        predictions["pickup_hour"].dt.dayofweek
    )

    predictions["is_weekend"] = (
        predictions["day_of_week"] >= 5
    )

    print("\nWORST 20 TEST PREDICTIONS")
    print("-" * 80)

    worst = predictions.sort_values(
        "abs_error",
        ascending=False,
    ).head(20)

    print(
        worst[
            [
                "pickup_hour",
                TARGET,
                "prediction",
                "abs_error",
                "hour_of_day",
                "is_weekend",
            ]
        ].to_string(index=False)
    )

    hourly = (
        predictions
        .groupby("hour_of_day")
        .agg(
            observations=("abs_error", "size"),
            mae=("abs_error", "mean"),
            rmse=(
                "squared_error",
                lambda x: np.sqrt(x.mean()),
            ),
        )
        .reset_index()
        .sort_values("mae", ascending=False)
    )

    print("\nERROR BY HOUR")
    print("-" * 80)
    print(hourly.to_string(index=False))

    weekend = (
        predictions
        .groupby("is_weekend")
        .agg(
            observations=("abs_error", "size"),
            mae=("abs_error", "mean"),
            rmse=(
                "squared_error",
                lambda x: np.sqrt(x.mean()),
            ),
        )
        .reset_index()
    )

    print("\nERROR BY WEEKEND STATUS")
    print("-" * 80)
    print(weekend.to_string(index=False))

    output = predictions[
        [
            "pickup_hour",
            TARGET,
            "prediction",
            "residual",
            "abs_error",
            "hour_of_day",
            "day_of_week",
            "is_weekend",
        ]
    ]

    output.to_csv(
        OUTPUT_DIR / "test_error_diagnostics.csv",
        index=False,
    )

    hourly.to_csv(
        OUTPUT_DIR / "test_error_by_hour.csv",
        index=False,
    )

    weekend.to_csv(
        OUTPUT_DIR / "test_error_by_weekend.csv",
        index=False,
    )

    return {
        "predictions": output,
        "hourly": hourly,
        "weekend": weekend,
    }

# ---------------------------------------------------------------------
# VIF
# ---------------------------------------------------------------------

def calculate_vif(df, features):
    print("\n" + "=" * 80)
    print("MULTICOLLINEARITY / VIF DIAGNOSTICS")
    print("=" * 80)

    X = build_design_matrix(df, features)

    # Constant does not have a meaningful VIF.
    X_vif = X.drop(columns=["const"], errors="ignore")

    vif_rows = []

    for index, column in enumerate(X_vif.columns):
        try:
            vif_value = variance_inflation_factor(
                X_vif.values,
                index,
            )
        except Exception:
            vif_value = np.nan

        vif_rows.append(
            {
                "feature": column,
                "VIF": vif_value,
            }
        )

    vif_df = pd.DataFrame(vif_rows)

    vif_df = vif_df.sort_values(
        "VIF",
        ascending=False,
        na_position="last",
    )

    print(vif_df.to_string(index=False))

    vif_df.to_csv(
        OUTPUT_DIR / "vif_diagnostics.csv",
        index=False,
    )

    return vif_df


# ---------------------------------------------------------------------
# RESIDUAL DIAGNOSTICS
# ---------------------------------------------------------------------

def residual_diagnostics(result):
    print("\n" + "=" * 80)
    print("RESIDUAL DIAGNOSTICS")
    print("=" * 80)

    model = result["model"]

    residuals = model.resid

    diagnostics = {
        "mean_residual": residuals.mean(),
        "median_residual": residuals.median(),
        "std_residual": residuals.std(),
        "min_residual": residuals.min(),
        "max_residual": residuals.max(),
        "residual_p95_abs": np.percentile(
            np.abs(residuals),
            95,
        ),
        "residual_p99_abs": np.percentile(
            np.abs(residuals),
            99,
        ),
    }

    for key, value in diagnostics.items():
        print(f"{key:<25}: {value:,.4f}")

    diagnostics_df = pd.DataFrame(
        [diagnostics]
    )

    diagnostics_df.to_csv(
        OUTPUT_DIR / "residual_diagnostics.csv",
        index=False,
    )

    residual_output = pd.DataFrame(
        {
            "pickup_hour": result["X_train"].index,
            "residual": residuals.values,
        }
    )

    residual_output.to_csv(
        OUTPUT_DIR / "training_residuals.csv",
        index=False,
    )

    return diagnostics_df


# ---------------------------------------------------------------------
# MODEL COMPARISON
# ---------------------------------------------------------------------

def compare_models(results):
    print("\n" + "=" * 80)
    print("MODEL COMPARISON")
    print("=" * 80)

    rows = []

    for result in results:
        model = result["model"]

        rows.append(
            {
                "model": result["name"],
                "train_r2": result["train_metrics"]["R2"],
                "test_r2": result["test_metrics"]["R2"],
                "train_mae": result["train_metrics"]["MAE"],
                "test_mae": result["test_metrics"]["MAE"],
                "train_rmse": result["train_metrics"]["RMSE"],
                "test_rmse": result["test_metrics"]["RMSE"],
                "adjusted_r2": model.rsquared_adj,
                "aic": model.aic,
                "bic": model.bic,
            }
        )

    comparison = pd.DataFrame(rows)

    print(comparison.to_string(index=False))

    comparison.to_csv(
        OUTPUT_DIR / "model_comparison.csv",
        index=False,
    )

    return comparison

def subway_residual_relationship(df):
    print("\n" + "=" * 80)
    print("SUBWAY RELATIONSHIP AFTER TEMPORAL CONTROLS")
    print("=" * 80)

    features = BASELINE_FEATURES + TIME_FEATURES

    X = build_design_matrix(df, features)
    y = df[TARGET].astype(float)

    model = sm.OLS(y, X).fit()

    df = df.copy()
    df["temporal_residual_demand"] = model.resid

    residual_corr = df[
        [
            "temporal_residual_demand",
            "subway_ridership",
        ]
    ].corr().iloc[0, 1]

    print(
        f"Correlation between temporal residual taxi demand "
        f"and subway ridership: {residual_corr:.6f}"
    )

    residuals = df[
        [
            "pickup_hour",
            "temporal_residual_demand",
            "subway_ridership",
            "taxi_trip_count",
        ]
    ]

    residuals.to_csv(
        OUTPUT_DIR / "subway_residual_relationship.csv",
        index=False,
    )

    return residual_corr

# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():

    print("=" * 80)
    print("METROPULSE — STATISTICAL ANALYSIS")
    print("=" * 80)

    df = load_data()
    df = prepare_data(df)

    # ---------------------------------------------------------------
    # MODEL 1
    # Temporal baseline
    # ---------------------------------------------------------------

    model_1_features = (
        BASELINE_FEATURES
        + TIME_FEATURES
    )

    model_1 = fit_model(
        "model_1_temporal_baseline",
        df,
        model_1_features,
    )

    # ---------------------------------------------------------------
    # MODEL 2
    # Temporal + transit
    # ---------------------------------------------------------------

    model_2_features = (
        BASELINE_FEATURES
        + TRANSIT_FEATURES
        + TIME_FEATURES
    )

    model_2 = fit_model(
        "model_2_transit",
        df,
        model_2_features,
    )

    # ---------------------------------------------------------------
    # MODEL 3
    # Temporal + transit + weather
    # ---------------------------------------------------------------

    model_3_features = (
        BASELINE_FEATURES
        + TRANSIT_FEATURES
        + WEATHER_FEATURES
        + TIME_FEATURES
    )

    model_3 = fit_model(
        "model_3_weather",
        df,
        model_3_features,
    )

    # ---------------------------------------------------------------
    # MODEL 4
    # Reduced specification
    # ---------------------------------------------------------------

    model_4 = fit_model(
        "model_4_reduced",
        df,
        REDUCED_FEATURES,
    )

    # ---------------------------------------------------------------
    # VIF
    # ---------------------------------------------------------------

    vif_df = calculate_vif(
        df,
        REDUCED_FEATURES,
    )

    # ---------------------------------------------------------------
    # Residual diagnostics
    # ---------------------------------------------------------------

    residual_diagnostics(model_4)
    error_diagnostics(model_4)

    # ---------------------------------------------------------------
    # Model comparison
    # ---------------------------------------------------------------

    comparison = compare_models(
        [
            model_1,
            model_2,
            model_3,
            model_4,
        ]
    )

    subway_residual_relationship(df)

    # ---------------------------------------------------------------
    # Final summary
    # ---------------------------------------------------------------

    print("\n" + "=" * 80)
    print("STATISTICAL ANALYSIS COMPLETE")
    print("=" * 80)

    print(f"Analytical observations: {len(df):,}")
    print(
        f"Output directory:        "
        f"{OUTPUT_DIR}"
    )

    print("\nModel ranking by test RMSE:")

    print(
        comparison[
            [
                "model",
                "test_rmse",
                "test_mae",
                "test_r2",
            ]
        ]
        .sort_values("test_rmse")
        .to_string(index=False)
    )

    print("\n[SUCCESS] Statistical analysis completed.")


if __name__ == "__main__":
    main()