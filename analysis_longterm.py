
import math
import statistics
from datetime import UTC, datetime
from pathlib import Path

from api_utils import fetch_json_with_cache

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

COINGECKO = "https://api.coingecko.com/api/v3"
YAHOO_SUMMARY = "https://query2.finance.yahoo.com/v10/finance/quoteSummary"
YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart"

CRYPTO_ASSETS = {
    "bitcoin": {
        "name": "Bitcoin",
        "symbol": "BTC",
        "thesis": "Digital monetary network with fixed-supply narrative and highest liquidity depth in crypto.",
        "narrative": "Store-of-value and collateral asset in crypto market structure.",
    },
    "ethereum": {
        "name": "Ethereum",
        "symbol": "ETH",
        "thesis": "Programmable settlement layer where utility depends on smart-contract activity and fee demand.",
        "narrative": "Compute and settlement network for on-chain applications.",
    },
}

TRADITIONAL_ASSETS = {
    "spy": {
        "name": "S&P 500 ETF",
        "symbol": "SPY",
        "asset_type": "etf",
        "macro_note": "High sensitivity to U.S. growth, real rates, and broad equity risk appetite.",
    },
    "qqq": {
        "name": "Nasdaq 100 ETF",
        "symbol": "QQQ",
        "asset_type": "etf",
        "macro_note": "Higher duration/growth sensitivity and concentration in mega-cap technology.",
    },
    "nvda": {
        "name": "NVIDIA",
        "symbol": "NVDA",
        "asset_type": "equity",
        "macro_note": "Cyclical semiconductor exposure with AI capex dependence and valuation sensitivity to rates.",
    },
    "gold": {
        "name": "Gold Futures",
        "symbol": "GC=F",
        "asset_type": "commodity",
        "macro_note": "Sensitive to real yields, USD direction, and geopolitical hedging demand.",
    },
    "oil": {
        "name": "Crude Oil Futures",
        "symbol": "CL=F",
        "asset_type": "commodity",
        "macro_note": "Driven by global growth, OPEC+ policy, inventories, and geopolitical supply shocks.",
    },
}


def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


def safe_div(a, b):
    if a is None or b in (None, 0):
        return None
    try:
        return a / b
    except ZeroDivisionError:
        return None


def to_float(value):
    if isinstance(value, dict):
        value = value.get("raw", value.get("fmt"))
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def mean_or_none(values):
    clean = [v for v in values if v is not None]
    return statistics.mean(clean) if clean else None


def fmt_num(value, digits=2):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    return f"{value:,.{digits}f}"


def fmt_money(value, digits=0):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    return f"${value:,.{digits}f}"


def fmt_pct(value, digits=2):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{digits}f}%"


def percentile_rank(series, value):
    if not series or value is None:
        return None
    ordered = sorted(series)
    count = sum(1 for item in ordered if item <= value)
    return 100.0 * count / len(ordered)


def score_threshold(value, good, bad, higher_is_better=True):
    if value is None:
        return None

    if higher_is_better:
        if value >= good:
            return 100.0
        if value <= bad:
            return 0.0
        return 100.0 * (value - bad) / (good - bad)

    if value <= good:
        return 100.0
    if value >= bad:
        return 0.0
    return 100.0 * (bad - value) / (bad - good)


def weighted_score(score_map, weights):
    total = 0.0
    used = 0.0
    for key, weight in weights.items():
        score = score_map.get(key)
        if score is None:
            continue
        total += score * weight
        used += weight
    if used == 0:
        return None, 0.0
    return total / used, used


def annualized_volatility(prices):
    if not prices or len(prices) < 20:
        return None
    returns = []
    for idx in range(1, len(prices)):
        prev = prices[idx - 1]
        curr = prices[idx]
        if prev and curr:
            returns.append(curr / prev - 1)
    if len(returns) < 20:
        return None
    return statistics.pstdev(returns) * math.sqrt(252) * 100.0


