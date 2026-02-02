# analysis_longterm.py
"""
Long-term analysis module.
Produces:
 - data/longterm_analysis.json  (structured scores & metric values)
 - docs/report_longterm.md     (human-readable explanation for GitHub Pages)
"""

import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

DATA_DIR = Path("data")
DOCS_DIR = Path("docs")
DOCS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

TODAY_TS = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
 TODAY_DATE = datetime.utcnow().strftime("%Y%m%d")

def safe_get(d, key, default=None):
    return d.get(key, default) if isinstance(d, dict) else default

def percentile_series(series):
    # return percentile rank 0..1 for each value, NaNs preserved
    return series.rank(pct=True, method="max")

def compute_metrics_for_stock(asset):
    """
    asset: dict from fetcher for stocks (has 'history' and 'info').
    Returns dict of computed metrics (raw numbers).
    """
    info = asset.get("info", {}) or {}
    hist = asset.get("history", []) or []
    out = {"asset": asset.get("ticker")}
    # price from last close
    price = None
    try:
        if hist:
            price = float(pd.DataFrame(hist)["Close"].astype(float).iloc[-1])
    except Exception:
        price = None
    out["price"] = price

    # fundamental fields (many names depending on provider)
    pe = safe_get(info, "trailingPE") or safe_get(info, "forwardPE") or None
    pb = safe_get(info, "priceToBook") or None
    trailing_eps = safe_get(info, "trailingEps") or safe_get(info, "epsTrailingTwelveMonths") or None
    book_value = safe_get(info, "bookValue") or None
    market_cap = safe_get(info, "marketCap") or None
    roe = safe_get(info, "returnOnEquity") or safe_get(info, "roe") or None
    dividend_yield = safe_get(info, "dividendYield") or None
    debt_to_equity = safe_get(info, "debtToEquity") or safe_get(info, "debtToEquityRatio") or None
    current_ratio = safe_get(info, "currentRatio") or None
    eps_growth = safe_get(info, "earningsQuarterlyGrowth") or None
    # some providers use decimals for percentages; normalize if needed
    try:
        if isinstance(roe, str):
            roe = float(roe)
    except:
        pass

    out.update({
        "pe": float(pe) if pe is not None else None,
        "pb": float(pb) if pb is not None else None,
        "trailing_eps": float(trailing_eps) if trailing_eps is not None else None,
        "book_value": float(book_value) if book_value is not None else None,
        "market_cap": float(market_cap) if market_cap is not None else None,
        "roe": float(roe) if roe is not None else None,
        "dividend_yield": float(dividend_yield) if dividend_yield is not None else None,
        "debt_to_equity": float(debt_to_equity) if debt_to_equity is not None else None,
        "current_ratio": float(current_ratio) if current_ratio is not None else None,
        "eps_growth": float(eps_growth) if eps_growth is not None else None
    })

    # momentum: 1y and 3y percentage change if history covers it
    try:
        df = pd.DataFrame(hist)
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        if len(df) >= 250:
            price_1y_ago = df["Close"].iloc[-250]
            out["pct_1y"] = (out["price"] - price_1y_ago) / price_1y_ago * 100.0
        else:
            out["pct_1y"] = None
    except Exception:
        out["pct_1y"] = None

    return out

