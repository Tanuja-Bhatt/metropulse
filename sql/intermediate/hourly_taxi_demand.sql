CREATE OR REPLACE TABLE intermediate.hourly_taxi_demand AS

SELECT

    pickup_hour,

    pickup_location_id,

    dropoff_location_id,

    -- -------------------------------------------------------------
    -- Demand
    -- -------------------------------------------------------------

    COUNT(*) AS trip_count,

    COUNT(*) FILTER (
        WHERE is_duration_valid
    ) AS duration_valid_trip_count,

    COUNT(*) FILTER (
        WHERE is_distance_valid
    ) AS distance_valid_trip_count,

    COUNT(*) FILTER (
        WHERE is_revenue_valid
    ) AS revenue_valid_trip_count,

    COUNT(*) FILTER (
        WHERE is_passenger_valid
    ) AS passenger_valid_trip_count,

    -- -------------------------------------------------------------
    -- Revenue
    -- -------------------------------------------------------------

    SUM(total_amount) FILTER (
        WHERE is_revenue_valid
    ) AS total_revenue,

    AVG(total_amount) FILTER (
        WHERE is_revenue_valid
    ) AS avg_total_amount,

    SUM(fare_amount) FILTER (
        WHERE is_revenue_valid
    ) AS total_fare_amount,

    AVG(fare_amount) FILTER (
        WHERE is_revenue_valid
    ) AS avg_fare_amount,

    -- -------------------------------------------------------------
    -- Distance
    -- -------------------------------------------------------------

    SUM(trip_distance) FILTER (
        WHERE is_distance_valid
    ) AS total_distance,

    AVG(trip_distance) FILTER (
        WHERE is_distance_valid
    ) AS avg_distance,

    -- -------------------------------------------------------------
    -- Duration
    -- -------------------------------------------------------------

    SUM(duration_seconds) FILTER (
        WHERE is_duration_valid
    ) AS total_duration_seconds,

    AVG(duration_seconds) FILTER (
        WHERE is_duration_valid
    ) AS avg_duration_seconds,

    -- -------------------------------------------------------------
    -- Passenger metrics
    -- -------------------------------------------------------------

    AVG(passenger_count) FILTER (
        WHERE is_passenger_valid
    ) AS avg_passenger_count,

    -- -------------------------------------------------------------
    -- Quality counts
    -- -------------------------------------------------------------

    COUNT(*) FILTER (
        WHERE is_zero_distance
    ) AS zero_distance_trip_count,

    COUNT(*) FILTER (
        WHERE is_extreme_distance
    ) AS extreme_distance_trip_count,

    COUNT(*) FILTER (
        WHERE is_negative_duration
    ) AS negative_duration_trip_count,

    COUNT(*) FILTER (
        WHERE is_long_duration
    ) AS long_duration_trip_count,

    COUNT(*) FILTER (
        WHERE is_negative_total
    ) AS negative_total_trip_count,

    COUNT(*) FILTER (
        WHERE is_unknown_passenger
    ) AS unknown_passenger_trip_count,

    COUNT(*) FILTER (
        WHERE is_unknown_payment
    ) AS unknown_payment_trip_count

FROM intermediate.taxi_trips_clean

GROUP BY
    pickup_hour,
    pickup_location_id,
    dropoff_location_id;