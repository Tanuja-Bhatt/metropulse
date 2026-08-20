from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

DB_PATH = DATA_DIR / "metropulse.duckdb"

TAXI_PATTERN = str(
    RAW_DIR
    / "taxi"
    / "yellow_tripdata_2024-*.parquet"
)

ZONE_LOOKUP = str(
    RAW_DIR
    / "zones"
    / "taxi_zone_lookup.csv"
)

WEATHER_FILE = str(
    RAW_DIR
    / "weather"
    / "nyc_hourly_weather_2024-04-01_2024-06-30.csv"
)

SUBWAY_FILE = str(
    RAW_DIR
    / "subway"
    / "nyc_subway_hourly_ridership_2024-04-01_2024-06-30.csv"
)


def connect_database():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    return duckdb.connect(str(DB_PATH))


def create_schemas(con):
    con.execute("""
        CREATE SCHEMA IF NOT EXISTS staging;
        CREATE SCHEMA IF NOT EXISTS intermediate;
        CREATE SCHEMA IF NOT EXISTS marts;
    """)


def build_staging(con):

    print("=" * 80)
    print("BUILDING STAGING LAYER")
    print("=" * 80)

    # ---------------------------------------------------------------
    # Taxi
    # ---------------------------------------------------------------

    print("\n[1/4] Creating staging.taxi_trips")

    con.execute(f"""
        CREATE OR REPLACE TABLE staging.taxi_trips AS

        SELECT
            *
        FROM read_parquet(
            '{TAXI_PATTERN}'
        )
        WHERE
            tpep_pickup_datetime >= TIMESTAMP '2024-04-01'
            AND tpep_pickup_datetime < TIMESTAMP '2024-07-01'
    """)

    taxi_count = con.execute("""
        SELECT COUNT(*)
        FROM staging.taxi_trips
    """).fetchone()[0]

    print(f"[SUCCESS] Taxi rows: {taxi_count:,}")

    # ---------------------------------------------------------------
    # Taxi zones
    # ---------------------------------------------------------------

    print("\n[2/4] Creating staging.taxi_zones")

    con.execute(f"""
        CREATE OR REPLACE TABLE staging.taxi_zones AS

        SELECT
            CAST(LocationID AS INTEGER) AS location_id,
            CAST(Borough AS VARCHAR) AS borough,
            CAST(Zone AS VARCHAR) AS zone,
            CAST(service_zone AS VARCHAR) AS service_zone

        FROM read_csv_auto(
            '{ZONE_LOOKUP}'
        )
    """)

    zone_count = con.execute("""
        SELECT COUNT(*)
        FROM staging.taxi_zones
    """).fetchone()[0]

    print(f"[SUCCESS] Taxi zone rows: {zone_count:,}")

    # ---------------------------------------------------------------
    # Weather
    # ---------------------------------------------------------------

    print("\n[3/4] Creating staging.weather_hourly")

    con.execute(f"""
        CREATE OR REPLACE TABLE staging.weather_hourly AS

        SELECT
            CAST(time AS TIMESTAMP) AS timestamp_hour,
            CAST(temperature_2m AS DOUBLE) AS temperature_2m,
            CAST(relative_humidity_2m AS INTEGER)
                AS relative_humidity_2m,
            CAST(precipitation AS DOUBLE) AS precipitation,
            CAST(rain AS DOUBLE) AS rain,
            CAST(snowfall AS DOUBLE) AS snowfall,
            CAST(weather_code AS INTEGER) AS weather_code,
            CAST(wind_speed_10m AS DOUBLE) AS wind_speed_10m,
            CAST(cloud_cover AS INTEGER) AS cloud_cover

        FROM read_csv_auto(
            '{WEATHER_FILE}'
        )
    """)

    weather_count = con.execute("""
        SELECT COUNT(*)
        FROM staging.weather_hourly
    """).fetchone()[0]

    print(f"[SUCCESS] Weather rows: {weather_count:,}")

    # ---------------------------------------------------------------
    # Subway
    # ---------------------------------------------------------------

    print("\n[4/4] Creating staging.subway_hourly")

    con.execute(f"""
        CREATE OR REPLACE TABLE staging.subway_hourly AS

        SELECT
            CAST(transit_timestamp AS TIMESTAMP)
                AS timestamp_hour,
            CAST(total_ridership AS BIGINT)
                AS total_ridership,
            CAST(total_transfers AS BIGINT)
                AS total_transfers

        FROM read_csv_auto(
            '{SUBWAY_FILE}'
        )
    """)

    subway_count = con.execute("""
        SELECT COUNT(*)
        FROM staging.subway_hourly
    """).fetchone()[0]

    print(f"[SUCCESS] Subway rows: {subway_count:,}")

def build_intermediate(con):

    print("\n")
    print("=" * 80)
    print("BUILDING INTERMEDIATE LAYER")
    print("=" * 80)

    print("\n[1/1] Creating intermediate.taxi_trips_clean")

    sql_path = (
        PROJECT_ROOT
        / "sql"
        / "intermediate"
        / "taxi_trips_clean.sql"
    )

    sql = sql_path.read_text(
        encoding="utf-8"
    )

    con.execute(sql)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.taxi_trips_clean
    """).fetchone()[0]

    print(
        f"[SUCCESS] Clean taxi rows: {row_count:,}"
    )

def build_trip_metrics(con):

    print("\n")
    print("=" * 80)
    print("BUILDING TRIP METRICS")
    print("=" * 80)

    print("\n[1/1] Creating intermediate.trip_metrics")

    sql_path = (
        PROJECT_ROOT
        / "sql"
        / "intermediate"
        / "trip_metrics.sql"
    )

    sql = sql_path.read_text(
        encoding="utf-8"
    )

    con.execute(sql)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.trip_metrics
    """).fetchone()[0]

    print(
        f"[SUCCESS] Trip metrics rows: {row_count:,}"
    )


