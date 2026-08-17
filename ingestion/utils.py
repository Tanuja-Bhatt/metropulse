from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


def sha256_file(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(chunk_size):
            sha256.update(chunk)

    return sha256.hexdigest()


def download_file(
    url: str,
    destination: Path,
    retries: int = 3,
    timeout: int = 120,
) -> None:
    """
    Download a file with retry handling.

    Existing files are not downloaded again.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        print(f"[SKIP] Already exists: {destination}")
        return

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            print(f"[DOWNLOAD] Attempt {attempt}/{retries}: {url}")

            with requests.get(url, stream=True, timeout=timeout) as response:
                response.raise_for_status()

                with destination.open("wb") as file:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            file.write(chunk)

            print(f"[SUCCESS] Saved: {destination}")
            return

        except requests.RequestException as error:
            last_error = error

            if destination.exists():
                destination.unlink()

            print(f"[ERROR] Attempt {attempt} failed: {error}")

            if attempt < retries:
                time.sleep(2 ** (attempt - 1))

    raise RuntimeError(
        f"Failed to download after {retries} attempts: {last_error}"
    )


def write_metadata(
    metadata_path: Path,
    metadata: dict,
) -> None:
    """Write ingestion metadata as formatted JSON."""
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, default=str)


def utc_timestamp() -> str:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()