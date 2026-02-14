const GLOSSARY = {
  "RSI": "Relative Strength Index, a momentum indicator from 0 to 100. Above 70 is often called overbought, below 30 oversold.",
  "MA50": "50-day moving average. It smooths price data to show medium-term trend direction.",
  "MA200": "200-day moving average. A widely used long-term trend baseline.",
  "200-day average": "Average closing price over the last 200 days. Often used to judge long-cycle valuation.",
  "ETH/BTC ratio": "Ethereum price divided by Bitcoin price. It tracks whether ETH is outperforming or underperforming BTC.",
  "market cap": "Total value of an asset supply at current price. Formula: price x circulating supply.",
  "volatility": "How fast and how far price moves over time. Higher volatility means larger swings.",
  "Bullish": "Expectation that price trend is likely to continue upward.",
  "Bearish": "Expectation that price trend is likely to continue downward.",
  "Undervalued": "Price appears low relative to selected valuation benchmarks.",
  "Overextended": "Price has moved far above trend or valuation norms and may be at higher pullback risk.",
  "overbought": "A condition where momentum is very strong and price may be stretched in the short term.",
  "oversold": "A condition where momentum is very weak and price may be stretched to the downside.",
  "support": "A price area where buying has historically been strong enough to slow declines.",
  "resistance": "A price area where selling has historically been strong enough to slow advances."
};

const FEED_SOURCES = [
  { name: "CoinDesk", url: "https://www.coindesk.com/arc/outboundfeeds/rss/" },
  { name: "Cointelegraph", url: "https://cointelegraph.com/rss" }
];

function escapeRegExp(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

async function fetchTextWithFallback(paths) {
  for (const path of paths) {
    try {
      const res = await fetch(path, { cache: "no-store" });
      if (res.ok) {
        return await res.text();
      }
    } catch (_) {}
  }
  throw new Error("Unable to load text from fallback paths.");
}

async function fetchJsonWithFallback(paths) {
  for (const path of paths) {
    try {
      const res = await fetch(path, { cache: "no-store" });
      if (res.ok) {
        return await res.json();
      }
    } catch (_) {}
  }
  throw new Error("Unable to load JSON from fallback paths.");
}

function extractSection(markdown, heading) {
  const marker = `## ${heading}`;
  const start = markdown.indexOf(marker);
  if (start === -1) {
    return "";
  }

  const rest = markdown.slice(start);
  const next = rest.indexOf("\n## ", marker.length);
  return (next === -1 ? rest : rest.slice(0, next)).trim();
}

function getLineValue(section, label) {
  const pattern = new RegExp(`- \\*\\*${escapeRegExp(label)}:\\*\\*\\s*([^\\n]+)`, "i");
  const match = section.match(pattern);
  return match ? match[1].trim() : "N/A";
}

function formatPctClass(valueText) {
  if (valueText.startsWith("-")) return "metric-negative";
  if (valueText.startsWith("+")) return "metric-positive";
  if (valueText.startsWith("0") || valueText.startsWith("N")) return "";
  return "metric-positive";
}

function markdownToHtml(markdown) {
  if (window.marked && typeof window.marked.parse === "function") {
    return window.marked.parse(markdown);
  }
  return `<pre>${markdown}</pre>`;
}

function showGlossary(term, definition) {
  const modal = document.getElementById("glossary-modal");
  document.getElementById("glossary-title").textContent = term;
  document.getElementById("glossary-body").textContent = definition;
  modal.classList.remove("hidden");
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
  while (walker.nextNode()) {
    textNodes.push(walker.currentNode);
  }

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
      if (start > cursor) {
        frag.appendChild(document.createTextNode(text.slice(cursor, start)));
      }

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

    if (cursor < text.length) {
      frag.appendChild(document.createTextNode(text.slice(cursor)));
    }

    node.parentNode.replaceChild(frag, node);
  }
}

function setActiveTab() {
  const page = document.body.dataset.page;
  document.querySelectorAll(".tab").forEach((tab) => {
    if (tab.dataset.page === page) {
      tab.classList.add("active");
    }
  });
}

function renderMetricPill(text) {
  const cls = text.includes("UP") || text.includes("BULL") || text.includes("POSITIVE")
    ? "pill good"
    : text.includes("DOWN") || text.includes("WEAK") || text.includes("ELEVATED")
      ? "pill warning"
      : "pill";
  return `<span class="${cls}">${text}</span>`;
}