def validate_trip_metrics(con):

    print("\n")
    print("=" * 80)
    print("TRIP METRICS VALIDATION")
    print("=" * 80)

    source_rows = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.taxi_trips_clean
    """).fetchone()[0]

    metric_rows = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.trip_metrics
    """).fetchone()[0]

    duplicate_rows = con.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT
                pickup_datetime,
                dropoff_datetime,
                vendor_id,
                pickup_location_id,
                dropoff_location_id,
                passenger_count,
                trip_distance,
                total_amount,
                COUNT(*) AS row_count
            FROM intermediate.trip_metrics
            GROUP BY
                pickup_datetime,
                dropoff_datetime,
                vendor_id,
                pickup_location_id,
                dropoff_location_id,
                passenger_count,
                trip_distance,
                total_amount
            HAVING COUNT(*) > 1
        )
    """).fetchone()[0]

    invalid_duration_metrics = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.trip_metrics
        WHERE trip_duration_minutes IS NOT NULL
          AND trip_duration_minutes <= 0
    """).fetchone()[0]

    invalid_speed_metrics = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.trip_metrics
        WHERE trip_speed_mph IS NOT NULL
          AND trip_speed_mph < 0
    """).fetchone()[0]

    invalid_tip_metrics = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.trip_metrics
        WHERE tip_percentage IS NOT NULL
          AND tip_percentage < 0
    """).fetchone()[0]

    airport_trips = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.trip_metrics
        WHERE is_airport_trip
    """).fetchone()[0]

    print(f"Source rows:                  {source_rows:,}")
    print(f"Trip metrics rows:            {metric_rows:,}")
    print(f"Duplicate groups:             {duplicate_rows:,}")
    print(f"Invalid duration metrics:     {invalid_duration_metrics:,}")
    print(f"Invalid speed metrics:        {invalid_speed_metrics:,}")
    print(f"Invalid tip metrics:          {invalid_tip_metrics:,}")
    print(f"Airport trips:                {airport_trips:,}")

    if source_rows != metric_rows:
        raise RuntimeError(
            "Trip metrics row count does not match "
            "clean taxi row count."
        )

    if invalid_duration_metrics != 0:
        raise RuntimeError(
            "Invalid positive-duration metric detected."
        )

    if invalid_speed_metrics != 0:
        raise RuntimeError(
            "Invalid negative-speed metric detected."
        )

    if invalid_tip_metrics != 0:
        raise RuntimeError(
            "Invalid negative tip percentage detected."
        )

    print(
        "\n[SUCCESS] Trip metrics row count reconciles."
    )

    print(
        "[SUCCESS] Trip metrics validation passed."
    )

def validate_intermediate(con):

    print("\n")
    print("=" * 80)
    print("INTERMEDIATE VALIDATION")
    print("=" * 80)

    taxi_rows = con.execute("""
        SELECT COUNT(*)
        FROM staging.taxi_trips
    """).fetchone()[0]

    clean_rows = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.taxi_trips_clean
    """).fetchone()[0]

    print(
        f"staging taxi rows:       {taxi_rows:,}"
    )

    print(
        f"intermediate taxi rows:  {clean_rows:,}"
    )

    if taxi_rows != clean_rows:
        raise RuntimeError(
            "Intermediate row count does not "
            "match staging row count."
        )

    print(
        "\n[SUCCESS] Intermediate row count reconciles."
    )

def validate_staging(con):

    print("\n")
    print("=" * 80)
    print("STAGING VALIDATION")
    print("=" * 80)

    expected = {
        "taxi": 10_777_291,
        "zones": 265,
        "weather": 2_184,
        "subway": 2_184,
    }

    actual = {
        "taxi": con.execute(
            "SELECT COUNT(*) FROM staging.taxi_trips"
        ).fetchone()[0],

        "zones": con.execute(
            "SELECT COUNT(*) FROM staging.taxi_zones"
        ).fetchone()[0],

        "weather": con.execute(
            "SELECT COUNT(*) FROM staging.weather_hourly"
        ).fetchone()[0],

        "subway": con.execute(
            "SELECT COUNT(*) FROM staging.subway_hourly"
        ).fetchone()[0],
    }

    for name in expected:

        print(
            f"{name:<10} "
            f"expected={expected[name]:>10,} "
            f"actual={actual[name]:>10,}"
        )

        if expected[name] != actual[name]:
            raise RuntimeError(
                f"Staging validation failed for {name}: "
                f"expected {expected[name]:,}, "
                f"got {actual[name]:,}"
            )

    print("\n[SUCCESS] All staging row counts reconcile.")


def build_hourly_spine(con):

    print("\n")
    print("=" * 80)
    print("BUILDING HOURLY SPINE")
    print("=" * 80)

    print("\n[1/1] Creating intermediate.hourly_spine")

    sql_path = (
        PROJECT_ROOT
        / "sql"
        / "intermediate"
        / "hourly_spine.sql"
    )

    sql = sql_path.read_text(
        encoding="utf-8"
    )

    con.execute(sql)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.hourly_spine
    """).fetchone()[0]

    print(
        f"[SUCCESS] Hourly spine rows: {row_count:,}"
    )

    if row_count != 2184:
        raise RuntimeError(
            f"Hourly spine expected 2,184 rows "
            f"but found {row_count:,}"
        )

def validate_hourly_sources(con):

    print("\n")
    print("=" * 80)
    print("HOURLY SOURCE VALIDATION")
    print("=" * 80)

    weather_missing = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.hourly_spine h
        LEFT JOIN staging.weather_hourly w
            ON h.timestamp_hour = w.timestamp_hour
        WHERE w.timestamp_hour IS NULL
    """).fetchone()[0]

    subway_missing = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.hourly_spine h
        LEFT JOIN staging.subway_hourly s
            ON h.timestamp_hour = s.timestamp_hour
        WHERE s.timestamp_hour IS NULL
    """).fetchone()[0]

    weather_extra = con.execute("""
        SELECT COUNT(*)
        FROM staging.weather_hourly w
        LEFT JOIN intermediate.hourly_spine h
            ON w.timestamp_hour = h.timestamp_hour
        WHERE h.timestamp_hour IS NULL
    """).fetchone()[0]

    subway_extra = con.execute("""
        SELECT COUNT(*)
        FROM staging.subway_hourly s
        LEFT JOIN intermediate.hourly_spine h
            ON s.timestamp_hour = h.timestamp_hour
        WHERE h.timestamp_hour IS NULL
    """).fetchone()[0]

    print(
        f"Missing weather hours: {weather_missing}"
    )

    print(
        f"Missing subway hours:  {subway_missing}"
    )

    print(
        f"Extra weather hours:   {weather_extra}"
    )

    print(
        f"Extra subway hours:    {subway_extra}"
    )

    if any([
        weather_missing,
        subway_missing,
        weather_extra,
        subway_extra
    ]):
        raise RuntimeError(
            "Hourly source reconciliation failed."
        )

    print(
        "\n[SUCCESS] Weather and subway "
        "fully reconcile with hourly spine."
    )

def build_hourly_taxi_demand(con):

    print("\n")
    print("=" * 80)
    print("BUILDING HOURLY TAXI DEMAND")
    print("=" * 80)

    print("\n[1/1] Creating intermediate.hourly_taxi_demand")

    sql_path = (
        PROJECT_ROOT
        / "sql"
        / "intermediate"
        / "hourly_taxi_demand.sql"
    )

    sql = sql_path.read_text(
        encoding="utf-8"
    )

    con.execute(sql)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.hourly_taxi_demand
    """).fetchone()[0]

    print(
        f"[SUCCESS] Hourly OD rows: {row_count:,}"
    )

