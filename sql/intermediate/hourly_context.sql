CREATE OR REPLACE TABLE intermediate.hourly_context AS

SELECT
    h.timestamp_hour,

    h.calendar_date,
    h.hour_of_day,
    h.day_of_week,
    h.is_weekend,
    h.week_start,
    h.month_start,

    -- Weather
    w.temperature_2m,
    w.relative_humidity_2m,
    w.precipitation,
    w.rain,
    w.snowfall,
    w.weather_code,
    w.wind_speed_10m,
    w.cloud_cover,

    -- Subway
    s.total_ridership,
    s.total_transfers

FROM intermediate.hourly_spine h

LEFT JOIN staging.weather_hourly w
    ON h.timestamp_hour = w.timestamp_hour

LEFT JOIN staging.subway_hourly s
    ON h.timestamp_hour = s.timestamp_hour;