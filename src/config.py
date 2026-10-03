"""
Settings for data generation and the Snowflake load, read from .env.
Snowflake credentials are only required by load_snowflake.py.
"""

from datetime import datetime
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    snowflake_account: str | None = None
    snowflake_user: str | None = None
    snowflake_password: str | None = None
    snowflake_role: str = "SYSADMIN"
    snowflake_warehouse: str = "COMPUTE_WH"
    snowflake_database: str = "ATTRIBUTION_DEV"

    num_users: int = Field(default=6000, gt=0)
    ad_reach_pct: float = Field(
        default=0.60, ge=0.0, le=1.0, description="Share of site users the ad platform can reach"
    )
    random_seed: int = 42
    start_date: str = "2024-11-01"
    end_date: str = "2024-12-15"

    data_dir: Path = REPO_ROOT / "data"

    @model_validator(mode="after")
    def check_date_range(self) -> "Config":
        if self.end_datetime < self.start_datetime:
            raise ValueError(f"END_DATE {self.end_date} is before START_DATE {self.start_date}")
        return self

    @property
    def start_datetime(self) -> datetime:
        return datetime.strptime(self.start_date, "%Y-%m-%d")

    @property
    def end_datetime(self) -> datetime:
        """Last second of end_date; the flight includes the whole day."""
        return datetime.strptime(self.end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

    @property
    def date_range_days(self) -> int:
        return (datetime.strptime(self.end_date, "%Y-%m-%d") - self.start_datetime).days + 1

    @property
    def channel_mix(self) -> dict[str, float]:
        """Session traffic mix by channel."""
        return {
            "direct": 0.40,
            "organic_search": 0.30,
            "social": 0.15,
            "referral": 0.10,
            "email": 0.05,
        }

    @property
    def publisher_viewability(self) -> dict[str, float]:
        return {
            "premium_news": 0.75,
            "premium_sports": 0.72,
            "premium_business": 0.70,
            "mid_tier_social": 0.62,
            "mid_tier_content": 0.58,
        }

    @property
    def ctr(self) -> dict[str, dict[str, float]]:
        """Click-through rate on viewable impressions, by campaign type and format."""
        return {
            "prospecting": {"display": 0.0010, "video": 0.0140, "native": 0.0028},
            "retargeting": {"display": 0.0020, "video": 0.0280, "native": 0.0056},
        }

    def snowflake_connection_params(self) -> dict[str, str]:
        missing = [
            name
            for name in ("snowflake_account", "snowflake_user", "snowflake_password")
            if not getattr(self, name)
        ]
        if missing:
            raise ValueError(f"Missing Snowflake settings in .env: {', '.join(m.upper() for m in missing)}")
        return {
            "account": self.snowflake_account,
            "user": self.snowflake_user,
            "password": self.snowflake_password,
            "role": self.snowflake_role,
            "warehouse": self.snowflake_warehouse,
            "database": self.snowflake_database,
        }


_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config
