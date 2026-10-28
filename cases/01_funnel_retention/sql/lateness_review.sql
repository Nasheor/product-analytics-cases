-- Delivered orders bucketed by days late against the estimated delivery date, with the mean score
-- of the latest review per order and the share of one-star reviews.
WITH d AS (
    SELECT order_id,
           date_diff('day', order_estimated_delivery_date::DATE, order_delivered_customer_date::DATE) AS days_late
    FROM orders
    WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL
), rv AS (
    SELECT order_id, review_score
    FROM reviews
    QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY review_answer_timestamp DESC) = 1
)
SELECT
    CASE WHEN days_late <= 0 THEN 'on time or early'
         WHEN days_late <= 7 THEN '1 to 7 days late'
         WHEN days_late <= 14 THEN '8 to 14 days late'
         ELSE 'more than 14 days late' END AS bucket,
    MIN(days_late) AS bucket_min,
    COUNT(*) AS orders,
    AVG(review_score) AS mean_score,
    100.0 * AVG((review_score = 1)::INT) AS one_star_pct
FROM d
JOIN rv USING (order_id)
GROUP BY bucket
ORDER BY bucket_min
