-- =============================================================================
-- METROPULSE — ORIGIN-DESTINATION FLOW
-- =============================================================================
-- Grain:
--   One row per pickup zone × dropoff zone pair.
--
-- Purpose:
--   Reusable OD-flow metrics for:
--   - route demand
--   - geographic flow analysis
--   - top origin-destination pairs
--   - airport flows
--   - dashboard route analysis
-- =============================================================================

CREATE OR REPLACE TABLE intermediate.od_flow AS

SELECT
    pickup_location_id,
    dropoff_location_id,

    COUNT(*) AS trips,

    SUM(
        CASE
            WHEN is_positive_revenue_trip
            THEN total_amount
            ELSE 0
        END
    ) AS total_revenue,

    AVG(
        CASE
            WHEN is_distance_valid
             AND trip_distance > 0
            THEN trip_distance
        END
    ) AS avg_trip_distance,

    AVG(
        CASE
            WHEN trip_duration_minutes IS NOT NULL
            THEN trip_duration_minutes
        END
    ) AS avg_trip_duration_minutes,

    AVG(
        CASE
            WHEN total_amount IS NOT NULL
             AND is_revenue_valid
            THEN total_amount
        END
    ) AS avg_total_amount,

    AVG(
        CASE
            WHEN fare_per_mile IS NOT NULL
            THEN fare_per_mile
        END
    ) AS avg_fare_per_mile,

    SUM(
        CASE
            WHEN is_airport_trip
            THEN 1
            ELSE 0
        END
    ) AS airport_trips,

    SUM(
        CASE
            WHEN is_tipped
            THEN 1
            ELSE 0
        END
    ) AS tipped_trips

FROM intermediate.trip_metrics

GROUP BY
    pickup_location_id,
    dropoff_location_id;