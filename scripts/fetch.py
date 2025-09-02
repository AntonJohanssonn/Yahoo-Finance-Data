#!/usr/bin/env python3
"""
Fetch quarterly Revenue & EPS (Net Income / Shares Outstanding) for the tickers
below and save:
  data/<TICKER>.json  and  data/index.json

Requires yfinance >= 0.2.40
"""
import json, time
from pathlib import Path
import yfinance as yf

TICKERS = ["AAPL", "MSFT", "NVDA", "ACB", "HRTX"]   # add/remove tickers here
OUT_DIR = Path("data")
OUT_DIR.mkdir(exist_ok=True)


def _first_existing(row, candidates):
    for c in candidates:
        if c in row and row[c] is not None:
            return row[c]
    return None


def quarter_results(symbol: str) -> dict:
    tkr = yf.Ticker(symbol)

    # Income statement (quarterly)
    stmt = getattr(tkr, "quarterly_income_stmt", None)
    if stmt is None or stmt.empty:
        stmt = getattr(tkr, "quarterly_financials", None)
    if stmt is None or stmt.empty:
        return {}

    stmt = stmt.T  # index = quarter end (Timestamp)

    revenue_cols  = ["Total Revenue", "Revenue"]
    earnings_cols = ["Net Income", "Net Income Common Stockholders",
                     "Net Income Applicable To Common Shares"]

    # Shares outstanding (note: one number, not historical per quarter)
    shares = tkr.info.get("sharesOutstanding", None)

    out = {}
    for idx, row in stmt.iterrows():
        date = str(idx.date())
        revenue = _first_existing(row, revenue_cols)
        net_income = _first_existing(row, earnings_cols)

        eps = None
        if net_income is not None and shares is not None and shares > 0:
            eps = net_income / shares

        out[date] = {
            "Revenue": revenue,
            "EPS": eps
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

