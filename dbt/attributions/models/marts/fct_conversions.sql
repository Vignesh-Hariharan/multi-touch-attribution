WITH conversions AS (
    SELECT
        transaction_id AS conversion_id,
        user_pseudo_id,
        session_id,
        event_timestamp AS conversion_timestamp,
        event_date AS conversion_date,
        revenue,
        channel AS session_channel,
        device_category
    FROM {{ ref('stg_events') }}
    WHERE is_conversion
),

paths AS (
    SELECT
        conversion_id,
        COUNT(*) AS touchpoint_count,
        SUM(CASE WHEN touchpoint_type = 'impression' THEN 1 ELSE 0 END) AS paid_touchpoint_count,
        MAX(CASE WHEN touchpoint_position = 1 THEN channel END) AS first_touch_channel,
        MAX(CASE WHEN touchpoint_position = total_touchpoints THEN channel END) AS last_touch_channel,
        MAX(days_to_conversion) AS days_from_first_touch,
        {{ dbt.listagg('channel', "' > '", 'ORDER BY touchpoint_position') }} AS pathway
    FROM {{ ref('int_attribution_window') }}
    GROUP BY conversion_id
)

SELECT
    c.conversion_id,
    c.user_pseudo_id,
    c.session_id,
    c.conversion_timestamp,
    c.conversion_date,
    c.revenue,
    c.session_channel,
    c.device_category,
    p.touchpoint_count,
    p.paid_touchpoint_count,
    p.paid_touchpoint_count > 0 AS has_paid_touch,
    p.first_touch_channel,
    p.last_touch_channel,
    p.days_from_first_touch,
    p.pathway
FROM conversions AS c
LEFT JOIN paths AS p
    ON c.conversion_id = p.conversion_id
