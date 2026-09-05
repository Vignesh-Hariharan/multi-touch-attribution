/*
    Display gap: position-based vs last-click on prospecting_display.

    On seed=42 this lands around +190%. That range is a property of the
    generator (paid mix, journey length, 40/40/20), not a market measurement.
*/

WITH last_touch AS (
    SELECT
        channel,
        SUM(last_touch_revenue) AS revenue
    FROM {{ ref('fct_attribution') }}
    WHERE channel LIKE '%prospecting%display%'
    GROUP BY channel
),

position_based AS (
    SELECT
        channel,
        SUM(position_based_revenue) AS revenue
    FROM {{ ref('fct_attribution') }}
    WHERE channel LIKE '%prospecting%display%'
    GROUP BY channel
),

comparison AS (
    SELECT
        COALESCE(lt.channel, pb.channel) AS channel,
        lt.revenue AS last_touch_revenue,
        pb.revenue AS position_based_revenue,
        pb.revenue - lt.revenue AS absolute_increase,
        ROUND((pb.revenue - lt.revenue) / NULLIF(lt.revenue, 0) * 100, 1) AS percent_increase
    FROM last_touch lt
    FULL OUTER JOIN position_based pb
        ON lt.channel = pb.channel
)

SELECT
    channel,
    ROUND(last_touch_revenue, 2) AS last_touch_revenue,
    ROUND(position_based_revenue, 2) AS position_based_revenue,
    ROUND(absolute_increase, 2) AS absolute_increase,
        percent_increase AS gap_pct
FROM comparison
ORDER BY percent_increase DESC;
