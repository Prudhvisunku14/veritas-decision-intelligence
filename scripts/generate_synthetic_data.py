from __future__ import annotations

from itertools import permutations
from pathlib import Path
import json
import math
import random

import numpy as np
import pandas as pd


SEED = 42
rng = np.random.default_rng(SEED)
random.seed(SEED)

ROOT = Path(__file__).resolve().parents[1]
BRONZE = ROOT / "data" / "bronze"
META = ROOT / "data" / "metadata"
BRONZE.mkdir(parents=True, exist_ok=True)
META.mkdir(parents=True, exist_ok=True)

START = pd.Timestamp("2025-05-01")
END = pd.Timestamp("2026-08-20")
INCIDENT_START = pd.Timestamp("2026-07-10")
INCIDENT_END = END
NEW_PRODUCT_LAUNCH = pd.Timestamp("2026-08-01")

REGIONS = ["North", "South", "East", "West"]
CHANNELS = ["Web", "App", "Marketplace"]
REGION_FACTOR = {"North": 1.15, "South": 1.00, "East": 0.82, "West": 1.08}
CHANNEL_FACTOR = {"Web": 1.0, "App": 0.86, "Marketplace": 0.72}

CATEGORIES = {
    "Electronics": 18000.0,
    "Home": 5200.0,
    "Beauty": 2100.0,
    "Grocery": 950.0,
    "Fashion": 3400.0,
    "Sports": 4500.0,
}

products = []
product_id = 1
for category, base_price in CATEGORIES.items():
    for i in range(10):
        pid = f"P{product_id:03d}"
        products.append(
            {
                "product_id": pid,
                "category": category,
                "base_price": base_price * (0.80 + 0.04 * i),
                "base_weight": 1.0 + 0.10 * (9 - i),
                "launch_date": NEW_PRODUCT_LAUNCH if pid == "P020" else START,
            }
        )
        product_id += 1
PRODUCT_DF = pd.DataFrame(products)
PRODUCT_LOOKUP = {row["product_id"]: row for row in products}

STOCKOUT_PRODUCTS = {"P003", "P004", "P007", "P008", "P025", "P031"}
PRICE_UP_PRODUCTS = {"P001", "P002", "P006", "P011", "P015", "P042"}
CHEAP_MIX_PRODUCTS = set(
    PRODUCT_DF.sort_values("base_price").head(18)["product_id"].tolist()
)


def seasonal_multiplier(date: pd.Timestamp) -> float:
    month = date.month
    month_factor = {
        1: 0.95, 2: 0.97, 3: 1.00, 4: 1.02, 5: 1.00, 6: 0.98,
        7: 1.00, 8: 1.03, 9: 1.06, 10: 1.18, 11: 1.12, 12: 1.15,
    }[month]
    weekend = 1.12 if date.dayofweek >= 5 else 1.0
    return month_factor * weekend


def trend_multiplier(date: pd.Timestamp) -> float:
    total_days = max((END - START).days, 1)
    elapsed = (date - START).days
    return 1.0 + 0.10 * (elapsed / total_days)


def promo_multiplier(date: pd.Timestamp) -> float:
    if date.day in (5, 6, 20, 21):
        return 1.08
    if date.month in (10, 11) and date.day <= 7:
        return 1.14
    return 1.0


def incident_progress(date: pd.Timestamp) -> float:
    if date < INCIDENT_START:
        return 0.0
    ramp_days = 14
    return min(1.0, max(0.0, (date - INCIDENT_START).days / ramp_days))


def product_weights(date: pd.Timestamp, region: str) -> np.ndarray:
    available = PRODUCT_DF[PRODUCT_DF["launch_date"] <= date].copy()
    weights = available["base_weight"].to_numpy(dtype=float)
    if region == "North" and INCIDENT_START <= date <= INCIDENT_END:
        p = incident_progress(date)
        # Adverse mix shift toward lower-value products.
        weights *= np.where(available["product_id"].isin(CHEAP_MIX_PRODUCTS), 1.06 + 0.05 * p, 0.97 - 0.03 * p)
        # Stocked-out products become harder to buy.
        weights *= np.where(available["product_id"].isin(STOCKOUT_PRODUCTS), 0.80, 1.0)
    weights = np.maximum(weights, 1e-6)
    weights /= weights.sum()
    return available["product_id"].to_numpy(), weights


