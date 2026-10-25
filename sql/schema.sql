-- ============================================================
-- Stock market database schema (SQLite)
-- Star schema: one dimension table (tickers) and one fact table
-- (daily prices). Metrics are calculated in views.
-- ============================================================

-- Dimension: one row per stock
CREATE TABLE IF NOT EXISTS dim_ticker (
    ticker        TEXT PRIMARY KEY,
    company_name  TEXT NOT NULL,
    sector        TEXT NOT NULL,
    is_benchmark  INTEGER NOT NULL DEFAULT 0   -- 1 = SPY benchmark
);

-- Fact: one row per stock per trading day
CREATE TABLE IF NOT EXISTS fact_daily_price (
    ticker      TEXT NOT NULL REFERENCES dim_ticker(ticker),
    trade_date  TEXT NOT NULL,                 -- ISO date YYYY-MM-DD
    open        REAL,
    high        REAL,
    low         REAL,
    close       REAL NOT NULL,                 -- split- and dividend-adjusted
    volume      INTEGER,
    loaded_at   TEXT NOT NULL,                 -- when the ETL wrote the row
    PRIMARY KEY (ticker, trade_date)           -- stops duplicate days
);

-- View: daily return for each stock, using LAG over the previous trading day
DROP VIEW IF EXISTS v_daily_return;
CREATE VIEW v_daily_return AS
SELECT ticker,
       trade_date,
       close,
       close / LAG(close) OVER (PARTITION BY ticker ORDER BY trade_date) - 1 AS daily_return
FROM fact_daily_price;

-- View: data quality summary per stock
DROP VIEW IF EXISTS v_data_quality;
CREATE VIEW v_data_quality AS
SELECT ticker,
       COUNT(*)                                       AS trading_days,
       MIN(trade_date)                                AS first_date,
       MAX(trade_date)                                AS last_date,
       SUM(close IS NULL)                             AS missing_close,
       SUM(high < low)                                AS high_below_low,
       SUM(close > high OR close < low)               AS close_outside_range
FROM fact_daily_price
GROUP BY ticker;
