"""
Campaign Generator

Creates synthetic programmatic advertising campaign data with realistic structure.
Campaigns vary by advertiser, type (prospecting/retargeting), and format (display/video/native).
"""

import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import pandas as pd

from config import get_config


class CampaignGenerator:
    """Generate synthetic advertising campaign configurations."""

    def __init__(self, config):
        self.config = config

    def generate(self) -> pd.DataFrame:
        """
        Generate campaign data.
        
        Structure: 3 advertisers × 2 types × 2 formats = 12 campaigns
        
        Returns:
            DataFrame with campaign configurations
        """
        print(f" Generating {self.config.num_campaigns} campaigns...")
        
        campaigns = []
        campaign_id = 1

        # Advertiser configurations
        advertisers = [
            {"name": "RetailCo", "formats": ["display", "video"]},
            {"name": "SaaS_Platform", "formats": ["native", "video"]},
            {"name": "CPG_Brand", "formats": ["display", "native"]},
        ]

        campaign_types = ["prospecting", "retargeting"]

        for advertiser in advertisers:
            for campaign_type in campaign_types:
                for creative_format in advertiser["formats"]:
                    campaign_name = f"{creative_format.upper()}_{campaign_type.upper()}_{campaign_id:02d}"
                    
                    campaigns.append({
                        "campaign_id": f"camp_{campaign_id:04d}",
                        "campaign_name": campaign_name,
                        "advertiser": advertiser["name"],
                        "campaign_type": campaign_type,
                        "creative_format": creative_format,
                        "start_date": self.config.start_date,
                        "end_date": self.config.end_date,
                        "daily_budget": self._generate_budget(campaign_type, creative_format),
                    })
                    campaign_id += 1

        df = pd.DataFrame(campaigns)
        print(f"   Generated {len(df)} campaigns")
        print(f"    - Prospecting: {len(df[df['campaign_type'] == 'prospecting'])}")
        print(f"    - Retargeting: {len(df[df['campaign_type'] == 'retargeting'])}")
        print(f"    - Formats: {df['creative_format'].value_counts().to_dict()}")
        
        return df

    def _generate_budget(self, campaign_type: str, creative_format: str) -> float:
        """
        Generate realistic daily budget based on campaign characteristics.
        
        Args:
            campaign_type: prospecting or retargeting
            creative_format: display, video, or native
            
        Returns:
            Daily budget in dollars
        """
        # Base budgets by format
        base_budgets = {
            "display": 500,
            "video": 1200,
            "native": 800,
        }
        
        budget = base_budgets.get(creative_format, 500)
        
        # Prospecting campaigns typically have larger budgets (wider audience)
        if campaign_type == "prospecting":
            budget *= 1.5
            
        return round(budget, 2)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Generate synthetic campaign data")
    parser.add_argument("--output", type=str, help="Output CSV path")
    args = parser.parse_args()

    # Load config
    config = get_config()
    
    # Generate campaigns
    generator = CampaignGenerator(config)
    campaigns_df = generator.generate()
    
    # Save to CSV
    output_path = args.output or config.data_dir / "campaigns.csv"
    campaigns_df.to_csv(output_path, index=False)
    print(f"\n Saved {len(campaigns_df)} campaigns to {output_path}")
    
    # Display all campaigns
    print("\n Campaign Summary:")
    print(campaigns_df.to_string(index=False))


if __name__ == "__main__":
    main()
