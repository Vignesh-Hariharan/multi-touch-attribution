WITH raw_events AS (
    SELECT * FROM {{ source('raw', 'ga4_events') }}
)

SELECT
    CAST(event_timestamp AS TIMESTAMP) AS event_timestamp,
    CAST(CAST(event_timestamp AS TIMESTAMP) AS DATE) AS event_date,
    event_name,
    user_pseudo_id,
    session_id,
    source,
    medium,
    campaign,
    CASE
        WHEN medium = '(none)' THEN 'direct'
        WHEN medium = 'organic' THEN LOWER(source) || '_organic'
        WHEN medium = 'social' THEN 'social_' || LOWER(source)
        WHEN medium = 'referral' THEN 'referral'
        WHEN medium = 'email' THEN 'email'
        ELSE LOWER(medium) || '_' || LOWER(source)
    END AS channel,
    page_location,
    device_category,
    country,
    CAST(revenue AS DECIMAL(10, 2)) AS revenue,
    transaction_id,
    event_name = 'purchase' AS is_conversion
FROM raw_events
