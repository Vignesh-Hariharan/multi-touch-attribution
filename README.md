# Multi-Touch Attribution Analytics

End-to-end attribution modeling pipeline built with Python, Snowflake, and dbt. Uses synthetic data to demonstrate production-grade analytics engineering practices while maintaining data privacy and reproducibility.

This project quantifies the true contribution of marketing touchpoints across the customer journey using four attribution models, revealing systematic biases in traditional last-click attribution.

## Dashboard

<p align="center">
  <a href="https://public.tableau.com/app/profile/vignesh.hariharan4351/viz/Book1_17622139583390/Multi-TouchAttributionAnalysisPosition-BasedvsLast-Click">
    <img src="images/Multi-Touch Attribution Analysis_ Position-Based vs Last-Click.png" alt="Multi-Touch Attribution Dashboard" width="600"/>
  </a>
</p>

**[View Dashboard on Tableau Public](https://public.tableau.com/app/profile/vignesh.hariharan4351/viz/Book1_17622139583390/Multi-TouchAttributionAnalysisPosition-BasedvsLast-Click)**

## Problem Statement

Traditional last-click attribution gives 100% credit to the final touchpoint before conversion, systematically undervaluing early-stage marketing efforts like prospecting campaigns. This leads to:

- Misallocated marketing budgets
- Underinvestment in awareness-stage channels
- Poor long-term growth strategy

## Solution

This project implements four attribution models (First Touch, Last Touch, Linear, Position-Based) to analyze conversion pathways and quantify the true value of each marketing channel across a realistic multi-touch customer journey.

### Key Finding

**Among 37 conversions (17% of total) that included paid prospecting touchpoints**, last-click attribution systematically undervalues early-stage awareness campaigns:

- **Prospecting Display:** +190% gap ($575 → $1,666 under position-based attribution)
- **Prospecting Native:** +107% gap ($1,778 → $3,677)
- **Prospecting Video:** +2% gap ($3,069 → $3,135)

**Why This Matters:** Even with conservative paid media penetration (17% of conversions), multi-touch attribution reveals **$3,056 in prospecting value** that last-click attribution misses entirely. This demonstrates how last-click models systematically bias toward organic/direct channels while ignoring the paid campaigns that initiated the customer journey.

**The Pattern:**
- **Paid Prospecting** (early-stage): +2% to +190% undervalued by last-click
- **Organic/Direct** (late-stage): -2% to -17% overvalued by last-click  
- **Email** (mid-funnel): +18% moderately undervalued

**Data Context:** This analysis simulates a conservative paid media strategy with 60% user overlap between web traffic and ad exposure, reflecting realistic match rates for programmatic platforms. For companies with higher paid penetration (40-60% of conversions), this misallocation scales proportionally.

## Technical Architecture

```
GA4 Events (Synthetic)          Programmatic Ads (Simulated)
  ~28K events, 220 conversions    ~14K impressions, 12 campaigns
         |                                    |
         +-------------> Python <-------------+
                           |
                      CSV Files
                    (data/ directory)
                           |
                           v
                  Snowflake Raw Schema
                   (3 raw tables)
                           |
                           v
              dbt Transformations Pipeline
           staging (3) → intermediate (2) → marts (2)
                           |
                           v
           Snowflake Analytics Schema
         (fct_attribution, fct_pathways)
                           |
              +------------+------------+
              |                         |
              v                         v
     Attribution Analysis         Data Quality Tests
     (4 attribution models)       (custom SQL tests)
```

**Stack**: Python 3.10+ | Snowflake | dbt 1.7 | Pandas | NumPy

## Quick Start

### Prerequisites

- Python 3.10+
- Snowflake account
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/Vignesh-Hariharan/attribution-analytics.git
cd attribution-analytics

# Install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure Snowflake credentials
cp .env.sample .env
# Edit .env with your Snowflake credentials

# Generate data
python src/extract_ga4.py
python src/generate_campaigns.py
python src/generate_impressions.py

# Load to Snowflake
python src/load_snowflake.py

# Run dbt models
cd dbt/attributions
dbt deps
dbt run --profiles-dir .
dbt test --profiles-dir .
```

## Project Structure

```
attribution-analytics/
├── src/
│   ├── config.py              # Configuration management
│   ├── extract_ga4.py         # Generate GA4 events
│   ├── generate_campaigns.py  # Generate campaign data
│   ├── generate_impressions.py # Generate ad impressions
│   └── load_snowflake.py      # Load data to Snowflake
├── dbt/
│   └── attributions/
│       ├── models/
│       │   ├── staging/        # Data cleaning layer
│       │   ├── intermediate/   # Business logic layer
│       │   └── marts/          # Analytics layer
│       ├── tests/              # Data quality tests
│       └── analyses/           # Ad-hoc analyses
├── sql/
│   └── snowflake_ddl.sql      # Database schema
├── data/                       # Generated CSV files
└── tests/                      # Python unit tests
```

## Attribution Models

This project implements four industry-standard attribution models to analyze how credit should be distributed across marketing touchpoints in the customer journey.

> **Visual diagrams sourced from:** [Roketto's Visual Guide to Marketing Attribution Models](https://www.helloroketto.com/articles/a-visual-guide-to-marketing-attribution-models)

### 1. First Touch Attribution

<img src="images/first-touch-attribution.png" alt="First Touch Attribution Model" width="600"/>

**100% credit to first touchpoint** - The initial interaction receives complete credit for conversions occurring later in the visitor journey. This model emphasizes awareness and acquisition channels.

**Implementation:** `WHEN touchpoint_position = 1 THEN revenue ELSE 0` ([fct_attribution.sql:42-45](dbt/attributions/models/marts/fct_attribution.sql#L42-L45))

### 2. Last Touch Attribution

<img src="images/last-touch-attribution.png" alt="Last Touch Attribution Model" width="600"/>

**100% credit to last touchpoint** - The final interaction before conversion receives all attribution credit. This is the default model in most analytics platforms but systematically undervalues early-stage marketing efforts.

**Implementation:** `WHEN touchpoint_position = total_touchpoints THEN revenue ELSE 0` ([fct_attribution.sql:47-52](dbt/attributions/models/marts/fct_attribution.sql#L47-L52))

### 3. Linear Attribution

<img src="images/linear-attribution.png" alt="Linear Attribution Model" width="600"/>

**Equal credit distributed across all touchpoints** - Every interaction in the customer journey receives equal attribution credit, providing a balanced view of all marketing efforts.

**Implementation:** `revenue / total_touchpoints` ([fct_attribution.sql:54-56](dbt/attributions/models/marts/fct_attribution.sql#L54-L56))

### 4. Position-Based Attribution (U-Shaped)

<img src="images/position-based-attribution.png" alt="Position-Based Attribution Model" width="600"/>

**Weighted credit to first and last positions**:
- 40% to first touchpoint (acquisition)
- 40% to last touchpoint (conversion)
- 20% distributed equally to middle touchpoints (nurture)

This model recognizes both the importance of initial awareness and final conversion moments.

**Implementation:** 40/40/20 split with edge case handling ([fct_attribution.sql:58-72](dbt/attributions/models/marts/fct_attribution.sql#L58-L72))

## Data Generation

The project generates realistic synthetic data to simulate production marketing datasets while ensuring privacy compliance and reproducibility. Key characteristics:

- **220 conversions** ($110K revenue) across 5,833 users (~3.8% conversion rate)
- **37 converters (17%)** exposed to paid prospecting campaigns before converting
- **Average journey length**: 1.9 touchpoints per conversion
- **47% multi-touch journeys** (2+ touchpoints), 53% single-touch
- **Temporal patterns**: Prospecting ads fire 1-14 days before first session (standard cold audience targeting)
- **User overlap**: 60% of web users are targeted with ads (realistic match rates for programmatic platforms)
- **Reproducibility**: Seeded random generation (seed=42) ensures consistent results for validation

**Data Scope Note:** This analysis reflects a conservative paid media strategy where paid prospecting reaches 17% of conversions. Real-world paid penetration varies widely (15-60% depending on industry and budget allocation). The attribution patterns and undervaluation principles demonstrated here scale proportionally with higher paid media investment.

## Validation

Run tests to ensure attribution logic is correct:

```bash
cd dbt/attributions
dbt test --profiles-dir .
```

Tests validate that:
- Attribution sums equal actual revenue for each conversion (custom SQL test)
- Data quality metrics pass (no nulls, valid types, referential integrity)
- Source data freshness and row counts meet expectations

## Results & Analysis

Query the attribution results to quantify channel undervaluation:

```sql
USE DATABASE ATTRIBUTION_DEV;
USE SCHEMA analytics;

-- Compare last-touch vs position-based attribution
SELECT
    channel,
    COUNT(DISTINCT conversion_id) AS conversions,
    ROUND(SUM(last_touch_revenue), 2) AS last_touch_revenue,
    ROUND(SUM(position_based_revenue), 2) AS position_based_revenue,
    ROUND((SUM(position_based_revenue) / NULLIF(SUM(last_touch_revenue), 0) - 1) * 100, 1) AS pct_change
FROM fct_attribution
GROUP BY channel
ORDER BY position_based_revenue DESC;
```

**Actual Results (seed=42, validated from Snowflake):**

| Channel | Last Touch Revenue | Position-Based Revenue | Gap % |
|---------|-------------------|------------------------|-------|
| **Paid Prospecting (Undervalued)** | | | |
| prospecting_display | $575 | $1,666 | **+190%** |
| prospecting_native | $1,778 | $3,677 | **+107%** |
| prospecting_video | $3,069 | $3,135 | +2% |
| **Organic/Direct (Overvalued)** | | | |
| google_organic | $16,273 | $14,129 | -13% |
| referral | $5,213 | $4,338 | -17% |
| direct | $20,805 | $20,460 | -2% |
| social_facebook | $6,806 | $6,516 | -4% |
| **Mid-Funnel** | | | |
| email | $3,381 | $3,979 | +18% |

**Key Insight:** Last-click attribution systematically overvalues organic/direct channels while undervaluing paid prospecting campaigns that initiated awareness. Among the 37 conversions with prospecting touchpoints, prospecting display receives nearly **3x more credit** under position-based models, revealing how traditional attribution masks the true value of top-of-funnel investments.

**Business Impact:** Even at 17% paid penetration, $3,056 in prospecting value is hidden by last-click attribution. For companies with 40-60% paid media penetration, this misallocation could represent $20-40K in budget optimization opportunities per $100K spend.

For detailed validation queries, see `dbt/attributions/analyses/validate_finding.sql` and `channel_comparison.sql`.

## Documentation

- **DATA_DICTIONARY.md**: Full schema documentation for all tables and columns
- **ASSUMPTIONS.md**: Key assumptions in data generation and attribution modeling
- **dbt docs**: Generate with `dbt docs generate --profiles-dir .` and serve with `dbt docs serve`

## References & Further Reading

This project's methodology and findings are grounded in established marketing attribution research:

### Attribution Modeling
- [Google Analytics Attribution Models](https://support.google.com/analytics/answer/10596866) - Overview of standard attribution models including first-click, last-click, linear, and position-based
- [What is Multi-Touch Attribution?](https://www.rockerbox.com/faq/what-is-multi-touch-attribution) - Rockerbox's explanation of MTA and its importance in understanding customer journeys

- [Data-Driven Attribution](https://support.google.com/google-ads/answer/6394265) - Google Ads documentation on moving beyond last-click models


### Programmatic Advertising & Campaign Strategy
- [Understanding Prospecting Campaigns](https://support.google.com/google-ads/answer/2404190) - Google Ads documentation on campaign structures and targeting
- [Attribution Lookback Windows](https://support.google.com/analytics/answer/1662518) - How attribution windows impact channel credit

### Data Modeling
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices) - Official dbt documentation on project structure and SQL style
- [Snowflake Table Design](https://docs.snowflake.com/en/user-guide/tables-storage-considerations) - Snowflake optimization and design guidelines

## Author

**Vignesh Hariharan**  
Analytics Engineer | Data Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://linkedin.com/in/h-vignesh)
[![Portfolio](https://img.shields.io/badge/Portfolio-View_Projects-green)](https://github.com/Vignesh-Hariharan)

> **Portfolio Project** demonstrating production-grade analytics engineering with modern 
> data stack (Python, Snowflake, dbt). View my other projects and experience at 
> [LinkedIn](https://linkedin.com/in/h-vignesh).
