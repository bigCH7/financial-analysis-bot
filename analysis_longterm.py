import requests
import time
from pathlib import Path
from datetime import datetime
import statistics

# =========================
# CONFIG
# =========================
ASSETS = {
    "bitcoin": {"symbol": "BTC", "max_supply": 21_000_000},
    "ethereum": {"symbol": "ETH", "max_supply": None},
}

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

COINGECKO = "https://api.coingecko.com/api/v3"
SESSION_CACHE = {}

# =========================
# SAFE API LAYER
# =========================
def safe_get(url, params=None, cache_key=None):
    if cache_key and cache_key in SESSION_CACHE:
        return SESSION_CACHE[cache_key]

    for attempt in range(5):
        r = requests.get(url, params=params, timeout=20)
        if r.status_code == 200:
            data = r.json()
            if cache_key:
                SESSION_CACHE[cache_key] = data
            return data

        if r.status_code == 429:
            sleep_time = 15 + attempt * 10
            print(f"Rate limited. Sleeping {sleep_time}s…")
            time.sleep(sleep_time)
            continue

        r.raise_for_status()

    return None

# =========================
# DATA
# =========================
def get_global():
    return safe_get(f"{COINGECKO}/global", cache_key="global")

def get_coin(asset):
    return safe_get(
        f"{COINGECKO}/coins/{asset}",
        params={"localization": "false", "market_data": "true"},
        cache_key=f"coin_{asset}",
    )

def get_prices(asset, days=365):
    data = safe_get(
        f"{COINGECKO}/coins/{asset}/market_chart",
        params={"vs_currency": "usd", "days": days, "interval": "daily"},
        cache_key=f"prices_{asset}",
    )
    if not data:
        return []
    return [p[1] for p in data["prices"]]

# =========================
# METRICS
# =========================
def volatility(prices):
    if len(prices) < 2:
        return None
    returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
    return statistics.stdev(returns) * (365 ** 0.5)

def drawdown(prices):
    if not prices:
        return None
    peak = prices[0]
    max_dd = 0
    for p in prices:
        peak = max(peak, p)
        dd = (p - peak) / peak
        max_dd = min(max_dd, dd)
    return max_dd * 100

# =========================
# VALUATION
# =========================
def btc_valuation():
    return {
        "Bear": 3e12 / 21_000_000,
        "Base": 10e12 / 21_000_000,
        "Bull": 20e12 / 21_000_000,
    }

def eth_valuation(price, mcap):
    if not price or not mcap:
        return None
    supply = mcap / price
    return {
        "Bear": 4e12 / supply,
        "Base": 10e12 / supply,
        "Bull": 20e12 / supply,
    }

# =========================
# SCENARIOS
# =========================
def scenarios(asset, valuation):
    if asset == "bitcoin":
        return {
            "Bear": (
                valuation["Bear"],
                "Global liquidity contraction, regulatory pressure, BTC treated purely as risk asset."
            ),
            "Base": (
                valuation["Base"],
                "Gradual institutional adoption, ETF flows offset volatility, BTC as digital gold."
            ),
            "Bull": (
                valuation["Bull"],
                "Monetary debasement, sovereign accumulation, BTC becomes global reserve hedge."
            ),
        }
    else:
        return {
            "Bear": (
                valuation["Bear"],
                "Layer-2 fragmentation, regulatory uncertainty, fee compression."
            ),
            "Base": (
                valuation["Base"],
                "ETH remains dominant settlement layer for DeFi, RWAs, rollups mature."
            ),
            "Bull": (
                valuation["Bull"],
                "ETH captures global financial rails, staking yield + fee burn shock supply."
            ),
        }

# =========================
# REPORT
# =========================
def generate_report():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = []

    lines.append("# Long-Term Crypto Valuation & Scenario Report")
    lines.append("")
    lines.append(f"_Generated automatically — {now}_")
    lines.append("")
    lines.append("---")

    global_data = get_global()
    btc_dom = global_data["data"]["market_cap_percentage"]["btc"] if global_data else None
    eth_dom = global_data["data"]["market_cap_percentage"]["eth"] if global_data else None

    lines.append("## Macro Backdrop")
    lines.append("")
    lines.append(f"- Bitcoin dominance: **{btc_dom:.2f}%**" if btc_dom else "- Bitcoin dominance: N/A")
    lines.append(f"- Ethereum dominance: **{eth_dom:.2f}%**" if eth_dom else "- Ethereum dominance: N/A")
    lines.append("")
    lines.append("---")

    for asset, cfg in ASSETS.items():
        coin = get_coin(asset)
        prices = get_prices(asset)

        price = coin["market_data"]["current_price"]["usd"] if coin else None
        mcap = coin["market_data"]["market_cap"]["usd"] if coin else None

        vol = volatility(prices)
        dd = drawdown(prices)

        if asset == "bitcoin":
            valuation = btc_valuation()
        else:
            valuation = eth_valuation(price, mcap)

        lines.append(f"## {cfg['symbol']} — Valuation & Scenarios")
        lines.append("")
        lines.append(f"- Current price: **${price:,.2f}**" if price else "- Price: N/A")
        lines.append(f"- Market cap: **${mcap/1e12:.2f}T**" if mcap else "- Market cap: N/A")
        lines.append(f"- Volatility (annualized): **{vol:.2f}**" if vol else "- Volatility: N/A")
        lines.append(f"- Max drawdown (1y): **{dd:.2f}%**" if dd else "- Max drawdown: N/A")
        lines.append("")

        lines.append("### Scenario Analysis")
        scenario_data = scenarios(asset, valuation)

        for name, (price_target, narrative) in scenario_data.items():
            lines.append(f"**{name} Case**")
            lines.append(f"- Implied price: **${price_target:,.0f}**")
            lines.append(f"- Thesis: {narrative}")
            lines.append("")

        lines.append("---")
        time.sleep(8)

    report_path = REPORT_DIR / "long_term_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to {report_path}")

# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    generate_report()
