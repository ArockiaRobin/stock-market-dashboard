"""
TRANSFORM: clean and validate prices before loading.
Every row that is removed is counted and reported, never dropped silently.
"""
import pandas as pd


def transform_prices(df):
    report = {"rows_in": len(df)}

    df = df.copy()
    # Dates as ISO text (YYYY-MM-DD) so SQLite date functions work
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y-%m-%d")
    df["volume"] = df["volume"].fillna(0).astype("int64")

    # Rule 1: a day without a closing price can't be used
    missing_close = df["close"].isna()
    report["removed_missing_close"] = int(missing_close.sum())
    df = df[~missing_close]

    # Rule 2: duplicate ticker + date (keep the last one downloaded)
    dupes = df.duplicated(subset=["ticker", "trade_date"], keep="last")
    report["removed_duplicates"] = int(dupes.sum())
    df = df[~dupes]

    # Rule 3: impossible price bars (high below low) are flagged, not fixed
    report["flag_high_below_low"] = int((df["high"] < df["low"]).sum())

    report["rows_out"] = len(df)
    return df.sort_values(["ticker", "trade_date"]).reset_index(drop=True), report
