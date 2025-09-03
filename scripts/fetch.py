#!/usr/bin/env python3
"""
Fetch quarterly Revenue & EPS for a set of tickers and save:
  data/<TICKER>.json  and  data/index.json

How tickers are chosen:
- If data/tickers.json exists (e.g., pasted from your iOS app), it is used.
- Otherwise we fall back to DEFAULT_TICKERS below.

Strategy:
1) Use quarterly income statement for:
   - Revenue (Total Revenue / Revenue)
   - EPS  (prefer Diluted EPS or Basic EPS line items)
2) Fallback EPS = Net Income / Shares Outstanding (if EPS rows missing)

Requires: yfinance >= 0.2.40
"""

import json
import time
from pathlib import Path
import yfinance as yf

# ---------- Configuration ----------
OUT_DIR = Path("data")
OUT_DIR.mkdir(exist_ok=True)

DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "ACB", "HRTX"]  # fallback if no data/tickers.json

# Candidate line names used by Yahoo for various tickers
REV_COLS = ["Total Revenue", "Revenue"]
EPS_COLS = [
    "Diluted EPS", "Basic EPS", "EPS (Diluted)", "EPS (Basic)",
    "EPS Diluted", "EPS Basic"
]
NI_COLS = [
    "Net Income", "Net Income Common Stockholders",
    "Net Income Applicable To Common Shares"
]
SHR_COLS = [
    "Diluted Average Shares",
    "Weighted Average Shares Diluted",
    "Weighted Average Diluted Shares Outstanding",
    "Common Shares Used to Calculate Diluted EPS",
    "Basic Average Shares",
    "Weighted Average Shares Outstanding"
]

# ---------- Helpers ----------
def load_tickers() -> list[str]:
    """
    Load tickers from data/tickers.json if present, else use DEFAULT_TICKERS.
    The JSON file should be a simple array of strings, e.g.:
      ["AAPL", "MSFT", "NVDA"]
    """
    tickers_file = OUT_DIR / "tickers.json"
    if tickers_file.exists():
        try:
            data = json.loads(tickers_file.read_text())
            if isinstance(data, list) and all(isinstance(x, str) for x in data):
                return [x.upper() for x in data]
        except Exception:
            pass
    return DEFAULT_TICKERS


def _first_existing(row, candidates):
    for c in candidates:
        if c in row and row[c] is not None:
            return row[c]
    return None


def quarter_results(symbol: str) -> dict:
    tkr = yf.Ticker(symbol)

    # Income statement (quarterly) — primary source for both Revenue and EPS
    # Try both names to be robust across yfinance versions.
    stmt = getattr(tkr, "quarterly_income_stmt", None)
    if stmt is None or getattr(stmt, "empty", True):
        stmt = getattr(tkr, "quarterly_financials", None)
    if stmt is None or getattr(stmt, "empty", True):
        return {}

    # Transpose: each row is one quarter (index = period end)
    stmt = stmt.T

    # Shares Outstanding (single trailing value) used only as last resort
    trailing_shares = None
    try:
        trailing_shares = tkr.info.get("sharesOutstanding", None)
    except Exception:
        # Some tickers may raise on .info; ignore and rely on statement shares
        pass

    out = {}
    for idx, row in stmt.iterrows():
        try:
            date = str(idx.date())
        except Exception:
            date = str(idx)

        revenue = _first_existing(row, REV_COLS)

        # Prefer true EPS lines from the statement to keep dates correct
        eps = _first_existing(row, EPS_COLS)

        if eps is None:
            # Fallback: compute EPS = Net Income / (Diluted or Basic shares)
            net_income = _first_existing(row, NI_COLS)
            shares = _first_existing(row, SHR_COLS)
            if shares is None:
                shares = trailing_shares
            if net_income is not None and shares:
                try:
                    eps = net_income / shares
                except Exception:
                    eps = None

        out[date] = {"Revenue": revenue, "EPS": eps}

    return out


# ---------- Main ----------
def main() -> None:
    tickers = load_tickers()
    print(f"Tickers: {tickers}", flush=True)

    index = []
    for symbol in tickers:
        print(f"Fetching {symbol} …", flush=True)
        data = quarter_results(symbol)
        (OUT_DIR / f"{symbol}.json").write_text(json.dumps(data, indent=2))
        index.append(symbol)
        time.sleep(0.5)  # polite pause between requests

    (OUT_DIR / "index.json").write_text(json.dumps(index, indent=2))
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
