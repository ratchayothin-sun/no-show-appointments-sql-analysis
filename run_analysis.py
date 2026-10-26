"""
run_analysis.py
Load the Kaggle CSV into SQLite, run the cleaning SQL, run every named query in
sql/02_analysis.sql, and save the results to results/*.csv.

Usage:
    python run_analysis.py path/to/KaggleV2-May-2016.csv
"""
import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "noshow.db"
RESULTS = ROOT / "results"


def load_raw(csv_path: Path, con: sqlite3.Connection) -> int:
    df = pd.read_csv(csv_path)
    df["PatientId"] = df["PatientId"].astype("int64")  # CSV stores it as a float
    df.to_sql("raw_appointments", con, if_exists="replace", index=False)
    return len(df)


def run_cleaning(con: sqlite3.Connection) -> None:
    con.executescript((ROOT / "sql" / "01_clean.sql").read_text(encoding="utf-8"))


def split_queries(sql_text: str) -> dict[str, str]:
    """Split a SQL file into {name: query} using '-- name: <id>' marker lines."""
    parts = re.split(r"^-- name:\s*(\S+)\s*$", sql_text, flags=re.MULTILINE)
    # parts = [preamble, name1, body1, name2, body2, ...]
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


def main(csv_path: str) -> None:
    csv = Path(csv_path)
    RESULTS.mkdir(exist_ok=True)
    DB_PATH.parent.mkdir(exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()  # always rebuild from scratch

    con = sqlite3.connect(DB_PATH)
    raw_n = load_raw(csv, con)
    run_cleaning(con)
    clean_n = con.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    print(f"raw rows: {raw_n:,} | clean rows: {clean_n:,} | removed: {raw_n - clean_n}")

    queries = split_queries((ROOT / "sql" / "02_analysis.sql").read_text(encoding="utf-8"))
    for name, query in queries.items():
        df = pd.read_sql_query(query, con)
        df.to_csv(RESULTS / f"{name}.csv", index=False)
        print(f"\n=== {name} ===")
        print(df.to_string(index=False))

    # Clean table for Power BI / Excel
    pd.read_sql_query("SELECT * FROM appointments", con).to_csv(
        ROOT / "data" / "appointments_clean.csv", index=False
    )
    con.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python run_analysis.py path/to/KaggleV2-May-2016.csv")
    main(sys.argv[1])
