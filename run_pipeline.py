"""
Run the full ETL pipeline:  Yahoo Finance -> clean/validate -> SQLite
Then build the dashboard.

Usage (from the project folder):
    python run_pipeline.py
"""
import sqlite3

import config
from etl.extract import extract_prices
from etl.transform import transform_prices
from etl.load import load
from dashboard.build_dashboard import build_dashboard


def main():
    all_tickers = list(config.TICKERS) + [config.BENCHMARK]

    print("1/4 Extracting prices...")
    raw = extract_prices(all_tickers, config.YEARS_OF_HISTORY)

    print("2/4 Transforming and validating...")
    clean, report = transform_prices(raw)
    for key, value in report.items():
        print(f"  {key}: {value}")

    print("3/4 Loading into SQLite...")
    total = load(config.DB_PATH, "sql/schema.sql", config.TICKERS, config.BENCHMARK, clean)
    print(f"  fact_daily_price now has {total} rows")

    # Data-quality summary from the database itself
    con = sqlite3.connect(config.DB_PATH)
    for row in con.execute("SELECT * FROM v_data_quality"):
        print("  ", row)
    con.close()

    print("4/4 Building dashboard...")
    path = build_dashboard(config.DB_PATH, "sql/kpis.sql", config.DASHBOARD_PATH)
    print(f"  Done. Open {path} in your browser.")


if __name__ == "__main__":
    main()
