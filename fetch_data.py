import json
import time
from datetime import UTC, datetime
from pathlib import Path

import yfinance as yf

from api_utils import fetch_json_with_cache

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

NOW = datetime.now(UTC).isoformat()

STOCKS = ["AAPL", "MSFT", "TSLA"]
CRYPTO = ["bitcoin", "ethereum"]
COMMODITIES = ["GC=F", "CL=F"]  # Gold, Oil


def fetch_stock(ticker):
    t = yf.Ticker(ticker)
    hist = t.history(period="1y")
    info = t.info if hasattr(t, "info") else {}
    return {
        "type": "stock",
        "ticker": ticker,
        "info": info,
        "history": hist.reset_index().to_dict("records"),
        "fetched_at": NOW,
    }


def fetch_crypto(coin):
    url = f"https://api.coingecko.com/api/v3/coins/{coin}"
    payload, source = fetch_json_with_cache(
        url,
        namespace="coingecko_coin",
        cache_key=f"coin_{coin}",
        retries=5,
    )
    return {
        "type": "crypto",
        "id": coin,
        "symbol": payload.get("symbol"),
        "market_data": payload.get("market_data"),
        "fetch_source": source,
        "fetched_at": NOW,
    }


results = []

for s in STOCKS:
    try:
        results.append(fetch_stock(s))
        time.sleep(1)
    except Exception as e:
        print("Stock error:", s, e)

for c in CRYPTO:
    try:
        results.append(fetch_crypto(c))
        time.sleep(1)
    except Exception as e:
        print("Crypto error:", c, e)

for com in COMMODITIES:
    try:
        results.append(fetch_stock(com))
        time.sleep(1)
    except Exception as e:
        print("Commodity error:", com, e)

filename = DATA_DIR / f"raw_{datetime.now(UTC).strftime('%Y%m%d')}.json"
with open(filename, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("Saved", filename)


