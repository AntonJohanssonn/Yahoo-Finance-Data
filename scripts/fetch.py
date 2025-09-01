#!/usr/bin/env python3
"""
Fetch quarterly Revenue & Net Income for the tickers below and save:
  data/<TICKER>.json  and  data/index.json
Requires yfinance >= 0.2.40
"""
import json, time
from pathlib import Path
import yfinance as yf

TICKERS = ["AAPL", "MSFT", "NVDA"]  # add/remove as you wish
OUT_DIR = Path("data")
OUT_DIR.mkdir(exist_ok=True)

def _first_existing(row, candidates):
    for c in candidates:
        if c in row and row[c] is not None:
            return row[c]
    return None

def quarter_results(symbol: str) -> dict:
    tkr = yf.Ticker(symbol)

    # Newer yfinance: quarterly_income_stmt (rows = line-items, cols = periods)
    stmt = getattr(tkr, "quarterly_income_stmt", None)
    if stmt is None or stmt.empty:
        # Fallback for older versions: quarterly_financials
        stmt = getattr(tkr, "quarterly_financials", None)
        if stmt is None or stmt.empty:
            return {}

    # Transpose: each row = one period
    stmt = stmt.T  # index = Timestamp (period end), columns = line items

    revenue_cols  = ["Total Revenue", "Revenue"]
    earnings_cols = ["Net Income", "Net Income Common Stockholders",
                     "Net Income Applicable To Common Shares"]

    out = {}
    for idx, row in stmt.iterrows():
        out[str(idx.date())] = {
            "Revenue":  _first_existing(row, revenue_cols),
            "Earnings": _first_existing(row, earnings_cols),
        }
    return out

def main() -> None:
    index = []
    for symbol in TICKERS:
        print(f"Fetching {symbol} …", flush=True)
        data = quarter_results(symbol)
        (OUT_DIR / f"{symbol}.json").write_text(json.dumps(data, indent=2))
        index.append(symbol)
        time.sleep(0.5)  # polite pause

    (OUT_DIR / "index.json").write_text(json.dumps(index, indent=2))
    print("Done.")

if __name__ == "__main__":
    main()
