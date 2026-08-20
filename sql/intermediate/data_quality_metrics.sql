-- =============================================================================
-- METROPULSE — DATA QUALITY METRICS
-- =============================================================================
-- Grain:
--   One row containing warehouse-level data-quality metrics.
--
-- Purpose:
--   Quantify:
--   - source completeness
--   - trip-level validity
--   - zone mapping quality
--   - temporal coverage
--   - weather/subway coverage
--   - financial anomalies
--   - passenger anomalies
--   - derived metric availability
--
-- Important:
--   This table does NOT modify or remove bad records.
--   It measures them.
-- =============================================================================

CREATE OR REPLACE TABLE intermediate.data_quality_metrics AS

WITH

-- =============================================================================
-- SOURCE COUNTS
-- =============================================================================

source_counts AS (

    SELECT
        (
            SELECT COUNT(*)
            FROM staging.taxi_trips
        ) AS staging_taxi_rows,

        (
            SELECT COUNT(*)
            FROM intermediate.taxi_trips_clean
        ) AS clean_taxi_rows,

        (
            SELECT COUNT(*)
            FROM intermediate.trip_metrics
        ) AS trip_metric_rows,

        (
            SELECT COUNT(*)
            FROM staging.taxi_zones
        ) AS taxi_zone_rows,

        (
            SELECT COUNT(*)
            FROM intermediate.hourly_spine
        ) AS hourly_spine_rows

),

-- =============================================================================
-- TRIP-LEVEL QUALITY
-- =============================================================================

trip_quality AS (

    SELECT

        COUNT(*) AS total_trips,

        -- -------------------------------------------------------------
        -- Pickup/dropoff zone completeness
        -- -------------------------------------------------------------

        SUM(
            CASE
                WHEN is_missing_pickup_zone
                THEN 1
                ELSE 0
            END
        ) AS missing_pickup_zone_trips,

        SUM(
            CASE
                WHEN is_missing_dropoff_zone
                THEN 1
                ELSE 0
            END
        ) AS missing_dropoff_zone_trips,

        -- -------------------------------------------------------------
        -- Duration quality
        -- -------------------------------------------------------------

        SUM(
            CASE
                WHEN NOT is_duration_valid
                THEN 1
                ELSE 0
            END
        ) AS invalid_duration_trips,

    
    SUM(
    CASE
        WHEN trip_duration_minutes IS NULL
        THEN 1
        ELSE 0
    END
) AS missing_valid_duration_metric_trips,
        SUM(
            CASE
                WHEN trip_duration_minutes IS NOT NULL
                THEN 1
                ELSE 0
            END
        ) AS valid_duration_metric_trips,

        -- -------------------------------------------------------------
        -- Distance quality
        -- -------------------------------------------------------------

        SUM(
            CASE
                WHEN NOT is_distance_valid
                THEN 1
                ELSE 0
            END
        ) AS invalid_distance_trips,

        SUM(
            CASE
                WHEN trip_distance IS NULL
                  OR trip_distance <= 0
                THEN 1
                ELSE 0
            END
        ) AS non_positive_distance_trips,

        SUM(
            CASE
                WHEN trip_speed_mph IS NOT NULL
                THEN 1
                ELSE 0
            END
        ) AS valid_speed_metric_trips,

        -- -------------------------------------------------------------
        -- Revenue quality
        -- -------------------------------------------------------------

        SUM(
            CASE
                WHEN NOT is_revenue_valid
                THEN 1
                ELSE 0
            END
        ) AS invalid_revenue_trips,

        SUM(
            CASE
                WHEN is_missing_fare
                THEN 1
                ELSE 0
            END
        ) AS missing_fare_trips,

        SUM(
            CASE
                WHEN is_negative_fare
                THEN 1
                ELSE 0
            END
        ) AS negative_fare_trips,

        SUM(
            CASE
                WHEN is_zero_fare
                THEN 1
                ELSE 0
            END
        ) AS zero_fare_trips,

        SUM(
            CASE
                WHEN is_missing_total
                THEN 1
                ELSE 0
            END
        ) AS missing_total_trips,

        SUM(
            CASE
                WHEN is_negative_total
                THEN 1
                ELSE 0
            END
        ) AS negative_total_trips,

        SUM(
            CASE
                WHEN is_zero_total
                THEN 1
                ELSE 0
            END
        ) AS zero_total_trips,

        -- -------------------------------------------------------------
        -- Passenger quality
        -- -------------------------------------------------------------

        SUM(
            CASE
                WHEN NOT is_passenger_valid
                THEN 1
                ELSE 0
            END
        ) AS invalid_passenger_trips,

        SUM(
            CASE
                WHEN is_unknown_passenger
                THEN 1
                ELSE 0
            END
        ) AS unknown_passenger_trips,

        SUM(
            CASE
                WHEN is_zero_passenger
                THEN 1
                ELSE 0
            END
        ) AS zero_passenger_trips,

        SUM(
            CASE
                WHEN is_high_passenger_count
                THEN 1
                ELSE 0
            END
        ) AS high_passenger_trips,

        -- -------------------------------------------------------------
        -- Payment quality
        -- -------------------------------------------------------------

        SUM(
            CASE
                WHEN is_unknown_payment
                THEN 1
                ELSE 0
            END
        ) AS unknown_payment_trips,

        -- -------------------------------------------------------------
        -- Derived metric completeness
        -- -------------------------------------------------------------

        SUM(
            CASE
                WHEN fare_per_mile IS NOT NULL
                THEN 1
                ELSE 0
            END
        ) AS valid_fare_per_mile_trips,

        SUM(
            CASE
                WHEN total_amount_per_mile IS NOT NULL
                THEN 1
                ELSE 0
            END
        ) AS valid_total_per_mile_trips,

        SUM(
            CASE
                WHEN tip_percentage IS NOT NULL
                THEN 1
                ELSE 0
            END
        ) AS valid_tip_percentage_trips

    FROM intermediate.trip_metrics

),

