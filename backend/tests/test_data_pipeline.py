import json
from pathlib import Path
import pandas as pd
import pytest

from backend.app.services import data_access
from backend.app.services.data_quality import (
    check_sales_data_quality,
    check_marketing_data_quality,
    check_inventory_data_quality,
)

ROOT = Path(__file__).resolve().parents[2]


def test_sales_net_revenue_formula():
    """Verify net_revenue = max(0.0, quantity * unit_price * (1 - discount_pct) - return_value)."""
    orders = pd.read_csv(ROOT / "data" / "bronze" / "raw_orders.csv")
    sample = orders.head(100).copy()
    
    for _, row in sample.iterrows():
        expected_gross = row["quantity"] * row["unit_price"] * (1.0 - row["discount_pct"])
        ret_val = row.get("return_value", row.get("returns_value", 0.0))
        expected_net = max(0.0, round(expected_gross - ret_val, 2))
        assert abs(row["net_revenue"] - expected_net) <= 0.05, (
            f"Row {row['order_id']}: net_revenue {row['net_revenue']} != expected {expected_net}"
        )


def test_data_quality_checks_pass():
    """Verify Data Quality checkers execute and score high quality for generated Bronze data."""
    orders = pd.read_csv(ROOT / "data" / "bronze" / "raw_orders.csv")
    products = pd.read_csv(ROOT / "data" / "bronze" / "dim_products.csv")
    marketing = pd.read_csv(ROOT / "data" / "bronze" / "raw_marketing.csv")
    inventory = pd.read_csv(ROOT / "data" / "bronze" / "raw_inventory_snapshots.csv")

    sales_dq = check_sales_data_quality(orders, products)
    marketing_dq = check_marketing_data_quality(marketing)
    inventory_dq = check_inventory_data_quality(inventory)

    assert sales_dq["data_quality_score"] >= 0.95
    assert marketing_dq["data_quality_score"] >= 0.95
    assert inventory_dq["data_quality_score"] >= 0.95


def test_gold_table_grains():
    """Verify Gold tables exist and have expected primary key grains."""
    kpi_daily = pd.read_csv(ROOT / "data" / "gold" / "kpi_region_daily.csv")
    prod_daily = pd.read_csv(ROOT / "data" / "gold" / "product_performance_daily.csv")

    # Grain 1: date x region x channel
    dups_kpi = kpi_daily.duplicated(subset=["date", "region", "channel"]).sum()
    assert dups_kpi == 0, f"Found {dups_kpi} duplicate grain entries in kpi_region_daily"

    # Grain 2: date x product_id x category x region
    dups_prod = prod_daily.duplicated(subset=["date", "product_id", "category", "region"]).sum()
    assert dups_prod == 0, f"Found {dups_prod} duplicate grain entries in product_performance_daily"


def test_inventory_availability_derived_correctly():
    """Verify inventory availability_pct is bounded [0, 1] or [0, 100] and derived without storing stockout_days at snapshot grain."""
    inv_snapshots = pd.read_csv(ROOT / "data" / "bronze" / "raw_inventory_snapshots.csv")
    assert "stockout_days" not in inv_snapshots.columns, "Snapshot grain must NOT store stockout_days"

    inv_daily = pd.read_csv(ROOT / "data" / "gold" / "inventory_daily.csv")
    assert "availability_pct" in inv_daily.columns
    assert (inv_daily["availability_pct"] >= 0.0).all()
    assert (inv_daily["availability_pct"] <= 1.0).all() or (inv_daily["availability_pct"] <= 100.0).all()


def test_ground_truth_isolation():
    """Verify production analytics modules do not import or access ground_truth_drivers.csv."""
    import inspect
    import backend.app.services.analytics as analytics
    import backend.app.services.evidence as evidence
    import backend.app.services.narrative as narrative

    for module in [analytics, evidence, narrative]:
        src = inspect.getsource(module)
        assert "ground_truth_drivers.csv" not in src, (
            f"Module {module.__name__} violates ground truth isolation!"
        )
