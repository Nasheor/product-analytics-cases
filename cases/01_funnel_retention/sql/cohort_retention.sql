-- Customers (customer_unique_id) by first-purchase month and the share with a second order within
-- 30, 60, 90, 120, 150 and 180 days. Any order status counts as an order placed. A cohort's window is
-- complete only when the data run 180 days past the cohort month (the orders stop on 2018-08-29).
WITH oc AS (
    SELECT c.customer_unique_id, o.order_purchase_timestamp AS ts
    FROM orders o
    JOIN customers c USING (customer_id)
), firsts AS (
    SELECT customer_unique_id, MIN(ts) AS first_ts
    FROM oc
    GROUP BY 1
), seconds AS (
    SELECT oc.customer_unique_id, MIN(oc.ts) AS second_ts
    FROM oc
    JOIN firsts USING (customer_unique_id)
    WHERE oc.ts > firsts.first_ts
    GROUP BY 1
)
SELECT
    strftime(first_ts, '%Y-%m') AS cohort,
    COUNT(*) AS customers,
    SUM((second_ts <= first_ts + INTERVAL 30 DAY)::INT) AS m1,
    SUM((second_ts <= first_ts + INTERVAL 60 DAY)::INT) AS m2,
    SUM((second_ts <= first_ts + INTERVAL 90 DAY)::INT) AS m3,
    SUM((second_ts <= first_ts + INTERVAL 120 DAY)::INT) AS m4,
    SUM((second_ts <= first_ts + INTERVAL 150 DAY)::INT) AS m5,
    SUM((second_ts <= first_ts + INTERVAL 180 DAY)::INT) AS m6,
    SUM((second_ts IS NOT NULL)::INT) AS ever
FROM firsts
LEFT JOIN seconds USING (customer_unique_id)
GROUP BY cohort
ORDER BY cohort
