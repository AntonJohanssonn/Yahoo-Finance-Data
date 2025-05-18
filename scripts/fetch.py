#!/usr/bin/env python3
"""
Fetch quarterly Revenue & EPS for the tickers below and save
data/<TICKER>.json   and   data/index.json (list of tickers).
Runs fine on GitHub Actions because yfinance does its own crumb handshake.
"""
import json, time
from pathlib import Path
import yfinance as yf

TICKERS = ["AAPL", "MSFT", "NVDA"]      # ← add/remove as you wish
OUT_DIR = Path("data")
OUT_DIR.mkdir(exist_ok=True)

def quarter_results(ticker):
    """Return {date: {"Revenue": …, "Earnings": …}, ...}"""
    df = yf.Ticker(ticker).quarterly_earnings
    if df.empty:
        return {}
    df.index = df.index.astype(str)
    return df.to_dict("index")

def main():
    index = []
    for symbol in TICKERS:
        print("Fetching", symbol, "…", flush=True)
        data = quarter_results(symbol)
        (OUT_DIR / f"{symbol}.json").write_text(json.dumps(data, indent=2))
        index.append(symbol)
        time.sleep(1)                      # polite pause
    # write index file
    (OUT_DIR / "index.json").write_text(json.dumps(index, indent=2))

if __name__ == "__main__":
    main()
