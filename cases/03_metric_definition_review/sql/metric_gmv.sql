-- GMV by purchase month under three definitions a team could each believe.
-- a: item price plus freight, every order whatever its status (what the order items table sums to)
-- b: payments received at face value, every order (vouchers and instalments included)
-- c: item price without freight, orders that were not cancelled or unavailable
SELECT
    purchase_month AS month,
    SUM(item_value + freight) AS a_items_plus_freight_all_orders,
    SUM(paid) AS b_payments_all_orders,
    SUM(CASE WHEN NOT is_cancelled THEN item_value ELSE 0 END) AS c_items_only_live_orders
FROM base_orders
GROUP BY 1
ORDER BY 1
