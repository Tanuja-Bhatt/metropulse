-- =============================================================================
-- METROPULSE — FARE AND PAYMENT METRICS
-- =============================================================================
-- Grain:
--   One row per payment type.
--
-- Purpose:
--   Reusable financial and payment-behavior metrics for:
--   - revenue analysis
--   - fare analysis
--   - tipping behavior
--   - payment-method distribution
--   - dashboard financial KPIs
--
-- Important:
--   Revenue metrics use validated revenue records.
--   Invalid fares/totals are not silently treated as zero.
-- =============================================================================

CREATE OR REPLACE TABLE intermediate.fare_payment_metrics AS

SELECT
    payment_type,
    payment_type_label,

    -- =============================================================
    -- Trip volume
    -- =============================================================

    COUNT(*) AS total_trips,

    SUM(
        CASE
            WHEN is_revenue_valid
            THEN 1
            ELSE 0
        END
    ) AS valid_revenue_trips,

    -- =============================================================
    -- Revenue
    -- =============================================================

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

    SUM(
        CASE
            WHEN is_revenue_valid
            THEN total_amount
            ELSE 0
        END
    ) AS total_revenue,

    -- =============================================================
    -- Average transaction economics
    -- =============================================================

    AVG(
        CASE
            WHEN is_revenue_valid
            THEN fare_amount
        END
    ) AS avg_fare_amount,

    AVG(
        CASE
            WHEN is_revenue_valid
            THEN total_amount
        END
    ) AS avg_total_amount,

    AVG(
        CASE
            WHEN is_revenue_valid
            THEN tip_amount
        END
    ) AS avg_tip_amount,

    -- =============================================================
    -- Tip behavior
    -- =============================================================

    SUM(
        CASE
            WHEN is_tipped
            THEN 1
            ELSE 0
        END
    ) AS tipped_trips,

    CASE
        WHEN COUNT(*) > 0
        THEN
            SUM(
                CASE
                    WHEN is_tipped
                    THEN 1
                    ELSE 0
                END
            )::DOUBLE / COUNT(*)
        ELSE NULL
    END AS tipped_trip_share,

    AVG(
        CASE
            WHEN tip_percentage IS NOT NULL
            THEN tip_percentage
        END
    ) AS avg_tip_percentage,

    -- =============================================================
    -- Distance economics
    -- =============================================================

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

    -- =============================================================
    -- Trip quality indicators
    -- =============================================================

    SUM(
        CASE
            WHEN is_zero_fare
            THEN 1
            ELSE 0
        END
    ) AS zero_fare_trips,

    SUM(
        CASE
            WHEN is_negative_fare
            THEN 1
            ELSE 0
        END
    ) AS negative_fare_trips,

    SUM(
        CASE
            WHEN is_zero_total
            THEN 1
            ELSE 0
        END
    ) AS zero_total_trips,

    SUM(
        CASE
            WHEN is_negative_total
            THEN 1
            ELSE 0
        END
    ) AS negative_total_trips,

    -- =============================================================
    -- Airport activity
    -- =============================================================

    SUM(
        CASE
            WHEN is_airport_trip
            THEN 1
            ELSE 0
        END
    ) AS airport_trips,

    SUM(
        CASE
            WHEN is_airport_trip
             AND is_revenue_valid
            THEN total_amount
            ELSE 0
        END
    ) AS airport_revenue,

    -- =============================================================
    -- Revenue per trip
    -- =============================================================

    CASE
        WHEN SUM(
            CASE
                WHEN is_revenue_valid
                THEN 1
                ELSE 0
            END
        ) > 0
        THEN
            SUM(
                CASE
                    WHEN is_revenue_valid
                    THEN total_amount
                    ELSE 0
                END
            )
            /
            SUM(
                CASE
                    WHEN is_revenue_valid
                    THEN 1
                    ELSE 0
                END
            )
        ELSE NULL
    END AS revenue_per_valid_trip

FROM intermediate.trip_metrics

GROUP BY
    payment_type,
    payment_type_label;