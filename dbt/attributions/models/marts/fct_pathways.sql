{{
    config(
        materialized='table'
    )
}}

/*
    Conversion Pathways Analysis
    
    Aggregates touchpoint sequences into conversion paths.
    Useful for understanding common user journeys.
*/

WITH attribution AS (
    SELECT * FROM {{ ref('fct_attribution') }}
),

-- Build pathway string for each conversion
pathways AS (
    SELECT
        conversion_id,
        user_pseudo_id,
        conversion_timestamp,
        MAX(total_revenue) AS revenue,
        MAX(total_touchpoints) AS pathway_length,
        LISTAGG(channel, ' → ') WITHIN GROUP (ORDER BY touchpoint_position) AS pathway
    FROM attribution
    GROUP BY conversion_id, user_pseudo_id, conversion_timestamp
),

-- Aggregate by pathway pattern
pathway_summary AS (
    SELECT
        pathway,
        COUNT(*) AS conversion_count,
        SUM(revenue) AS total_revenue,
        ROUND(AVG(revenue), 2) AS avg_revenue,
        ROUND(AVG(pathway_length), 1) AS avg_pathway_length,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_conversions
    FROM pathways
    GROUP BY pathway
    HAVING COUNT(*) >= 2  -- Only show pathways with 2+ conversions
)

SELECT
    pathway,
    conversion_count,
    total_revenue,
    avg_revenue,
    avg_pathway_length,
    pct_of_conversions
FROM pathway_summary
ORDER BY conversion_count DESC
