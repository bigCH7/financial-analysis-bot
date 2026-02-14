"""
analysis.py
Generates:
 - data/analysis_latest.json  (machine-friendly)
 - data/report_YYYYMMDD.md    (human-readable markdown report)
"""

import json
from pathlib import Path
from datetime import UTC, datetime
import pandas as pd
import numpy as np

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
TODAY = datetime.now(UTC).strftime("%Y%m%d")

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period, min_periods=1).mean()
    avg_loss = loss.rolling(period, min_periods=1).mean()
    rs = avg_gain / (avg_loss.replace(0, np.nan))
    rs = rs.fillna(0)
    return 100 - (100 / (1 + rs))

def format_currency(x):
    try:
        if abs(x) >= 1e9:
            return f"${x/1e9:.2f}B"
        if abs(x) >= 1e6:
            return f"${x/1e6:.2f}M"
        return f"${x:.2f}"
    except:
        return str(x)

# find latest raw file
raw_files = sorted(DATA_DIR.glob("raw_*.json"))
if not raw_files:
    print("No raw_*.json files found in data/. Run fetch_data.py first.")
    exit(0)

latest_raw = raw_files[-1]
with open(latest_raw) as f:
    raw = json.load(f)

analysis_results = []
md_lines = []
md_lines.append(f"# Daily Financial Report â€” {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}\n")
md_lines.append("_Automatically generated. Not financial advice._\n")

for asset in raw:
    # name keys
    asset_id = asset.get("ticker") or asset.get("id") or asset.get("symbol") or "unknown"
    summary = {"asset": asset_id}

    # If we have history (stocks, commodities)
    if asset.get("history"):
        try:
            df = pd.DataFrame(asset["history"])
            if "Close" not in df.columns:
                raise ValueError("No Close column")
            df["Close"] = pd.to_numeric(df["Close"], errors="coerce").fillna(method="ffill").fillna(method="bfill")
            # compute indicators
            df["MA50"] = df["Close"].rolling(50, min_periods=1).mean()
            df["MA200"] = df["Close"].rolling(200, min_periods=1).mean()
            df["RSI"] = rsi(df["Close"])
            last = df.iloc[-1]

            price = float(last["Close"])
            ma50 = float(last["MA50"])
            ma200 = float(last["MA200"])
            last_rsi = float(last["RSI"])

            # basic textual logic
            long_term = "Bullish" if ma50 > ma200 else "Bearish"
            rsi_label = "Overbought" if last_rsi > 70 else "Oversold" if last_rsi < 30 else "Neutral"

            # strength metric: percent gap between MAs
            if ma200 != 0:
                gap_pct = (ma50 - ma200) / ma200 * 100.0
            else:
                gap_pct = 0.0

            # human suggestion (simple deterministic rules)
            suggestion = "Hold / Watch"
            if long_term == "Bullish" and last_rsi < 70:
                suggestion = "Consider accumulate (long-term)"
            if long_term == "Bearish" and last_rsi > 60:
                suggestion = "Caution / consider reducing exposure"
            if rsi_label == "Oversold" and long_term == "Bullish":
                suggestion = "Potential buying opportunity (oversold in uptrend)"

            # build JSON summary
            summary.update({
                "type": "historical",
                "price": round(price, 2),
                "ma50": round(ma50, 2),
                "ma200": round(ma200, 2),
                "rsi": round(last_rsi, 2),
                "ma_gap_pct": round(gap_pct, 2),
                "long_term_outlook": long_term,
                "short_term_signal": rsi_label,
                "suggestion": suggestion
            })

            # build markdown section
            md_lines.append(f"## {asset_id}")
            md_lines.append(f"- Current price: **{format_currency(price)}**")
            md_lines.append(f"- Long-term (MA50 vs MA200): **{long_term}** (MA50={format_currency(ma50)}, MA200={format_currency(ma200)}, gap={gap_pct:.2f}%)")
            md_lines.append(f"- Short-term (RSI): **{last_rsi:.2f}** â†’ *{rsi_label}*")
            md_lines.append(f"- Quick suggestion: **{suggestion}**")
            md_lines.append("")  # blank line

        except Exception as e:
            summary.update({"error": f"history_parse_error: {str(e)}"})
            md_lines.append(f"## {asset_id}")
            md_lines.append(f"- Error parsing historical data: {e}")
            md_lines.append("")
    else:
        # No history â€” attempt to use market_data (likely crypto)
        md_lines.append(f"## {asset_id} (market-data only)")
        market = asset.get("market_data", {}) or {}
        # Try to fetch usd price
        price = None
        try:
            if isinstance(market.get("current_price"), dict):
                price = market.get("current_price", {}).get("usd")
            else:
                price = market.get("current_price")
        except:
            price = None
        # Try 24h change
        pct24 = market.get("price_change_percentage_24h") or market.get("price_change_percentage_24h_in_currency", {}).get("usd") if isinstance(market.get("price_change_percentage_24h_in_currency"), dict) else None

        # Fallback labels
        if price is None:
            md_lines.append("- Price: not available")
            summary.update({"type": "market", "price": None})
        else:
            md_lines.append(f"- Current price (USD): **{format_currency(price)}**")
            summary.update({"type": "market", "price": round(price, 2)})
            if pct24 is not None:
                md_lines.append(f"- 24h change: **{pct24:.2f}%**")
                summary["pct24"] = round(pct24, 2)
            # simple sentiment
            sentiment = "Neutral"
            if pct24 is not None:
                if pct24 > 5:
                    sentiment = "Strong positive (24h)"
                elif pct24 < -5:
                    sentiment = "Strong negative (24h)"
                elif pct24 > 1:
                    sentiment = "Slight positive"
                elif pct24 < -1:
                    sentiment = "Slight negative"
            md_lines.append(f"- Quick sentiment: *{sentiment}*")
            md_lines.append(f"- Suggestion: *Use longer-term metrics; this uses only public market snapshot.*")
            md_lines.append("")
    analysis_results.append(summary)

# write JSON output
out_json = DATA_DIR / "analysis_latest.json"
with open(out_json, "w") as f:
    json.dump(analysis_results, f, indent=2)

# write markdown report (timestamped)
out_md = DATA_DIR / f"report_{TODAY}.md"
with open(out_md, "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))

# also write a "latest" copy for convenience
(latest_md := DATA_DIR / "report_latest.md").write_text("\n".join(md_lines), encoding="utf-8")

print("Analysis JSON saved:", out_json)
print("Report saved:", out_md)
print("Report latest saved:", latest_md)


