{{
    config(
        materialized='view'
    )
}}

/*
    Joins touchpoints to conversions within the attribution window.
    Calculates touchpoint position and sequence for attribution models.
*/

WITH conversions AS (
    SELECT
        user_pseudo_id,
        transaction_id AS conversion_id,
        event_timestamp AS conversion_timestamp,
        revenue,
        device_category AS conversion_device,
        country
    FROM {{ ref('stg_events') }}
    WHERE is_conversion = TRUE
),

touchpoints AS (
    SELECT * FROM {{ ref('int_touchpoints') }}
),

-- Join touchpoints to conversions within attribution window
touchpoints_to_conversions AS (
    SELECT
        c.conversion_id,
        c.user_pseudo_id,
        c.conversion_timestamp,
        c.revenue,
        c.conversion_device,
        c.country,
        
        t.touchpoint_id,
        t.touchpoint_timestamp,
        t.channel,
        t.touchpoint_type,
        t.device_category AS touchpoint_device,
        
        -- Days between touchpoint and conversion
        DATEDIFF('day', t.touchpoint_timestamp, c.conversion_timestamp) AS days_to_conversion
        
    FROM conversions c
    INNER JOIN touchpoints t
        ON c.user_pseudo_id = t.user_pseudo_id
        AND t.touchpoint_timestamp < c.conversion_timestamp  -- Touchpoint before conversion
        AND t.touchpoint_timestamp >= DATEADD('day', -{{ var('attribution_window_days') }}, c.conversion_timestamp)  -- Within window
),

-- Add touchpoint position and total count per conversion
with_position AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY conversion_id 
            ORDER BY touchpoint_timestamp
        ) AS touchpoint_position,
        
        COUNT(*) OVER (
            PARTITION BY conversion_id
        ) AS total_touchpoints
        
    FROM touchpoints_to_conversions
)

SELECT
    conversion_id,
    user_pseudo_id,
    conversion_timestamp,
    revenue,
    conversion_device,
    country,
    touchpoint_id,
    touchpoint_timestamp,
    channel,
    touchpoint_type,
    touchpoint_device,
    touchpoint_position,
    total_touchpoints,
    days_to_conversion
FROM with_position
ORDER BY conversion_id, touchpoint_position