def max_drawdown(prices):
    if not prices:
        return None
    peak = prices[0]
    worst = 0.0
    for price in prices:
        peak = max(peak, price)
        if peak:
            dd = (price / peak - 1.0) * 100.0
            worst = min(worst, dd)
    return worst


def recovery_days_after_drawdown(prices):
    if not prices or len(prices) < 3:
        return None
    peak = prices[0]
    peak_idx = 0
    trough_idx = 0
    trough_price = prices[0]

    for idx, price in enumerate(prices):
        if price > peak:
            peak = price
            peak_idx = idx
            trough_idx = idx
            trough_price = price
        if price < trough_price:
            trough_price = price
            trough_idx = idx

    if trough_idx <= peak_idx:
        return None

    for idx in range(trough_idx, len(prices)):
        if prices[idx] >= peak:
            return idx - trough_idx
    return None


def label_from_score(score):
    if score is None:
        return "Insufficient data"
    if score >= 75:
        return "Undervalued / High-conviction zone"
    if score >= 60:
        return "Constructive long-term setup"
    if score >= 45:
        return "Neutral / fair-value zone"
    if score >= 30:
        return "Caution / risk-reward mixed"
    return "High risk / weak long-term setup"


def confidence_score(used_weight, data_points, source_labels):
    coverage = clamp(used_weight)
    sample = clamp(data_points / 365.0 * 100.0)

    if all(src == "live" for src in source_labels):
        freshness = 100.0
    elif any(src == "live" for src in source_labels):
        freshness = 75.0
    elif all(src == "cache" for src in source_labels):
        freshness = 55.0
    else:
        freshness = 45.0

    return round(0.45 * coverage + 0.30 * freshness + 0.25 * sample, 1)


def quantile(series, q):
    if not series:
        return None
    ordered = sorted(series)
    idx = int((len(ordered) - 1) * q)
    return ordered[idx]


def build_scenarios(current_price, history):
    if current_price is None or not history:
        return None
    p20 = quantile(history, 0.2)
    p50 = quantile(history, 0.5)
    p80 = quantile(history, 0.8)
    if None in (p20, p50, p80):
        return None

    return {
        "bear": {
            "target": p20,
            "delta_pct": (p20 / current_price - 1.0) * 100.0,
            "assumption": "Multiple compression / weaker demand and tighter liquidity.",
        },
        "base": {
            "target": p50,
            "delta_pct": (p50 / current_price - 1.0) * 100.0,
            "assumption": "Mean reversion toward cycle-normal valuation and usage trends.",
        },
        "bull": {
            "target": p80,
            "delta_pct": (p80 / current_price - 1.0) * 100.0,
            "assumption": "Sustained growth, stable macro backdrop, and expanding risk appetite.",
        },
    }


def get_crypto_history(asset, days=365):
    try:
        url = f"{COINGECKO}/coins/{asset}/market_chart"
        payload, source = fetch_json_with_cache(
            url,
            params={"vs_currency": "usd", "days": days},
            namespace="coingecko_market_chart",
            cache_key=f"{asset}_usd_{days}",
            retries=5,
        )
    except Exception:
        return [], [], [], "unavailable"

    prices = [row[1] for row in payload.get("prices", []) if isinstance(row[1], (int, float))]
    market_caps = [row[1] for row in payload.get("market_caps", []) if isinstance(row[1], (int, float))]
    volumes = [row[1] for row in payload.get("total_volumes", []) if isinstance(row[1], (int, float))]
    return prices, market_caps, volumes, source


def get_crypto_details(asset):
    try:
        url = f"{COINGECKO}/coins/{asset}"
        payload, source = fetch_json_with_cache(
            url,
            params={
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "true",
                "developer_data": "true",
                "sparkline": "false",
            },
            namespace="coingecko_coin",
            cache_key=f"coin_{asset}",
            retries=5,
        )
        return payload, source
    except Exception:
        return {}, "unavailable"


