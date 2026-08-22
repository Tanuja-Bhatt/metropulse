import duckdb
from pathlib import Path

DB_PATH = Path("data/metropulse.duckdb")
OUTPUT_PATH = Path("outputs/recommendation_sensitivity.csv")

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(DB_PATH), read_only=True)

query = """
WITH windows AS (

    SELECT * FROM (
        VALUES
            ('14:00-18:00', 14, 18),
            ('15:00-19:00', 15, 19),
            ('16:00-20:00', 16, 20)
    ) AS t(window_name, start_hour, end_hour)

),

window_metrics AS (

    SELECT
        w.window_name,
        w.start_hour,
        w.end_hour,

        AVG(
            CASE
                WHEN h.hour_of_day >= w.start_hour
                 AND h.hour_of_day < w.end_hour
                THEN h.taxi_trip_count
            END
        ) AS peak_window_avg_hourly_trips,

        AVG(
            CASE
                WHEN NOT (
                    h.hour_of_day >= w.start_hour
                    AND h.hour_of_day < w.end_hour
                )
                THEN h.taxi_trip_count
            END
        ) AS outside_window_avg_hourly_trips,

        SUM(
            CASE
                WHEN h.hour_of_day >= w.start_hour
                 AND h.hour_of_day < w.end_hour
                THEN h.taxi_trip_count
                ELSE 0
            END
        ) AS window_total_trips,

        COUNT(
            CASE
                WHEN h.hour_of_day >= w.start_hour
                 AND h.hour_of_day < w.end_hour
                THEN 1
            END
        ) AS window_hours

    FROM marts.hourly_mobility_summary h
    CROSS JOIN windows w

    GROUP BY
        w.window_name,
        w.start_hour,
        w.end_hour

)

SELECT
    window_name,
    start_hour,
    end_hour,
    window_hours,
    peak_window_avg_hourly_trips,
    outside_window_avg_hourly_trips,
    window_total_trips,

    100.0 * (
        peak_window_avg_hourly_trips
        - outside_window_avg_hourly_trips
    )
    / NULLIF(outside_window_avg_hourly_trips, 0)
    AS demand_lift_pct

FROM window_metrics

ORDER BY start_hour
"""

df = con.sql(query).df()

df.to_csv(OUTPUT_PATH, index=False)

print("\nRECOMMENDATION SENSITIVITY")
print("=" * 80)
print(df.to_string(index=False))

print("\nSaved:")
print(OUTPUT_PATH)

con.close()