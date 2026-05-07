-- =============================================================================
-- Snowflake DDL for Attribution Analytics
-- Creates database, schemas, and tables for the attribution pipeline
-- =============================================================================

-- Database Setup
-- -----------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS ATTRIBUTION_DEV;
USE DATABASE ATTRIBUTION_DEV;

-- Schema Setup
-- -----------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS raw
    COMMENT = 'Raw data landing zone - all VARCHAR for flexibility';

CREATE SCHEMA IF NOT EXISTS analytics
    COMMENT = 'Curated analytics tables - dbt-managed';

-- Switch to raw schema for table creation
USE SCHEMA raw;

-- Raw Tables (All VARCHAR for initial load flexibility)
-- -----------------------------------------------------------------------------

-- GA4 Events Table
CREATE OR REPLACE TABLE raw.ga4_events (
    event_timestamp VARCHAR(50),
    event_date VARCHAR(10),
    event_name VARCHAR(100),
    user_pseudo_id VARCHAR(50),
    session_id VARCHAR(50),
    source VARCHAR(100),
    medium VARCHAR(50),
    campaign VARCHAR(200),
    page_location VARCHAR(500),
    device_category VARCHAR(20),
    country VARCHAR(100),
    revenue VARCHAR(20),
    transaction_id VARCHAR(50)
)
COMMENT = 'Raw GA4 event data - synthetic or from BigQuery API';

-- Campaigns Table
CREATE OR REPLACE TABLE raw.campaigns (
    campaign_id VARCHAR(30),
    campaign_name VARCHAR(100),
    advertiser VARCHAR(100),
    campaign_type VARCHAR(30),
    creative_format VARCHAR(30),
    start_date VARCHAR(20),
    end_date VARCHAR(20),
    daily_budget VARCHAR(20)
)
COMMENT = 'Campaign configuration data';

-- Ad Impressions Table
CREATE OR REPLACE TABLE raw.impressions (
    impression_id VARCHAR(50),
    impression_timestamp VARCHAR(50),
    user_pseudo_id VARCHAR(50),
    campaign_id VARCHAR(30),
    campaign_name VARCHAR(100),
    campaign_type VARCHAR(30),
    creative_format VARCHAR(30),
    publisher VARCHAR(50),
    is_viewable VARCHAR(10),
    has_click VARCHAR(10),
    device_category VARCHAR(20)
)
COMMENT = 'Ad impression event data';

-- Indexes for Query Performance
-- -----------------------------------------------------------------------------
-- Note: Snowflake doesn't use traditional indexes, but clustering helps

-- Enable clustering on user_pseudo_id for join performance
ALTER TABLE raw.ga4_events CLUSTER BY (user_pseudo_id);
ALTER TABLE raw.impressions CLUSTER BY (user_pseudo_id);

-- Metadata & Validation Views
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW raw.v_data_quality AS
SELECT
    'ga4_events' AS table_name,
    COUNT(*) AS row_count,
    COUNT(DISTINCT user_pseudo_id) AS unique_users,
    MIN(TRY_CAST(event_timestamp AS TIMESTAMP)) AS min_timestamp,
    MAX(TRY_CAST(event_timestamp AS TIMESTAMP)) AS max_timestamp
FROM raw.ga4_events

UNION ALL

SELECT
    'impressions' AS table_name,
    COUNT(*) AS row_count,
    COUNT(DISTINCT user_pseudo_id) AS unique_users,
    MIN(TRY_CAST(impression_timestamp AS TIMESTAMP)) AS min_timestamp,
    MAX(TRY_CAST(impression_timestamp AS TIMESTAMP)) AS max_timestamp
FROM raw.impressions

UNION ALL

SELECT
    'campaigns' AS table_name,
    COUNT(*) AS row_count,
    NULL AS unique_users,
    NULL AS min_timestamp,
    NULL AS max_timestamp
FROM raw.campaigns;

-- User Overlap Analysis View
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW raw.v_user_overlap AS
WITH web_users AS (
    SELECT DISTINCT user_pseudo_id FROM raw.ga4_events
),
ad_users AS (
    SELECT DISTINCT user_pseudo_id FROM raw.impressions
),
overlap AS (
    SELECT w.user_pseudo_id
    FROM web_users w
    INNER JOIN ad_users a ON w.user_pseudo_id = a.user_pseudo_id
)
SELECT
    (SELECT COUNT(*) FROM web_users) AS web_users,
    (SELECT COUNT(*) FROM ad_users) AS ad_users,
    (SELECT COUNT(*) FROM overlap) AS overlap_users,
    ROUND((SELECT COUNT(*) FROM overlap)::FLOAT / 
          (SELECT COUNT(*) FROM web_users) * 100, 2) AS overlap_pct;

-- =============================================================================
-- Grant Permissions (if using role-based access)
-- =============================================================================

-- Grant usage on schemas to SYSADMIN role
GRANT USAGE ON SCHEMA raw TO ROLE SYSADMIN;
GRANT USAGE ON SCHEMA analytics TO ROLE SYSADMIN;

-- Grant select on all tables/views in raw
GRANT SELECT ON ALL TABLES IN SCHEMA raw TO ROLE SYSADMIN;
GRANT SELECT ON ALL VIEWS IN SCHEMA raw TO ROLE SYSADMIN;

-- Grant full access on analytics (dbt will manage this schema)
GRANT ALL ON SCHEMA analytics TO ROLE SYSADMIN;

-- =============================================================================
-- Validation Queries (Run after data load to verify)
-- =============================================================================

-- Check data quality metrics
-- SELECT * FROM raw.v_data_quality;

-- Check user overlap
-- SELECT * FROM raw.v_user_overlap;

-- Check sample events
-- SELECT * FROM raw.ga4_events LIMIT 10;

-- Check sample impressions  
-- SELECT * FROM raw.impressions LIMIT 10;

-- Check campaigns
-- SELECT * FROM raw.campaigns ORDER BY campaign_id;
