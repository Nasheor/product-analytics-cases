-- Late versus on-time delivered orders: share of orders and mean latest review score.
WITH d AS (
    SELECT order_id,
           (order_delivered_customer_date::DATE > order_estimated_delivery_date::DATE) AS late
    FROM orders
    WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL
), rv AS (
    SELECT order_id, review_score
    FROM reviews
    QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY review_answer_timestamp DESC) = 1
)
SELECT
    CASE WHEN late THEN 'late' ELSE 'on time' END AS delivery,
    COUNT(*) AS delivered_orders,
    100.0 * COUNT(*) / SUM(COUNT(*)) OVER () AS share_pct,
    AVG(rv.review_score) AS mean_score,
    100.0 * AVG((rv.review_score = 1)::INT) AS one_star_pct
FROM d
LEFT JOIN rv USING (order_id)
GROUP BY late
ORDER BY late
