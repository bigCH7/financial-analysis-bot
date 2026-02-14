import statistics
from datetime import UTC, datetime
from pathlib import Path

from api_utils import fetch_json_with_cache

ASSETS = {
    "bitcoin": "Bitcoin (BTC)",
    "ethereum": "Ethereum (ETH)",
}

VS_CURRENCY = "usd"
DAYS = 30
API_DELAY = 1.8

REPORT_DIR = Path("reports")
REPORT_FILE = REPORT_DIR / "short_term.md"


def get_price_history(asset_id):
    url = f"https://api.coingecko.com/api/v3/coins/{asset_id}/market_chart"
    params = {
        "vs_currency": VS_CURRENCY,
        "days": DAYS,
        "interval": "daily",
    }
    payload, source = fetch_json_with_cache(
        url,
        params=params,
        namespace="coingecko_market_chart",
        cache_key=f"{asset_id}_{VS_CURRENCY}_{DAYS}",
        retries=5,
    )
    return payload, source


def analyze_short_term(prices):
    values = [p[1] for p in prices]

    current = values[-1]
    price_7d = values[-8]
    price_30d = values[0]

    change_7d = (current / price_7d - 1) * 100
    change_30d = (current / price_30d - 1) * 100

    returns = [
        (values[i] / values[i - 1] - 1) * 100
        for i in range(1, len(values))
    ]

    volatility = statistics.stdev(returns)

    if change_30d > 5:
        trend = "UPTREND"
    elif change_30d < -5:
        trend = "DOWNTREND"
    else:
        trend = "SIDEWAYS"

    momentum = "STRONG" if abs(change_7d) > 5 else "WEAK"
    vol_state = "ELEVATED" if volatility > 4 else "NORMAL"

    return {
        "current": current,
        "change_7d": change_7d,
        "change_30d": change_30d,
        "trend": trend,
        "momentum": momentum,
        "volatility": vol_state,
    }


def generate_report():
    REPORT_DIR.mkdir(exist_ok=True)

    lines = []
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    lines.append("# Short-Term Market Context\n")
    lines.append(f"_Generated automatically - {now}_\n")

    for asset_id, name in ASSETS.items():
        payload = None
        source = "none"
        try:
            payload, source = get_price_history(asset_id)
        except Exception:
            payload = None

        if not payload or "prices" not in payload:
            lines.append(f"## {name}\n")
            lines.append("Data unavailable due to API limits and no local cache.\n")
            continue

        s = analyze_short_term(payload["prices"])

        lines.append(f"## {name}\n")
        lines.append(f"- **Current price:** ${s['current']:,.0f}")
        lines.append(f"- **7D change:** {s['change_7d']:.2f}%")
        lines.append(f"- **30D change:** {s['change_30d']:.2f}%")
        lines.append(f"- **Trend:** **{s['trend']}**")
        lines.append(f"- **Momentum:** **{s['momentum']}**")
        lines.append(f"- **Volatility:** **{s['volatility']}**")
        lines.append(f"- **Data source:** {source}\n")

    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    generate_report()

