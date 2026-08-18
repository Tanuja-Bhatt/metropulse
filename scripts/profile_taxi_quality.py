from pathlib import Path
import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TAXI_DIR = PROJECT_ROOT / "data" / "raw" / "taxi"

TAXI_PATTERN = str(
    TAXI_DIR / "yellow_tripdata_2024-*.parquet"
)


con = duckdb.connect()


print("=" * 80)
print("METROPULSE — TAXI DATA QUALITY RECONNAISSANCE")
print("=" * 80)


# -------------------------------------------------------------------
# 1. Required-period population
# -------------------------------------------------------------------

print("\n1. REQUIRED PERIOD")
print("-" * 80)

con.sql(
    f"""
    SELECT
        COUNT(*) AS total_source_rows,

        COUNT(*) FILTER (
            WHERE
                tpep_pickup_datetime >= TIMESTAMP '2024-04-01'
                AND tpep_pickup_datetime < TIMESTAMP '2024-07-01'
        ) AS in_scope_rows,

        COUNT(*) FILTER (
            WHERE
                tpep_pickup_datetime < TIMESTAMP '2024-04-01'
                OR tpep_pickup_datetime >= TIMESTAMP '2024-07-01'
        ) AS out_of_scope_rows

    FROM read_parquet('{TAXI_PATTERN}')
    """
).show()


# -------------------------------------------------------------------
# 2. Temporal validity
# -------------------------------------------------------------------

print("\n2. TEMPORAL VALIDITY")
print("-" * 80)

con.sql(
    f"""
    SELECT

        COUNT(*) AS total_rows,

        COUNT(*) FILTER (
            WHERE tpep_dropoff_datetime < tpep_pickup_datetime
        ) AS negative_duration_rows,

        COUNT(*) FILTER (
            WHERE tpep_dropoff_datetime = tpep_pickup_datetime
        ) AS zero_duration_rows,

        COUNT(*) FILTER (
            WHERE
                DATE_DIFF(
                    'second',
                    tpep_pickup_datetime,
                    tpep_dropoff_datetime
                ) > 24 * 60 * 60
        ) AS duration_over_24h

    FROM read_parquet('{TAXI_PATTERN}')
    WHERE
        tpep_pickup_datetime >= TIMESTAMP '2024-04-01'
        AND tpep_pickup_datetime < TIMESTAMP '2024-07-01'
    """
).show()


# -------------------------------------------------------------------
# 3. Trip distance
# -------------------------------------------------------------------

print("\n3. TRIP DISTANCE")
print("-" * 80)

con.sql(
    f"""
    SELECT

        COUNT(*) AS total_rows,

        COUNT(*) FILTER (
            WHERE trip_distance = 0
        ) AS zero_distance,

        COUNT(*) FILTER (
            WHERE trip_distance < 0
        ) AS negative_distance,

        COUNT(*) FILTER (
            WHERE trip_distance > 100
        ) AS distance_over_100_miles,

        COUNT(*) FILTER (
            WHERE trip_distance > 500
        ) AS distance_over_500_miles,

        MAX(trip_distance) AS max_distance

    FROM read_parquet('{TAXI_PATTERN}')
    WHERE
        tpep_pickup_datetime >= TIMESTAMP '2024-04-01'
        AND tpep_pickup_datetime < TIMESTAMP '2024-07-01'
    """
).show()


# -------------------------------------------------------------------
# 4. Fare anomalies
# -------------------------------------------------------------------

print("\n4. FARE / PAYMENT AMOUNT")
print("-" * 80)

con.sql(
    f"""
    SELECT

        COUNT(*) AS total_rows,

        COUNT(*) FILTER (
            WHERE fare_amount < 0
        ) AS negative_fare,

        COUNT(*) FILTER (
            WHERE fare_amount = 0
        ) AS zero_fare,

        COUNT(*) FILTER (
            WHERE total_amount < 0
        ) AS negative_total,

        COUNT(*) FILTER (
            WHERE total_amount = 0
        ) AS zero_total,

        MIN(fare_amount) AS min_fare,

        MAX(fare_amount) AS max_fare,

        MIN(total_amount) AS min_total,

        MAX(total_amount) AS max_total

    FROM read_parquet('{TAXI_PATTERN}')
    WHERE
        tpep_pickup_datetime >= TIMESTAMP '2024-04-01'
        AND tpep_pickup_datetime < TIMESTAMP '2024-07-01'
    """
).show()


# -------------------------------------------------------------------
# 5. Passenger anomalies
# -------------------------------------------------------------------

print("\n5. PASSENGER COUNT")
print("-" * 80)

con.sql(
    f"""
    SELECT

        COUNT(*) AS total_rows,

        COUNT(*) FILTER (
            WHERE passenger_count IS NULL
        ) AS null_passengers,

        COUNT(*) FILTER (
            WHERE passenger_count = 0
        ) AS zero_passengers,

        COUNT(*) FILTER (
            WHERE passenger_count < 0
        ) AS negative_passengers,

        COUNT(*) FILTER (
            WHERE passenger_count > 6
        ) AS passengers_over_6,

        MIN(passenger_count) AS min_passengers,

        MAX(passenger_count) AS max_passengers

    FROM read_parquet('{TAXI_PATTERN}')
    WHERE
        tpep_pickup_datetime >= TIMESTAMP '2024-04-01'
        AND tpep_pickup_datetime < TIMESTAMP '2024-07-01'
    """
).show()


