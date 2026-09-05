# Multi-Touch Attribution Analytics

[![CI](https://github.com/Vignesh-Hariharan/multi-touch-attribution/actions/workflows/ci.yml/badge.svg)](https://github.com/Vignesh-Hariharan/multi-touch-attribution/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8.svg)](https://www.snowflake.com/)
[![dbt](https://img.shields.io/badge/dbt-FF694B.svg)](https://www.getdbt.com/)
[![Tableau Public](https://img.shields.io/badge/Tableau-Live%20Dashboard-E97627.svg)](https://public.tableau.com/views/Multi-TouchAttributionAnalysis/Multi-TouchAttributionAnalysis?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)

An attribution pipeline that compares four models (first-touch, last-touch, linear,
position-based) on a synthetic marketing dataset. Python loads GA4-schema events and
ad impressions into Snowflake; dbt builds staging → intermediate → marts and tests
that attributed revenue sums back to actuals.

## Dashboard

<p align="center">
  <a href="https://public.tableau.com/views/Multi-TouchAttributionAnalysis/Multi-TouchAttributionAnalysis?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link">
    <img src="images/Multi-Touch Attribution Analysis.png" alt="Multi-Touch Attribution Dashboard" width="600"/>
  </a>
</p>

[View the dashboard on Tableau Public](https://public.tableau.com/views/Multi-TouchAttributionAnalysis/Multi-TouchAttributionAnalysis?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)

The live viz compares last-click vs position-based — the pair with a single gap %.
First-touch and linear are in the mart.

## The question

Last-click gives 100% of conversion credit to the final touchpoint. That's the
platform default, so channels that show up early get less. The pipeline scores
the same conversions four ways so you can see where the models split, and so all
four still add up to the same revenue.

## What this run produces

Synthetic data, seed 42. That way dbt tests have a known answer and CI doesn't
need a GA4 login. On real traffic the gaps move with journey length and paid mix.

Of 220 conversions in this run, 37 (17%) had a paid prospecting touch before
converting. Position-based vs last-click:

| Channel | Last-touch | Position-based | Gap |
|---------|-----------:|---------------:|----:|
| prospecting_display | $575 | $1,666 | +190% |
| prospecting_native | $1,778 | $3,677 | +107% |
| prospecting_video | $3,069 | $3,135 | +2% |
| email | $3,381 | $3,979 | +18% |
| direct | $20,805 | $20,460 | -2% |
| social_facebook | $6,806 | $6,516 | -4% |
| google_organic | $16,273 | $14,129 | -13% |
| referral | $5,213 | $4,338 | -17% |

Display's +190% comes from this generator (17% paid mix, 1.9 average touches,
40/40/20). Don't read it as a live-campaign number. Queries that rebuild the
table are in `dbt/attributions/analyses/`.

## Architecture

```
GA4 Events (synthetic)          Programmatic Ads (simulated)
  ~28K events, 220 conversions    ~14K impressions, 12 campaigns
         |                                    |
         +-------------> Python <-------------+
                           |
                      CSV files (data/)
                           |
                           v
                  Snowflake raw schema (3 tables)
                           |
                           v
              dbt: staging (3) -> intermediate (2) -> marts (2)
                           |
                           v
           Snowflake analytics schema
         (fct_attribution, fct_pathways)
                           |
              +------------+------------+
              v                         v
     Attribution models          Custom SQL tests
```

Stack: Python 3.10+, Snowflake, dbt 1.7, pandas, NumPy.

## Setup

```bash
git clone https://github.com/Vignesh-Hariharan/multi-touch-attribution.git
cd multi-touch-attribution

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.sample .env               # add your Snowflake credentials

# generate the synthetic data
python src/generate_ga4.py
python src/generate_campaigns.py
python src/generate_impressions.py

# load and transform
python src/load_snowflake.py
cd dbt/attributions
dbt deps
dbt run --profiles-dir .
dbt test --profiles-dir .
```

## Project structure

```
multi-touch-attribution/
├── src/                          # data generation + Snowflake load
│   ├── config.py
│   ├── generate_ga4.py
│   ├── generate_campaigns.py
│   ├── generate_impressions.py
│   └── load_snowflake.py
├── dbt/attributions/
│   ├── models/
│   │   ├── staging/              # cleaning
│   │   ├── intermediate/         # journey construction
│   │   └── marts/                # fct_attribution, fct_pathways
│   ├── tests/                    # custom SQL tests
│   └── analyses/                 # validation queries
├── sql/snowflake_ddl.sql
├── data/                         # generated CSVs (git-ignored)
└── tests/                        # Python unit tests
```

## The four models

All four are implemented in [`fct_attribution.sql`](dbt/attributions/models/marts/fct_attribution.sql).

- **First touch** — 100% to the first touchpoint. `WHEN touchpoint_position = 1 THEN revenue ELSE 0`
- **Last touch** — 100% to the last touchpoint; the platform default. `WHEN touchpoint_position = total_touchpoints THEN revenue ELSE 0`
- **Linear** — equal credit across touchpoints. `revenue / total_touchpoints`
- **Position-based (U-shaped)** — 40% first, 40% last, 20% split across the middle, with edge-case handling for single- and two-touch journeys.

Model diagrams adapted from [Roketto's visual guide to attribution models](https://www.helloroketto.com/articles/a-visual-guide-to-marketing-attribution-models).

## Data generation

The synthetic dataset is built to resemble a programmatic marketing funnel:

- 220 conversions ($110K revenue) across 5,833 users (~3.8% conversion rate)
- 37 converters (17%) exposed to paid prospecting before converting
- Average journey length 1.9 touchpoints; 47% multi-touch, 53% single-touch
- Prospecting ads fire 1–14 days before the first session (cold-audience timing)
- 60% of web users are also ad-targeted, in the range of real programmatic match rates

Paid mix here is 17% of conversions, the low end of the 15–60% range campaigns
actually run. Turn that up and the gaps get bigger — that's the generator.

## Validation

```bash
cd dbt/attributions
dbt test --profiles-dir .
```

Tests check that attributed revenue sums back to actual revenue per conversion, that there
are no nulls or type violations, and that row counts and freshness match expectations.

## Documentation

- `DATA_DICTIONARY.md` — table and column definitions
- `ASSUMPTIONS.md` — data-generation and modeling assumptions
- dbt docs — `dbt docs generate --profiles-dir .` then `dbt docs serve`

## References

- [Google Analytics attribution models](https://support.google.com/analytics/answer/10596866)
- [Google Ads: data-driven attribution](https://support.google.com/google-ads/answer/6394265)
- [dbt best practices](https://docs.getdbt.com/guides/best-practices)

---

Vignesh Hariharan — [LinkedIn](https://linkedin.com/in/h-vignesh) · [GitHub](https://github.com/Vignesh-Hariharan)