def validate_hourly_taxi_demand(con):

    print("\n")
    print("=" * 80)
    print("HOURLY TAXI DEMAND VALIDATION")
    print("=" * 80)

    source_trips = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.taxi_trips_clean
    """).fetchone()[0]

    aggregated_trips = con.execute("""
        SELECT SUM(trip_count)
        FROM intermediate.hourly_taxi_demand
    """).fetchone()[0]

    print(
        f"Source trips:       {source_trips:,}"
    )

    print(
        f"Aggregated trips:   {aggregated_trips:,}"
    )

    if source_trips != aggregated_trips:
        raise RuntimeError(
            "Taxi aggregation reconciliation failed."
        )

    print(
        "\n[SUCCESS] Taxi trip count reconciles "
        "through hourly OD aggregation."
    )
def build_zone_performance(con):

    print("\n")
    print("=" * 80)
    print("BUILDING ZONE PERFORMANCE")
    print("=" * 80)

    sql_path = (
        PROJECT_ROOT
        / "sql"
        / "intermediate"
        / "zone_performance.sql"
    )

    sql = sql_path.read_text(
        encoding="utf-8"
    )

    con.execute(sql)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.zone_performance
    """).fetchone()[0]

    print(
        f"[SUCCESS] Zone performance rows: {row_count:,}"
    )


def validate_zone_performance(con):

    print("\n")
    print("=" * 80)
    print("ZONE PERFORMANCE VALIDATION")
    print("=" * 80)

    zone_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.zone_performance
    """).fetchone()[0]

    distinct_locations = con.execute("""
        SELECT COUNT(DISTINCT location_id)
        FROM intermediate.zone_performance
    """).fetchone()[0]

    missing_zones = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.zone_performance
        WHERE zone IS NULL
    """).fetchone()[0]

    negative_pickups = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.zone_performance
        WHERE pickup_trips < 0
    """).fetchone()[0]

    negative_dropoffs = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.zone_performance
        WHERE dropoff_trips < 0
    """).fetchone()[0]

    print(f"Zone rows:                  {zone_count:,}")
    print(f"Distinct locations:         {distinct_locations:,}")
    print(f"Missing zone mappings:      {missing_zones:,}")
    print(f"Negative pickup counts:     {negative_pickups:,}")
    print(f"Negative dropoff counts:    {negative_dropoffs:,}")

    if zone_count != distinct_locations:
        raise RuntimeError(
            "Zone performance grain is not unique."
        )

    if missing_zones != 0:
        raise RuntimeError(
            "Zone performance contains unmapped locations."
        )

    if negative_pickups != 0 or negative_dropoffs != 0:
        raise RuntimeError(
            "Zone performance contains negative trip counts."
        )

    print(
        "\n[SUCCESS] Zone performance grain is unique."
    )

    print(
        "[SUCCESS] Zone mappings are complete."
    )

    print(
        "[SUCCESS] Zone performance validation passed."
    )

def build_od_flow(con):

    print("\n")
    print("=" * 80)
    print("BUILDING OD FLOW")
    print("=" * 80)

    sql_path = (
        PROJECT_ROOT
        / "sql"
        / "intermediate"
        / "od_flow.sql"
    )

    sql = sql_path.read_text(
        encoding="utf-8"
    )

    con.execute(sql)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.od_flow
    """).fetchone()[0]

    print(
        f"[SUCCESS] OD flow rows: {row_count:,}"
    )


def validate_od_flow(con):

    print("\n")
    print("=" * 80)
    print("OD FLOW VALIDATION")
    print("=" * 80)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.od_flow
    """).fetchone()[0]

    unique_pairs = con.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT
                pickup_location_id,
                dropoff_location_id
            FROM intermediate.od_flow
            GROUP BY
                pickup_location_id,
                dropoff_location_id
        )
    """).fetchone()[0]

    od_trips = con.execute("""
        SELECT SUM(trips)
        FROM intermediate.od_flow
    """).fetchone()[0]

    expected_trips = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.trip_metrics
    """).fetchone()[0]

    invalid_trip_counts = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.od_flow
        WHERE trips <= 0
    """).fetchone()[0]

    missing_pickup_zones = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.od_flow o
        LEFT JOIN staging.taxi_zones z
            ON o.pickup_location_id = z.location_id
        WHERE z.location_id IS NULL
    """).fetchone()[0]

    missing_dropoff_zones = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.od_flow o
        LEFT JOIN staging.taxi_zones z
            ON o.dropoff_location_id = z.location_id
        WHERE z.location_id IS NULL
    """).fetchone()[0]

    print(f"OD rows:                    {row_count:,}")
    print(f"Unique OD pairs:            {unique_pairs:,}")
    print(f"Aggregated trips:           {od_trips:,}")
    print(f"Expected trips:             {expected_trips:,}")
    print(f"Invalid trip counts:        {invalid_trip_counts:,}")
    print(f"Missing pickup zones:       {missing_pickup_zones:,}")
    print(f"Missing dropoff zones:      {missing_dropoff_zones:,}")

    if row_count != unique_pairs:
        raise RuntimeError(
            "OD flow grain is not unique."
        )

    if od_trips != expected_trips:
        raise RuntimeError(
            "OD flow trip count does not reconcile "
            "with trip-level source."
        )

    if invalid_trip_counts != 0:
        raise RuntimeError(
            "OD flow contains invalid trip counts."
        )

    if missing_pickup_zones != 0:
        raise RuntimeError(
            "OD flow contains unmapped pickup zones."
        )

    if missing_dropoff_zones != 0:
        raise RuntimeError(
            "OD flow contains unmapped dropoff zones."
        )

    print(
        "\n[SUCCESS] OD flow grain is unique."
    )

    print(
        "[SUCCESS] OD flow trip totals reconcile."
    )

    print(
        "[SUCCESS] OD zone mappings are complete."
    )

    print(
        "[SUCCESS] OD flow validation passed."
    )

def build_hourly_context(con):

    print("\n")
    print("=" * 80)
    print("BUILDING HOURLY CONTEXT")
    print("=" * 80)

    sql_path = (
        PROJECT_ROOT
        / "sql"
        / "intermediate"
        / "hourly_context.sql"
    )

    sql = sql_path.read_text(
        encoding="utf-8"
    )

    con.execute(sql)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.hourly_context
    """).fetchone()[0]

    print(
        f"[SUCCESS] Hourly context rows: {row_count:,}"
    )

    if row_count != 2184:
        raise RuntimeError(
            f"Hourly context expected 2,184 rows "
            f"but found {row_count:,}"
        )

