# MetroPulse Architecture

## Objective

MetroPulse is an end-to-end urban mobility intelligence platform for New York City using official public data.

## Data Sources

- NYC TLC Yellow Taxi Trip Records
- NYC TLC Taxi Zone data
- Open-Meteo Historical Weather API
- MTA Subway Hourly Ridership

## Pipeline

Official Public Sources
        ↓
Programmatic Ingestion
        ↓
Immutable Raw Layer
        ↓
DuckDB
        ↓
Staging Models
        ↓
Intermediate Models
        ↓
Analytical Marts
        ↓
Data Quality Tests
        ↓
Statistical Analysis
        ↓
Streamlit Dashboard
        ↓
Business Recommendations

## Core Analytical Layers

### Raw
Original source data preserved without modification.

### Staging
Schema normalization and basic type handling.

### Intermediate
Reusable business and analytical transformations.

### Marts
Dashboard- and analysis-ready datasets.

### Tests
Automated data-quality and reconciliation checks.