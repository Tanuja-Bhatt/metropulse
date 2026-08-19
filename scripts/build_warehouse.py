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
        build_hourly_spine(con)
        validate_hourly_sources(con)
        build_hourly_taxi_demand(con)
        validate_hourly_taxi_demand(con)
        build_hourly_context(con)
        validate_hourly_context(con)
        build_hourly_mobility(con)
        validate_hourly_mobility(con)

        print("\n")
        print("=" * 80)
        print("WAREHOUSE BUILD COMPLETE")
        print("=" * 80)
        print(f"Database: {DB_PATH}")

    finally:
        con.close()


if __name__ == "__main__":
    main()