-- =============================================================================
-- HOURLY COVERAGE
-- =============================================================================

hourly_quality AS (

    SELECT

        COUNT(*) AS hourly_rows,

        COUNT(DISTINCT pickup_hour) AS unique_hours,

        MIN(pickup_hour) AS earliest_hour,

        MAX(pickup_hour) AS latest_hour,

        SUM(
            CASE
                WHEN temperature_2m IS NULL
                  OR relative_humidity_2m IS NULL
                  OR precipitation IS NULL
                  OR wind_speed_10m IS NULL
                  OR cloud_cover IS NULL
                THEN 1
                ELSE 0
            END
        ) AS incomplete_weather_hours,

        SUM(
            CASE
                WHEN subway_ridership IS NULL
                THEN 1
                ELSE 0
            END
        ) AS missing_subway_hours,

        SUM(
            CASE
                WHEN taxi_trip_count IS NULL
                THEN 1
                ELSE 0
            END
        ) AS missing_taxi_demand_hours

    FROM marts.hourly_mobility_summary

),

-- =============================================================================
-- ZONE QUALITY
-- =============================================================================

zone_quality AS (

    SELECT

        COUNT(*) AS zone_rows,

        COUNT(DISTINCT location_id) AS unique_zone_locations,

        SUM(
            CASE
                WHEN zone IS NULL
                THEN 1
                ELSE 0
            END
        ) AS missing_zone_names,

        SUM(
            CASE
                WHEN service_zone IS NULL
                THEN 1
                ELSE 0
            END
        ) AS missing_service_zones

    FROM intermediate.zone_performance

),

-- =============================================================================
-- OD QUALITY
-- =============================================================================

od_quality AS (

    SELECT

        COUNT(*) AS od_rows,

        COUNT(*) AS unique_od_pairs,

        SUM(trips) AS od_trip_total,

        SUM(
            CASE
                WHEN trips <= 0
                THEN 1
                ELSE 0
            END
        ) AS invalid_od_rows

    FROM intermediate.od_flow

),

-- =============================================================================
-- COMBINE ALL QUALITY METRICS
-- =============================================================================

combined AS (

    SELECT
        s.*,
        t.*,
        h.*,
        z.*,
        o.*

    FROM source_counts s

    CROSS JOIN trip_quality t

    CROSS JOIN hourly_quality h

    CROSS JOIN zone_quality z

    CROSS JOIN od_quality o

)

SELECT
    *,

    -- =========================================================================
    -- Completeness percentages
    -- =========================================================================

    CASE
        WHEN total_trips > 0
        THEN 100.0
             * (total_trips - missing_pickup_zone_trips)
             / total_trips
        ELSE NULL
    END AS pickup_zone_completeness_pct,

    CASE
        WHEN total_trips > 0
        THEN 100.0
             * (total_trips - missing_dropoff_zone_trips)
             / total_trips
        ELSE NULL
    END AS dropoff_zone_completeness_pct,

    CASE
        WHEN total_trips > 0
        THEN 100.0
             * (total_trips - invalid_duration_trips)
             / total_trips
        ELSE NULL
    END AS duration_validity_pct,

    CASE
        WHEN total_trips > 0
        THEN 100.0
             * (total_trips - invalid_distance_trips)
             / total_trips
        ELSE NULL
    END AS distance_validity_pct,

    CASE
        WHEN total_trips > 0
        THEN 100.0
             * (total_trips - invalid_revenue_trips)
             / total_trips
        ELSE NULL
    END AS revenue_validity_pct,

    CASE
        WHEN total_trips > 0
        THEN 100.0
             * (total_trips - invalid_passenger_trips)
             / total_trips
        ELSE NULL
    END AS passenger_validity_pct,

    CASE
        WHEN hourly_rows > 0
        THEN 100.0
             * (hourly_rows - incomplete_weather_hours)
             / hourly_rows
        ELSE NULL
    END AS weather_completeness_pct,

    CASE
        WHEN hourly_rows > 0
        THEN 100.0
             * (hourly_rows - missing_subway_hours)
             / hourly_rows
        ELSE NULL
    END AS subway_completeness_pct,

    -- =========================================================================
    -- Overall warehouse status
    -- =========================================================================

    CASE
        WHEN staging_taxi_rows = clean_taxi_rows
         AND clean_taxi_rows = trip_metric_rows
         AND missing_pickup_zone_trips = 0
         AND missing_dropoff_zone_trips = 0
         AND incomplete_weather_hours = 0
         AND missing_subway_hours = 0
         AND invalid_od_rows = 0
        THEN 'PASS'

        ELSE 'REVIEW'
    END AS warehouse_quality_status

FROM combined;