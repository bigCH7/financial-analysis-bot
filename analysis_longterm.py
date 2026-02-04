import requests
from pathlib import Path
from datetime import datetime
import statistics

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

COINGECKO = "https://api.coingecko.com/api/v3"

def get_price_history(asset, days=365):
    url = f"{COINGECKO}/coins/{asset}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return [p[1] for p in r.json()["prices"]]

def valuation_bitcoin(prices):
    current = prices[-1]
    ma200 = statistics.mean(prices[-200:])

    ratio = current / ma200

    if ratio < 0.9:
        verdict = "Undervalued (historically cheap)"
    elif ratio < 1.1:
        verdict = "Fairly valued (neutral zone)"
    else:
        verdict = "Overextended (late-cycle risk)"

    return f"""
Price vs 200D Average:
- Current price: ${current:,.0f}
- 200D average: ${ma200:,.0f}
- Ratio: {ratio:.2f}

Valuation verdict:
{verdict}

Interpretation:
The 200-day average is widely used by long-term investors to judge cycle positioning.
Prices meaningfully below it historically indicate accumulation zones.
"""

def valuation_ethereum(prices, btc_prices):
    eth_current = prices[-1]
    btc_current = btc_prices[-1]
    ratio = eth_current / btc_current

    if ratio < 0.04:
        verdict = "ETH deeply undervalued vs BTC"
    elif ratio < 0.055:
        verdict = "ETH fairly valued vs BTC"
    else:
        verdict = "ETH expensive vs BTC"

    return f"""
ETH/BTC Relative Valuation:
- ETH price: ${eth_current:,.0f}
- BTC price: ${btc_current:,.0f}
- ETH/BTC ratio: {ratio:.4f}

Relative valuation verdict:
{verdict}

Interpretation:
ETH/BTC is a key capital-rotation metric.
Professional investors use it to decide when to rotate between growth (ETH)
and defensive (BTC) exposure.
"""

def generate_report():
    btc_prices = get_price_history("bitcoin")
    eth_prices = get_price_history("ethereum")

    report = []
    report.append("# Long-Term Crypto Valuation Report\n")
    report.append(f"_Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_\n")

    report.append("## Bitcoin (BTC)\n")
    report.append("### Valuation Analysis\n")
    report.append(valuation_bitcoin(btc_prices))

    report.append("\n---\n")

    report.append("## Ethereum (ETH)\n")
    report.append("### Valuation Analysis\n")
    report.append(valuation_ethereum(eth_prices, btc_prices))

    output = REPORT_DIR / "long_term_report.md"
    output.write_text("\n".join(report), encoding="utf-8")

    print("✔ Long-term valuation report generated")

if __name__ == "__main__":
    generate_report()
