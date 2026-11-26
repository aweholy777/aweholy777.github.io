// GET /api/daily-reference?date=YYYY-MM-DD
// 回傳 { status:"success", reference:"哥林多後書 4：1∼10", source:"duranno|cgn-youtube", date }
// 來源順序：duranno.tw 直抓 → CGN 中文《活潑的生命》YouTube 頻道標題
const DURANNO = "https://www.duranno.tw/livinglife/index.php/daily";
const CGN_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id=UCqUnxXxHSFb6At-njlSX9AQ";
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)";

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET,OPTIONS",
  "access-control-allow-headers": "content-type",
};

function json(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      ...CORS,
    },
  });
}

export function onRequestOptions() {
  return new Response(null, { status: 204, headers: CORS });
}

function taipeiToday() {
  return new Date(Date.now() + 8 * 3600 * 1000).toISOString().slice(0, 10);
}

async function fromDuranno() {
  const r = await fetch(DURANNO, { headers: { "user-agent": UA } });
  if (!r.ok) return null;
  const html = await r.text();
  const m = html.match(/<div class="range">\s*([^<]+?)\s*<\/div>/);
  return m && m[1].trim() ? m[1].trim() : null;
}

async function fromCgn(date) {
  const r = await fetch(CGN_RSS, { headers: { "user-agent": UA } });
  if (!r.ok) return null;
  const xml = await r.text();
  const ymd = date.replace(/-/g, "");
  for (const m of xml.matchAll(/<title>([^<]*)<\/title>/g)) {
    const t = m[1];
    if (!t.includes("活潑的生命") || !t.includes(ymd)) continue;
    const mm = t.match(/[（(]\s*([^（）()]+?)\s*(\d+)\s*[：:]\s*(\d+)\s*[~∼\-–－—～]\s*(?:(\d+)\s*[：:])?\s*(\d+)\s*[）)]/);
    if (!mm) continue;
    const book = mm[1].trim();
    const reference = mm[4]
      ? `${book}${mm[2]}：${mm[3]}∼${mm[4]}：${mm[5]}`
      : `${book}${mm[2]}：${mm[3]}∼${mm[5]}`;
    return { reference, videoTitle: t.replace(/&amp;/g, "&").replace(/&#39;/g, "'").replace(/&quot;/g, '"') };
  }
  return null;
}

export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  const today = taipeiToday();
  const date = url.searchParams.get("date") || today;
  // duranno /daily 永遠只回傳「今天」，查詢非今日的歷史日期時略過它、直接走 CGN RSS
  if (date === today) {
    try {
      const ref = await fromDuranno();
      if (ref) return json({ status: "success", reference: ref, source: "duranno", date });
    } catch (e) { /* 維護中或憑證問題，往下備援 */ }
  }
  try {
    const hit = await fromCgn(date);
    if (hit) {
      return json({
        status: "success",
        reference: hit.reference,
        videoTitle: hit.videoTitle,
        source: "cgn-youtube",
        date,
      });
    }
  } catch (e) { /* 繼續 */ }
  const hint = date === today
    ? "無法自動取得今日進度（duranno 與 CGN 都尚未提供或失敗），請手動輸入經文範圍。"
    : `${date} 不在 CGN YouTube 最新 15 天清單內，請手動輸入經文範圍。`;
  return json({ status: "error", error: hint, date }, 502);
}
