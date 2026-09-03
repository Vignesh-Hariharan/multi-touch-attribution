# Multi-Touch Attribution Analytics

[![CI](https://github.com/Vignesh-Hariharan/multi-touch-attribution/actions/workflows/ci.yml/badge.svg)](https://github.com/Vignesh-Hariharan/multi-touch-attribution/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8.svg)](https://www.snowflake.com/)
[![dbt](https://img.shields.io/badge/dbt-FF694B.svg)](https://www.getdbt.com/)
[![Tableau Public](https://img.shields.io/badge/Tableau-Live%20Dashboard-E97627.svg)](https://public.tableau.com/views/Multi-TouchAttributionAnalysis/Multi-TouchAttributionAnalysis?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)

An attribution pipeline that compares four models (first-touch, last-touch, linear,
position-based) on a synthetic marketing dataset, built with Python, Snowflake and dbt.
It runs on GA4-schema event data plus programmatic ad impressions, layers the transforms
in dbt (staging → intermediate → marts), and checks the output with custom SQL tests.

## Dashboard

<p align="center">
  <a href="https://public.tableau.com/views/Multi-TouchAttributionAnalysis/Multi-TouchAttributionAnalysis?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link">
    <img src="images/Multi-Touch Attribution Analysis.png" alt="Multi-Touch Attribution Dashboard" width="600"/>
  </a>
</p>

[View the dashboard on Tableau Public](https://public.tableau.com/views/Multi-TouchAttributionAnalysis/Multi-TouchAttributionAnalysis?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)

## The question

Last-click attribution gives 100% of the credit to the final touchpoint before a
conversion. That default undervalues the campaigns that started the journey — prospecting
and awareness — which biases budget toward channels that only show up near the end. The
pipeline quantifies that bias by scoring the same conversions under four models and
comparing the credit each channel receives.

## What the data shows

Of 220 conversions, 37 (17%) included a paid prospecting touchpoint before converting.
For those channels, position-based attribution assigns materially more credit than
last-click:

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

The pattern is consistent: early-stage paid channels are undervalued by last-click (up to
+190%), late-stage organic and direct are overvalued (-2% to -17%), and email sits in the
middle. Even at this conservative 17% paid penetration, about $3,056 of prospecting credit
moves between channels depending on the model. The gap scales with paid penetration —
higher paid mix, larger reallocation.

Results are reproducible: data generation is seeded (`seed=42`), so the numbers above match
a clean run. Validation queries are in `dbt/attributions/analyses/`.

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

Paid penetration here (17% of conversions) is deliberately conservative; real campaigns run
15–60% depending on budget. The direction of the attribution gap holds across that range.

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
