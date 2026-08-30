from __future__ import annotations

from datetime import datetime, timezone
import json
import uuid
import pandas as pd

from backend.app.config import settings
from backend.app import db

GOLD = settings.root_dir / "data" / "gold"
META = settings.root_dir / "data" / "metadata"


def _read_gold(name: str, parse_dates: list[str] | None = None) -> pd.DataFrame:
    return pd.read_csv(GOLD / f"{name}.csv", parse_dates=parse_dates or [])


def get_kpi_region_daily(region: str) -> pd.DataFrame:
    if db.duckdb_available():
        con = db.connect(read_only=True)
        try:
            return con.execute("SELECT * FROM kpi_region_daily WHERE region = ? ORDER BY date", [region]).fetchdf()
        finally:
            con.close()
    df = _read_gold("kpi_region_daily", ["date"])
    return df[df["region"] == region].copy().sort_values("date")


def get_inventory_daily(region: str) -> pd.DataFrame:
    if db.duckdb_available():
        con = db.connect(read_only=True)
        try:
            return con.execute("SELECT * FROM inventory_daily WHERE region = ? ORDER BY date", [region]).fetchdf()
        finally:
            con.close()
    df = _read_gold("inventory_daily", ["date"])
    return df[df["region"] == region].copy().sort_values("date")


def get_product_daily(region: str) -> pd.DataFrame:
    if db.duckdb_available():
        con = db.connect(read_only=True)
        try:
            return con.execute("SELECT * FROM product_performance_daily WHERE region = ? ORDER BY date", [region]).fetchdf()
        finally:
            con.close()
    df = _read_gold("product_performance_daily", ["date"])
    return df[df["region"] == region].copy().sort_values("date")


def get_source_metadata(scenario: str = "main") -> dict:
    meta = json.loads((META / "source_metadata.json").read_text(encoding="utf-8"))
    return meta["source_status"].get(scenario, meta["source_status"]["main"])


def get_dataset_metadata() -> dict:
    return json.loads((META / "source_metadata.json").read_text(encoding="utf-8"))


def append_feedback(payload: dict) -> dict:
    row = {"feedback_id": str(uuid.uuid4()), "created_at": datetime.now(timezone.utc).isoformat(), **payload, "status": "queued_for_validation"}
    path = META / "feedback_log.csv"
    pd.DataFrame([row]).to_csv(path, mode="a", index=False, header=not path.exists())
    return row


def append_telemetry(row: dict) -> None:
    path = META / "telemetry_log.csv"
    pd.DataFrame([row]).to_csv(path, mode="a", index=False, header=not path.exists())
