-- Arms of qualifying tests in one package file ($source is 'exploratory' or 'confirmatory'):
-- at least two arms and at least 1,000 impressions in every arm. The control arm is the package
-- created first (arm_rank 1). Click-through rate per arm and the test's pooled rate.
WITH src AS (
    SELECT * FROM exploratory WHERE $source = 'exploratory'
    UNION ALL
    SELECT * FROM confirmatory WHERE $source = 'confirmatory'
), ranked AS (
    SELECT
        clickability_test_id AS test_id,
        test_week,
        headline,
        eyecatcher_id,
        impressions,
        clicks,
        ROW_NUMBER() OVER (PARTITION BY clickability_test_id ORDER BY created_at, headline) AS arm_rank,
        COUNT(*) OVER (PARTITION BY clickability_test_id) AS arms,
        MIN(impressions) OVER (PARTITION BY clickability_test_id) AS min_impressions,
        SUM(impressions) OVER (PARTITION BY clickability_test_id) AS test_impressions,
        SUM(clicks) OVER (PARTITION BY clickability_test_id) AS test_clicks
    FROM src
)
SELECT
    test_id, test_week, arm_rank, arms, headline, eyecatcher_id, impressions, clicks,
    clicks * 1.0 / impressions AS ctr,
    test_impressions, test_clicks,
    test_clicks * 1.0 / test_impressions AS pooled_ctr
FROM ranked
WHERE arms >= 2 AND min_impressions >= 1000
ORDER BY test_id, arm_rank
