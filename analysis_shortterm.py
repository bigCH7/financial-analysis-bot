import statistics
from datetime import UTC, datetime
from pathlib import Path

from api_utils import fetch_json_with_cache

ASSETS = {
    "bitcoin": {"name": "Bitcoin (BTC)", "binance": "BTCUSDT"},
    "ethereum": {"name": "Ethereum (ETH)", "binance": "ETHUSDT"},
}

VS_CURRENCY = "usd"
REPORT_DIR = Path("reports")
REPORT_FILE = REPORT_DIR / "short_term.md"


def fmt_pct(value, digits=2):
    if value is None:
        return "N/A"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{digits}f}%"


def fmt_price(value):
    if value is None:
        return "N/A"
    return f"${value:,.0f}"


def ema(values, period):
    if not values or len(values) < period:
        return None
    k = 2 / (period + 1)
    out = values[0]
    for v in values[1:]:
        out = v * k + out * (1 - k)
    return out


def roc(values, lookback):
    if not values or len(values) <= lookback:
        return None
    base = values[-1 - lookback]
    if base == 0:
        return None
    return (values[-1] / base - 1.0) * 100.0


def rsi(values, period=14):
    if not values or len(values) <= period:
        return None
    gains = []
    losses = []
    for i in range(1, len(values)):
        delta = values[i] - values[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    avg_gain = statistics.mean(gains[-period:])
    avg_loss = statistics.mean(losses[-period:])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def volatility_pct(values):
    if not values or len(values) < 10:
        return None
    rets = [(values[i] / values[i - 1] - 1.0) * 100.0 for i in range(1, len(values))]
    if len(rets) < 2:
        return None
    return statistics.stdev(rets)


def get_daily_history(asset_id, days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{asset_id}/market_chart"
    payload, source = fetch_json_with_cache(
        url,
        params={"vs_currency": VS_CURRENCY, "days": days, "interval": "daily"},
        namespace="coingecko_market_chart",
        cache_key=f"{asset_id}_{VS_CURRENCY}_{days}_daily",
        retries=5,
    )
    prices = [row[1] for row in payload.get("prices", []) if isinstance(row, list) and isinstance(row[1], (int, float))]
    volumes = [row[1] for row in payload.get("total_volumes", []) if isinstance(row, list) and isinstance(row[1], (int, float))]
    return prices, volumes, source


def get_hourly_history(asset_id, days=3):
    url = f"https://api.coingecko.com/api/v3/coins/{asset_id}/market_chart"
    payload, source = fetch_json_with_cache(
        url,
        params={"vs_currency": VS_CURRENCY, "days": days},
        namespace="coingecko_market_chart",
        cache_key=f"{asset_id}_{VS_CURRENCY}_{days}_hourly",
        retries=5,
    )
    prices = [row[1] for row in payload.get("prices", []) if isinstance(row, list) and isinstance(row[1], (int, float))]
    return prices, source


def get_binance_funding(symbol):
    try:
        payload, source = fetch_json_with_cache(
            "https://fapi.binance.com/fapi/v1/premiumIndex",
            params={"symbol": symbol},
            namespace="binance_funding",
            cache_key=f"funding_{symbol}",
            retries=3,
        )
        rate = float(payload.get("lastFundingRate")) * 100.0 if payload.get("lastFundingRate") is not None else None
        mark = float(payload.get("markPrice")) if payload.get("markPrice") is not None else None
        return rate, mark, source
    except Exception:
        return None, None, "unavailable"


def get_binance_orderbook(symbol):
    try:
        payload, source = fetch_json_with_cache(
            "https://api.binance.com/api/v3/depth",
            params={"symbol": symbol, "limit": 100},
            namespace="binance_depth",
            cache_key=f"depth_{symbol}",
            retries=3,
        )
        bids = [(float(p), float(q)) for p, q in payload.get("bids", [])]
        asks = [(float(p), float(q)) for p, q in payload.get("asks", [])]
        return bids, asks, source
    except Exception:
        return [], [], "unavailable"


def analyze_tactical(asset_id, asset_meta):
    daily_prices, daily_volumes, daily_source = get_daily_history(asset_id, days=30)
    hourly_prices, hourly_source = get_hourly_history(asset_id, days=3)

    if len(daily_prices) < 10:
        return None

    current = daily_prices[-1]
    p7 = daily_prices[-8] if len(daily_prices) >= 8 else daily_prices[0]
    p30 = daily_prices[0]
    change_7d = (current / p7 - 1.0) * 100.0
    change_30d = (current / p30 - 1.0) * 100.0

    ema20 = ema(hourly_prices[-80:], 20) if hourly_prices else None
    ema50 = ema(hourly_prices[-120:], 50) if hourly_prices else None
    trend_up = ema20 is not None and ema50 is not None and ema20 > ema50
    trend_down = ema20 is not None and ema50 is not None and ema20 < ema50

    roc_6 = roc(hourly_prices, 6) if hourly_prices else None
    roc_24 = roc(hourly_prices, 24) if hourly_prices else None
    rsi_14 = rsi(hourly_prices[-120:], 14) if hourly_prices else None
    vol_hourly = volatility_pct(hourly_prices[-80:]) if hourly_prices else None

    if vol_hourly is not None and vol_hourly > 2.5:
        regime = "High-Volatility Warning"
    elif trend_up or trend_down:
        regime = "Trend-Following"
    else:
        regime = "Mean-Reversion"

    if trend_up and (roc_24 or 0) > 0:
        vibe = "Aggressive buying detected - trend is currently being respected."
    elif trend_down and (roc_24 or 0) < 0:
        vibe = "Persistent sell pressure - avoid fighting momentum."
    else:
        vibe = "Mixed tape - wait for confirmation before sizing up."

    # CVD proxy from daily close direction * daily volume
    cvd = 0.0
    cvd_points = []
    for i in range(1, min(len(daily_prices), len(daily_volumes))):
        delta = 1.0 if daily_prices[i] > daily_prices[i - 1] else -1.0
        cvd += delta * daily_volumes[i]
        cvd_points.append(cvd)
    cvd_slope = (cvd_points[-1] - cvd_points[0]) / abs(cvd_points[0]) * 100.0 if len(cvd_points) > 2 and cvd_points[0] != 0 else None
    fakeout = change_7d > 0 and (cvd_slope is None or cvd_slope < 0)

    funding_rate, mark_price, funding_source = get_binance_funding(asset_meta["binance"])
    bids, asks, depth_source = get_binance_orderbook(asset_meta["binance"])

    obi = None
    support_zone = None
    target_zone = None
    sell_wall_within_1pct = False
    liquidity_note = "Order book unavailable."

    if bids and asks:
        px = mark_price or current
        low = px * 0.99
        high = px * 1.01
        bid_w = sum(p * q for p, q in bids if p >= low)
        ask_w = sum(p * q for p, q in asks if p <= high)
        total = bid_w + ask_w
        obi = (bid_w / total * 100.0) if total > 0 else None
        max_ask = max((p, q) for p, q in asks if p <= px * 1.015) if any(p <= px * 1.015 for p, _ in asks) else None
        max_bid = max((p, q) for p, q in bids if p >= px * 0.985) if any(p >= px * 0.985 for p, _ in bids) else None
        if max_ask and max_bid:
            support_zone = max_bid[0]
            target_zone = max_ask[0]
        if max_ask and max_ask[0] <= px * 1.01:
            sell_wall_within_1pct = True
        if obi is not None:
            liquidity_note = f"Order-book imbalance is {obi:.1f}% bid-side."

    if regime == "Trend-Following" and trend_up:
        trend = "UPTREND"
    elif regime == "Trend-Following" and trend_down:
        trend = "DOWNTREND"
    else:
        trend = "SIDEWAYS"

    momentum = "STRONG" if (roc_24 is not None and abs(roc_24) > 2.0) else "WEAK"
    volatility = "ELEVATED" if (vol_hourly is not None and vol_hourly > 2.5) else "NORMAL"

    if funding_rate is None:
        leverage_risk = "Funding unavailable; leverage trap signal is limited."
    elif funding_rate > 0.05:
        leverage_risk = "Funding is stretched (Greed Tax high) - long squeeze risk elevated."
    elif funding_rate < -0.03:
        leverage_risk = "Funding is deeply negative - short squeeze risk can spike on rebounds."
    else:
        leverage_risk = "Funding is near neutral - leverage pressure is contained."

    entry_signal = "Neutral / wait"
    if trend == "UPTREND" and not fakeout and not sell_wall_within_1pct:
        entry_signal = "Buy pullbacks"
    elif trend == "DOWNTREND" and funding_rate is not None and funding_rate > 0:
        entry_signal = "Defensive / avoid chasing longs"
    elif fakeout:
        entry_signal = "Fakeout warning"

    support = support_zone if support_zone is not None else min(daily_prices[-7:])
    target = target_zone if target_zone is not None else max(daily_prices[-7:])
    atr_proxy = statistics.mean([abs(hourly_prices[i] - hourly_prices[i - 1]) for i in range(1, len(hourly_prices))]) if len(hourly_prices) > 10 else current * 0.01
    stop_loss = support - atr_proxy if support is not None and atr_proxy is not None else None

    source = daily_source
    if hourly_source == "live" or daily_source == "live":
        source = "live"
    elif hourly_source == "cache" or daily_source == "cache":
        source = "cache"

    return {
        "current": current,
        "change_7d": change_7d,
        "change_30d": change_30d,
        "trend": trend,
        "momentum": momentum,
        "volatility": volatility,
        "regime": regime,
        "vibe": vibe,
        "ema20": ema20,
        "ema50": ema50,
        "roc_6": roc_6,
        "roc_24": roc_24,
        "rsi_14": rsi_14,
        "cvd_slope": cvd_slope,
        "fakeout": fakeout,
        "obi": obi,
        "sell_wall_within_1pct": sell_wall_within_1pct,
        "funding_rate": funding_rate,
        "leverage_risk": leverage_risk,
        "liquidity_note": liquidity_note,
        "support": support,
        "target": target,
        "stop_loss": stop_loss,
        "entry_signal": entry_signal,
        "data_source": source,
        "funding_source": funding_source,
        "depth_source": depth_source,
    }


def generate_report():
    REPORT_DIR.mkdir(exist_ok=True)
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = ["# Short-Term Crypto Tactical Brief\n", f"_Generated automatically - {now}_\n"]

    for asset_id, meta in ASSETS.items():
        s = analyze_tactical(asset_id, meta)
        lines.append(f"## {meta['name']}\n")

        if not s:
            lines.append("Data unavailable due to API limits and no local cache.\n")
            continue

        lines.append(f"- **Current price:** {fmt_price(s['current'])}")
        lines.append(f"- **7D change:** {s['change_7d']:.2f}%")
        lines.append(f"- **30D change:** {s['change_30d']:.2f}%")
        lines.append(f"- **Trend:** **{s['trend']}**")
        lines.append(f"- **Momentum:** **{s['momentum']}**")
        lines.append(f"- **Volatility:** **{s['volatility']}**")
        lines.append(f"- **Data source:** {s['data_source']}\n")

        lines.append("### Status Pulse (30-Second Context)\n")
        lines.append(f"- **Tactical regime:** {s['regime']}")
        lines.append(f"- **The vibe:** {s['vibe']}\n")

        lines.append("### Momentum Engine\n")
        lines.append(f"- **Speedometer (EMA20/EMA50):** {fmt_price(s['ema20'])} / {fmt_price(s['ema50'])}.")
        lines.append(f"- **Velocity (ROC 6h / 24h):** {fmt_pct(s['roc_6'])} / {fmt_pct(s['roc_24'])}.")
        lines.append(f"- **Stamina meter (RSI 14):** {s['rsi_14']:.1f}" if s['rsi_14'] is not None else "- **Stamina meter (RSI 14):** N/A")
        lines.append("")

        lines.append("### Truth Layer (Order Flow & Volume)\n")
        lines.append(f"- **CVD proxy:** {fmt_pct(s['cvd_slope'])}.")
        if s["fakeout"]:
            lines.append("- **Fakeout warning:** Price is rising but CVD proxy is not confirming (low-liquidity pump risk).")
        else:
            lines.append("- **Validation:** Volume proxy is broadly aligned with price direction.")
        lines.append(f"- **Order-book imbalance (OBI):** {fmt_pct(s['obi'])} bid-side." if s["obi"] is not None else "- **Order-book imbalance (OBI):** unavailable.")
        lines.append(f"- **Depth note:** {s['liquidity_note']}\n")

        lines.append("### Trap Detector (Leverage & Liquidity)\n")
        lines.append(f"- **Funding rate (Greed Tax):** {fmt_pct(s['funding_rate'], 4)} (source: {s['funding_source']}).")
        lines.append(f"- **Leverage risk:** {s['leverage_risk']}")
        lines.append("- **Liquidity cluster note:** Nearest large walls are used as tactical zones when available.\n")

        lines.append("### Tactical Levels\n")
        lines.append(f"- **Battle Zone (Support):** {fmt_price(s['support'])}")
        lines.append(f"- **Target (Resistance):** {fmt_price(s['target'])}")
        lines.append(f"- **Stop-loss (ATR proxy):** {fmt_price(s['stop_loss'])}\n")

        lines.append("### Final Entry Signal\n")
        lines.append(f"- **Action:** {s['entry_signal']}")
        lines.append("- **Validation chain:** Trend -> CVD -> Order Book -> Leverage trap.\n")
        lines.append("---\n")

    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    generate_report()
