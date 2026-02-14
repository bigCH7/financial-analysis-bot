const GLOSSARY = {
  "RSI": "Relative Strength Index, a momentum indicator from 0 to 100. Above 70 is often called overbought, below 30 oversold.",
  "MA50": "50-day moving average. It smooths price data to show medium-term trend direction.",
  "MA200": "200-day moving average. A widely used long-term trend baseline.",
  "200-day average": "Average closing price over the last 200 days. Often used to judge cycle positioning.",
  "ETH/BTC ratio": "Ethereum price divided by Bitcoin price. It tracks ETH strength relative to BTC.",
  "market cap": "Total value of an asset supply at current price.",
  "volatility": "How fast and how far price moves over time.",
  "Bullish": "Expectation that trend is likely upward.",
  "Bearish": "Expectation that trend is likely downward.",
  "Undervalued": "Price appears low relative to chosen benchmarks.",
  "Overextended": "Price appears stretched versus trend and may face pullback risk.",
  "overbought": "Momentum is very strong and short-term reversal risk can rise.",
  "oversold": "Momentum is very weak and rebound potential can increase.",
  "support": "A level where buying has often slowed declines.",
  "resistance": "A level where selling has often slowed advances."
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

function renderNewsList(targetId, items, fallbackAsset) {
  const target = document.getElementById(targetId);
  if (!target) return;

  if (!items || !items.length) {
    const query = fallbackAsset ? `${fallbackAsset} crypto` : "bitcoin ethereum crypto";
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
    const href = asset.details_page || "";
    const p7 = asset.price?.change_7d_pct;
    const source = asset.source?.short_term || "snapshot";
    const updated = fmtDateTime(asset.updated_at);
    const openAction = href
      ? `<p><a class="tab" href="${href}">Open ${asset.symbol}</a></p>`
      : `<p class="muted">Details page: coming soon</p>`;
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
        ${openAction}
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
  renderNewsList("overview-news", payload.overview_news || [], "crypto market");

  setMetaRow("overview-news-meta", [
    { label: "News updated", value: fmtDateTime(payload.generated_at) },
    { label: "Feed", value: "cached RSS" }
  ]);
}

async function initAssetPage(assetId) {
  const payload = await getAssetPayload(assetId);

  const summary = document.getElementById("asset-summary");
  const p7 = payload.price?.change_7d_pct;
  const p30 = payload.price?.change_30d_pct;
  const updated = fmtDateTime(payload.updated_at);
  const source = payload.source?.short_term || "unknown";

  summary.innerHTML = `
    <p class="metric" id="live-price">${fmtPrice(payload.price?.current_usd)}</p>
    <p class="muted">7D: <span class="${pctClass(p7)}">${fmtPct(p7)}</span> | 30D: <span class="${pctClass(p30)}">${fmtPct(p30)}</span></p>
    <div class="pill-row">
      ${renderMetricPill(payload.indicators?.trend || "")}
      ${renderMetricPill(payload.indicators?.momentum || "")}
      ${renderMetricPill(payload.indicators?.volatility || "")}
      ${payload.valuation?.verdict ? `<span class="pill">${payload.valuation.verdict}</span>` : ""}
    </div>
  `;

  setMetaRow("asset-summary-meta", [
    { label: "Updated", value: updated },
    { label: "Source", value: source }
  ]);

  const analysis = document.getElementById("analysis-content");
  analysis.innerHTML = markdownToHtml(payload.analysis_markdown || "No analysis available.");
  highlightTerms(analysis);

  setMetaRow("asset-analysis-meta", [
    { label: "Updated", value: updated },
    { label: "Source", value: source }
  ]);

  setMetaRow("asset-chart-meta", [
    { label: "Window", value: "30D live" },
    { label: "Price source", value: "CoinGecko" }
  ]);

  setupAccordion("analysis-toggle", "analysis-content");
  await drawAssetChart(assetId, "price-chart");
  await setLivePrice(assetId, "live-price");
  setInterval(() => setLivePrice(assetId, "live-price"), 60000);

  renderNewsList("asset-news", payload.news || [], assetId);
  setMetaRow("asset-news-meta", [
    { label: "News updated", value: fmtDateTime(payload.source?.news_generated_at) },
    { label: "Feed", value: "cached RSS" }
  ]);
}

async function initNewsPage() {
  try {
    const payload = await getIndexPayload();
    const all = payload.overview_news || [];
    renderNewsList("news-results", all, "crypto market");

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
          renderNewsList("news-results", all, "crypto market");
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
    renderNewsList("news-results", [], "crypto market");
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
    if (page === "news") await initNewsPage();
  } catch (_) {
    document.querySelectorAll("[data-error-target]").forEach((el) => {
      el.textContent = "Unable to load normalized data snapshot. Please refresh soon.";
    });
  }
}

document.addEventListener("DOMContentLoaded", boot);

