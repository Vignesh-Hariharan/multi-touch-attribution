/*
    Analysis: Channel Attribution Comparison Across All Models
    
    Compares revenue attribution for each channel across all 4 models.
    Use this to build Tableau visualizations.
*/

WITH attribution AS (
    SELECT * FROM {{ ref('fct_attribution') }}
),

channel_totals AS (
    SELECT
        channel,
        COUNT(DISTINCT conversion_id) AS conversion_count,
        SUM(first_touch_revenue) AS first_touch_total,
        SUM(last_touch_revenue) AS last_touch_total,
        SUM(linear_revenue) AS linear_total,
        SUM(position_based_revenue) AS position_based_total
    FROM attribution
    GROUP BY channel
),

with_percentages AS (
    SELECT
        channel,
        conversion_count,
        
        -- Revenue by model
        ROUND(first_touch_total, 2) AS first_touch_revenue,
        ROUND(last_touch_total, 2) AS last_touch_revenue,
        ROUND(linear_total, 2) AS linear_revenue,
        ROUND(position_based_total, 2) AS position_based_revenue,
        
        -- Percentage of total (last-touch baseline)
        ROUND(last_touch_total * 100.0 / SUM(last_touch_total) OVER (), 2) AS last_touch_pct,
        ROUND(position_based_total * 100.0 / SUM(position_based_total) OVER (), 2) AS position_based_pct,
        
        -- Change from last-touch
        ROUND((position_based_total - last_touch_total) / NULLIF(last_touch_total, 0) * 100, 1) AS pct_change
        
    FROM channel_totals
)

SELECT *
FROM with_percentages
ORDER BY position_based_revenue DESC;
