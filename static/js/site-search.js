(function () {
  const root = document.querySelector("[data-search-root]");
  if (!root) return;

  const input = root.querySelector("[data-search-input]");
  const sectionSelect = root.querySelector("[data-search-section]");
  const status = root.querySelector("[data-search-status]");
  const results = root.querySelector("[data-search-results]");

  let shards = [];
  const loadedByUrl = new Map();
  let loadingCount = 0;
  let loadFailed = false;

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

  function allLoadedItems() {
    const out = [];
    for (const items of loadedByUrl.values()) {
      if (Array.isArray(items)) out.push(...items);
    }
    return out;
  }

  function shardsForSection(section) {
    if (!section) return shards;
    if (section === "舊約QT" || section === "新約QT") {
      return shards.filter((s) => s.section === section);
    }
    return shards.filter((s) => !s.section);
  }

  function ensureShardsLoaded(section) {
    const targets = shardsForSection(section).filter((s) => !loadedByUrl.has(s.url));
    if (!targets.length) return;
    loadingCount += targets.length;
    render();
    targets.forEach((shard) => {
      loadedByUrl.set(shard.url, null); // 標記載入中，避免重複請求
      fetch(shard.url, { credentials: "same-origin" })
        .then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        })
        .then((items) => {
          loadedByUrl.set(shard.url, Array.isArray(items) ? items : []);
        })
        .catch(() => {
          loadedByUrl.delete(shard.url);
          loadFailed = true;
        })
        .finally(() => {
          loadingCount = Math.max(0, loadingCount - 1);
          render();
        });
    });
  }

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
    const index = allLoadedItems();
    const loadingSuffix = loadingCount > 0 ? "（其餘分片載入中…）" : "";

    if (!terms.length) {
      if (loadingCount > 0 && !index.length) {
        status.textContent = "正在載入搜尋索引...";
      } else if (loadFailed && !index.length) {
        status.textContent = "搜尋索引載入失敗，請稍後再試。";
      } else {
        status.textContent = `已載入 ${index.length} 篇文章，請輸入關鍵字搜尋。${loadingSuffix}`;
      }
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
      ? `找到 ${matches.length} 筆結果${matches.length === 80 ? "，只顯示前 80 筆" : ""}。${loadingSuffix}`
      : (loadingCount > 0 ? "搜尋索引載入中…" : "找不到符合的文章。");

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
    .then((data) => {
      if (Array.isArray(data)) {
        loadedByUrl.set("/index.json", data);
        render();
      } else if (data && Array.isArray(data.shards)) {
        shards = data.shards;
        ensureShardsLoaded(sectionSelect.value);
      } else {
        throw new Error("格式錯誤");
      }
      input.focus();
    })
    .catch(() => {
      status.textContent = "搜尋索引載入失敗，請稍後再試。";
    });

  input.addEventListener("input", debounce(render, 120));
  sectionSelect.addEventListener("change", () => {
    ensureShardsLoaded(sectionSelect.value);
    render();
  });
}());
