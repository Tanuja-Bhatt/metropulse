-- =============================================================================
-- METROPULSE — GEOGRAPHIC PERFORMANCE MART
-- =============================================================================
-- Grain:
--   One row per taxi zone.
--
-- Purpose:
--   Zone contribution, pickup/dropoff activity, revenue, airport activity,
--   concentration and underserved-zone screening.
-- =============================================================================

CREATE OR REPLACE TABLE marts.geographic_performance AS

WITH zone AS (

    SELECT
        location_id,
        zone,
        service_zone,

        pickup_trips,
        dropoff_trips,

        pickup_revenue,
        dropoff_revenue,

        avg_pickup_duration_minutes,
        avg_pickup_distance,
        avg_fare_per_mile,

        airport_pickup_trips,
        airport_dropoff_trips,

        total_zone_activity,
        total_zone_revenue,

        revenue_per_zone_activity,

        airport_pickup_share,
        airport_dropoff_share

    FROM intermediate.zone_performance

),

market AS (

    SELECT
        SUM(total_zone_activity) AS total_market_activity,
        SUM(total_zone_revenue) AS total_market_revenue,

        AVG(total_zone_activity) AS avg_zone_activity,

        MEDIAN(total_zone_activity) AS median_zone_activity

    FROM zone

),

ranked AS (

    SELECT
        z.*,

        RANK() OVER (
            ORDER BY total_zone_activity DESC
        ) AS activity_rank,

        RANK() OVER (
            ORDER BY total_zone_revenue DESC
        ) AS revenue_rank,

        PERCENT_RANK() OVER (
            ORDER BY total_zone_activity
        ) AS activity_percentile

    FROM zone z

)

SELECT

    r.*,

    100.0 * r.total_zone_activity
        / NULLIF(m.total_market_activity, 0)
        AS zone_activity_contribution_pct,

    100.0 * r.total_zone_revenue
        / NULLIF(m.total_market_revenue, 0)
        AS zone_revenue_contribution_pct,

    CASE
        WHEN r.total_zone_activity < m.median_zone_activity
        AND r.total_zone_activity > 0
        THEN TRUE
        ELSE FALSE
    END AS below_median_activity_indicator,

    CASE
        WHEN r.total_zone_activity < m.median_zone_activity
        THEN 'Below Median Activity'
        ELSE 'At/Above Median Activity'
    END AS activity_segment

FROM ranked r

CROSS JOIN market m;