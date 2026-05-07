{{
    config(
        materialized='view'
    )
}}

/*
    Staging model for ad impressions
    - Filters to viewable impressions only
    - Casts types
    - Builds channel name from campaign metadata
*/

WITH raw_impressions AS (
    SELECT * FROM {{ source('raw', 'impressions') }}
),

typed AS (
    SELECT
        impression_id,
        TRY_CAST(impression_timestamp AS TIMESTAMP) AS impression_timestamp,
        user_pseudo_id,
        campaign_id,
        campaign_name,
        campaign_type,
        creative_format,
        publisher,
        TRY_CAST(is_viewable AS BOOLEAN) AS is_viewable,
        TRY_CAST(has_click AS BOOLEAN) AS has_click,
        device_category
    FROM raw_impressions
    WHERE TRY_CAST(impression_timestamp AS TIMESTAMP) IS NOT NULL
),

-- Filter to viewable impressions only
viewable_only AS (
    SELECT *
    FROM typed
    WHERE is_viewable = TRUE
),

-- Build channel name: {campaign_type}_{creative_format}
with_channel AS (
    SELECT
        *,
        LOWER(campaign_type) || '_' || LOWER(creative_format) AS channel
    FROM viewable_only
)

SELECT
    impression_id,
    impression_timestamp,
    user_pseudo_id,
    campaign_id,
    campaign_name,
    campaign_type,
    creative_format,
    channel,
    publisher,
    has_click,
    device_category
FROM with_channel
