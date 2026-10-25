"""
LOAD: write tickers and prices into SQLite.
Uses INSERT OR REPLACE on the (ticker, trade_date) primary key, so running
the pipeline again updates existing days instead of creating duplicates.
"""
import sqlite3
from datetime import datetime
from pathlib import Path


def load(db_path, schema_path, tickers, benchmark, prices):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(Path(schema_path).read_text())

    # Dimension table
    rows = [(t, name, sector, 0) for t, (name, sector) in tickers.items()]
    rows.append((benchmark, "S&P 500 ETF (benchmark)", "Benchmark", 1))
    con.executemany("INSERT OR REPLACE INTO dim_ticker VALUES (?, ?, ?, ?)", rows)

    # Fact table
    loaded_at = datetime.now().isoformat(timespec="seconds")
    records = [
        (r.ticker, r.trade_date, r.open, r.high, r.low, r.close, int(r.volume), loaded_at)
        for r in prices.itertuples(index=False)
    ]
    con.executemany(
        "INSERT OR REPLACE INTO fact_daily_price VALUES (?, ?, ?, ?, ?, ?, ?, ?)", records
    )
    con.commit()
    total = con.execute("SELECT COUNT(*) FROM fact_daily_price").fetchone()[0]
    con.close()
    return total
