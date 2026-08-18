CREATE OR REPLACE TABLE intermediate.hourly_spine AS

SELECT
    timestamp_hour,

    CAST(timestamp_hour AS DATE) AS calendar_date,

    EXTRACT(
        HOUR FROM timestamp_hour
    ) AS hour_of_day,

    EXTRACT(
        DOW FROM timestamp_hour
    ) AS day_of_week,

    CASE
        WHEN EXTRACT(DOW FROM timestamp_hour) IN (0, 6)
            THEN TRUE
        ELSE FALSE
    END AS is_weekend,

    DATE_TRUNC(
        'week',
        timestamp_hour
    ) AS week_start,

    DATE_TRUNC(
        'month',
        timestamp_hour
    ) AS month_start

FROM generate_series(
    TIMESTAMP '2024-04-01 00:00:00',
    TIMESTAMP '2024-06-30 23:00:00',
    INTERVAL 1 HOUR
) AS t(timestamp_hour);