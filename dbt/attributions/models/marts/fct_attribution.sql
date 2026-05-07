{{
    config(
        materialized='table',
        unique_key='touchpoint_id'
    )
}}

/*
    Core Attribution Model
    
    Applies 4 attribution models to calculate revenue credit:
    1. First Touch: 100% to first touchpoint
    2. Last Touch: 100% to last touchpoint (baseline)
    3. Linear: Equal credit across all touchpoints
    4. Position-Based (U-Shaped): 40% first, 40% last, 20% middle
*/

WITH attribution_base AS (
    SELECT * FROM {{ ref('int_attribution_window') }}
),

with_attribution_credits AS (
    SELECT
        conversion_id,
        user_pseudo_id,
        conversion_timestamp,
        revenue AS total_revenue,
        conversion_device,
        country,
        
        touchpoint_id,
        touchpoint_timestamp,
        channel,
        touchpoint_type,
        touchpoint_device,
        touchpoint_position,
        total_touchpoints,
        days_to_conversion,
        
        -- MODEL 1: First Touch Attribution
        -- 100% credit to position 1
        CASE 
            WHEN touchpoint_position = 1 THEN revenue 
            ELSE 0 
        END AS first_touch_revenue,
        
        -- MODEL 2: Last Touch Attribution (Baseline)
        -- 100% credit to last position
        CASE 
            WHEN touchpoint_position = total_touchpoints THEN revenue 
            ELSE 0 
        END AS last_touch_revenue,
        
        -- MODEL 3: Linear Attribution
        -- Equal credit across all touchpoints
        revenue / total_touchpoints AS linear_revenue,
        
        -- MODEL 4: Position-Based Attribution (U-Shaped: 40/40/20)
        -- 40% to first, 40% to last, 20% split among middle
        CASE
            -- Single touchpoint: 100%
            WHEN total_touchpoints = 1 THEN revenue
            
            -- Two touchpoints: 50/50
            WHEN total_touchpoints = 2 AND touchpoint_position = 1 THEN revenue * 0.5
            WHEN total_touchpoints = 2 AND touchpoint_position = 2 THEN revenue * 0.5
            
            -- Three or more: 40/40/20 split
            WHEN touchpoint_position = 1 THEN revenue * 0.4  -- First gets 40%
            WHEN touchpoint_position = total_touchpoints THEN revenue * 0.4  -- Last gets 40%
            ELSE revenue * 0.2 / (total_touchpoints - 2)  -- Middle touchpoints split 20%
        END AS position_based_revenue

    FROM attribution_base
)

SELECT
    conversion_id,
    user_pseudo_id,
    conversion_timestamp,
    total_revenue,
    conversion_device,
    country,
    touchpoint_id,
    touchpoint_timestamp,
    channel,
    touchpoint_type,
    touchpoint_device,
    touchpoint_position,
    total_touchpoints,
    days_to_conversion,
    first_touch_revenue,
    last_touch_revenue,
    linear_revenue,
    position_based_revenue

FROM with_attribution_credits
ORDER BY conversion_id, touchpoint_position
