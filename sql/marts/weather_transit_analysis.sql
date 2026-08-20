-- =============================================================================
-- METROPULSE — WEATHER / TRANSIT ANALYSIS MART
-- =============================================================================
-- Grain:
--   One row per canonical hour.
--
-- Purpose:
--   Weather effects / associations across:
--   - taxi demand
--   - trip duration
--   - distance
--   - amount
--   - subway ridership
--   - subway transfers
--
-- Important:
--   These are observational associations, not causal estimates.
-- =============================================================================

CREATE OR REPLACE TABLE marts.weather_transit_analysis AS

WITH hourly AS (

    SELECT
        pickup_hour,
        calendar_date,
        hour_of_day,
        day_of_week,
        is_weekend,
        month_start,

        taxi_trip_count,
        taxi_revenue,
        taxi_distance,
        taxi_duration_seconds,

        subway_ridership,
        subway_transfers,

        temperature_2m,
        relative_humidity_2m,
        precipitation,
        rain,
        snowfall,
        weather_code,
        wind_speed_10m,
        cloud_cover

    FROM marts.hourly_mobility_summary

),

classified AS (

    SELECT

        *,

        CASE
            WHEN precipitation IS NULL
                THEN 'Unknown'

            WHEN precipitation = 0
                THEN 'Dry'

            WHEN precipitation < 2.5
                THEN 'Light Rain'

            WHEN precipitation < 7.6
                THEN 'Moderate Rain'

            ELSE 'Heavy Rain'

        END AS precipitation_category,

        CASE
            WHEN temperature_2m < 5
                THEN 'Cold'

            WHEN temperature_2m < 15
                THEN 'Mild'

            WHEN temperature_2m < 25
                THEN 'Warm'

            ELSE 'Hot'

        END AS temperature_category,

        CASE
            WHEN taxi_trip_count > 0
            THEN taxi_revenue / taxi_trip_count
        END AS amount_per_trip,

        CASE
            WHEN taxi_trip_count > 0
            THEN taxi_distance / taxi_trip_count
        END AS distance_per_trip,

        CASE
            WHEN taxi_trip_count > 0
            THEN
                (taxi_duration_seconds / 60.0)
                / taxi_trip_count
        END AS duration_minutes_per_trip,

        CASE
            WHEN taxi_trip_count > 0
            THEN
                subway_ridership::DOUBLE / taxi_trip_count
        END AS subway_to_taxi_ratio

    FROM hourly

)

SELECT

    *,

    AVG(taxi_trip_count) OVER (
        PARTITION BY precipitation_category
    ) AS category_avg_taxi_trips,

    AVG(taxi_revenue) OVER (
        PARTITION BY precipitation_category
    ) AS category_avg_taxi_revenue,

    AVG(distance_per_trip) OVER (
        PARTITION BY precipitation_category
    ) AS category_avg_distance_per_trip,

    AVG(duration_minutes_per_trip) OVER (
        PARTITION BY precipitation_category
    ) AS category_avg_duration_per_trip,

    AVG(amount_per_trip) OVER (
        PARTITION BY precipitation_category
    ) AS category_avg_amount_per_trip,

    AVG(subway_ridership) OVER (
        PARTITION BY precipitation_category
    ) AS category_avg_subway_ridership,

    AVG(subway_transfers) OVER (
        PARTITION BY precipitation_category
    ) AS category_avg_subway_transfers

FROM classified;