"""
GA4 Event Data Extractor/Generator

Generates synthetic GA4 e-commerce event data when real GA4 API access is unavailable.
Creates realistic user journeys with sessions, page views, and purchase events.
"""

import argparse
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

import numpy as np
import pandas as pd
from faker import Faker

from config import get_config


class GA4EventGenerator:
    """Generate synthetic GA4 event data with realistic patterns."""

    def __init__(self, config):
        self.config = config
        np.random.seed(config.random_seed)
        self.fake = Faker()
        Faker.seed(config.random_seed)

    def generate_users(self) -> List[str]:
        """Generate user pseudo IDs."""
        num_users = int(self.config.num_events / 6)  # ~6 events per user on average
        return [f"user_{str(i).zfill(6)}" for i in range(1, num_users + 1)]

    def generate_sessions(self, users: List[str]) -> pd.DataFrame:
        """Generate session data for users."""
        sessions = []
        session_id = 1

        for user_id in users:
            # Number of sessions per user (1-5, weighted toward 1-2)
            num_sessions = np.random.choice([1, 2, 3, 4, 5], p=[0.50, 0.25, 0.15, 0.07, 0.03])

            for _ in range(num_sessions):
                # Random timestamp within date range
                days_offset = np.random.randint(0, self.config.date_range_days)
                hour = np.random.randint(8, 22)  # Business hours weighted
                minute = np.random.randint(0, 60)
                
                session_start = self.config.start_datetime + timedelta(
                    days=days_offset, hours=hour, minutes=minute
                )

                # Assign channel (source/medium)
                channel = np.random.choice(
                    list(self.config.channel_distribution.keys()),
                    p=list(self.config.channel_distribution.values())
                )

                sessions.append({
                    "user_pseudo_id": user_id,
                    "session_id": f"session_{session_id}",
                    "session_start": session_start,
                    "channel": channel,
                })
                session_id += 1

        return pd.DataFrame(sessions)

    def generate_events(self, sessions: pd.DataFrame) -> pd.DataFrame:
        """Generate events from sessions."""
        events = []
        event_types = {
            "session_start": 1.0,
            "page_view": 0.8,
            "scroll": 0.5,
            "add_to_cart": 0.15,
            "begin_checkout": 0.08,
            "purchase": 0.025,  # ~2.5% conversion rate
        }

        for _, session in sessions.iterrows():
            session_duration_minutes = np.random.randint(1, 30)
            
            for event_type, probability in event_types.items():
                if np.random.random() < probability:
                    # Event timestamp within session duration
                    minutes_offset = np.random.randint(0, session_duration_minutes)
                    event_timestamp = session["session_start"] + timedelta(minutes=minutes_offset)

                    # Parse channel to source/medium
                    if session["channel"] == "direct":
                        source, medium = "direct", "(none)"
                    elif session["channel"] == "organic_search":
                        source, medium = "google", "organic"
                    elif session["channel"] == "social":
                        source, medium = "facebook", "social"
                    elif session["channel"] == "referral":
                        source, medium = self.fake.domain_name(), "referral"
                    elif session["channel"] == "email":
                        source, medium = "newsletter", "email"
                    else:
                        source, medium = "unknown", "unknown"

                    event_data = {
                        "event_timestamp": event_timestamp,
                        "event_date": event_timestamp.strftime("%Y%m%d"),
                        "event_name": event_type,
                        "user_pseudo_id": session["user_pseudo_id"],
                        "session_id": session["session_id"],
                        "source": source,
                        "medium": medium,
                        "campaign": "(not set)" if session["channel"] != "email" else "monthly_newsletter",
                        "page_location": self._generate_page_url(event_type),
                        "device_category": np.random.choice(
                            ["mobile", "desktop", "tablet"], p=[0.60, 0.35, 0.05]
                        ),
                        "country": "United States",
                        "revenue": 0.0,
                        "transaction_id": None,
                    }

                    # Add revenue for purchase events
                    if event_type == "purchase":
                        event_data["revenue"] = round(np.random.uniform(25, 500), 2)
                        event_data["transaction_id"] = f"txn_{uuid.uuid4().hex[:12]}"

                    events.append(event_data)

        return pd.DataFrame(events).sort_values("event_timestamp").reset_index(drop=True)

    def _generate_page_url(self, event_type: str) -> str:
        """Generate realistic page URLs based on event type."""
        base_url = "https://example-shop.com"
        
        pages = {
            "session_start": ["/", "/home"],
            "page_view": ["/products", "/categories", "/about", "/contact"],
            "scroll": ["/products", "/blog"],
            "add_to_cart": ["/products/item-1", "/products/item-2", "/products/item-3"],
            "begin_checkout": ["/checkout"],
            "purchase": ["/checkout/confirmation"],
        }
        
        page = np.random.choice(pages.get(event_type, ["/"]))
        return f"{base_url}{page}"

    def generate(self) -> pd.DataFrame:
        """Generate complete GA4 event dataset."""
        print(f" Generating {self.config.num_events:,} GA4 events...")
        
        users = self.generate_users()
        print(f"   Generated {len(users):,} users")
        
        sessions = self.generate_sessions(users)
        print(f"   Generated {len(sessions):,} sessions")
        
        events = self.generate_events(sessions)
        print(f"   Generated {len(events):,} events")
        
        purchases = events[events["event_name"] == "purchase"]
        total_revenue = purchases["revenue"].sum()
        print(f"   Generated {len(purchases):,} purchases (${total_revenue:,.2f} revenue)")
        
        return events


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Generate synthetic GA4 event data")
    parser.add_argument("--output", type=str, help="Output CSV path")
    args = parser.parse_args()

    # Load config
    config = get_config()
    
    # Generate events
    generator = GA4EventGenerator(config)
    events_df = generator.generate()
    
    # Save to CSV
    output_path = args.output or config.data_dir / "ga4_events.csv"
    events_df.to_csv(output_path, index=False)
    print(f"\n Saved {len(events_df):,} events to {output_path}")
    
    # Display sample
    print("\n Sample data:")
    print(events_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
