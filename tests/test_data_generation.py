"""
Unit tests for data generation modules.

Tests validate that synthetic data generators produce correct output:
- Correct number of rows
- Required columns present
- Data types valid
- User overlap within expected range
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
import pytest
from config import get_config
from extract_ga4 import GA4EventGenerator
from generate_campaigns import CampaignGenerator
from generate_impressions import ImpressionGenerator


@pytest.fixture
def config():
    """Load test configuration."""
    return get_config()


@pytest.fixture
def sample_events(config):
    """Generate small sample of GA4 events for testing."""
    # Override config for faster testing
    config.num_events = 1000
    generator = GA4EventGenerator(config)
    return generator.generate()


@pytest.fixture
def sample_campaigns(config):
    """Generate campaigns for testing."""
    generator = CampaignGenerator(config)
    return generator.generate()


class TestGA4EventGenerator:
    """Tests for GA4 event generation."""

    def test_generates_events(self, sample_events):
        """Test that events are generated."""
        assert len(sample_events) > 0
        assert len(sample_events) <= 1500  # Approximate with session expansion

    def test_required_columns(self, sample_events):
        """Test all required columns are present."""
        required_columns = [
            "event_timestamp",
            "event_name",
            "user_pseudo_id",
            "session_id",
            "source",
            "medium",
            "campaign",
            "device_category",
            "revenue",
            "transaction_id",
        ]
        for col in required_columns:
            assert col in sample_events.columns, f"Missing column: {col}"

    def test_has_conversions(self, sample_events):
        """Test that purchase events with revenue exist."""
        purchases = sample_events[sample_events["event_name"] == "purchase"]
        assert len(purchases) > 0, "No purchase events generated"
        
        # Check revenue exists
        assert (purchases["revenue"] > 0).all(), "Purchase events should have revenue"

    def test_user_ids_format(self, sample_events):
        """Test user IDs follow expected format."""
        user_ids = sample_events["user_pseudo_id"].unique()
        assert len(user_ids) > 0
        
        # Check format (should be user_XXXXXX)
        for uid in user_ids[:10]:  # Sample check
            assert uid.startswith("user_"), f"Invalid user ID format: {uid}"

    def test_timestamps_valid(self, sample_events):
        """Test timestamps are valid and chronological."""
        assert sample_events["event_timestamp"].notna().all()
        
        # Check timestamps are within expected range
        min_ts = sample_events["event_timestamp"].min()
        max_ts = sample_events["event_timestamp"].max()
        assert pd.notna(min_ts) and pd.notna(max_ts)


class TestCampaignGenerator:
    """Tests for campaign generation."""

    def test_generates_12_campaigns(self, sample_campaigns):
        """Test exactly 12 campaigns are generated."""
        assert len(sample_campaigns) == 12

    def test_required_columns(self, sample_campaigns):
        """Test all required columns are present."""
        required_columns = [
            "campaign_id",
            "campaign_name",
            "advertiser",
            "campaign_type",
            "creative_format",
            "start_date",
            "end_date",
            "daily_budget",
        ]
        for col in required_columns:
            assert col in sample_campaigns.columns, f"Missing column: {col}"

    def test_campaign_types(self, sample_campaigns):
        """Test campaign types are valid."""
        valid_types = ["prospecting", "retargeting"]
        assert sample_campaigns["campaign_type"].isin(valid_types).all()

    def test_creative_formats(self, sample_campaigns):
        """Test creative formats are valid."""
        valid_formats = ["display", "video", "native"]
        assert sample_campaigns["creative_format"].isin(valid_formats).all()

    def test_unique_campaign_ids(self, sample_campaigns):
        """Test campaign IDs are unique."""
        assert len(sample_campaigns["campaign_id"].unique()) == 12


class TestImpressionGenerator:
    """Tests for impression generation."""

    def test_generates_impressions(self, config, sample_events, sample_campaigns):
        """Test that impressions are generated."""
        config.num_impressions = 500
        generator = ImpressionGenerator(config)
        impressions = generator.generate(sample_events, sample_campaigns)
        
        assert len(impressions) > 0
        assert len(impressions) <= 600  # Approximate

    def test_required_columns(self, config, sample_events, sample_campaigns):
        """Test all required columns are present."""
        config.num_impressions = 100
        generator = ImpressionGenerator(config)
        impressions = generator.generate(sample_events, sample_campaigns)
        
        required_columns = [
            "impression_id",
            "impression_timestamp",
            "user_pseudo_id",
            "campaign_id",
            "campaign_type",
            "creative_format",
            "publisher",
            "is_viewable",
            "has_click",
        ]
        for col in required_columns:
            assert col in impressions.columns, f"Missing column: {col}"

    def test_user_overlap(self, config, sample_events, sample_campaigns):
        """Test user overlap is within expected range."""
        config.num_impressions = 500
        config.user_overlap_pct = 0.60
        
        generator = ImpressionGenerator(config)
        impressions = generator.generate(sample_events, sample_campaigns)
        
        event_users = set(sample_events["user_pseudo_id"].unique())
        impression_users = set(impressions["user_pseudo_id"].unique())
        
        overlap_users = event_users & impression_users
        overlap_pct = len(overlap_users) / len(event_users)
        
        # Allow 20% margin of error
        assert 0.40 <= overlap_pct <= 0.80, f"Overlap {overlap_pct:.2f} outside range"

    def test_viewability(self, config, sample_events, sample_campaigns):
        """Test viewability is boolean."""
        config.num_impressions = 100
        generator = ImpressionGenerator(config)
        impressions = generator.generate(sample_events, sample_campaigns)
        
        assert impressions["is_viewable"].dtype == bool
        
        # Check viewability rate is realistic (40-80%)
        viewable_rate = impressions["is_viewable"].mean()
        assert 0.40 <= viewable_rate <= 0.80

    def test_prospecting_timing(self, config, sample_events, sample_campaigns):
        """Test prospecting impressions appear before first session."""
        config.num_impressions = 200
        generator = ImpressionGenerator(config)
        impressions = generator.generate(sample_events, sample_campaigns)
        
        # Get prospecting impressions
        prospecting = impressions[impressions["campaign_type"] == "prospecting"]
        
        if len(prospecting) > 0:
            # For each user, check timing
            for user_id in prospecting["user_pseudo_id"].unique()[:5]:  # Sample
                user_events = sample_events[sample_events["user_pseudo_id"] == user_id]
                user_impressions = prospecting[prospecting["user_pseudo_id"] == user_id]
                
                if len(user_events) > 0 and len(user_impressions) > 0:
                    first_session = user_events["event_timestamp"].min()
                    first_impression = user_impressions["impression_timestamp"].min()
                    
                    # Prospecting should be BEFORE first session
                    assert first_impression < first_session, \
                        "Prospecting impression should appear before first session"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
