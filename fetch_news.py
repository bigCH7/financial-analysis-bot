import json
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree

from api_utils import fetch_text_with_cache

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

FEEDS = [
    {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"name": "Cointelegraph", "url": "https://cointelegraph.com/rss"},
]


def parse_items(xml_text, source_name):
    items = []
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return items

    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        if not title or not link:
            continue
        items.append(
            {
                "title": title,
                "link": link,
                "pub_date": pub_date,
                "source": source_name,
            }
        )
    return items


def generate_news_snapshot():
    all_items = []

    for feed in FEEDS:
        try:
            xml_text, source_mode = fetch_text_with_cache(
                feed["url"],
                namespace="news_feed",
                cache_key=feed["url"],
                retries=5,
            )
            parsed = parse_items(xml_text, feed["name"])
            for row in parsed:
                row["fetch_source"] = source_mode
            all_items.extend(parsed)
        except Exception as exc:
            print(f"News feed error for {feed['name']}: {exc}")

    output = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "count": len(all_items),
        "items": all_items[:40],
    }

    out_file = DATA_DIR / "news_latest.json"
    out_file.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print("Saved", out_file)


if __name__ == "__main__":
    generate_news_snapshot()
