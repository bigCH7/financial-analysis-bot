import requests
import time
from pathlib import Path
from datetime import datetime

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

COINGECKO = "https://api.coingecko.com/api/v3"


def safe_get(url, params=None, retries=3):
    for i in range(retries):
        r = requests.get(url, params=params, timeout=20)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            time.sleep(10)
        else:
            r.raise_for_status()
    raise RuntimeError("API rate limit")


def get_global():
    return safe_get(f"{COINGECKO}/global")["data"]


def get_market(asset):
    return safe_get(
        f"{COINGECKO}/coins/{asset}/market_chart",
        params={"vs_currency": "usd", "days": 365}
    )


def valuation(asset):
    data = get_market(asset)
    prices = [p[1] for p in data["prices"]]

    current = prices[-1]
    avg_365 = sum(prices) / len(prices)

    ratio = current / avg_365

    if ratio < 0.8:
        verdict = "Undervalued"
    elif ratio > 1.2:
        verdict = "Overvalued"
    else:
        verdict = "Fairly valued"

    return {
        "current": round(current, 2),
        "average": round(avg_365, 2),
        "ratio": round(ratio, 2),
        "verdict": verdict
    }


def generate_report():
    global_data = get_global()

    btc_dom = global_data["market_cap_percentage"]["btc"]
    eth_dom = global_data["market_cap_percentage"]["eth"]

    btc_val = valuation("bitcoin")
    eth_val = valuation("ethereum")

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    report = f"""# Long-Term Crypto Analysis
_Last updated: {now}_

---

## Macro & Capital Flow
- Bitcoin dominance: **{btc_dom:.2f}%**
- Ethereum dominance: **{eth_dom:.2f}%**

**Interpretation:**  
{"Risk-off environment. Capital consolidating into Bitcoin."
 if btc_dom > 55 else
 "Risk-on environment. Capital rotating into altcoins."}

---

## Valuation Analysis

### Bitcoin (BTC)
- Current price: **${btc_val['current']}**
- 365d average price: **${btc_val['average']}**
- Price / Average ratio: **{btc_val['ratio']}**
- Valuation: **{btc_val['verdict']}**

### Ethereum (ETH)
- Current price: **${eth_val['current']}**
- 365d average price: **${eth_val['average']}**
- Price / Average ratio: **{eth_val['ratio']}**
- Valuation: **{eth_val['verdict']}**

---

_Disclaimer: Educational analysis only. Not financial advice._
"""

    path = REPORT_DIR / "long_term_report.md"
    path.write_text(report, encoding="utf-8")
    print("✅ Long-term valuation report generated")


if __name__ == "__main__":
    generate_report()