def validate_hourly_context(con):

    print("\n")
    print("=" * 80)
    print("HOURLY CONTEXT VALIDATION")
    print("=" * 80)

    result = con.execute("""
        SELECT
            COUNT(*) AS rows,
            COUNT(DISTINCT timestamp_hour) AS unique_hours,

            COUNT(*) FILTER (
                WHERE temperature_2m IS NULL
            ) AS missing_weather,

            COUNT(*) FILTER (
                WHERE total_ridership IS NULL
            ) AS missing_subway

        FROM intermediate.hourly_context
    """).fetchone()

    rows = result[0]
    unique_hours = result[1]
    missing_weather = result[2]
    missing_subway = result[3]

    print(f"Rows:              {rows:,}")
    print(f"Unique hours:      {unique_hours:,}")
    print(f"Missing weather:   {missing_weather:,}")
    print(f"Missing subway:    {missing_subway:,}")

    if rows != 2184:
        raise RuntimeError(
            "Hourly context row count failed."
        )

    if unique_hours != 2184:
        raise RuntimeError(
            "Hourly context uniqueness failed."
        )

    if missing_weather != 0:
        raise RuntimeError(
            "Missing weather values detected."
        )

    if missing_subway != 0:
        raise RuntimeError(
            "Missing subway values detected."
        )

    print(
        "\n[SUCCESS] Hourly context is one-to-one "
        "with the canonical hourly spine."
    )

def build_hourly_mobility(con):

    print("\n")
    print("=" * 80)
    print("BUILDING HOURLY MOBILITY MART")
    print("=" * 80)

    sql_path = (
        PROJECT_ROOT
        / "sql"
        / "marts"
        / "hourly_mobility.sql"
    )

    sql = sql_path.read_text(
        encoding="utf-8"
    )

    con.execute(sql)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM marts.hourly_mobility
    """).fetchone()[0]

    print(
        f"[SUCCESS] Mobility mart rows: {row_count:,}"
    )

def validate_hourly_mobility(con):

    print("\n")
    print("=" * 80)
    print("MOBILITY MART VALIDATION")
    print("=" * 80)

    # ---------------------------------------------------------------
    # Basic mart reconciliation
    # ---------------------------------------------------------------

    result = con.execute("""
        SELECT
            COUNT(*) AS mart_rows,
            COUNT(DISTINCT pickup_hour) AS hours,
            SUM(trip_count) AS trips
        FROM marts.hourly_mobility
    """).fetchone()

    mart_rows = result[0]
    hours = result[1]
    trips = result[2]

    expected_trips = con.execute("""
        SELECT SUM(trip_count)
        FROM intermediate.hourly_taxi_demand
    """).fetchone()[0]

    print(f"Mart rows:          {mart_rows:,}")
    print(f"Distinct hours:     {hours:,}")
    print(f"Taxi trips:         {trips:,}")
    print(f"Expected trips:     {expected_trips:,}")

    # ---------------------------------------------------------------
    # Validate mart grain
    #
    # Expected grain:
    # one row per pickup_hour + pickup_location_id + dropoff_location_id
    # ---------------------------------------------------------------

    grain_check = con.execute("""
        SELECT
            COUNT(*) AS total_rows,
            COUNT(DISTINCT (
                pickup_hour,
                pickup_location_id,
                dropoff_location_id
            )) AS unique_grain_rows
        FROM marts.hourly_mobility
    """).fetchone()

    total_rows = grain_check[0]
    unique_grain_rows = grain_check[1]

    print(f"Unique grain rows:  {unique_grain_rows:,}")

    # ---------------------------------------------------------------
    # Validate zone mapping
    # ---------------------------------------------------------------

    zone_check = con.execute("""
        SELECT
            COUNT(*) FILTER (
                WHERE pickup_zone IS NULL
            ) AS missing_pickup_zone,

            COUNT(*) FILTER (
                WHERE dropoff_zone IS NULL
            ) AS missing_dropoff_zone

        FROM marts.hourly_mobility
    """).fetchone()

    missing_pickup_zone = zone_check[0]
    missing_dropoff_zone = zone_check[1]

    print(f"Missing pickup zones:  {missing_pickup_zone:,}")

    print(f"Missing dropoff zones: {missing_dropoff_zone:,}")

    # ---------------------------------------------------------------
    # Assertions
    # ---------------------------------------------------------------

    if trips != expected_trips:
        raise RuntimeError(
            "Mobility mart changed taxi trip totals."
        )

    if hours != 2184:
        raise RuntimeError(
            "Mobility mart does not cover all hours."
        )

    if total_rows != unique_grain_rows:
        raise RuntimeError(
            "Mobility mart grain is not unique."
        )

    if missing_pickup_zone != 0:
        raise RuntimeError(
            "Mobility mart contains unmapped pickup zones."
        )

    if missing_dropoff_zone != 0:
        raise RuntimeError(
            "Mobility mart contains unmapped dropoff zones."
        )

    print(
        "\n[SUCCESS] Mobility mart preserves "
        "taxi aggregation grain."
    )

    print(
        "[SUCCESS] Mobility mart grain is unique."
    )

    print(
        "[SUCCESS] All taxi zones are mapped."
    )

def build_hourly_mobility_summary(con):

    print("\n")
    print("=" * 80)
    print("BUILDING HOURLY MOBILITY SUMMARY")
    print("=" * 80)

    sql_path = (
        PROJECT_ROOT
        / "sql"
        / "marts"
        / "hourly_mobility_summary.sql"
    )

    sql = sql_path.read_text(
        encoding="utf-8"
    )

    con.execute(sql)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM marts.hourly_mobility_summary
    """).fetchone()[0]

    print(
        f"[SUCCESS] Hourly summary rows: "
        f"{row_count:,}"
    )

    if row_count != 2184:
        raise RuntimeError(
            f"Hourly summary expected 2,184 rows "
            f"but found {row_count:,}"
        )

