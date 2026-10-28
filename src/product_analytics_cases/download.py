"""Download the two public datasets into ``data/raw/<dataset>/`` and record what arrived.

``python -m product_analytics_cases download olist`` fetches the nine Olist CSV files from a public
Hugging Face mirror (the Kaggle API needs an account and a token, and this repo has neither).
``python -m product_analytics_cases download upworthy`` fetches the exploratory and confirmatory
package files of the Upworthy Research Archive from their OSF download links.

The function refuses to run unless ``LICENCE_CHECK.md`` names the dataset's source, so the licence
row always exists before the bytes do (workspace rule 3). Every file's sha256 and row count go to
``results/data_sources.json``. Files whose published sha256 is known are verified against it.
Only the standard library is used, so the script works before the virtual environment is complete.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
RESULTS = ROOT / "results"
LICENCE_CHECK = ROOT / "LICENCE_CHECK.md"

HF_BASE = "https://huggingface.co/datasets/bulutttt/olist-raw-data/resolve/main/"

# name, url, bytes expected, sha256 expected (None when the mirror publishes no hash)
SOURCES: dict[str, dict[str, list[dict[str, object]]]] = {
    "olist": {
        "licence_marker": "huggingface.co/datasets/bulutttt/olist-raw-data",
        "files": [
            {"name": "olist_customers_dataset.csv", "size": 9033957, "sha256": None},
            {"name": "olist_geolocation_dataset.csv", "size": 61273883,
             "sha256": "b514f6fc991b9566aeba02aa5d67e2c3630f034b60a0e05aa0d082a3b66d88d6"},
            {"name": "olist_order_items_dataset.csv", "size": 15438671,
             "sha256": "0bc4d068c4fe38cbb01bd90e8746e3c613fe7b4baef75fab7b0e329701c3e279"},
            {"name": "olist_order_payments_dataset.csv", "size": 5777138, "sha256": None},
            {"name": "olist_order_reviews_dataset.csv", "size": 14451670,
             "sha256": "012b61c7593e34f51fa614efdf802b9c7056ce6aae5307ddb93236e7cfc797d7"},
            {"name": "olist_orders_dataset.csv", "size": 17654914,
             "sha256": "8df58ef3d2d7e9944010f7beecd9b75367f5588ec6e3c91cec19ae3345ef9ecf"},
            {"name": "olist_products_dataset.csv", "size": 2379446, "sha256": None},
            {"name": "olist_sellers_dataset.csv", "size": 174703, "sha256": None},
            {"name": "product_category_name_translation.csv", "size": 2613, "sha256": None},
        ],
    },
    "upworthy": {
        "licence_marker": "osf.io/download/3vqmp/",
        "files": [
            {"name": "upworthy-archive-exploratory-packages-03.12.2020.csv", "size": 14260949,
             "url": "https://osf.io/download/3vqmp/",
             "sha256": "8368313b060f4015a0c6fb34e6d788163cee29554144aba9390b14922eb9d8ce"},
            {"name": "upworthy-archive-confirmatory-packages-03.12.2020.csv", "size": 66517697,
             "url": "https://osf.io/download/vy8mj/",
             "sha256": "b2a88288c88f2b67d40413c9bdbebe79a1c0b5d9a9354180549f59f3bfff685f"},
        ],
    },
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _row_count(path: Path) -> int:
    """Data rows in a CSV file, counted with the csv module because review text spans lines."""
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        return sum(1 for _ in reader)


def _licence_row_exists(marker: str) -> bool:
    return LICENCE_CHECK.exists() and marker in LICENCE_CHECK.read_text(encoding="utf-8")


def _fetch(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "product-analytics-cases/0.1"})
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(req, timeout=120) as r, tmp.open("wb") as out:
        for chunk in iter(lambda: r.read(1 << 20), b""):
            out.write(chunk)
    tmp.replace(dest)


def download(dataset: str, force: bool = False) -> dict[str, object]:
    """Fetch one dataset, verify it, and merge its record into results/data_sources.json."""
    if dataset not in SOURCES:
        raise SystemExit(f"unknown dataset {dataset!r}, choose one of {sorted(SOURCES)}")
    spec = SOURCES[dataset]
    if not _licence_row_exists(str(spec["licence_marker"])):
        raise SystemExit(f"LICENCE_CHECK.md has no row for {dataset}: write it before downloading")
    folder = RAW / dataset
    folder.mkdir(parents=True, exist_ok=True)
    record: dict[str, object] = {"files": []}
    for item in spec["files"]:
        name = str(item["name"])
        dest = folder / name
        url = str(item.get("url") or HF_BASE + name)
        if force or not dest.exists() or dest.stat().st_size != item["size"]:
            print(f"downloading {name} from {url}")
            _fetch(url, dest)
        digest = _sha256(dest)
        expected = item.get("sha256")
        if expected and digest != expected:
            raise SystemExit(f"{name}: sha256 {digest} does not match the published {expected}")
        if dest.stat().st_size != item["size"]:
            raise SystemExit(f"{name}: size {dest.stat().st_size} differs from the listed {item['size']}")
        rows = _row_count(dest)
        record["files"].append({"name": name, "url": url, "bytes": dest.stat().st_size, "sha256": digest,
                                "sha256_verified_against_publisher": bool(expected), "rows": rows})
        print(f"  {name}: {rows:,} rows, sha256 {digest[:12]}, verified={bool(expected)}")
    record["rows_total"] = sum(int(f["rows"]) for f in record["files"])  # type: ignore[index]
    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / "data_sources.json"
    merged = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    merged[dataset] = record
    out.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return record


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    force = "--force" in args
    names = [a for a in args if not a.startswith("--")] or ["olist", "upworthy"]
    for name in names:
        download(name, force=force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
