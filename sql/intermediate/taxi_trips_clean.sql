CREATE OR REPLACE TABLE intermediate.taxi_trips_clean AS

WITH base AS (

    SELECT
        VendorID AS vendor_id,

        tpep_pickup_datetime AS pickup_datetime,
        tpep_dropoff_datetime AS dropoff_datetime,

        passenger_count,

        trip_distance,

        RatecodeID AS rate_code_id,

        store_and_fwd_flag,

        PULocationID AS pickup_location_id,
        DOLocationID AS dropoff_location_id,

        payment_type,

        fare_amount,
        extra,
        mta_tax,
        tip_amount,
        tolls_amount,
        improvement_surcharge,
        total_amount,
        congestion_surcharge,
        Airport_fee AS airport_fee

    FROM staging.taxi_trips
),

derived AS (

    SELECT

        *,

        DATE_TRUNC(
            'hour',
            pickup_datetime
        ) AS pickup_hour,

        CAST(
            pickup_datetime AS DATE
        ) AS pickup_date,

        EXTRACT(
            HOUR FROM pickup_datetime
        ) AS pickup_hour_of_day,

        EXTRACT(
            DOW FROM pickup_datetime
        ) AS pickup_day_of_week,

        DATE_TRUNC(
            'week',
            pickup_datetime
        ) AS pickup_week,

        DATE_TRUNC(
            'month',
            pickup_datetime
        ) AS pickup_month,

        DATE_DIFF(
            'second',
            pickup_datetime,
            dropoff_datetime
        ) AS duration_seconds

    FROM base
),

flagged AS (

    SELECT

        *,

        -- ---------------------------------------------------------
        -- Temporal quality flags
        -- ---------------------------------------------------------

        pickup_datetime IS NULL
            AS is_missing_pickup_datetime,

        dropoff_datetime IS NULL
            AS is_missing_dropoff_datetime,

        dropoff_datetime < pickup_datetime
            AS is_negative_duration,

        dropoff_datetime = pickup_datetime
            AS is_zero_duration,

        duration_seconds > 86400
            AS is_long_duration,

        -- ---------------------------------------------------------
        -- Distance quality flags
        -- ---------------------------------------------------------

        trip_distance IS NULL
            AS is_missing_distance,

        trip_distance = 0
            AS is_zero_distance,

        trip_distance < 0
            AS is_negative_distance,

        trip_distance > 100
            AS is_extreme_distance,

        -- ---------------------------------------------------------
        -- Financial quality flags
        -- ---------------------------------------------------------

        fare_amount IS NULL
            AS is_missing_fare,

        fare_amount < 0
            AS is_negative_fare,

        fare_amount = 0
            AS is_zero_fare,

        total_amount IS NULL
            AS is_missing_total,

        total_amount < 0
            AS is_negative_total,

        total_amount = 0
            AS is_zero_total,

        -- ---------------------------------------------------------
        -- Passenger quality flags
        -- ---------------------------------------------------------

        passenger_count IS NULL
            AS is_unknown_passenger,

        passenger_count = 0
            AS is_zero_passenger,

        passenger_count > 6
            AS is_high_passenger_count,

        -- ---------------------------------------------------------
        -- Payment quality
        -- ---------------------------------------------------------

        payment_type = 0
            AS is_unknown_payment,

        -- ---------------------------------------------------------
        -- Referential integrity
        -- ---------------------------------------------------------

        pickup_location_id IS NULL
            AS is_missing_pickup_zone,

        dropoff_location_id IS NULL
            AS is_missing_dropoff_zone

    FROM derived
)

SELECT

    *,

    -- -------------------------------------------------------------
    -- Metric-specific validity
    -- -------------------------------------------------------------

    NOT (
        is_missing_pickup_datetime
        OR is_missing_dropoff_datetime
        OR is_negative_duration
        OR is_long_duration
    ) AS is_duration_valid,

    NOT (
        is_missing_distance
        OR is_negative_distance
        OR is_zero_distance
        OR is_extreme_distance
    ) AS is_distance_valid,

    NOT (
        is_missing_total
        OR is_negative_total
    ) AS is_revenue_valid,

    
    NOT (
    is_unknown_passenger
    OR is_zero_passenger
) AS is_passenger_valid,

    CASE payment_type
        WHEN 1 THEN 'Credit Card'
        WHEN 2 THEN 'Cash'
        WHEN 3 THEN 'No Charge'
        WHEN 4 THEN 'Dispute'
        WHEN 5 THEN 'Unknown'
        ELSE 'Unknown'
    END AS payment_type_label,

    CASE
        WHEN is_negative_duration THEN 'Negative Duration'
        WHEN is_long_duration THEN 'Over 24 Hours'
        WHEN is_zero_duration THEN 'Zero Duration'
        ELSE 'Valid Duration'
    END AS duration_quality,

    CASE
        WHEN is_negative_distance THEN 'Negative Distance'
        WHEN is_extreme_distance THEN 'Extreme Distance'
        WHEN is_zero_distance THEN 'Zero Distance'
        ELSE 'Valid Distance'
    END AS distance_quality,

    CASE
        WHEN is_negative_total THEN 'Negative Total'
        WHEN is_zero_total THEN 'Zero Total'
        ELSE 'Valid Revenue'
    END AS revenue_quality

FROM flagged;