def get_yahoo_summary(symbol):
    try:
        payload, source = fetch_json_with_cache(
            f"{YAHOO_SUMMARY}/{symbol}",
            params={
                "modules": "price,summaryDetail,defaultKeyStatistics,financialData,assetProfile",
            },
            namespace="yahoo_summary",
            cache_key=f"summary_{symbol}",
            retries=4,
        )
        result = (payload.get("quoteSummary", {}).get("result") or [{}])[0]
        return result, source
    except Exception:
        return {}, "unavailable"


def get_yahoo_history(symbol):
    try:
        payload, source = fetch_json_with_cache(
            f"{YAHOO_CHART}/{symbol}",
            params={"range": "10y", "interval": "1mo"},
            namespace="yahoo_history",
            cache_key=f"history_{symbol}_10y_1mo",
            retries=4,
        )

        result = (payload.get("chart", {}).get("result") or [{}])[0]
        close = ((result.get("indicators", {}).get("quote") or [{}])[0]).get("close") or []
        prices = [float(x) for x in close if isinstance(x, (int, float))]
        return prices, source
    except Exception:
        return [], "unavailable"

def score_crypto(asset_id, meta):
    prices, market_caps, volumes, history_source = get_crypto_history(asset_id)
    details, details_source = get_crypto_details(asset_id)

    current = prices[-1] if prices else None
    ma200 = statistics.mean(prices[-200:]) if len(prices) >= 200 else None
    price_to_ma = safe_div(current, ma200)

    market_data = details.get("market_data", {})
    developer = details.get("developer_data", {})

    circulating = to_float(market_data.get("circulating_supply"))
    total_supply = to_float(market_data.get("total_supply"))
    max_supply = to_float(market_data.get("max_supply"))
    market_cap = to_float((market_data.get("market_cap") or {}).get("usd"))
    fdv = to_float((market_data.get("fully_diluted_valuation") or {}).get("usd"))
    vol_24h = to_float((market_data.get("total_volume") or {}).get("usd"))

    circulating_ratio = safe_div(circulating, total_supply)
    max_supply_ratio = safe_div(circulating, max_supply)
    fdv_ratio = safe_div(fdv, market_cap)
    turnover = safe_div(vol_24h, market_cap)
    nvt_proxy = safe_div(market_cap, vol_24h)

    commit_4w = to_float(developer.get("commit_count_4_weeks"))
    stars = to_float(developer.get("stars"))

    vol_30 = statistics.mean(volumes[-30:]) if len(volumes) >= 30 else None
    vol_180 = statistics.mean(volumes[-180:]) if len(volumes) >= 180 else None
    usage_growth_proxy = safe_div(vol_30, vol_180)

    ann_vol = annualized_volatility(prices)
    mdd = max_drawdown(prices)
    recovery = recovery_days_after_drawdown(prices)

    price_percentile = percentile_rank(prices, current)

    tokenomics_score = mean_or_none(
        [
            score_threshold(circulating_ratio, good=0.90, bad=0.45, higher_is_better=True),
            score_threshold(fdv_ratio, good=1.15, bad=2.5, higher_is_better=False),
            score_threshold(max_supply_ratio, good=0.80, bad=0.35, higher_is_better=True),
        ]
    )

    network_score = mean_or_none(
        [
            score_threshold(usage_growth_proxy, good=1.15, bad=0.75, higher_is_better=True),
            score_threshold(nvt_proxy, good=20, bad=140, higher_is_better=False),
            score_threshold(turnover, good=0.08, bad=0.01, higher_is_better=True),
        ]
    )

    dev_score = mean_or_none(
        [
            score_threshold(commit_4w, good=250, bad=25, higher_is_better=True),
            score_threshold(stars, good=30000, bad=2000, higher_is_better=True),
        ]
    )

    liquidity_score = mean_or_none(
        [
            score_threshold(turnover, good=0.10, bad=0.01, higher_is_better=True),
            score_threshold(abs(mdd) if mdd is not None else None, good=25, bad=75, higher_is_better=False),
        ]
    )

    macro_narrative_score = mean_or_none(
        [
            score_threshold(price_to_ma, good=1.05, bad=0.70, higher_is_better=True),
            score_threshold(price_percentile, good=65, bad=20, higher_is_better=True),
            score_threshold(abs(mdd) if mdd is not None else None, good=25, bad=80, higher_is_better=False),
        ]
    )

    score_map = {
        "tokenomics": tokenomics_score,
        "usage": network_score,
        "dev_security": dev_score,
        "liquidity": liquidity_score,
        "macro_narrative": macro_narrative_score,
    }
    weights = {
        "tokenomics": 20,
        "usage": 25,
        "dev_security": 20,
        "liquidity": 15,
        "macro_narrative": 20,
    }

    composite, used_weight = weighted_score(score_map, weights)
    confidence = confidence_score(used_weight, len(prices), [history_source, details_source])
    verdict = label_from_score(composite)
    scenarios = build_scenarios(current, prices)

    lines = []
    lines.append(f"## {meta['name']} ({meta['symbol']})")
    lines.append("")
    lines.append(f"_Data sources: CoinGecko history ({history_source}), CoinGecko fundamentals ({details_source})_")
    lines.append("")
    lines.append("### One-line Long-Term Summary")
    lines.append("")
    lines.append(f"Long-term: **{verdict}** - {meta['thesis']} Key narrative: {meta['narrative']}.")
    lines.append("")
    lines.append("### Composite Scorecard")
    lines.append("")
    lines.append(f"- **Composite score:** {fmt_num(composite, 1)}/100")
    lines.append(f"- **Confidence:** {fmt_num(confidence, 1)}/100")
    lines.append(f"- **Supply/issuance & tokenomics (20%):** {fmt_num(tokenomics_score, 1)}")
    lines.append(f"- **Network usage activity (25%):** {fmt_num(network_score, 1)}")
    lines.append(f"- **Developer & security (20%):** {fmt_num(dev_score, 1)}")
    lines.append(f"- **Liquidity & market structure (15%):** {fmt_num(liquidity_score, 1)}")
    lines.append(f"- **Macro/regulatory & narrative (20%):** {fmt_num(macro_narrative_score, 1)}")
    lines.append("")
    lines.append("### Supply & Issuance")
    lines.append("")
    lines.append(f"- **Circulating supply:** {fmt_num(circulating, 0)}")
    lines.append(f"- **Total supply:** {fmt_num(total_supply, 0)}")
    lines.append(f"- **Max supply:** {fmt_num(max_supply, 0)}")
    lines.append(f"- **Circulating/Total:** {fmt_pct(circulating_ratio * 100 if circulating_ratio is not None else None)}")
    lines.append(f"- **FDV / Market Cap:** {fmt_num(fdv_ratio, 2)}")
    lines.append("")
    lines.append("### Network Activity & Economics")
    lines.append("")
    lines.append(f"- **Market cap:** {fmt_money(market_cap, 0)}")
    lines.append(f"- **24H volume:** {fmt_money(vol_24h, 0)}")
    lines.append(f"- **Turnover (Vol/Cap):** {fmt_pct(turnover * 100 if turnover is not None else None)}")
    lines.append(f"- **NVT proxy (Cap/Volume):** {fmt_num(nvt_proxy, 2)}")
    lines.append(f"- **30d vs 180d volume trend proxy:** {fmt_num(usage_growth_proxy, 2)}")
    lines.append("")
    lines.append("### Developer & Protocol Health")
    lines.append("")
    lines.append(f"- **GitHub commits (4w):** {fmt_num(commit_4w, 0)}")
    lines.append(f"- **GitHub stars:** {fmt_num(stars, 0)}")
    lines.append("- **Security / upgrade risk:** No exploit database integrated yet; treat as manual diligence item.")
    lines.append("")
    lines.append("### Cross-Asset Risk")
    lines.append("")
    lines.append(f"- **Annualized volatility (1y):** {fmt_pct(ann_vol)}")
    lines.append(f"- **Max drawdown (1y):** {fmt_pct(mdd)}")
    lines.append(f"- **Drawdown recovery time estimate:** {fmt_num(recovery, 0)} trading days")
    lines.append(f"- **Price vs 200d average:** {fmt_num(price_to_ma, 2)}")
    lines.append(f"- **Price percentile (1y):** {fmt_pct(price_percentile)}")
    lines.append("")
    lines.append("### Scenario Analysis (Base / Bull / Bear)")
    lines.append("")
    if scenarios:
        lines.append("| Case | Implied Price | Move vs Current | Core Assumption |")
        lines.append("|---|---:|---:|---|")
        lines.append(f"| Bear | {fmt_money(scenarios['bear']['target'], 0)} | {fmt_pct(scenarios['bear']['delta_pct'])} | {scenarios['bear']['assumption']} |")
        lines.append(f"| Base | {fmt_money(scenarios['base']['target'], 0)} | {fmt_pct(scenarios['base']['delta_pct'])} | {scenarios['base']['assumption']} |")
        lines.append(f"| Bull | {fmt_money(scenarios['bull']['target'], 0)} | {fmt_pct(scenarios['bull']['delta_pct'])} | {scenarios['bull']['assumption']} |")
    else:
        lines.append("Scenario model unavailable due to insufficient history.")
    lines.append("")
    lines.append("Valuation verdict:")
    lines.append(verdict)
    lines.append("")
    lines.append("**Long-term verdict:** " + verdict)
    lines.append("")
    lines.append("### Method Notes")
    lines.append("")
    lines.append("- NVT/MVRV are approximated with available market-cap and volume feeds; direct realized-cap not integrated yet.")
    lines.append("- Percentile-based interpretation is preferred over hard static thresholds where history is available.")
    lines.append("- Not investment advice; use with independent risk management.")
    lines.append("")
    lines.append("---")

    return "\n".join(lines)


