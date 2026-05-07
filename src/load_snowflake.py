"""
Snowflake Data Loader

Loads generated CSV files into Snowflake raw tables.
Executes DDL, loads data, and validates the load.

Uses direct SQL inserts for reliability across environments.
"""

import argparse
from pathlib import Path
from typing import Dict

import pandas as pd
import snowflake.connector

from config import get_config


class SnowflakeLoader:
    """Load CSV data into Snowflake."""

    def __init__(self, config):
        self.config = config
        self.conn = None

    def connect(self):
        """Establish Snowflake connection."""
        print(" Connecting to Snowflake...")
        
        self.conn = snowflake.connector.connect(
            **self.config.get_snowflake_connection_params()
        )
        
        print(f"   Connected to {self.config.snowflake_account}")
        return self.conn

    def execute_ddl(self):
        """Execute DDL script to create database and tables."""
        print("\n  Executing DDL...")
        
        cursor = self.conn.cursor()
        
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS ATTRIBUTION_DEV")
        print("   Database created")
        
        # Use database and create schemas
        cursor.execute("USE DATABASE ATTRIBUTION_DEV")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS raw")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS analytics")
        print("   Schemas created")
        
        # Create tables
        cursor.execute("""
            CREATE OR REPLACE TABLE raw.campaigns (
                campaign_id VARCHAR(30),
                advertiser VARCHAR(100),
                campaign_type VARCHAR(30),
                campaign_name VARCHAR(100),
                creative_format VARCHAR(20),
                start_date DATE,
                end_date DATE,
                daily_budget DECIMAL(10,2)
            )
        """)
        
        cursor.execute("""
            CREATE OR REPLACE TABLE raw.ga4_events (
                event_timestamp VARCHAR(50),
                event_date VARCHAR(10),
                event_name VARCHAR(100),
                user_pseudo_id VARCHAR(50),
                session_id VARCHAR(50),
                source VARCHAR(100),
                medium VARCHAR(50),
                campaign VARCHAR(200),
                page_location VARCHAR(500),
                device_category VARCHAR(20),
                country VARCHAR(100),
                revenue VARCHAR(20),
                transaction_id VARCHAR(50)
            )
        """)
        
        cursor.execute("""
            CREATE OR REPLACE TABLE raw.impressions (
                impression_id VARCHAR(50),
                impression_timestamp VARCHAR(50),
                user_pseudo_id VARCHAR(50),
                campaign_id VARCHAR(30),
                campaign_name VARCHAR(100),
                campaign_type VARCHAR(30),
                creative_format VARCHAR(30),
                publisher VARCHAR(50),
                is_viewable VARCHAR(10),
                has_click VARCHAR(10),
                device_category VARCHAR(20)
            )
        """)
        
        print("   Tables created")
        cursor.close()

    def load_table(self, csv_filename: str, table_name: str, schema: str = "raw") -> int:
        """
        Load CSV file into Snowflake table using direct SQL inserts.
        
        Args:
            csv_filename: Name of CSV file in data directory
            table_name: Name of target table
            schema: Schema name (default: raw)
            
        Returns:
            Number of rows loaded
        """
        csv_path = self.config.data_dir / csv_filename
        
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        print(f"\n Loading {csv_filename} → {schema}.{table_name}")
        
        # Read CSV
        df = pd.read_csv(csv_path)
        df = df.fillna('')  # Replace NaN with empty string
        print(f"   Loaded {len(df):,} rows from CSV")
        
        # Use schema
        cursor = self.conn.cursor()
        cursor.execute(f"USE SCHEMA {self.config.snowflake_database}.{schema}")
        
        # Build insert statement based on table
        if table_name == "campaigns":
            placeholders = "(%s, %s, %s, %s, %s, %s, %s, %s)"
            insert_sql = f"INSERT INTO {table_name} VALUES {placeholders}"
            data = [(str(row['campaign_id']), str(row['campaign_name']), str(row['advertiser']),
                    str(row['campaign_type']), str(row['creative_format']), 
                    str(row['start_date']), str(row['end_date']), str(row['daily_budget']))
                   for _, row in df.iterrows()]
        
        elif table_name == "ga4_events":
            placeholders = "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            insert_sql = f"INSERT INTO {table_name} VALUES {placeholders}"
            data = [(str(row['event_timestamp']), str(row['event_date']), str(row['event_name']),
                    str(row['user_pseudo_id']), str(row['session_id']), str(row['source']),
                    str(row['medium']), str(row['campaign']), str(row['page_location']),
                    str(row['device_category']), str(row['country']), str(row['revenue']),
                    str(row['transaction_id']) if pd.notna(row['transaction_id']) else '')
                   for _, row in df.iterrows()]
        
        elif table_name == "impressions":
            placeholders = "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            insert_sql = f"INSERT INTO {table_name} VALUES {placeholders}"
            data = [(str(row['impression_id']), str(row['impression_timestamp']), str(row['user_pseudo_id']),
                    str(row['campaign_id']), str(row['campaign_name']), str(row['campaign_type']),
                    str(row['creative_format']), str(row['publisher']), str(row['is_viewable']),
                    str(row['has_click']), str(row['device_category']))
                   for _, row in df.iterrows()]
        else:
            raise ValueError(f"Unknown table: {table_name}")
        
        # Bulk insert
        cursor.executemany(insert_sql, data)
        print(f"   Loaded {len(df):,} rows to {schema}.{table_name}")
        
        cursor.close()
        return len(df)

    def validate(self) -> Dict[str, int]:
        """
        Validate loaded data.
        
        Returns:
            Dictionary with validation metrics
        """
        print("\n Validating data load...")
        
        cursor = self.conn.cursor()
        cursor.execute(f"USE SCHEMA {self.config.snowflake_database}.raw")
        
        # Check row counts
        tables = ["ga4_events", "campaigns", "impressions"]
        counts = {}
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            counts[table] = count
            print(f"   {table}: {count:,} rows")
        
        # Check user overlap (simplified - no view needed)
        print("\n User Overlap Analysis:")
        cursor.execute("SELECT COUNT(DISTINCT user_pseudo_id) FROM ga4_events")
        web_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT user_pseudo_id) FROM impressions")
        ad_users = cursor.fetchone()[0]
        
        print(f"  - Web users: {web_users:,}")
        print(f"  - Ad-targeted users: {ad_users:,}")
        
        cursor.close()
        
        print("\n Validation complete!")
        return counts

    def close(self):
        """Close Snowflake connection."""
        if self.conn:
            self.conn.close()
            print("\n Disconnected from Snowflake")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Load data into Snowflake")
    parser.add_argument("--skip-ddl", action="store_true", help="Skip DDL execution")
    args = parser.parse_args()

    # Load config
    config = get_config()
    
    # Initialize loader
    loader = SnowflakeLoader(config)
    
    try:
        # Connect
        loader.connect()
        
        # Execute DDL (unless skipped)
        if not args.skip_ddl:
            loader.execute_ddl()
        else:
            print("\n Skipping DDL execution")
        
        # Load tables
        loader.load_table("campaigns.csv", "campaigns")
        loader.load_table("ga4_events.csv", "ga4_events")
        loader.load_table("impressions.csv", "impressions")
        
        # Validate
        counts = loader.validate()
        
        # Summary
        print("\n" + "="*60)
        print(" LOAD COMPLETE!")
        print("="*60)
        print(f"Total rows loaded: {sum(counts.values()):,}")
        print("\n Next steps:")
        print("  1. Run dbt: cd dbt/attributions && dbt run")
        print("  2. Or use Makefile: make transform")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n Error: {e}")
        raise
    finally:
        loader.close()


if __name__ == "__main__":
    main()
