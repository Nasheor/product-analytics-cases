-- How many exploratory tests satisfy each clause of the selection rule, for the memo's Data section.
WITH t AS (
    SELECT
        clickability_test_id AS test_id,
        COUNT(*) AS arms,
        COUNT(DISTINCT eyecatcher_id) AS images,
        COUNT(DISTINCT headline) AS headlines,
        MIN(impressions) AS min_impressions
    FROM exploratory
    GROUP BY 1
)
SELECT
    COUNT(*) AS tests,
    SUM((arms >= 2 AND min_impressions >= 1000)::INT) AS qualifying,
    SUM((arms = 2)::INT) AS two_arm,
    SUM((arms = 2 AND images = 1 AND headlines = 2 AND min_impressions >= 1000)::INT) AS rule_candidates
FROM t
