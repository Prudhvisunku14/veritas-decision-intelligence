from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "veritas_kpi.duckdb"
BRONZE = ROOT / "data" / "bronze"
GOLD = ROOT / "data" / "gold"
GOLD.mkdir(parents=True, exist_ok=True)


def build_gold_csvs() -> None:
    sales = pd.read_csv(BRONZE / "raw_orders.csv", parse_dates=["date", "order_ts"])
    marketing = pd.read_csv(BRONZE / "raw_marketing.csv", parse_dates=["date"])
    inventory = pd.read_csv(BRONZE / "raw_inventory_snapshots.csv", parse_dates=["date", "snapshot_ts"])

    sales_daily = sales.groupby(["date", "region", "channel"], as_index=False).agg(
        revenue=("net_revenue", "sum"), orders=("order_id", "nunique"), cogs=("cogs", "sum")
    )
    marketing_daily = marketing.groupby(["date", "region", "channel"], as_index=False).agg(
        impressions=("impressions", "sum"), clicks=("clicks", "sum"), sessions=("sessions", "sum"),
        checkout_starts=("checkout_starts", "sum"), checkout_completes=("checkout_completes", "sum"),
        marketing_spend=("spend", "sum")
    )
    kpi = marketing_daily.merge(sales_daily, on=["date", "region", "channel"], how="left")
    kpi[["revenue", "orders", "cogs"]] = kpi[["revenue", "orders", "cogs"]].fillna(0)
    kpi["conversion_rate"] = kpi["orders"] / kpi["sessions"].clip(lower=1)
    kpi["aov"] = kpi["revenue"] / kpi["orders"].clip(lower=1)
    kpi["gross_margin"] = (kpi["revenue"] - kpi["cogs"]) / kpi["revenue"].replace(0, pd.NA)
    kpi["checkout_success_rate"] = kpi["checkout_completes"] / kpi["checkout_starts"].clip(lower=1)
    kpi.to_csv(GOLD / "kpi_region_daily.csv", index=False)

    product = sales.groupby(["date", "region", "product_id", "category"], as_index=False).agg(
        revenue=("net_revenue", "sum"), orders=("order_id", "nunique"), units=("quantity", "sum"),
        avg_unit_price=("unit_price", "mean"), cogs=("cogs", "sum")
    )
    product["gross_margin"] = (product["revenue"] - product["cogs"]) / product["revenue"].replace(0, pd.NA)
    product.to_csv(GOLD / "product_performance_daily.csv", index=False)

    inventory_daily = inventory.groupby(["date", "region", "product_id"], as_index=False).agg(
        available_snapshots=("stockout_flag", lambda s: int((s == 0).sum())),
        snapshots=("stockout_flag", "count"),
        stockout_hours=("stockout_flag", lambda s: float((s == 1).sum() * 4)),
        avg_stock=("stock_level", "mean"), replenishment_qty=("replenishment_qty", "sum")
    )
    inventory_daily["availability_pct"] = inventory_daily["available_snapshots"] / inventory_daily["snapshots"].clip(lower=1)
    inventory_daily.to_csv(GOLD / "inventory_daily.csv", index=False)


def build_duckdb_if_available() -> bool:
    try:
        import duckdb
    except ModuleNotFoundError:
        print("duckdb package not installed; Gold CSV fallback created. Install requirements.txt for DuckDB mode.")
        return False

    if DB_PATH.exists():
        DB_PATH.unlink()
    con = duckdb.connect(str(DB_PATH))
    for name in ["kpi_region_daily", "product_performance_daily", "inventory_daily"]:
        path = str(GOLD / f"{name}.csv").replace("'", "''")
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM read_csv_auto('{path}', header=true)")
    for name, file_name in [
        ("fact_sales_line", "raw_orders.csv"), ("fact_marketing_daily", "raw_marketing.csv"),
        ("fact_inventory_snapshot", "raw_inventory_snapshots.csv"), ("dim_product", "dim_products.csv")
    ]:
        path = str(BRONZE / file_name).replace("'", "''")
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM read_csv_auto('{path}', header=true)")
    con.execute("CREATE TABLE feedback_log (feedback_id BIGINT, created_at TIMESTAMP, insight_id VARCHAR, user_id VARCHAR, rating VARCHAR, corrected_driver VARCHAR, free_text VARCHAR, action_taken BOOLEAN, status VARCHAR)")
    con.execute("CREATE TABLE telemetry_log (request_id VARCHAR, created_at TIMESTAMP, insight_id VARCHAR, total_latency_ms DOUBLE, sql_latency_ms DOUBLE, analytics_latency_ms DOUBLE, llm_latency_ms DOUBLE, model_calls INTEGER, model_used VARCHAR, input_tokens INTEGER, output_tokens INTEGER, estimated_cost_usd DOUBLE, cache_hit BOOLEAN, failures INTEGER)")
    con.close()
    print(f"Initialized DuckDB at {DB_PATH}")
    return True


def main() -> None:
    build_gold_csvs()
    build_duckdb_if_available()


if __name__ == "__main__":
    main()
