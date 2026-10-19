"""Dataset downloader and documentation script for ASTRA-GUARD.

This script documents official sources, expected file sizes, and licenses for:
1. ESA-ADB (ESA Anomaly Detection Benchmark)
2. CelesTrak Active Satellites & Debris GP/TLE Catalog
3. ESA Kelvins Collision Avoidance Challenge (CDM Dataset)
4. Sen1Floods11 Sentinel-1 SAR Flood Event Chips

Rule (rules.md §9): Large datasets are NOT auto-downloaded by AI agents.
Users can run this script manually when full offline training is desired.
Small samples are pre-committed under data/samples/ for immediate local evaluation.
"""

import argparse
import os
import sys
import urllib.request
from typing import Any

DATASETS: dict[str, dict[str, Any]] = {
    "celestrak": {
        "name": "CelesTrak GP Active Satellites",
        "size": "~4.8 MB",
        "license": "Public Domain (CelesTrak)",
        "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
        "destination": "data/raw/celestrak_active.tle",
        "description": "General Perturbations (GP) element sets (TLE format) for active space objects.",
    },
    "esa_adb": {
        "name": "ESA Spacecraft Anomaly Detection Benchmark (ESA-ADB)",
        "size": "~1.2 GB",
        "license": "ESA Open Access / Academic Use",
        "url": "https://github.com/esa/AD-benchmarking",
        "destination": "data/raw/esa_adb/",
        "description": "Multi-mission telemetry with validated ground-truth anomaly events.",
    },
    "kelvins_cdm": {
        "name": "ESA Kelvins Spacecraft Collision Avoidance Challenge",
        "size": "~180 MB",
        "license": "ESA Kelvins Challenge License (Open Research)",
        "url": "https://kelvins.esa.int/collision-avoidance-challenge/data/",
        "destination": "data/raw/kelvins_cdm/",
        "description": "Conjunction Data Messages (CDMs) time-series tracking collision probabilities.",
    },
    "sen1floods11": {
        "name": "Sen1Floods11 Sentinel-1 Flood Dataset",
        "size": "~2.4 GB",
        "license": "CC-BY-4.0",
        "url": "https://github.com/cloudtostreet/Sen1Floods11",
        "destination": "data/raw/sen1floods11/",
        "description": "Raw Sentinel-1 SAR chips paired with permanent water and flood event annotations.",
    },
}


def print_catalog() -> None:
    """Print documentation table of all supported datasets."""
    print("=" * 80)
    print("ASTRA-GUARD External Datasets Catalog")
    print("=" * 80)
    for key, info in DATASETS.items():
        print(f"Key:         {key}")
        print(f"Name:        {info['name']}")
        print(f"Size:        {info['size']}")
        print(f"License:     {info['license']}")
        print(f"URL:         {info['url']}")
        print(f"Target Path: {info['destination']}")
        print(f"Description: {info['description']}")
        print("-" * 80)


def download_dataset(key: str, force: bool = False) -> None:
    """Download a dataset if it has a direct public file URL."""
    if key not in DATASETS:
        print(f"Error: Unknown dataset '{key}'. Available: {list(DATASETS.keys())}")
        sys.exit(1)

    info = DATASETS[key]
    dest = info["destination"]
    url = info["url"]

    if os.path.exists(dest) and not force:
        print(f"Dataset '{key}' already exists at {dest}. Use --force to re-download.")
        return

    os.makedirs(os.path.dirname(dest) if os.path.dirname(dest) else ".", exist_ok=True)

    if key == "celestrak":
        print(f"Downloading {info['name']} ({info['size']}) from {url}...")
        try:
            urllib.request.urlretrieve(url, dest)
            print(f"Successfully saved to {dest}")
        except Exception as e:  # noqa: BLE001
            print(f"Failed to download {key}: {e}")
    else:
        print(f"\n[NOTE] {info['name']} requires user registration or repository cloning.")
        print(f"  Size: {info['size']}")
        print(f"  Official URL: {url}")
        print(f"  Please download or clone into: {dest}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ASTRA-GUARD Dataset Downloader & Documentation")
    parser.add_argument("--list", action="store_true", help="List all datasets and specifications")
    parser.add_argument("--dataset", type=str, choices=list(DATASETS.keys()), help="Dataset key to download")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing downloads")
    args = parser.parse_args()

    if args.list or not args.dataset:
        print_catalog()
        if not args.dataset:
            print("\nUsage example to download CelesTrak TLEs: python scripts/download_datasets.py --dataset celestrak")
            return

    if args.dataset:
        download_dataset(args.dataset, force=args.force)


if __name__ == "__main__":
    main()