def extract_module(summary, name):
    return summary.get(name, {}) if isinstance(summary, dict) else {}

def score_traditional(asset_id, meta):
    symbol = meta["symbol"]
    summary, summary_source = get_yahoo_summary(symbol)
    prices, history_source = get_yahoo_history(symbol)

    price_mod = extract_module(summary, "price")
    detail_mod = extract_module(summary, "summaryDetail")
    stats_mod = extract_module(summary, "defaultKeyStatistics")
    fin_mod = extract_module(summary, "financialData")

    current = to_float(price_mod.get("regularMarketPrice"))
    market_cap = to_float(price_mod.get("marketCap"))

    trailing_pe = to_float(stats_mod.get("trailingPE"))
    forward_pe = to_float(stats_mod.get("forwardPE"))
    pb = to_float(stats_mod.get("priceToBook"))
    ev_ebitda = to_float(stats_mod.get("enterpriseToEbitda"))
    ps = to_float(stats_mod.get("priceToSalesTrailing12Months"))
    peg = to_float(stats_mod.get("pegRatio"))

    gross_margin = to_float(fin_mod.get("grossMargins"))
    op_margin = to_float(fin_mod.get("operatingMargins"))
    net_margin = to_float(fin_mod.get("profitMargins"))
    roe = to_float(fin_mod.get("returnOnEquity"))

    rev_growth = to_float(fin_mod.get("revenueGrowth"))
    eps_growth = to_float(fin_mod.get("earningsGrowth"))

    debt_to_equity = to_float(fin_mod.get("debtToEquity"))
    current_ratio = to_float(fin_mod.get("currentRatio"))
    quick_ratio = to_float(fin_mod.get("quickRatio"))

    free_cashflow = to_float(fin_mod.get("freeCashflow"))
    operating_cashflow = to_float(fin_mod.get("operatingCashflow"))
    payout_ratio = to_float(detail_mod.get("payoutRatio"))
    dividend_yield = to_float(detail_mod.get("dividendYield"))

    beta = to_float(stats_mod.get("beta"))
    insider = to_float(stats_mod.get("heldPercentInsiders"))
    institution = to_float(stats_mod.get("heldPercentInstitutions"))

    expense_ratio = to_float(detail_mod.get("annualReportExpenseRatio"))

    fcf_yield = safe_div(free_cashflow, market_cap)

    ma_24m = statistics.mean(prices[-24:]) if len(prices) >= 24 else None
    price_to_ma = safe_div(current, ma_24m)
    price_percentile = percentile_rank(prices, current)

    ann_vol = annualized_volatility(prices)
    mdd = max_drawdown(prices)
    recovery = recovery_days_after_drawdown(prices)

    asset_type = meta.get("asset_type")

    if asset_type == "equity":
        valuation_score = mean_or_none(
            [
                score_threshold(trailing_pe, good=16, bad=45, higher_is_better=False),
                score_threshold(pb, good=3, bad=18, higher_is_better=False),
                score_threshold(peg, good=1.4, bad=3.0, higher_is_better=False),
                score_threshold(price_percentile, good=55, bad=90, higher_is_better=False),
            ]
        )
        growth_profit_score = mean_or_none(
            [
                score_threshold((rev_growth or 0) * 100 if rev_growth is not None else None, good=12, bad=-5, higher_is_better=True),
                score_threshold((eps_growth or 0) * 100 if eps_growth is not None else None, good=15, bad=-8, higher_is_better=True),
                score_threshold((gross_margin or 0) * 100 if gross_margin is not None else None, good=45, bad=20, higher_is_better=True),
                score_threshold((net_margin or 0) * 100 if net_margin is not None else None, good=18, bad=4, higher_is_better=True),
            ]
        )
    elif asset_type == "etf":
        valuation_score = mean_or_none(
            [
                score_threshold(price_percentile, good=50, bad=90, higher_is_better=False),
                score_threshold((expense_ratio or 0) * 100 if expense_ratio is not None else None, good=0.10, bad=0.95, higher_is_better=False),
                score_threshold((dividend_yield or 0) * 100 if dividend_yield is not None else None, good=1.5, bad=0.0, higher_is_better=True),
            ]
        )
        growth_profit_score = mean_or_none(
            [
                score_threshold(price_to_ma, good=1.05, bad=0.80, higher_is_better=True),
                score_threshold((dividend_yield or 0) * 100 if dividend_yield is not None else None, good=2.0, bad=0.0, higher_is_better=True),
            ]
        )
    else:
        valuation_score = mean_or_none(
            [
                score_threshold(price_percentile, good=45, bad=90, higher_is_better=False),
                score_threshold(price_to_ma, good=1.00, bad=1.35, higher_is_better=False),
            ]
        )
        growth_profit_score = mean_or_none(
            [
                score_threshold(price_to_ma, good=1.08, bad=0.80, higher_is_better=True),
            ]
        )

    balance_cashflow_score = mean_or_none(
        [
            score_threshold(debt_to_equity, good=40, bad=220, higher_is_better=False),
            score_threshold(current_ratio, good=1.8, bad=0.8, higher_is_better=True),
            score_threshold((fcf_yield or 0) * 100 if fcf_yield is not None else None, good=8, bad=0, higher_is_better=True),
            score_threshold((payout_ratio or 0) * 100 if payout_ratio is not None else None, good=45, bad=120, higher_is_better=False),
        ]
    )

    comp_mgmt_score = mean_or_none(
        [
            score_threshold((roe or 0) * 100 if roe is not None else None, good=18, bad=6, higher_is_better=True),
            score_threshold((insider or 0) * 100 if insider is not None else None, good=8, bad=0.2, higher_is_better=True),
            score_threshold((institution or 0) * 100 if institution is not None else None, good=75, bad=20, higher_is_better=True),
        ]
    )

    macro_reg_score = mean_or_none(
        [
            score_threshold(beta, good=0.9, bad=1.8, higher_is_better=False),
            score_threshold(abs(mdd) if mdd is not None else None, good=20, bad=60, higher_is_better=False),
            score_threshold(abs(ann_vol) if ann_vol is not None else None, good=12, bad=45, higher_is_better=False),
        ]
    )

    score_map = {
        "valuation": valuation_score,
        "growth_profit": growth_profit_score,
        "balance_cashflow": balance_cashflow_score,
        "comp_mgmt": comp_mgmt_score,
        "macro_reg": macro_reg_score,
    }
    weights = {
        "valuation": 25,
        "growth_profit": 25,
        "balance_cashflow": 20,
        "comp_mgmt": 15,
        "macro_reg": 15,
    }

    composite, used_weight = weighted_score(score_map, weights)
    confidence = confidence_score(used_weight, len(prices) * 21, [summary_source, history_source])
    verdict = label_from_score(composite)
    scenarios = build_scenarios(current, prices)

    lines = []
    lines.append(f"## {meta['name']} ({symbol})")
    lines.append("")
    lines.append(f"_Data sources: Yahoo summary ({summary_source}), Yahoo history ({history_source})_")
    lines.append("")
    lines.append("### One-line Long-Term Summary")
    lines.append("")
    lines.append(f"Long-term: **{verdict}** - {meta['macro_note']}")
    lines.append("")
    lines.append("### Composite Scorecard")
    lines.append("")
    lines.append(f"- **Composite score:** {fmt_num(composite, 1)}/100")
    lines.append(f"- **Confidence:** {fmt_num(confidence, 1)}/100")
    lines.append(f"- **Valuation (25%):** {fmt_num(valuation_score, 1)}")
    lines.append(f"- **Growth & profitability (25%):** {fmt_num(growth_profit_score, 1)}")
    lines.append(f"- **Balance sheet & cash flow (20%):** {fmt_num(balance_cashflow_score, 1)}")
    lines.append(f"- **Competitive position & management (15%):** {fmt_num(comp_mgmt_score, 1)}")
    lines.append(f"- **Macro/regulatory (15%):** {fmt_num(macro_reg_score, 1)}")
    lines.append("")
    lines.append("### Valuation")
    lines.append("")
    lines.append(f"- **P/E:** {fmt_num(trailing_pe, 2)}")
    lines.append(f"- **Forward P/E:** {fmt_num(forward_pe, 2)}")
    lines.append(f"- **P/B:** {fmt_num(pb, 2)}")
    lines.append(f"- **EV/EBITDA:** {fmt_num(ev_ebitda, 2)}")
    lines.append(f"- **Price/Sales:** {fmt_num(ps, 2)}")
    lines.append(f"- **PEG:** {fmt_num(peg, 2)}")
    lines.append(f"- **Price percentile vs 10y history:** {fmt_pct(price_percentile)}")
    lines.append("")
    lines.append("### Profitability, Growth, and Balance-Sheet Health")
    lines.append("")
    lines.append(f"- **Revenue growth:** {fmt_pct((rev_growth * 100) if rev_growth is not None else None)}")
    lines.append(f"- **EPS growth:** {fmt_pct((eps_growth * 100) if eps_growth is not None else None)}")
    lines.append(f"- **Gross margin:** {fmt_pct((gross_margin * 100) if gross_margin is not None else None)}")
    lines.append(f"- **Operating margin:** {fmt_pct((op_margin * 100) if op_margin is not None else None)}")
    lines.append(f"- **Net margin:** {fmt_pct((net_margin * 100) if net_margin is not None else None)}")
    lines.append(f"- **Debt/Equity:** {fmt_num(debt_to_equity, 2)}")
    lines.append(f"- **Current ratio:** {fmt_num(current_ratio, 2)}")
    lines.append(f"- **Quick ratio:** {fmt_num(quick_ratio, 2)}")
    lines.append("")
    lines.append("### Cash Flow, Shareholder Returns, and Governance")
    lines.append("")
    lines.append(f"- **Free cash flow:** {fmt_money(free_cashflow, 0)}")
    lines.append(f"- **Operating cash flow:** {fmt_money(operating_cashflow, 0)}")
    lines.append(f"- **FCF yield:** {fmt_pct((fcf_yield * 100) if fcf_yield is not None else None)}")
    lines.append(f"- **Dividend yield:** {fmt_pct((dividend_yield * 100) if dividend_yield is not None else None)}")
    lines.append(f"- **Payout ratio:** {fmt_pct((payout_ratio * 100) if payout_ratio is not None else None)}")
    lines.append(f"- **Insider ownership:** {fmt_pct((insider * 100) if insider is not None else None)}")
    lines.append(f"- **Institutional ownership:** {fmt_pct((institution * 100) if institution is not None else None)}")
    lines.append("")
    lines.append("### Volatility, Drawdown, and Macro Sensitivity")
    lines.append("")
    lines.append(f"- **Annualized volatility:** {fmt_pct(ann_vol)}")
    lines.append(f"- **Max drawdown (history window):** {fmt_pct(mdd)}")
    lines.append(f"- **Recovery time estimate:** {fmt_num(recovery, 0)} monthly bars")
    lines.append(f"- **Beta:** {fmt_num(beta, 2)}")
    lines.append("- **Macro/cycle note:** " + meta["macro_note"])
    lines.append("")
    lines.append("### Scenario Analysis (Base / Bull / Bear)")
    lines.append("")
    if scenarios:
        lines.append("| Case | Implied Price | Move vs Current | Core Assumption |")
        lines.append("|---|---:|---:|---|")
        lines.append(f"| Bear | {fmt_money(scenarios['bear']['target'], 2)} | {fmt_pct(scenarios['bear']['delta_pct'])} | {scenarios['bear']['assumption']} |")
        lines.append(f"| Base | {fmt_money(scenarios['base']['target'], 2)} | {fmt_pct(scenarios['base']['delta_pct'])} | {scenarios['base']['assumption']} |")
        lines.append(f"| Bull | {fmt_money(scenarios['bull']['target'], 2)} | {fmt_pct(scenarios['bull']['delta_pct'])} | {scenarios['bull']['assumption']} |")
    else:
        lines.append("Scenario model unavailable due to insufficient history.")
    lines.append("")
    lines.append("Valuation verdict:")
    lines.append(verdict)
    lines.append("")
    lines.append("**Long-term verdict:** " + verdict)
    lines.append("")
    lines.append("### Method Notes")
    lines.append("")
    lines.append("- Where fields are unavailable (especially ETFs/futures), scoring automatically reduces confidence and re-weights available evidence.")
    lines.append("- Percentile framing is based on available 10-year monthly history from Yahoo chart data.")
    lines.append("- Not investment advice; this is a decision-support framework.")
    lines.append("")
    lines.append("---")

    return "\n".join(lines)


