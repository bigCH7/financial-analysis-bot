import requests
import time
from pathlib import Path
from datetime import datetime
import statistics

# =========================
# CONFIG
# =========================
ASSETS = {
    "bitcoin": {"symbol": "BTC"},
    "ethereum": {"symbol": "ETH"},
}

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

COINGECKO = "https://api.coingecko.com/api/v3"
CACHE = {}

# =========================
# SAFE API
# =========================
def safe_get(url, params=None, key=None):
    if key and key in CACHE:
        return CACHE[key]

    for i in range(5):
        r = requests.get(url, params=params, timeout=20)
        if r.status_code == 200:
            data = r.json()
            if key:
                CACHE[key] = data
            return data
        if r.status_code == 429:
            time.sleep(15 + i * 10)
            continue
        r.raise_for_status()
    raise RuntimeError("API rate limit")

# =========================
# DATA
# =========================
def get_prices(asset, days=365):
    data = safe_get(
        f"{COINGECKO}/coins/{asset}/market_chart",
        params={"vs_currency": "usd", "days": days},
        key=f"prices_{asset}",
    )
    return [p[1] for p in data["prices"]]

def get_coin(asset):
    return safe_get(
        f"{COINGECKO}/coins/{asset}",
        params={"market_data": "true", "developer_data": "true"},
        key=f"coin_{asset}",
    )

def get_global():
    return safe_get(f"{COINGECKO}/global", key="global")

# =========================
# METRICS
# =========================
def volatility(prices):
    returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
    return statistics.stdev(returns) * (365 ** 0.5)

def drawdown(prices):
    peak = prices[0]
    max_dd = 0
    for p in prices:
        peak = max(peak, p)
        max_dd = min(max_dd, (p - peak) / peak)
    return max_dd * 100

def moving_avg(prices, window):
    return sum(prices[-window:]) / window

def trend(prices):
    return (prices[-1] - prices[-200]) / prices[-200] * 100

# =========================
# REGIME
# =========================
def risk_regime(prices):
    vol = volatility(prices)
    dd = drawdown(prices)
    tr = trend(prices)

    if dd < -40 and vol > 0.9:
        return "Panic"
    if tr > 30 and vol < 0.6:
        return "Expansion"
    if tr > 0 and vol > 0.8:
        return "Distribution"
    return "Accumulation"

# =========================
# ON-CHAIN PROXIES
# =========================
def onchain_metrics(coin):
    mcap = coin["market_data"]["market_cap"]["usd"]
    fdv = coin["market_data"]["fully_diluted_valuation"]["usd"] or mcap
    volume = coin["market_data"]["total_volume"]["usd"]
    commits = coin["developer_data"]["commit_count_4_weeks"] or 0

    return {
        "mcap_fdv": mcap / fdv if fdv else 1,
        "volume_ratio": volume / mcap if mcap else 0,
        "commits": commits,
    }

# =========================
# VALUATION ENGINE
# =========================
def valuation_band(prices, coin, onchain):
    price = prices[-1]
    ma200 = moving_avg(prices, 200)
    ma365 = moving_avg(prices, 365)

    score = 0

    score += -2 if price < ma365 * 0.7 else 0
    score += -1 if price < ma200 * 0.9 else 0
    score += 1 if price > ma200 * 1.3 else 0
    score += 2 if price > ma365 * 1.6 else 0

    if onchain["mcap_fdv"] < 0.8:
        score -= 1
    elif onchain["mcap_fdv"] > 1.05:
        score += 1

    if onchain["volume_ratio"] > 0.15:
        score += 1
    elif onchain["volume_ratio"] < 0.04:
        score -= 1

    if score <= -3:
        band = "Deeply Undervalued"
    elif score == -2:
        band = "Undervalued"
    elif -1 <= score <= 1:
        band = "Fair Value"
    elif score == 2:
        band = "Overvalued"
    else:
        band = "Extremely Overvalued"

    return band, score

# =========================
# REPORT
# =========================
def generate_report():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Long-Term Crypto Valuation Report",
        "",
        f"_Generated automatically — {now}_",
        "",
        "---",
    ]

    global_data = get_global()
    lines += [
        "## Macro Overview",
        "",
        f"- Bitcoin dominance: **{global_data['data']['market_cap_percentage']['btc']:.2f}%**",
        f"- Ethereum dominance: **{global_data['data']['market_cap_percentage']['eth']:.2f}%**",
        "",
        "---",
    ]

    for asset, cfg in ASSETS.items():
        prices = get_prices(asset)
        coin = get_coin(asset)
        onchain = onchain_metrics(coin)

        band, score = valuation_band(prices, coin, onchain)

        lines += [
            f"## {cfg['symbol']} — Valuation Assessment",
            "",
            f"- Price: **${coin['market_data']['current_price']['usd']:,.2f}**",
            f"- Valuation band: **{band}**",
            f"- Valuation score: **{score}**",
            "",
            "### Supporting Metrics",
            f"- Price / 200-day MA: **{prices[-1] / moving_avg(prices,200):.2f}**",
            f"- Price / 365-day MA: **{prices[-1] / moving_avg(prices,365):.2f}**",
            f"- Market Cap / FDV: **{onchain['mcap_fdv']:.2f}**",
            f"- Volume / Market Cap: **{onchain['volume_ratio']:.3f}**",
            f"- Developer commits (4w): **{onchain['commits']}**",
            "",
            "---",
        ]

        time.sleep(6)

    REPORT_DIR.joinpath("long_term_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("Long-term valuation report generated.")

# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    generate_report()

