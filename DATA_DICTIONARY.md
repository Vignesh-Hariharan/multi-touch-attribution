# Data Dictionary

## Raw Tables

### raw.ga4_events
Web analytics events from GA4.

| Column | Type | Description |
|--------|------|-------------|
| event_timestamp | TIMESTAMP | When the event occurred |
| event_date | DATE | Date of event |
| event_name | VARCHAR | Type of event (session_start, page_view, purchase) |
| user_pseudo_id | VARCHAR | Unique user identifier |
| session_id | VARCHAR | Unique session identifier |
| source | VARCHAR | Traffic source (google, facebook, direct) |
| medium | VARCHAR | Traffic medium (organic, social, email) |
| campaign | VARCHAR | Campaign name if applicable |
| page_location | VARCHAR | Page URL |
| device_category | VARCHAR | Device type (desktop, mobile, tablet) |
| country | VARCHAR | User country |
| revenue | DECIMAL(10,2) | Transaction revenue |
| transaction_id | VARCHAR | Unique transaction identifier |

### raw.impressions
Ad impression data from display campaigns.

| Column | Type | Description |
|--------|------|-------------|
| impression_id | VARCHAR | Unique impression identifier |
| impression_timestamp | TIMESTAMP | When ad was shown |
| user_pseudo_id | VARCHAR | User who saw the ad |
| campaign_id | VARCHAR | Campaign identifier |
| campaign_name | VARCHAR | Campaign name |
| campaign_type | VARCHAR | prospecting or retargeting |
| creative_format | VARCHAR | display, video, or native |
| publisher | VARCHAR | Where ad was shown |
| is_viewable | BOOLEAN | Was impression viewable |
| has_click | BOOLEAN | Did user click |
| device_category | VARCHAR | Device type |

### raw.campaigns
Campaign configuration data.

| Column | Type | Description |
|--------|------|-------------|
| campaign_id | VARCHAR | Unique campaign identifier |
| campaign_name | VARCHAR | Campaign name |
| advertiser | VARCHAR | Advertiser name |
| campaign_type | VARCHAR | prospecting or retargeting |
| creative_format | VARCHAR | display, video, or native |
| start_date | DATE | Campaign start |
| end_date | DATE | Campaign end |
| daily_budget | DECIMAL(10,2) | Daily spend limit |

## Analytics Tables

### analytics.fct_attribution
Final attribution table with revenue credit by touchpoint.

| Column | Type | Description |
|--------|------|-------------|
| conversion_id | VARCHAR | Transaction identifier |
| user_pseudo_id | VARCHAR | User identifier |
| conversion_timestamp | TIMESTAMP | When purchase occurred |
| total_revenue | DECIMAL(10,2) | Transaction amount |
| touchpoint_id | VARCHAR | Unique touchpoint identifier |
| touchpoint_timestamp | TIMESTAMP | When touchpoint occurred |
| channel | VARCHAR | Marketing channel |
| touchpoint_type | VARCHAR | impression or session |
| touchpoint_position | INTEGER | Position in journey (1 = first) |
| total_touchpoints | INTEGER | Total touchpoints for this conversion |
| days_to_conversion | INTEGER | Days from touchpoint to purchase |
| first_touch_revenue | DECIMAL(10,2) | Credit under first-touch model |
| last_touch_revenue | DECIMAL(10,2) | Credit under last-touch model |
| linear_revenue | DECIMAL(10,2) | Credit under linear model |
| position_based_revenue | DECIMAL(10,2) | Credit under position-based model |

### analytics.fct_pathways
Aggregated conversion paths.

| Column | Type | Description |
|--------|------|-------------|
| conversion_id | VARCHAR | Transaction identifier |
| user_pseudo_id | VARCHAR | User identifier |
| touchpoint_count | INTEGER | Number of touchpoints |
| channel_path | VARCHAR | Ordered list of channels |
| total_revenue | DECIMAL(10,2) | Transaction amount |
| first_touch_channel | VARCHAR | First channel in path |
| last_touch_channel | VARCHAR | Last channel in path |

## Key Metrics

- **Conversion**: A purchase event with revenue > 0
- **Touchpoint**: Any marketing interaction (web session or ad impression)
- **Attribution Window**: 30 days before conversion
- **Channel**: Derived from source/medium for web traffic, campaign_type/format for ads
