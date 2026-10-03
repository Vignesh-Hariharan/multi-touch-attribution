import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from config import Config  # noqa: E402
from generate_campaigns import CampaignGenerator  # noqa: E402
from generate_ga4 import GA4EventGenerator  # noqa: E402
from generate_impressions import ImpressionGenerator  # noqa: E402

NUM_USERS = 1500


def make_config():
    return Config(_env_file=None, num_users=NUM_USERS)


@pytest.fixture(scope="module")
def config():
    return make_config()


@pytest.fixture(scope="module")
def events(config):
    return GA4EventGenerator(config).generate()


@pytest.fixture(scope="module")
def campaigns(config):
    return CampaignGenerator(config).generate()


@pytest.fixture(scope="module")
def impressions(config, events, campaigns):
    return ImpressionGenerator(config).generate(events, campaigns)


@pytest.fixture(scope="module")
def user_activity(events):
    first_visit = events[events.event_name == "session_start"].groupby("user_pseudo_id").event_timestamp.min()
    first_purchase = events[events.event_name == "purchase"].groupby("user_pseudo_id").event_timestamp.min()
    return pd.DataFrame({"first_visit": first_visit}).join(first_purchase.rename("first_purchase"))


def digest(df: pd.DataFrame) -> str:
    return hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()


class TestReproducibility:
    def test_same_seed_same_output(self, config, events, impressions, campaigns):
        events_again = GA4EventGenerator(config).generate()
        impressions_again = ImpressionGenerator(config).generate(events_again, campaigns)
        pd.testing.assert_frame_equal(events, events_again)
        pd.testing.assert_frame_equal(impressions, impressions_again)

    def test_independent_of_python_hash_seed(self):
        script = (
            f"import sys, hashlib; sys.path.insert(0, {str(SRC)!r})\n"
            "from config import Config\n"
            "from generate_ga4 import GA4EventGenerator\n"
            "from generate_campaigns import CampaignGenerator\n"
            "from generate_impressions import ImpressionGenerator\n"
            f"c = Config(_env_file=None, num_users={NUM_USERS})\n"
            "e = GA4EventGenerator(c).generate()\n"
            "i = ImpressionGenerator(c).generate(e, CampaignGenerator(c).generate())\n"
            "print(hashlib.sha256((e.to_csv(index=False) + i.to_csv(index=False)).encode()).hexdigest())\n"
        )
        digests = set()
        for hash_seed in ("1", "2024"):
            result = subprocess.run(
                [sys.executable, "-c", script],
                env={**os.environ, "PYTHONHASHSEED": hash_seed},
                capture_output=True,
                text=True,
                check=True,
            )
            digests.add(result.stdout.strip().splitlines()[-1])
        assert len(digests) == 1

    def test_different_seed_different_output(self, events):
        other = GA4EventGenerator(Config(_env_file=None, num_users=NUM_USERS, random_seed=7)).generate()
        assert digest(other) != digest(events)