def validate_hourly_mobility_summary(con):

    print("\n")
    print("=" * 80)
    print("HOURLY MOBILITY SUMMARY VALIDATION")
    print("=" * 80)

    result = con.execute("""
        SELECT
            COUNT(*) AS rows,
            COUNT(DISTINCT pickup_hour) AS unique_hours,
            SUM(taxi_trip_count) AS taxi_trips
        FROM marts.hourly_mobility_summary
    """).fetchone()

    rows = result[0]
    unique_hours = result[1]
    taxi_trips = result[2]

    expected_trips = con.execute("""
        SELECT SUM(trip_count)
        FROM marts.hourly_mobility
    """).fetchone()[0]

    print(f"Rows:               {rows:,}")
    print(f"Unique hours:       {unique_hours:,}")
    print(f"Taxi trips:         {taxi_trips:,}")
    print(f"Expected trips:     {expected_trips:,}")

    if rows != 2184:
        raise RuntimeError(
            f"Hourly summary expected 2,184 rows "
            f"but found {rows:,}"
        )

    if unique_hours != 2184:
        raise RuntimeError(
            f"Hourly summary expected 2,184 unique hours "
            f"but found {unique_hours:,}"
        )

    if taxi_trips != expected_trips:
        raise RuntimeError(
            "Hourly summary changed taxi trip totals."
        )

    print(
        "\n[SUCCESS] Hourly summary contains "
        "one row per canonical hour."
    )

    print(
        "[SUCCESS] Hourly summary preserves "
        "taxi trip totals."
    )

# =============================================================================
# ADDITIONAL ANALYTICAL LAYERS
# =============================================================================

def build_fare_payment_metrics(con):
    print("\n")
    print("=" * 80)
    print("BUILDING FARE AND PAYMENT METRICS")
    print("=" * 80)

    sql_path = (
        PROJECT_ROOT
        / "sql"
        / "intermediate"
        / "fare_payment_metrics.sql"
    )

    sql = sql_path.read_text(encoding="utf-8")
    con.execute(sql)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.fare_payment_metrics
    """).fetchone()[0]

    print(
        f"[SUCCESS] Fare/payment metric rows: {row_count:,}"
    )


def validate_fare_payment_metrics(con):
    print("\n")
    print("=" * 80)
    print("FARE AND PAYMENT METRICS VALIDATION")
    print("=" * 80)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.fare_payment_metrics
    """).fetchone()[0]

    duplicate_groups = con.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT
                payment_type,
                payment_type_label
            FROM intermediate.fare_payment_metrics
            GROUP BY
                payment_type,
                payment_type_label
            HAVING COUNT(*) > 1
        )
    """).fetchone()[0]

    negative_revenue = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.fare_payment_metrics
        WHERE total_revenue < 0
    """).fetchone()[0]

    print(f"Payment metric rows:       {row_count:,}")
    print(f"Duplicate payment groups:  {duplicate_groups:,}")
    print(f"Negative total revenue:    {negative_revenue:,}")

    if duplicate_groups != 0:
        raise RuntimeError(
            "Fare/payment metrics contain duplicate payment groups."
        )

    if negative_revenue != 0:
        raise RuntimeError(
            "Fare/payment metrics contain negative aggregate revenue."
        )

    if row_count == 0:
        raise RuntimeError(
            "Fare/payment metrics table is empty."
        )

    print("[SUCCESS] Fare/payment metric grain is unique.")
    print("[SUCCESS] Fare/payment metrics validation passed.")


def build_airport_metrics(con):
    print("\n")
    print("=" * 80)
    print("BUILDING AIRPORT METRICS")
    print("=" * 80)

    sql_path = (
        PROJECT_ROOT
        / "sql"
        / "intermediate"
        / "airport_metrics.sql"
    )

    sql = sql_path.read_text(encoding="utf-8")
    con.execute(sql)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.airport_metrics
    """).fetchone()[0]

    print(
        f"[SUCCESS] Airport metric rows: {row_count:,}"
    )


def validate_airport_metrics(con):
    print("\n")
    print("=" * 80)
    print("AIRPORT METRICS VALIDATION")
    print("=" * 80)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.airport_metrics
    """).fetchone()[0]

    total_airport_trips = con.execute("""
        SELECT SUM(total_trips)
        FROM intermediate.airport_metrics
        WHERE airport_category != 'Non-Airport'
    """).fetchone()[0]

    expected_airport_trips = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.trip_metrics
        WHERE is_airport_trip
    """).fetchone()[0]

    invalid_revenue = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.airport_metrics
        WHERE total_revenue < 0
    """).fetchone()[0]

    print(f"Airport metric rows:       {row_count:,}")
    print(f"Airport trips:             {total_airport_trips:,}")
    print(f"Expected airport trips:    {expected_airport_trips:,}")
    print(f"Negative aggregate revenue:{invalid_revenue:,}")

    if total_airport_trips != expected_airport_trips:
        raise RuntimeError(
            "Airport trip totals do not reconcile with trip-level source."
        )

    if invalid_revenue != 0:
        raise RuntimeError(
            "Airport metrics contain negative aggregate revenue."
        )

    if row_count == 0:
        raise RuntimeError(
            "Airport metrics table is empty."
        )

    print("[SUCCESS] Airport trip totals reconcile.")
    print("[SUCCESS] Airport metrics validation passed.")


