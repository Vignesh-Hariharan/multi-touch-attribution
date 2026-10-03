SELECT
    i.impression_id,
    i.impression_timestamp,
    c.start_date,
    c.end_date
FROM {{ ref('stg_impressions') }} AS i
INNER JOIN {{ ref('stg_campaigns') }} AS c
    ON i.campaign_id = c.campaign_id
WHERE CAST(i.impression_timestamp AS DATE) < c.start_date
    OR CAST(i.impression_timestamp AS DATE) > c.end_date
