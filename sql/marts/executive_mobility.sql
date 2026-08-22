-- =============================================================================
-- METROPULSE — EXECUTIVE MOBILITY MART
-- =============================================================================
-- Grain:
--   One row for the complete analytical period.
--
-- Purpose:
--   Authoritative executive KPI layer for:
--   - total taxi demand
--   - passengers
--   - revenue / amount
--   - distance
--   - duration
--   - fare economics
--   - airport activity
--   - tipping
--   - peak-hour demand
--   - demand volatility
-- =============================================================================

CREATE OR REPLACE TABLE marts.executive_mobility AS

WITH hourly AS (

    SELECT *
    FROM marts.hourly_mobility_summary

),

trip AS (

    SELECT
        COUNT(*) AS total_trips,

        SUM(
            CASE
                WHEN passenger_count IS NOT NULL
                THEN passenger_count
                ELSE 0
            END
        ) AS total_passengers,

        SUM(
            CASE
                WHEN fare_amount IS NOT NULL
                THEN fare_amount
                ELSE 0
            END
        ) AS total_fare_amount,

        SUM(
            CASE
                WHEN total_amount IS NOT NULL
                THEN total_amount
                ELSE 0
            END
        ) AS total_amount,

        SUM(
            CASE
                WHEN trip_distance IS NOT NULL
                AND trip_distance > 0
                THEN trip_distance
                ELSE 0
            END
        ) AS total_distance,

        SUM(
            CASE
                WHEN trip_duration_minutes IS NOT NULL
                AND trip_duration_minutes > 0
                THEN trip_duration_minutes
                ELSE 0
            END
        ) AS total_duration_minutes,

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

        AVG(total_amount) AS avg_amount_per_trip,

        AVG(trip_distance) AS avg_distance_per_trip,

        AVG(trip_duration_minutes) AS avg_duration_minutes,

        AVG(trip_speed_mph) AS avg_speed_mph,

        MEDIAN(total_amount) AS median_amount_per_trip,

        MEDIAN(trip_distance) AS median_distance,

        MEDIAN(trip_duration_minutes) AS median_duration_minutes,

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
                WHEN is_airport_trip
                THEN 1
                ELSE 0
            END
        ) AS airport_trips

    FROM intermediate.trip_metrics

),

peak AS (

    SELECT
        hour_of_day AS peak_hour,
        AVG(taxi_trip_count) AS peak_hour_trips
    FROM hourly
    GROUP BY hour_of_day
    ORDER BY AVG(taxi_trip_count) DESC
    LIMIT 1

),

hour_stats AS (

    SELECT
        AVG(taxi_trip_count) AS avg_hourly_trips,
        STDDEV_SAMP(taxi_trip_count) AS hourly_demand_stddev,
        MAX(taxi_trip_count) AS max_hourly_trips
    FROM hourly

),

daily AS (

    SELECT
        calendar_date,
        SUM(taxi_trip_count) AS daily_trips
    FROM hourly
    GROUP BY calendar_date

),

daily_stats AS (

    SELECT
        AVG(daily_trips) AS avg_daily_trips,
        STDDEV_SAMP(daily_trips) AS daily_demand_stddev
    FROM daily

)

SELECT

    trip.total_trips,

    trip.total_passengers,

    trip.total_fare_amount,

    trip.total_amount,

    trip.total_distance,

    trip.total_duration_minutes,

    trip.avg_fare_per_mile,

    trip.avg_amount_per_minute,

    trip.avg_amount_per_trip,

    trip.avg_distance_per_trip,

    trip.avg_duration_minutes,

    trip.avg_speed_mph,

    trip.median_amount_per_trip,

    trip.median_distance,

    trip.median_duration_minutes,

    trip.tipped_trips,

    trip.avg_tip_percentage,

    trip.airport_trips,

    100.0 * trip.airport_trips
        / NULLIF(trip.total_trips, 0)
        AS airport_share_pct,

    peak.peak_hour,

    peak.peak_hour_trips,

    100.0 * peak.peak_hour_trips
    / NULLIF(daily_stats.avg_daily_trips, 0)
    AS peak_hour_share_pct,

    hour_stats.avg_hourly_trips,

    hour_stats.hourly_demand_stddev,

    100.0 * hour_stats.hourly_demand_stddev
        / NULLIF(hour_stats.avg_hourly_trips, 0)
        AS hourly_demand_cv_pct,

    daily_stats.avg_daily_trips,

    daily_stats.daily_demand_stddev,

    100.0 * daily_stats.daily_demand_stddev
        / NULLIF(daily_stats.avg_daily_trips, 0)
        AS daily_demand_cv_pct

FROM trip
CROSS JOIN peak
CROSS JOIN hour_stats
CROSS JOIN daily_stats;
