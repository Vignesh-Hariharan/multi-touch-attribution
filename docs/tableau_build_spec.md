# Tableau build spec: Multi-Touch Attribution

Build specification for the Tableau Public dashboard. The sources are the three
CSVs in `export/`, written from Snowflake by `python src/export_marts.py --target dev`.

---

## 1. The story to lead with

The same 277 purchases ($38,492) are credited four ways. Paid media gets $0 under
last-touch and $20,603 under first-touch; position-based lands at $11,600 (30%).
The dashboard should make that range the first thing anyone sees, then show which
channels give up credit when you move off last-touch.

Suggested title line:

> Last-touch credits paid media with $0 of $38.5K. Position-based credits $11.6K.

Use "last-touch" everywhere, never "last-click". Viewable impressions count as
touches, so last-click would be the wrong name.

---

## 2. Data sources

Four connections, kept separate. Don't relate or blend them; they are at
different grains.

| Name in Tableau | File | Grain | Notes |
|-----------------|------|-------|-------|
| Conversions | `fct_conversions.csv` | one row per purchase | All KPI cards come from here |
| Channels | `agg_channel_attribution.csv` | one row per channel | Wide: one column per model |
| Channels by model | `agg_channel_attribution.csv` again | channel × model | Pivot the four `*_revenue` model columns (see below) |
| Pathways | `fct_pathways.csv` | one row per pathway | |

For **Channels by model**, select `first_touch_revenue`, `last_touch_revenue`,
`linear_revenue` and `position_based_revenue` and choose Pivot. Rename the two new
fields to `Model Field` and `Credited Revenue`. Only use `channel`,
`channel_group`, `Model Field` and `Credited Revenue` from this source: after the
pivot, every other column repeats four times.

Types: `conversion_timestamp` → Date & Time, `conversion_date` → Date, every
`*revenue*` field → currency (0 decimals), `*_share` and `*_pct` → percentage.

Revenue never comes from summing `fct_attribution`'s `conversion_revenue`, which is
why that table isn't exported. That mistake is what produced the old 110K figure.

---

## 3. Calculated fields

### Conversions

```
// Revenue
SUM([revenue])

// Purchases
COUNTD([conversion_id])

// AOV
SUM([revenue]) / COUNTD([conversion_id])

// Purchases with paid touch %
SUM(IIF([has_paid_touch], 1, 0)) / COUNTD([conversion_id])

// Avg touches per purchase
AVG([touchpoint_count])
```

### Channels by model

```
// Model
CASE [Model Field]
  WHEN "last_touch_revenue"     THEN "Last-touch"
  WHEN "position_based_revenue" THEN "Position-based"
  WHEN "linear_revenue"         THEN "Linear"
  WHEN "first_touch_revenue"    THEN "First-touch"
END

// Model Order   (sort Model by this, ascending)
CASE [Model]
  WHEN "Last-touch" THEN 1 WHEN "Position-based" THEN 2
  WHEN "Linear" THEN 3 WHEN "First-touch" THEN 4
END

// Share of Model Revenue   (table calc, compute using channel_group)
SUM([Credited Revenue]) / TOTAL(SUM([Credited Revenue]))
```

### Channels: model comparison parameter

```
// p_Compare : string list = "Position-based", "Linear", "First-touch"   (default Position-based)

// Compared Revenue
CASE [p_Compare]
  WHEN "Position-based" THEN SUM([position_based_revenue])
  WHEN "Linear"         THEN SUM([linear_revenue])
  WHEN "First-touch"    THEN SUM([first_touch_revenue])
END

// Change vs Last-touch
[Compared Revenue] - SUM([last_touch_revenue])
```

Don't chart `position_vs_last_touch_pct`. It's null for every paid channel,
because their last-touch credit is $0, and a percentage over zero means nothing.
Show the dollar change instead.

---

## 4. Worksheets

### 4.1 KPI row (Conversions)
Five cards: Revenue, Purchases, AOV, Purchases with paid touch %, Avg touches per
purchase. Number plus a small caption only.

### 4.2 Paid share by model: the headline (Channels by model)
- Rows: `Model`, sorted by `Model Order`
- Columns: `SUM(Credited Revenue)`, stacked by `channel_group`
- Color: Paid media in the accent, Site visit in gray
- Label the Paid media segment with its dollars and `Share of Model Revenue`

