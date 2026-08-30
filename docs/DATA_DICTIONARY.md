# Data Dictionary

## raw_orders.csv

Grain: order x product line. Refresh: hourly.

Important fields: `order_id`, `line_id`, `order_ts`, `date`, `region`, `channel`, `product_id`, `category`, `quantity`, `unit_price`, `discount_pct`, `returns_value`, `cogs`, `net_revenue`.

## raw_marketing.csv

Grain: campaign x region x channel x day. Refresh: daily.

Important fields: `date`, `campaign_id`, `region`, `channel`, `impressions`, `clicks`, `sessions`, `checkout_starts`, `checkout_completes`, `spend`.

## raw_inventory_snapshots.csv

Grain: SKU x warehouse x timestamp. Refresh: every four hours.

Important fields: `snapshot_ts`, `date`, `region`, `warehouse_id`, `product_id`, `stock_level`, `stockout_flag`, `replenishment_qty`.

## ground_truth_drivers.csv

Synthetic evaluation only. Never queried by the analytical engine when generating explanations.
