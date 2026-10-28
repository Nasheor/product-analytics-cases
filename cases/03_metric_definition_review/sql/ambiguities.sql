-- Ambiguities in the source that make the metric definitions diverge, each with its count.
SELECT 'distinct order_status values' AS ambiguity, COUNT(DISTINCT order_status) AS n FROM orders
UNION ALL SELECT 'orders whose status is not delivered', COUNT(*) FROM orders WHERE order_status <> 'delivered'
UNION ALL SELECT 'orders with more than one item row', COUNT(*) FROM (SELECT order_id FROM order_items GROUP BY 1 HAVING COUNT(*) > 1)
UNION ALL SELECT 'orders without an item row', COUNT(*) FROM orders o WHERE NOT EXISTS (SELECT 1 FROM order_items i WHERE i.order_id = o.order_id)
UNION ALL SELECT 'orders with more than one payment row', COUNT(*) FROM (SELECT order_id FROM payments GROUP BY 1 HAVING COUNT(*) > 1)
UNION ALL SELECT 'orders paid in more than one instalment', COUNT(DISTINCT order_id) FROM payments WHERE payment_installments > 1
UNION ALL SELECT 'orders without a payment row', COUNT(*) FROM orders o WHERE NOT EXISTS (SELECT 1 FROM payments p WHERE p.order_id = o.order_id)
UNION ALL SELECT 'orders whose payments differ from item value plus freight by more than one real',
    COUNT(*) FROM (
        SELECT o.order_id, COALESCE(p.paid, 0) AS paid, COALESCE(i.value, 0) AS value
        FROM orders o
        LEFT JOIN (SELECT order_id, SUM(payment_value) AS paid FROM payments GROUP BY 1) p USING (order_id)
        LEFT JOIN (SELECT order_id, SUM(price + freight_value) AS value FROM order_items GROUP BY 1) i USING (order_id)
    ) WHERE ABS(paid - value) > 1
UNION ALL SELECT 'orders with more than one review row', COUNT(*) FROM (SELECT order_id FROM reviews GROUP BY 1 HAVING COUNT(*) > 1)
UNION ALL SELECT 'review ids attached to more than one order', COUNT(*) FROM (SELECT review_id FROM reviews GROUP BY 1 HAVING COUNT(DISTINCT order_id) > 1)
UNION ALL SELECT 'orders without a review row', COUNT(*) FROM orders o WHERE NOT EXISTS (SELECT 1 FROM reviews r WHERE r.order_id = o.order_id)
UNION ALL SELECT 'delivered orders without an approval timestamp', COUNT(*) FROM orders WHERE order_status = 'delivered' AND order_approved_at IS NULL
UNION ALL SELECT 'delivered orders without a delivery timestamp', COUNT(*) FROM orders WHERE order_status = 'delivered' AND order_delivered_customer_date IS NULL
UNION ALL SELECT 'orders delivered on the estimated day itself (on time by date, late by timestamp)', COUNT(*)
    FROM orders WHERE order_delivered_customer_date::DATE = order_estimated_delivery_date::DATE AND order_delivered_customer_date > order_estimated_delivery_date
UNION ALL SELECT 'orders with a carrier stamp before the approval stamp', COUNT(*) FROM orders WHERE order_delivered_carrier_date < order_approved_at
UNION ALL SELECT 'months with fewer than 100 orders', COUNT(*) FROM (SELECT strftime(order_purchase_timestamp, '%Y-%m') AS m FROM orders GROUP BY 1 HAVING COUNT(*) < 100)
