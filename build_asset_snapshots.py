import json
import re
from datetime import UTC, datetime
from pathlib import Path

DATA_DIR = Path("data")
ASSETS_DIR = DATA_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

SHORT_REPORT = Path("reports/short_term.md")
LONG_REPORT = Path("reports/long_term_report.md")
NEWS_FILE = DATA_DIR / "news_latest.json"
ANALYSIS_FILE = DATA_DIR / "analysis_latest.json"
WATCHLIST_FILE = DATA_DIR / "watchlist_quotes.json"

CRYPTO_ASSETS = {
    "bitcoin": {
        "name": "Bitcoin",
        "symbol": "BTC",
        "heading": "Bitcoin (BTC)",
        "news_keyword": "bitcoin",
        "details_page": "btc.html",
        "about": {
            "what_it_is": "Bitcoin is a decentralized digital currency with no central issuer.",
            "what_it_represents": "It is often treated as a scarce monetary asset and macro risk barometer.",
            "who_or_what": "It is not a company. It is an open-source network maintained by global participants.",
            "how_it_works": "Transactions are validated by proof-of-work mining and stored on a public blockchain."
        },
    },
    "ethereum": {
        "name": "Ethereum",
        "symbol": "ETH",
        "heading": "Ethereum (ETH)",
        "news_keyword": "ethereum",
        "details_page": "eth.html",
        "about": {
            "what_it_is": "Ethereum is a programmable blockchain platform and the native asset is ETH.",
            "what_it_represents": "It represents usage of smart contracts, DeFi rails, and on-chain applications.",
            "who_or_what": "It is not a company. It is an open protocol supported by developers, validators, and users.",
            "how_it_works": "It runs smart contracts on-chain and secures consensus through proof-of-stake validators."
        },
    },
}

WATCHLIST_ASSETS = {
    "spy": {
        "name": "S&P 500 ETF",
        "symbol": "SPY",
        "news_keyword": "s&p 500",
        "details_page": "asset.html?asset=spy",
        "about": {
            "what_it_is": "SPY is an exchange-traded fund designed to track the S&P 500 Index.",
            "what_it_represents": "It represents broad large-cap U.S. equity market exposure.",
            "who_or_what": "Issued by State Street, it holds a basket of U.S. large-cap stocks.",
            "how_it_works": "Its price follows the index through a portfolio that mirrors S&P 500 constituents."
        },
    },
    "qqq": {
        "name": "Nasdaq 100 ETF",
        "symbol": "QQQ",
        "news_keyword": "nasdaq",
        "details_page": "asset.html?asset=qqq",
        "about": {
            "what_it_is": "QQQ is an ETF that tracks the Nasdaq-100 Index.",
            "what_it_represents": "It represents large non-financial growth companies, especially technology-heavy exposure.",
            "who_or_what": "Issued by Invesco, it holds Nasdaq-100 component stocks.",
            "how_it_works": "Its holdings are rebalanced to follow index methodology and sector concentration rules."
        },
    },
    "nvda": {
        "name": "NVIDIA",
        "symbol": "NVDA",
        "news_keyword": "nvidia",
        "details_page": "asset.html?asset=nvda",
        "about": {
            "what_it_is": "NVIDIA is a semiconductor and computing company focused on GPUs and AI platforms.",
            "what_it_represents": "It represents demand for AI infrastructure, data center compute, and advanced chips.",
            "who_or_what": "Publicly traded U.S. company: NVIDIA Corporation.",
            "how_it_works": "Revenue is driven by GPU hardware and software ecosystems used in AI, gaming, and enterprise compute."
        },
    },
    "gold": {
        "name": "Gold Futures",
        "symbol": "GC=F",
        "news_keyword": "gold",
        "details_page": "asset.html?asset=gold",
        "about": {
            "what_it_is": "GC=F tracks front-month COMEX gold futures pricing.",
            "what_it_represents": "It represents market expectations for gold as a store-of-value and macro hedge.",
            "who_or_what": "It is a commodity futures contract, not a company.",
            "how_it_works": "Futures prices reflect supply-demand, rates, dollar strength, and geopolitical risk sentiment."
        },
    },
    "oil": {
        "name": "Crude Oil Futures",
        "symbol": "CL=F",
        "news_keyword": "oil",
        "details_page": "asset.html?asset=oil",
        "about": {
            "what_it_is": "CL=F tracks front-month WTI crude oil futures pricing.",
            "what_it_represents": "It represents global energy demand, supply constraints, and geopolitical risk premiums.",
            "who_or_what": "It is a commodity futures contract, not a company.",
            "how_it_works": "Futures react to inventory data, production policy, transport bottlenecks, and macro growth expectations."
        },
    },
}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def extract_section(markdown: str, heading: str) -> str:
    marker = f"## {heading}"
    start = markdown.find(marker)
    if start == -1:
        return ""
    rest = markdown[start:]
    next_section = rest.find("\n## ", len(marker))
    return rest if next_section == -1 else rest[:next_section]


