import requests
import pandas as pd
import numpy as np
from datetime import datetime

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

