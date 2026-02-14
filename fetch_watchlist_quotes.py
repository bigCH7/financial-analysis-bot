import csv
import io
import json
from datetime import UTC, datetime
from pathlib import Path

from api_utils import fetch_json_with_cache, fetch_text_with_cache

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

WATCHLIST = {
    "spy": {"symbol": "SPY", "name": "S&P 500 ETF", "stooq": "spy.us"},
    "qqq": {"symbol": "QQQ", "name": "Nasdaq 100 ETF", "stooq": "qqq.us"},
    "nvda": {"symbol": "NVDA", "name": "NVIDIA", "stooq": "nvda.us"},
    "gold": {"symbol": "GC=F", "name": "Gold Futures", "stooq": "xauusd"},
    "oil": {"symbol": "CL=F", "name": "Crude Oil Futures", "stooq": "cl.f"},
}


def blank_row(asset_id, meta):
    return {
        "asset": asset_id,
        "symbol": meta["symbol"],
        "name": meta["name"],
        "price": None,
        "change_24h_pct": None,
        "currency": "USD",
        "market_time": None,
        "fetch_source": "unavailable",
    }


def parse_bulk_quote(payload):
    rows = payload.get("quoteResponse", {}).get("result", [])
    return {row.get("symbol"): row for row in rows if row.get("symbol")}


def fetch_chart_quote(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d"
    payload, source = fetch_json_with_cache(
        url,
        namespace="yahoo_chart",
        cache_key=f"chart_{symbol}",
        retries=3,
    )

    result = (payload.get("chart", {}).get("result") or [{}])[0]
    meta = result.get("meta", {})
    close = ((result.get("indicators", {}).get("quote") or [{}])[0]).get("close") or []
    close = [c for c in close if isinstance(c, (int, float))]

    price = meta.get("regularMarketPrice")
    if price is None and close:
        price = close[-1]

    pct = None
    if isinstance(price, (int, float)) and len(close) >= 2 and close[-2]:
        pct = (price / close[-2] - 1) * 100

    return {
        "price": price,
        "change_24h_pct": pct,
        "currency": meta.get("currency") or "USD",
        "market_time": meta.get("regularMarketTime"),
        "fetch_source": f"yahoo_chart_{source}",
    }


def parse_float(text):
    if text in (None, "", "N/D", "-"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def fetch_stooq_quote(stooq_symbol):
    url = f"https://stooq.com/q/l/?s={stooq_symbol}&f=sd2t2ohlcv&h&e=csv"
    text, source = fetch_text_with_cache(
        url,
        namespace="stooq_quote",
        cache_key=f"stooq_{stooq_symbol}",
        retries=3,
    )

    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise RuntimeError(f"No rows returned for {stooq_symbol}")

    row = rows[0]
    close = parse_float(row.get("Close"))
    open_price = parse_float(row.get("Open"))
    pct = None
    if isinstance(close, (int, float)) and isinstance(open_price, (int, float)) and open_price:
        pct = (close / open_price - 1) * 100

    date = (row.get("Date") or "").strip()
    time = (row.get("Time") or "").strip()
    market_time = f"{date} {time}".strip() or None

    return {
        "price": close,
        "change_24h_pct": pct,
        "currency": "USD",
        "market_time": market_time,
        "fetch_source": f"stooq_{source}",
    }


def fetch_quotes():
    symbols = ",".join(item["symbol"] for item in WATCHLIST.values())
    bulk_url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbols}"

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "unavailable",
        "quotes": {},
    }

    for asset_id, meta in WATCHLIST.items():
        out["quotes"][asset_id] = blank_row(asset_id, meta)

    by_symbol = {}
    bulk_source = None

    try:
        payload, source = fetch_json_with_cache(
            bulk_url,
            namespace="yahoo_quote",
            cache_key=f"watchlist_{symbols}",
            retries=3,
        )
        by_symbol = parse_bulk_quote(payload)
        bulk_source = f"yahoo_quote_{source}"
    except Exception as exc:
        print(f"Watchlist bulk quote fallback: {exc}")

    for asset_id, meta in WATCHLIST.items():
        row = by_symbol.get(meta["symbol"], {})
        price = row.get("regularMarketPrice")
        if price is not None:
            out["quotes"][asset_id] = {
                "asset": asset_id,
                "symbol": meta["symbol"],
                "name": meta["name"],
                "price": price,
                "change_24h_pct": row.get("regularMarketChangePercent"),
                "currency": row.get("currency") or "USD",
                "market_time": row.get("regularMarketTime"),
                "fetch_source": bulk_source or "yahoo_quote_unknown",
            }
            continue

        try:
            chart = fetch_chart_quote(meta["symbol"])
            if chart.get("price") is not None:
                out["quotes"][asset_id] = {
                    "asset": asset_id,
                    "symbol": meta["symbol"],
                    "name": meta["name"],
                    "price": chart.get("price"),
                    "change_24h_pct": chart.get("change_24h_pct"),
                    "currency": chart.get("currency") or "USD",
                    "market_time": chart.get("market_time"),
                    "fetch_source": chart.get("fetch_source") or "yahoo_chart_unknown",
                }
                continue
        except Exception:
            pass

        try:
            stooq = fetch_stooq_quote(meta["stooq"])
            if stooq.get("price") is not None:
                out["quotes"][asset_id] = {
                    "asset": asset_id,
                    "symbol": meta["symbol"],
                    "name": meta["name"],
                    "price": stooq.get("price"),
                    "change_24h_pct": stooq.get("change_24h_pct"),
                    "currency": stooq.get("currency") or "USD",
                    "market_time": stooq.get("market_time"),
                    "fetch_source": stooq.get("fetch_source") or "stooq_unknown",
                }
        except Exception:
            pass

    live_sources = {
        q.get("fetch_source")
        for q in out["quotes"].values()
        if q.get("price") is not None and q.get("fetch_source")
    }

    if not live_sources:
        out["source"] = "unavailable"
    elif len(live_sources) == 1:
        out["source"] = next(iter(live_sources))
    else:
        out["source"] = "mixed"

    out_file = DATA_DIR / "watchlist_quotes.json"
    out_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Saved", out_file)


if __name__ == "__main__":
    fetch_quotes()
