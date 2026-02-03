import requests
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from datetime import datetime, timedelta


def get_price_30d_change(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": 30,
        "interval": "daily"
    }
    data = requests.get(url, params=params, timeout=20).json()
    prices = data["prices"]

    start_price = prices[0][1]
    end_price = prices[-1][1]

    return round(((end_price - start_price) / start_price) * 100, 2)


def get_market_dominance():
    url = "https://api.coingecko.com/api/v3/global"
    data = requests.get(url, timeout=20).json()
    market = data["data"]["market_cap_percentage"]

    return round(market["btc"], 2), round(market["eth"], 2)


def get_macro_context():
    btc_dom, eth_dom = get_market_dominance()
    btc_30d = get_price_30d_change("bitcoin")
    eth_30d = get_price_30d_change("ethereum")
    eth_vs_btc = round(eth_30d - btc_30d, 2)

def get_price_history(coin_id, days=200):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily"
    }
    data = requests.get(url, params=params, timeout=20).json()
    prices = [p[1] for p in data["prices"]]
    return prices


def valuation_assessment(coin_id, relative_strength=0):
    prices = get_price_history(coin_id, days=200)
    current_price = prices[-1]
    long_term_avg = sum(prices) / len(prices)

    deviation_pct = ((current_price - long_term_avg) / long_term_avg) * 100

    score = 50  # neutral base

    # Price deviation logic
    if deviation_pct < -15:
        score += 20
        label = "Undervalued"
    elif deviation_pct > 20:
        score -= 20
        label = "Overextended"
    else:
        label = "Neutral"

    # Relative strength adjustment (ETH vs BTC)
    score += int(relative_strength / 2)

    score = max(0, min(100, score))

    return {
        "current_price": round(current_price, 2),
        "long_term_avg": round(long_term_avg, 2),
        "deviation_pct": round(deviation_pct, 2),
        "valuation_label": label,
        "valuation_score": score
    }

    if btc_dom > 50 and eth_vs_btc < 0:
        interpretation = (
            "Risk-off environment. Capital consolidating into Bitcoin. "
            "Investors favor store-of-value over growth."
        )
    elif eth_vs_btc > 0:
        interpretation = (
            "Risk-on signals emerging. Capital rotating into Ethereum and higher-beta assets."
        )
    else:
        interpretation = (
            "Neutral macro regime. No strong long-term capital preference."
        )

    return {
        "btc_dominance": btc_dom,
        "eth_dominance": eth_dom,
        "btc_30d": btc_30d,
        "eth_30d": eth_30d,
        "eth_vs_btc_30d": eth_vs_btc,
        "macro_interpretation": interpretation
    }


# -----------------------------
# Configuration
# -----------------------------
ASSETS = {
    "bitcoin": "bitcoin",
    "ethereum": "ethereum"
}

DAYS = 365
OUTPUT_FILE = "data/analysis_longterm.md"


# -----------------------------
# Data Fetching
# -----------------------------
def fetch_price_history(coin_id, days):
    url = (
        f"https://api.coingecko.com/api/v3/coins/"
        f"{coin_id}/market_chart"
        f"?vs_currency=usd&days={days}&interval=daily"
    )
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    prices = r.json()["prices"]

    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


# -----------------------------
# Regime Analysis
# -----------------------------
def classify_regime(df):
    df["ma200"] = df["price"].rolling(200).mean()

    latest = df.iloc[-1]
    prev = df.iloc[-30]

    price = latest["price"]
    ma200 = latest["ma200"]
    slope = (latest["ma200"] - prev["ma200"]) / prev["ma200"]

    if price > ma200 and slope > 0:
        regime = "Bullish"
    elif price < ma200 and slope < 0:
        regime = "Bearish"
    else:
        regime = "Neutral / Transition"

    distance = (price - ma200) / ma200 * 100 if ma200 else 0

    return regime, price, ma200, slope * 100, distance


