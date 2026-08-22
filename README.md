# MetroPulse

End-to-end urban mobility intelligence platform for New York City, combining Yellow Taxi trips, subway ridership, weather observations, taxi-zone geography, statistical analysis, and data-quality monitoring.

## Project Status

**Submission-ready analytical dashboard and reproducible warehouse pipeline.**

---

## Business Objective

MetroPulse analyzes NYC mobility patterns to answer four decision questions:

1. When does taxi demand peak and how does it vary across time?
2. Where is taxi activity and revenue concentrated geographically?
3. How do payment behavior, weather, and transit relate to taxi outcomes?
4. Which operational capacity interventions are worth testing?

The project is designed as a **decision-support system**, not as a causal claim about taxi supply or rider behavior.

---

## Data Sources

The pipeline uses official public data sources for:

- NYC Yellow Taxi trip records
- NYC taxi-zone shapefiles and lookup data
- NYC subway ridership / transit data
- Weather observations

Source metadata is stored under:

```text
data/metadata/
```

---

## Architecture

```text
Official Public Sources
        |
        v
   Ingestion Scripts
        |
        v
     Raw Data
        |
        v
   SQL Transformations
        |
        +----------------------+
        |                      |
        v                      v
 Intermediate Models       Data Quality
        |
        v
    Mart Layer
        |
        v
      DuckDB
        |
        +----------------------+
        |                      |
        v                      v
 Streamlit Dashboard     Statistical Analysis
```

---

## Repository Structure

```text
metropulse/
├── data/
│   ├── metadata/
│   ├── raw/
│   └── processed/
│
├── docs/
│   ├── metric_dictionary.md
│   └── pilot_design.md
│
├── metropulse_app/
│   ├── app.py
│   ├── charts.py
│   ├── db.py
│   ├── formatting.py
│   ├── queries.py
│   └── __init__.py
│
├── outputs/
│   ├── statistical_analysis/
│   ├── anomaly_kpi_impact.csv
│   ├── query_optimization_benchmarks.csv
│   └── recommendation_sensitivity.csv
│
├── scripts/
│   ├── analyze_findings.py
│   ├── analyze_mobility_regression.py
│   ├── analyze_taxi_quality.py
│   ├── analyze_taxi_quality_2.py
│   ├── benchmark_optimizations.py
│   ├── build_warehouse.py
│   ├── download_subway.py
│   ├── download_taxi.py
│   ├── download_weather.py
│   ├── download_zones.py
│   ├── recommendation_sensitivity.py
│   ├── rebuild_metropulse.ps1
│   └── run_statistical_analysis.py
│
├── sql/
│   ├── intermediate/
│   └── marts/
│
├── AI_USAGE.md
├── README.md
└── requirements.txt
```

---

## Rebuild the Warehouse

The repository includes a PowerShell rebuild script:

```powershell
.\scripts\rebuild_metropulse.ps1
```

The script performs the following steps:

1. Downloads / validates Yellow Taxi data.
2. Downloads / validates weather data.
3. Downloads / validates subway data.
4. Downloads / validates taxi-zone data.
5. Builds the DuckDB analytical warehouse.

The resulting warehouse is:

```text
data/metropulse.duckdb
```

The DuckDB file is intentionally excluded from Git because it is a generated artifact.

### Important

The rebuild script is intended to reproduce the warehouse from the configured source-data pipeline. It executes the ingestion scripts rather than simply rebuilding from an existing local DuckDB file.

If the source data is already available locally and you only need to rebuild the warehouse, inspect the individual ingestion and warehouse-build scripts before running the full rebuild script.

---

## Run the Dashboard

From the project root:

```powershell
python -m streamlit run .\metropulse_app\app.py
```

The dashboard contains six analytical views:

1. **Executive Overview**
2. **Temporal Demand**
3. **Geographic Performance**
4. **Fares & Payments**
5. **Weather & Transit**
6. **Data Quality & Anomalies**

---

## SQL Transformation Pipeline

The SQL pipeline contains reusable intermediate models for:

- Cleaned taxi trips
- Trip-level metrics
- Hourly demand
- Hourly context
- Airport activity
- Geographic performance
- Origin-destination flows
- Fare and payment metrics
- Weather and mobility metrics
- Data-quality metrics

---

## Mart Layer

The analytical mart layer contains:

- `executive_mobility`
- `fare_payment_analysis`
- `geographic_performance`
- `hourly_mobility`
- `hourly_mobility_summary`
- `statistical_analysis`
- `temporal_demand`
- `weather_transit_analysis`
- `data_quality_anomalies`

---

## Data Quality

The warehouse includes data-quality validation covering:

- Row-count reconciliation
- Duplicate detection
- Timestamp validity
- Distance validity
- Duration validity
- Revenue validity
- Passenger validity
- Zone mapping
- Payment classification
- Analytical grain checks

The dashboard reports **Issue Flags** rather than summing overlapping issue populations and incorrectly presenting them as unique affected trips.

Multiple quality rules can flag the same trip. Therefore, an issue-flag count should **not** be interpreted as the number of unique problematic trips.

---

## Statistical Analysis

The statistical workflow evaluates four model specifications:

1. Temporal baseline
2. Temporal + transit
3. Temporal + weather
4. Reduced model

Evaluation uses chronological train/test separation and reports:

