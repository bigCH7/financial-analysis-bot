import requests
from datetime import datetime
from pathlib import Path

# -----------------------------
# Configuration
# -----------------------------
COINGECKO_API = "https://api.coingecko.com/api/v3"
VS_CURRENCY = "usd"

ASSETS = {
    "bitcoin": "BTC",
    "ethereum": "ETH"
}

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

# -----------------------------
# Data Fetching
# -----------------------------
def get_global_data():
    r = requests.get(f"{COINGECKO_API}/global")
    r.raise_for_status()
    return r.json()["data"]

def get_market_chart(asset_id, days=30):
    r = requests.get(
        f"{COINGECKO_API}/coins/{asset_id}/market_chart",
        params={
            "vs_currency": VS_CURRENCY,
            "days": days,
            "interval": "daily"
        }
    )
    r.raise_for_status()
    return r.json()["prices"]

# -----------------------------
# Calculations
# -----------------------------
def performance_30d(prices):
    start = prices[0][1]
    end = prices[-1][1]
    return ((end - start) / start) * 100

# -----------------------------
# Analysis Logic
# -----------------------------
def macro_analysis():
    global_data = get_global_data()

    btc_dom = global_data["market_cap_percentage"]["btc"]
    eth_dom = global_data["market_cap_percentage"]["eth"]

    btc_prices = get_market_chart("bitcoin", 30)
    eth_prices = get_market_chart("ethereum", 30)

    btc_perf = performance_30d(btc_prices)
    eth_perf = performance_30d(eth_prices)
    eth_vs_btc = eth_perf - btc_perf

    if btc_dom > 55 and eth_vs_btc < 0:
        interpretation = (
            "Risk-off environment. Capital consolidating into Bitcoin. "
            "Bitcoin dominance elevated — defensive positioning."
        )
    else:
        interpretation = (
            "Risk-on or neutral environment. Capital rotating toward higher beta assets."
        )

    return {
        "btc_dominance": btc_dom,
        "eth_dominance": eth_dom,
        "btc_30d": btc_perf,
        "eth_30d": eth_perf,
        "eth_vs_btc": eth_vs_btc,
        "interpretation": interpretation
    }

# -----------------------------
# Reporting
# -----------------------------
def generate_report(data):
    timestamp = datetime.utcnow()
    filename = REPORT_DIR / f"long_term_report_{timestamp.date()}.md"

    report = f"""# Long-Term Crypto Macro Analysis

**Generated:** {timestamp.strftime('%Y-%m-%d %H:%M UTC')}

## Macro & Capital Flow Context

- **Bitcoin dominance:** {data['btc_dominance']:.2f}%
- **Ethereum dominance:** {data['eth_dominance']:.2f}%
- **BTC 30d performance:** {data['btc_30d']:.2f}%
- **ETH 30d performance:** {data['eth_30d']:.2f}%
- **ETH vs BTC (30d):** {data['eth_vs_btc']:.2f}%

## Interpretation

{data['interpretation']}

---

*Automatically generated. Not financial advice.*
"""

    filename.write_text(report, encoding="utf-8")
    return filename

# -----------------------------
# Main
# -----------------------------
def main():
    print("=" * 30)
    print("LONG-TERM CRYPTO MACRO ANALYSIS")
    print("=" * 30)

    data = macro_analysis()

    print("\nMacro & Capital Flow Context")
    print(f"- Bitcoin dominance: {data['btc_dominance']:.2f}%")
    print(f"- Ethereum dominance: {data['eth_dominance']:.2f}%")
    print(f"- BTC 30d performance: {data['btc_30d']:.2f}%")
    print(f"- ETH 30d performance: {data['eth_30d']:.2f}%")
    print(f"- ETH vs BTC (30d): {data['eth_vs_btc']:.2f}%")

    print(f"\nInterpretation: {data['interpretation']}")

    report_path = generate_report(data)
    print(f"\nReport saved to: {report_path}")

if __name__ == "__main__":
    main()

