-- On-time delivery rate by purchase month under three definitions.
-- a: delivered orders received on or before the estimated day (date comparison)
-- b: delivered orders received before the estimated day's midnight (timestamp comparison, so a
--    delivery on the estimated day itself counts as late)
-- c: every order that was not cancelled or unavailable, received on or before the estimated day,
--    with orders never delivered counted as not on time
SELECT
    purchase_month AS month,
    100.0 * AVG(CASE WHEN is_delivered AND order_delivered_customer_date IS NOT NULL THEN on_time_by_date::INT END)
        AS a_delivered_on_or_before_estimated_day_pct,
    100.0 * AVG(CASE WHEN is_delivered AND order_delivered_customer_date IS NOT NULL THEN on_time_by_timestamp::INT END)
        AS b_delivered_before_estimated_midnight_pct,
    100.0 * AVG(CASE WHEN NOT is_cancelled THEN COALESCE(on_time_by_date, FALSE)::INT END)
        AS c_all_live_orders_on_time_pct
FROM base_orders
GROUP BY 1
ORDER BY 1
