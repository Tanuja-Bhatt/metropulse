from pathlib import Path

import pandas as pd
import geopandas as gpd
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]

WEATHER_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "weather"
    / "nyc_hourly_weather_2024-04-01_2024-06-30.csv"
)


def profile_weather():
    print("=" * 70)
    print("WEATHER PROFILE")
    print("=" * 70)

    df = pd.read_csv(WEATHER_FILE)

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nData types:")
    print(df.dtypes)

    print("\nMissing values:")
    print(df.isna().sum())

    print("\nDuplicate timestamps:")
    print(df["time"].duplicated().sum())

    df["time"] = pd.to_datetime(df["time"])

    print("\nTimestamp range:")
    print(df["time"].min())
    print(df["time"].max())

    print("\nTimestamp frequency:")
    print(
        df["time"]
        .sort_values()
        .diff()
        .value_counts()
        .head(10)
    )

    print("\nWeather code distribution:")
    print(df["weather_code"].value_counts().sort_index())

    print()


SUBWAY_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "subway"
    / "nyc_subway_hourly_ridership_2024-04-01_2024-06-30.csv"
)

def profile_subway():
    print("=" * 70)
    print("SUBWAY PROFILE")
    print("=" * 70)

    df = pd.read_csv(SUBWAY_FILE)

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nData types:")
    print(df.dtypes)

    print("\nMissing values:")
    print(df.isna().sum())

    df["transit_timestamp"] = pd.to_datetime(
        df["transit_timestamp"]
    )

    print("\nTimestamp range:")
    print(df["transit_timestamp"].min())
    print(df["transit_timestamp"].max())

    print("\nDuplicate timestamps:")
    print(df["transit_timestamp"].duplicated().sum())

    print("\nRidership summary:")
    print(df["total_ridership"].describe())

    print("\nTransfer summary:")
    print(df["total_transfers"].describe())

    print("\nZero-ridership hours:")
    print(
        (df["total_ridership"] == 0).sum()
    )

    print()

ZONE_LOOKUP_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "zones"
    / "taxi_zone_lookup.csv"
)

ZONE_SHP_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "zones"
    / "taxi_zones"
    / "taxi_zones.shp"
)

TAXI_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "taxi"
)

def profile_zones():
    print("=" * 70)
    print("TAXI ZONE PROFILE")
    print("=" * 70)

    lookup = pd.read_csv(ZONE_LOOKUP_FILE)

    print("\nLookup shape:")
    print(lookup.shape)

    print("\nLookup columns:")
    print(lookup.columns.tolist())

    print("\nMissing values:")
    print(lookup.isna().sum())

    print("\nDuplicate LocationIDs:")
    print(
        lookup["LocationID"].duplicated().sum()
    )

    print("\nBorough distribution:")
    print(lookup["Borough"].value_counts(dropna=False))

    print("\nService zone distribution:")
    print(
        lookup["service_zone"]
        .value_counts(dropna=False)
    )

    zones = gpd.read_file(ZONE_SHP_FILE)


    print("\nGeospatial shape:")
    print(zones.shape)

    print("\nGeospatial columns:")
    print(zones.columns.tolist())

    print("\nCRS:")
    print(zones.crs)

    print("\nMissing geometry:")
    print(zones.geometry.isna().sum())

    print("\nInvalid geometry:")
    print((~zones.geometry.is_valid).sum())

    print("\nDuplicate LocationIDs in geometry:")
    print(
        zones["LocationID"].duplicated().sum()
    )

    print()

