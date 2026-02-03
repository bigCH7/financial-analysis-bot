import requests
import datetime
import statistics

# -----------------------------
# CONFIG
# -----------------------------
ASSETS = {
    "bitcoin": "btc",
    "ethereum": "eth"
}

COINGECKO_API = "https://api.coingecko.com/api/v3"


# -----------------------------
# DATA FETCHING
# -----------------------------
def get_market_data(asset_id):
    url = f"{COINGECKO_API}/coins/{asset_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": "365",
        "interval": "daily"
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()["prices"]


def get_global_data():
    url = f"{COINGECKO_API}/global"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()["data"]


# -----------------------------
# MACRO ANALYSIS
# -----------------------------
def get_macro_context():
    global_data = get_global_data()

    btc_dom = round(global_data["market_cap_percentage"]["btc"], 2)
    eth_dom = round(global_data["market_cap_percentage"]["eth"], 2)

    btc_prices = get_market_data("bitcoin")
    eth_prices = get_market_data("ethereum")

    btc_30d = performance_pct(btc_prices, 30)
    eth_30d = performance_pct(eth_prices, 30)
    eth_vs_btc = round(eth_30d - btc_30d, 2)

    if btc_dom > 55 and eth_vs_btc < 0:
        interpretation = (
            "Risk-off environment. Capital consolidating into Bitcoin. "
            "Investors favor store-of-value over growth."
        )
    else:
        interpretation = (
            "Risk-on or neutral environment. Capital rotating into higher-beta assets."
        )

    return {
        "btc_dominance": btc_dom,
        "eth_dominance": eth_dom,
        "btc_30d": btc_30d,
        "eth_30d": eth_30d,
        "eth_vs_btc_30d": eth_vs_btc,
        "interpretation": interpretation
    }


# -----------------------------
# VALUATION ANALYSIS (CRYPTO-ADAPTED)
# -----------------------------
def valuation_assessment(asset_id):
    prices = get_market_data(asset_id)
    closes = [p[1] for p in prices]

    current_price = closes[-1]
    avg_200d = statistics.mean(closes[-200:])

    deviation_pct = round(((current_price - avg_200d) / avg_200d) * 100, 2)

    # Crypto valuation logic (relative, not absolute like P/E)
    if deviation_pct < -20:
        label = "Deeply Undervalued"
        score = 80
    elif deviation_pct < -10:
        label = "Undervalued"
        score = 70
    elif deviation_pct < 10:
        label = "Fairly Valued"
        score = 50
    elif deviation_pct < 25:
        label = "Overvalued"
        score = 35
    else:
        label = "Highly Overvalued"
        score = 20

    return {
        "current_price": round(current_price, 2),
        "avg_200d": round(avg_200d, 2),
        "deviation_pct": deviation_pct,
        "valuation_label": label,
        "valuation_score": score
    }


# -----------------------------
# HELPERS
# -----------------------------
def performance_pct(price_data, days):
    if len(price_data) < days:
        return 0.0
    start = price_data[-days][1]
    end = price_data[-1][1]
    return round(((end - start) / start) * 100, 2)


# -----------------------------
# MAIN REPORT
# -----------------------------
def main():
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    macro = get_macro_context()
    btc_val = valuation_assessment("bitcoin")
    eth_val = valuation_assessment("ethereum")

    report = ""
    report += "==============================\n"
    report += "LONG-TERM CRYPTO MACRO ANALYSIS\n"
    report += "==============================\n\n"

    report += "Macro & Capital Flow Context\n"
    report += f"- Bitcoin dominance: {macro['btc_dominance']}%\n"
    report += f"- Ethereum dominance: {macro['eth_dominance']}%\n"
    report += f"- BTC 30d performance: {macro['btc_30d']}%\n"
    report += f"- ETH 30d performance: {macro['eth_30d']}%\n"
    report += f"- ETH vs BTC (30d): {macro['eth_vs_btc_30d']}%\n\n"
    report += f"Interpretation: {macro['interpretation']}\n\n"

    report += "==============================\n"
    report += "VALUATION ANALYSIS (LONG TERM)\n"
    report += "==============================\n\n"

    report += "Bitcoin\n"
    report += f"- Current price: ${btc_val['current_price']}\n"
    report += f"- 200d average: ${btc_val['avg_200d']}\n"
    report += f"- Deviation: {btc_val['deviation_pct']}%\n"
    report += f"- Valuation: {btc_val['valuation_label']}\n"
    report += f"- Valuation score: {btc_val['valuation_score']}/100\n\n"

    report += "Ethereum\n"
    report += f"- Current price: ${eth_val['current_price']}\n"
    report += f"- 200d average: ${eth_val['avg_200d']}\n"
    report += f"- Deviation: {eth_val['deviation_pct']}%\n"
    report += f"- Valuation: {eth_val['valuation_label']}\n"
    report += f"- Valuation score: {eth_val['valuation_score']}/100\n\n"

    report += f"Report generated: {now}\n"
    report += "_Automatically generated. Not financial advice._\n"

    print(report)


if __name__ == "__main__":
    main()

