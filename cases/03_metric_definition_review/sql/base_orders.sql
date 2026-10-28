-- One row per order: the single table the recommended metric definitions are computed from.
-- Item value and freight come from the order items, payments from the payment rows (several per
-- order when vouchers are used), the review score is the latest review per order.
WITH items AS (
    SELECT order_id, COUNT(*) AS items, SUM(price) AS item_value, SUM(freight_value) AS freight
    FROM order_items
    GROUP BY 1
), pays AS (
    SELECT order_id, SUM(payment_value) AS paid, COUNT(*) AS payment_rows,
           MAX(payment_installments) AS installments, arg_max(payment_type, payment_value) AS main_payment_type
    FROM payments
    GROUP BY 1
), latest_review AS (
    SELECT order_id, review_score AS latest_score
    FROM reviews
    QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY review_answer_timestamp DESC) = 1
), all_reviews AS (
    SELECT order_id, AVG(review_score) AS mean_score, COUNT(*) AS review_rows
    FROM reviews
    GROUP BY 1
)
SELECT
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_state,
    o.order_status,
    o.order_purchase_timestamp,
    strftime(o.order_purchase_timestamp, '%Y-%m') AS purchase_month,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    strftime(o.order_delivered_customer_date, '%Y-%m') AS delivered_month,
    (o.order_status = 'delivered') AS is_delivered,
    (o.order_status IN ('canceled', 'unavailable')) AS is_cancelled,
    (o.order_delivered_customer_date::DATE <= o.order_estimated_delivery_date::DATE) AS on_time_by_date,
    (o.order_delivered_customer_date <= o.order_estimated_delivery_date) AS on_time_by_timestamp,
    COALESCE(i.items, 0) AS items,
    COALESCE(i.item_value, 0) AS item_value,
    COALESCE(i.freight, 0) AS freight,
    COALESCE(p.paid, 0) AS paid,
    COALESCE(p.payment_rows, 0) AS payment_rows,
    p.installments,
    p.main_payment_type,
    r.latest_score,
    a.mean_score,
    COALESCE(a.review_rows, 0) AS review_rows,
    ROW_NUMBER() OVER (PARTITION BY c.customer_unique_id ORDER BY o.order_purchase_timestamp, o.order_id) AS customer_order_number
FROM orders o
JOIN customers c USING (customer_id)
LEFT JOIN items i USING (order_id)
LEFT JOIN pays p USING (order_id)
LEFT JOIN latest_review r USING (order_id)
LEFT JOIN all_reviews a USING (order_id)
