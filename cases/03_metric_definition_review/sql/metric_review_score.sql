-- Average review score under three definitions.
-- a: mean over every review row, by the month the review was created
-- b: mean of the latest review per order, by purchase month (one vote per order)
-- c: mean of the latest review per delivered order, by purchase month
WITH a AS (
    SELECT strftime(review_creation_date, '%Y-%m') AS month, AVG(review_score) AS a_all_review_rows_by_review_month
    FROM reviews
    GROUP BY 1
), b AS (
    SELECT purchase_month AS month,
           AVG(latest_score) AS b_latest_review_per_order_by_purchase_month,
           AVG(CASE WHEN is_delivered THEN latest_score END) AS c_latest_review_delivered_orders_by_purchase_month
    FROM base_orders
    GROUP BY 1
)
SELECT month, a_all_review_rows_by_review_month, b_latest_review_per_order_by_purchase_month,
       c_latest_review_delivered_orders_by_purchase_month
FROM a
FULL JOIN b USING (month)
ORDER BY month
