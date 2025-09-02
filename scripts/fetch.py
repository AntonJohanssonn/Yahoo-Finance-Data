#!/usr/bin/env python3
"""
Fetch quarterly Revenue & EPS for the tickers below and save:
  data/<TICKER>.json  and  data/index.json
Requires yfinance >= 0.2.40
"""
import json, time
from pathlib import Path
import yfinance as yf

TICKERS = ["AAPL", "MSFT", "NVDA"]
OUT_DIR = Path("data")
OUT_DIR.mkdir(exist_ok=True)

def _first_existing(row, candidates):
    for c in candidates:
        if c in row and row[c] is not None:
            return row[c]
    return None

def quarter_results(symbol: str) -> dict:
    tkr = yf.Ticker(symbol)

    # Income statement for revenue
    stmt = getattr(tkr, "quarterly_income_stmt", None)
    if stmt is None or stmt.empty:
        stmt = getattr(tkr, "quarterly_financials", None)
    if stmt is None or stmt.empty:
        return {}

    stmt = stmt.T  # index = period end

    # EPS is usually in quarterly_earnings
    eps_df = getattr(tkr, "quarterly_earnings", None)
    eps = {}
    if eps_df is not None and not eps_df.empty:
        for idx, row in eps_df.iterrows():
            eps[str(idx.date())] = row.get("Earnings", None)

    revenue_cols = ["Total Revenue", "Revenue"]

    out = {}
    for idx, row in stmt.iterrows():
        date = str(idx.date())
        out[date] = {
            "Revenue": _first_existing(row, revenue_cols),
            "EPS": eps.get(date, None)   # match with quarterly earnings
        }
    return out

def main() -> None:
    index = []
    for symbol in TICKERS:
        print(f"Fetching {symbol} …", flush=True)
        data = quarter_results(symbol)
        (OUT_DIR / f"{symbol}.json").write_text(json.dumps(data, indent=2))
        index.append(symbol)
        time.sleep(0.5)
    (OUT_DIR / "index.json").write_text(json.dumps(index, indent=2))
    print("Done.")

if __name__ == "__main__":
    main()

