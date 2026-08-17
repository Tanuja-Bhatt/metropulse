from pathlib import Path
import sys

import pyarrow.parquet as pq

# Allow imports from the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.utils import (
    download_file,
    sha256_file,
    utc_timestamp,
    write_metadata,
)


BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

MONTHS = ["04", "05", "06"]
YEAR = "2024"

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "taxi"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata" / "taxi"


def download_taxi_month(month: str) -> None:
    filename = f"yellow_tripdata_{YEAR}-{month}.parquet"

    url = f"{BASE_URL}/{filename}"

    destination = RAW_DIR / filename
    metadata_path = METADATA_DIR / f"{filename}.json"

    download_file(
        url=url,
        destination=destination,
    )

    print(f"[VALIDATE] Reading Parquet metadata: {filename}")

    parquet_file = pq.ParquetFile(destination)

    schema = parquet_file.schema_arrow

    schema_definition = [
        {
            "name": field.name,
            "type": str(field.type),
        }
        for field in schema
    ]

    schema_json = str(schema_definition).encode("utf-8")

    schema_fingerprint = __import__("hashlib").sha256(
        schema_json
    ).hexdigest()

    metadata = {
        "source": "NYC Taxi & Limousine Commission",
        "dataset": "Yellow Taxi Trip Records",
        "source_url": url,
        "period": f"{YEAR}-{month}",
        "extraction_timestamp_utc": utc_timestamp(),
        "file_name": filename,
        "file_size_bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
        "row_count": parquet_file.metadata.num_rows,
        "row_groups": parquet_file.num_row_groups,
        "schema_fingerprint": schema_fingerprint,
        "columns": parquet_file.schema_arrow.names,
    }

    write_metadata(metadata_path, metadata)

    print(f"[METADATA] Saved: {metadata_path}")
    print()


def main() -> None:
    print("=" * 70)
    print("MetroPulse — NYC Yellow Taxi Ingestion")
    print("=" * 70)

    for month in MONTHS:
        download_taxi_month(month)

    print("=" * 70)
    print("Taxi ingestion complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()