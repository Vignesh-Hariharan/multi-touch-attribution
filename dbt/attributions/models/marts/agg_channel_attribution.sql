WITH by_channel AS (
    SELECT
        channel,
        touchpoint_type,
        COUNT(*) AS touchpoints,
        COUNT(DISTINCT conversion_id) AS conversions_touched,
        SUM(first_touch_revenue) AS first_touch_revenue,
        SUM(last_touch_revenue) AS last_touch_revenue,
        SUM(linear_revenue) AS linear_revenue,
        SUM(position_based_revenue) AS position_based_revenue
    FROM {{ ref('fct_attribution') }}
    GROUP BY channel, touchpoint_type
)

SELECT
    channel,
    CASE WHEN touchpoint_type = 'impression' THEN 'Paid media' ELSE 'Site visit' END AS channel_group,
    touchpoints,
    conversions_touched,
    first_touch_revenue,
    last_touch_revenue,
    linear_revenue,
    position_based_revenue,
    position_based_revenue - last_touch_revenue AS position_vs_last_touch,
    (position_based_revenue - last_touch_revenue) / NULLIF(last_touch_revenue, 0) AS position_vs_last_touch_pct,
    last_touch_revenue / SUM(last_touch_revenue) OVER () AS last_touch_share,
    position_based_revenue / SUM(position_based_revenue) OVER () AS position_based_share
FROM by_channel
