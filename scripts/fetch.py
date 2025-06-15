#!/usr/bin/env python3
"""
Fetch quarterly Revenue & Net Income for the tickers below and save
data/<TICKER>.json   and   data/index.json (list of tickers).
Compatible with yfinance >= 0.2.40 (earnings API v2)
"""
import json, time
from pathlib import Path
import yfinance as yf
import pandas as pd       # already pulled in by yfinance

TICKERS = ["AAPL", "MSFT", "NVDA"]      # add/remove as you wish
OUT_DIR = Path("data")
OUT_DIR.mkdir(exist_ok=True)


def quarter_results(symbol: str) -> dict:
    """
    Returns:
        { "2024-12-31": {"Revenue": 123_456_789_000,
                         "Earnings": 34_567_890_000}, … }
    """
    tkr = yf.Ticker(symbol)

    # Get the dataframe: rows = line-items, columns = period end-dates
    stmt = tkr.quarterly_income_stmt
    if stmt.empty:
        return {}

    # Pivot so each row is one period
    stmt = stmt.T  # index = period (Timestamp), columns = line items

    # Different tickers label revenue slightly differently
    revenue_cols  = ["Total Revenue", "Revenue"]
    earnings_cols = ["Net Income", "Net Income Common Stockholders",
                     "Net Income Applicable To Common Shares"]

    def first_existing(row, candidates):
        for c in candidates:
            if c in row:
                return row[c]
        return None

    out = {}
    for idx, row in stmt.iterrows():
        out[str(idx.date())] = {
            "Revenue":  first_existing(row, revenue_cols),
            "Earnings": first_existing(row, earnings_cols),
        }

    return out


def main() -> None:
    index = []
    for symbol in TICKERS:
        print("Fetching", symbol, "…", flush=True)
        data = quarter_results(symbol)
        (OUT_DIR / f"{symbol}.json").write_text(json.dumps(data, indent=2))
        index.append(symbol)
        time.sleep(1)        # polite pause

    (OUT_DIR / "index.json").write_text(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()

