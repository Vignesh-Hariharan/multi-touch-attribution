"""
Synthetic programmatic impressions for the site users the ad platform can reach.

Prospecting serves in the 14 days before a user's first site visit. Retargeting
serves after the first visit and stops at the user's first purchase or 14 days
after the visit, whichever is sooner. Every impression falls inside its
campaign's flight dates. Attribution later keeps only viewable impressions, so
these act as view-through touches; clicks are recorded but do not create sessions.
"""

import argparse
from datetime import timedelta

import numpy as np
import pandas as pd

from config import get_config

PROSPECTING_LOOKBACK = timedelta(days=14)
RETARGETING_WINDOW = timedelta(days=14)
RETARGETING_DELAY = timedelta(hours=1)
PROSPECTING_IMPRESSIONS = (1, 6)
RETARGETING_IMPRESSIONS = (1, 5)

IMPRESSION_COLUMNS = [
    "impression_id",
    "impression_timestamp",
    "user_pseudo_id",
    "campaign_id",
    "campaign_name",
    "campaign_type",
    "creative_format",
    "publisher",
    "is_viewable",
    "has_click",
    "device_category",
]


class ImpressionGenerator:
    def __init__(self, config):
        self.config = config
        self.rng = np.random.default_rng([config.random_seed, 2])

    @staticmethod
    def _user_activity(events: pd.DataFrame) -> pd.DataFrame:
        events = events.assign(event_timestamp=pd.to_datetime(events["event_timestamp"]))
        first_visit = (
            events[events["event_name"] == "session_start"].groupby("user_pseudo_id")["event_timestamp"].min()
        )
        first_purchase = events[events["event_name"] == "purchase"].groupby("user_pseudo_id")["event_timestamp"].min()
        device = events.groupby("user_pseudo_id")["device_category"].first()
        return (
            pd.DataFrame({"first_visit": first_visit, "device_category": device})
            .join(first_purchase.rename("first_purchase"))
            .sort_index()
        )

    def _draw(self, campaigns: pd.DataFrame, earliest, latest, count_range):
        """Draw impressions uniformly in [earliest, latest), clipped to each campaign's flight."""
        draws = []
        for _ in range(int(self.rng.integers(*count_range))):
            campaign = campaigns.iloc[int(self.rng.integers(len(campaigns)))]
            lo = max(earliest, campaign["flight_start"])
            hi = min(latest, campaign["flight_end"])
            if hi <= lo:
                continue
            offset = (hi - lo).total_seconds() * self.rng.random()
            draws.append((lo + timedelta(seconds=int(offset)), campaign))
        return draws

    def generate(self, events: pd.DataFrame, campaigns: pd.DataFrame) -> pd.DataFrame:
        campaigns = campaigns.assign(
            flight_start=pd.to_datetime(campaigns["start_date"]),
            flight_end=pd.to_datetime(campaigns["end_date"]) + timedelta(days=1),
        )
        by_type = {t: c.reset_index(drop=True) for t, c in campaigns.groupby("campaign_type")}
        publishers = list(self.config.publisher_viewability)

        users = self._user_activity(events)
        n_reached = round(len(users) * self.config.ad_reach_pct)
        reached = sorted(self.rng.choice(users.index.to_numpy(), size=n_reached, replace=False))

        rows = []
        for user_id in reached:
            user = users.loc[user_id]
            first_visit = user["first_visit"]

            served = self._draw(
                by_type["prospecting"],
                first_visit - PROSPECTING_LOOKBACK,
                first_visit,
                PROSPECTING_IMPRESSIONS,
            )
            retarget_end = first_visit + RETARGETING_WINDOW
            if pd.notna(user["first_purchase"]):
                retarget_end = min(retarget_end, user["first_purchase"])
            served += self._draw(
                by_type["retargeting"],
                first_visit + RETARGETING_DELAY,
                retarget_end,
                RETARGETING_IMPRESSIONS,
            )

            for ts, campaign in served:
                publisher = publishers[int(self.rng.integers(len(publishers)))]
                is_viewable = bool(self.rng.random() < self.config.publisher_viewability[publisher])
                ctr = self.config.ctr[campaign["campaign_type"]][campaign["creative_format"]]
                has_click = bool(is_viewable and self.rng.random() < ctr)
                rows.append(
                    {
                        "impression_timestamp": ts,
                        "user_pseudo_id": user_id,
                        "campaign_id": campaign["campaign_id"],
                        "campaign_name": campaign["campaign_name"],
                        "campaign_type": campaign["campaign_type"],
                        "creative_format": campaign["creative_format"],
                        "publisher": publisher,
                        "is_viewable": is_viewable,
                        "has_click": has_click,
                        "device_category": user["device_category"],
                    }
                )

        df = pd.DataFrame(rows).sort_values(
            ["impression_timestamp", "user_pseudo_id", "campaign_id"], kind="mergesort", ignore_index=True
        )
        df.insert(0, "impression_id", [f"imp_{i:07d}" for i in range(1, len(df) + 1)])
        df = df[IMPRESSION_COLUMNS]

        print(
            f"Impressions: {len(df):,} for {df['user_pseudo_id'].nunique():,} users "
            f"({df['campaign_type'].value_counts().to_dict()}), "
            f"{df['is_viewable'].mean():.1%} viewable, {int(df['has_click'].sum())} clicks"
        )
        return df


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic ad impressions")
    parser.add_argument("--output", type=str, help="Output CSV path")
    args = parser.parse_args()

    config = get_config()
    events = pd.read_csv(config.data_dir / "ga4_events.csv")
    campaigns = pd.read_csv(config.data_dir / "campaigns.csv")

    impressions = ImpressionGenerator(config).generate(events, campaigns)

    output_path = args.output or config.data_dir / "impressions.csv"
    impressions.to_csv(output_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
