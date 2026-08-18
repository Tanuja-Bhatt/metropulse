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

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

LATITUDE = 40.7128
LONGITUDE = -74.0060

START_DATE = "2024-04-01"
END_DATE = "2024-06-30"

TIMEZONE = "America/New_York"

HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "rain",
    "snowfall",
    "weather_code",
    "wind_speed_10m",
    "cloud_cover",
]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "weather"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata" / "weather"


# -------------------------------------------------------------------
# Utility
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

def fetch_weather() -> dict:
    """Fetch historical hourly weather from Open-Meteo."""

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": ",".join(HOURLY_VARIABLES),
        "timezone": TIMEZONE,
    }

    print("[REQUEST] Open-Meteo historical weather API")

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=120,
    )

    response.raise_for_status()

    payload = response.json()

    if payload.get("error"):
        raise RuntimeError(
            f"Open-Meteo API error: {payload.get('reason')}"
        )

    return payload


# -------------------------------------------------------------------
# Validation
# -------------------------------------------------------------------

def validate_payload(payload: dict) -> pd.DataFrame:
    """Validate and convert API response into a DataFrame."""

    if "hourly" not in payload:
        raise ValueError("API response does not contain hourly data.")

    hourly = payload["hourly"]

    required_columns = {"time", *HOURLY_VARIABLES}

    missing_columns = required_columns - set(hourly.keys())

    if missing_columns:
        raise ValueError(
            f"Missing hourly variables: {missing_columns}"
        )

    df = pd.DataFrame(hourly)

    if df.empty:
        raise ValueError("Weather dataset is empty.")

    df["time"] = pd.to_datetime(df["time"])

    if df["time"].duplicated().any():
        raise ValueError("Weather dataset contains duplicate timestamps.")

    if not df["time"].is_monotonic_increasing:
        raise ValueError(
            "Weather timestamps are not monotonically increasing."
        )

    return df


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():

    print("=" * 70)
    print("MetroPulse — Open-Meteo Weather Ingestion")
    print("=" * 70)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    output_file = RAW_DIR / "nyc_hourly_weather_2024-04-01_2024-06-30.csv"
    metadata_file = (
        METADATA_DIR
        / "nyc_hourly_weather_2024-04-01_2024-06-30.json"
    )

    # Idempotency
    if output_file.exists():
        print(f"[SKIP] Already exists: {output_file}")
        return

    payload = fetch_weather()

    df = validate_payload(payload)

    df.to_csv(output_file, index=False)

    # Expected number of hourly records.
    expected_hours = len(
    pd.date_range(
        start=f"{START_DATE} 00:00:00",
        end=f"{END_DATE} 23:00:00",
        freq="h",
    )
)

    metadata = {
        "source": "Open-Meteo Historical Weather API",
        "source_url": BASE_URL,
        "dataset": "NYC Hourly Historical Weather",
        "start_date": START_DATE,
        "end_date": END_DATE,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "timezone": TIMEZONE,
        "hourly_variables": HOURLY_VARIABLES,
        "extraction_timestamp_utc": utc_timestamp(),
        "file_name": output_file.name,
        "file_size_bytes": output_file.stat().st_size,
        "sha256": sha256_file(output_file),
        "row_count": len(df),
        "expected_hourly_rows": expected_hours,
        "min_timestamp": str(df["time"].min()),
        "max_timestamp": str(df["time"].max()),
    }

    write_metadata(metadata_file, metadata)

    print(f"[SUCCESS] Saved weather data: {output_file}")
    print(f"[ROWS] {len(df):,}")
    print(f"[EXPECTED] {expected_hours:,}")
    print(f"[METADATA] {metadata_file}")

    print("=" * 70)
    print("Weather ingestion complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()