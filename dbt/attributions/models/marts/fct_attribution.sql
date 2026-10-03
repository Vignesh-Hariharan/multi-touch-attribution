SELECT
    conversion_id,
    user_pseudo_id,
    conversion_timestamp,
    revenue AS conversion_revenue,
    touchpoint_id,
    touchpoint_timestamp,
    channel,
    touchpoint_type,
    touchpoint_position,
    total_touchpoints,
    days_to_conversion,

    CASE WHEN touchpoint_position = 1 THEN revenue ELSE 0 END AS first_touch_revenue,

    CASE WHEN touchpoint_position = total_touchpoints THEN revenue ELSE 0 END AS last_touch_revenue,

    revenue / total_touchpoints AS linear_revenue,

    -- 40/40/20; a single touch takes everything and two touches split 50/50
    CASE
        WHEN total_touchpoints = 1 THEN revenue
        WHEN total_touchpoints = 2 THEN revenue * 0.5
        WHEN touchpoint_position = 1 THEN revenue * 0.4
        WHEN touchpoint_position = total_touchpoints THEN revenue * 0.4
        ELSE revenue * 0.2 / (total_touchpoints - 2)
    END AS position_based_revenue

FROM {{ ref('int_attribution_window') }}
