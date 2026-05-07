{{
    config(
        materialized='view'
    )
}}

/*
    Staging model for campaigns
    - Simple type casting
    - Campaign metadata
*/

WITH raw_campaigns AS (
    SELECT * FROM {{ source('raw', 'campaigns') }}
),

final AS (
    SELECT
        CAMPAIGN_ID AS campaign_id,
        CAMPAIGN_NAME AS campaign_name,
        ADVERTISER AS advertiser,
        CAMPAIGN_TYPE AS campaign_type,
        CREATIVE_FORMAT AS creative_format,
        TRY_CAST(START_DATE AS DATE) AS start_date,
        TRY_CAST(END_DATE AS DATE) AS end_date,
        TRY_CAST(DAILY_BUDGET AS DECIMAL(10,2)) AS daily_budget
    FROM raw_campaigns
)

SELECT * FROM final
