"""
Synthetic GA4-style event export: users, sessions, and ordered in-session events.

user_pseudo_id is a browser cookie in GA4, so device is fixed per user. Every
session opens with session_start, and the purchase funnel is nested
(add_to_cart -> begin_checkout -> purchase), so a purchase always follows a
session_start, a cart add and a checkout in the same session.
"""

import argparse
from datetime import timedelta

import numpy as np
import pandas as pd

from config import get_config

SESSIONS_PER_USER = ([1, 2, 3, 4, 5], [0.50, 0.25, 0.15, 0.07, 0.03])
MIN_SESSION_GAP = timedelta(hours=1)
MAX_SESSION_LENGTH = timedelta(minutes=40)
DEVICE_MIX = {"mobile": 0.60, "desktop": 0.35, "tablet": 0.05}

P_ADD_TO_CART = 0.15
P_CHECKOUT_GIVEN_CART = 0.50
P_PURCHASE_GIVEN_CHECKOUT = 0.35

ORDER_VALUE_MEDIAN = 110.0
ORDER_VALUE_SIGMA = 0.6
ORDER_VALUE_BOUNDS = (15.0, 800.0)

REFERRAL_DOMAINS = ["reddit.com", "slickdeals.net", "medium.com", "trustpilot.com"]

BASE_URL = "https://example-shop.com"
PAGES = ["/", "/products", "/categories", "/products/item-1", "/products/item-2", "/blog"]

EVENT_COLUMNS = [
    "event_timestamp",
    "event_date",
    "event_name",
    "user_pseudo_id",
    "session_id",
    "source",
    "medium",
    "campaign",
    "page_location",
    "device_category",
    "country",
    "revenue",
    "transaction_id",
]


class GA4EventGenerator:
    def __init__(self, config):
        self.config = config
        self.rng = np.random.default_rng([config.random_seed, 1])

    def generate_users(self) -> pd.DataFrame:
        n = self.config.num_users
        devices = self.rng.choice(list(DEVICE_MIX), size=n, p=list(DEVICE_MIX.values()))
        return pd.DataFrame(
            {
                "user_pseudo_id": [f"user_{i:06d}" for i in range(1, n + 1)],
                "device_category": devices,
            }
        )

    def generate_sessions(self, users: pd.DataFrame) -> pd.DataFrame:
        counts, probs = SESSIONS_PER_USER
        channels = list(self.config.channel_mix)
        channel_p = list(self.config.channel_mix.values())
        rows = []

        for user in users.itertuples(index=False):
            n_sessions = self.rng.choice(counts, p=probs)
            starts = sorted(
                self.config.start_datetime
                + timedelta(
                    days=int(self.rng.integers(0, self.config.date_range_days)),
                    hours=int(self.rng.integers(8, 22)),
                    minutes=int(self.rng.integers(0, 60)),
                    seconds=int(self.rng.integers(0, 60)),
                )
                for _ in range(n_sessions)
            )
            for i in range(1, len(starts)):
                starts[i] = max(starts[i], starts[i - 1] + MIN_SESSION_GAP)
            latest_start = self.config.end_datetime - MAX_SESSION_LENGTH
            for start in (s for s in starts if s <= latest_start):
                rows.append(
                    {
                        "user_pseudo_id": user.user_pseudo_id,
                        "device_category": user.device_category,
                        "session_start": start,
                        "channel": self.rng.choice(channels, p=channel_p),
                    }
                )

        sessions = pd.DataFrame(rows).sort_values(["session_start", "user_pseudo_id"], ignore_index=True)
        sessions["session_id"] = [f"session_{i:06d}" for i in range(1, len(sessions) + 1)]
        return sessions

    def _source_medium(self, channel: str):
        if channel == "direct":
            return "(direct)", "(none)", "(not set)"
        if channel == "organic_search":
            return "google", "organic", "(not set)"
        if channel == "social":
            return "facebook", "social", "(not set)"
        if channel == "referral":
            return self.rng.choice(REFERRAL_DOMAINS), "referral", "(not set)"
        if channel == "email":
            return "newsletter", "email", "monthly_newsletter"
        raise ValueError(f"Unknown channel: {channel}")

    def _order_value(self) -> float:
        value = self.rng.lognormal(np.log(ORDER_VALUE_MEDIAN), ORDER_VALUE_SIGMA)
        return round(float(np.clip(value, *ORDER_VALUE_BOUNDS)), 2)

    def generate_events(self, sessions: pd.DataFrame) -> pd.DataFrame:
        events = []
        txn_counter = 0

        for s in sessions.itertuples(index=False):
            source, medium, campaign = self._source_medium(s.channel)
            ts = s.session_start
            session_events = [("session_start", ts, "/")]

            for _ in range(int(self.rng.integers(1, 6))):
                ts += timedelta(seconds=int(self.rng.integers(10, 180)))
                session_events.append(("page_view", ts, self.rng.choice(PAGES)))
            if self.rng.random() < 0.5:
                ts += timedelta(seconds=int(self.rng.integers(5, 60)))
                session_events.append(("scroll", ts, session_events[-1][2]))

            purchase = None
            if self.rng.random() < P_ADD_TO_CART:
                ts += timedelta(seconds=int(self.rng.integers(20, 240)))
                session_events.append(("add_to_cart", ts, "/products/item-1"))
                if self.rng.random() < P_CHECKOUT_GIVEN_CART:
                    ts += timedelta(seconds=int(self.rng.integers(30, 300)))
                    session_events.append(("begin_checkout", ts, "/checkout"))
                    if self.rng.random() < P_PURCHASE_GIVEN_CHECKOUT:
                        ts += timedelta(seconds=int(self.rng.integers(60, 600)))
                        txn_counter += 1
                        purchase = (f"txn_{txn_counter:06d}", self._order_value())
                        session_events.append(("purchase", ts, "/checkout/confirmation"))

            for name, event_ts, page in session_events:
                is_purchase = name == "purchase"
                events.append(
                    {
                        "event_timestamp": event_ts,
                        "event_date": event_ts.strftime("%Y%m%d"),
                        "event_name": name,
                        "user_pseudo_id": s.user_pseudo_id,
                        "session_id": s.session_id,
                        "source": source,
                        "medium": medium,
                        "campaign": campaign,
                        "page_location": f"{BASE_URL}{page}",
                        "device_category": s.device_category,
                        "country": "United States",
                        "revenue": purchase[1] if is_purchase else 0.0,
                        "transaction_id": purchase[0] if is_purchase else None,
                    }
                )

        df = pd.DataFrame(events, columns=EVENT_COLUMNS)
        return df.sort_values(["event_timestamp", "session_id"], kind="mergesort", ignore_index=True)

    def generate(self) -> pd.DataFrame:
        users = self.generate_users()
        sessions = self.generate_sessions(users)
        events = self.generate_events(sessions)

        purchases = events[events["event_name"] == "purchase"]
        print(
            f"GA4: {len(users):,} users, {len(sessions):,} sessions, {len(events):,} events, "
            f"{len(purchases):,} purchases (${purchases['revenue'].sum():,.2f})"
        )
        return events


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic GA4 events")
    parser.add_argument("--output", type=str, help="Output CSV path")
    args = parser.parse_args()

    config = get_config()
    events = GA4EventGenerator(config).generate()

    config.data_dir.mkdir(exist_ok=True)
    output_path = args.output or config.data_dir / "ga4_events.csv"
    events.to_csv(output_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