function renderMarketCards(shortMd, analysisLatest) {
  const btcSection = extractSection(shortMd, "Bitcoin (BTC)");
  const ethSection = extractSection(shortMd, "Ethereum (ETH)");

  const btc = analysisLatest.find((row) => row.asset === "bitcoin") || {};
  const eth = analysisLatest.find((row) => row.asset === "ethereum") || {};

  const cards = [
    {
      id: "bitcoin",
      title: "Bitcoin",
      symbol: "BTC",
      section: btcSection,
      fallbackPrice: btc.price
    },
    {
      id: "ethereum",
      title: "Ethereum",
      symbol: "ETH",
      section: ethSection,
      fallbackPrice: eth.price
    }
  ];

  return cards.map((card) => {
    const price = getLineValue(card.section, "Current price");
    const change7 = getLineValue(card.section, "7D change");
    const trend = getLineValue(card.section, "Trend");
    const momentum = getLineValue(card.section, "Momentum");
    const volatility = getLineValue(card.section, "Volatility");

    const priceView = price === "N/A" && card.fallbackPrice
      ? `$${Number(card.fallbackPrice).toLocaleString()}`
      : price;

    return `
      <article class="card">
        <h3>${card.title} (${card.symbol})</h3>
        <div class="metric">${priceView}</div>
        <p class="muted">7D change: <span class="${formatPctClass(change7)}">${change7}</span></p>
        <div class="pill-row">
          ${renderMetricPill(trend)}
          ${renderMetricPill(momentum)}
          ${renderMetricPill(volatility)}
        </div>
        <p><a class="tab" href="${card.id === "bitcoin" ? "btc.html" : "eth.html"}">Open ${card.symbol}</a></p>
      </article>
    `;
  }).join("");
}

async function fetchFeedItems(assetKeyword) {
  const items = [];

  for (const feed of FEED_SOURCES) {
    const endpoint = `https://api.allorigins.win/raw?url=${encodeURIComponent(feed.url)}`;

    try {
      const response = await fetch(endpoint, { cache: "no-store" });
      if (!response.ok) continue;
      const xml = await response.text();
      const doc = new DOMParser().parseFromString(xml, "application/xml");
      const rows = Array.from(doc.querySelectorAll("item"));

      for (const row of rows) {
        const title = row.querySelector("title")?.textContent?.trim() || "Untitled";
        const link = row.querySelector("link")?.textContent?.trim() || "#";
        const pubDate = row.querySelector("pubDate")?.textContent?.trim() || "";
        const lower = `${title}`.toLowerCase();

        if (assetKeyword && !lower.includes(assetKeyword)) {
          continue;
        }

        items.push({ title, link, pubDate, source: feed.name });
      }
    } catch (_) {}
  }

  items.sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate));
  return items.slice(0, 10);
}

function renderNewsList(targetId, items, fallbackAsset) {
  const target = document.getElementById(targetId);
  if (!target) return;

  if (!items.length) {
    const query = fallbackAsset ? `${fallbackAsset} crypto` : "bitcoin ethereum crypto";
    target.innerHTML = `
      <li class="news-item">
        <p class="muted">Live feeds unavailable right now.</p>
        <a href="https://news.google.com/search?q=${encodeURIComponent(query)}" target="_blank" rel="noopener noreferrer">Open live search on Google News</a>
      </li>
    `;
    return;
  }

  target.innerHTML = items.map((item) => `
    <li class="news-item">
      <a href="${item.link}" target="_blank" rel="noopener noreferrer">${item.title}</a>
      <div class="timestamp">${item.source}${item.pubDate ? ` • ${new Date(item.pubDate).toUTCString()}` : ""}</div>
    </li>
  `).join("");
}

