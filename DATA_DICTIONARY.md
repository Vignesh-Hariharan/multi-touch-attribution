# Data Dictionary

## Raw (`raw` schema)

Loaded from `data/*.csv` by `src/load_snowflake.py`. Every column is VARCHAR; the
types below are what the staging models cast to.

### raw.ga4_events

One row per event.

| Column | Type | Description |
|--------|------|-------------|
| event_timestamp | TIMESTAMP | When the event fired, second precision |
| event_date | DATE | Date of the event (YYYYMMDD in the raw file, recomputed from the timestamp in staging) |
| event_name | VARCHAR | session_start, page_view, scroll, add_to_cart, begin_checkout, purchase |
| user_pseudo_id | VARCHAR | Browser cookie id, `user_000001` |
| session_id | VARCHAR | `session_000001`, numbered in order of session start |
| source | VARCHAR | (direct), google, facebook, newsletter, or a referring domain |
| medium | VARCHAR | (none), organic, social, referral, email |
| campaign | VARCHAR | `monthly_newsletter` for email, otherwise (not set) |
| page_location | VARCHAR | Page URL |
| device_category | VARCHAR | mobile, desktop, tablet; fixed per user |
| country | VARCHAR | Always United States |
| revenue | DECIMAL(10,2) | Order value on purchase rows, 0 elsewhere |
| transaction_id | VARCHAR | `txn_000001` on purchase rows, null elsewhere |

### raw.campaigns

One row per campaign; 12 in total.

| Column | Type | Description |
|--------|------|-------------|
| campaign_id | VARCHAR | `camp_0001` |
| campaign_name | VARCHAR | `{FORMAT}_{TYPE}_{nn}` |
| advertiser | VARCHAR | RetailCo, SaaS_Platform, CPG_Brand |
| campaign_type | VARCHAR | prospecting, retargeting |
| creative_format | VARCHAR | display, video, native |
| start_date | DATE | First day of the flight |
| end_date | DATE | Last day of the flight, inclusive |
| daily_budget | DECIMAL(10,2) | Not used by the models |

### raw.impressions

One row per impression served to a site user, viewable or not.

| Column | Type | Description |
|--------|------|-------------|
| impression_id | VARCHAR | `imp_0000001`, numbered in time order |
| impression_timestamp | TIMESTAMP | When the ad was served |
| user_pseudo_id | VARCHAR | Same id space as ga4_events |
| campaign_id | VARCHAR | References raw.campaigns |
| campaign_name | VARCHAR | Denormalized from campaigns |
| campaign_type | VARCHAR | prospecting, retargeting |
| creative_format | VARCHAR | display, video, native |
| publisher | VARCHAR | One of five publisher groups |
| is_viewable | BOOLEAN | Met the MRC viewability standard |
| has_click | BOOLEAN | Clicked; only possible when viewable |
| device_category | VARCHAR | The user's device |

## Intermediate (views)

**int_touchpoints**: one row per session (at its session_start) and per viewable
impression. Columns: touchpoint_id, user_pseudo_id, touchpoint_timestamp, channel,
touchpoint_type (`session` or `impression`), device_category.

**int_attribution_window**: each purchase joined to the same user's touchpoints in
the 30 days before it. Grain is conversion_id × touchpoint_id. Adds
days_to_conversion, touchpoint_position (1 = earliest, ties broken by
touchpoint_id) and total_touchpoints.

## Marts (`analytics` schema, tables)

### fct_attribution

Credit per touchpoint under each model. **Grain:** conversion_id × touchpoint_id.
A session or impression can appear under more than one conversion when a user
bought twice.

| Column | Type | Description |
|--------|------|-------------|
| conversion_id | VARCHAR | transaction_id of the purchase |
| user_pseudo_id | VARCHAR | Buyer |
| conversion_timestamp | TIMESTAMP | Purchase time |
| conversion_revenue | DECIMAL | Purchase revenue, repeated on every touchpoint row; don't sum it |
| touchpoint_id | VARCHAR | session_id or impression_id |
| touchpoint_timestamp | TIMESTAMP | Session start or impression time |
| channel | VARCHAR | Site channel, or `{campaign_type}_{creative_format}` for impressions |
| touchpoint_type | VARCHAR | session, impression |
| touchpoint_position | INTEGER | 1 = earliest touch in the window |
| total_touchpoints | INTEGER | Touches in this conversion's window |
| days_to_conversion | INTEGER | Calendar days from touch to purchase |
| first_touch_revenue | DECIMAL | Credit under first-touch |
| last_touch_revenue | DECIMAL | Credit under last-touch |
| linear_revenue | DECIMAL | Credit under linear |
| position_based_revenue | DECIMAL | Credit under 40/40/20 position-based |

### fct_conversions

One row per purchase. Use this for revenue, order and AOV figures.

| Column | Type | Description |
|--------|------|-------------|
| conversion_id | VARCHAR | transaction_id |
| user_pseudo_id | VARCHAR | Buyer |
| session_id | VARCHAR | Session the purchase happened in |
| conversion_timestamp | TIMESTAMP | Purchase time |
| conversion_date | DATE | Purchase date |
| revenue | DECIMAL | Order value |
| session_channel | VARCHAR | Channel of the purchase session |
| device_category | VARCHAR | Buyer's device |
| touchpoint_count | INTEGER | Touches in the 30-day window (at least 1) |
| paid_touchpoint_count | INTEGER | Of those, viewable impressions |
| has_paid_touch | BOOLEAN | paid_touchpoint_count > 0 |
| first_touch_channel | VARCHAR | Channel of position 1 |
| last_touch_channel | VARCHAR | Channel of the final position |
| days_from_first_touch | INTEGER | days_to_conversion of the earliest touch |
| pathway | VARCHAR | Channels in order, joined with ` > ` |

### agg_channel_attribution

One row per channel.

| Column | Type | Description |
|--------|------|-------------|
| channel | VARCHAR | As in fct_attribution |
| channel_group | VARCHAR | `Paid media` (impressions) or `Site visit` (sessions) |
| touchpoints | INTEGER | Touch rows credited, counted once per conversion they sit in |
| conversions_touched | INTEGER | Distinct conversions with this channel in the path |
| first_touch_revenue | DECIMAL | Total credit under first-touch |
| last_touch_revenue | DECIMAL | Total credit under last-touch |
| linear_revenue | DECIMAL | Total credit under linear |
| position_based_revenue | DECIMAL | Total credit under position-based |
| position_vs_last_touch | DECIMAL | position_based_revenue − last_touch_revenue |
| position_vs_last_touch_pct | DECIMAL | That difference over last_touch_revenue; null when last-touch is 0 |
| last_touch_share | DECIMAL | Channel's share of all last-touch credit |
| position_based_share | DECIMAL | Channel's share of all position-based credit |

### fct_pathways

One row per channel sequence that converted at least `min_pathway_conversions`
(default 2) times.

| Column | Type | Description |
|--------|------|-------------|
| pathway | VARCHAR | Channels in order, joined with ` > ` |
| pathway_length | INTEGER | Touches in the sequence |
| conversion_count | INTEGER | Purchases that followed it |
| total_revenue | DECIMAL | Their revenue |
| avg_revenue | DECIMAL | Average order value on the path |
| share_of_conversions | DECIMAL | conversion_count over all purchases, including paths filtered out here |

## Exports

`export/fct_conversions.csv`, `export/agg_channel_attribution.csv` and
`export/fct_pathways.csv` are the three reporting marts as built on Snowflake,
sorted by their key, with decimals rounded to four places. They're the
dashboard's data sources.
