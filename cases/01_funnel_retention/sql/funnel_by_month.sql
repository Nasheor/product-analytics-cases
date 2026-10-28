-- Order funnel by purchase month: created, approved, handed to carrier, delivered, reviewed.
-- Steps are cumulative. An order that reached a later step counts as having passed the earlier
-- ones, so the funnel stays monotone where an earlier timestamp is missing (14 delivered orders
-- have no approval stamp). "Reviewed" means a delivered order with at least one review row.
WITH o AS (
    SELECT
        order_id,
        strftime(order_purchase_timestamp, '%Y-%m') AS month,
        order_status,
        (order_approved_at IS NOT NULL OR order_delivered_carrier_date IS NOT NULL
            OR order_delivered_customer_date IS NOT NULL) AS approved,
        (order_delivered_carrier_date IS NOT NULL OR order_delivered_customer_date IS NOT NULL) AS carrier,
        (order_delivered_customer_date IS NOT NULL) AS delivered
    FROM orders
), r AS (
    SELECT DISTINCT order_id FROM reviews
)
SELECT
    month,
    COUNT(*) AS created,
    SUM(approved::INT) AS approved,
    SUM(carrier::INT) AS handed_to_carrier,
    SUM(delivered::INT) AS delivered,
    SUM((delivered AND r.order_id IS NOT NULL)::INT) AS reviewed,
    SUM((order_status = 'canceled')::INT) AS canceled,
    SUM((order_status = 'unavailable')::INT) AS unavailable
FROM o
LEFT JOIN r USING (order_id)
GROUP BY month
ORDER BY month
