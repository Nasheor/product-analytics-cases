-- The pre-registered selection rule from README.md: among exploratory tests with exactly two arms,
-- the same eyecatcher_id on both arms (no image change), different headlines and at least 1,000
-- impressions per arm, take the test with the most total impressions. Ties go to the lower test id.
WITH t AS (
    SELECT
        clickability_test_id AS test_id,
        COUNT(*) AS arms,
        COUNT(DISTINCT eyecatcher_id) AS images,
        COUNT(DISTINCT headline) AS headlines,
        MIN(impressions) AS min_impressions,
        SUM(impressions) AS total_impressions
    FROM exploratory
    GROUP BY 1
), chosen AS (
    SELECT test_id
    FROM t
    WHERE arms = 2 AND images = 1 AND headlines = 2 AND min_impressions >= 1000
    ORDER BY total_impressions DESC, test_id
    LIMIT 1
)
SELECT
    e.clickability_test_id AS test_id,
    e.test_week,
    e.created_at,
    ROW_NUMBER() OVER (ORDER BY e.created_at, e."Unnamed: 0") AS arm_rank,
    e.headline,
    e.eyecatcher_id,
    e.impressions,
    e.clicks,
    e.clicks * 1.0 / e.impressions AS ctr
FROM exploratory e
JOIN chosen USING (test_id)
ORDER BY arm_rank
