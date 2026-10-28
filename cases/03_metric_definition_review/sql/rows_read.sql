-- Rows read by this case: the five raw tables the base order table and the metric queries touch.
SELECT (SELECT COUNT(*) FROM orders) + (SELECT COUNT(*) FROM customers) + (SELECT COUNT(*) FROM order_items)
     + (SELECT COUNT(*) FROM payments) + (SELECT COUNT(*) FROM reviews) AS rows_read
