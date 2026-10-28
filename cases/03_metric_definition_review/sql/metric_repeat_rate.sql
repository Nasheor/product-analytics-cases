-- Repeat rate by purchase month under three definitions.
-- a: share of the month's orders placed by a customer with an earlier order in the data
-- b: share of the month's distinct customers who have more than one order anywhere in the data
--    (it looks into the future, so it rises as the data mature)
-- c: share of the month's first-time customers who place another order within 90 days
--    (needs 90 days of follow-up, so the last three months are incomplete)
WITH cust AS (
    SELECT customer_unique_id, COUNT(*) AS orders_ever
    FROM base_orders
    GROUP BY 1
), nxt AS (
    SELECT b.order_id, MIN(n.order_purchase_timestamp) AS next_ts
    FROM base_orders b
    JOIN base_orders n
      ON n.customer_unique_id = b.customer_unique_id AND n.order_purchase_timestamp > b.order_purchase_timestamp
    WHERE b.customer_order_number = 1
    GROUP BY 1
)
SELECT
    b.purchase_month AS month,
    100.0 * AVG((b.customer_order_number > 1)::INT) AS a_orders_from_returning_customers_pct,
    100.0 * COUNT(DISTINCT CASE WHEN c.orders_ever > 1 THEN b.customer_unique_id END)
          / COUNT(DISTINCT b.customer_unique_id) AS b_customers_with_more_than_one_order_ever_pct,
    100.0 * AVG(CASE WHEN b.customer_order_number = 1
                     THEN COALESCE(x.next_ts <= b.order_purchase_timestamp + INTERVAL 90 DAY, FALSE)::INT END)
          AS c_first_timers_back_within_90_days_pct
FROM base_orders b
JOIN cust c USING (customer_unique_id)
LEFT JOIN nxt x USING (order_id)
GROUP BY 1
ORDER BY 1
