-- Rows read by this case: the exploratory and the confirmatory package files.
SELECT (SELECT COUNT(*) FROM exploratory) + (SELECT COUNT(*) FROM confirmatory) AS rows_read