- RMSE
- MAE
- R²
- Coefficients
- Confidence intervals
- p-values
- Residual diagnostics
- VIF diagnostics
- Error diagnostics by hour and weekend
- HAC sensitivity analysis

Model performance is interpreted as **predictive evidence**.

It is not presented as causal evidence that transit or weather independently causes taxi demand.

---

## Key Findings

### Peak Demand

Taxi demand peaks during the evening period, with the highest average hourly demand occurring around **18:00**.

### Geographic Concentration

Taxi activity and revenue are highly concentrated across NYC taxi zones rather than being evenly distributed.

### Transit Relationship

The raw relationship between subway activity and taxi demand is materially stronger than the relationship remaining after temporal controls.

The temporal-residual taxi/subway correlation is approximately **0.0945**, so the raw association should not be interpreted as evidence of a strong independent causal relationship.

### Weather

Weather effects are descriptive and must be interpreted alongside sample size.

The available observation counts vary substantially across precipitation categories, with severe-weather categories containing far fewer observations than dry conditions.

Therefore, estimates for rare weather conditions should not be over-interpreted.

### Data Quality

Multiple quality rules can flag the same trip. Therefore, issue counts are treated as **issue flags rather than unique affected-trip counts**.

---

## Decision Recommendations

MetroPulse supports exactly two operational pilots.

### 1. Airport-Focused Capacity Allocation

Test targeted capacity allocation during the airport-focused afternoon peak.

**Primary metric:**

```text
Completed airport trips / available vehicle-hour
```

**Guardrails:**

- Revenue productivity
- Non-airport service
- Operational service-quality measures

### 2. Multi-Hour Citywide Peak-Capacity Planning

Test planned incremental capacity during the citywide evening peak.

**Primary metric:**

```text
Completed trips / available vehicle-hour
```

**Guardrails:**

- Service quality
- Utilization
- Post-peak service
- Revenue productivity

Both initiatives require controlled operational experiments.

Historical observational data is insufficient to claim causal uplift from either intervention.

Detailed pilot definitions are documented in:

```text
docs/pilot_design.md
```

---

## Recommendation Sensitivity

The recommendation analysis evaluates multiple peak-capacity windows:

| Window | Demand Lift vs. Outside Window |
|---|---:|
| 14:00–18:00 | 65.7% |
| 15:00–19:00 | 76.2% |
| 16:00–20:00 | 77.2% |

The sensitivity analysis supports a **multi-hour peak-capacity strategy** rather than relying on a single-hour intervention.

These results are descriptive and should be validated through prospective operational testing.

---

## Query Optimization

The project includes benchmark evidence for optimized analytical queries.

| Analysis | Before | After |
|---|---:|---:|
| Payment analysis | 680.0 ms | 1.5 ms |
| Geographic analysis | 35.4 ms | 0.8 ms |

The benchmark results are stored in:

```text
outputs/query_optimization_benchmarks.csv
```

The reported improvements are benchmark results from the project environment and should not be interpreted as universal performance guarantees across different hardware or database configurations.

---

## Anomaly / Data-Quality KPI Impact

The project also evaluates how quality-valid records affect executive KPIs.

The current analysis compares:

- All trips
- Quality-valid trips

The resulting retention metrics are stored in:

```text
outputs/anomaly_kpi_impact.csv
```

This analysis demonstrates why data-quality treatment matters when interpreting executive-level metrics.

---

## Metric Definitions

The authoritative metric definitions are documented in:

```text
docs/metric_dictionary.md
```

Each metric includes its:

- Formula
- Grain
- Exclusions
- Assumptions
- Interpretation limitations

---

## AI Disclosure

AI-assisted development is documented in:

```text
AI_USAGE.md
```

AI-generated suggestions were reviewed against the actual project code, SQL, data outputs, and analytical results before inclusion.

AI assistance was used as an engineering and analytical aid, not as an authoritative source of evidence.

---

## Reproducibility

Pinned Python dependencies are provided in:

```text
requirements.txt
```

The project uses:

- Python
- DuckDB
- Pandas
- GeoPandas
- Plotly
- Streamlit
- Statsmodels
- SciPy

The primary analytical warehouse is generated from the project's ingestion and SQL transformation pipeline.

---

## Important Analytical Limitations

MetroPulse is an **observational mobility analytics project**.

The available historical data does not directly observe:

- Vehicle supply
- Unmet demand
- Passenger wait time
- Driver acceptance / rejection
- Treatment / control assignment

Therefore, historical relationships are not presented as causal effects.

In particular:

- Demand patterns describe observed taxi activity rather than unmet demand.
- Weather relationships are descriptive associations.
- Transit relationships are interpreted after accounting for temporal structure where applicable.
- Predictive model performance does not establish causal relationships.
- Rare weather categories have limited evidence bases.
- Data-quality issue flags may overlap across trips.

The two operational recommendations are proposed as experiments precisely because causal impact must be measured prospectively.

---

## Final Submission Artifacts

The final submission should include:

- Public GitHub repository
- Deployed Streamlit dashboard
- Executive decision memo
- Metric dictionary
- AI usage disclosure
- Reproducible rebuild instructions
- Statistical analysis outputs
- Final Git commit SHA
- Demonstration video

---

## Project Principle

> **Use historical mobility data to identify where an operational decision is worth testing — not to pretend that observational data has already proven the intervention works.**