import requests
import pandas as pd
from datetime import datetime

# -----------------------------
# Configuration
# -----------------------------
ASSETS = {
    "bitcoin": "bitcoin",
    "ethereum": "ethereum"
}

DAYS = 365  # 1 year of daily data
OUTPUT_FILE = "data/analysis_longterm.md"


# -----------------------------
# Helpers
# -----------------------------
def fetch_price_history(coin_id, days):
    url = (
        f"https://api.coingecko.com/api/v3/coins/"
        f"{coin_id}/market_chart"
        f"?vs_currency=usd&days={days}&interval=daily"
    )
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    prices = data["prices"]
    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


def classify_regime(df):
    df["ma200"] = df["price"].rolling(200).mean()

    latest = df.iloc[-1]
    prev = df.iloc[-30]  # ~1 month slope

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

    return {
        "price": price,
        "ma200": ma200,
        "slope_pct": slope * 100,
        "distance_pct": distance,
        "regime": regime
    }


# -----------------------------
# Main
# -----------------------------
def main():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = []
    lines.append(f"# Long-Term Market Regime Report\n")
    lines.append(f"_Generated: {now}_\n")
    lines.append("_Methodology: 200-day trend, slope, and relative positioning._\n")

    for name, coin_id in ASSETS.items():
        df = fetch_price_history(coin_id, DAYS)
        stats = classify_regime(df)

        lines.append(f"## {name.capitalize()}")
        lines.append(f"- Current price: **${stats['price']:.2f}**")
        lines.append(f"- 200-day average: **${stats['ma200']:.2f}**")
        lines.append(f"- Trend slope (30d): **{stats['slope_pct']:.2f}%**")
        lines.append(f"- Distance from trend: **{stats['distance_pct']:.2f}%**")
        lines.append(f"- **Long-term regime:** **{stats['regime']}**\n")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
