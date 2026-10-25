# Stock Performance Dashboard

An end-to-end analytics pipeline: daily stock prices are pulled from Yahoo Finance with Python, cleaned and validated, stored in a SQLite star schema, and turned into an interactive one-page dashboard.

```
Yahoo Finance (yfinance) → extract.py → transform.py → load.py → SQLite (market.db) → build_dashboard.py → stock_dashboard.html
```

## What the dashboard shows

- **KPI cards:** best 1-year return, benchmark (SPY) return, how many stocks beat the benchmark, most volatile stock
- **Key metrics table:** last close, 1-year return, 52-week high and low, annualized volatility, max drawdown
- **Performance comparison:** every stock rebased to 100 so different price levels can be compared; SPY dashed
- **Candlestick chart:** last 12 months with 20- and 50-day moving averages and volume; dropdown to switch stocks
- **Correlation heatmap:** how closely daily returns move together

## How to run (Windows, Anaconda/Miniconda)

```
cd path\to\stock-market-dashboard
pip install -r requirements.txt
python run_pipeline.py
```

Then open `dashboard/stock_dashboard.html` in a browser. Run it again any day to refresh the data; existing days are updated, not duplicated.

Change the stocks, benchmark or history length in `config.py`.

## Project structure

```
config.py                  tickers, benchmark, history length, file paths
run_pipeline.py            runs extract → transform → load → dashboard
etl/
  extract.py               downloads adjusted daily prices with yfinance
  transform.py             cleans data and reports every removed or flagged row
  load.py                  writes to SQLite with INSERT OR REPLACE (re-runnable)
sql/
  schema.sql               star schema (dim_ticker, fact_daily_price) and views
  kpis.sql                 KPI query: last close, 1-year return, 52-week range
dashboard/
  build_dashboard.py       builds the interactive HTML dashboard with Plotly
data/                      market.db is created here
```

## Design decisions

| Decision | Why |
|---|---|
| **SQLite** instead of a database server | No setup; the same SQL ports to MySQL or SQL Server with small changes |
| **Star schema** (one dimension, one fact table) | Clean joins and the same model a BI tool like Power BI expects |
| **Primary key on (ticker, trade_date)** + `INSERT OR REPLACE` | Running the pipeline twice never creates duplicate days |
| **Adjusted prices** (`auto_adjust=True`) | Splits and dividends don't create fake jumps in returns |
| **Validation in transform.py** | Missing closes and duplicates are removed and counted; impossible bars (high below low) are flagged |
| **Rebased performance chart** | A $60 stock and a $400 stock can be compared on one axis |
| **Volatility in Python, not SQL** | Many SQLite builds don't include `SQRT` |
| **Single HTML file with Plotly** | Interactive, shareable, and works offline |

## Ideas to extend it

- Load into MySQL or Azure SQL and connect Power BI to the same star schema
- Schedule a daily refresh (Windows Task Scheduler)
- Add fundamentals (P/E, earnings dates) from a second data source
- Add sector-level views and a risk vs. return scatter

## Notes

Data comes from Yahoo Finance through the open-source `yfinance` library, for learning and personal analysis. Not investment advice.

---

*Code drafted with AI assistance; run, tested and reviewed by the author.*
