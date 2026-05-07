/*
    Validation Analysis: Prospecting Display Undervaluation
    
    This query DISCOVERS the actual percentage by which last-click
    attribution undervalues prospecting display ads.
    
    Expected result: 150-200% increase from last-touch to position-based
    (exact number emerges from realistic data simulation)
*/

WITH last_touch AS (
    SELECT
        channel,
        SUM(last_touch_revenue) AS revenue
    FROM {{ ref('fct_attribution') }}
    WHERE channel LIKE '%prospecting%display%'
    GROUP BY channel
),

position_based AS (
    SELECT
        channel,
        SUM(position_based_revenue) AS revenue
    FROM {{ ref('fct_attribution') }}
    WHERE channel LIKE '%prospecting%display%'
    GROUP BY channel
),

comparison AS (
    SELECT
        COALESCE(lt.channel, pb.channel) AS channel,
        lt.revenue AS last_touch_revenue,
        pb.revenue AS position_based_revenue,
        pb.revenue - lt.revenue AS absolute_increase,
        ROUND((pb.revenue - lt.revenue) / NULLIF(lt.revenue, 0) * 100, 1) AS percent_increase
    FROM last_touch lt
    FULL OUTER JOIN position_based pb
        ON lt.channel = pb.channel
)

SELECT
    channel,
    ROUND(last_touch_revenue, 2) AS last_touch_revenue,
    ROUND(position_based_revenue, 2) AS position_based_revenue,
    ROUND(absolute_increase, 2) AS absolute_increase,
    percent_increase AS undervaluation_pct
FROM comparison
ORDER BY percent_increase DESC;

/*
    INTERPRETATION:
    
    If undervaluation_pct = 175%:
    "Last-click attribution undervalues prospecting display by 175%"
    
    If undervaluation_pct = 220%:
    "Last-click attribution undervalues prospecting display by 220%"
    
    This is your HEADLINE FINDING for the portfolio.
*/
