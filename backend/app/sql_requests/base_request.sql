WITH LatestReviews AS (
    SELECT 
        r.id AS review_id,
        r.pr_id,
        ROW_NUMBER() OVER (PARTITION BY r.pr_id ORDER BY r.created_at DESC) as rn
    FROM reviews r
)
SELECT 
    pr.number AS pr_number,
    rsi.category,
    SUM(rsi.issue_count) AS total_issues
FROM pull_requests pr
JOIN LatestReviews lr ON pr.id = lr.pr_id
JOIN review_stat_items rsi ON lr.review_id = rsi.review_id
WHERE lr.rn = 1
GROUP BY pr.number, rsi.category
ORDER BY pr.number;