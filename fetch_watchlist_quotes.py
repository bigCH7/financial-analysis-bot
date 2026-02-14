import json
from datetime import UTC, datetime
from pathlib import Path

from api_utils import fetch_json_with_cache

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

WATCHLIST = {
    "spy": {"symbol": "SPY", "name": "S&P 500 ETF"},
    "qqq": {"symbol": "QQQ", "name": "Nasdaq 100 ETF"},
    "nvda": {"symbol": "NVDA", "name": "NVIDIA"},
    "gold": {"symbol": "GC=F", "name": "Gold Futures"},
    "oil": {"symbol": "CL=F", "name": "Crude Oil Futures"},
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
    }


def fetch_quotes():
    symbols = ",".join(item["symbol"] for item in WATCHLIST.values())
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbols}"

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "unavailable",
        "quotes": {},
    }

    for asset_id, meta in WATCHLIST.items():
        out["quotes"][asset_id] = blank_row(asset_id, meta)

    try:
        payload, source = fetch_json_with_cache(
            url,
            namespace="yahoo_quote",
            cache_key=f"watchlist_{symbols}",
            retries=5,
        )

        rows = payload.get("quoteResponse", {}).get("result", [])
        by_symbol = {row.get("symbol"): row for row in rows}
        out["source"] = source

        for asset_id, meta in WATCHLIST.items():
            row = by_symbol.get(meta["symbol"], {})
            out["quotes"][asset_id] = {
                "asset": asset_id,
                "symbol": meta["symbol"],
                "name": meta["name"],
                "price": row.get("regularMarketPrice"),
                "change_24h_pct": row.get("regularMarketChangePercent"),
                "currency": row.get("currency") or "USD",
                "market_time": row.get("regularMarketTime"),
            }
    except Exception as exc:
        print(f"Watchlist quote fetch fallback: {exc}")

    out_file = DATA_DIR / "watchlist_quotes.json"
    out_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Saved", out_file)


if __name__ == "__main__":
    fetch_quotes()