# -----------------------------
# Risk & Drawdown Analysis
# -----------------------------
def risk_metrics(df):
    df["returns"] = df["price"].pct_change()

    volatility = df["returns"].std() * np.sqrt(365)

    cumulative = (1 + df["returns"]).cumprod()
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak

    max_dd = drawdown.min() * 100

    if volatility < 50:
        risk_class = "Low"
    elif volatility < 80:
        risk_class = "Medium"
    else:
        risk_class = "High"

    return volatility, max_dd, risk_class


# -----------------------------
# Relative Valuation vs History
# -----------------------------
def valuation_metrics(df):
    mean_price = df["price"].mean()
    std_price = df["price"].std()
    latest_price = df["price"].iloc[-1]

    z_score = (latest_price - mean_price) / std_price

    if z_score < -1:
        valuation = "Compressed (Below historical norm)"
    elif z_score > 1:
        valuation = "Stretched (Above historical norm)"
    else:
        valuation = "Neutral (Near historical norm)"

    return z_score, valuation


# -----------------------------
# Main
# -----------------------------
def main():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = []
    lines.append("# Long-Term Market Analysis\n")
    lines.append(f"_Generated: {now}_\n")
    lines.append("_Methodology: Regime + risk + valuation vs historical behavior._\n")

    for name, coin_id in ASSETS.items():
        df = fetch_price_history(coin_id, DAYS)

        regime, price, ma200, slope, distance = classify_regime(df)
        vol, max_dd, risk_class = risk_metrics(df)
        z_score, valuation = valuation_metrics(df)

        lines.append(f"## {name.capitalize()}")

        lines.append("### Market Regime")
        lines.append(f"- Current price: **${price:.2f}**")
        lines.append(f"- 200-day average: **${ma200:.2f}**")
        lines.append(f"- Trend slope (30d): **{slope:.2f}%**")
        lines.append(f"- Distance from trend: **{distance:.2f}%**")
        lines.append(f"- **Long-term regime:** **{regime}**\n")

        lines.append("### Risk Profile")
        lines.append(f"- Annualized volatility: **{vol:.2f}%**")
        lines.append(f"- Max drawdown (1y): **{max_dd:.2f}%**")
        lines.append(f"- **Professional risk class:** **{risk_class}**\n")

        lines.append("### Relative Valuation (Self-Historical)")
        lines.append(f"- Z-score vs 1y history: **{z_score:.2f}**")
        lines.append(f"- **Valuation state:** **{valuation}**\n")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()

def main():
    report = ""

    # ---- MACRO CONTEXT ----
    macro = get_macro_context()

    report += "==============================\n"
    report += "LONG-TERM CRYPTO MACRO ANALYSIS\n"
    report += "==============================\n\n"

    report += "Macro & Capital Flow Context\n"
    report += f"- Bitcoin dominance: {macro['btc_dominance']}%\n"
    report += f"- Ethereum dominance: {macro['eth_dominance']}%\n"
    report += f"- BTC 30d performance: {macro['btc_30d']}%\n"
    report += f"- ETH 30d performance: {macro['eth_30d']}%\n"
    report += f"- ETH vs BTC (30d): {macro['eth_vs_btc_30d']}%\n\n"
    report += f"Interpretation: {macro['macro_interpretation']}\n"

    print(report)


if __name__ == "__main__":
     btc_val = valuation_assessment("bitcoin")
    eth_val = valuation_assessment("ethereum", macro["eth_vs_btc_30d"])

    report += "\nVALUATION ANALYSIS\n"
    report += "------------------\n"

    report += (
        f"Bitcoin:\n"
        f"- Price vs 200d avg: {btc_val['deviation_pct']}%\n"
        f"- Valuation: {btc_val['valuation_label']}\n"
        f"- Valuation score: {btc_val['valuation_score']}/100\n\n"
    )

    report += (
        f"Ethereum:\n"
        f"- Price vs 200d avg: {eth_val['deviation_pct']}%\n"
        f"- Valuation: {eth_val['valuation_label']}\n"
        f"- Valuation score: {eth_val['valuation_score']}/100\n"
    )

    main()
