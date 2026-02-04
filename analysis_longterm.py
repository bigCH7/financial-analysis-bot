import requests
import time
from pathlib import Path
from datetime import datetime

# =========================
# Configuration
# =========================

ASSETS = {
    "bitcoin": "Bitcoin (BTC)",
    "ethereum": "Ethereum (ETH)"
}

VS_CURRENCY = "usd"
DAYS = 365
API_DELAY = 2.5  # seconds between API calls (rate-limit safety)

REPORT_DIR = Path("reports")
REPORT_FILE = REPORT_DIR / "index.md"

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

def analyze_valuation(prices):
    values = [p[1] for p in prices]

    current = values[-1]
    avg_1y = sum(values) / len(values)
    low_1y = min(values)
    high_1y = max(values)

    ratio = current / avg_1y

    if ratio < 0.8:
        band = "UNDERVALUED"
        score = -2
    elif ratio < 0.95:
        band = "SLIGHTLY UNDERVALUED"
        score = -1
    elif ratio <= 1.05:
        band = "FAIR VALUE"
        score = 0
    elif ratio <= 1.2:
        band = "SLIGHTLY OVERVALUED"
        score = 1
    else:
        band = "OVERVALUED"
        score = 2

    return {
        "current": current,
        "avg_1y": avg_1y,
        "low_1y": low_1y,
        "high_1y": high_1y,
        "band": band,
        "score": score
    }

# =========================
# Report Generation
# =========================

def generate_report():
    REPORT_DIR.mkdir(exist_ok=True)

    lines = []
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines.append("# Long-Term Crypto Valuation Report\n")
    lines.append(f"_Generated automatically — {now}_\n")

    for asset_id, name in ASSETS.items():
        time.sleep(API_DELAY)

        data = get_price_history(asset_id)
        if not data or "prices" not in data:
            lines.append(f"## {name}\n")
            lines.append("Data unavailable due to API limits.\n")
            continue

        valuation = analyze_valuation(data["prices"])

        lines.append(f"## {name}\n")
        lines.append(f"- **Current price:** ${valuation['current']:,.0f}")
        lines.append(f"- **1Y average price:** ${valuation['avg_1y']:,.0f}")
        lines.append(
            f"- **1Y low / high:** "
            f"${valuation['low_1y']:,.0f} / ${valuation['high_1y']:,.0f}"
        )
        lines.append(f"- **Valuation:** **{valuation['band']}**\n")

    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")

# =========================
# Entry Point
# =========================

if __name__ == "__main__":
    generate_report()