def generate_marketing() -> pd.DataFrame:
    rows = []
    campaigns = ["AlwaysOn", "Performance"]
    dates = pd.date_range(START, END, freq="D")
    for date in dates:
        for region in REGIONS:
            for channel in CHANNELS:
                base_sessions = 420.0 * REGION_FACTOR[region] * CHANNEL_FACTOR[channel]
                base_sessions *= seasonal_multiplier(date) * trend_multiplier(date) * promo_multiplier(date)
                base_sessions *= rng.normal(1.0, 0.035)

                incident = region == "North" and INCIDENT_START <= date <= INCIDENT_END
                p = incident_progress(date) if incident else 0.0
                marketing_mult = 1.0 - 0.10 * p
                sessions = max(120.0, base_sessions * marketing_mult)

                spend = sessions * (18.5 + rng.normal(0, 0.9))
                # Intentional contradiction late in the incident: spend appears less reduced than sessions.
                if incident and date >= INCIDENT_END - pd.Timedelta(days=8):
                    spend *= 1.10

                checkout_starts = sessions * (0.105 + rng.normal(0, 0.002))
                base_checkout_success = 0.39
                funnel_mult = 1.0 - 0.045 * p if incident else 1.0
                checkout_success_rate = base_checkout_success * funnel_mult
                checkout_completes = checkout_starts * checkout_success_rate

                impressions = sessions * (23.0 + rng.normal(0, 1.0))
                clicks = sessions * (1.6 + rng.normal(0, 0.05))

                for campaign in campaigns:
                    share = 0.58 if campaign == "AlwaysOn" else 0.42
                    c_completes = round(checkout_completes * share, 2)
                    rows.append(
                        {
                            "date": date.date().isoformat(),
                            "campaign_id": f"{campaign}_{region}_{channel}",
                            "region": region,
                            "channel": channel,
                            "impressions": round(impressions * share),
                            "clicks": round(clicks * share),
                            "sessions": round(sessions * share),
                            "checkout_starts": round(checkout_starts * share, 2),
                            "checkout_completes": c_completes,
                            "conversions": c_completes,
                            "spend": round(spend * share, 2),
                            "updated_at": f"{date.date().isoformat()} 23:59:59",
                        }
                    )
    return pd.DataFrame(rows)


def daily_inventory_availability(date: pd.Timestamp, region: str) -> float:
    if region != "North" or not (INCIDENT_START <= date <= INCIDENT_END):
        return 0.97
    p = incident_progress(date)
    return 0.97 - 0.16 * p


def generate_inventory() -> pd.DataFrame:
    rows = []
    dates = pd.date_range(START, END, freq="D")
    for date in dates:
        active_products = PRODUCT_DF[PRODUCT_DF["launch_date"] <= date]
        for region in REGIONS:
            warehouse = f"WH_{region}"
            for _, prod in active_products.iterrows():
                for hour in (0, 4, 8, 12, 16, 20):
                    incident_stockout = (
                        region == "North"
                        and INCIDENT_START <= date <= INCIDENT_END
                        and prod.product_id in STOCKOUT_PRODUCTS
                    )
                    p = incident_progress(date) if incident_stockout else 0.0
                    stockout_prob = 0.02 + (0.30 * p if incident_stockout else 0.0)
                    stockout = rng.random() < stockout_prob
                    stock_level = 0 if stockout else int(max(5, rng.normal(85, 24)))
                    replenishment = int(max(0, rng.normal(18, 8))) if hour in (8, 16) else 0
                    rows.append(
                        {
                            "snapshot_ts": f"{date.date().isoformat()} {hour:02d}:00:00",
                            "date": date.date().isoformat(),
                            "region": region,
                            "warehouse_id": warehouse,
                            "product_id": prod.product_id,
                            "stock_level": stock_level,
                            "stockout_flag": int(stockout),
                            "replenishment_qty": replenishment,
                        }
                    )
    return pd.DataFrame(rows)


def generate_orders(marketing: pd.DataFrame) -> pd.DataFrame:
    marketing_daily = (
        marketing.groupby(["date", "region", "channel"], as_index=False)
        .agg(
            sessions=("sessions", "sum"),
            checkout_starts=("checkout_starts", "sum"),
            checkout_completes=("checkout_completes", "sum"),
        )
    )

    rows = []
    order_counter = 1
    for rec in marketing_daily.itertuples(index=False):
        date = pd.Timestamp(rec.date)
        incident = rec.region == "North" and INCIDENT_START <= date <= INCIDENT_END
        p = incident_progress(date) if incident else 0.0

        # Base conversion includes funnel effect from marketing table and independent stock-availability effect.
        checkout_ratio = rec.checkout_completes / max(rec.checkout_starts, 1.0)
        base_order_conversion = 0.042 * (checkout_ratio / 0.39)
        stock_mult = 1.0 - 0.02 * p if incident else 1.0
        conversion = max(0.008, base_order_conversion * stock_mult * rng.normal(1.0, 0.018))
        n_orders = max(1, int(round(rec.sessions * conversion)))

        active_ids, weights = product_weights(date, rec.region)
        chosen_products = rng.choice(active_ids, size=n_orders, p=weights)

        for pid in chosen_products:
            prod = PRODUCT_LOOKUP[pid]
            quantity = int(rng.choice([1, 1, 1, 1, 2, 2, 3]))
            price_mult = 1.02 if incident and pid in PRICE_UP_PRODUCTS else 1.0
            unit_price = round(float(prod["base_price"] * price_mult * rng.normal(1.0, 0.018)), 2)
            promo = date.day in (5, 6, 20, 21) or (date.month in (10, 11) and date.day <= 7)
            discount_pct = round(float(np.clip(rng.normal(0.07 if promo else 0.025, 0.012), 0, 0.18)), 4)
            gross = quantity * unit_price * (1.0 - discount_pct)
            return_flag = rng.random() < 0.028
            returns_val = round(gross, 2) if return_flag else 0.0
            net_revenue = round(max(0.0, gross - returns_val), 2)
            cogs = round(gross * float(np.clip(rng.normal(0.66, 0.025), 0.55, 0.78)), 2)
            order_ts = date + pd.Timedelta(hours=int(rng.integers(0, 24)), minutes=int(rng.integers(0, 60)))
            order_id = f"O{order_counter:08d}"
            rows.append(
                {
                    "order_id": order_id,
                    "line_id": f"{order_id}_1",
                    "order_ts": order_ts.isoformat(sep=" "),
                    "date": date.date().isoformat(),
                    "region": rec.region,
                    "channel": rec.channel,
                    "product_id": pid,
                    "category": prod["category"],
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "discount_pct": round(discount_pct, 4),
                    "return_flag": int(return_flag),
                    "return_value": returns_val,
                    "returns_value": returns_val,
                    "cogs": cogs,
                    "net_revenue": net_revenue,
                }
            )
            order_counter += 1
    return pd.DataFrame(rows)


