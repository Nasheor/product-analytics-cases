-- Rows read by this case: the four raw tables the funnel and retention queries touch.
SELECT (SELECT COUNT(*) FROM orders) + (SELECT COUNT(*) FROM customers)
     + (SELECT COUNT(*) FROM reviews) + (SELECT COUNT(*) FROM payments) AS rows_read
