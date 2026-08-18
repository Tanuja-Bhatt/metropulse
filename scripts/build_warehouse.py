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

        print("\n")
        print("=" * 80)
        print("WAREHOUSE STAGING BUILD COMPLETE")
        print("=" * 80)
        print(f"Database: {DB_PATH}")

    finally:
        con.close()


if __name__ == "__main__":
    main()