def shapley_driver_ground_truth() -> pd.DataFrame:
    # Independent synthetic intervention multipliers. The product of all enabled drivers
    # gives the macro incident revenue index. Shapley allocates interaction effects fairly.
    factors = {
        "marketing_traffic": ("sessions", 0.91),
        "checkout_funnel_degradation": ("conversion", 0.97),
        "stock_availability": ("conversion", 0.98),
        "adverse_product_mix": ("aov", 0.99),
        "pricing_offset": ("aov", 1.02),
    }

    def revenue_index(enabled: set[str]) -> float:
        s = c = a = 1.0
        for name in enabled:
            target, mult = factors[name]
            if target == "sessions":
                s *= mult
            elif target == "conversion":
                c *= mult
            else:
                a *= mult
        return s * c * a

    names = list(factors)
    contributions = {name: 0.0 for name in names}
    perms = list(permutations(names))
    for perm in perms:
        enabled: set[str] = set()
        prev = revenue_index(enabled)
        for name in perm:
            enabled.add(name)
            cur = revenue_index(enabled)
            contributions[name] += cur - prev
            prev = cur
    for name in contributions:
        contributions[name] /= len(perms)

    final_delta = revenue_index(set(names)) - 1.0
    rows = []
    for name, contribution in contributions.items():
        rows.append(
            {
                "incident_start": INCIDENT_START.date().isoformat(),
                "incident_end": INCIDENT_END.date().isoformat(),
                "driver": name,
                "true_contribution_pct_points": round(100 * contribution, 4),
                "true_share_of_total_delta": round(contribution / final_delta, 6) if final_delta else 0.0,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    marketing = generate_marketing()
    inventory = generate_inventory()
    orders = generate_orders(marketing)
    ground_truth = shapley_driver_ground_truth()

    PRODUCT_DF.assign(
        launch_date=PRODUCT_DF["launch_date"].dt.date.astype(str)
    ).to_csv(BRONZE / "dim_products.csv", index=False)
    marketing.to_csv(BRONZE / "raw_marketing.csv", index=False)
    inventory.to_csv(BRONZE / "raw_inventory_snapshots.csv", index=False)
    orders.to_csv(BRONZE / "raw_orders.csv", index=False)
    ground_truth.to_csv(META / "ground_truth_drivers.csv", index=False)

    metadata = {
        "dataset_start": START.date().isoformat(),
        "dataset_end": END.date().isoformat(),
        "incident_start": INCIDENT_START.date().isoformat(),
        "incident_end": INCIDENT_END.date().isoformat(),
        "new_product_launch": NEW_PRODUCT_LAUNCH.date().isoformat(),
        "source_status": {
            "main": {
                "sales": {"freshness_hours": 6, "data_quality_score": 0.97},
                "inventory": {"freshness_hours": 4, "data_quality_score": 0.97},
                "marketing": {"freshness_hours": 30, "data_quality_score": 0.80},
            },
            "degraded": {
                "sales": {"freshness_hours": 8, "data_quality_score": 0.92},
                "inventory": {"freshness_hours": 10, "data_quality_score": 0.88},
                "marketing": {"freshness_hours": 72, "data_quality_score": 0.58},
            },
        },
        "notes": "Ground-truth metadata is evaluation-only and must never be queried by the insight engine.",
    }
    (META / "source_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Generated {len(orders):,} order lines")
    print(f"Generated {len(marketing):,} marketing rows")
    print(f"Generated {len(inventory):,} inventory snapshots")
    print(f"Incident: {INCIDENT_START.date()} to {INCIDENT_END.date()}")


if __name__ == "__main__":
    main()
