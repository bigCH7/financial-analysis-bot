import json
from pathlib import Path
import pandas as pd
import numpy as np

DATA_DIR = Path("data")

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

files = sorted(DATA_DIR.glob("raw_*.json"))
if not files:
    print("No data files found")
    exit()

latest_file = files[-1]

with open(latest_file) as f:
    data = json.load(f)

report = []

for asset in data:
    if "history" not in asset:
        continue

    df = pd.DataFrame(asset["history"])
    if "Close" not in df:
        continue

    df["Close"] = df["Close"].astype(float)
    df["MA50"] = df["Close"].rolling(50).mean()
    df["MA200"] = df["Close"].rolling(200).mean()
    df["RSI"] = rsi(df["Close"])

    last = df.iloc[-1]

    long_term = "Bullish" if last["MA50"] > last["MA200"] else "Bearish"
    short_term = (
        "Overbought" if last["RSI"] > 70
        else "Oversold" if last["RSI"] < 30
        else "Neutral"
    )

    report.append({
        "asset": asset.get("ticker", asset.get("id")),
        "price": round(last["Close"], 2),
        "rsi": round(last["RSI"], 2),
        "long_term_outlook": long_term,
        "short_term_signal": short_term
    })

out = DATA_DIR / "analysis_latest.json"
with open(out, "w") as f:
    json.dump(report, f, indent=2)

print("Analysis saved:", out)
