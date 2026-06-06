(function () {
  const root = document.querySelector("[data-search-root]");
  if (!root) return;

  const input = root.querySelector("[data-search-input]");
  const sectionSelect = root.querySelector("[data-search-section]");
  const status = root.querySelector("[data-search-status]");
  const results = root.querySelector("[data-search-results]");
  let index = [];

  const escapeHtml = (value) =>
    String(value || "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[char]));

  const normalize = (value) =>
    String(value || "")
      .toLowerCase()
      .replace(/\s+/g, " ")
      .trim();

  const termsFrom = (query) =>
    normalize(query)
      .split(" ")
      .filter(Boolean);

  function makeSnippet(content, terms) {
    const text = String(content || "").replace(/\s+/g, " ").trim();
    if (!text) return "";

    const lower = text.toLowerCase();
    const firstHit = terms
      .map((term) => lower.indexOf(term))
      .filter((position) => position >= 0)
      .sort((a, b) => a - b)[0];
    const start = Math.max(0, (firstHit || 0) - 55);
    const snippet = text.slice(start, start + 150);

    return `${start > 0 ? "..." : ""}${escapeHtml(snippet)}${start + 150 < text.length ? "..." : ""}`;
  }

  function scoreItem(item, terms) {
    const title = normalize(item.title);
    const section = normalize(item.section);
    const date = normalize(item.date);
    const content = normalize(item.content);
    const haystack = `${title} ${section} ${date} ${content}`;

    if (!terms.every((term) => haystack.includes(term))) return 0;

    let score = 1;
    for (const term of terms) {
      if (title.includes(term)) score += 8;
      if (date.includes(term)) score += 5;
      if (section.includes(term)) score += 3;
      if (content.includes(term)) score += 1;
    }

    return score;
  }

  function render() {
    const terms = termsFrom(input.value);
    const section = sectionSelect.value;

    if (!terms.length) {
      status.textContent = `已載入 ${index.length} 篇文章，請輸入關鍵字搜尋。`;
      results.innerHTML = "";
      return;
    }

    const matches = index
      .filter((item) => !section || item.section === section)
      .map((item) => ({ item, score: scoreItem(item, terms) }))
      .filter((entry) => entry.score > 0)
      .sort((a, b) => b.score - a.score || a.item.title.localeCompare(b.item.title, "zh-Hant"))
      .slice(0, 80);

    status.textContent = matches.length
      ? `找到 ${matches.length} 筆結果${matches.length === 80 ? "，只顯示前 80 筆" : ""}。`
      : "找不到符合的文章。";

    results.innerHTML = matches.map(({ item }) => `
      <article class="site-search__result">
        <a class="site-search__title" href="${escapeHtml(item.url)}">${escapeHtml(item.title)}</a>
        <div class="site-search__meta">${escapeHtml(item.section || "文章")}${item.date ? ` · ${escapeHtml(item.date)}` : ""}</div>
        <p class="site-search__snippet">${makeSnippet(item.content || item.summary, terms)}</p>
      </article>
    `).join("");
  }

  function debounce(fn, delay) {
    let timer = 0;
    return function () {
      window.clearTimeout(timer);
      timer = window.setTimeout(fn, delay);
    };
  }

  fetch("/index.json", { credentials: "same-origin" })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((items) => {
      index = Array.isArray(items) ? items : [];
      render();
      input.focus();
    })
    .catch(() => {
      status.textContent = "搜尋索引載入失敗，請稍後再試。";
    });

  input.addEventListener("input", debounce(render, 120));
  sectionSelect.addEventListener("change", render);
}());