def generate_report():
    report = []
    report.append("# Long-Term Multi-Asset Analysis Report")
    report.append("")
    report.append(f"_Updated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}_")
    report.append("")
    report.append("## Framework")
    report.append("")
    report.append("This report scores assets with a weighted, percentile-oriented rubric and pairs it with qualitative risk context.")
    report.append("Scoring is normalized to 0-100, then mapped to human labels and a confidence score based on coverage and data freshness.")
    report.append("")
    report.append("### Crypto Weights")
    report.append("")
    report.append("- Supply/issuance & tokenomics: 20%")
    report.append("- Network usage activity: 25%")
    report.append("- Developer & security: 20%")
    report.append("- Liquidity & market structure: 15%")
    report.append("- Macro/regulatory & narrative: 20%")
    report.append("")
    report.append("### Traditional Asset Weights")
    report.append("")
    report.append("- Valuation: 25%")
    report.append("- Growth & profitability: 25%")
    report.append("- Balance sheet & cash flow: 20%")
    report.append("- Competitive position & management: 15%")
    report.append("- Macro/regulatory: 15%")
    report.append("")
    report.append("---")
    report.append("")

    for asset_id, meta in CRYPTO_ASSETS.items():
        report.append(score_crypto(asset_id, meta))

    for asset_id, meta in TRADITIONAL_ASSETS.items():
        report.append(score_traditional(asset_id, meta))

    output = REPORT_DIR / "long_term_report.md"
    output.write_text("\n".join(report), encoding="utf-8")
    print("Long-term valuation report generated")


if __name__ == "__main__":
    generate_report()

