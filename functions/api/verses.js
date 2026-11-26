// GET /api/verses?book=哥林多後書&ch=4&v1=1&v2=10
// 回傳 { status:"success", book, ch, verses:[{chap,sec,text}], truncated }
// 資料來源：信望愛 FHL 和合本（unv）——單次範圍查詢（每章 1 次 HTTP 請求）。
const FHL = "https://bible.fhl.net/json/qb.php";
const UA = "cmtc-daily-qt/1.0 (+https://cmtc.tw)";
const MAX_VERSES = 200;

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET,OPTIONS",
  "access-control-allow-headers": "content-type",
};

const BOOKS = {
  "創世記": "創",
  "出埃及記": "出",
  "利未記": "利",
  "民數記": "民",
  "申命記": "申",
  "約書亞記": "書",
  "士師記": "士",
  "路得記": "得",
  "撒母耳記上": "撒上",
  "撒母耳記下": "撒下",
  "列王紀上": "王上",
  "列王紀下": "王下",
  "歷代志上": "代上",
  "歷代志下": "代下",
  "以斯拉記": "拉",
  "尼希米記": "尼",
  "以斯帖記": "斯",
  "約伯記": "伯",
  "詩篇": "詩",
  "箴言": "箴",
  "傳道書": "傳",
  "雅歌": "歌",
  "以賽亞書": "賽",
  "耶利米書": "耶",
  "耶利米哀歌": "哀",
  "以西結書": "結",
  "但以理書": "但",
  "何西阿書": "何",
  "約珥書": "珥",
  "阿摩司書": "摩",
  "俄巴底亞書": "俄",
  "約拿書": "拿",
  "彌迦書": "彌",
  "那鴻書": "鴻",
  "哈巴谷書": "哈",
  "西番雅書": "番",
  "哈該書": "該",
  "撒迦利亞書": "亞",
  "瑪拉基書": "瑪",
  "馬太福音": "太",
  "馬可福音": "可",
  "路加福音": "路",
  "約翰福音": "約",
  "使徒行傳": "徒",
  "羅馬書": "羅",
  "哥林多前書": "林前",
  "哥林多後書": "林後",
  "加拉太書": "加",
  "以弗所書": "弗",
  "腓立比書": "腓",
  "歌羅西書": "西",
  "帖撒羅尼迦前書": "帖前",
  "帖撒羅尼迦後書": "帖後",
  "提摩太前書": "提前",
  "提摩太後書": "提後",
  "提多書": "多",
  "腓利門書": "門",
  "希伯來書": "來",
  "雅各書": "雅",
  "彼得前書": "彼前",
  "彼得後書": "彼後",
  "約翰一書": "約一",
  "約翰二書": "約二",
  "約翰三書": "約三",
  "猶大書": "猶",
  "啟示錄": "啟",
};

function json(payload, status = 200, extra = {}) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": status === 200 ? "public, max-age=86400" : "no-store",
      ...CORS,
      ...extra,
    },
  });
}

export function onRequestOptions() {
  return new Response(null, { status: 204, headers: CORS });
}

function pick(params, name) {
  const v = parseInt(params.get(name) || "", 10);
  return Number.isFinite(v) && v > 0 ? v : 0;
}

export async function onRequestGet(context) {
  const params = new URL(context.request.url).searchParams;
  const book = (params.get("book") || "").trim();
  const code = BOOKS[book];
  if (!code) {
    return json({ status: "error", error: `書卷對照表找不到：${book || "(空)"}` }, 400);
  }
  const ch = pick(params, "ch");
  const v1 = pick(params, "v1");
  const v2 = pick(params, "v2") || v1;
  if (!ch || !v1) return json({ status: "error", error: "參數錯誤：需要 ch 與 v1" }, 400);
  if (v2 < v1) return json({ status: "error", error: "參數錯誤：v2 小於 v1" }, 400);

  const end = Math.min(v2, v1 + MAX_VERSES - 1);
  const secParam = v1 === end ? `${v1}` : `${v1}-${end}`;
  const url = `${FHL}?chineses=${encodeURIComponent(code)}&chap=${ch}&sec=${secParam}&version=unv`;

  let data;
  try {
    const r = await fetch(url, { headers: { "user-agent": UA } });
    if (!r.ok) {
      return json({ status: "error", error: `FHL 回應異常（HTTP ${r.status}）` }, 502);
    }
    data = await r.json();
  } catch (e) {
    return json({ status: "error", error: "FHL 連線失敗，請稍後再試" }, 502);
  }

  const recs = (data && data.record) || [];
  const out = recs
    .map((rec) => ({ chap: Number(rec.chap), sec: Number(rec.sec), text: rec.bible_text }))
    .filter((v) => v.sec >= v1 && v.sec <= end)
    .sort((a, b) => a.sec - b.sec);

  if (!out.length) {
    return json({ status: "error", error: `FHL 查無經文（${book} ${ch}:${v1}）` }, 502);
  }
  const hitCap = end < v2 && out[out.length - 1].sec >= end;
  return json({ status: "success", book, ch, verses: out, truncated: hitCap }, 200);
}
