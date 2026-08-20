-- =============================================================================
-- METROPULSE — WEATHER AND MOBILITY METRICS
-- =============================================================================
-- Grain:
--   One row per canonical hour.
--
-- Purpose:
--   Reusable hourly metrics for:
--   - weather conditions
--   - taxi demand
--   - subway ridership
--   - taxi/subway relationship
--   - weather-demand comparison
--   - dashboard weather analysis
--
-- Important:
--   This table is based on the canonical hourly mobility summary.
--   It does not claim that weather causes changes in demand.
-- =============================================================================

CREATE OR REPLACE TABLE intermediate.weather_mobility_metrics AS

SELECT
    pickup_hour,

    -- =============================================================
    -- Calendar / time context
    -- =============================================================

    hour_of_day,
    is_weekend,
    month_start,

    -- =============================================================
    -- Mobility
    -- =============================================================

    taxi_trip_count,
    subway_ridership,
    subway_transfers,

    -- =============================================================
    -- Weather
    -- =============================================================

    temperature_2m,
    relative_humidity_2m,
    precipitation,
    rain,
    wind_speed_10m,
    cloud_cover,

    -- =============================================================
    -- Weather classification
    -- =============================================================

    CASE
        WHEN precipitation IS NULL
        THEN 'Unknown'

        WHEN precipitation = 0
        THEN 'Dry'

        WHEN precipitation <= 1
        THEN 'Light Rain'

        WHEN precipitation <= 5
        THEN 'Moderate Rain'

        ELSE 'Heavy Rain'
    END AS precipitation_category,

    CASE
        WHEN precipitation IS NULL
        THEN NULL

        WHEN precipitation > 0
        THEN TRUE

        ELSE FALSE
    END AS is_raining,

    -- =============================================================
    -- Temperature classification
    -- =============================================================

    CASE
        WHEN temperature_2m IS NULL
        THEN 'Unknown'

        WHEN temperature_2m < 5
        THEN 'Cold'

        WHEN temperature_2m < 15
        THEN 'Cool'

        WHEN temperature_2m < 25
        THEN 'Mild'

        WHEN temperature_2m < 32
        THEN 'Warm'

        ELSE 'Hot'
    END AS temperature_category,

    -- =============================================================
    -- Mobility relationship
    -- =============================================================

    CASE
        WHEN subway_ridership > 0
        THEN taxi_trip_count::DOUBLE / subway_ridership
        ELSE NULL
    END AS taxi_to_subway_ratio,

    CASE
        WHEN subway_ridership > 0
        THEN taxi_trip_count::DOUBLE / subway_ridership
        ELSE NULL
    END AS taxi_subway_demand_ratio,

    -- =============================================================
    -- Weather availability flag
    -- =============================================================

    CASE
        WHEN temperature_2m IS NULL
          OR relative_humidity_2m IS NULL
          OR precipitation IS NULL
          OR wind_speed_10m IS NULL
          OR cloud_cover IS NULL
        THEN FALSE

        ELSE TRUE
    END AS weather_complete

FROM marts.hourly_mobility_summary;