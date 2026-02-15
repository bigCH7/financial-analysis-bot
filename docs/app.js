const GLOSSARY = {
  "RSI": "Relative Strength Index, a momentum indicator from 0 to 100. Above 70 is often called overbought, below 30 oversold.",
  "MA50": "50-day moving average. It smooths price data to show medium-term trend direction.",
  "MA200": "200-day moving average. A widely used long-term trend baseline.",
  "200-day average": "Average closing price over the last 200 days. Often used to judge cycle positioning.",
  "ETH/BTC ratio": "Ethereum price divided by Bitcoin price. It tracks ETH strength relative to BTC.",
  "market cap": "Market capitalization: total value of an asset supply or company equity at current price.",
  "Market Capitalization": "Total market value of a company or asset, typically price multiplied by shares or circulating supply.",
  "volatility": "How fast and how far price moves over time.",
  "Volatility (VIX)": "VIX is a market volatility index often called the fear gauge for expected near-term U.S. equity volatility.",
  "Bullish": "Expectation that trend is likely upward.",
  "Bearish": "Expectation that trend is likely downward.",
  "bull market": "A period where prices trend upward broadly and investor sentiment is generally optimistic.",
  "bear market": "A period of broad price declines and weaker investor sentiment.",
  "Bull vs. Bear Market": "Bull means broadly rising markets, while bear means broadly falling markets.",
  "Undervalued": "Price appears low relative to chosen benchmarks.",
  "Overextended": "Price appears stretched versus trend and may face pullback risk.",
  "overbought": "Momentum is very strong and short-term reversal risk can rise.",
  "oversold": "Momentum is very weak and rebound potential can increase.",
  "support": "A level where buying has often slowed declines.",
  "resistance": "A level where selling has often slowed advances.",
  "decentralized": "Not controlled by a single central authority; decisions and validation are distributed across many participants.",
  "public blockchain": "A ledger that anyone can inspect, verify, and in many cases participate in validating.",
  "global participants": "Users, validators, miners, and developers from multiple regions who interact with the same network.",
  "native asset": "The core token of a blockchain network used for fees, security incentives, and value transfer.",
  "smart contracts": "Self-executing code on blockchain that runs automatically when preset conditions are met.",
  "DeFi rails": "Decentralized finance infrastructure for trading, borrowing, lending, and payments without traditional intermediaries.",
  "on-chain applications": "Apps whose key logic and state transitions are executed or recorded directly on blockchain.",
  "proof-of-stake": "A consensus method where validators secure the network by staking tokens instead of using mining hardware.",
  "proof-of-work": "A consensus method where miners use computational work to validate transactions and secure the network.",
  "validator": "A network participant that confirms transactions and helps produce new blocks in proof-of-stake systems.",
  "liquidity": "How easily an asset can be bought or sold without causing a large price move.",
  "drawdown": "The percentage decline from a prior peak to a subsequent trough.",
  "ETF": "Exchange-traded fund: a tradable basket that tracks an index, sector, or strategy.",
  "Exchange-Traded Fund (ETF)": "A fund that trades on an exchange like a stock and typically tracks an index, sector, or theme.",
  "futures contract": "A derivative agreement to buy or sell an asset at a specified future date and price.",
  "Future / Forward Contract": "An agreement to transact an asset at a future date; futures are standardized and exchange-traded, forwards are typically private contracts.",
  "risk premium": "Extra expected return investors demand for taking additional risk.",
  "Stock (Equity)": "A tiny piece of ownership in a company.",
  "stock": "A tiny piece of ownership in a company.",
  "equity": "Ownership interest in a company, usually represented by shares.",
  "Bond": "A debt investment where the issuer borrows money and pays interest, then repays principal at maturity.",
  "Portfolio": "Your combined collection of investments, such as stocks, bonds, funds, and cash.",
  "Diversification": "Spreading investments across assets to reduce concentration risk.",
  "Capital Gain": "Profit from selling an investment for more than its purchase price.",
  "Dividend": "A cash payment a company may distribute to shareholders from earnings.",
  "Mutual Fund": "A pooled investment vehicle managed by professionals that buys a basket of securities.",
  "Index Fund": "A fund designed to track a market index, often with lower costs and broad diversification.",
  "Real Estate Investment Trust (REIT)": "A company that owns or finances income-producing real estate and often pays regular dividends.",
  "REIT": "A real estate investment trust that gives exposure to property-related income and assets.",
  "Derivative": "A contract whose value depends on an underlying asset, index, rate, or other benchmark.",
  "Option": "A contract giving the right, not the obligation, to buy or sell an asset at a set price before expiration.",
  "Option (Call & Put)": "A call gives the right to buy; a put gives the right to sell, at a set strike price before expiration.",
  "Commodity": "A raw material or primary good such as oil, gold, wheat, or natural gas.",
  "Cryptocurrency": "A digital asset that uses cryptography and blockchain networks for transfer and settlement.",
  "Annuity": "An insurance contract often used for retirement income, typically exchanging a lump sum for future payouts.",
  "Preferred Stock": "A class of stock that usually has priority dividends and claims over common stock but limited voting rights.",
  "Initial Public Offering (IPO)": "The first sale of a private company's shares to the public market.",
  "IPO": "Initial public offering: when a private company lists shares for public trading.",
  "Price-to-Earnings Ratio (P/E Ratio)": "Valuation metric equal to price per share divided by earnings per share.",
  "P/E Ratio": "Price-to-earnings ratio: price per share divided by earnings per share.",
  "Earnings Per Share (EPS)": "Company profit allocated to each outstanding share, used to assess profitability.",
  "EPS": "Earnings per share: profit allocated per outstanding share.",
  "Bid-Ask Spread": "Difference between the highest price buyers will pay and the lowest price sellers will accept.",
  "Limit Order": "An order to buy or sell only at a specified price or better.",
  "Market Order": "An order to buy or sell immediately at the best available current price.",
  "Limit Order vs. Market Order": "Limit orders prioritize price control; market orders prioritize immediate execution.",
  "Short Selling": "Selling borrowed shares to profit if price falls, with potentially unlimited upside risk if price rises.",
  "Margin Trading": "Using borrowed funds from a broker to increase position size and potential gains or losses.",
  "Dividend Yield": "Annual dividend per share divided by share price, shown as a percentage.",
  "Expense Ratio": "Annual fund operating cost as a percentage of assets.",
  "Dollar-Cost Averaging (DCA)": "Investing fixed amounts at regular intervals to reduce timing risk.",
  "DCA": "Dollar-cost averaging: investing fixed amounts on a schedule regardless of price.",
  "Fundamental Analysis": "Evaluating value using financial statements, business quality, industry dynamics, and macro factors.",
  "Technical Analysis": "Using price, volume, and chart patterns to evaluate trend and momentum.",
  "Alpha": "Return above a benchmark after adjusting for risk.",
  "Beta": "Sensitivity of an asset's returns relative to the broader market.",
  "Asset Allocation": "How you divide investments across asset classes such as stocks, bonds, and cash.",
  "Rebalancing": "Adjusting portfolio weights back to target allocation after market moves.",
  "Risk Tolerance": "How much volatility and potential loss an investor is willing to accept.",
  "Time Horizon": "Expected length of time an investment is intended to be held.",
  "Tax-Loss Harvesting": "Selling positions at a loss to offset taxable capital gains.",
  "Blue Chip": "A large, established company known for financial strength and operating stability.",
  "Growth vs. Value Investing": "Growth seeks faster earnings expansion; value seeks assets trading below perceived intrinsic value.",
  "Securities and Exchange Commission (SEC)": "U.S. regulator overseeing securities markets, disclosures, and investor protections.",
  "SEC": "U.S. Securities and Exchange Commission, the primary federal securities regulator.",
  "Broker-Dealer": "A firm that executes trades for clients and may also trade for its own account.",
  "Fiduciary Duty": "Legal and ethical obligation to act in a client's best interest.",
  "Prospectus": "Official fund or offering document describing objectives, risks, fees, and holdings.",
  "10-K": "Comprehensive annual report public companies file with the SEC.",
  "10-Q": "Quarterly financial report public companies file with the SEC.",
  "10-K / 10-Q Reports": "Required SEC filings providing annual and quarterly company financial disclosures.",
  "Insider Trading": "Trading based on material non-public information, which is illegal when done improperly.",
  "Dark Pool": "Private trading venue where large orders can be executed with limited pre-trade transparency."
};

