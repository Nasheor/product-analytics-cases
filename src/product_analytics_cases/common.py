"""Shared helpers for the three case studies.

Each case's ``analysis.py`` opens a DuckDB connection with views over the raw CSV files, runs named
SQL files from its ``sql/`` folder, and writes a results file whose every number carries the name of
the query or function that produced it. The helpers here keep those conventions in one place.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
DERIVED = ROOT / "data" / "derived"
RESULTS = ROOT / "results"
CASES = ROOT / "cases"

OLIST_VIEWS = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}
UPWORTHY_VIEWS = {
    "exploratory": "upworthy-archive-exploratory-packages-03.12.2020.csv",
    "confirmatory": "upworthy-archive-confirmatory-packages-03.12.2020.csv",
}


def raw_present(dataset: str) -> bool:
    views = OLIST_VIEWS if dataset == "olist" else UPWORTHY_VIEWS
    return all((RAW / dataset / f).exists() for f in views.values())


def connect(dataset: str) -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with one view per raw file of ``dataset`` (``olist`` or ``upworthy``)."""
    views = OLIST_VIEWS if dataset == "olist" else UPWORTHY_VIEWS
    con = duckdb.connect(database=":memory:")
    con.execute("SET threads TO 1")  # a fixed summation order keeps floating sums identical run to run
    for name, fname in views.items():
        path = (RAW / dataset / fname).as_posix()
        con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_csv('{path}', header=true, all_varchar=false)")
    return con


def sql_text(case_dir: Path, name: str) -> str:
    return (case_dir / "sql" / name).read_text(encoding="utf-8")


def run_sql(con: duckdb.DuckDBPyConnection, case_dir: Path, name: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    """Run ``sql/<name>`` from the case folder and return a DataFrame. Named parameters use ``$name``."""
    return con.execute(sql_text(case_dir, name), params or {}).df()


class Results:
    """Collects numbers, tables and figures for one case with the source of each item."""

    def __init__(self, case: str) -> None:
        self.case = case
        self.numbers: dict[str, dict[str, Any]] = {}
        self.tables: dict[str, dict[str, Any]] = {}
        self.figures: dict[str, dict[str, Any]] = {}
        self.notes: dict[str, str] = {}

    def number(self, key: str, value: Any, source: str, unit: str = "") -> None:
        if isinstance(value, float):
            value = round(value, 6)
        self.numbers[key] = {"value": value, "source": source, "unit": unit}

    def table(self, key: str, df: pd.DataFrame, source: str, max_rows: int = 200) -> None:
        df = df.head(max_rows).copy()
        for c in df.columns:
            if str(df[c].dtype).startswith("datetime"):
                df[c] = df[c].astype(str)
        self.tables[key] = {"source": source, "columns": list(map(str, df.columns)),
                            "rows": json.loads(df.to_json(orient="values", double_precision=6))}

    def figure(self, key: str, path: Path, source: str) -> None:
        self.figures[key] = {"file": path.relative_to(ROOT).as_posix(), "source": source}

    def note(self, key: str, text: str) -> None:
        self.notes[key] = text

    def write(self) -> Path:
        RESULTS.mkdir(exist_ok=True)
        out = RESULTS / f"{self.case}.json"
        payload = {"case": self.case, "numbers": self.numbers, "tables": self.tables,
                   "figures": self.figures, "notes": self.notes}
        out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return out


def write_derived(dataset: str, name: str, df: pd.DataFrame) -> Path:
    """Save an aggregate under data/derived/<dataset>/ (the folder carries the licence note)."""
    folder = DERIVED / dataset
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    df.round(6).to_csv(path, index=False)
    return path


def load_results(case: str) -> dict[str, Any]:
    return json.loads((RESULTS / f"{case}.json").read_text(encoding="utf-8"))


def value(case: str, key: str) -> Any:
    return load_results(case)["numbers"][key]["value"]
