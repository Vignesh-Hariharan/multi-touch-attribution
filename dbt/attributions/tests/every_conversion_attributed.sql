-- Purchases that never reached fct_attribution would silently drop out of every channel total.

SELECT e.transaction_id
FROM {{ ref('stg_events') }} AS e
LEFT JOIN (SELECT DISTINCT conversion_id FROM {{ ref('fct_attribution') }}) AS a
    ON e.transaction_id = a.conversion_id
WHERE e.is_conversion
    AND a.conversion_id IS NULL
