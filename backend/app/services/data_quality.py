from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd
import numpy as np


VALID_REGIONS = {"North", "South", "East", "West"}
VALID_CHANNELS = {"Web", "App", "Mobile App", "Marketplace"}


def check_sales_data_quality(df: pd.DataFrame, dim_products: pd.DataFrame | None = None) -> dict:
    """Check Sales (orders) data quality."""
    issues = []
    total_rows = len(df)
    if total_rows == 0:
        return {"data_quality_score": 0.0, "total_rows": 0, "issues": ["Sales dataset is empty"]}

    missing_vals = df[["order_id", "date", "region", "net_revenue"]].isnull().sum().sum()
    if missing_vals > 0:
        issues.append(f"Found {missing_vals} missing values in critical sales columns")

    neg_qty = (df["quantity"] <= 0).sum()
    if neg_qty > 0:
        issues.append(f"Found {neg_qty} rows with non-positive quantity")

    neg_price = (df["unit_price"] <= 0).sum()
    if neg_price > 0:
        issues.append(f"Found {neg_price} rows with non-positive unit_price")

    invalid_reg = (~df["region"].isin(VALID_REGIONS)).sum()
    if invalid_reg > 0:
        issues.append(f"Found {invalid_reg} rows with invalid region")

    dup_lines = df.duplicated(subset=["order_id", "line_id"]).sum() if "line_id" in df.columns else 0
    if dup_lines > 0:
        issues.append(f"Found {dup_lines} duplicate order line IDs")

    ref_errors = 0
    if dim_products is not None and "product_id" in df.columns and "product_id" in dim_products.columns:
        valid_pids = set(dim_products["product_id"].unique())
        ref_errors = (~df["product_id"].isin(valid_pids)).sum()
        if ref_errors > 0:
            issues.append(f"Found {ref_errors} sales rows with missing product keys (referential integrity)")

    error_count = missing_vals + neg_qty + neg_price + invalid_reg + dup_lines + ref_errors
    score = max(0.0, min(1.0, 1.0 - (error_count / (total_rows * 5.0))))
    return {
        "data_quality_score": round(score, 4),
        "total_rows": total_rows,
        "issues": issues,
    }


def check_marketing_data_quality(df: pd.DataFrame) -> dict:
    """Check Marketing daily data quality."""
    issues = []
    total_rows = len(df)
    if total_rows == 0:
        return {"data_quality_score": 0.0, "total_rows": 0, "issues": ["Marketing dataset is empty"]}

    missing_vals = df[["date", "region", "spend", "sessions"]].isnull().sum().sum()
    if missing_vals > 0:
        issues.append(f"Found {missing_vals} missing values in marketing columns")

    neg_spend = (df["spend"] < 0).sum()
    if neg_spend > 0:
        issues.append(f"Found {neg_spend} rows with negative marketing spend")

    zero_sessions = (df["sessions"] == 0).sum()
    if zero_sessions > 0:
        issues.append(f"Found {zero_sessions} rows with 0 sessions")

    invalid_reg = (~df["region"].isin(VALID_REGIONS)).sum()
    if invalid_reg > 0:
        issues.append(f"Found {invalid_reg} rows with invalid region")

    error_count = missing_vals + neg_spend + invalid_reg
    score = max(0.0, min(1.0, 1.0 - (error_count / (total_rows * 4.0))))
    return {
        "data_quality_score": round(score, 4),
        "total_rows": total_rows,
        "issues": issues,
    }


def check_inventory_data_quality(df: pd.DataFrame) -> dict:
    """Check Inventory snapshot data quality."""
    issues = []
    total_rows = len(df)
    if total_rows == 0:
        return {"data_quality_score": 0.0, "total_rows": 0, "issues": ["Inventory dataset is empty"]}

    missing_vals = df[["date", "region", "product_id", "stock_level"]].isnull().sum().sum()
    if missing_vals > 0:
        issues.append(f"Found {missing_vals} missing values in inventory columns")

    neg_stock = (df["stock_level"] < 0).sum()
    if neg_stock > 0:
        issues.append(f"Found {neg_stock} rows with negative stock level")

    invalid_flags = (~df["stockout_flag"].isin([0, 1])).sum()
    if invalid_flags > 0:
        issues.append(f"Found {invalid_flags} invalid stockout_flag values")

    error_count = missing_vals + neg_stock + invalid_flags
    score = max(0.0, min(1.0, 1.0 - (error_count / (total_rows * 3.0))))
    return {
        "data_quality_score": round(score, 4),
        "total_rows": total_rows,
        "issues": issues,
    }
