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

    print("API unavailable. Using fallback.")
    return None

# =========================
# DATA FETCHERS
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

def pct_change(prices):
    if len(prices) < 30:
        return None
    return (prices[-1] - prices[-30]) / prices[-30] * 100

# =========================
# VALUATION
# =========================
def btc_valuation():
    bands = {"Conservative": 5e12, "Base": 10e12, "Bull": 20e12}
    return {k: v / 21_000_000 for k, v in bands.items()}

def eth_valuation(price, mcap):
    if not price or not mcap:
        return None
    supply = mcap / price
    bands = {"Conservative": 5e12, "Base": 10e12, "Bull": 20e12}
    return {k: v / supply for k, v in bands.items()}

# =========================
# REPORT
# =========================
def generate_report():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = []

    lines.append("# Long-Term Crypto Macro, Valuation & Growth Report")
    lines.append("")
    lines.append(f"_Generated automatically — {now}_")
    lines.append("")
    lines.append("---")

    global_data = get_global()
    btc_dom = global_data["data"]["market_cap_percentage"]["btc"] if global_data else None
    eth_dom = global_data["data"]["market_cap_percentage"]["eth"] if global_data else None

    lines.append("## Macro Context")
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
        change_30d = pct_change(prices)

        if asset == "bitcoin":
            valuation = btc_valuation()
            model = "Digital Store of Value"
        else:
            valuation = eth_valuation(price, mcap)
            model = "Programmable Settlement Layer"

        lines.append(f"## {cfg['symbol']} — Long-Term Outlook")
        lines.append("")
        lines.append(f"- Price: **${price:,.2f}**" if price else "- Price: N/A")
        lines.append(f"- Market cap: **${mcap/1e12:.2f}T**" if mcap else "- Market cap: N/A")
        lines.append(f"- Volatility (annualized): **{vol:.2f}**" if vol else "- Volatility: N/A")
        lines.append(f"- Max drawdown: **{dd:.2f}%**" if dd else "- Max drawdown: N/A")
        lines.append(f"- 30d change: **{change_30d:.2f}%**" if change_30d else "- 30d change: N/A")
        lines.append("")
        lines.append(f"### Valuation Model — {model}")
        if valuation:
            for k, v in valuation.items():
                lines.append(f"- {k}: **${v:,.0f}**")
        else:
            lines.append("- Valuation unavailable (API limited)")
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

