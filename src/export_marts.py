"""
Export the reporting marts to CSV for Tableau Public, which cannot connect to Snowflake.

--target dev reads Snowflake; --target local reads the DuckDB file written by
`dbt build --target local`. With --check, nothing is written: the fresh export
is compared against the committed CSVs and any difference beyond rounding fails.
"""

import argparse
import datetime as dt
import io
import sys
from decimal import Decimal

import numpy as np
import pandas as pd

from config import REPO_ROOT, get_config

EXPORT_DIR = REPO_ROOT / "export"
DUCKDB_PATH = REPO_ROOT / "dbt" / "attributions" / "attribution.duckdb"
MARTS = {
    "fct_conversions": "conversion_id",
    "agg_channel_attribution": "channel",
    "fct_pathways": "pathway",
}
TOLERANCE = 0.01


def read_local(mart: str) -> pd.DataFrame:
    import duckdb

    if not DUCKDB_PATH.exists():
        raise FileNotFoundError(f"{DUCKDB_PATH} not found; run `dbt build --target local` first")
    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as conn:
        rel = conn.sql(f"SELECT * FROM analytics.{mart}")
        df = rel.df()
        for col, col_type in zip(rel.columns, rel.types, strict=True):
            if str(col_type) == "DATE":
                df[col] = df[col].dt.strftime("%Y-%m-%d")
        return df


def read_snowflake(conn, database: str, mart: str) -> pd.DataFrame:
    cur = conn.cursor()
    cur.execute("SELECT * FROM IDENTIFIER(%s)", (f"{database}.analytics.{mart}",))
    columns = [col[0] for col in cur.description]
    df = pd.DataFrame(cur.fetchall(), columns=columns)
    cur.close()
    return df


def normalize(df: pd.DataFrame, key: str) -> pd.DataFrame:
    df = df.rename(columns=str.lower)
    for col in df.columns:
        values = df[col].dropna()
        if values.empty:
            continue
        first = values.iloc[0]
        if isinstance(first, Decimal):
            df[col] = df[col].astype(float)
        elif isinstance(first, (pd.Timestamp, dt.datetime)):
            df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(first, dt.date):
            df[col] = df[col].astype(str)
        if pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].round(4)
    return df.sort_values(key, ignore_index=True)


def compare(fresh: pd.DataFrame, committed: pd.DataFrame, mart: str) -> list:
    if list(fresh.columns) != list(committed.columns):
        return [f"{mart}: columns {list(fresh.columns)} != committed {list(committed.columns)}"]
    if len(fresh) != len(committed):
        return [f"{mart}: {len(fresh)} rows != committed {len(committed)}"]

    problems = []
    for col in fresh.columns:
        a, b = fresh[col], committed[col]
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            same = np.isclose(a.astype(float), b.astype(float), atol=TOLERANCE, equal_nan=True)
        else:
            same = (a.astype(str) == b.astype(str)).to_numpy()
        if not same.all():
            row = int(np.argmin(same))
            problems.append(
                f"{mart}.{col}: {int((~same).sum())} rows differ, "
                f"first at row {row}: {a.iloc[row]!r} vs {b.iloc[row]!r}"
            )
    return problems


def main():
    parser = argparse.ArgumentParser(description="Export reporting marts to CSV")
    parser.add_argument("--target", choices=["dev", "local"], required=True)
    parser.add_argument("--check", action="store_true", help="Compare against committed CSVs instead of writing")
    args = parser.parse_args()

    config = get_config()
    conn = None
    if args.target == "dev":
        import snowflake.connector

        conn = snowflake.connector.connect(**config.snowflake_connection_params())

    try:
        exports = {}
        for mart, key in MARTS.items():
            raw = read_snowflake(conn, config.snowflake_database, mart) if conn else read_local(mart)
            exports[mart] = normalize(raw, key)
    finally:
        if conn:
            conn.close()

    if args.check:
        problems = []
        for mart, fresh in exports.items():
            committed_path = EXPORT_DIR / f"{mart}.csv"
            if not committed_path.exists():
                raise FileNotFoundError(f"{committed_path} not found; nothing to check against")
            committed = pd.read_csv(committed_path, keep_default_na=False, na_values=[""])
            committed = committed.sort_values(MARTS[mart], ignore_index=True)
            fresh = pd.read_csv(io.StringIO(fresh.to_csv(index=False)), keep_default_na=False, na_values=[""])
            problems += compare(fresh, committed, mart)
        if problems:
            print("\n".join(problems), file=sys.stderr)
            sys.exit(1)
        print(f"{args.target} build matches the committed exports ({', '.join(exports)})")
        return

    EXPORT_DIR.mkdir(exist_ok=True)
    for mart, df in exports.items():
        df.to_csv(EXPORT_DIR / f"{mart}.csv", index=False)
        print(f"export/{mart}.csv: {len(df):,} rows")


if __name__ == "__main__":
    main()