def profile_taxi():

    print("=" * 70)
    print("TAXI PROFILE")
    print("=" * 70)

    con = duckdb.connect()

    taxi_pattern = str(
        TAXI_DIR / "yellow_tripdata_2024-*.parquet"
    )

    print("\nFiles:")

    print(
        con.sql(
            f"""
            SELECT DISTINCT file_name
            FROM parquet_file_metadata(
                '{taxi_pattern}'
            )
            ORDER BY file_name
            """
        )
    )

    print("\nColumn information:")

    print(
        con.sql(
            f"""
            DESCRIBE
            SELECT *
            FROM read_parquet(
                '{taxi_pattern}'
            )
            """
        )
    )

    print("\nTotal rows:")

    print(
        con.sql(
            f"""
            SELECT COUNT(*) AS total_rows
            FROM read_parquet(
                '{taxi_pattern}'
            )
            """
        )
    )

    print("\nMonthly row counts:")

    print(
        con.sql(
            f"""
            SELECT
                DATE_TRUNC(
                    'month',
                    tpep_pickup_datetime
                ) AS pickup_month,
                COUNT(*) AS row_count
            FROM read_parquet(
                '{taxi_pattern}'
            )
            GROUP BY 1
            ORDER BY 1
            """
        )
    )

    print("\nPickup timestamp range:")

    print(
        con.sql(
            f"""
            SELECT
                MIN(tpep_pickup_datetime) AS min_pickup,
                MAX(tpep_pickup_datetime) AS max_pickup
            FROM read_parquet(
                '{taxi_pattern}'
            )
            """
        )
    )

    print("\nDropoff timestamp range:")

    print(
        con.sql(
            f"""
            SELECT
                MIN(tpep_dropoff_datetime) AS min_dropoff,
                MAX(tpep_dropoff_datetime) AS max_dropoff
            FROM read_parquet(
                '{taxi_pattern}'
            )
            """
        )
    )

    print("\nNull counts:")

    print(
        con.sql(
            f"""
            SELECT
                COUNT(*) AS total_rows,

                COUNT(*) FILTER (
                    WHERE tpep_pickup_datetime IS NULL
                ) AS null_pickup,

                COUNT(*) FILTER (
                    WHERE tpep_dropoff_datetime IS NULL
                ) AS null_dropoff,

                COUNT(*) FILTER (
                    WHERE PULocationID IS NULL
                ) AS null_pickup_zone,

                COUNT(*) FILTER (
                    WHERE DOLocationID IS NULL
                ) AS null_dropoff_zone,

                COUNT(*) FILTER (
                    WHERE passenger_count IS NULL
                ) AS null_passenger_count,

                COUNT(*) FILTER (
                    WHERE trip_distance IS NULL
                ) AS null_trip_distance,

                COUNT(*) FILTER (
                    WHERE fare_amount IS NULL
                ) AS null_fare_amount,

                COUNT(*) FILTER (
                    WHERE total_amount IS NULL
                ) AS null_total_amount

            FROM read_parquet(
                '{taxi_pattern}'
            )
            """
        )
    )

    print("\nBasic numerical summary:")

    print(
        con.sql(
            f"""
            SELECT

                MIN(trip_distance) AS min_distance,
                MAX(trip_distance) AS max_distance,
                AVG(trip_distance) AS avg_distance,

                MIN(fare_amount) AS min_fare,
                MAX(fare_amount) AS max_fare,
                AVG(fare_amount) AS avg_fare,

                MIN(total_amount) AS min_total_amount,
                MAX(total_amount) AS max_total_amount,
                AVG(total_amount) AS avg_total_amount,

                MIN(passenger_count) AS min_passengers,
                MAX(passenger_count) AS max_passengers,
                AVG(passenger_count) AS avg_passengers

            FROM read_parquet(
                '{taxi_pattern}'
            )
            """
        )
    )

    print("\nPayment type distribution:")

    print(
        con.sql(
            f"""
            SELECT
                payment_type,
                COUNT(*) AS trip_count
            FROM read_parquet(
                '{taxi_pattern}'
            )
            GROUP BY payment_type
            ORDER BY trip_count DESC
            """
        )
    )

    print("\nVendor distribution:")

    print(
        con.sql(
            f"""
            SELECT
                VendorID,
                COUNT(*) AS trip_count
            FROM read_parquet(
                '{taxi_pattern}'
            )
            GROUP BY VendorID
            ORDER BY trip_count DESC
            """
        )
    )

    print("\nPickup/dropoff zone coverage:")

    print(
        con.sql(
            f"""
            SELECT
                COUNT(*) FILTER (
                    WHERE PULocationID IS NULL
                ) AS null_pickup_zone,

                COUNT(*) FILTER (
                    WHERE DOLocationID IS NULL
                ) AS null_dropoff_zone,

                COUNT(DISTINCT PULocationID)
                    AS distinct_pickup_zones,

                COUNT(DISTINCT DOLocationID)
                    AS distinct_dropoff_zones

            FROM read_parquet(
                '{taxi_pattern}'
            )
            """
        )
    )

    con.close()

if __name__ == "__main__":
    profile_weather()
    profile_subway()
    profile_zones()
    profile_taxi()