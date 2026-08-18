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

con = duckdb.connect()

BASE_FILTER = """
    tpep_pickup_datetime >= TIMESTAMP '2024-04-01'
    AND tpep_pickup_datetime < TIMESTAMP '2024-07-01'
"""


print("=" * 90)
print("METROPULSE — TAXI QUALITY IMPACT ANALYSIS")
print("=" * 90)


# -------------------------------------------------------------------
# 1. Overlap between temporal anomalies
# -------------------------------------------------------------------

print("\n1. TEMPORAL ANOMALY OVERLAP")
print("-" * 90)

con.sql(
    f"""
    SELECT
        COUNT(*) FILTER (
            WHERE tpep_dropoff_datetime < tpep_pickup_datetime
        ) AS negative_duration,

        COUNT(*) FILTER (
            WHERE tpep_dropoff_datetime = tpep_pickup_datetime
        ) AS zero_duration,

        COUNT(*) FILTER (
            WHERE DATE_DIFF(
                'second',
                tpep_pickup_datetime,
                tpep_dropoff_datetime
            ) > 24 * 60 * 60
        ) AS over_24h,

        COUNT(*) FILTER (
            WHERE
                tpep_dropoff_datetime < tpep_pickup_datetime
                AND tpep_dropoff_datetime = tpep_pickup_datetime
        ) AS impossible_overlap

    FROM read_parquet('{TAXI_PATTERN}')
    WHERE {BASE_FILTER}
    """
).show()


# -------------------------------------------------------------------
# 2. Distance anomaly impact
# -------------------------------------------------------------------

print("\n2. DISTANCE ANOMALY IMPACT")
print("-" * 90)

con.sql(
    f"""
    SELECT

        COUNT(*) AS total_trips,

        SUM(trip_distance) AS total_distance,

        COUNT(*) FILTER (
            WHERE trip_distance = 0
        ) AS zero_distance_trips,

        SUM(trip_distance) FILTER (
            WHERE trip_distance = 0
        ) AS zero_distance_amount,

        COUNT(*) FILTER (
            WHERE trip_distance > 100
        ) AS over_100_mile_trips,

        SUM(trip_distance) FILTER (
            WHERE trip_distance > 100
        ) AS over_100_mile_distance,

        COUNT(*) FILTER (
            WHERE trip_distance > 500
        ) AS over_500_mile_trips,

        SUM(trip_distance) FILTER (
            WHERE trip_distance > 500
        ) AS over_500_mile_distance

    FROM read_parquet('{TAXI_PATTERN}')
    WHERE {BASE_FILTER}
    """
).show()


# -------------------------------------------------------------------
# 3. Fare anomaly impact
# -------------------------------------------------------------------

print("\n3. FARE ANOMALY IMPACT")
print("-" * 90)

con.sql(
    f"""
    SELECT

        COUNT(*) AS total_trips,

        SUM(fare_amount) AS gross_fare_amount,

        SUM(total_amount) AS gross_total_amount,

        COUNT(*) FILTER (
            WHERE fare_amount < 0
        ) AS negative_fare_trips,

        SUM(fare_amount) FILTER (
            WHERE fare_amount < 0
        ) AS negative_fare_value,

        COUNT(*) FILTER (
            WHERE total_amount < 0
        ) AS negative_total_trips,

        SUM(total_amount) FILTER (
            WHERE total_amount < 0
        ) AS negative_total_value,

        COUNT(*) FILTER (
            WHERE fare_amount = 0
        ) AS zero_fare_trips,

        SUM(total_amount) FILTER (
            WHERE fare_amount = 0
        ) AS zero_fare_total_value,

        COUNT(*) FILTER (
            WHERE total_amount = 0
        ) AS zero_total_trips

    FROM read_parquet('{TAXI_PATTERN}')
    WHERE {BASE_FILTER}
    """
).show()


# -------------------------------------------------------------------
# 4. Passenger anomaly impact
# -------------------------------------------------------------------

print("\n4. PASSENGER ANOMALY IMPACT")
print("-" * 90)

