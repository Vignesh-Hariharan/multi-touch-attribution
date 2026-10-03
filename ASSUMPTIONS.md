# Assumptions

Everything below is a parameter of the generator, chosen to look like a mid-size
B2C store running programmatic campaigns. None of it is fitted to real data. The
constants live at the top of `src/generate_ga4.py` and `src/generate_impressions.py`
and in `src/config.py`.

## Site traffic (`generate_ga4.py`)

- **Window:** 2024-11-01 to 2024-12-15. Sessions start between 08:00 and 21:59 on a
  uniformly random day. No weekly pattern and no Black Friday spike.
- **Users:** 6,000. `user_pseudo_id` is a browser cookie in GA4, so each user keeps
  one device: mobile 60%, desktop 35%, tablet 5%.
- **Sessions per user:** 1 to 5, weighted 50/25/15/7/3%. A user's sessions are at
  least an hour apart, so they never overlap.
- **Channel per session:** direct 40%, organic search 30%, social 15%, referral 10%,
  email 5%, drawn independently for each session.
- **In-session events:** `session_start`, then 1 to 5 page views and an optional
  scroll. The funnel is nested: add to cart 15% of sessions, checkout 50% of carts,
  purchase 35% of checkouts. That's about 2.6% of sessions in expectation; this run
  converts 2.43%.
- **Order value:** lognormal with a $110 median, clipped to $15 to $800. This run's
  mean is $138.96.

## Ad impressions (`generate_impressions.py`)

- **Reach:** a random 60% of site users can be matched by the ad platform. Nobody
  outside the site's users appears in the impression log.
- **Prospecting:** 1 to 5 impressions per reached user in the 14 days before their
  first visit. Nothing serves before the flight starts on Nov 1, so users who first
  visit in the opening days get a shorter prospecting window, or none.
- **Retargeting:** 1 to 4 impressions from an hour after the first visit until the
  first purchase or 14 days after the visit, whichever comes first.
- **Viewability:** set per publisher, 58% to 75%, about 68% overall. Only viewable
  impressions become touchpoints. Under the MRC standard an impression counts as
  viewable when half its pixels are on screen for one continuous second, or two
  seconds for video.
- **Clicks:** viewable impressions only. Rates are 0.10% for prospecting display,
  0.28% native and 1.40% video, doubled for retargeting. Clicks are recorded but
  don't create sessions.

## Attribution (`dbt/attributions`)

- 30-day lookback (`attribution_window_days`). A touch has to be strictly earlier
  than the purchase.
- A touchpoint is a session (timestamped at its `session_start`) or a viewable
  impression. Touches at the same second are ordered by `touchpoint_id`.
- Position-based is 40/40/20. One touch takes 100%; two touches split 50/50.
- Each purchase is attributed separately. Four users bought twice, so a touch can
  sit in the path of both of their purchases.

## Limitations

1. **Ads don't cause purchases here.** Purchase probability doesn't depend on
   exposure. The models only show how each rule splits credit; they say nothing
   about incrementality.
2. **Last-touch can't credit paid media.** Every purchase happens in a session, and
   impressions never land between a session's start and its checkout, so the last
   touch is always a site visit. In real logs an impression can land mid-session
   (say, in another tab), and that would give paid media some last-touch credit.
3. **No paid-click sessions.** In GA4 a clicked ad shows up as a `cpc` session.
   Here clicks never generate traffic, so paid media only ever appears as
   view-through.
4. **One device per user, no cross-device stitching**, and no consent loss beyond
   the 60% reach.
5. **No seasonality.** Traffic is flat across a window that includes Black Friday
   and Cyber Monday.
