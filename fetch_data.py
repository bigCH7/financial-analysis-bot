import json
import requests
from datetime import datetime
from pathlib import Path
import yfinance as yf
import time

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

NOW = datetime.utcnow().isoformat()

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
        "fetched_at": NOW
    }

def fetch_crypto(coin):
    url = f"https://api.coingecko.com/api/v3/coins/{coin}"
    r = requests.get(url, timeout=20)
    data = r.json()
    return {
        "type": "crypto",
        "id": coin,
        "symbol": data.get("symbol"),
        "market_data": data.get("market_data"),
        "fetched_at": NOW
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

filename = DATA_DIR / f"raw_{datetime.utcnow().strftime('%Y%m%d')}.json"
with open(filename, "w") as f:
    json.dump(results, f, indent=2)

print("Saved", filename)
