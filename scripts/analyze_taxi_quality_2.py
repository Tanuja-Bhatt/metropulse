from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TAXI_PATTERN = str(
    PROJECT_ROOT
    / "data"
    / "raw"
    / "taxi"
    / "yellow_tripdata_2024-*.parquet"
)

WHERE = """
    tpep_pickup_datetime >= TIMESTAMP '2024-04-01'
    AND tpep_pickup_datetime < TIMESTAMP '2024-07-01'
"""

con = duckdb.connect()


print("=" * 90)
print("METROPULSE — TARGETED TAXI QUALITY ANALYSIS")
print("=" * 90)


# -------------------------------------------------------------------
# A. Financial impact of negative values
# -------------------------------------------------------------------

print("\nA. FINANCIAL IMPACT")
print("-" * 90)

q = f"""
SELECT
    COUNT(*) AS total_trips,

    ROUND(SUM(fare_amount), 2) AS gross_fare,

    ROUND(SUM(total_amount), 2) AS gross_total,

    COUNT(*) FILTER (
        WHERE fare_amount < 0
    ) AS negative_fare_trips,

    ROUND(
        SUM(fare_amount) FILTER (
            WHERE fare_amount < 0
        ), 2
    ) AS negative_fare_value,

    COUNT(*) FILTER (
        WHERE total_amount < 0
    ) AS negative_total_trips,

    ROUND(
        SUM(total_amount) FILTER (
            WHERE total_amount < 0
        ), 2
    ) AS negative_total_value,

    ROUND(
        100.0 *
        ABS(
            SUM(total_amount) FILTER (
                WHERE total_amount < 0
            )
        )
        / SUM(total_amount),
        3
    ) AS negative_total_pct_of_gross

FROM read_parquet('{TAXI_PATTERN}')
WHERE {WHERE}
"""

con.sql(q).show()


# -------------------------------------------------------------------
# B. Extreme distance + unknown passenger/payment
# -------------------------------------------------------------------

print("\nB. EXTREME DISTANCE VS UNKNOWN PASSENGER/PAYMENT")
print("-" * 90)

q = f"""
SELECT
    CASE
        WHEN trip_distance > 500 THEN '>500 miles'
        WHEN trip_distance > 100 THEN '100-500 miles'
        WHEN trip_distance > 50 THEN '50-100 miles'
        ELSE '<=50 miles'
    END AS distance_bucket,

    COUNT(*) AS trips,

    COUNT(*) FILTER (
        WHERE payment_type = 0
    ) AS payment_unknown,

    COUNT(*) FILTER (
        WHERE passenger_count IS NULL
    ) AS passenger_unknown,

    COUNT(*) FILTER (
        WHERE
            payment_type = 0
            AND passenger_count IS NULL
    ) AS both_unknown,

    ROUND(
        AVG(trip_distance), 2
    ) AS avg_distance,

    ROUND(
        SUM(total_amount), 2
    ) AS total_amount

FROM read_parquet('{TAXI_PATTERN}')
WHERE {WHERE}

GROUP BY 1
ORDER BY
    CASE distance_bucket
        WHEN '<=50 miles' THEN 1
        WHEN '50-100 miles' THEN 2
        WHEN '100-500 miles' THEN 3
        WHEN '>500 miles' THEN 4
    END
"""

con.sql(q).show()


# -------------------------------------------------------------------
# C. Zero-distance characteristics
# -------------------------------------------------------------------

print("\nC. ZERO-DISTANCE CHARACTERISTICS")
print("-" * 90)

q = f"""
SELECT
    COUNT(*) AS zero_distance_trips,

    COUNT(*) FILTER (
        WHERE payment_type = 0
    ) AS payment_unknown,

    COUNT(*) FILTER (
        WHERE passenger_count IS NULL
    ) AS passenger_unknown,

    COUNT(*) FILTER (
        WHERE fare_amount < 0
    ) AS negative_fare,

    COUNT(*) FILTER (
        WHERE total_amount < 0
    ) AS negative_total,

    COUNT(*) FILTER (
        WHERE tpep_dropoff_datetime <
              tpep_pickup_datetime
    ) AS negative_duration,

    COUNT(*) FILTER (
        WHERE tpep_dropoff_datetime =
              tpep_pickup_datetime
    ) AS zero_duration,

    ROUND(
        AVG(fare_amount), 2
    ) AS avg_fare,

    ROUND(
        AVG(total_amount), 2
    ) AS avg_total,

    ROUND(
        SUM(total_amount), 2
    ) AS total_amount

FROM read_parquet('{TAXI_PATTERN}')
WHERE
    {WHERE}
    AND trip_distance = 0
"""

con.sql(q).show()


# -------------------------------------------------------------------
# D. Long-duration characteristics
# -------------------------------------------------------------------

print("\nD. LONG-DURATION CHARACTERISTICS")
print("-" * 90)

q = f"""
SELECT
    COUNT(*) AS over_24h_trips,

    COUNT(*) FILTER (
        WHERE trip_distance > 100
    ) AS over_100_mile,

    COUNT(*) FILTER (
        WHERE payment_type = 0
    ) AS payment_unknown,

    COUNT(*) FILTER (
        WHERE passenger_count IS NULL
    ) AS passenger_unknown,

    ROUND(
        AVG(trip_distance), 2
    ) AS avg_distance,

    ROUND(
        AVG(total_amount), 2
    ) AS avg_total_amount,

    ROUND(
        SUM(total_amount), 2
    ) AS total_amount

FROM read_parquet('{TAXI_PATTERN}')
WHERE
    {WHERE}
    AND DATE_DIFF(
        'second',
        tpep_pickup_datetime,
        tpep_dropoff_datetime
    ) > 24 * 60 * 60
"""

con.sql(q).show()


# -------------------------------------------------------------------
# E. Negative-duration characteristics
# -------------------------------------------------------------------

print("\nE. NEGATIVE-DURATION CHARACTERISTICS")
print("-" * 90)

q = f"""
SELECT
    COUNT(*) AS negative_duration_trips,

    COUNT(*) FILTER (
        WHERE payment_type = 0
    ) AS payment_unknown,

    COUNT(*) FILTER (
        WHERE passenger_count IS NULL
    ) AS passenger_unknown,

    COUNT(*) FILTER (
        WHERE trip_distance = 0
    ) AS zero_distance,

    COUNT(*) FILTER (
        WHERE fare_amount < 0
    ) AS negative_fare,

    COUNT(*) FILTER (
        WHERE total_amount < 0
    ) AS negative_total,

    ROUND(
        SUM(total_amount), 2
    ) AS total_amount

FROM read_parquet('{TAXI_PATTERN}')
WHERE
    {WHERE}
    AND tpep_dropoff_datetime < tpep_pickup_datetime
"""

con.sql(q).show()


con.close()