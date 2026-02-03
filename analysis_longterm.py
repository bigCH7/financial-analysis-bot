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
        params={"market_data": "true"},
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
# POSITION SIZING
# =========================
def raw_position_size(vol):
    # inverse volatility weighting
    return 1 / vol if vol > 0 else 0

def normalize(weights):
    total = sum(weights.values())
    return {k: v / total * 100 for k, v in weights.items()}

def regime_bias(asset, regime):
    if regime == "Panic":
        return 1.3 if asset == "bitcoin" else 0.7
    if regime == "Expansion":
        return 1.2 if asset == "ethereum" else 0.8
    if regime == "Distribution":
        return 1.1 if asset == "bitcoin" else 0.9
    return 1.0

# =========================
# REPORT
# =========================
def generate_report():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Long-Term Crypto Portfolio Allocation Report",
        "",
        f"_Generated automatically — {now}_",
        "",
        "---",
    ]

    global_data = get_global()
    if global_data:
        lines += [
            "## Macro Overview",
            "",
            f"- Bitcoin dominance: **{global_data['data']['market_cap_percentage']['btc']:.2f}%**",
            f"- Ethereum dominance: **{global_data['data']['market_cap_percentage']['eth']:.2f}%**",
            "",
            "---",
        ]

    metrics = {}
    weights = {}

    for asset, cfg in ASSETS.items():
        prices = get_prices(asset)
        coin = get_coin(asset)

        vol = volatility(prices)
        dd = drawdown(prices)
        tr = trend(prices)
        regime = risk_regime(prices)

        base_weight = raw_position_size(vol)
        bias = regime_bias(asset, regime)
        weights[asset] = base_weight * bias

        metrics[asset] = {
            "price": coin["market_data"]["current_price"]["usd"],
            "vol": vol,
            "dd": dd,
            "trend": tr,
            "regime": regime,
        }

        time.sleep(6)

    allocation = normalize(weights)

    for asset, cfg in ASSETS.items():
        m = metrics[asset]
        lines += [
            f"## {cfg['symbol']} — Position Analysis",
            "",
            f"- Price: **${m['price']:,.2f}**",
            f"- Volatility (annualized): **{m['vol']:.2f}**",
            f"- Max drawdown (1y): **{m['dd']:.2f}%**",
            f"- 200d trend: **{m['trend']:.2f}%**",
            f"- Risk regime: **{m['regime']}**",
            "",
            f"### Suggested Portfolio Weight",
            f"- **{allocation[asset]:.1f}%** of crypto allocation",
            "",
            "---",
        ]

    REPORT_DIR.joinpath("long_term_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("Long-term allocation report generated.")

# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    generate_report()
