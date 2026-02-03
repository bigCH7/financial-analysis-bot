import requests
import time
from pathlib import Path
from datetime import datetime
import statistics
import sys

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

COINGECKO_BASE = "https://api.coingecko.com/api/v3"


def safe_get(url, params=None, retries=5, delay=10):
    for attempt in range(retries):
        r = requests.get(url, params=params, timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            print("Rate limited. Sleeping...")
            time.sleep(delay * (attempt + 1))
            continue
        r.raise_for_status()
    raise RuntimeError("API rate limit exceeded")


def get_prices(asset_id, days=365):
    data = safe_get(
        f"{COINGECKO_BASE}/coins/{asset_id}/market_chart",
        params={"vs_currency": "usd", "days": days, "interval": "daily"},
    )
    return [p[1] for p in data["prices"]]


def valuation_summary(asset, prices):
    current = prices[-1]
    avg = statistics.mean(prices)
    low = min(prices)
    high = max(prices)

    valuation = "FAIR"
    if current < avg * 0.8:
        valuation = "UNDERVALUED"
    elif current > avg * 1.2:
        valuation = "OVERVALUED"

    return {
        "asset": asset.upper(),
        "current": current,
        "average": avg,
        "low": low,
        "high": high,
        "valuation": valuation,
    }


def generate_markdown(btc, eth):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    return f"""# Long-Term Crypto Valuation Report

_Last updated: {now}_

---

## Bitcoin (BTC)

- Current price: ${btc['current']:,.0f}
- 1Y average price: ${btc['average']:,.0f}
- 1Y low / high: ${btc['low']:,.0f} / ${btc['high']:,.0f}
- **Valuation:** **{btc['valuation']}**

---

## Ethereum (ETH)

- Current price: ${eth['current']:,.0f}
- 1Y average price: ${eth['average']:,.0f}
- 1Y low / high: ${eth['low']:,.0f} / ${eth['high']:,.0f}
- **Valuation:** **{eth['valuation']}**

---

## Interpretation

This valuation compares current price to long-term averages.
It is **not** a trading signal.

- UNDERVALUED → price significantly below long-term mean
- FAIR → within normal historical range
- OVERVALUED → price stretched vs long-term history
"""


def markdown_to_html(md_text):
    html = md_text
    html = html.replace("# ", "<h1>").replace("\n", "</h1>\n", 1)
    html = html.replace("## ", "<h2>").replace("\n", "</h2>\n")
    html = html.replace("- ", "<li>").replace("\n", "</li>\n")
    html = html.replace("**", "<strong>").replace("<strong>", "</strong>", 1)
    html = html.replace("\n\n", "<br><br>")

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Long-Term Crypto Valuation</title>
<style>
body {{
  font-family: Arial, sans-serif;
  max-width: 800px;
  margin: auto;
  padding: 40px;
}}
h1, h2 {{
  border-bottom: 1px solid #ddd;
  padding-bottom: 5px;
}}
</style>
</head>
<body>
{html}
</body>
</html>
"""


def main():
    print("Running long-term valuation...")

    btc_prices = get_prices("bitcoin")
    eth_prices = get_prices("ethereum")

    btc = valuation_summary("btc", btc_prices)
    eth = valuation_summary("eth", eth_prices)

    md = generate_markdown(btc, eth)
    html = markdown_to_html(md)

    md_path = REPORT_DIR / "long_term_report.md"
    html_path = REPORT_DIR / "long_term_report.html"

    md_path.write_text(md, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")

    print("Report generated successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Fatal error:", e)
        sys.exit(1)
