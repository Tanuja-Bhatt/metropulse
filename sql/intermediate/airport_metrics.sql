-- =============================================================================
-- METROPULSE — AIRPORT METRICS
-- =============================================================================
-- Grain:
--   One row per airport trip category.
--
-- Purpose:
--   Reusable airport mobility metrics for:
--   - JFK / LaGuardia activity
--   - airport pickup/dropoff demand
--   - airport revenue
--   - airport trip economics
--   - airport vs non-airport comparison
--   - dashboard airport analysis
--
-- Airport zone IDs:
--   132 = JFK Airport
--   138 = LaGuardia Airport
-- =============================================================================

CREATE OR REPLACE TABLE intermediate.airport_metrics AS

WITH airport_classified AS (

    SELECT
        CASE
    WHEN pickup_location_id = 132
     AND dropoff_location_id = 132
    THEN 'JFK to JFK'

    WHEN pickup_location_id = 138
     AND dropoff_location_id = 138
    THEN 'LaGuardia to LaGuardia'

    WHEN pickup_location_id = 132
     AND dropoff_location_id = 138
    THEN 'JFK to LaGuardia'

    WHEN pickup_location_id = 138
     AND dropoff_location_id = 132
    THEN 'LaGuardia to JFK'

    WHEN pickup_location_id = 132
    THEN 'JFK Pickup'

    WHEN dropoff_location_id = 132
    THEN 'JFK Dropoff'

    WHEN pickup_location_id = 138
    THEN 'LaGuardia Pickup'

    WHEN dropoff_location_id = 138
    THEN 'LaGuardia Dropoff'

    ELSE 'Non-Airport'
END AS airport_category,

        *

    FROM intermediate.trip_metrics

),

aggregated AS (

    SELECT
        airport_category,

        COUNT(*) AS total_trips,

        SUM(
            CASE
                WHEN is_revenue_valid
                THEN 1
                ELSE 0
            END
        ) AS valid_revenue_trips,

        SUM(
            CASE
                WHEN is_revenue_valid
                THEN total_amount
                ELSE 0
            END
        ) AS total_revenue,

        SUM(
            CASE
                WHEN is_revenue_valid
                THEN fare_amount
                ELSE 0
            END
        ) AS total_fare_revenue,

        SUM(
            CASE
                WHEN is_revenue_valid
                THEN tip_amount
                ELSE 0
            END
        ) AS total_tip_revenue,

        AVG(
            CASE
                WHEN is_revenue_valid
                THEN total_amount
            END
        ) AS avg_total_amount,

        AVG(
            CASE
                WHEN is_revenue_valid
                THEN fare_amount
            END
        ) AS avg_fare_amount,

        AVG(
            CASE
                WHEN trip_distance IS NOT NULL
                 AND is_distance_valid
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
                WHEN fare_per_mile IS NOT NULL
                THEN fare_per_mile
            END
        ) AS avg_fare_per_mile,

        AVG(
            CASE
                WHEN total_amount_per_mile IS NOT NULL
                THEN total_amount_per_mile
            END
        ) AS avg_total_amount_per_mile,

        SUM(
            CASE
                WHEN is_tipped
                THEN 1
                ELSE 0
            END
        ) AS tipped_trips,

        AVG(
            CASE
                WHEN tip_percentage IS NOT NULL
                THEN tip_percentage
            END
        ) AS avg_tip_percentage,

        SUM(
            CASE
                WHEN passenger_count IS NOT NULL
                THEN passenger_count
                ELSE 0
            END
        ) AS total_passengers,

        AVG(
            CASE
                WHEN passenger_count IS NOT NULL
                 AND passenger_count > 0
                THEN passenger_count
            END
        ) AS avg_passengers

    FROM airport_classified

    GROUP BY
        airport_category

)

SELECT
    *,

    CASE
        WHEN total_trips > 0
        THEN tipped_trips::DOUBLE / total_trips
        ELSE NULL
    END AS tipped_trip_share,

    CASE
        WHEN valid_revenue_trips > 0
        THEN total_revenue / valid_revenue_trips
        ELSE NULL
    END AS revenue_per_valid_trip

FROM aggregated;