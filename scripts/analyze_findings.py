import duckdb

DB_PATH = "data/metropulse.duckdb"

con = duckdb.connect(DB_PATH, read_only=True)

print("=" * 80)
print("METROPULSE — FINAL FINDINGS EXTRACTION")
print("=" * 80)

print("\n1. WEEKDAY VS WEEKEND")
print("-" * 80)

print(con.sql("""
    SELECT
        CASE
            WHEN is_weekend THEN 'Weekend'
            ELSE 'Weekday'
        END AS day_type,
        COUNT(*) AS hours,
        ROUND(AVG(taxi_trip_count), 2) AS avg_taxi_trips,
        MEDIAN(taxi_trip_count) AS median_taxi_trips,
        ROUND(AVG(subway_ridership), 2) AS avg_subway_ridership
    FROM marts.hourly_mobility_summary
    GROUP BY is_weekend
    ORDER BY is_weekend
"""))

print("\n2. WEATHER IMPACT")
print("-" * 80)

print(con.sql("""
    SELECT
        precipitation_category,
        COUNT(*) AS hours,
        ROUND(AVG(taxi_trip_count), 2) AS avg_taxi_trips,
        MEDIAN(taxi_trip_count) AS median_taxi_trips
    FROM (
        SELECT
            CASE
                WHEN precipitation = 0 THEN 'Dry'
                WHEN precipitation <= 1 THEN 'Light rain'
                WHEN precipitation <= 5 THEN 'Moderate rain'
                ELSE 'Heavy rain'
            END AS precipitation_category,
            taxi_trip_count
        FROM marts.hourly_mobility_summary
    )
    GROUP BY precipitation_category
    ORDER BY
        CASE precipitation_category
            WHEN 'Dry' THEN 1
            WHEN 'Light rain' THEN 2
            WHEN 'Moderate rain' THEN 3
            WHEN 'Heavy rain' THEN 4
        END
"""))

print("\n3. TOP PICKUP ZONES")
print("-" * 80)

print(con.sql("""
    SELECT
        pickup_location_id,
        pickup_zone,
        pickup_borough,
        SUM(trip_count) AS trips
    FROM marts.hourly_mobility
    GROUP BY
        pickup_location_id,
        pickup_zone,
        pickup_borough
    ORDER BY trips DESC
    LIMIT 20
"""))

print("\n4. TOP OD PAIRS")
print("-" * 80)

print(con.sql("""
    SELECT
        pickup_zone,
        dropoff_zone,
        SUM(trip_count) AS trips
    FROM marts.hourly_mobility
    GROUP BY
        pickup_zone,
        dropoff_zone
    ORDER BY trips DESC
    LIMIT 20
"""))

con.close()