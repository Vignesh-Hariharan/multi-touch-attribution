WITH sessions AS (
    SELECT
        session_id AS touchpoint_id,
        user_pseudo_id,
        event_timestamp AS touchpoint_timestamp,
        channel,
        'session' AS touchpoint_type,
        device_category
    FROM {{ ref('stg_events') }}
    WHERE event_name = 'session_start'
),

viewable_impressions AS (
    SELECT
        impression_id AS touchpoint_id,
        user_pseudo_id,
        impression_timestamp AS touchpoint_timestamp,
        channel,
        'impression' AS touchpoint_type,
        device_category
    FROM {{ ref('stg_impressions') }}
    WHERE is_viewable
)

SELECT * FROM sessions
UNION ALL
SELECT * FROM viewable_impressions
