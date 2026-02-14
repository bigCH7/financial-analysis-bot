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

ASSETS = {
    "bitcoin": {"name": "Bitcoin", "symbol": "BTC", "heading": "Bitcoin (BTC)"},
    "ethereum": {"name": "Ethereum", "symbol": "ETH", "heading": "Ethereum (ETH)"},
}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


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
    match = re.search(r"Valuation verdict:\s*\n([^\n]+)", long_section)
    if match:
        return match.group(1).strip()
    match = re.search(r"Relative valuation verdict:\s*\n([^\n]+)", long_section)
    if match:
        return match.group(1).strip()
    return ""


def load_news():
    if not NEWS_FILE.exists():
        return {"generated_at": "", "items": []}
    payload = json.loads(NEWS_FILE.read_text(encoding="utf-8"))
    return {
        "generated_at": payload.get("generated_at", ""),
        "items": payload.get("items", []),
    }


def load_analysis_map():
    if not ANALYSIS_FILE.exists():
        return {}
    rows = json.loads(ANALYSIS_FILE.read_text(encoding="utf-8"))
    return {row.get("asset"): row for row in rows if row.get("asset")}


def filter_news(items, keyword):
    key = keyword.lower()
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


def build_assets():
    short_md = read_text(SHORT_REPORT)
    long_md = read_text(LONG_REPORT)
    news = load_news()
    analysis_map = load_analysis_map()

    first_asset_pos = long_md.find("\n## ")
    macro_markdown = long_md[:first_asset_pos].strip() if first_asset_pos > 0 else ""

    assets_for_index = []

    for asset_id, meta in ASSETS.items():
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

        asset_payload = {
            "asset": asset_id,
            "name": meta["name"],
            "symbol": meta["symbol"],
            "updated_at": datetime.now(UTC).isoformat(),
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
            "news": filter_news(news.get("items", []), asset_id),
        }

        (ASSETS_DIR / f"{asset_id}.json").write_text(
            json.dumps(asset_payload, indent=2), encoding="utf-8"
        )

        assets_for_index.append(
            {
                "asset": asset_id,
                "name": meta["name"],
                "symbol": meta["symbol"],
                "price": asset_payload["price"],
                "indicators": asset_payload["indicators"],
                "valuation": {"verdict": asset_payload["valuation"]["verdict"]},
                "updated_at": asset_payload["updated_at"],
            }
        )

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
