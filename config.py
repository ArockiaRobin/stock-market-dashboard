"""
Project settings. Change the tickers or dates here; nothing else needs editing.
"""

# Stocks to track: ticker -> (company name, sector)
TICKERS = {
    "AAPL": ("Apple", "Technology"),
    "MSFT": ("Microsoft", "Technology"),
    "NVDA": ("NVIDIA", "Technology"),
    "AMZN": ("Amazon", "Consumer Discretionary"),
    "JPM":  ("JPMorgan Chase", "Financials"),
    "XOM":  ("Exxon Mobil", "Energy"),
}

# Benchmark used for comparison (S&P 500 ETF)
BENCHMARK = "SPY"

# How much history to load (years back from today)
YEARS_OF_HISTORY = 3

# Where the database and dashboard are saved
DB_PATH = "data/market.db"
DASHBOARD_PATH = "dashboard/stock_dashboard.html"