def build_scores(stock_metrics_list):
    df = pd.DataFrame(stock_metrics_list).set_index("asset")

    # choose metrics and mark whether higher is better
    metric_info = {
        # metric_name: higher_is_better (True/False)
        "pe": False,
        "pb": False,
        "trailing_eps": True,
        "eps_growth": True,
        "roe": True,
        "dividend_yield": True,
        "debt_to_equity": False,
        "current_ratio": True,
        "pct_1y": True
    }

    # compute percentile ranks for each available metric
    percentiles = {}
    for m, higher_is_better in metric_info.items():
        if m in df.columns:
            col = df[m]
            # treat inf / -inf as NaN
            col = col.replace([np.inf, -np.inf], np.nan)
            # If metric mostly missing, skip
            if col.notna().sum() < 1:
                percentiles[m] = pd.Series([np.nan] * len(df), index=df.index)
                continue
            p = percentile_series(col.fillna(np.nan))
            # invert if lower is better
            if not higher_is_better:
                p = 1.0 - p
            percentiles[m] = p

    pct_df = pd.DataFrame(percentiles)

    # Now define category scores as average of relevant percentiles
    categories = {
        "valuation": ["pe", "pb"],
        "growth": ["trailing_eps", "eps_growth"],
        "profitability": ["roe", "dividend_yield"],
        "health": ["debt_to_equity", "current_ratio"],
        "momentum": ["pct_1y"]
    }

    category_scores = {}
    for cat, metrics in categories.items():
        available = [m for m in metrics if m in pct_df.columns]
        if not available:
            category_scores[cat] = pd.Series([np.nan] * len(df), index=df.index)
            continue
        category_scores[cat] = pct_df[available].mean(axis=1, skipna=True)

    cat_df = pd.DataFrame(category_scores)

    # weights
    weights = {
        "valuation": 0.25,
        "growth": 0.30,
        "profitability": 0.15,
        "health": 0.20,
        "momentum": 0.10
    }

    # compute combined score 0..100
    combined = pd.Series(0.0, index=cat_df.index)
    denom = 0.0
    for c, w in weights.items():
        if c in cat_df.columns:
            # fill NaN with category mean to be conservative
            cat_vals = cat_df[c].fillna(cat_df[c].mean() if cat_df[c].notna().any() else 0.5)
            combined += cat_vals * w
            denom += w

    # normalize to 0..100
    if denom > 0:
        combined = combined / denom * 100.0
    else:
        combined = combined * 0.0

    results = []
    for asset in df.index:
        item = {
            "asset": asset,
            "price": df.at[asset, "price"] if "price" in df.columns else None,
            "category_scores": {},
            "combined_score": round(float(combined[asset]), 2)
        }
        for c in category_scores:
            item["category_scores"][c] = round(float(category_scores[c].get(asset, np.nan)) * 100.0, 2) if not pd.isna(category_scores[c].get(asset, np.nan)) else None

        # also include key raw metrics for transparency
        raw = df.loc[asset].to_dict()
        cleaned_raw = {k: (None if (pd.isna(v)) else (round(float(v), 4) if isinstance(v, (int, float, np.floating)) else v)) for k, v in raw.items()}
        item["raw_metrics"] = cleaned_raw

        results.append(item)

    return results

def label_from_score(score):
    if score is None:
        return "No score"
    if score >= 80:
        return "Strong Buy"
    if score >= 60:
        return "Buy / Accumulate"
    if score >= 40:
        return "Hold / Neutral"
    if score >= 20:
        return "Caution"
    return "Avoid"

def generate_markdown_report(results):
    lines = []
    lines.append(f"# Long-term Analysis — {TODAY_TS}\n")
    lines.append("_Automatically generated. Not financial advice._\n")

    for r in results:
        label = label_from_score(r.get("combined_score"))
        lines.append(f"## {r['asset']} — **{label}** (score: {r['combined_score']}/100)")
        price = r.get("price")
        if price is not None:
            lines.append(f"- Current price: **${price:,.2f}**")
        # show top category reasons
        cats = r.get("category_scores", {})
        top_cat = max(cats.items(), key=lambda x: (x[1] or 0))[0] if cats else None
        lines.append(f"- Highest contributing category: **{top_cat}**" if top_cat else "- No category data available")
        # show raw metrics summary
        raw = r.get("raw_metrics", {})
        if raw:
            # keep a few highlighted metrics
            for key in ["pe", "pb", "roe", "eps_growth", "dividend_yield", "debt_to_equity", "current_ratio", "pct_1y"]:
                val = raw.get(key)
                if val is not None:
                    lines.append(f"- {key}: `{val}`")
        lines.append(f"- Quick take: {label}. See raw metrics above for details.")
        lines.append("")  # blank line

    return "\n".join(lines)

def main():
    # discover latest raw JSON created by fetcher
    raw_files = sorted(DATA_DIR.glob("raw_*.json"))
    if not raw_files:
        print("No raw files found in data/. Run fetch_data.py first.")
        return
    raw = json.load(open(raw_files[-1], "r", encoding="utf-8"))

    # only consider stocks for long-term scoring (crypto/commodities separate)
    stocks = [a for a in raw if a.get("type") == "stock"]

    metrics_list = []
    for s in stocks:
        try:
            m = compute_metrics_for_stock(s)
            metrics_list.append(m)
        except Exception as e:
            print("Error computing metrics for", s.get("ticker"), e)

    if not metrics_list:
        print("No stock metrics to score.")
        return

    scored = build_scores(metrics_list)

    # write JSON
    out_json = DATA_DIR / "longterm_analysis.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(scored, f, indent=2)

    # write markdown for docs (so Pages can render)
    md = generate_markdown_report(scored)
    out_md = DOCS_DIR / "report_longterm.md"
    out_md.write_text(md, encoding="utf-8")

    # write convenience latest pointer
    (DOCS_DIR / "report_longterm_latest.md").write_text(md, encoding="utf-8")

    print("Long-term analysis saved:", out_json, out_md)

if __name__ == "__main__":
    main()
