WITH by_pathway AS (
    SELECT
        pathway,
        MAX(touchpoint_count) AS pathway_length,
        COUNT(*) AS conversion_count,
        SUM(revenue) AS total_revenue,
        AVG(revenue) AS avg_revenue,
        COUNT(*) * 1.0 / SUM(COUNT(*)) OVER () AS share_of_conversions
    FROM {{ ref('fct_conversions') }}
    GROUP BY pathway
)

SELECT *
FROM by_pathway
WHERE conversion_count >= {{ var('min_pathway_conversions') }}
