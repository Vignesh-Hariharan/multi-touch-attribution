-- Each model must hand out exactly the conversion's revenue across its touchpoints.

SELECT
    conversion_id,
    MAX(conversion_revenue) AS revenue,
    SUM(first_touch_revenue) AS first_touch,
    SUM(last_touch_revenue) AS last_touch,
    SUM(linear_revenue) AS linear,
    SUM(position_based_revenue) AS position_based
FROM {{ ref('fct_attribution') }}
GROUP BY conversion_id
HAVING
    ABS(SUM(first_touch_revenue) - MAX(conversion_revenue)) > 0.01
    OR ABS(SUM(last_touch_revenue) - MAX(conversion_revenue)) > 0.01
    OR ABS(SUM(linear_revenue) - MAX(conversion_revenue)) > 0.01
    OR ABS(SUM(position_based_revenue) - MAX(conversion_revenue)) > 0.01
