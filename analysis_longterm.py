import requests
import time
from pathlib import Path
from datetime import datetime

# =========================
# CONFIG
# =========================
ASSETS = {
    "bitcoin": {
        "symbol": "BTC",
        "max_supply": 21_000_000,
        "store_of_value": True
    },
    "ethereum": {
        "symbol": "ETH",
        "max_supply": None,  # elastic
        "store_of_value": False
    }
}

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# =========================
# HELPERS
# =========================
def safe_get(url, params=None):
    for _ in range(3):
        r = requests.get(url, params=params, timeout=20)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            time.sleep(15)
        else:
            r.raise_for_status()
    raise RuntimeError("API rate limit exceeded")

def get_price_data(asset):
    data = safe_get(
        f"{COINGECKO_BASE}/coins/{asset}",
        params={"localization": "false", "tickers": "false", "market_data": "true"}
    )
    return data["market_data"]

def get_market_chart(asset, days=365):
    data = safe_get(
        f"{COINGECKO_BASE}/coins/{asset}/market_chart",
        params={"vs_currency": "usd", "days": days, "interval": "daily"}
    )
    return data["prices"]

def pct_change(prices, days):
    if len(prices) < days:
        return None
    start = prices[-days][1]
    end = prices[-1][1]
    return (end - start) / start * 100

# =========================
# VALUATION MODELS
# =========================
def btc_valuation(price, supply):
    """
    Bitcoin valuation via Store-of-Value bands
    """
    market_cap = price * supply

    low_band = 5e12    # conservative digital gold thesis
    mid_band = 10e12   # base case
    high_band = 20e12  # global reserve asset

    def implied_price(cap):
        return cap / supply

    return {
        "current_market_cap": market_cap,
        "valuation_ranges": {
            "conservative": implied_price(low_band),
            "base_case": implied_price(mid_band),
            "bull_case": implied_price(high_band),
        }
    }

def eth_valuation(price, market_cap):
    """
    Ethereum valuation via network utility (GDP multiple proxy)
    """
    low = 0.05 * 1e14
    mid = 0.10 * 1e14
    high = 0.20 * 1e14

    def implied_price(cap):
        return cap / (market_cap / price)

    return {
        "current_market_cap": market_cap,
        "valuation_ranges": {
            "conservative": implied_price(low),
            "base_case": implied_price(mid),
            "bull_case": implied_price(high),
        }
    }

# =========================
# REPORT
# =========================
def generate_report():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = []

    lines.append("# Long-Term Crypto Valuation Report")
    lines.append("")
    lines.append(f"_Generated automatically — {now}_")
    lines.append("")
    lines.append("---")

    for asset, cfg in ASSETS.items():
        data = get_price_data(asset)
        prices = get_market_chart(asset)
        price = data["current_price"]["usd"]
        market_cap = data["market_cap"]["usd"]

        perf_30d = pct_change(prices, 30)
        perf_365d = pct_change(prices, 365)

        lines.append(f"## {cfg['symbol']} — Long-Term Valuation")
        lines.append("")
        lines.append(f"- Current price: **${price:,.2f}**")
        lines.append(f"- Market cap: **${market_cap/1e12:.2f}T**")
        if perf_30d is not None:
            lines.append(f"- 30d performance: **{perf_30d:.2f}%**")
        if perf_365d is not None:
            lines.append(f"- 1y performance: **{perf_365d:.2f}%**")
        lines.append("")

        if asset == "bitcoin":
            valuation = btc_valuation(price, cfg["max_supply"])
            lines.append("### Valuation Model: Store of Value (Digital Gold)")
        else:
            valuation = eth_valuation(price, market_cap)
            lines.append("### Valuation Model: Network Utility & Settlement Layer")

        ranges = valuation["valuation_ranges"]

        lines.append("")
        lines.append("**Implied long-term valuation ranges:**")
        lines.append("")
        lines.append(f"- Conservative: **${ranges['conservative']:,.0f}**")
        lines.append(f"- Base case: **${ranges['base_case']:,.0f}**")
        lines.append(f"- Bull case: **${ranges['bull_case']:,.0f}**")
        lines.append("")
        lines.append("**Interpretation:**")
        if price < ranges["conservative"]:
            lines.append("- Asset appears **deeply undervalued** relative to long-term fundamentals.")
        elif price < ranges["base_case"]:
            lines.append("- Asset appears **moderately undervalued**.")
        elif price < ranges["bull_case"]:
            lines.append("- Asset appears **fairly valued with upside optionality**.")
        else:
            lines.append("- Asset appears **priced for optimistic scenarios**.")

        lines.append("")
        lines.append("---")

        time.sleep(10)  # avoid rate limits

    report_path = REPORT_DIR / "long_term_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Report generated: {report_path}")

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    generate_report()

