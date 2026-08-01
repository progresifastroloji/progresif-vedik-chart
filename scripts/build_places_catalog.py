#!/usr/bin/env python3
"""GeoNames dogum yeri katalogunu indirir ve SQLite veritabanini olusturur."""

from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from place_catalog import build_places_database


BASE_URL = "https://download.geonames.org/export/dump"
FILES = ("cities500.zip", "countryInfo.txt", "admin1CodesASCII.txt")


def _download(name: str, directory: Path) -> Path:
    target = directory / name
    request = urllib.request.Request(
        f"{BASE_URL}/{name}",
        headers={"User-Agent": "VedicAI-PlaceCatalog/1.0 (GeoNames CC-BY-4.0)"},
    )
    with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "data" / "places" / "places.sqlite3"),
    )
    args = parser.parse_args()
    output = Path(args.output).resolve()
    staged_output = output.with_suffix(f"{output.suffix}.tmp")

    try:
        with tempfile.TemporaryDirectory(prefix="vedicai-geonames-") as temp_dir:
            directory = Path(temp_dir)
            downloaded = {name: _download(name, directory) for name in FILES}
            count = build_places_database(
                downloaded["cities500.zip"],
                staged_output,
                country_info_path=downloaded["countryInfo.txt"],
                admin1_codes_path=downloaded["admin1CodesASCII.txt"],
                dataset_name="cities500",
            )
        staged_output.replace(output)
    finally:
        if staged_output.exists():
            staged_output.unlink()
    checksum = hashlib.sha256()
    with output.open("rb") as database:
        while chunk := database.read(1024 * 1024):
            checksum.update(chunk)
    print(f"Katalog hazir: {output}")
    print(f"Yer sayisi: {count}")
    print(f"SHA-256: {checksum.hexdigest()}")


if __name__ == "__main__":
    main()