def clean_section(markdown: str) -> str:
    cleaned = (markdown or "").strip()
    while cleaned.endswith("---"):
        cleaned = cleaned[:-3].rstrip()
    return cleaned


def parse_money(text: str):
    if not text:
        return None
    cleaned = text.replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_percent(text: str):
    if not text:
        return None
    cleaned = text.replace("%", "").replace("+", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def line_value(section: str, label: str):
    pattern = re.compile(rf"- \*\*{re.escape(label)}:\*\*\s*([^\n]+)", re.IGNORECASE)
    match = pattern.search(section)
    return match.group(1).strip() if match else ""


def infer_verdict(long_section: str):
    match = re.search(r"\*\*Long-term verdict:\*\*\s*([^\n]+)", long_section)
    if match:
        return match.group(1).strip()
    match = re.search(r"Valuation verdict:\s*\n([^\n]+)", long_section)
    if match:
        return match.group(1).strip()
    match = re.search(r"Relative valuation verdict:\s*\n([^\n]+)", long_section)
    if match:
        return match.group(1).strip()
    return ""

def load_news():
    payload = read_json(NEWS_FILE, {"generated_at": "", "items": []})
    return {
        "generated_at": payload.get("generated_at", ""),
        "items": payload.get("items", []),
    }


def load_analysis_map():
    rows = read_json(ANALYSIS_FILE, [])
    return {row.get("asset"): row for row in rows if row.get("asset")}


def load_watchlist_quotes():
    payload = read_json(WATCHLIST_FILE, {"generated_at": "", "source": "unknown", "quotes": {}})
    return {
        "generated_at": payload.get("generated_at", ""),
        "source": payload.get("source", "unknown"),
        "quotes": payload.get("quotes", {}),
    }


def filter_news(items, keyword):
    key = (keyword or "").lower()
    out = []
    for item in items:
        title = (item.get("title") or "").strip()
        if key and key not in title.lower():
            continue
        out.append(
            {
                "title": title,
                "url": item.get("link") or "",
                "published_at": item.get("pub_date") or "",
                "source": item.get("source") or "",
                "fetch_source": item.get("fetch_source") or "",
            }
        )
    return out[:12]


def build_crypto_payload(asset_id, meta, short_md, long_md, analysis_map, news):
    heading = meta["heading"]
    short_section = clean_section(extract_section(short_md, heading))
    long_section = clean_section(extract_section(long_md, heading))

    current_price = parse_money(line_value(short_section, "Current price"))
    change_7d = parse_percent(line_value(short_section, "7D change"))
    change_30d = parse_percent(line_value(short_section, "30D change"))
    trend = line_value(short_section, "Trend").replace("**", "")
    momentum = line_value(short_section, "Momentum").replace("**", "")
    volatility = line_value(short_section, "Volatility").replace("**", "")
    data_source = line_value(short_section, "Data source")

    analysis_row = analysis_map.get(asset_id, {})
    change_24h = analysis_row.get("pct24")

    return {
        "asset": asset_id,
        "name": meta["name"],
        "symbol": meta["symbol"],
        "market_type": "crypto",
        "details_page": meta.get("details_page"),
        "updated_at": datetime.now(UTC).isoformat(),
        "about": meta.get("about", {}),
        "source": {
            "short_term": data_source or "unknown",
            "news_generated_at": news.get("generated_at", ""),
        },
        "price": {
            "current_usd": current_price,
            "change_24h_pct": change_24h,
            "change_7d_pct": change_7d,
            "change_30d_pct": change_30d,
        },
        "indicators": {
            "trend": trend,
            "momentum": momentum,
            "volatility": volatility,
        },
        "valuation": {
            "verdict": infer_verdict(long_section),
            "long_term_markdown": long_section,
        },
        "analysis_markdown": f"{long_section}\n\n---\n\n### Short-Term Context\n\n{short_section}",
        "news": filter_news(news.get("items", []), meta.get("news_keyword", asset_id)),
    }


def classify_move(pct):
    if pct is None:
        return "SIDEWAYS"
    if pct > 1.0:
        return "UPTREND"
    if pct < -1.0:
        return "DOWNTREND"
    return "SIDEWAYS"


def build_watchlist_payload(asset_id, meta, quotes, news, long_md):
    q = quotes.get(asset_id, {})
    change_24h = q.get("change_24h_pct")
    trend = classify_move(change_24h)

    heading = f"{meta['name']} ({meta['symbol']})"
    long_section = clean_section(extract_section(long_md, heading))
    verdict = infer_verdict(long_section)

    summary_lines = [
        f"## {meta['name']} ({meta['symbol']})",
        "",
        "### Short-Term Context",
        "",
        f"- **Current price:** ${q.get('price') if q.get('price') is not None else 'N/A'}",
        f"- **24H change:** {change_24h:.2f}%" if isinstance(change_24h, (int, float)) else "- **24H change:** N/A",
        f"- **Trend:** **{trend}**",
        f"- **Data source:** {q.get('fetch_source') or 'unknown'}",
    ]

    if long_section:
        analysis_markdown = f"{long_section}\n\n---\n\n" + "\n".join(summary_lines)
    else:
        analysis_markdown = "\n".join(summary_lines + ["- **Coverage:** long-term model unavailable in latest run"]) 

    return {
        "asset": asset_id,
        "name": meta["name"],
        "symbol": meta["symbol"],
        "market_type": "traditional",
        "details_page": meta.get("details_page"),
        "updated_at": datetime.now(UTC).isoformat(),
        "about": meta.get("about", {}),
        "source": {
            "short_term": q.get("fetch_source") or "unknown",
            "news_generated_at": news.get("generated_at", ""),
        },
        "price": {
            "current_usd": q.get("price"),
            "change_24h_pct": change_24h,
            "change_7d_pct": None,
            "change_30d_pct": None,
        },
        "indicators": {
            "trend": trend,
            "momentum": "N/A",
            "volatility": "N/A",
        },
        "valuation": {
            "verdict": verdict or "Snapshot only",
            "long_term_markdown": long_section,
        },
        "analysis_markdown": analysis_markdown,
        "news": filter_news(news.get("items", []), meta.get("news_keyword", meta["name"])),
    }

def index_entry(payload):
    return {
        "asset": payload["asset"],
        "name": payload["name"],
        "symbol": payload["symbol"],
        "market_type": payload.get("market_type", "unknown"),
        "details_page": payload.get("details_page"),
        "price": payload["price"],
        "indicators": payload["indicators"],
        "valuation": {"verdict": payload.get("valuation", {}).get("verdict", "")},
        "updated_at": payload["updated_at"],
        "source": {"short_term": payload.get("source", {}).get("short_term", "unknown")},
    }


def build_assets():
    short_md = read_text(SHORT_REPORT)
    long_md = read_text(LONG_REPORT)
    news = load_news()
    analysis_map = load_analysis_map()
    watchlist = load_watchlist_quotes()
    watchlist_quotes = watchlist.get("quotes", {})

    first_asset_pos = long_md.find("\n## ")
    macro_markdown = long_md[:first_asset_pos].strip() if first_asset_pos > 0 else ""

    assets_for_index = []

    for asset_id, meta in CRYPTO_ASSETS.items():
        payload = build_crypto_payload(asset_id, meta, short_md, long_md, analysis_map, news)
        (ASSETS_DIR / f"{asset_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        assets_for_index.append(index_entry(payload))

    for asset_id, meta in WATCHLIST_ASSETS.items():
        payload = build_watchlist_payload(asset_id, meta, watchlist_quotes, news, long_md)
        (ASSETS_DIR / f"{asset_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        assets_for_index.append(index_entry(payload))

    overview_news = filter_news(news.get("items", []), "")[:10]

    index_payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "macro_markdown": macro_markdown,
        "assets": assets_for_index,
        "overview_news": overview_news,
    }

    (ASSETS_DIR / "index.json").write_text(json.dumps(index_payload, indent=2), encoding="utf-8")
    print("Saved", ASSETS_DIR / "index.json")


if __name__ == "__main__":
    build_assets()

