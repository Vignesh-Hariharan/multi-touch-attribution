"""
Impression Generator

Generates synthetic programmatic ad impression data with realistic timing patterns.
KEY: Prospecting ads appear EARLY (before first session), retargeting ads appear LATE.
This creates the natural condition where position-based attribution reveals prospecting's value.
"""

import argparse
import uuid
from datetime import timedelta
from pathlib import Path
from typing import List, Dict, Set

import numpy as np
import pandas as pd

from config import get_config


class ImpressionGenerator:
    """Generate synthetic ad impression data with realistic user journey timing."""

    def __init__(self, config):
        self.config = config
        np.random.seed(config.random_seed)

    def generate(self, events_df: pd.DataFrame, campaigns_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate ad impressions with realistic timing patterns.
        
        Strategy:
        - Select target users (USER_OVERLAP_PCT of total users)
        - For new users (1 session): Show prospecting ads BEFORE first session
        - For returning users (2+ sessions): Show retargeting ads AFTER first session
        - This naturally creates early vs late touchpoint patterns
        
        Args:
            events_df: GA4 events dataframe
            campaigns_df: Campaigns dataframe
            
        Returns:
            DataFrame with ad impressions
        """
        print(f" Generating {self.config.num_impressions:,} ad impressions...")
        
        # Get user first session times
        user_sessions = self._analyze_user_sessions(events_df)
        print(f"   Analyzed {len(user_sessions):,} users")
        
        # Select users to target (overlap percentage)
        target_users = self._select_target_users(user_sessions)
        print(f"   Selected {len(target_users):,} users to target ({self.config.user_overlap_pct:.0%} overlap)")
        
        # Generate impressions
        impressions = self._generate_user_impressions(target_users, user_sessions, campaigns_df)
        
        impressions_df = pd.DataFrame(impressions)
        impressions_df = impressions_df.sort_values("impression_timestamp").reset_index(drop=True)
        
        self._print_stats(impressions_df)
        
        return impressions_df

    def _analyze_user_sessions(self, events_df: pd.DataFrame) -> Dict[str, Dict]:
        """Analyze user session patterns."""
        user_data = {}
        
        for user_id in events_df["user_pseudo_id"].unique():
            user_events = events_df[events_df["user_pseudo_id"] == user_id]
            
            # Get session starts only
            session_starts = user_events[user_events["event_name"] == "session_start"]
            
            user_data[user_id] = {
                "first_session": user_events["event_timestamp"].min(),
                "last_session": user_events["event_timestamp"].max(),
                "session_count": len(session_starts),
                "has_purchased": (user_events["event_name"] == "purchase").any(),
            }
        
        return user_data

    def _select_target_users(self, user_sessions: Dict) -> Set[str]:
        """Select users to show ads to based on overlap percentage."""
        all_users = list(user_sessions.keys())
        num_target = int(len(all_users) * self.config.user_overlap_pct)
        target_users = set(np.random.choice(all_users, size=num_target, replace=False))
        return target_users

    def _generate_user_impressions(
        self, 
        target_users: Set[str], 
        user_sessions: Dict, 
        campaigns_df: pd.DataFrame
    ) -> List[Dict]:
        """Generate impressions for target users with realistic timing."""
        impressions = []
        impressions_per_user = self.config.num_impressions // len(target_users)
        
        for user_id in target_users:
            user_info = user_sessions[user_id]
            
            # Determine campaign targeting
            if user_info["session_count"] == 1:
                # New user → Prospecting campaigns
                campaign_type = "prospecting"
                eligible_campaigns = campaigns_df[campaigns_df["campaign_type"] == "prospecting"]
                num_imps = np.random.randint(3, 8)  # More prospecting impressions
                
            elif user_info["session_count"] >= 2 and not user_info["has_purchased"]:
                # Returning non-purchaser → Retargeting campaigns
                campaign_type = "retargeting"
                eligible_campaigns = campaigns_df[campaigns_df["campaign_type"] == "retargeting"]
                num_imps = np.random.randint(2, 5)
                
            else:
                # Skip purchasers (no post-purchase ads for simplicity)
                continue
            
            if len(eligible_campaigns) == 0:
                continue
            
            # Generate impressions for this user
            for _ in range(num_imps):
                campaign = eligible_campaigns.sample(1).iloc[0]
                
                # CRITICAL: Timing logic that creates the attribution insight
                if campaign_type == "prospecting":
                    # Prospecting: BEFORE first session (awareness phase)
                    # This makes them appear at POSITION 1 in attribution
                    days_before = np.random.uniform(1, 14)
                    impression_ts = user_info["first_session"] - timedelta(days=days_before)
                else:
                    # Retargeting: AFTER first session (consideration phase)  
                    # This makes them appear at LATER positions
                    days_after = np.random.uniform(1, 7)
                    impression_ts = user_info["first_session"] + timedelta(days=days_after)
                
                # Add random hour/minute
                impression_ts = impression_ts.replace(
                    hour=np.random.randint(0, 24),
                    minute=np.random.randint(0, 60),
                    second=np.random.randint(0, 60)
                )
                
                # Select publisher
                publisher = np.random.choice(list(self.config.publishers.keys()))
                publisher_config = self.config.publishers[publisher]
                
                # Viewability (binary based on publisher rate)
                is_viewable = np.random.random() < publisher_config["viewability"]
                
                # Click (only if viewable)
                has_click = False
                if is_viewable:
                    ctr = self.config.campaign_ctr[campaign_type][campaign["creative_format"]]
                    has_click = np.random.random() < ctr
                
                # Device
                device = np.random.choice(["mobile", "desktop", "tablet"], p=[0.60, 0.35, 0.05])
                
                impressions.append({
                    "impression_id": str(uuid.uuid4()),
                    "impression_timestamp": impression_ts,
                    "user_pseudo_id": user_id,
                    "campaign_id": campaign["campaign_id"],
                    "campaign_name": campaign["campaign_name"],
                    "campaign_type": campaign_type,
                    "creative_format": campaign["creative_format"],
                    "publisher": publisher,
                    "is_viewable": is_viewable,
                    "has_click": has_click,
                    "device_category": device,
                })
        
        return impressions

    def _print_stats(self, impressions_df: pd.DataFrame):
        """Print impression statistics."""
        total = len(impressions_df)
        print(f"   Generated {total:,} impressions")
        
        print(f"\n  Campaign Type Distribution:")
        for ctype in ["prospecting", "retargeting"]:
            count = len(impressions_df[impressions_df["campaign_type"] == ctype])
            pct = count / total * 100
            print(f"    - {ctype.capitalize()}: {count:,} ({pct:.1f}%)")
        
        print(f"\n  Creative Format Distribution:")
        for fmt, count in impressions_df["creative_format"].value_counts().items():
            pct = count / total * 100
            print(f"    - {fmt.capitalize()}: {count:,} ({pct:.1f}%)")
        
        viewable = impressions_df["is_viewable"].sum()
        viewable_rate = viewable / total * 100
        print(f"\n  Viewability: {viewable:,} ({viewable_rate:.1f}%)")
        
        clicks = impressions_df["has_click"].sum()
        ctr = clicks / viewable * 100 if viewable > 0 else 0
        print(f"  Clicks: {clicks:,} (CTR: {ctr:.3f}%)")
        
        unique_users = impressions_df["user_pseudo_id"].nunique()
        print(f"  Unique Users: {unique_users:,}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Generate synthetic ad impression data")
    parser.add_argument("--output", type=str, help="Output CSV path")
    args = parser.parse_args()

    # Load config
    config = get_config()
    
    # Load dependencies
    events_df = pd.read_csv(config.data_dir / "ga4_events.csv", parse_dates=["event_timestamp"])
    campaigns_df = pd.read_csv(config.data_dir / "campaigns.csv")
    
    # Generate impressions
    generator = ImpressionGenerator(config)
    impressions_df = generator.generate(events_df, campaigns_df)
    
    # Save to CSV
    output_path = args.output or config.data_dir / "impressions.csv"
    impressions_df.to_csv(output_path, index=False)
    print(f"\n Saved {len(impressions_df):,} impressions to {output_path}")
    
    # Display sample
    print("\n Sample impressions:")
    print(impressions_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
