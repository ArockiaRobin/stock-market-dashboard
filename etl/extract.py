"""
EXTRACT: download daily prices from Yahoo Finance with the yfinance library.
Returns one tidy DataFrame: ticker, trade_date, open, high, low, close, volume.
"""
from datetime import date, timedelta

import pandas as pd
import yfinance as yf


def extract_prices(tickers, years):
    start = date.today() - timedelta(days=365 * years + 10)
    frames = []
    for ticker in tickers:
        # auto_adjust=True adjusts prices for splits and dividends,
        # so returns are comparable across the whole period
        raw = yf.download(ticker, start=start.isoformat(), auto_adjust=True, progress=False)
        if raw.empty:
            print(f"  WARNING: no data returned for {ticker}")
            continue
        # Newer yfinance versions return two-level columns ("Close", "AAPL"); flatten them
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        df = raw.reset_index().rename(columns={
            "Date": "trade_date", "Open": "open", "High": "high",
            "Low": "low", "Close": "close", "Volume": "volume",
        })
        df["ticker"] = ticker
        frames.append(df[["ticker", "trade_date", "open", "high", "low", "close", "volume"]])
        print(f"  {ticker}: {len(df)} rows")
    if not frames:
        raise RuntimeError("No data downloaded. Check your internet connection.")
    return pd.concat(frames, ignore_index=True)