async function drawAssetChart(assetId, canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  let payload;
  try {
    const url = `https://api.coingecko.com/api/v3/coins/${assetId}/market_chart?vs_currency=usd&days=30&interval=daily`;
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

  const points = (payload.prices || []).map((row) => Number(row[1])).filter(Number.isFinite);
  if (!points.length) return;

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
  const min = Math.min(...points);
  const max = Math.max(...points);
  const span = max - min || 1;

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

  ctx.beginPath();
  points.forEach((value, index) => {
    const x = pad + ((width - pad * 2) * index) / (points.length - 1);
    const y = height - pad - ((value - min) / span) * (height - pad * 2);
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.lineWidth = 2.5;
  ctx.strokeStyle = "#7655d9";
  ctx.stroke();

  ctx.fillStyle = "#6d6480";
  ctx.font = "12px Poppins, sans-serif";
  ctx.fillText(`30D range: $${min.toLocaleString(undefined, { maximumFractionDigits: 0 })} - $${max.toLocaleString(undefined, { maximumFractionDigits: 0 })}`, pad, 18);
}

async function setLivePrice(assetId, targetId) {
  const target = document.getElementById(targetId);
  if (!target) return;

  const url = `https://api.coingecko.com/api/v3/simple/price?ids=${assetId}&vs_currencies=usd&include_24hr_change=true`;

  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return;
    const data = await res.json();
    const row = data[assetId];
    if (!row) return;
    const price = Number(row.usd || 0).toLocaleString();
    const pct = Number(row.usd_24h_change || 0);
    const pctText = `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
    target.innerHTML = `$${price} <span class="${pct >= 0 ? "metric-positive" : "metric-negative"}">(${pctText} 24h)</span>`;
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

async function initOverviewPage() {
  const [longTerm, shortTerm, latestJson] = await Promise.all([
    fetchTextWithFallback(["reports/long_term_report.md", "../reports/long_term_report.md"]),
    fetchTextWithFallback(["reports/short_term.md", "../reports/short_term.md"]),
    fetchJsonWithFallback(["data/analysis_latest.json", "../data/analysis_latest.json"])
  ]);

  const firstAsset = longTerm.indexOf("\n## ");
  const macro = firstAsset > 0 ? longTerm.slice(0, firstAsset) : longTerm;

  const macroContainer = document.getElementById("macro-content");
  macroContainer.innerHTML = markdownToHtml(macro.trim());
  highlightTerms(macroContainer);

  document.getElementById("asset-cards").innerHTML = renderMarketCards(shortTerm, latestJson);

  const newsItems = await fetchFeedItems("");
  renderNewsList("overview-news", newsItems, "crypto market");
}

async function initAssetPage(assetId, heading) {
  const [longTerm, shortTerm] = await Promise.all([
    fetchTextWithFallback(["reports/long_term_report.md", "../reports/long_term_report.md"]),
    fetchTextWithFallback(["reports/short_term.md", "../reports/short_term.md"])
  ]);

  const longSection = extractSection(longTerm, heading);
  const shortSection = extractSection(shortTerm, heading);

  const summary = document.getElementById("asset-summary");
  const price = getLineValue(shortSection, "Current price");
  const change7 = getLineValue(shortSection, "7D change");
  const change30 = getLineValue(shortSection, "30D change");
  const trend = getLineValue(shortSection, "Trend");
  const momentum = getLineValue(shortSection, "Momentum");
  const volatility = getLineValue(shortSection, "Volatility");

  summary.innerHTML = `
    <p class="metric" id="live-price">${price}</p>
    <p class="muted">7D: <span class="${formatPctClass(change7)}">${change7}</span> | 30D: <span class="${formatPctClass(change30)}">${change30}</span></p>
    <div class="pill-row">
      ${renderMetricPill(trend)}
      ${renderMetricPill(momentum)}
      ${renderMetricPill(volatility)}
    </div>
  `;

  const analysisContainer = document.getElementById("analysis-content");
  const merged = `${longSection}\n\n---\n\n### Short-Term Context\n\n${shortSection}`;
  analysisContainer.innerHTML = markdownToHtml(merged);
  highlightTerms(analysisContainer);

  setupAccordion("analysis-toggle", "analysis-content");
  await drawAssetChart(assetId, "price-chart");
  await setLivePrice(assetId, "live-price");
  setInterval(() => setLivePrice(assetId, "live-price"), 60000);

  const keyword = assetId === "bitcoin" ? "bitcoin" : "ethereum";
  const newsItems = await fetchFeedItems(keyword);
  renderNewsList("asset-news", newsItems, keyword);
}

async function initNewsPage() {
  const allNews = await fetchFeedItems("");
  renderNewsList("news-results", allNews, "crypto market");

  const buttons = document.querySelectorAll("[data-filter]");
  buttons.forEach((btn) => {
    btn.addEventListener("click", async () => {
      buttons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const filter = btn.dataset.filter;
      const keyword = filter === "all" ? "" : filter;
      const filtered = await fetchFeedItems(keyword);
      renderNewsList("news-results", filtered, keyword || "crypto market");
    });
  });
}

async function boot() {
  setActiveTab();
  initGlossary();

  const page = document.body.dataset.page;

  try {
    if (page === "overview") {
      await initOverviewPage();
    }

    if (page === "btc") {
      await initAssetPage("bitcoin", "Bitcoin (BTC)");
    }

    if (page === "eth") {
      await initAssetPage("ethereum", "Ethereum (ETH)");
    }

    if (page === "news") {
      await initNewsPage();
    }
  } catch (error) {
    const errorTargets = document.querySelectorAll("[data-error-target]");
    errorTargets.forEach((el) => {
      el.textContent = "Unable to load fresh data right now. Please refresh in a minute.";
    });
  }
}

document.addEventListener("DOMContentLoaded", boot);
