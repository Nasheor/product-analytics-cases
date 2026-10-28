-- Tests present in both package files. The archive splits by test, so the expected answer is zero,
-- which decides how the winner's-curse check is done (a seeded split of each test instead).
SELECT COUNT(DISTINCT e.clickability_test_id) AS shared_tests
FROM exploratory e
JOIN confirmatory c ON c.clickability_test_id = e.clickability_test_id
