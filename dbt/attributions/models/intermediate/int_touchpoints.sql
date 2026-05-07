{{
    config(
        materialized='view'
    )
}}

/*
    Combines all marketing touchpoints (web sessions + ad impressions)
    into a unified touchpoint table for attribution analysis.
*/

WITH sessions AS (
    SELECT
        user_pseudo_id,
        event_timestamp AS touchpoint_timestamp,
        channel,
        device_category,
        'session' AS touchpoint_type,
        session_id AS touchpoint_id
    FROM {{ ref('stg_events') }}
    WHERE event_name = 'session_start'
),

impressions AS (
    SELECT
        user_pseudo_id,
        impression_timestamp AS touchpoint_timestamp,
        channel,
        device_category,
        'impression' AS touchpoint_type,
        impression_id AS touchpoint_id
    FROM {{ ref('stg_impressions') }}
),

combined AS (
    SELECT * FROM sessions
    UNION ALL
    SELECT * FROM impressions
)

SELECT
    touchpoint_id,
    user_pseudo_id,
    touchpoint_timestamp,
    channel,
    touchpoint_type,
    device_category
FROM combined
ORDER BY user_pseudo_id, touchpoint_timestamp
