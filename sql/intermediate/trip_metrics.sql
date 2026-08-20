-- =============================================================================
-- METROPULSE — TRIP-LEVEL ANALYTICAL METRICS
-- =============================================================================
-- Grain:
--   One row per cleaned taxi trip.
--
-- Purpose:
--   Reusable trip-level metrics for:
--   - trip economics
--   - fare analysis
--   - tipping
--   - payment behavior
--   - airport analysis
--   - duration / distance / speed analysis
--   - downstream geographic and dashboard models
--
-- Important:
--   Existing data-quality flags from taxi_trips_clean are preserved.
--   Derived ratios are NULL when their underlying inputs are invalid.
-- =============================================================================

CREATE OR REPLACE TABLE intermediate.trip_metrics AS

WITH base AS (

    SELECT
        vendor_id,
        pickup_datetime,
        dropoff_datetime,

        passenger_count,
        trip_distance,

        rate_code_id,
        store_and_fwd_flag,

        pickup_location_id,
        dropoff_location_id,

        payment_type,
        payment_type_label,

        fare_amount,
        extra,
        mta_tax,
        tip_amount,
        tolls_amount,
        improvement_surcharge,
        total_amount,
        congestion_surcharge,
        airport_fee,

        is_missing_pickup_zone,
        is_missing_dropoff_zone,

        is_duration_valid,
        is_distance_valid,
        is_revenue_valid,
        is_passenger_valid,

        duration_quality,
        distance_quality,
        revenue_quality,

        is_missing_fare,
        is_negative_fare,
        is_zero_fare,

        is_missing_total,
        is_negative_total,
        is_zero_total,

        is_unknown_passenger,
        is_zero_passenger,
        is_high_passenger_count,
        is_unknown_payment

    FROM intermediate.taxi_trips_clean

),

derived AS (

    SELECT
        *,

        -- =============================================================
        -- Duration validity
        -- =============================================================
        -- The existing is_duration_valid flag is preserved, but a
        -- positive chronological duration is required for calculations.
        -- =============================================================

        CASE
            WHEN pickup_datetime IS NOT NULL
             AND dropoff_datetime IS NOT NULL
             AND dropoff_datetime > pickup_datetime
            THEN TRUE
            ELSE FALSE
        END AS has_positive_duration,

        -- =============================================================
        -- Trip duration
        -- =============================================================

        CASE
            WHEN is_duration_valid
             AND pickup_datetime IS NOT NULL
             AND dropoff_datetime IS NOT NULL
             AND dropoff_datetime > pickup_datetime
            THEN EXTRACT(
                EPOCH FROM (dropoff_datetime - pickup_datetime)
            ) / 60.0
            ELSE NULL
        END AS trip_duration_minutes,

        -- =============================================================
        -- Trip speed
        -- =============================================================
        -- Requires:
        --   valid distance
        --   positive duration
        -- =============================================================

        CASE
            WHEN is_distance_valid
             AND trip_distance >= 0
             AND is_duration_valid
             AND pickup_datetime IS NOT NULL
             AND dropoff_datetime IS NOT NULL
             AND dropoff_datetime > pickup_datetime
            THEN trip_distance /
                 (
                    EXTRACT(
                        EPOCH FROM (dropoff_datetime - pickup_datetime)
                    ) / 3600.0
                 )
            ELSE NULL
        END AS trip_speed_mph,

        -- =============================================================
        -- Fare per mile
        -- =============================================================

        CASE
            WHEN is_distance_valid
             AND trip_distance > 0
             AND is_revenue_valid
            THEN fare_amount / trip_distance
            ELSE NULL
        END AS fare_per_mile,

        -- =============================================================
        -- Total amount per mile
        -- =============================================================

        CASE
            WHEN is_distance_valid
             AND trip_distance > 0
             AND is_revenue_valid
            THEN total_amount / trip_distance
            ELSE NULL
        END AS total_amount_per_mile,

        -- =============================================================
        -- Total amount per minute
        -- =============================================================

        CASE
            WHEN is_revenue_valid
             AND is_duration_valid
             AND pickup_datetime IS NOT NULL
             AND dropoff_datetime IS NOT NULL
             AND dropoff_datetime > pickup_datetime
            THEN total_amount /
                 (
                    EXTRACT(
                        EPOCH FROM (dropoff_datetime - pickup_datetime)
                    ) / 60.0
                 )
            ELSE NULL
        END AS total_amount_per_minute,

        -- =============================================================
        -- Tip percentage
        -- =============================================================
        -- Tip percentage is measured against fare amount.
        -- Invalid/zero fares produce NULL rather than an artificial
        -- percentage.
        -- =============================================================

        CASE
            WHEN is_revenue_valid
             AND fare_amount > 0
             AND tip_amount >= 0
            THEN tip_amount / fare_amount
            ELSE NULL
        END AS tip_percentage,

        -- =============================================================
        -- Tipped-trip indicator
        -- =============================================================

        CASE
            WHEN tip_amount > 0
            THEN TRUE
            ELSE FALSE
        END AS is_tipped,

        -- =============================================================
        -- Airport pickup
        --
        -- 132 = JFK Airport
        -- 138 = LaGuardia Airport
        -- =============================================================

        CASE
            WHEN pickup_location_id IN (132, 138)
            THEN TRUE
            ELSE FALSE
        END AS is_airport_pickup,

        -- =============================================================
        -- Airport dropoff
        -- =============================================================

        CASE
            WHEN dropoff_location_id IN (132, 138)
            THEN TRUE
            ELSE FALSE
        END AS is_airport_dropoff,

        -- =============================================================
        -- Any airport involvement
        -- =============================================================

        CASE
            WHEN pickup_location_id IN (132, 138)
              OR dropoff_location_id IN (132, 138)
            THEN TRUE
            ELSE FALSE
        END AS is_airport_trip,

        -- =============================================================
        -- Airport trip direction
        -- =============================================================

        CASE
            WHEN pickup_location_id IN (132, 138)
             AND dropoff_location_id IN (132, 138)
            THEN 'Airport to Airport'

            WHEN pickup_location_id IN (132, 138)
            THEN 'Airport Pickup'

            WHEN dropoff_location_id IN (132, 138)
            THEN 'Airport Dropoff'

            ELSE 'Non-Airport'
        END AS airport_trip_type,

        -- =============================================================
        -- Positive revenue indicator
        -- =============================================================

        CASE
            WHEN is_revenue_valid
             AND total_amount > 0
            THEN TRUE
            ELSE FALSE
        END AS is_positive_revenue_trip

    FROM base

)

SELECT
    *
FROM derived;