WITH raw_campaigns AS (
    SELECT * FROM {{ source('raw', 'campaigns') }}
)

SELECT
    campaign_id,
    campaign_name,
    advertiser,
    campaign_type,
    creative_format,
    CAST(start_date AS DATE) AS start_date,
    CAST(end_date AS DATE) AS end_date,
    CAST(daily_budget AS DECIMAL(10, 2)) AS daily_budget
FROM raw_campaigns
