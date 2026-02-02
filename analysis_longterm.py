# analysis_longterm.py
"""
Long-term analysis module.
Produces:
 - data/longterm_analysis.json  (structured scores & metric values)
 - docs/report_longterm.md     (human-readable explanation for GitHub Pages)
 - docs/report_longterm_latest.md (convenience copy)
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


def safe_get(d, *keys, default=None):
    """Try several keys from a dict; return first non-None."""
    if not isinstance(d, dict):
        return default
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def percentile_series(series):
    """Return percentile rank 0..1 for each value, preserving index."""
    s = series.copy()
    s = s.replace([np.inf, -np.inf], np.nan)
    # If all NaN, return series of NaN
    if s.notna().sum() == 0:
        return pd.Series([np.nan] * len(s), index=s.index)
    return s.rank(pct=True, method="max")


def compute_metrics_for_stock(asset):
    """
    asset: dict from fetcher for stocks (has 'history' and 'info').
    Returns dict of computed metrics (raw numbers).
    """
    info = asset.get("info", {}) or {}
    hist = asset.get("history", []) or []
    out = {"asset": asset.get("ticker") or asset.get("symbol") or "unknown"}
    # price from last close
    price = None
    try:
        if hist:
            dfh = pd.DataFrame(hist)
            if "Close" in dfh.columns:
                price = float(pd.to_numeric(dfh["Close"], errors="coerce").iloc[-1])
    except Exception:
        price = None
    out["price"] = price

    # fundamental fields (many names depending on provider)
    pe = safe_get(info, "trailingPE", "trailing_pe", "trailing_pe_ratio")
    if pe is None:
        # try alternate keys some providers use
        pe = safe_get(info, "forwardPE", default=None)
    pb = safe_get(info, "priceToBook", "priceToBookMRQ", default=None)
    trailing_eps = safe_get(info, "trailingEps", "epsTrailingTwelveMonths", default=None)
    book_value = safe_get(info, "bookValue", default=None)
    market_cap = safe_get(info, "marketCap", default=None)
    roe = safe_get(info, "returnOnEquity", "returnOnEquityMRQ", default=None)
    dividend_yield = safe_get(info, "dividendYield", default=None)
    debt_to_equity = safe_get(info, "debtToEquity", "debtToEquityMRQ", default=None)
    current_ratio = safe_get(info, "currentRatio", default=None)
    eps_growth = safe_get(info, "earningsQuarterlyGrowth", default=None)

    # coerce numeric where possible
    def to_num(x):
        try:
            if x is None:
                return None
            return float(x)
        except Exception:
            return None

    out.update({
        "pe": to_num(pe),
        "pb": to_num(pb),
        "trailing_eps": to_num(trailing_eps),
        "book_value": to_num(book_value),
        "market_cap": to_num(market_cap),
        "roe": to_num(roe),
        "dividend_yield": to_num(dividend_yield),
        "debt_to_equity": to_num(debt_to_equity),
        "current_ratio": to_num(current_ratio),
        "eps_growth": to_num(eps_growth),
    })

    # momentum: 1y pct change if history covers ~250 trading days
    try:
        if hist:
            df = pd.DataFrame(hist)
            if "Close" in df.columns:
                df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
                if len(df) >= 252:
                    price_1y_ago = df["Close"].iloc[-252]
                    if price_1y_ago and out["price"]:
                        out["pct_1y"] = float((out["price"] - price_1y_ago) / price_1y_ago * 100.0)
                    else:
                        out["pct_1y"] = None
                else:
                    out["pct_1y"] = None
            else:
                out["pct_1y"] = None
        else:
            out["pct_1y"] = None
    except Exception:
        out["pct_1y"] = None

    return out


def build_scores(stock_metrics_list):
    df = pd.DataFrame(stock_metrics_list).set_index("asset")

    # metrics and whether higher is better
    metric_info = {
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

    # percentiles
    percentiles = {}
    for m, higher_is_better in metric_info.items():
        if m in df.columns:
            col = df[m].astype(float)
            # if there are no valid values, produce NaNs
            if col.notna().sum() == 0:
                percentiles[m] = pd.Series([np.nan] * len(df), index=df.index)
                continue
            p = percentile_series(col)
            if not higher_is_better:
                p = 1.0 - p
            percentiles[m] = p

    pct_df = pd.DataFrame(percentiles)

    # category grouping
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

    # weights (tweakable)
    weights = {
        "valuation": 0.25,
        "growth": 0.30,
        "profitability": 0.15,
        "health": 0.20,
        "momentum": 0.10
    }

    combined = pd.Series(0.0, index=cat_df.index)
    denom = 0.0
    for c, w in weights.items():
        if c in cat_df.columns:
            col = cat_df[c].fillna(cat_df[c].mean() if cat_df[c].notna().any() else 0.5)
            combined += col * w
            denom += w

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
            val = category_scores[c].get(asset, np.nan)
            item["category_scores"][c] = (None if pd.isna(val) else round(float(val) * 100.0, 2))
        # raw metrics
        raw = df.loc[asset].to_dict()
        cleaned_raw = {}
        for k, v in raw.items():
            if pd.isna(v):
                cleaned_raw[k] = None
            else:
                try:
                    if isinstance(v, (int, float, np.floating, np.integer)):
                        cleaned_raw[k] = float(round(v, 6))
                    else:
                        cleaned_raw[k] = v
                except:
                    cleaned_raw[k] = v
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
        cats = r.get("category_scores", {})
        if cats:
            # show top 2 categories
            top = sorted(cats.items(), key=lambda x: (x[1] or 0), reverse=True)[:2]
            for name, val in top:
                if val is not None:
                    lines.append(f"- {name.capitalize()} score: **{val}%**")
        raw = r.get("raw_metrics", {})
        if raw:
            # show selective raw metrics for transparency
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

    # select only stocks
    stocks = [a for a in raw if a.get("type") == "stock"]

    if not stocks:
        print("No stocks found in raw data; nothing to score.")
        return

    metrics_list = []
    for s in stocks:
        try:
            m = compute_metrics_for_stock(s)
            metrics_list.append(m)
        except Exception as e:
            print("Error computing metrics for", s.get("ticker") or s.get("id"), e)

    if not metrics_list:
        print("No valid metrics computed.")
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

    # latest convenience copy
    (DOCS_DIR / "report_longterm_latest.md").write_text(md, encoding="utf-8")

    print("Long-term analysis saved:", out_json, out_md)


if __name__ == "__main__":
    main()
