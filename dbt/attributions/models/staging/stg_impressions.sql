WITH raw_impressions AS (
    SELECT * FROM {{ source('raw', 'impressions') }}
)

SELECT
    impression_id,
    CAST(impression_timestamp AS TIMESTAMP) AS impression_timestamp,
    user_pseudo_id,
    campaign_id,
    campaign_name,
    campaign_type,
    creative_format,
    LOWER(campaign_type) || '_' || LOWER(creative_format) AS channel,
    publisher,
    CAST(is_viewable AS BOOLEAN) AS is_viewable,
    CAST(has_click AS BOOLEAN) AS has_click,
    device_category
FROM raw_impressions