# -------------------------------------------------------------------
# 6. Payment type
# -------------------------------------------------------------------

print("\n6. PAYMENT TYPE")
print("-" * 80)

con.sql(
    f"""
    SELECT
        payment_type,
        COUNT(*) AS trip_count,
        ROUND(
            100.0 * COUNT(*) /
            SUM(COUNT(*)) OVER (),
            3
        ) AS pct_of_trips
    FROM read_parquet('{TAXI_PATTERN}')
    WHERE
        tpep_pickup_datetime >= TIMESTAMP '2024-04-01'
        AND tpep_pickup_datetime < TIMESTAMP '2024-07-01'
    GROUP BY payment_type
    ORDER BY trip_count DESC
    """
).show()


# -------------------------------------------------------------------
# 7. Vendor
# -------------------------------------------------------------------

print("\n7. VENDOR")
print("-" * 80)

con.sql(
    f"""
    SELECT
        VendorID,
        COUNT(*) AS trip_count,
        ROUND(
            100.0 * COUNT(*) /
            SUM(COUNT(*)) OVER (),
            3
        ) AS pct_of_trips
    FROM read_parquet('{TAXI_PATTERN}')
    WHERE
        tpep_pickup_datetime >= TIMESTAMP '2024-04-01'
        AND tpep_pickup_datetime < TIMESTAMP '2024-07-01'
    GROUP BY VendorID
    ORDER BY trip_count DESC
    """
).show()


# -------------------------------------------------------------------
# 8. Zone validity
# -------------------------------------------------------------------

print("\n8. ZONE IDS")
print("-" * 80)

zone_lookup = str(
    PROJECT_ROOT
    / "data"
    / "raw"
    / "zones"
    / "taxi_zone_lookup.csv"
)

con.sql(
    f"""
    WITH valid_zones AS (
        SELECT DISTINCT
            LocationID
        FROM read_csv_auto('{zone_lookup}')
    ),

    taxi AS (
        SELECT
            PULocationID,
            DOLocationID
        FROM read_parquet('{TAXI_PATTERN}')
        WHERE
            tpep_pickup_datetime >= TIMESTAMP '2024-04-01'
            AND tpep_pickup_datetime < TIMESTAMP '2024-07-01'
    )

    SELECT

        COUNT(*) AS total_rows,

        COUNT(*) FILTER (
            WHERE vpu.LocationID IS NULL
        ) AS invalid_pickup_zone,

        COUNT(*) FILTER (
            WHERE vdo.LocationID IS NULL
        ) AS invalid_dropoff_zone

    FROM taxi t

    LEFT JOIN valid_zones vpu
        ON t.PULocationID = vpu.LocationID

    LEFT JOIN valid_zones vdo
        ON t.DOLocationID = vdo.LocationID
    """
).show()


# -------------------------------------------------------------------
# 9. Unknown passenger count ↔ payment type
# -------------------------------------------------------------------

print("\n9. PASSENGER NULL VS PAYMENT TYPE")
print("-" * 80)

con.sql(
    f"""
    SELECT

        COUNT(*) FILTER (
            WHERE passenger_count IS NULL
        ) AS null_passenger,

        COUNT(*) FILTER (
            WHERE payment_type = 0
        ) AS payment_type_zero,

        COUNT(*) FILTER (
            WHERE
                passenger_count IS NULL
                AND payment_type = 0
        ) AS both

    FROM read_parquet('{TAXI_PATTERN}')
    WHERE
        tpep_pickup_datetime >= TIMESTAMP '2024-04-01'
        AND tpep_pickup_datetime < TIMESTAMP '2024-07-01'
    """
).show()


# -------------------------------------------------------------------
# 10. Duplicate complete rows
# -------------------------------------------------------------------

print("\n10. EXACT DUPLICATE ROWS")
print("-" * 80)

con.sql(
    f"""
    SELECT
        COUNT(*) AS duplicate_rows
    FROM (
        SELECT
            *,
            COUNT(*) OVER (
                PARTITION BY
                    VendorID,
                    tpep_pickup_datetime,
                    tpep_dropoff_datetime,
                    passenger_count,
                    trip_distance,
                    RatecodeID,
                    store_and_fwd_flag,
                    PULocationID,
                    DOLocationID,
                    payment_type,
                    fare_amount,
                    extra,
                    mta_tax,
                    tip_amount,
                    tolls_amount,
                    improvement_surcharge,
                    total_amount,
                    congestion_surcharge,
                    Airport_fee
            ) AS duplicate_count

        FROM read_parquet('{TAXI_PATTERN}')

        WHERE
            tpep_pickup_datetime >= TIMESTAMP '2024-04-01'
            AND tpep_pickup_datetime < TIMESTAMP '2024-07-01'
    )
    WHERE duplicate_count > 1
    """
).show()


con.close()