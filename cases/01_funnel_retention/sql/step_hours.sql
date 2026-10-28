-- Median hours between consecutive funnel steps by purchase month. The NULL month row is the
-- overall median. Negative values (a carrier stamp before the approval stamp) are kept as recorded.
WITH o AS (
    SELECT
        strftime(order_purchase_timestamp, '%Y-%m') AS month,
        date_diff('minute', order_purchase_timestamp, order_approved_at) / 60.0 AS approve_hours,
        date_diff('minute', order_approved_at, order_delivered_carrier_date) / 60.0 AS carrier_hours,
        date_diff('minute', order_delivered_carrier_date, order_delivered_customer_date) / 60.0 AS deliver_hours
    FROM orders
)
SELECT
    month,
    COUNT(*) AS orders,
    median(approve_hours) AS approve_hours,
    median(carrier_hours) AS carrier_hours,
    median(deliver_hours) AS deliver_hours
FROM o
GROUP BY ROLLUP (month)
ORDER BY month NULLS LAST
