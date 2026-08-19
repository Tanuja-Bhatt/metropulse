CREATE OR REPLACE TABLE marts.hourly_mobility_summary AS

SELECT

    -- =============================================================
    -- TIME
    -- =============================================================

    pickup_hour,

    calendar_date,
    hour_of_day,
    day_of_week,
    is_weekend,
    week_start,
    month_start,

    -- =============================================================
    -- TAXI DEMAND
    -- =============================================================

    SUM(trip_count) AS taxi_trip_count,

    SUM(total_revenue) AS taxi_revenue,

    SUM(total_distance) AS taxi_distance,

    SUM(total_duration_seconds) AS taxi_duration_seconds,

    -- =============================================================
    -- TAXI QUALITY COUNTS
    -- =============================================================

    SUM(zero_distance_trip_count)
        AS zero_distance_trip_count,

    SUM(extreme_distance_trip_count)
        AS extreme_distance_trip_count,

    SUM(negative_duration_trip_count)
        AS negative_duration_trip_count,

    SUM(long_duration_trip_count)
        AS long_duration_trip_count,

    SUM(negative_total_trip_count)
        AS negative_total_trip_count,

    SUM(unknown_passenger_trip_count)
        AS unknown_passenger_trip_count,

    SUM(unknown_payment_trip_count)
        AS unknown_payment_trip_count,

    -- =============================================================
    -- WEATHER
    -- =============================================================

    MAX(temperature_2m)
        AS temperature_2m,

    MAX(relative_humidity_2m)
        AS relative_humidity_2m,

    MAX(precipitation)
        AS precipitation,

    MAX(rain)
        AS rain,

    MAX(snowfall)
        AS snowfall,

    MAX(weather_code)
        AS weather_code,

    MAX(wind_speed_10m)
        AS wind_speed_10m,

    MAX(cloud_cover)
        AS cloud_cover,

    -- =============================================================
    -- SUBWAY
    -- =============================================================

    MAX(total_ridership)
        AS subway_ridership,

    MAX(total_transfers)
        AS subway_transfers

FROM marts.hourly_mobility

GROUP BY

    pickup_hour,

    calendar_date,
    hour_of_day,
    day_of_week,
    is_weekend,
    week_start,
    month_start;