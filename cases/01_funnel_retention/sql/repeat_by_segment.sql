-- Six-month repeat rate for cohorts with a complete 180-day window ($cohort_from to $cohort_to),
-- split by the customer's state and by the main payment type of the first order (the payment row
-- with the largest value when an order has several rows).
WITH oc AS (
    SELECT c.customer_unique_id, c.customer_state, o.order_id, o.order_purchase_timestamp AS ts
    FROM orders o
    JOIN customers c USING (customer_id)
), firsts AS (
    SELECT customer_unique_id, MIN(ts) AS first_ts
    FROM oc
    GROUP BY 1
), first_order AS (
    SELECT oc.customer_unique_id, oc.customer_state, oc.order_id, oc.ts AS first_ts
    FROM oc
    JOIN firsts USING (customer_unique_id)
    WHERE oc.ts = firsts.first_ts
    QUALIFY ROW_NUMBER() OVER (PARTITION BY oc.customer_unique_id ORDER BY oc.order_id) = 1
), main_payment AS (
    SELECT order_id, payment_type
    FROM payments
    QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY payment_value DESC, payment_sequential) = 1
), seconds AS (
    SELECT oc.customer_unique_id, MIN(oc.ts) AS second_ts
    FROM oc
    JOIN firsts USING (customer_unique_id)
    WHERE oc.ts > firsts.first_ts
    GROUP BY 1
), base AS (
    SELECT f.customer_unique_id, f.customer_state, COALESCE(p.payment_type, 'none') AS payment_type,
           (s.second_ts <= f.first_ts + INTERVAL 180 DAY) AS repeat_6m
    FROM first_order f
    LEFT JOIN main_payment p USING (order_id)
    LEFT JOIN seconds s USING (customer_unique_id)
    WHERE strftime(f.first_ts, '%Y-%m') BETWEEN $cohort_from AND $cohort_to
)
SELECT 'state' AS split, customer_state AS segment, COUNT(*) AS customers,
       100.0 * AVG(COALESCE(repeat_6m, FALSE)::INT) AS repeat_6m_pct
FROM base
GROUP BY 1, 2
UNION ALL
SELECT 'payment_type', payment_type, COUNT(*), 100.0 * AVG(COALESCE(repeat_6m, FALSE)::INT)
FROM base
GROUP BY 1, 2
ORDER BY split, customers DESC
