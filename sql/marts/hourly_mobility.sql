CREATE OR REPLACE TABLE marts.hourly_mobility AS

SELECT

    -- -------------------------------------------------------------
    -- Grain
    -- -------------------------------------------------------------

    t.pickup_hour,

    t.pickup_location_id,
    pu.borough AS pickup_borough,
    pu.zone AS pickup_zone,
    pu.service_zone AS pickup_service_zone,

    t.dropoff_location_id,
    dz.borough AS dropoff_borough,
    dz.zone AS dropoff_zone,
    dz.service_zone AS dropoff_service_zone,

    -- -------------------------------------------------------------
    -- Calendar / context
    -- -------------------------------------------------------------

    c.calendar_date,
    c.hour_of_day,
    c.day_of_week,
    c.is_weekend,
    c.week_start,
    c.month_start,

    -- -------------------------------------------------------------
    -- Taxi demand
    -- -------------------------------------------------------------

    t.trip_count,

    t.duration_valid_trip_count,
    t.distance_valid_trip_count,
    t.revenue_valid_trip_count,
    t.passenger_valid_trip_count,

    -- -------------------------------------------------------------
    -- Revenue
    -- -------------------------------------------------------------

    t.total_revenue,
    t.avg_total_amount,
    t.total_fare_amount,
    t.avg_fare_amount,

    -- -------------------------------------------------------------
    -- Distance
    -- -------------------------------------------------------------

    t.total_distance,
    t.avg_distance,

    -- -------------------------------------------------------------
    -- Duration
    -- -------------------------------------------------------------

    t.total_duration_seconds,
    t.avg_duration_seconds,

    -- -------------------------------------------------------------
    -- Passenger
    -- -------------------------------------------------------------

    t.avg_passenger_count,

    -- -------------------------------------------------------------
    -- Quality counts
    -- -------------------------------------------------------------

    t.zero_distance_trip_count,
    t.extreme_distance_trip_count,
    t.negative_duration_trip_count,
    t.long_duration_trip_count,
    t.negative_total_trip_count,
    t.unknown_passenger_trip_count,
    t.unknown_payment_trip_count,

    -- -------------------------------------------------------------
    -- Weather
    -- -------------------------------------------------------------

    c.temperature_2m,
    c.relative_humidity_2m,
    c.precipitation,
    c.rain,
    c.snowfall,
    c.weather_code,
    c.wind_speed_10m,
    c.cloud_cover,

    -- -------------------------------------------------------------
    -- Subway
    -- -------------------------------------------------------------

    c.total_ridership,
    c.total_transfers

FROM intermediate.hourly_taxi_demand t

LEFT JOIN intermediate.hourly_context c
    ON t.pickup_hour = c.timestamp_hour

LEFT JOIN staging.taxi_zones pu
    ON t.pickup_location_id = pu.location_id

LEFT JOIN staging.taxi_zones dz
    ON t.dropoff_location_id = dz.location_id;