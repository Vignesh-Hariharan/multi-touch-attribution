WITH channel_totals AS (
    SELECT
        SUM(first_touch_revenue) AS first_touch,
        SUM(last_touch_revenue) AS last_touch,
        SUM(linear_revenue) AS linear,
        SUM(position_based_revenue) AS position_based
    FROM {{ ref('agg_channel_attribution') }}
),

revenue AS (
    SELECT SUM(revenue) AS total FROM {{ ref('fct_conversions') }}
)

SELECT *
FROM channel_totals
CROSS JOIN revenue
WHERE ABS(first_touch - total) > 0.01
    OR ABS(last_touch - total) > 0.01
    OR ABS(linear - total) > 0.01
    OR ABS(position_based - total) > 0.01