def build_weather_mobility_metrics(con):
    print("\n")
    print("=" * 80)
    print("BUILDING WEATHER-MOBILITY METRICS")
    print("=" * 80)

    sql_path = (
        PROJECT_ROOT
        / "sql"
        / "intermediate"
        / "weather_mobility_metrics.sql"
    )

    sql = sql_path.read_text(encoding="utf-8")
    con.execute(sql)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.weather_mobility_metrics
    """).fetchone()[0]

    print(
        f"[SUCCESS] Weather/mobility metric rows: {row_count:,}"
    )


def validate_weather_mobility_metrics(con):
    print("\n")
    print("=" * 80)
    print("WEATHER-MOBILITY METRICS VALIDATION")
    print("=" * 80)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.weather_mobility_metrics
    """).fetchone()[0]

    unique_hours = con.execute("""
        SELECT COUNT(DISTINCT pickup_hour)
        FROM intermediate.weather_mobility_metrics
    """).fetchone()[0]

    expected_hours = con.execute("""
        SELECT COUNT(*)
        FROM marts.hourly_mobility_summary
    """).fetchone()[0]

    invalid_rain_flag = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.weather_mobility_metrics
        WHERE is_raining IS NULL
          AND precipitation IS NOT NULL
    """).fetchone()[0]

    print(f"Weather metric rows:       {row_count:,}")
    print(f"Unique hours:               {unique_hours:,}")
    print(f"Expected hours:             {expected_hours:,}")
    print(f"Invalid rain flags:         {invalid_rain_flag:,}")

    if row_count != expected_hours:
        raise RuntimeError(
            "Weather/mobility metrics do not preserve hourly grain."
        )

    if unique_hours != expected_hours:
        raise RuntimeError(
            "Weather/mobility metrics contain duplicate hours."
        )

    if invalid_rain_flag != 0:
        raise RuntimeError(
            "Weather/mobility metrics contain invalid rain flags."
        )

    print("[SUCCESS] Weather/mobility metrics preserve hourly grain.")
    print("[SUCCESS] Weather/mobility metrics validation passed.")


def build_data_quality_metrics(con):
    print("\n")
    print("=" * 80)
    print("BUILDING DATA QUALITY METRICS")
    print("=" * 80)

    sql_path = (
        PROJECT_ROOT
        / "sql"
        / "intermediate"
        / "data_quality_metrics.sql"
    )

    sql = sql_path.read_text(encoding="utf-8")
    con.execute(sql)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.data_quality_metrics
    """).fetchone()[0]

    print(
        f"[SUCCESS] Data quality metric rows: {row_count:,}"
    )


def validate_data_quality_metrics(con):
    print("\n")
    print("=" * 80)
    print("DATA QUALITY METRICS VALIDATION")
    print("=" * 80)

    row_count = con.execute("""
        SELECT COUNT(*)
        FROM intermediate.data_quality_metrics
    """).fetchone()[0]

    status = con.execute("""
        SELECT warehouse_quality_status
        FROM intermediate.data_quality_metrics
        LIMIT 1
    """).fetchone()[0]

    staging_rows = con.execute("""
        SELECT staging_taxi_rows
        FROM intermediate.data_quality_metrics
        LIMIT 1
    """).fetchone()[0]

    clean_rows = con.execute("""
        SELECT clean_taxi_rows
        FROM intermediate.data_quality_metrics
        LIMIT 1
    """).fetchone()[0]

    trip_metric_rows = con.execute("""
        SELECT trip_metric_rows
        FROM intermediate.data_quality_metrics
        LIMIT 1
    """).fetchone()[0]

    print(f"Quality metric rows:        {row_count:,}")
    print(f"Staging taxi rows:          {staging_rows:,}")
    print(f"Clean taxi rows:            {clean_rows:,}")
    print(f"Trip metric rows:            {trip_metric_rows:,}")
    print(f"Warehouse quality status:   {status}")

    if row_count != 1:
        raise RuntimeError(
            "Data quality metrics must contain exactly one warehouse-level row."
        )

    if staging_rows != clean_rows:
        raise RuntimeError(
            "Data quality metrics detected staging/clean row mismatch."
        )

    if clean_rows != trip_metric_rows:
        raise RuntimeError(
            "Data quality metrics detected clean/trip-metric row mismatch."
        )

    if status != "PASS":
        raise RuntimeError(
            "Warehouse quality status is REVIEW."
        )

    print("[SUCCESS] Data quality metrics contain one warehouse-level record.")
    print("[SUCCESS] Warehouse quality status is PASS.")

