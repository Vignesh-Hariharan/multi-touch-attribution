/*
    Test: Attribution Model Sum Check
    
    CRITICAL TEST: Ensures all 4 attribution models sum to actual revenue.
    Each model must allocate exactly 100% of revenue - no more, no less.
    
    This test MUST pass or the attribution math is wrong.
*/

WITH attribution AS (
    SELECT * FROM {{ ref('fct_attribution') }}
),

per_conversion_sums AS (
    SELECT
        conversion_id,
        MAX(total_revenue) AS actual_revenue,
        SUM(first_touch_revenue) AS first_touch_sum,
        SUM(last_touch_revenue) AS last_touch_sum,
        SUM(linear_revenue) AS linear_sum,
        SUM(position_based_revenue) AS position_based_sum
    FROM attribution
    GROUP BY conversion_id
),

failures AS (
    SELECT
        conversion_id,
        actual_revenue,
        first_touch_sum,
        last_touch_sum,
        linear_sum,
        position_based_sum,
        
        -- Calculate differences (should be near 0)
        ABS(first_touch_sum - actual_revenue) AS first_touch_diff,
        ABS(last_touch_sum - actual_revenue) AS last_touch_diff,
        ABS(linear_sum - actual_revenue) AS linear_diff,
        ABS(position_based_sum - actual_revenue) AS position_based_diff
        
    FROM per_conversion_sums
    WHERE 
        -- Allow 1 cent tolerance for rounding
        ABS(first_touch_sum - actual_revenue) > 0.01 OR
        ABS(last_touch_sum - actual_revenue) > 0.01 OR
        ABS(linear_sum - actual_revenue) > 0.01 OR
        ABS(position_based_sum - actual_revenue) > 0.01
)

-- Return failures (test passes if this returns 0 rows)
SELECT * FROM failures
