WITH conversions AS (
    SELECT
        transaction_id AS conversion_id,
        user_pseudo_id,
        event_timestamp AS conversion_timestamp,
        revenue
    FROM {{ ref('stg_events') }}
    WHERE is_conversion
),

in_window AS (
    SELECT
        c.conversion_id,
        c.user_pseudo_id,
        c.conversion_timestamp,
        c.revenue,
        t.touchpoint_id,
        t.touchpoint_timestamp,
        t.channel,
        t.touchpoint_type,
        {{ dbt.datediff('t.touchpoint_timestamp', 'c.conversion_timestamp', 'day') }} AS days_to_conversion
    FROM conversions AS c
    INNER JOIN {{ ref('int_touchpoints') }} AS t
        ON c.user_pseudo_id = t.user_pseudo_id
        AND t.touchpoint_timestamp < c.conversion_timestamp
        AND t.touchpoint_timestamp >= {{ dbt.dateadd('day', -var('attribution_window_days'), 'c.conversion_timestamp') }}
)

SELECT
    *,
    ROW_NUMBER() OVER (
        PARTITION BY conversion_id
        ORDER BY touchpoint_timestamp, touchpoint_id
    ) AS touchpoint_position,
    COUNT(*) OVER (PARTITION BY conversion_id) AS total_touchpoints
FROM in_window
