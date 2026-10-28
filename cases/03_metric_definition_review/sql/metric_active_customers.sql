-- Active customers by purchase month under three definitions.
-- a: distinct customer_unique_id with any order in the month
-- b: distinct customer_unique_id with a delivered order placed in the month
-- c: distinct customer_id, the per-order key that a reader can mistake for a customer key
SELECT
    purchase_month AS month,
    COUNT(DISTINCT customer_unique_id) AS a_unique_customers_any_status,
    COUNT(DISTINCT CASE WHEN is_delivered THEN customer_unique_id END) AS b_unique_customers_delivered,
    COUNT(DISTINCT customer_id) AS c_customer_id_per_order
FROM base_orders
GROUP BY 1
ORDER BY 1
