-- Delivered revenue net of cancellations under three definitions.
-- a: delivered orders, item value plus freight, by purchase month
-- b: delivered orders, item value plus freight, by the month the customer received the order
-- c: payments of every order that was not cancelled or unavailable, by purchase month
--    (shipped, invoiced and processing orders count as revenue already)
WITH a AS (
    SELECT purchase_month AS month, SUM(item_value + freight) AS a_delivered_by_purchase_month
    FROM base_orders WHERE is_delivered GROUP BY 1
), b AS (
    SELECT delivered_month AS month, SUM(item_value + freight) AS b_delivered_by_delivery_month
    FROM base_orders WHERE is_delivered AND delivered_month IS NOT NULL GROUP BY 1
), c AS (
    SELECT purchase_month AS month, SUM(paid) AS c_payments_of_live_orders_by_purchase_month
    FROM base_orders WHERE NOT is_cancelled GROUP BY 1
)
SELECT month, a_delivered_by_purchase_month, b_delivered_by_delivery_month, c_payments_of_live_orders_by_purchase_month
FROM a
FULL JOIN b USING (month)
FULL JOIN c USING (month)
ORDER BY month
