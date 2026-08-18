from pathlib import Path
import hashlib
import json
import sys

import pandas as pd
import requests


# Allow imports from project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.utils import utc_timestamp, write_metadata


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

API_URL = "https://data.ny.gov/resource/wujg-7c2s.json"

START_TIMESTAMP = "2024-04-01T00:00:00"
END_TIMESTAMP = "2024-07-01T00:00:00"

OUTPUT_FILE = (
    "nyc_subway_hourly_ridership_2024-04-01_2024-06-30.csv"
)

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "subway"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata" / "subway"


# -------------------------------------------------------------------
# Hash
# -------------------------------------------------------------------

def sha256_file(file_path: Path) -> str:
    """Return SHA-256 hash for a file."""

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.hexdigest()


# -------------------------------------------------------------------
# API request
# -------------------------------------------------------------------

def fetch_subway_data() -> pd.DataFrame:
    """
    Query the official MTA dataset.

    We aggregate ridership to one row per local NYC hour.
    """

    params = {
        "$select": (
            "transit_timestamp,"
            "sum(ridership) as total_ridership,"
            "sum(transfers) as total_transfers"
        ),
        "$where": (
            f"transit_timestamp >= '{START_TIMESTAMP}' "
            f"AND transit_timestamp < '{END_TIMESTAMP}' "
            "AND transit_mode = 'subway'"
        ),
        "$group": "transit_timestamp",
        "$order": "transit_timestamp",
        "$limit": 50000,
    }

    print("[REQUEST] Querying official MTA Subway Hourly Ridership API")

    response = requests.get(
        API_URL,
        params=params,
        timeout=120,
    )

    response.raise_for_status()

    records = response.json()

    if not records:
        raise ValueError(
            "MTA API returned no records for the requested period."
        )

    df = pd.DataFrame(records)

    return df


# -------------------------------------------------------------------
# Validation
# -------------------------------------------------------------------

def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate returned MTA hourly data."""

    required_columns = {
        "transit_timestamp",
        "total_ridership",
        "total_transfers",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing expected columns: {missing}"
        )

    df["transit_timestamp"] = pd.to_datetime(
        df["transit_timestamp"]
    )

    df["total_ridership"] = pd.to_numeric(
        df["total_ridership"],
        errors="coerce",
    )

    df["total_transfers"] = pd.to_numeric(
        df["total_transfers"],
        errors="coerce",
    )

    if df["transit_timestamp"].duplicated().any():
        raise ValueError(
            "Duplicate hourly timestamps detected."
        )

    if not df["transit_timestamp"].is_monotonic_increasing:
        raise ValueError(
            "Timestamps are not ordered."
        )

    if df["total_ridership"].isna().any():
        raise ValueError(
            "Null ridership values detected."
        )

    if (df["total_ridership"] < 0).any():
        raise ValueError(
            "Negative ridership values detected."
        )

    return df


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():

    print("=" * 70)
    print("MetroPulse — MTA Subway Ridership Ingestion")
    print("=" * 70)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    output_file = RAW_DIR / OUTPUT_FILE

    metadata_file = (
        METADATA_DIR
        / f"{OUTPUT_FILE}.json"
    )

    # ---------------------------------------------------------------
    # Idempotency
    # ---------------------------------------------------------------

    if output_file.exists():

        print(f"[SKIP] Already exists: {output_file}")
        return

    # ---------------------------------------------------------------
    # API query
    # ---------------------------------------------------------------

    df = fetch_subway_data()

    print(f"[API] Received {len(df):,} hourly records")

    # ---------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------

    df = validate_data(df)

    # ---------------------------------------------------------------
    # Save
    # ---------------------------------------------------------------

    df.to_csv(
        output_file,
        index=False,
    )

    # ---------------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------------

    expected_hours = len(
        pd.date_range(
            start="2024-04-01 00:00:00",
            end="2024-06-30 23:00:00",
            freq="h",
        )
    )

    metadata = {
        "source": "Metropolitan Transportation Authority",
        "dataset": "MTA Subway Hourly Ridership: 2020-2024",
        "dataset_id": "wujg-7c2s",
        "source_url": API_URL,
        "start_timestamp": START_TIMESTAMP,
        "end_timestamp_exclusive": END_TIMESTAMP,
        "filter": "transit_mode = subway",
        "aggregation": (
            "GROUP BY transit_timestamp; "
            "SUM(ridership), SUM(transfers)"
        ),
        "extraction_timestamp_utc": utc_timestamp(),
        "file_name": output_file.name,
        "file_size_bytes": output_file.stat().st_size,
        "sha256": sha256_file(output_file),
        "row_count": len(df),
        "expected_hourly_rows": expected_hours,
        "min_timestamp": str(df["transit_timestamp"].min()),
        "max_timestamp": str(df["transit_timestamp"].max()),
        "total_ridership": float(
            df["total_ridership"].sum()
        ),
        "total_transfers": float(
            df["total_transfers"].sum()
        ),
    }

    write_metadata(
        metadata_file,
        metadata,
    )

    print(
        f"[SUCCESS] Saved: {output_file}"
    )

    print(
        f"[ROWS] {len(df):,}"
    )

    print(
        f"[EXPECTED] {expected_hours:,}"
    )

    print(
        f"[TOTAL RIDERSHIP] "
        f"{df['total_ridership'].sum():,.0f}"
    )

    print(
        f"[METADATA] {metadata_file}"
    )

    print("=" * 70)
    print("MTA Subway ingestion complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()