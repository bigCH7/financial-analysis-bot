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
# SAFE API
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
            time.sleep(15 + attempt * 10)
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
    peak = prices[0]
    max_dd = 0
    for p in prices:
        peak = max(peak, p)
        dd = (p - peak) / peak
        max_dd = min(max_dd, dd)
    return max_dd * 100

def trend(prices):
    if len(prices) < 200:
        return None
    return (prices[-1] - prices[-200]) / prices[-200] * 100

# =========================
# RISK REGIME
# =========================
def risk_regime(prices):
    if len(prices) < 200:
        return "Unknown", "Insufficient data"

    vol = volatility(prices)
    dd = drawdown(prices)
    tr = trend(prices)

    if dd < -40 and vol > 0.9:
        return "Panic / Capitulation", "Forced selling, liquidity stress, long-term opportunity forming."
    if tr > 30 and vol < 0.6:
        return "Expansion", "Uptrend intact, momentum favored."
    if tr > 0 and vol > 0.8:
        return "Distribution", "Volatility rising near highs, risk of reversal."
    return "Accumulation", "Depressed prices, volatility compressing, patient capital favored."

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
            "Bear": (valuation["Bear"], "Liquidity contraction, BTC treated as risk asset."),
            "Base": (valuation["Base"], "ETF flows, gradual institutional adoption."),
            "Bull": (valuation["Bull"], "Monetary debasement, sovereign demand."),
        }
    return {
        "Bear": (valuation["Bear"], "Regulatory pressure, fee compression."),
        "Base": (valuation["Base"], "ETH as dominant settlement layer."),
        "Bull": (valuation["Bull"], "Global financial rails migrate on-chain."),
    }

# =========================
# REPORT
# =========================
def generate_report():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Long-Term Crypto Valuation, Risk & Scenario Report",
        "",
        f"_Generated automatically — {now}_",
        "",
        "---",
    ]

    global_data = get_global()
    if global_data:
        lines += [
            "## Macro Context",
            "",
            f"- Bitcoin dominance: **{global_data['data']['market_cap_percentage']['btc']:.2f}%**",
            f"- Ethereum dominance: **{global_data['data']['market_cap_percentage']['eth']:.2f}%**",
            "",
            "---",
        ]

    for asset, cfg in ASSETS.items():
        coin = get_coin(asset)
        prices = get_prices(asset)

        price = coin["market_data"]["current_price"]["usd"] if coin else None
        mcap = coin["market_data"]["market_cap"]["usd"] if coin else None

        vol = volatility(prices)
        dd = drawdown(prices)
        tr = trend(prices)

        regime, regime_note = risk_regime(prices)

        valuation = btc_valuation() if asset == "bitcoin" else eth_valuation(price, mcap)

        lines += [
            f"## {cfg['symbol']} — Long-Term Assessment",
            "",
            f"- Price: **${price:,.2f}**" if price else "- Price: N/A",
            f"- Market cap: **${mcap/1e12:.2f}T**" if mcap else "- Market cap: N/A",
            f"- Volatility (annualized): **{vol:.2f}**" if vol else "- Volatility: N/A",
            f"- Max drawdown (1y): **{dd:.2f}%**",
            f"- 200d trend: **{tr:.2f}%**",
            "",
            f"### Risk Regime: **{regime}**",
            f"- Interpretation: {regime_note}",
            "",
            "### Scenario Analysis",
        ]

        for name, (target, thesis) in scenarios(asset, valuation).items():
            lines += [
                f"**{name} Case**",
                f"- Implied price: **${target:,.0f}**",
                f"- Thesis: {thesis}",
                "",
            ]

        lines.append("---")
        time.sleep(8)

    REPORT_DIR.joinpath("long_term_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("Report generated successfully.")

# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    generate_report()
