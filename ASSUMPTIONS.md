# Project Assumptions

## Data Generation Assumptions

### User Behavior
- Users have 1-5 sessions on average, with most having 1-2 sessions
- **Conversion rate is approximately 3-4%** of total users (220 conversions / 5,833 users = 3.8%) — see [Shopify](https://www.shopify.com/blog/ecommerce-conversion-rate) benchmarks
- Sessions occur during business hours (8am-10pm) weighted toward evening
- Session duration varies from 2-30 minutes
- Users interact with 3-8 pages per session

### Marketing Touchpoints
- **60% of web users are exposed to paid advertising** (realistic programmatic match rates due to Safari ITP/Firefox tracking protection)
- **Prospecting campaigns target cold audiences 1-14 days before their first website visit** — based on [Google Ads](https://support.google.com/google-ads/answer/3419241) 30-day view-through window
- Ad impressions are predominantly prospecting-focused (awareness-stage campaigns)
- **67% of ad impressions are viewable** — per [MRC standards](https://mediaratingcouncil.org/) (50% minimum) and IAS industry reports (66-68% average)
- **Click-through rate is approximately 0.1-1.4%** depending on format — [Google Display](https://support.google.com/google-ads/answer/2615875) (0.1%), [YouTube](https://support.google.com/google-ads/answer/2375464) (1.4%)

### Campaign Structure
- 12 campaigns total across three creative formats: display, video, native
- Campaign data includes both prospecting and retargeting types for completeness
- Campaigns run for the full date range (Nov 1 - Dec 15, 2024)
- Daily budgets vary by format: display ($500-750), video ($1200-1800), native ($800-1200)
- **Analysis Focus**: This project analyzes prospecting campaigns vs organic/direct channels

## Attribution Assumptions

### Attribution Window
- 30-day lookback window from conversion
- Only touchpoints before conversion are included
- No post-conversion touchpoints considered

### Attribution Models
- **First Touch**: Assumes first interaction drives all value
- **Last Touch**: Assumes final interaction drives all value (industry baseline)
- **Linear**: Assumes equal contribution from all touchpoints
- **Position-Based (U-Shaped)**: 40% first, 40% last, 20% middle (assumes awareness and closing moments most important)

### Channel Classification
- Direct traffic: medium = '(none)'
- Organic search: medium = 'organic', source = search engine
- Social: medium = 'social', source = social platform
- Email: medium = 'email'
- Referral: medium = 'referral'
- Paid ads: campaign_type + creative_format (e.g., prospecting_display)

## Technical Assumptions

### Data Quality
- All timestamps are valid and in chronological order
- User IDs are consistent across sessions and impressions
- Revenue values are positive for all conversions
- No duplicate transaction IDs

### Snowflake Environment
- ACCOUNTADMIN role has full permissions
- COMPUTE_WH warehouse is available and running
- Database can be dropped and recreated cleanly
- X-Small warehouse is sufficient for this data volume

### dbt Assumptions
- dbt 1.7+ is compatible with Snowflake adapter
- Views are sufficient for staging/intermediate layers
- Tables are needed for final marts (query performance)
- Tests run after model builds

## Business Assumptions

### Marketing Strategy
- Prospecting campaigns focus on awareness and new customer acquisition
- Analysis examines how last-click attribution undervalues early-stage paid media
- Multi-touch journeys occur in 47% of conversions (average 1.9 touchpoints overall)
- Display ads drive awareness even if they don't directly lead to clicks

### Analysis Scope
- **Primary Focus**: Paid prospecting campaigns vs organic/direct channels
- **Key Question**: How much credit should awareness-stage paid media receive?
- Analysis timeframe is 45 days (sufficient for attribution analysis)
- B2C e-commerce context (single purchase per transaction)
- 17% of conversions include paid prospecting touchpoints (conservative paid media strategy)
- No consideration of offline touchpoints (TV, radio, direct mail)

## Data Source & Methodology

This project uses **synthetic data** generated to realistically simulate GA4 web analytics and programmatic advertising patterns. This approach is necessary because:

- Real GA4 data contains proprietary customer information protected by privacy regulations (GDPR, CCPA)
- Programmatic ad platform data (DV360, Trade Desk) requires client authorization and cannot be publicly shared
- Marketing data from employers is confidential and subject to non-disclosure agreements
- Public portfolio projects require reproducible, shareable datasets that don't expose business-sensitive information

The synthetic data generation follows industry-standard patterns observed in real e-commerce and programmatic advertising, ensuring the attribution methodology and findings remain valid and applicable to production environments.

## Research Sources

All parameters are based on publicly available industry benchmarks:

### E-commerce Metrics
- **Conversion Rate (2.5%):** [Shopify E-commerce Benchmarks](https://www.shopify.com/blog/ecommerce-conversion-rate) (2-4% typical), [Baymard Institute Cart Abandonment](https://baymard.com/lists/cart-abandonment-rate) (3.4% average)
- **Average Order Value ($25-$500):** [Statista E-commerce Statistics](https://www.statista.com/topics/871/online-shopping/) ($100-$200 typical range)

### Programmatic Advertising
- **Cookie Match Rate (60%):** Industry reports show 50-70% match rates due to Safari ITP and Firefox tracking protection
- **Display CTR (0.10%):** [Google Ads Benchmarks](https://support.google.com/google-ads/answer/2615875) (0.05-0.15% for cold audiences)
- **Video CTR (1.40%):** [YouTube TrueView Benchmarks](https://support.google.com/google-ads/answer/2375464) (1-2% typical)
- **Native CTR (0.28%):** Outbrain and Taboola platform benchmarks (0.2-0.4%)
- **Retargeting Lift (2x):** Industry consensus that retargeting outperforms prospecting 2-3x

### Ad Quality Standards
- **Viewability (67%):** [MRC Viewability Standard](https://mediaratingcouncil.org/) (50% minimum threshold), IAS Media Quality Reports (66-68% industry average)
- **Attribution Window (7-30 days):** [Google Ads View-Through Conversions](https://support.google.com/google-ads/answer/3419241) (30-day default), Facebook Ads (7-day default)

### Traffic Distribution
- **Channel Mix (40% direct, 30% organic):** BrightEdge Organic Search Traffic Report, adjusted for B2C e-commerce patterns

Parameters use midpoint values when industry sources provide ranges (e.g., 0.05-0.15% CTR → 0.10%).

## Known Limitations

1. **Analysis Scope**: Focuses on prospecting vs organic/direct attribution; does not analyze retargeting campaign attribution
2. **Conservative Paid Penetration**: Only 17% of conversions include paid prospecting touchpoints (lower than typical 30-50% paid penetration in production)
3. **Simplified Journey Paths**: Real customer journeys may include more touchpoint variety and cross-channel complexity
4. **Single Device Assumption**: Does not model cross-device attribution (mobile to desktop conversions)
5. **No Seasonality Effects**: Uniform traffic distribution rather than seasonal peaks/troughs
6. **Controlled Parameters**: Conversion rates, user overlap, and budgets are fixed rather than dynamic

## Why These Assumptions Matter

These assumptions enable:
- **Reproducibility**: Anyone can run the pipeline and validate the findings independently
- **Clear Signal**: Controlled data reveals attribution model differences without confounding factors
- **Realistic Patterns**: Campaign timing and user behavior mirror actual programmatic advertising constraints
- **Methodology Focus**: Demonstrates attribution engineering skills without business-sensitive data

For production deployment, this framework would be adapted to:
- Connect to actual GA4 and ad platform APIs (Google Analytics Data API, DV360 API)
- Incorporate client-specific business rules and KPIs
- Add cross-device identity resolution
- Include all relevant marketing channels and touchpoints
- Validate assumptions against observed historical patterns
