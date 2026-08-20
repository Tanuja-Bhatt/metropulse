-- =============================================================================
-- METROPULSE — TEMPORAL DEMAND MART
-- =============================================================================
-- Grain:
--   One row per canonical hour.
--
-- Purpose:
--   Demand timing, peaks, volatility, concentration and weekday/weekend analysis.
-- =============================================================================

CREATE OR REPLACE TABLE marts.temporal_demand AS

WITH base AS (

    SELECT
        pickup_hour,
        calendar_date,
        hour_of_day,
        day_of_week,
        is_weekend,
        week_start,
        month_start,

        taxi_trip_count,
        taxi_revenue,
        taxi_distance,
        taxi_duration_seconds,

        subway_ridership,
        subway_transfers,

        temperature_2m,
        precipitation,
        rain,
        snowfall

    FROM marts.hourly_mobility_summary

),

stats AS (

    SELECT
        AVG(taxi_trip_count) AS overall_avg_hourly_demand,
        STDDEV_SAMP(taxi_trip_count) AS overall_stddev_hourly_demand,
        MAX(taxi_trip_count) AS overall_max_hourly_demand
    FROM base

),

hourly_profile AS (

    SELECT
        hour_of_day,

        AVG(taxi_trip_count) AS avg_hourly_trips,

        MEDIAN(taxi_trip_count) AS median_hourly_trips,

        STDDEV_SAMP(taxi_trip_count) AS stddev_hourly_trips,

        SUM(taxi_trip_count) AS total_trips,

        COUNT(*) AS observations

    FROM base

    GROUP BY hour_of_day

),

daily_profile AS (

    SELECT
        day_of_week,

        is_weekend,

        AVG(taxi_trip_count) AS avg_hourly_trips,

        SUM(taxi_trip_count) AS total_trips,

        COUNT(*) AS observations

    FROM base

    GROUP BY
        day_of_week,
        is_weekend

)

SELECT

    b.*,

    h.avg_hourly_trips AS hour_avg_trips,

    h.median_hourly_trips AS hour_median_trips,

    h.stddev_hourly_trips AS hour_stddev_trips,

    h.total_trips AS hour_total_trips,

    h.observations AS hour_observations,

    d.avg_hourly_trips AS day_avg_trips,

    d.total_trips AS day_total_trips,

    d.observations AS day_observations,

    s.overall_avg_hourly_demand,

    s.overall_stddev_hourly_demand,

    s.overall_max_hourly_demand,

    CASE
        WHEN s.overall_avg_hourly_demand > 0
        THEN
            100.0
            * b.taxi_trip_count
            / s.overall_avg_hourly_demand
        ELSE NULL
    END AS demand_index_pct,

    CASE
        WHEN s.overall_avg_hourly_demand > 0
        THEN
            100.0
            * s.overall_stddev_hourly_demand
            / s.overall_avg_hourly_demand
        ELSE NULL
    END AS overall_demand_cv_pct

FROM base b

LEFT JOIN hourly_profile h
    ON b.hour_of_day = h.hour_of_day

LEFT JOIN daily_profile d
    ON b.day_of_week = d.day_of_week
   AND b.is_weekend = d.is_weekend

CROSS JOIN stats s;