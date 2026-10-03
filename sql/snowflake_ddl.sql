-- Raw landing tables, run by src/load_snowflake.py inside the database named by
-- SNOWFLAKE_DATABASE. Columns are VARCHAR and in the same order as the generated
-- CSVs; the dbt staging models apply types.

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE TABLE raw.ga4_events (
    event_timestamp VARCHAR,
    event_date VARCHAR,
    event_name VARCHAR,
    user_pseudo_id VARCHAR,
    session_id VARCHAR,
    source VARCHAR,
    medium VARCHAR,
    campaign VARCHAR,
    page_location VARCHAR,
    device_category VARCHAR,
    country VARCHAR,
    revenue VARCHAR,
    transaction_id VARCHAR
);

CREATE OR REPLACE TABLE raw.campaigns (
    campaign_id VARCHAR,
    campaign_name VARCHAR,
    advertiser VARCHAR,
    campaign_type VARCHAR,
    creative_format VARCHAR,
    start_date VARCHAR,
    end_date VARCHAR,
    daily_budget VARCHAR
);

CREATE OR REPLACE TABLE raw.impressions (
    impression_id VARCHAR,
    impression_timestamp VARCHAR,
    user_pseudo_id VARCHAR,
    campaign_id VARCHAR,
    campaign_name VARCHAR,
    campaign_type VARCHAR,
    creative_format VARCHAR,
    publisher VARCHAR,
    is_viewable VARCHAR,
    has_click VARCHAR,
    device_category VARCHAR
);