con.sql(
    f"""
    SELECT

        COUNT(*) AS total_trips,

        COUNT(*) FILTER (
            WHERE passenger_count IS NULL
        ) AS null_passengers,

        COUNT(*) FILTER (
            WHERE passenger_count = 0
        ) AS zero_passengers,

        COUNT(*) FILTER (
            WHERE passenger_count > 6
        ) AS passengers_over_6,

        AVG(passenger_count) FILTER (
            WHERE passenger_count IS NOT NULL
        ) AS avg_non_null_passengers,

        SUM(total_amount) FILTER (
            WHERE passenger_count IS NULL
        ) AS revenue_null_passenger,

        SUM(total_amount) FILTER (
            WHERE passenger_count = 0
        ) AS revenue_zero_passenger

    FROM read_parquet('{TAXI_PATTERN}')
    WHERE {BASE_FILTER}
    """
).show()


# -------------------------------------------------------------------
# 5. Unknown passenger/payment relationship
# -------------------------------------------------------------------

print("\n5. UNKNOWN PASSENGER / PAYMENT RELATIONSHIP")
print("-" * 90)

con.sql(
    f"""
    SELECT

        COUNT(*) FILTER (
            WHERE payment_type = 0
        ) AS payment_zero,

        COUNT(*) FILTER (
            WHERE passenger_count IS NULL
        ) AS passenger_null,

        COUNT(*) FILTER (
            WHERE
                payment_type = 0
                AND passenger_count IS NULL
        ) AS both,

        SUM(total_amount) FILTER (
            WHERE
                payment_type = 0
                AND passenger_count IS NULL
        ) AS total_amount_both

    FROM read_parquet('{TAXI_PATTERN}')
    WHERE {BASE_FILTER}
    """
).show()


# -------------------------------------------------------------------
# 6. Extreme distance records
# -------------------------------------------------------------------

print("\n6. EXTREME DISTANCE RECORDS")
print("-" * 90)

con.sql(
    f"""
    SELECT
        tpep_pickup_datetime,
        tpep_dropoff_datetime,
        trip_distance,
        fare_amount,
        total_amount,
        passenger_count,
        PULocationID,
        DOLocationID,
        payment_type,
        VendorID

    FROM read_parquet('{TAXI_PATTERN}')

    WHERE
        {BASE_FILTER}
        AND trip_distance > 500

    ORDER BY trip_distance DESC

    LIMIT 20
    """
).show()


# -------------------------------------------------------------------
# 7. Extreme fare records
# -------------------------------------------------------------------

print("\n7. EXTREME FARE RECORDS")
print("-" * 90)

con.sql(
    f"""
    SELECT
        tpep_pickup_datetime,
        tpep_dropoff_datetime,
        trip_distance,
        fare_amount,
        total_amount,
        passenger_count,
        PULocationID,
        DOLocationID,
        payment_type,
        VendorID

    FROM read_parquet('{TAXI_PATTERN}')

    WHERE
        {BASE_FILTER}
        AND (
            fare_amount < 0
            OR total_amount < 0
        )

    ORDER BY total_amount

    LIMIT 20
    """
).show()


# -------------------------------------------------------------------
# 8. Invalid temporal records
# -------------------------------------------------------------------

print("\n8. INVALID TEMPORAL RECORDS")
print("-" * 90)

con.sql(
    f"""
    SELECT
        tpep_pickup_datetime,
        tpep_dropoff_datetime,
        DATE_DIFF(
            'second',
            tpep_pickup_datetime,
            tpep_dropoff_datetime
        ) AS duration_seconds,
        trip_distance,
        fare_amount,
        total_amount,
        passenger_count,
        payment_type

    FROM read_parquet('{TAXI_PATTERN}')

    WHERE
        {BASE_FILTER}
        AND (
            tpep_dropoff_datetime < tpep_pickup_datetime
            OR DATE_DIFF(
                'second',
                tpep_pickup_datetime,
                tpep_dropoff_datetime
            ) > 24 * 60 * 60
        )

    ORDER BY duration_seconds

    LIMIT 30
    """
).show()


con.close()