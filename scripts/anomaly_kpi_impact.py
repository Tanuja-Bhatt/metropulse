import duckdb
from pathlib import Path

DB_PATH = Path("data/metropulse.duckdb")
OUTPUT_PATH = Path("outputs/anomaly_kpi_impact.csv")

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(DB_PATH), read_only=True)

query = """
WITH classified AS (

    SELECT
        total_amount,

        CASE
            WHEN COALESCE(is_duration_valid, FALSE)
             AND COALESCE(is_distance_valid, FALSE)
             AND COALESCE(is_revenue_valid, FALSE)
             AND COALESCE(is_passenger_valid, FALSE)
            THEN TRUE
            ELSE FALSE
        END AS is_quality_valid

    FROM intermediate.trip_metrics

),

summary AS (

    SELECT
        'All trips' AS population,

        COUNT(*) AS total_trips,

        SUM(
            CASE
                WHEN total_amount IS NOT NULL
                THEN total_amount
                ELSE 0
            END
        ) AS total_revenue,

        AVG(total_amount) AS avg_amount_per_trip

    FROM classified

    UNION ALL

    SELECT
        'Quality-valid trips' AS population,

        COUNT(*) AS total_trips,

        SUM(
            CASE
                WHEN total_amount IS NOT NULL
                THEN total_amount
                ELSE 0
            END
        ) AS total_revenue,

        AVG(total_amount) AS avg_amount_per_trip

    FROM classified

    WHERE is_quality_valid

),

comparison AS (

    SELECT
        population,
        total_trips,
        total_revenue,
        avg_amount_per_trip,

        100.0 * total_trips
            / NULLIF(
                MAX(
                    CASE
                        WHEN population = 'All trips'
                        THEN total_trips
                    END
                ) OVER (),
                0
            ) AS trip_retention_pct,

        100.0 * total_revenue
            / NULLIF(
                MAX(
                    CASE
                        WHEN population = 'All trips'
                        THEN total_revenue
                    END
                ) OVER (),
                0
            ) AS revenue_retention_pct

    FROM summary

)

SELECT *
FROM comparison
ORDER BY
    CASE
        WHEN population = 'All trips' THEN 1
        ELSE 2
    END
"""

df = con.sql(query).df()

df.to_csv(OUTPUT_PATH, index=False)

print(df.to_string(index=False))

print("\nSaved:")
print(OUTPUT_PATH)

con.close()