def validate_data_quality_tests(con):

    print("\n")
    print("=" * 80)
    print("AUTOMATED DATA QUALITY TEST SUITE")
    print("=" * 80)

    tests = [

        # ---------------------------------------------------------------------
        # TEST 01 — STAGING / CLEAN RECONCILIATION
        # ---------------------------------------------------------------------

        (
            "DQ-TEST-01",
            "Staging and clean taxi row counts reconcile",
            """
            SELECT
                (
                    SELECT COUNT(*)
                    FROM staging.taxi_trips
                )
                =
                (
                    SELECT COUNT(*)
                    FROM intermediate.taxi_trips_clean
                )
            """
        ),

        # ---------------------------------------------------------------------
        # TEST 02 — CLEAN / METRIC RECONCILIATION
        # ---------------------------------------------------------------------

        (
            "DQ-TEST-02",
            "Clean and trip-metric row counts reconcile",
            """
            SELECT
                (
                    SELECT COUNT(*)
                    FROM intermediate.taxi_trips_clean
                )
                =
                (
                    SELECT COUNT(*)
                    FROM intermediate.trip_metrics
                )
            """
        ),

        # ---------------------------------------------------------------------
        # TEST 03 — DUPLICATE GROUPS
        # Uses the exact existing warehouse duplicate definition.
        # ---------------------------------------------------------------------

        (
            "DQ-TEST-03",
            "No duplicate trip metric groups",
            """
            SELECT COUNT(*) = 0
            FROM (
                SELECT
                    pickup_datetime,
                    dropoff_datetime,
                    vendor_id,
                    pickup_location_id,
                    dropoff_location_id,
                    passenger_count,
                    trip_distance,
                    total_amount,
                    COUNT(*) AS row_count
                FROM intermediate.trip_metrics
                GROUP BY
                    pickup_datetime,
                    dropoff_datetime,
                    vendor_id,
                    pickup_location_id,
                    dropoff_location_id,
                    passenger_count,
                    trip_distance,
                    total_amount
                HAVING COUNT(*) > 1
            )
            """
        ),

        # ---------------------------------------------------------------------
        # TEST 04 — PICKUP ZONE COMPLETENESS
        # ---------------------------------------------------------------------

        (
            "DQ-TEST-04",
            "All pickup locations have zone mappings",
            """
            SELECT COUNT(*) = 0
            FROM intermediate.trip_metrics t
            LEFT JOIN staging.taxi_zones z
                ON t.pickup_location_id = z.location_id
            WHERE z.location_id IS NULL
            """
        ),

        # ---------------------------------------------------------------------
        # TEST 05 — DROPOFF ZONE COMPLETENESS
        # ---------------------------------------------------------------------

        (
            "DQ-TEST-05",
            "All dropoff locations have zone mappings",
            """
            SELECT COUNT(*) = 0
            FROM intermediate.trip_metrics t
            LEFT JOIN staging.taxi_zones z
                ON t.dropoff_location_id = z.location_id
            WHERE z.location_id IS NULL
            """
        ),

        # ---------------------------------------------------------------------
        # TEST 06 — HOURLY SPINE CONTINUITY
        # ---------------------------------------------------------------------

        (
            "DQ-TEST-06",
            "Canonical hourly spine has no temporal gaps",
            """
            WITH hours AS (
                SELECT
                    timestamp_hour,
                    LAG(timestamp_hour)
                        OVER (
                            ORDER BY timestamp_hour
                        ) AS previous_hour
                FROM intermediate.hourly_spine
            )

            SELECT COUNT(*) = 0
            FROM hours
            WHERE previous_hour IS NOT NULL
              AND timestamp_hour - previous_hour
                    <> INTERVAL '1 hour'
            """
        ),

        # ---------------------------------------------------------------------
        # TEST 07 — WEATHER COMPLETENESS
        # ---------------------------------------------------------------------

        (
            "DQ-TEST-07",
            "Weather covers every canonical hour",
            """
            SELECT COUNT(*) = 0
            FROM intermediate.hourly_context
            WHERE temperature_2m IS NULL
            """
        ),

        # ---------------------------------------------------------------------
        # TEST 08 — SUBWAY COMPLETENESS
        # ---------------------------------------------------------------------

        (
            "DQ-TEST-08",
            "Subway covers every canonical hour",
            """
            SELECT COUNT(*) = 0
            FROM intermediate.hourly_context
            WHERE total_ridership IS NULL
            """
        ),

        # ---------------------------------------------------------------------
        # TEST 09 — HOURLY TAXI DEMAND RECONCILIATION
        # ---------------------------------------------------------------------

        (
            "DQ-TEST-09",
            "Hourly taxi demand preserves total trip count",
            """
            SELECT
                SUM(trip_count)
                =
                (
                    SELECT COUNT(*)
                    FROM intermediate.trip_metrics
                )
            FROM intermediate.hourly_taxi_demand
            """
        ),

        # ---------------------------------------------------------------------
        # TEST 10 — MOBILITY MART RECONCILIATION
        # ---------------------------------------------------------------------

        (
            "DQ-TEST-10",
            "Mobility mart preserves total trip count",
            """
            SELECT
                SUM(trip_count)
                =
                (
                    SELECT COUNT(*)
                    FROM intermediate.trip_metrics
                )
            FROM marts.hourly_mobility
            """
        ),

        # ---------------------------------------------------------------------
        # TEST 11 — HOURLY SUMMARY RECONCILIATION
        # ---------------------------------------------------------------------

        (
            "DQ-TEST-11",
            "Hourly mobility summary preserves total trip count",
            """
            SELECT
                SUM(taxi_trip_count)
                =
                (
                    SELECT COUNT(*)
                    FROM intermediate.trip_metrics
                )
            FROM marts.hourly_mobility_summary
            """
        ),

        # ---------------------------------------------------------------------
        # TEST 12 — HOURLY SUMMARY GRAIN
        # ---------------------------------------------------------------------

        (
            "DQ-TEST-12",
            "Hourly summary contains one row per canonical hour",
            """
            SELECT
                COUNT(*) = COUNT(DISTINCT pickup_hour)
            FROM marts.hourly_mobility_summary
            """
        ),

        # ---------------------------------------------------------------------
        # TEST 13 — VALID REVENUE INTEGRITY
        # ---------------------------------------------------------------------

        (
            "DQ-TEST-13",
            "Revenue-valid trips contain no negative total amounts",
            """
            SELECT COUNT(*) = 0
            FROM intermediate.trip_metrics
            WHERE is_revenue_valid
              AND total_amount < 0
            """
        ),

        # ---------------------------------------------------------------------
        # TEST 14 — DURATION METRIC INTEGRITY
        # Mirrors existing validation rule.
        # ---------------------------------------------------------------------

        (
            "DQ-TEST-14",
            "No non-positive populated duration metrics",
            """
            SELECT COUNT(*) = 0
            FROM intermediate.trip_metrics
            WHERE trip_duration_minutes IS NOT NULL
              AND trip_duration_minutes <= 0
            """
        ),

        # ---------------------------------------------------------------------
        # TEST 15 — TIP METRIC INTEGRITY
        # Mirrors existing validation rule.
        # ---------------------------------------------------------------------

        (
            "DQ-TEST-15",
            "No negative populated tip percentages",
            """
            SELECT COUNT(*) = 0
            FROM intermediate.trip_metrics
            WHERE tip_percentage IS NOT NULL
              AND tip_percentage < 0
            """
        ),
    ]

    failures = []

    for test_id, test_name, sql in tests:

        result = con.execute(sql).fetchone()[0]

        passed = bool(result)

        if passed:
            print(f"[PASS] {test_id} — {test_name}")
        else:
            print(f"[FAIL] {test_id} — {test_name}")
            failures.append((test_id, test_name))

    print("-" * 80)

    total_tests = len(tests)
    passed_tests = total_tests - len(failures)

    print(f"Automated tests executed: {total_tests}")
    print(f"Automated tests passed:   {passed_tests}")
    print(f"Automated tests failed:   {len(failures)}")

    if failures:

        print("\nFAILED TESTS:")

        for test_id, test_name in failures:
            print(f"  - {test_id}: {test_name}")

        raise RuntimeError(
            "Automated data-quality test suite failed."
        )

    print("\n[SUCCESS] All automated data-quality tests passed.")

def build_executive_mobility(con):
    print("\n" + "=" * 80)
    print("BUILDING EXECUTIVE MOBILITY MART")
    print("=" * 80)

    sql_path = PROJECT_ROOT / "sql" / "marts" / "executive_mobility.sql"

    sql = sql_path.read_text(encoding="utf-8")
    con.execute(sql)

    row_count = con.sql(
        "SELECT COUNT(*) FROM marts.executive_mobility"
    ).fetchone()[0]

    if row_count != 1:
        raise RuntimeError(
            f"Executive mobility mart must contain exactly 1 row; "
            f"found {row_count}."
        )

    print(f"[SUCCESS] Executive mobility rows: {row_count}")


def build_temporal_demand(con):
    print("\n" + "=" * 80)
    print("BUILDING TEMPORAL DEMAND MART")
    print("=" * 80)

    sql_path = PROJECT_ROOT / "sql" / "marts" / "temporal_demand.sql"

    sql = sql_path.read_text(encoding="utf-8")
    con.execute(sql)

    row_count = con.sql(
        "SELECT COUNT(*) FROM marts.temporal_demand"
    ).fetchone()[0]

    expected = con.sql(
        "SELECT COUNT(*) FROM marts.hourly_mobility_summary"
    ).fetchone()[0]

    if row_count != expected:
        raise RuntimeError(
            "Temporal demand mart row count does not reconcile "
            "with hourly summary."
        )

    print(f"[SUCCESS] Temporal demand rows: {row_count}")


