from pathlib import Path
import sys
import zipfile

import pandas as pd

# Allow imports from the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.utils import (
    download_file,
    sha256_file,
    utc_timestamp,
    write_metadata,
)


# Official NYC TLC sources
LOOKUP_URL = (
    "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
)

SHAPEFILE_URL = (
    "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip"
)


RAW_DIR = PROJECT_ROOT / "data" / "raw" / "zones"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata" / "zones"


def process_lookup_table() -> None:
    """Download and validate the official taxi zone lookup table."""

    filename = "taxi_zone_lookup.csv"

    destination = RAW_DIR / filename
    metadata_path = METADATA_DIR / f"{filename}.json"

    download_file(
        url=LOOKUP_URL,
        destination=destination,
    )

    print(f"[VALIDATE] Reading lookup table: {filename}")

    df = pd.read_csv(destination)

    required_columns = {
        "LocationID",
        "Borough",
        "Zone",
        "service_zone",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Lookup table is missing required columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError("Lookup table is empty.")

    if df["LocationID"].duplicated().any():
        raise ValueError(
            "Lookup table contains duplicate LocationID values."
        )

    metadata = {
        "source": "NYC Taxi & Limousine Commission",
        "dataset": "Taxi Zone Lookup Table",
        "source_url": LOOKUP_URL,
        "extraction_timestamp_utc": utc_timestamp(),
        "file_name": filename,
        "file_size_bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
        "row_count": len(df),
        "columns": list(df.columns),
        "unique_location_ids": int(df["LocationID"].nunique()),
    }

    write_metadata(metadata_path, metadata)

    print(f"[SUCCESS] Lookup table validated.")
    print(f"[ROWS] {len(df):,}")
    print(f"[METADATA] {metadata_path}")
    print()


def process_shapefile() -> None:
    """Download and validate the official taxi-zone shapefile ZIP."""

    filename = "taxi_zones.zip"

    destination = RAW_DIR / filename
    metadata_path = METADATA_DIR / f"{filename}.json"

    download_file(
        url=SHAPEFILE_URL,
        destination=destination,
    )

    print(f"[VALIDATE] Inspecting ZIP archive: {filename}")

    with zipfile.ZipFile(destination, "r") as archive:

        if archive.testzip() is not None:
            raise ValueError(
                "Taxi zone ZIP archive failed integrity testing."
            )

        members = archive.namelist()

    required_extensions = {".shp", ".shx", ".dbf"}

    archive_extensions = {
        Path(member).suffix.lower()
        for member in members
    }

    missing_extensions = required_extensions - archive_extensions

    if missing_extensions:
        raise ValueError(
            f"Taxi zone ZIP is missing required shapefile components: "
            f"{missing_extensions}"
        )

    metadata = {
        "source": "NYC Taxi & Limousine Commission",
        "dataset": "Taxi Zone Shapefile",
        "source_url": SHAPEFILE_URL,
        "extraction_timestamp_utc": utc_timestamp(),
        "file_name": filename,
        "file_size_bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
        "archive_member_count": len(members),
        "archive_members": members,
    }

    write_metadata(metadata_path, metadata)

    print("[SUCCESS] Taxi zone ZIP validated.")
    print(f"[FILES] {len(members)} archive members")
    print(f"[METADATA] {metadata_path}")
    print()


def main() -> None:

    print("=" * 70)
    print("MetroPulse — NYC Taxi Zone Ingestion")
    print("=" * 70)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    process_lookup_table()
    process_shapefile()

    print("=" * 70)
    print("Taxi zone ingestion complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()