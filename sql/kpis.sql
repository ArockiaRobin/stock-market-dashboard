-- ============================================================
-- KPI query used by the dashboard (SQLite)
-- One row per stock: latest price, 1-year return and 52-week range.
-- (Volatility is calculated in Python, because SQLite builds often
--  lack SQRT.)
-- ============================================================
WITH latest AS (
    SELECT ticker, MAX(trade_date) AS last_date
    FROM fact_daily_price
    GROUP BY ticker
),
year_ago AS (
    -- closing price on the last trading day at least 365 days before the latest date
    SELECT f.ticker, f.close AS close_1y
    FROM fact_daily_price f
    JOIN latest l ON l.ticker = f.ticker
    WHERE f.trade_date = (
        SELECT MAX(trade_date) FROM fact_daily_price x
        WHERE x.ticker = f.ticker
          AND x.trade_date <= date(l.last_date, '-365 days')
    )
),
range_52w AS (
    SELECT f.ticker, MAX(f.high) AS high_52w, MIN(f.low) AS low_52w
    FROM fact_daily_price f
    JOIN latest l ON l.ticker = f.ticker
    WHERE f.trade_date > date(l.last_date, '-365 days')
    GROUP BY f.ticker
)
SELECT d.ticker,
       d.company_name,
       d.sector,
       d.is_benchmark,
       l.last_date,
       p.close                         AS last_close,
       p.close / y.close_1y - 1        AS return_1y,
       g.high_52w,
       g.low_52w
FROM dim_ticker d
JOIN latest l           ON l.ticker = d.ticker
JOIN fact_daily_price p ON p.ticker = d.ticker AND p.trade_date = l.last_date
LEFT JOIN year_ago y    ON y.ticker = d.ticker
LEFT JOIN range_52w g   ON g.ticker = d.ticker
ORDER BY d.is_benchmark, return_1y DESC;
