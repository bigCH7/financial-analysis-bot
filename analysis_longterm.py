import requests
import time
import statistics
from datetime import datetime

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
HEADERS = {"Accept": "application/json"}

# -----------------------------
# Utility: safe API request
# -----------------------------
def safe_get(url, params=None, retries=3, backoff=5):
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=20)
            if r.status_code == 429:
                time.sleep(backoff * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == retries - 1:
                print(f"[WARN] API failed after retries: {e}")
                return None
            time.sleep(backoff * (attempt + 1))
    return None


# -----------------------------
# Market Data
# -----------------------------
def get_market_data(asset_id, days=365):
    url = f"{COINGECKO_BASE}/coins/{asset_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily"
    }
    data = safe_get(url, params)
    if not data or "prices" not in data:
        return []

    return [p[1] for p in data["prices"]]


def get_dominance():
    url = f"{COINGECKO_BASE}/global"
    data = safe_get(url)
    if not data:
        return {}

    mkt = data.get("data", {}).get("market_cap_percentage", {})
    return {
        "btc": round(mkt.get("btc", 0), 2),
        "eth": round(mkt.get("eth", 0), 2)
    }


# -----------------------------
# Analytics
# -----------------------------
def percent_change(prices):
    if len(prices) < 2:
        return 0.0
    return round((prices[-1] - prices[0]) / prices[0] * 100, 2)


def volatility(prices):
    if len(prices) < 10:
        return 0.0
    returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
    return round(statistics.stdev(returns) * 100, 2)


def risk_assessment(asset_id):
    prices = get_market_data(asset_id)
    if not prices:
        return {
            "30d": 0,
            "volatility": 0,
            "status": "Data unavailable"
        }

    last_30 = prices[-30:]
    return {
        "30d": percent_change(last_30),
        "volatility": volatility(last_30),
        "status": "OK"
    }


# -----------------------------
# Macro Interpretation
# -----------------------------
def interpret(btc, eth, dom):
    lines = []

    if btc["30d"] < 0 and eth["30d"] < btc["30d"]:
        lines.append("Risk-off environment. Capital consolidating into Bitcoin.")
    elif eth["30d"] > btc["30d"]:
        lines.append("Risk-on environment. Capital rotating into higher beta assets.")
    else:
        lines.append("Mixed signals. Market indecision.")

    if dom["btc"] > 55:
        lines.append("Bitcoin dominance elevated — defensive positioning.")
    else:
        lines.append("Lower BTC dominance — speculative appetite present.")

    return " ".join(lines)


# -----------------------------
# Main Report
# -----------------------------
def main():
    print("=" * 30)
    print("LONG-TERM CRYPTO MACRO ANALYSIS")
    print("=" * 30)
    print()

    dom = get_dominance()
    btc = risk_assessment("bitcoin")
    eth = risk_assessment("ethereum")

    print("Macro & Capital Flow Context")
    print(f"- Bitcoin dominance: {dom.get('btc', 0)}%")
    print(f"- Ethereum dominance: {dom.get('eth', 0)}%")
    print(f"- BTC 30d performance: {btc['30d']}%")
    print(f"- ETH 30d performance: {eth['30d']}%")
    print(f"- ETH vs BTC (30d): {round(eth['30d'] - btc['30d'], 2)}%")
    print()
    print("Interpretation:", interpret(btc, eth, dom))
    print()
    print(f"Generated: {datetime.utcnow().isoformat()} UTC")


if __name__ == "__main__":
    main()
