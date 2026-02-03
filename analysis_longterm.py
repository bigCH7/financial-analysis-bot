import requests
import datetime
import statistics
import math

# -----------------------------
# CONFIG
# -----------------------------
ASSETS = ["bitcoin", "ethereum"]
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
# HELPERS
# -----------------------------
def performance_pct(price_data, days):
    start = price_data[-days][1]
    end = price_data[-1][1]
    return round(((end - start) / start) * 100, 2)


def daily_returns(prices):
    returns = []
    for i in range(1, len(prices)):
        prev = prices[i - 1]
        curr = prices[i]
        returns.append((curr - prev) / prev)
    return returns


def max_drawdown(prices):
    peak = prices[0]
    max_dd = 0
    for p in prices:
        if p > peak:
            peak = p
        drawdown = (p - peak) / peak
        max_dd = min(max_dd, drawdown)
    return round(max_dd * 100, 2)


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
            "Investors prioritize capital preservation."
        )
    else:
        interpretation = (
            "Neutral or risk-on environment. Capital rotating into higher-beta assets."
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
# VALUATION (MEAN REVERSION)
# -----------------------------
def valuation_assessment(asset_id):
    prices = get_market_data(asset_id)
    closes = [p[1] for p in prices]

    current = closes[-1]
    avg_200 = statistics.mean(closes[-200:])
    deviation = round(((current - avg_200) / avg_200) * 100, 2)

    if deviation < -20:
        label, score = "Deeply Undervalued", 80
    elif deviation < -10:
        label, score = "Undervalued", 70
    elif deviation < 10:
        label, score = "Fairly Valued", 50
    elif deviation < 25:
        label, score = "Overvalued", 35
    else:
        label, score = "Highly Overvalued", 20

    return {
        "current_price": round(current, 2),
        "avg_200d": round(avg_200, 2),
        "deviation_pct": deviation,
        "label": label,
        "score": score
    }


# -----------------------------
# RISK & DRAWDOWN ANALYSIS
# -----------------------------
def risk_assessment(asset_id):
    prices_raw = get_market_data(asset_id)
    prices = [p[1] for p in prices_raw]

    returns = daily_returns(prices)
    volatility = statistics.stdev(returns) * math.sqrt(365) * 100
    volatility = round(volatility, 2)

    dd = max_drawdown(prices)

    if volatility > 90 or dd < -70:
        regime = "Extreme Risk"
        risk_score = 20
    elif volatility > 70 or dd < -55:
        regime = "High Risk"
        risk_score = 35
    elif volatility > 50 or dd < -40:
        regime = "Moderate Risk"
        risk_score = 55
    else:
        regime = "Lower Risk (Crypto-relative)"
        risk_score = 75

    return {
        "volatility": volatility,
        "max_drawdown": dd,
        "regime": regime,
        "risk_score": risk_score
    }


# -----------------------------
# MAIN REPORT
# -----------------------------
def main():
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    macro = get_macro_context()

    btc_val = valuation_assessment("bitcoin")
    eth_val = valuation_assessment("ethereum")

    btc_risk = risk_assessment("bitcoin")
    eth_risk = risk_assessment("ethereum")

    report = ""
    report += "==============================\n"
    report += "LONG-TERM CRYPTO ANALYSIS\n"
    report += "==============================\n\n"

    report += "MACRO CONTEXT\n"
    report += f"- Bitcoin dominance: {macro['btc_dominance']}%\n"
    report += f"- Ethereum dominance: {macro['eth_dominance']}%\n"
    report += f"- BTC 30d performance: {macro['btc_30d']}%\n"
    report += f"- ETH 30d performance: {macro['eth_30d']}%\n"
    report += f"- ETH vs BTC (30d): {macro['eth_vs_btc_30d']}%\n"
    report += f"Interpretation: {macro['interpretation']}\n\n"

    report += "==============================\n"
    report += "VALUATION (LONG TERM)\n"
    report += "==============================\n\n"

    report += (
        f"Bitcoin: {btc_val['label']} | "
        f"Deviation: {btc_val['deviation_pct']}% | "
        f"Score: {btc_val['score']}/100\n"
    )

    report += (
        f"Ethereum: {eth_val['label']} | "
        f"Deviation: {eth_val['deviation_pct']}% | "
        f"Score: {eth_val['score']}/100\n\n"
    )

    report += "==============================\n"
    report += "RISK & DRAWDOWNS\n"
    report += "==============================\n\n"

    report += (
        f"Bitcoin:\n"
        f"- Annualized volatility: {btc_risk['volatility']}%\n"
        f"- Max drawdown (1y): {btc_risk['max_drawdown']}%\n"
        f"- Risk regime: {btc_risk['regime']}\n"
        f"- Risk score: {btc_risk['risk_score']}/100\n\n"
    )

    report += (
        f"Ethereum:\n"
        f"- Annualized volatility: {eth_risk['volatility']}%\n"
        f"- Max drawdown (1y): {eth_risk['max_drawdown']}%\n"
        f"- Risk regime: {eth_risk['regime']}\n"
        f"- Risk score: {eth_risk['risk_score']}/100\n\n"
    )

    report += f"Report generated: {now}\n"
    report += "_Automatically generated. Not financial advice._\n"

    print(report)


if __name__ == "__main__":
    main()

