"""
Configuration management for Attribution Analytics project.
All parameters loaded from environment variables - no hardcoding.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Central configuration class using Pydantic for validation.
    Loads all settings from .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Snowflake Connection
    snowflake_account: str = Field(..., description="Snowflake account identifier")
    snowflake_user: str = Field(..., description="Snowflake username")
    snowflake_password: str = Field(..., description="Snowflake password")
    snowflake_role: str = Field(default="ACCOUNTADMIN")
    snowflake_warehouse: str = Field(default="COMPUTE_WH")
    snowflake_database: str = Field(default="ATTRIBUTION_DEV")

    # Data Generation Parameters
    num_events: int = Field(default=35000, description="Number of GA4 events to generate")
    num_impressions: int = Field(default=27000, description="Number of ad impressions")
    num_campaigns: int = Field(default=12, description="Number of campaigns")
    user_overlap_pct: float = Field(
        default=0.60, ge=0.0, le=1.0, description="Percentage of users with both events and impressions"
    )
    random_seed: int = Field(default=42, description="Random seed for reproducibility")
    start_date: str = Field(default="2024-11-01", description="Start date for data generation")
    end_date: str = Field(default="2024-12-15", description="End date for data generation")

    # Optional GA4 Configuration
    ga4_property_id: Optional[str] = Field(default=None)
    google_application_credentials: Optional[str] = Field(default=None)

    # Derived Properties
    @property
    def data_dir(self) -> Path:
        """Data directory path."""
        path = Path(__file__).parent.parent / "data"
        path.mkdir(exist_ok=True)
        return path

    @property
    def start_datetime(self) -> datetime:
        """Start date as datetime object."""
        return datetime.strptime(self.start_date, "%Y-%m-%d")

    @property
    def end_datetime(self) -> datetime:
        """End date as datetime object."""
        return datetime.strptime(self.end_date, "%Y-%m-%d")

    @property
    def date_range_days(self) -> int:
        """Number of days in date range."""
        return (self.end_datetime - self.start_datetime).days

    # Publisher Configuration (realistic viewability rates)
    @property
    def publishers(self) -> Dict[str, Dict[str, float]]:
        """
        Publisher configurations with viewability rates.
        Based on industry standards (MRC guidelines).
        """
        return {
            "premium_news": {"viewability": 0.75},
            "premium_sports": {"viewability": 0.72},
            "premium_business": {"viewability": 0.70},
            "mid_tier_social": {"viewability": 0.62},
            "mid_tier_content": {"viewability": 0.58},
        }

    # Channel Distribution (realistic traffic patterns)
    @property
    def channel_distribution(self) -> Dict[str, float]:
        """Realistic channel distribution for web traffic."""
        return {
            "direct": 0.40,
            "organic_search": 0.30,
            "social": 0.15,
            "referral": 0.10,
            "email": 0.05,
        }

    # Campaign Type CTR (click-through rates by format)
    @property
    def campaign_ctr(self) -> Dict[str, Dict[str, float]]:
        """
        Click-through rates by campaign type and format.
        Based on programmatic advertising benchmarks.
        """
        return {
            "prospecting": {
                "display": 0.0010,  # 0.10%
                "video": 0.0140,  # 1.40%
                "native": 0.0028,  # 0.28%
            },
            "retargeting": {
                "display": 0.0020,  # 0.20% (2x prospecting)
                "video": 0.0280,  # 2.80%
                "native": 0.0056,  # 0.56%
            },
        }

    def get_snowflake_connection_params(self) -> Dict[str, str]:
        """Get Snowflake connection parameters as dict."""
        return {
            "account": self.snowflake_account,
            "user": self.snowflake_user,
            "password": self.snowflake_password,
            "role": self.snowflake_role,
            "warehouse": self.snowflake_warehouse,
            "database": self.snowflake_database,
        }


# Singleton instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get or create config singleton.
    
    Returns:
        Config instance loaded from environment
    """
    global _config
    if _config is None:
        _config = Config()
    return _config
