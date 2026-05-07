{{
    config(
        materialized='view'
    )
}}

/*
    Staging model for GA4 events
    - Casts types from VARCHAR raw table
    - Filters to relevant events
    - Extracts channel from source/medium
*/

WITH raw_events AS (
    SELECT * FROM {{ source('raw', 'ga4_events') }}
),

typed AS (
    SELECT
        TRY_CAST(event_timestamp AS TIMESTAMP) AS event_timestamp,
        event_date,
        event_name,
        user_pseudo_id,
        session_id,
        source,
        medium,
        campaign,
        page_location,
        device_category,
        country,
        TRY_CAST(revenue AS DECIMAL(10,2)) AS revenue,
        transaction_id
    FROM raw_events
    WHERE TRY_CAST(event_timestamp AS TIMESTAMP) IS NOT NULL
),

with_channel AS (
    SELECT
        *,
        CASE
            WHEN medium = '(none)' OR medium = 'none' THEN 'direct'
            WHEN medium = 'organic' THEN LOWER(source) || '_organic'
            WHEN medium = 'social' THEN 'social_' || LOWER(source)
            WHEN medium = 'referral' THEN 'referral'
            WHEN medium = 'email' THEN 'email'
            ELSE LOWER(medium) || '_' || LOWER(source)
        END AS channel
    FROM typed
),

-- Extract conversions (purchase events with revenue)
final AS (
    SELECT
        event_timestamp,
        event_date,
        event_name,
        user_pseudo_id,
        session_id,
        source,
        medium,
        campaign,
        channel,
        page_location,
        device_category,
        country,
        revenue,
        transaction_id,
        
        -- Flag conversions
        CASE 
            WHEN event_name = 'purchase' 
             AND transaction_id IS NOT NULL 
             AND revenue > 0 
            THEN TRUE 
            ELSE FALSE 
        END AS is_conversion

    FROM with_channel
)

SELECT * FROM final
