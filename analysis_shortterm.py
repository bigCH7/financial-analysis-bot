import requests
import time
from pathlib import Path
from datetime import datetime
import statistics

# =========================
# Configuration
# =========================

ASSETS = {
    "bitcoin": "Bitcoin (BTC)",
    "ethereum": "Ethereum (ETH)"
}

VS_CURRENCY = "usd"
DAYS = 30
API_DELAY = 2.5

REPORT_DIR = Path("reports")
REPORT_FILE = REPORT_DIR / "short_term.md"

# =========================
# Helpers
# =========================

def safe_get(url, params=None, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=20)
            if r.status_code == 429:
                time.sleep(10)
                continue
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(5)

def get_price_history(asset_id):
    url = f"https://api.coingecko.com/api/v3/coins/{asset_id}/market_chart"
    params = {
        "vs_currency": VS_CURRENCY,
        "days": DAYS,
        "interval": "daily"
    }
    return safe_get(url, params)

def analyze_short_term(prices):
    values = [p[1] for p in prices]

    current = values[-1]
    price_7d = values[-8]
    price_30d = values[0]

    change_7d = (current / price_7d - 1) * 100
    change_30d = (current / price_30d - 1) * 100

    returns = [
        (values[i] / values[i - 1] - 1) * 100
        for i in range(1, len(values))
    ]

    volatility = statistics.stdev(returns)

    # Trend logic
    if change_30d > 5:
        trend = "UPTREND"
    elif change_30d < -5:
        trend = "DOWNTREND"
    else:
        trend = "SIDEWAYS"

    # Momentum logic
    momentum = "STRONG" if abs(change_7d) > 5 else "WEAK"

    # Volatility regime
    if volatility > 4:
        vol_state = "ELEVATED"
    else:
        vol_state = "NORMAL"

    return {
        "current": current,
        "change_7d": change_7d,
        "change_30d": change_30d,
        "trend": trend,
        "momentum": momentum,
        "volatility": vol_state
    }

# =========================
# Report Generation
# =========================

def generate_report():
    REPORT_DIR.mkdir(exist_ok=True)

    lines = []
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines.append("# Short-Term Market Context\n")
    lines.append(f"_Generated automatically — {now}_\n")

    for asset_id, name in ASSETS.items():
        time.sleep(API_DELAY)

        data = get_price_history(asset_id)
        if not data or "prices" not in data:
            lines.append(f"## {name}\n")
            lines.append("Data unavailable due to API limits.\n")
            continue

        s = analyze_short_term(data["prices"])

        lines.append(f"## {name}\n")
        lines.append(f"- **Current price:** ${s['current']:,.0f}")
        lines.append(f"- **7D change:** {s['change_7d']:.2f}%")
        lines.append(f"- **30D change:** {s['change_30d']:.2f}%")
        lines.append(f"- **Trend:** **{s['trend']}**")
        lines.append(f"- **Momentum:** **{s['momentum']}**")
        lines.append(f"- **Volatility:** **{s['volatility']}**\n")

    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")

# =========================
# Entry Point
# =========================

if __name__ == "__main__":
    generate_report()