function escapeRegExp(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

async function fetchJsonWithFallback(paths) {
  for (const path of paths) {
    try {
      const res = await fetch(path, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch (_) {}
  }
  throw new Error("Unable to load JSON from fallback paths.");
}

function markdownToHtml(markdown) {
  if (window.marked && typeof window.marked.parse === "function") {
    return window.marked.parse(markdown || "");
  }
  return `<pre>${markdown || ""}</pre>`;
}

function pctClass(value) {
  if (value == null || Number.isNaN(value)) return "";
  if (value < 0) return "metric-negative";
  if (value > 0) return "metric-positive";
  return "";
}

function fmtPct(value) {
  if (value == null || Number.isNaN(value)) return "N/A";
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function fmtPrice(value) {
  if (value == null || Number.isNaN(value)) return "N/A";
  return `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function fmtDateTime(value) {
  if (!value) return "N/A";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : d.toUTCString();
}

function setMetaRow(id, chips) {
  const row = document.getElementById(id);
  if (!row) return;
  const safe = (chips || []).filter((chip) => chip && chip.value && chip.value !== "N/A");
  row.innerHTML = safe
    .map((chip) => `<span class="meta-chip"><strong>${chip.label}:</strong> ${chip.value}</span>`)
    .join("");
}

function setActiveTab() {
  const page = document.body.dataset.page;
  document.querySelectorAll(".tab").forEach((tab) => {
    if (tab.dataset.page === page) tab.classList.add("active");
  });
}

function showGlossary(term, definition) {
  document.getElementById("glossary-title").textContent = term;
  document.getElementById("glossary-body").textContent = definition;
  document.getElementById("glossary-modal").classList.remove("hidden");
}

function initGlossary() {
  const modalHtml = `
    <div id="glossary-modal" class="modal hidden" role="dialog" aria-modal="true" aria-labelledby="glossary-title">
      <div class="modal-card">
        <h3 id="glossary-title" class="modal-title"></h3>
        <p id="glossary-body" class="muted"></p>
        <button type="button" id="glossary-close" class="modal-close">Close</button>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML("beforeend", modalHtml);

  document.addEventListener("click", (event) => {
    const button = event.target.closest(".term-btn");
    if (button) {
      const key = button.dataset.term;
      showGlossary(key, GLOSSARY[key]);
      return;
    }

    if (event.target.id === "glossary-close" || event.target.id === "glossary-modal") {
      document.getElementById("glossary-modal").classList.add("hidden");
    }
  });
}

function highlightTerms(container) {
  const terms = Object.keys(GLOSSARY).sort((a, b) => b.length - a.length);
  if (!terms.length) return;

  const lowerToCanonical = new Map(terms.map((term) => [term.toLowerCase(), term]));
  const pattern = new RegExp(`\\b(${terms.map(escapeRegExp).join("|")})\\b`, "gi");

  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
      const parentTag = node.parentElement ? node.parentElement.tagName : "";
      if (["SCRIPT", "STYLE", "BUTTON", "A", "CODE", "PRE"].includes(parentTag)) {
        return NodeFilter.FILTER_REJECT;
      }
      return NodeFilter.FILTER_ACCEPT;
    }
  });

  const textNodes = [];
  while (walker.nextNode()) textNodes.push(walker.currentNode);

  for (const node of textNodes) {
    const text = node.nodeValue;
    pattern.lastIndex = 0;
    let match = pattern.exec(text);
    if (!match) continue;

    const frag = document.createDocumentFragment();
    let cursor = 0;

    while (match) {
      const found = match[0];
      const start = match.index;
      if (start > cursor) frag.appendChild(document.createTextNode(text.slice(cursor, start)));

      const canonical = lowerToCanonical.get(found.toLowerCase()) || found;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "term-btn";
      btn.dataset.term = canonical;
      btn.textContent = found;
      frag.appendChild(btn);

      cursor = start + found.length;
      match = pattern.exec(text);
    }

    if (cursor < text.length) frag.appendChild(document.createTextNode(text.slice(cursor)));
    node.parentNode.replaceChild(frag, node);
  }
}

function renderMetricPill(text) {
  if (!text) return "";
  const upper = text.toUpperCase();
  const cls = upper.includes("UP") || upper.includes("STRONG")
    ? "pill good"
    : upper.includes("DOWN") || upper.includes("WEAK") || upper.includes("ELEVATED")
      ? "pill warning"
      : "pill";
  return `<span class="${cls}">${text}</span>`;
}

function valuationBandClass(band) {
  const key = (band || "").toLowerCase();
  if (key.includes("under")) return "valuation-pill valuation-undervalued";
  if (key.includes("over")) return "valuation-pill valuation-overvalued";
  return "valuation-pill valuation-fair";
}

function renderValuationBadge(band, score) {
  const key = (band || "fair").toLowerCase();
  const emoji = key.includes("under") ? "??" : key.includes("over") ? "??" : "?";
  const cls = valuationBandClass(key);
  const scoreText = (typeof score === "number" && !Number.isNaN(score)) ? ` (${score.toFixed(1)})` : "";
  return `<span class="${cls}">${emoji} ${key.toUpperCase()}${scoreText}</span>`;
}

function renderNewsList(targetId, items, fallbackAsset) {
  const target = document.getElementById(targetId);
  if (!target) return;

  if (!items || !items.length) {
    const query = fallbackAsset ? `${fallbackAsset} asset` : "finance markets";
    target.innerHTML = `
      <li class="news-item">
        <p class="muted">News snapshot unavailable right now.</p>
        <a href="https://news.google.com/search?q=${encodeURIComponent(query)}" target="_blank" rel="noopener noreferrer">Open Google News search</a>
      </li>
    `;
    return;
  }

  target.innerHTML = items.map((item) => `
    <li class="news-item">
      <a href="${item.url || item.link || '#'}" target="_blank" rel="noopener noreferrer">${item.title || "Untitled"}</a>
      <div class="timestamp">${item.source || "Unknown"}${(item.published_at || item.pubDate) ? ` • ${new Date(item.published_at || item.pubDate).toUTCString()}` : ""}</div>
    </li>
  `).join("");
}

function renderAbout(id, about) {
  const el = document.getElementById(id);
  if (!el) return;

  if (!about || Object.keys(about).length === 0) {
    el.innerHTML = "<p class='muted'>No asset background available yet.</p>";
    return;
  }

  el.innerHTML = `
    <p><strong>What it is:</strong> ${about.what_it_is || "N/A"}</p>
    <p><strong>What it represents:</strong> ${about.what_it_represents || "N/A"}</p>
    <p><strong>Who or what it belongs to:</strong> ${about.who_or_what || "N/A"}</p>
    <p><strong>How it works:</strong> ${about.how_it_works || "N/A"}</p>
  `;
  highlightTerms(el);
}

async function drawAssetChart(assetId, canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  let payload;
  try {
    const url = `https://api.coingecko.com/api/v3/coins/${assetId}/market_chart?vs_currency=usd&days=365&interval=daily`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error("chart fetch failed");
    payload = await res.json();
  } catch (_) {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#6d6480";
    ctx.font = "14px Poppins, sans-serif";
    ctx.fillText("Chart unavailable right now.", 14, 28);
    return;
  }

  const raw = (payload.prices || []).map((row) => Number(row[1])).filter(Number.isFinite);
  if (!raw.length) return;
  const points = raw.length > 180 ? raw.slice(-180) : raw;

  const ma = points.map((_, idx) => {
    if (idx < 199) return null;
    const win = points.slice(idx - 199, idx + 1);
    return win.reduce((sum, v) => sum + v, 0) / win.length;
  });

  const allValues = points.concat(ma.filter((v) => v != null));
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const span = max - min || 1;

  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const cssWidth = canvas.clientWidth || 900;
  const cssHeight = canvas.clientHeight || 260;
  canvas.width = Math.floor(cssWidth * dpr);
  canvas.height = Math.floor(cssHeight * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const pad = 28;
  const width = cssWidth;
  const height = cssHeight;

  ctx.clearRect(0, 0, width, height);

  for (let i = 0; i < 4; i += 1) {
    const y = pad + ((height - pad * 2) * i) / 3;
    ctx.strokeStyle = "#efe5ff";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad, y);
    ctx.lineTo(width - pad, y);
    ctx.stroke();
  }

  const xFor = (index) => pad + ((width - pad * 2) * index) / Math.max(points.length - 1, 1);
  const yFor = (value) => height - pad - ((value - min) / span) * (height - pad * 2);

  ctx.beginPath();
  points.forEach((value, index) => {
    const x = xFor(index);
    const y = yFor(value);
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.lineWidth = 2.6;
  ctx.strokeStyle = "#7655d9";
  ctx.stroke();

  ctx.beginPath();
  let started = false;
  ma.forEach((value, index) => {
    if (value == null) return;
    const x = xFor(index);
    const y = yFor(value);
    if (!started) {
      ctx.moveTo(x, y);
      started = true;
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.lineWidth = 2;
  ctx.strokeStyle = "#f2a66f";
  ctx.stroke();

  ctx.fillStyle = "#7655d9";
  ctx.font = "12px Poppins, sans-serif";
  ctx.fillText("Price", width - 110, 20);
  ctx.fillStyle = "#f2a66f";
  ctx.fillText("200D MA", width - 56, 20);
}

async function setLivePrice(assetId, targetId) {
  const target = document.getElementById(targetId);
  if (!target) return;

  try {
    const url = `https://api.coingecko.com/api/v3/simple/price?ids=${assetId}&vs_currencies=usd&include_24hr_change=true`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return;
    const data = await res.json();
    const row = data[assetId];
    if (!row) return;
    const pct = Number(row.usd_24h_change || 0);
    target.innerHTML = `${fmtPrice(row.usd)} <span class="${pctClass(pct)}">(${fmtPct(pct)} 24h)</span>`;
  } catch (_) {}
}

function setupAccordion(buttonId, sectionId) {
  const button = document.getElementById(buttonId);
  const section = document.getElementById(sectionId);
  if (!button || !section) return;

  button.addEventListener("click", () => {
    section.classList.toggle("hidden");
    const expanded = !section.classList.contains("hidden");
    button.textContent = `${expanded ? "-" : "+"} Show full analysis`;
  });
}

function renderAssetCards(assets) {
  return assets.map((asset) => {
    const href = asset.details_page || `asset.html?asset=${asset.asset}`;
    const p7 = asset.price?.change_7d_pct;
    const source = asset.source?.short_term || "snapshot";
    const updated = fmtDateTime(asset.updated_at);
    const periodLabel = p7 == null ? "24H change" : "7D change";
    const periodValue = p7 == null ? asset.price?.change_24h_pct : p7;

    return `
      <article class="card">
        <h3>${asset.name} (${asset.symbol})</h3>
        <div class="metric">${fmtPrice(asset.price?.current_usd)}</div>
        <p class="muted">${periodLabel}: <span class="${pctClass(periodValue)}">${fmtPct(periodValue)}</span></p>
        <div class="pill-row">
          ${renderMetricPill(asset.indicators?.trend || "")}
          ${renderMetricPill(asset.indicators?.momentum || "")}
          ${renderMetricPill(asset.indicators?.volatility || "")}
        </div>
        <div class="meta-row">
          <span class="meta-chip"><strong>Source:</strong> ${source}</span>
          <span class="meta-chip"><strong>Updated:</strong> ${updated}</span>
        </div>
        <p><a class="tab" href="${href}">Open ${asset.symbol}</a></p>
      </article>
    `;
  }).join("");
}

async function getIndexPayload() {
  return fetchJsonWithFallback([
    "data/assets/index.json",
    "../data/assets/index.json"
  ]);
}

async function getAssetPayload(assetId) {
  return fetchJsonWithFallback([
    `data/assets/${assetId}.json`,
    `../data/assets/${assetId}.json`
  ]);
}

async function initOverviewPage() {
  const payload = await getIndexPayload();
  const macroContainer = document.getElementById("macro-content");
  macroContainer.innerHTML = markdownToHtml(payload.macro_markdown || "");
  highlightTerms(macroContainer);

  setMetaRow("overview-macro-meta", [
    { label: "Updated", value: fmtDateTime(payload.generated_at) },
    { label: "Source", value: "normalized snapshot" }
  ]);

  document.getElementById("asset-cards").innerHTML = renderAssetCards(payload.assets || []);
  highlightTerms(document.getElementById("asset-cards"));
  renderNewsList("overview-news", payload.overview_news || [], "asset market");

  setMetaRow("overview-news-meta", [
    { label: "News updated", value: fmtDateTime(payload.generated_at) },
    { label: "Feed", value: "cached RSS" }
  ]);
}

async function initAssetPage(assetId) {
  const payload = await getAssetPayload(assetId);

  const title = document.getElementById("asset-title");
  if (title) title.textContent = `${payload.name} (${payload.symbol})`;

  const subtitle = document.getElementById("asset-subtitle");
  if (subtitle) subtitle.textContent = payload.market_type === "crypto"
    ? "Crypto asset profile, analysis, and news."
    : "Traditional asset profile, snapshot, and news.";

  renderAbout("asset-about", payload.about);

  const summary = document.getElementById("asset-summary");
  const p7 = payload.price?.change_7d_pct;
  const p30 = payload.price?.change_30d_pct;
  const p24 = payload.price?.change_24h_pct;
  const updated = fmtDateTime(payload.updated_at);
  const source = payload.source?.short_term || "unknown";
  const sideWindow = p7 == null ? `24H: <span class="${pctClass(p24)}">${fmtPct(p24)}</span>` : `7D: <span class="${pctClass(p7)}">${fmtPct(p7)}</span> | 30D: <span class="${pctClass(p30)}">${fmtPct(p30)}</span>`;

  if (summary) {
    const band = payload.valuation?.band || "fair";
    const summaryLine = payload.valuation?.summary_line || "";
    const score = payload.valuation?.score;
    summary.innerHTML = `
      <p class="metric" id="live-price">${fmtPrice(payload.price?.current_usd)}</p>
      <p class="muted">${sideWindow}</p>
      ${summaryLine ? `<p class="longterm-line"><strong>${summaryLine}</strong></p>` : ""}
      <div class="pill-row">
        ${renderValuationBadge(band, score)}
        ${renderMetricPill(payload.indicators?.trend || "")}
        ${renderMetricPill(payload.indicators?.momentum || "")}
        ${renderMetricPill(payload.indicators?.volatility || "")}
      </div>
    `;
    highlightTerms(summary);
  }

  setMetaRow("asset-summary-meta", [
    { label: "Updated", value: updated },
    { label: "Source", value: source }
  ]);

  const analysis = document.getElementById("analysis-content");
  if (analysis) {
    analysis.innerHTML = markdownToHtml(payload.analysis_markdown || "No analysis available.");
    highlightTerms(analysis);
  }

  setMetaRow("asset-analysis-meta", [
    { label: "Updated", value: updated },
    { label: "Source", value: source }
  ]);

  setMetaRow("asset-chart-meta", [
    { label: "Window", value: payload.market_type === "crypto" ? "1Y sparkline + 200D MA" : "snapshot" },
    { label: "Price source", value: source }
  ]);

  setupAccordion("analysis-toggle", "analysis-content");

  if (payload.market_type === "crypto") {
    await drawAssetChart(assetId, "price-chart");
    await setLivePrice(assetId, "live-price");
    setInterval(() => setLivePrice(assetId, "live-price"), 60000);
  }

  renderNewsList("asset-news", payload.news || [], assetId);
  setMetaRow("asset-news-meta", [
    { label: "News updated", value: fmtDateTime(payload.source?.news_generated_at) },
    { label: "Feed", value: "cached RSS" }
  ]);
}

function getAssetFromQuery() {
  const params = new URLSearchParams(window.location.search);
  return params.get("asset") || "bitcoin";
}

async function initNewsPage() {
  try {
    const payload = await getIndexPayload();
    const all = payload.overview_news || [];
    renderNewsList("news-results", all, "asset market");

    setMetaRow("news-feed-meta", [
      { label: "Updated", value: fmtDateTime(payload.generated_at) },
      { label: "Source", value: "normalized snapshot" }
    ]);

    const buttons = document.querySelectorAll("[data-filter]");
    buttons.forEach((btn) => {
      btn.addEventListener("click", async () => {
        buttons.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const filter = btn.dataset.filter;

        if (filter === "all") {
          renderNewsList("news-results", all, "asset market");
          return;
        }

        const asset = await getAssetPayload(filter);
        renderNewsList("news-results", asset.news || [], filter);
        setMetaRow("news-feed-meta", [
          { label: "Updated", value: fmtDateTime(asset.source?.news_generated_at) },
          { label: "Source", value: "asset snapshot" }
        ]);
      });
    });
  } catch (_) {
    renderNewsList("news-results", [], "asset market");
  }
}

async function boot() {
  setActiveTab();
  initGlossary();

  const page = document.body.dataset.page;
  try {
    if (page === "overview") await initOverviewPage();
    if (page === "btc") await initAssetPage("bitcoin");
    if (page === "eth") await initAssetPage("ethereum");
    if (page === "asset") await initAssetPage(getAssetFromQuery());
    if (page === "news") await initNewsPage();
  } catch (_) {
    document.querySelectorAll("[data-error-target]").forEach((el) => {
      el.textContent = "Unable to load normalized data snapshot. Please refresh soon.";
    });
  }
}

document.addEventListener("DOMContentLoaded", boot);



