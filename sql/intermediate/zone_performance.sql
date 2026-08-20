-- =============================================================================
-- METROPULSE — ZONE PERFORMANCE
-- =============================================================================
-- Grain:
--   One row per taxi zone.
--
-- Purpose:
--   Reusable geographic performance metrics for:
--   - demand concentration
--   - revenue concentration
--   - trip economics
--   - airport activity
--   - pickup/dropoff activity
--   - dashboard geographic analysis
-- =============================================================================

CREATE OR REPLACE TABLE intermediate.zone_performance AS

WITH pickup_metrics AS (

    SELECT
        pickup_location_id AS location_id,

        COUNT(*) AS pickup_trips,

        SUM(
            CASE
                WHEN is_positive_revenue_trip
                THEN total_amount
                ELSE 0
            END
        ) AS pickup_revenue,

        AVG(
            CASE
                WHEN trip_duration_minutes IS NOT NULL
                THEN trip_duration_minutes
            END
        ) AS avg_pickup_duration_minutes,

        AVG(
            CASE
                WHEN trip_distance > 0
                 AND is_distance_valid
                THEN trip_distance
            END
        ) AS avg_pickup_distance,

        AVG(
            CASE
                WHEN fare_per_mile IS NOT NULL
                THEN fare_per_mile
            END
        ) AS avg_fare_per_mile,

        SUM(
            CASE
                WHEN is_airport_pickup
                THEN 1
                ELSE 0
            END
        ) AS airport_pickup_trips

    FROM intermediate.trip_metrics

    GROUP BY
        pickup_location_id

),

dropoff_metrics AS (

    SELECT
        dropoff_location_id AS location_id,

        COUNT(*) AS dropoff_trips,

        SUM(
            CASE
                WHEN is_positive_revenue_trip
                THEN total_amount
                ELSE 0
            END
        ) AS dropoff_revenue,

        SUM(
            CASE
                WHEN is_airport_dropoff
                THEN 1
                ELSE 0
            END
        ) AS airport_dropoff_trips

    FROM intermediate.trip_metrics

    GROUP BY
        dropoff_location_id

),

combined AS (

    SELECT
        COALESCE(
            p.location_id,
            d.location_id
        ) AS location_id,

        COALESCE(
            p.pickup_trips,
            0
        ) AS pickup_trips,

        COALESCE(
            d.dropoff_trips,
            0
        ) AS dropoff_trips,

        COALESCE(
            p.pickup_revenue,
            0
        ) AS pickup_revenue,

        COALESCE(
            d.dropoff_revenue,
            0
        ) AS dropoff_revenue,

        p.avg_pickup_duration_minutes,

        p.avg_pickup_distance,

        p.avg_fare_per_mile,

        COALESCE(
            p.airport_pickup_trips,
            0
        ) AS airport_pickup_trips,

        COALESCE(
            d.airport_dropoff_trips,
            0
        ) AS airport_dropoff_trips

    FROM pickup_metrics p

    FULL OUTER JOIN dropoff_metrics d
        ON p.location_id = d.location_id

)

SELECT
    c.*,

    z.zone,
    z.service_zone,

    pickup_trips + dropoff_trips AS total_zone_activity,

    pickup_revenue + dropoff_revenue AS total_zone_revenue,

    CASE
        WHEN pickup_trips + dropoff_trips > 0
        THEN (
            pickup_revenue + dropoff_revenue
        ) / (
            pickup_trips + dropoff_trips
        )
        ELSE NULL
    END AS revenue_per_zone_activity,

    CASE
        WHEN pickup_trips > 0
        THEN airport_pickup_trips::DOUBLE / pickup_trips
        ELSE NULL
    END AS airport_pickup_share,

    CASE
        WHEN dropoff_trips > 0
        THEN airport_dropoff_trips::DOUBLE / dropoff_trips
        ELSE NULL
    END AS airport_dropoff_share

FROM combined c

LEFT JOIN staging.taxi_zones z
    ON c.location_id = z.location_id;