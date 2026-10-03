"""
Campaign metadata: 3 advertisers x 2 campaign types x 2 creative formats = 12 campaigns,
all running for the full simulation window.
"""

import argparse

import pandas as pd

from config import get_config

ADVERTISERS = [
    {"name": "RetailCo", "formats": ["display", "video"]},
    {"name": "SaaS_Platform", "formats": ["native", "video"]},
    {"name": "CPG_Brand", "formats": ["display", "native"]},
]
CAMPAIGN_TYPES = ["prospecting", "retargeting"]
BASE_DAILY_BUDGET = {"display": 500, "video": 1200, "native": 800}
PROSPECTING_BUDGET_MULTIPLIER = 1.5

CAMPAIGN_COLUMNS = [
    "campaign_id",
    "campaign_name",
    "advertiser",
    "campaign_type",
    "creative_format",
    "start_date",
    "end_date",
    "daily_budget",
]


class CampaignGenerator:
    def __init__(self, config):
        self.config = config

    def generate(self) -> pd.DataFrame:
        rows = []
        campaign_id = 1
        for advertiser in ADVERTISERS:
            for campaign_type in CAMPAIGN_TYPES:
                for creative_format in advertiser["formats"]:
                    budget = BASE_DAILY_BUDGET[creative_format]
                    if campaign_type == "prospecting":
                        budget *= PROSPECTING_BUDGET_MULTIPLIER
                    rows.append(
                        {
                            "campaign_id": f"camp_{campaign_id:04d}",
                            "campaign_name": f"{creative_format.upper()}_{campaign_type.upper()}_{campaign_id:02d}",
                            "advertiser": advertiser["name"],
                            "campaign_type": campaign_type,
                            "creative_format": creative_format,
                            "start_date": self.config.start_date,
                            "end_date": self.config.end_date,
                            "daily_budget": round(float(budget), 2),
                        }
                    )
                    campaign_id += 1

        df = pd.DataFrame(rows, columns=CAMPAIGN_COLUMNS)
        print(f"Campaigns: {len(df)} ({df['campaign_type'].value_counts().to_dict()})")
        return df


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic campaign metadata")
    parser.add_argument("--output", type=str, help="Output CSV path")
    args = parser.parse_args()

    config = get_config()
    campaigns = CampaignGenerator(config).generate()

    config.data_dir.mkdir(exist_ok=True)
    output_path = args.output or config.data_dir / "campaigns.csv"
    campaigns.to_csv(output_path, index=False)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