Four bars of identical length ($38,492), with the paid segment growing from
nothing to just over half. That's the whole argument in one chart.

### 4.3 Change vs last-touch by channel (Channels)
- Rows: `channel`, sorted by `Change vs Last-touch`, descending
- Columns: `Change vs Last-touch`
- Color: `channel_group`, using the same two colors as 4.2
- Zero reference line, dollar labels at the bar ends
- Show the `p_Compare` control above the chart

Paid channels gain credit and site channels lose it. Direct and organic lose the most.

### 4.4 Credit by channel and model (Channels by model)
Highlight table: `channel` on rows, `Model` on columns (sorted by `Model Order`),
`SUM(Credited Revenue)` as color and label, with a single-hue sequential palette.
Sort channels by position-based credit. This is the reference grid for anyone who
wants the numbers.

### 4.5 Top converting paths (Pathways)
Top 10 `pathway` by `conversion_count`: a horizontal bar labeled with
`conversion_count` and `share_of_conversions`. Add a caption: "Paths that converted
at least twice; 30 paths cover 49% of purchases."

---

## 5. Dashboard assembly

1280×900, fixed size.

```
┌──────────────────────────────────────────────────────────────┐
│ Title line (the finding)                                      │
│ KPI row: Revenue · Purchases · AOV · Paid-touch % · Avg touches│
├───────────────────────────────┬──────────────────────────────┤
│ 4.2 Paid share by model       │ 4.3 Change vs last-touch      │
│     (headline)                │     [p_Compare]               │
├───────────────────────────────┼──────────────────────────────┤
│ 4.4 Credit by channel × model │ 4.5 Top converting paths      │
├───────────────────────────────┴──────────────────────────────┤
│ Caption                                                       │
└──────────────────────────────────────────────────────────────┘
```

### Rules
- Two colors carry the meaning: accent for Paid media, gray for Site visit. Use
  the same pair in 4.2 and 4.3. 4.4 uses one sequential hue.
- Sort categorical axes by value, never alphabetically. The exception is models,
  which follow `Model Order`.
- Caption: "Synthetic GA4-style events and ad impressions, seed 42, Nov 1 – Dec 15
  2024. 30-day lookback; viewable impressions count as touches. Ads have no causal
  effect in the generator, so this shows how each rule assigns credit, not
  incrementality."

---

## 6. Expected numbers

Check the finished dashboard against these numbers before publishing.

KPI row: Revenue $38,492 · Purchases 277 · AOV $138.96 · Purchases with paid touch
58.5% (162) · Avg touches 3.3.

Paid media by model: Last-touch $0 (0%), Position-based $11,600 (30.1%), Linear
$13,691 (35.6%), First-touch $20,603 (53.5%).

| Channel | First-touch | Last-touch | Linear | Position-based |
|---------|-----------:|-----------:|-------:|---------------:|
| direct | $6,591 | $14,745 | $9,578 | $10,177 |
| google_organic | $5,046 | $11,081 | $6,765 | $7,609 |
| social_facebook | $4,527 | $5,819 | $4,807 | $5,035 |
| prospecting_video | $8,694 | $0 | $3,382 | $4,118 |
| prospecting_display | $5,800 | $0 | $3,507 | $3,182 |
| prospecting_native | $5,581 | $0 | $3,616 | $3,107 |
| referral | $862 | $4,744 | $2,401 | $2,697 |
| email | $862 | $2,103 | $1,249 | $1,374 |
| retargeting_display | $466 | $0 | $1,084 | $516 |
| retargeting_video | $0 | $0 | $1,130 | $356 |
| retargeting_native | $62 | $0 | $973 | $321 |

Top paths: direct (24, 8.7%), social_facebook (16, 5.8%), google_organic (15, 5.4%).

---

## 7. Publish to Tableau Public

1. Extract before publishing.
2. Keep the workbook and dashboard name `Multi-Touch Attribution Analysis`, so
   publishing overwrites the existing viz and the README link keeps working.
3. Turn off "Show sheets as tabs".
4. In the description, link this repo and repeat the caption.
5. Export a PNG to `images/dashboard.png` and embed it at the top of the README.