def build_geographic_performance(con):
    print("\n" + "=" * 80)
    print("BUILDING GEOGRAPHIC PERFORMANCE MART")
    print("=" * 80)

    sql_path = PROJECT_ROOT / "sql" / "marts" / "geographic_performance.sql"

    sql = sql_path.read_text(encoding="utf-8")
    con.execute(sql)

    row_count = con.sql(
        "SELECT COUNT(*) FROM marts.geographic_performance"
    ).fetchone()[0]

    expected = con.sql(
        "SELECT COUNT(*) FROM intermediate.zone_performance"
    ).fetchone()[0]

    if row_count != expected:
        raise RuntimeError(
            "Geographic performance mart row count does not reconcile."
        )

    print(f"[SUCCESS] Geographic performance rows: {row_count}")


def build_fare_payment_analysis(con):
    print("\n" + "=" * 80)
    print("BUILDING FARE / PAYMENT ANALYSIS MART")
    print("=" * 80)

    sql_path = PROJECT_ROOT / "sql" / "marts" / "fare_payment_analysis.sql"

    sql = sql_path.read_text(encoding="utf-8")
    con.execute(sql)

    row_count = con.sql(
        "SELECT COUNT(*) FROM marts.fare_payment_analysis"
    ).fetchone()[0]

    if row_count == 0:
        raise RuntimeError(
            "Fare/payment analysis mart is empty."
        )

    print(f"[SUCCESS] Fare/payment rows: {row_count}")


def build_weather_transit_analysis(con):
    print("\n" + "=" * 80)
    print("BUILDING WEATHER / TRANSIT ANALYSIS MART")
    print("=" * 80)

    sql_path = (
        PROJECT_ROOT
        / "sql"
        / "marts"
        / "weather_transit_analysis.sql"
    )

    sql = sql_path.read_text(encoding="utf-8")
    con.execute(sql)

    row_count = con.sql(
        "SELECT COUNT(*) FROM marts.weather_transit_analysis"
    ).fetchone()[0]

    expected = con.sql(
        "SELECT COUNT(*) FROM marts.hourly_mobility_summary"
    ).fetchone()[0]

    if row_count != expected:
        raise RuntimeError(
            "Weather/transit mart row count does not reconcile."
        )

    print(f"[SUCCESS] Weather/transit rows: {row_count}")





def build_statistical_analysis(con):
    print("\n" + "=" * 80)
    print("BUILDING STATISTICAL ANALYSIS MART")
    print("=" * 80)

    sql_path = (
        PROJECT_ROOT
        / "sql"
        / "marts"
        / "statistical_analysis.sql"
    )

    sql = sql_path.read_text(encoding="utf-8")
    con.execute(sql)

    row_count = con.sql(
        "SELECT COUNT(*) FROM marts.statistical_analysis"
    ).fetchone()[0]

    if row_count == 0:
        raise RuntimeError(
            "Statistical analysis mart is empty."
        )

    print(f"[SUCCESS] Statistical analysis rows: {row_count}")

def build_data_quality_anomalies(con):
    print("\n" + "=" * 80)
    print("BUILDING DATA QUALITY / ANOMALY MART")
    print("=" * 80)

    sql_path = (
        PROJECT_ROOT
        / "sql"
        / "marts"
        / "data_quality_anomalies.sql"
    )

    sql = sql_path.read_text(encoding="utf-8")
    con.execute(sql)

    row_count = con.sql(
        "SELECT COUNT(*) FROM marts.data_quality_anomalies"
    ).fetchone()[0]

    issue_count = con.sql(
        """
        SELECT COUNT(DISTINCT issue_id)
        FROM marts.data_quality_anomalies
        """
    ).fetchone()[0]

    null_issue_ids = con.sql(
        """
        SELECT COUNT(*)
        FROM marts.data_quality_anomalies
        WHERE issue_id IS NULL
        """
    ).fetchone()[0]

    if row_count != 8:
        raise RuntimeError(
            f"Expected exactly 8 material DQ findings; found {row_count}."
        )

    if issue_count != 8:
        raise RuntimeError(
            f"Expected 8 unique DQ issue IDs; found {issue_count}."
        )

    if null_issue_ids != 0:
        raise RuntimeError(
            "Data-quality anomaly mart contains NULL issue IDs."
        )

    print(f"[SUCCESS] Material DQ findings: {row_count}")
    print("[SUCCESS] DQ issue IDs are unique and complete.")

def main():

    print("=" * 80)
    print("METROPULSE — DUCKDB WAREHOUSE BUILD")
    print("=" * 80)

    con = connect_database()

    try:
        create_schemas(con)
        build_staging(con)
        validate_staging(con)
        build_intermediate(con)
        validate_intermediate(con)
        build_trip_metrics(con)
        validate_trip_metrics(con)
        build_zone_performance(con)
        validate_zone_performance(con)
        build_od_flow(con)
        validate_od_flow(con)
        build_hourly_spine(con)
        validate_hourly_sources(con)
        build_hourly_taxi_demand(con)
        validate_hourly_taxi_demand(con)
        build_hourly_context(con)
        validate_hourly_context(con)
        build_hourly_mobility(con)
        validate_hourly_mobility(con)
        build_hourly_mobility_summary(con)
        validate_hourly_mobility_summary(con)
        build_fare_payment_metrics(con)
        validate_fare_payment_metrics(con)

        build_airport_metrics(con)
        validate_airport_metrics(con)

        build_weather_mobility_metrics(con)
        validate_weather_mobility_metrics(con)

        build_data_quality_metrics(con)
        validate_data_quality_metrics(con)

        build_executive_mobility(con)
        build_temporal_demand(con)
        build_geographic_performance(con)
        build_fare_payment_analysis(con)
        build_weather_transit_analysis(con)
        build_data_quality_anomalies(con)
        build_statistical_analysis(con)
        validate_data_quality_tests(con)

        print("\n")
        print("=" * 80)
        print("WAREHOUSE BUILD COMPLETE")
        print("=" * 80)
        print(f"Database: {DB_PATH}")

    finally:
        con.close()


if __name__ == "__main__":
    main()