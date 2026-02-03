import requests
import statistics
from datetime import datetime
from pathlib import Path

# -----------------------------
# Configuration
# -----------------------------
ASSETS = {
    "bitcoin": "BTC",
    "ethereum": "ETH"
}

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

# -----------------------------
# Data Fetching
# -----------------------------
def get_market_data(asset_id, days=365):
    url = (
        f"https://api.coingecko.com/api/v3/coins/{asset_id}/market_chart"
        f"?vs_currency=usd&days={days}&interval=daily"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()["prices"]


def get_global_data():
    r = requests.get("https://api.coingecko.com/api/v3/global", timeout=30)
    r.raise_for_status()
    return r.json()["data"]

# -----------------------------
# Analytics
# -----------------------------
def moving_average(prices, window=200):
    if len(prices) < window:
        return None
    return statistics.mean(prices[-window:])


def price_percentile(prices):
    current = prices[-1]
    below = sum(1 for p in prices if p <= current)
    return round((below / len(prices)) * 100, 2)


def performance(prices, days=30):
    if len(prices) <= days:
        return None
    return round(((prices[-1] / prices[-days]) - 1) * 100, 2)


# -----------------------------
# Report Generation
# -----------------------------
def generate_report():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = []

    lines.append("# Long-Term Crypto Investment Report")
    lines.append("")
    lines.append(f"_Generated automatically on {now}_")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Macro context
    global_data = get_global_data()
    btc_dom = global_data["market_cap_percentage"]["btc"]
    eth_dom = global_data["market_cap_percentage"]["eth"]

    lines.append("## Macro & Capital Flow Context")
    lines.append(f"- Bitcoin dominance: **{btc_dom:.2f}%**")
    lines.append(f"- Ethereum dominance: **{eth_dom:.2f}%**")
    lines.append("")

    if btc_dom > 55:
        lines.append(
            "**Interpretation:** Risk-off environment. "
            "Capital concentrating in Bitcoin as defensive positioning."
        )
    else:
        lines.append(
            "**Interpretation:** Risk-on environment. "
            "Capital rotating into higher-beta assets."
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # Asset sections
    for asset, ticker in ASSETS.items():
        data = get_market_data(asset)
        prices = [p[1] for p in data]

        ma_200 = moving_average(prices)
        pct = price_percentile(prices)
        perf_30d = performance(prices, 30)

        lines.append(f"## {ticker} Long-Term Valuation")
        lines.append(f"- Current price: **${prices[-1]:,.2f}**")
        lines.append(f"- 30-day performance: **{perf_30d}%**")
        lines.append(f"- Price percentile (1Y): **{pct}%**")

        if ma_200:
            lines.append(f"- 200-day average: **${ma_200:,.2f}**")

            if prices[-1] > ma_200:
                trend = "Above long-term average (bullish bias)"
            else:
                trend = "Below long-term average (bearish bias)"

            lines.append(f"- Trend position: **{trend}**")

        # Valuation interpretation
        if pct < 30:
            valuation = "Historically cheap relative to last year"
        elif pct > 70:
            valuation = "Historically expensive relative to last year"
        else:
            valuation = "Fairly valued within historical range"

        lines.append(f"- Valuation signal: **{valuation}**")
        lines.append("")
        lines.append(
            "_Note: Crypto valuation is relative and regime-dependent, "
            "not based on cash flows._"
        )
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)

# -----------------------------
# Main
# -----------------------------
def main():
    report = generate_report()
    report_path = REPORT_DIR / "long_term_report.md"
    report_path.write_text(report, encoding="utf-8")

    print("✅ Long-term report generated:")
    print(report_path.resolve())

if __name__ == "__main__":
    main()