class TestEvents:
    def test_columns_match_raw_table(self, events):
        assert list(events.columns) == [
            "event_timestamp", "event_date", "event_name", "user_pseudo_id", "session_id", "source",
            "medium", "campaign", "page_location", "device_category", "country", "revenue", "transaction_id",
        ]

    def test_every_session_opens_with_session_start(self, events):
        ordered = events.sort_values(["session_id", "event_timestamp"], kind="mergesort")
        first = ordered.groupby("session_id").event_name.first()
        assert (first == "session_start").all()
        assert (events.event_name == "session_start").sum() == events.session_id.nunique()

    def test_timestamps_strictly_increase_within_session(self, events):
        gaps = events.sort_values(["session_id", "event_timestamp"]).groupby("session_id").event_timestamp.diff()
        assert (gaps.dropna() > pd.Timedelta(0)).all()

    def test_purchase_follows_cart_and_checkout_in_same_session(self, events):
        steps = events.pivot_table(
            index="session_id", columns="event_name", values="event_timestamp", aggfunc="min"
        )
        purchased = steps[steps["purchase"].notna()]
        assert len(purchased) > 0
        assert (purchased["session_start"] < purchased["add_to_cart"]).all()
        assert (purchased["add_to_cart"] < purchased["begin_checkout"]).all()
        assert (purchased["begin_checkout"] < purchased["purchase"]).all()

    def test_purchases_carry_unique_transaction_and_revenue(self, events):
        purchases = events[events.event_name == "purchase"]
        assert purchases.transaction_id.notna().all()
        assert purchases.transaction_id.is_unique
        assert (purchases.revenue > 0).all()
        others = events[events.event_name != "purchase"]
        assert others.transaction_id.isna().all()
        assert (others.revenue == 0).all()

    def test_device_fixed_per_user(self, events):
        assert (events.groupby("user_pseudo_id").device_category.nunique() == 1).all()

    def test_source_medium_fixed_per_session(self, events):
        assert (events.groupby("session_id")[["source", "medium"]].nunique() == 1).all().all()

    def test_sessions_of_one_user_do_not_overlap(self, events):
        bounds = events.groupby(["user_pseudo_id", "session_id"]).event_timestamp.agg(["min", "max"])
        bounds = bounds.reset_index().sort_values(["user_pseudo_id", "min"])
        previous_end = bounds.groupby("user_pseudo_id")["max"].shift()
        assert (bounds["min"][previous_end.notna()] > previous_end.dropna()).all()

    def test_events_inside_simulation_window(self, config, events):
        assert events.event_timestamp.min() >= config.start_datetime
        assert events.event_timestamp.max() <= config.end_datetime


class TestCampaigns:
    def test_structure(self, campaigns):
        assert len(campaigns) == 12
        assert campaigns.campaign_id.is_unique
        assert campaigns.groupby("campaign_type").size().to_dict() == {"prospecting": 6, "retargeting": 6}

    def test_flight_matches_config(self, config, campaigns):
        assert (campaigns.start_date == config.start_date).all()
        assert (campaigns.end_date == config.end_date).all()


class TestImpressions:
    def test_ids_unique_and_sequential(self, impressions):
        assert impressions.impression_id.is_unique
        assert impressions.impression_timestamp.is_monotonic_increasing

    def test_reach_matches_config(self, config, events, impressions):
        expected = round(events.user_pseudo_id.nunique() * config.ad_reach_pct)
        assert impressions.user_pseudo_id.nunique() <= expected
        assert impressions.user_pseudo_id.nunique() >= 0.95 * expected

    def test_inside_campaign_flight(self, impressions, campaigns):
        merged = impressions.merge(campaigns[["campaign_id", "start_date", "end_date"]], on="campaign_id")
        day = merged.impression_timestamp.dt.normalize()
        assert (day >= pd.to_datetime(merged.start_date)).all()
        assert (day <= pd.to_datetime(merged.end_date)).all()

    def test_prospecting_before_first_visit(self, impressions, user_activity):
        prospecting = impressions[impressions.campaign_type == "prospecting"]
        first_visit = prospecting.user_pseudo_id.map(user_activity.first_visit)
        assert len(prospecting) > 0
        assert (prospecting.impression_timestamp < first_visit).all()

    def test_retargeting_after_visit_and_before_first_purchase(self, impressions, user_activity):
        retargeting = impressions[impressions.campaign_type == "retargeting"]
        activity = user_activity.loc[retargeting.user_pseudo_id]
        assert len(retargeting) > 0
        assert (retargeting.impression_timestamp.to_numpy() > activity.first_visit.to_numpy()).all()
        bought = activity.first_purchase.notna().to_numpy()
        assert (retargeting.impression_timestamp.to_numpy()[bought] < activity.first_purchase.to_numpy()[bought]).all()

    def test_clicks_only_on_viewable(self, impressions):
        assert not (impressions.has_click & ~impressions.is_viewable).any()

    def test_device_matches_site_device(self, impressions, events):
        site_device = events.groupby("user_pseudo_id").device_category.first()
        assert (impressions.device_category == impressions.user_pseudo_id.map(site_device)).all()
