// GET /api/archive-sections?url=/daily-qt/ntqt/2018-03-07/
// 回傳 { status:"success", section2, section3, section4 }（該篇典藏文章的默想／分享／回應）
const BASE = "https://cmtc.tw";
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)";

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET,OPTIONS",
  "access-control-allow-headers": "content-type",
};

function json(payload, status = 200, extra = {}) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      ...CORS,
      ...extra,
    },
  });
}

export function onRequestOptions() {
  return new Response(null, { status: 204, headers: CORS });
}

function toText(html) {
  return html
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/(p|div|li|h[1-6]|blockquote)>/gi, "\n\n")
    .replace(/<[^>]+>/g, "")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&#126;/g, "~")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

// 彈性匹配 1~4 段標題（含 2016 早期較長的標題如「2.有感動的經文並完成默想（...）」）
const HEADING_RE = /<(?:strong|b|h[2-4])[^>]*>\s*([1-4])\s*[\.、]?\s*[^<]{2,60}<\/(?:strong|b|h[2-4])>/gi;

function extractSections(body) {
  const marks = [];
  for (const m of body.matchAll(HEADING_RE)) {
    marks.push({ num: Number(m[1]), start: m.index, end: m.index + m[0].length });
  }
  const out = {};
  for (let i = 0; i < marks.length; i++) {
    const nextStart = i + 1 < marks.length ? marks[i + 1].start : body.length;
    out[marks[i].num] = toText(body.slice(marks[i].end, nextStart));
  }
  return out;
}

async function loadArticleHtml(context, path) {
  // 優先使用 Cloudflare Pages 內建 ASSETS 站內直讀，免公網繞行
  if (context.env && context.env.ASSETS && typeof context.env.ASSETS.fetch === "function") {
    const assetUrl = new URL(path, context.request.url);
    const r = await context.env.ASSETS.fetch(assetUrl);
    if (r.ok) return r.text();
  }
  const r = await fetch(BASE + path, { headers: { "user-agent": UA } });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.text();
}

export async function onRequestGet(context) {
  const params = new URL(context.request.url).searchParams;
  let path = params.get("url") || "";
  if (path && !path.startsWith("/")) path = "/" + path;
  if (!/^\/daily-qt\/(otqt|ntqt)\/[0-9A-Za-z._-]+\/?$/.test(path)) {
    return json({ status: "error", error: "url 參數需為 /daily-qt/(otqt|ntqt)/<日期>/" }, 400);
  }
  if (!path.endsWith("/")) path += "/";

  let html;
  try {
    html = await loadArticleHtml(context, path);
  } catch (e) {
    return json({ status: "error", error: `文章讀取失敗（${e.message || "網路錯誤"}）` }, 502);
  }

  // 只取內文容器，避免抓到側欄／頁尾
  const c0 = html.indexOf("post__content");
  const c1 = html.indexOf("</article>", c0 > 0 ? c0 : 0);
  const body = c0 > 0 && c1 > c0 ? html.slice(c0, c1) : html;

  const sections = extractSections(body);
  const s2 = sections[2] || "";
  const s3 = sections[3] || "";
  const s4 = sections[4] || "";

  if (!s3 && !s4) {
    return json({ status: "error", error: "這篇文章沒有「分享默想經文／今天的回應」段落" }, 404);
  }
  return json(
    { status: "success", url: path, section2: s2, section3: s3, section4: s4 },
    200,
    { "cache-control": "public, max-age=604800" },
  );
}
