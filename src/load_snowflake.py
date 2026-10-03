"""
Load the generated CSVs into Snowflake raw tables.

Creates the configured database, runs sql/snowflake_ddl.sql, checks each CSV
header against its table's columns, then uploads to the table stage and runs
COPY INTO. Fails if Snowflake loads a different row count than the CSV holds.
"""

import csv

import pandas as pd
import snowflake.connector

from config import REPO_ROOT, get_config

DDL_PATH = REPO_ROOT / "sql" / "snowflake_ddl.sql"
TABLES = ["campaigns", "ga4_events", "impressions"]

COPY_FILE_FORMAT = (
    "TYPE = CSV SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '\"' "
    "EMPTY_FIELD_AS_NULL = TRUE ERROR_ON_COLUMN_COUNT_MISMATCH = TRUE"
)


def create_tables(conn, database: str) -> None:
    cur = conn.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS IDENTIFIER(%s)", (database,))
    cur.execute("USE DATABASE IDENTIFIER(%s)", (database,))
    cur.close()
    conn.execute_string(DDL_PATH.read_text())
    print(f"Created raw tables in {database}")


def check_header(cur, table: str, csv_path) -> None:
    with open(csv_path, newline="") as f:
        header = next(csv.reader(f))
    cur.execute(
        "SELECT LOWER(column_name) FROM information_schema.columns "
        "WHERE table_schema = 'RAW' AND table_name = %s ORDER BY ordinal_position",
        (table.upper(),),
    )
    columns = [row[0] for row in cur.fetchall()]
    if header != columns:
        raise ValueError(f"{csv_path.name} header {header} does not match raw.{table} columns {columns}")


def load_table(conn, table: str, data_dir) -> int:
    csv_path = data_dir / f"{table}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"{csv_path} not found; run the generators first")

    expected_rows = len(pd.read_csv(csv_path, dtype=str))
    cur = conn.cursor()
    check_header(cur, table, csv_path)

    cur.execute(f"PUT 'file://{csv_path.resolve()}' @raw.%{table} OVERWRITE = TRUE AUTO_COMPRESS = TRUE")
    cur.execute(
        f"COPY INTO raw.{table} FROM @raw.%{table} "
        f"FILE_FORMAT = ({COPY_FILE_FORMAT}) ON_ERROR = ABORT_STATEMENT FORCE = TRUE PURGE = TRUE"
    )
    result_columns = [col[0].lower() for col in cur.description]
    if "rows_loaded" not in result_columns:
        raise RuntimeError(f"COPY INTO raw.{table} processed no files: {cur.fetchall()}")
    loaded_idx = result_columns.index("rows_loaded")
    loaded = sum(row[loaded_idx] for row in cur.fetchall())
    cur.close()

    if loaded != expected_rows:
        raise RuntimeError(f"raw.{table}: loaded {loaded:,} rows but {csv_path.name} has {expected_rows:,}")
    print(f"raw.{table}: {loaded:,} rows")
    return loaded


def main():
    config = get_config()
    conn = snowflake.connector.connect(**config.snowflake_connection_params())
    try:
        create_tables(conn, config.snowflake_database)
        for table in TABLES:
            load_table(conn, table, config.data_dir)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
