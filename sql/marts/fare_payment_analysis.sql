-- =============================================================================
-- METROPULSE — FARE / PAYMENT ANALYSIS MART
-- =============================================================================
-- Grain:
--   One row per payment type.
--
-- Purpose:
--   Fare economics, payment behavior, tipping and distribution analysis.
-- =============================================================================

CREATE OR REPLACE TABLE marts.fare_payment_analysis AS

WITH trip AS (

    SELECT

        payment_type,

        payment_type_label,

        COUNT(*) AS trips,

        SUM(passenger_count) AS passengers,

        SUM(fare_amount) AS fare_amount,

        SUM(total_amount) AS total_amount,

        SUM(trip_distance)
            FILTER (
                WHERE is_distance_valid
            ) AS total_distance,

        SUM(trip_duration_minutes)
            FILTER (
                WHERE is_duration_valid
            ) AS total_duration_minutes,

        AVG(fare_amount) AS avg_fare,

        MEDIAN(fare_amount) AS median_fare,

        AVG(total_amount) AS avg_amount,

        MEDIAN(total_amount) AS median_amount,

        STDDEV_SAMP(total_amount) AS amount_stddev,

        AVG(
            CASE
                WHEN trip_distance > 0
                THEN fare_amount / trip_distance
            END
        ) AS avg_fare_per_mile,

        AVG(
            CASE
                WHEN trip_duration_minutes > 0
                THEN total_amount / trip_duration_minutes
            END
        ) AS avg_amount_per_minute,

        AVG(trip_distance) AS avg_distance,

        AVG(trip_duration_minutes) AS avg_duration_minutes,

        AVG(trip_speed_mph) AS avg_speed_mph,

        SUM(
            CASE
                WHEN is_tipped
                THEN 1
                ELSE 0
            END
        ) AS tipped_trips,

        AVG(tip_percentage) AS avg_tip_percentage,

        MEDIAN(tip_percentage) AS median_tip_percentage,

        SUM(tip_amount) AS total_tips,

        SUM(
            CASE
                WHEN is_airport_trip
                THEN 1
                ELSE 0
            END
        ) AS airport_trips

    FROM intermediate.trip_metrics

    GROUP BY
        payment_type,
        payment_type_label

),

market AS (

    SELECT
        SUM(trips) AS market_trips,
        SUM(total_amount) AS market_amount
    FROM trip

)

SELECT

    t.*,

    100.0 * t.trips
        / NULLIF(m.market_trips, 0)
        AS trip_share_pct,

    100.0 * t.total_amount
        / NULLIF(m.market_amount, 0)
        AS amount_share_pct,

    100.0 * t.tipped_trips
        / NULLIF(t.trips, 0)
        AS tipping_rate_pct,

    100.0 * t.airport_trips
        / NULLIF(t.trips, 0)
        AS airport_share_pct

FROM trip t

CROSS JOIN market m;