-- Monthly Analysis

SELECT
    date_trunc('month', t.created_at) AS month_start,
    -- Count of positive tweets / total tweets
    SUM(CASE WHEN t.sentiment = 'positive' THEN 1 ELSE 0 END)::decimal / COUNT(*) AS positive_ratio,
    -- Count of neutral tweets / total tweets
    SUM(CASE WHEN t.sentiment = 'neutral'  THEN 1 ELSE 0 END)::decimal / COUNT(*) AS neutral_ratio,
    -- Count of negative tweets / total tweets
    SUM(CASE WHEN t.sentiment = 'negative' THEN 1 ELSE 0 END)::decimal / COUNT(*) AS negative_ratio
FROM analyses AS a
JOIN tweets AS t ON a.analysis_id = t.analysis_id
WHERE a.username = 'getgrass_io'
GROUP BY 1
ORDER BY 1;

-- Weekly Analysis
SELECT
    date_trunc('WEEK', t.created_at) AS week_start,
    COUNT(*) AS total_tweets,
    SUM(CASE WHEN t.sentiment = 'positive' THEN 1 ELSE 0 END)::decimal / COUNT(*) AS positive_ratio,
    SUM(CASE WHEN t.sentiment = 'neutral'  THEN 1 ELSE 0 END)::decimal / COUNT(*) AS neutral_ratio,
    SUM(CASE WHEN t.sentiment = 'negative' THEN 1 ELSE 0 END)::decimal / COUNT(*) AS negative_ratio
FROM analyses AS a
JOIN tweets AS t ON a.analysis_id = t.analysis_id
WHERE a.username = 'getgrass_io'
GROUP BY 1
ORDER BY 1;
