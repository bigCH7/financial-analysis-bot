import requests
import time
from pathlib import Path
from datetime import datetime
import statistics

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
        "max_supply": None,
        "store_of_value": False
    }
}

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

COINGECKO = "https://api.coingecko.com/api/v3"

# =========================
# API HELPERS
# =========================
def safe_get(url, params=None):
    for _ in range(3):
        r = requests.get(url, params=params, timeout=20)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            time.sleep(20)
        else:
            r.raise_for_status()
    raise RuntimeError("API rate limit")

def get_market_data(asset):
    data = safe_get(
        f"{COINGECKO}/coins/{asset}",
        params={"localization": "false", "market_data": "true"}
    )
    return data["market_data"]

def get_prices(asset, days=365):
    data = safe_get(
        f"{COINGECKO}/coins/{asset}/market_chart",
        params={"vs_currency": "usd", "days": days, "interval": "daily"}
    )
    return [p[1] for p in data["prices"]]

def pct_change(prices, days):
    if len(prices) < days:
        return None
    return (prices[-1] - prices[-days]) / prices[-days] * 100

# =========================
# VALUATION MODELS
# =========================
def btc_valuation(price, supply):
    bands = {
        "conservative": 5e12,
        "base_case": 10e12,
        "bull_case": 20e12
    }
    return {k: v / supply for k, v in bands.items()}

def eth_valuation(price, market_cap):
    float_supply = market_cap / price
    bands = {
        "conservative": 5e12,
        "base_case": 10e12,
        "bull_case": 20e12
    }
    return {k: v / float_supply for k, v in bands.items()}

# =========================
# RISK & MACRO OVERLAY
# =========================
def volatility(prices):
    returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
    return statistics.stdev(returns) * (365 ** 0.5)

def drawdown(prices):
    peak = prices[0]
    max_dd = 0
    for p in prices:
        peak = max(peak, p)
        dd = (p - peak) / peak
        max_dd = min(max_dd, dd)
    return max_dd * 100

def risk_score(vol, dd, dominance):
    score = 0
    if vol > 0.8:
        score += 2
    elif vol > 0.6:
        score += 1

    if dd < -60:
        score += 2
    elif dd < -40:
        score += 1

    if dominance > 55:
        score += 1

    if score <= 1:
        return "Low"
    if score <= 3:
        return "Moderate"
    return "High"

# =========================
# REPORT
# =========================
def generate_report():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = []

    lines.append("# Long-Term Crypto Valuation & Risk Report")
    lines.append("")
    lines.append(f"_Generated automatically — {now}_")
    lines.append("")
    lines.append("---")

    global_data = safe_get(f"{COINGECKO}/global")
    btc_dom = global_data["data"]["market_cap_percentage"]["btc"]
    eth_dom = global_data["data"]["market_cap_percentage"]["eth"]

    lines.append("## Macro Market Context")
    lines.append("")
    lines.append(f"- Bitcoin dominance: **{btc_dom:.2f}%**")
    lines.append(f"- Ethereum dominance: **{eth_dom:.2f}%**")

    if btc_dom > 55:
        lines.append("- Interpretation: **Risk-off environment. Capital consolidating into Bitcoin.**")
    else:
        lines.append("- Interpretation: **Risk-on environment. Capital rotating into higher beta assets.**")

    lines.append("")
    lines.append("---")

    for asset, cfg in ASSETS.items():
        data = get_market_data(asset)
        prices = get_prices(asset)

        price = data["current_price"]["usd"]
        market_cap = data["market_cap"]["usd"]

        vol = volatility(prices)
        dd = drawdown(prices)

        if asset == "bitcoin":
            valuation = btc_valuation(price, cfg["max_supply"])
            dom = btc_dom
            model = "Store of Value (Digital Gold)"
        else:
            valuation = eth_valuation(price, market_cap)
            dom = eth_dom
            model = "Network Utility & Settlement Layer"

        risk = risk_score(vol, dd, btc_dom)

        lines.append(f"## {cfg['symbol']} — Long-Term Analysis")
        lines.append("")
        lines.append(f"- Current price: **${price:,.2f}**")
        lines.append(f"- Market cap: **${market_cap/1e12:.2f}T**")
        lines.append(f"- Annualized volatility: **{vol:.2f}**")
        lines.append(f"- Max drawdown (1y): **{dd:.2f}%**")
        lines.append("")
        lines.append(f"### Valuation Model: {model}")
        lines.append("")
        lines.append("**Implied valuation ranges:**")
        lines.append(f"- Conservative: **${valuation['conservative']:,.0f}**")
        lines.append(f"- Base case: **${valuation['base_case']:,.0f}**")
        lines.append(f"- Bull case: **${valuation['bull_case']:,.0f}**")
        lines.append("")
        lines.append(f"### Risk Assessment: **{risk}**")

        if risk == "Low":
            lines.append("- Environment favorable for long-term accumulation.")
        elif risk == "Moderate":
            lines.append("- Balanced risk. Position sizing and patience recommended.")
        else:
            lines.append("- Elevated systemic risk. Long-term thesis intact, but volatility likely.")

        lines.append("")
        lines.append("---")

        time.sleep(10)

    report_path = REPORT_DIR / "long_term_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report generated: {report_path}")

# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    generate_report()


