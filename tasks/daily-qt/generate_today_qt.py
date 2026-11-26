#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日早上 6 點產生「當日QT」頁面（content/today-qt.md）。

流程（與「生成當日QT」產生器一致）：
  1. 取當日進度：duranno.tw 官網 → CGN《活潑的生命》YouTube → 自家 https://cmtc.tw/api/daily-reference
  2. 依進度抓和合本經文：https://bible.fhl.net/json/qb.php （FHL，version=unv）
  3. 在既有 QT 典藏（content/daily-qt/{otqt,ntqt}）找出涵蓋同一段經文的舊文章，
     沿用它的「今天默想經文／分享默想經文／今天的回應」
  4. 寫出 content/today-qt.md（Hugo 產生 /today-qt/ 頁面）

只用標準庫，GitHub Actions 與本機都能跑。

用法：
  python tasks/daily-qt/generate_today_qt.py                 # 產生今天
  python tasks/daily-qt/generate_today_qt.py --date 2026-10-22
  python tasks/daily-qt/generate_today_qt.py --reference "歷代志上29：10∼19"
  python tasks/daily-qt/generate_today_qt.py --dry-run       # 只印出，不寫檔
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONTENT = REPO / "content"
ARCHIVE_DIRS = [CONTENT / "daily-qt" / "otqt", CONTENT / "daily-qt" / "ntqt"]
OUT_FILE = CONTENT / "today-qt.md"
LAST_RUN = Path(__file__).resolve().parent / "last-run.json"

# 第三層備援：自家 Cloudflare Pages Function（functions/api/daily-reference.js，內部同樣 duranno → CGN）
# 2026-11-27 起取代原本別人的 Vercel 代理（那支只抓 duranno，duranno 一維護就 500）
DAILY_REFERENCE_URL = "https://cmtc.tw/api/daily-reference"
# 來源站（活潑的生命官網）：直接抓最可靠
DURANNO_URL = "https://www.duranno.tw/livinglife/index.php/daily"

# 備援：CGN 中文《活潑的生命》YouTube 頻道（每日影片標題含 YYYYMMDD 與經文範圍）
CGN_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id=UCqUnxXxHSFb6At-njlSX9AQ"
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
FHL_URL = "https://bible.fhl.net/json/qb.php"
UA = "cmtc-daily-qt/1.0 (+https://cmtc.tw)"

# 書卷全名 → FHL chineses 代碼（與產生器 BOOKS 表一致）
BOOKS = [
    ("創", "創世記"), ("出", "出埃及記"), ("利", "利未記"), ("民", "民數記"), ("申", "申命記"),
    ("書", "約書亞記"), ("士", "士師記"), ("得", "路得記"), ("撒上", "撒母耳記上"), ("撒下", "撒母耳記下"),
    ("王上", "列王紀上"), ("王下", "列王紀下"), ("代上", "歷代志上"), ("代下", "歷代志下"), ("拉", "以斯拉記"),
    ("尼", "尼希米記"), ("斯", "以斯帖記"), ("伯", "約伯記"), ("詩", "詩篇"), ("箴", "箴言"),
    ("傳", "傳道書"), ("歌", "雅歌"), ("賽", "以賽亞書"), ("耶", "耶利米書"), ("哀", "耶利米哀歌"),
    ("結", "以西結書"), ("但", "但以理書"), ("何", "何西阿書"), ("珥", "約珥書"), ("摩", "阿摩司書"),
    ("俄", "俄巴底亞書"), ("拿", "約拿書"), ("彌", "彌迦書"), ("鴻", "那鴻書"), ("哈", "哈巴谷書"),
    ("番", "西番雅書"), ("該", "哈該書"), ("亞", "撒迦利亞書"), ("瑪", "瑪拉基書"), ("太", "馬太福音"),
    ("可", "馬可福音"), ("路", "路加福音"), ("約", "約翰福音"), ("徒", "使徒行傳"), ("羅", "羅馬書"),
    ("林前", "哥林多前書"), ("林後", "哥林多後書"), ("加", "加拉太書"), ("弗", "以弗所書"), ("腓", "腓立比書"),
    ("西", "歌羅西書"), ("帖前", "帖撒羅尼迦前書"), ("帖後", "帖撒羅尼迦後書"), ("提前", "提摩太前書"),
    ("提後", "提摩太後書"), ("多", "提多書"), ("門", "腓利門書"), ("來", "希伯來書"), ("雅", "雅各書"),
    ("彼前", "彼得前書"), ("彼後", "彼得後書"), ("約一", "約翰一書"), ("約二", "約翰二書"), ("約三", "約翰三書"),
    ("猶", "猶大書"), ("啟", "啟示錄"),
]
NAME2CODE = {name: code for code, name in BOOKS}

REF_RE = re.compile(
    r"^(?P<book>[\u4e00-\u9fff]+?)\s*(?P<ch1>\d+)\s*[：:]\s*(?P<v1>\d+)"
    r"\s*[∼~\-－—]\s*(?:(?P<ch2>\d+)\s*[：:]\s*)?(?P<v2>\d+)\s*$"
)
TITLE_RE = re.compile(
    r"QT\s*(?P<book>[\u4e00-\u9fff]+?)\s*(?P<ch1>\d+)\s*[：:]\s*(?P<v1>\d+)"
    r"\s*[∼~\-－—]\s*(?:(?P<ch2>\d+)\s*[：:]\s*)?(?P<v2>\d+)"
)
SECTION_RE = re.compile(r"\*\*\s*(?P<num>[1-4])\s*[\.、]\s*(?P<title>[^*]+?)\s*\*\*")


# ---------------------------------------------------------------- HTTP helpers
def http_get(url: str, tries: int = 4, timeout: int = 30) -> bytes:
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001 - 網路錯誤一律重試
            last = e
            time.sleep(2 + 3 * i)
    raise RuntimeError(f"取得失敗（重試 {tries} 次）：{url}\n最後錯誤：{last}")


TAIPEI_TZ = dt.timezone(dt.timedelta(hours=8))


def taipei_today() -> str:
    return dt.datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d")


def get_cgn_reference(date: str | None) -> str | None:
    """備援來源：CGN 中文《活潑的生命》YouTube 頻道。
    影片標題格式：[活潑的生命] 20261122 主題(哥林多後書 1:15~24)
    duranno.tw 維護時（頁面只剩「每日經文系統維護中」）可用。"""
    day = date or taipei_today()
    ymd = day.replace("-", "")
    try:
        cp = subprocess.run(
            ["curl", "-sS", "-m", "40", "-A", BROWSER_UA, CGN_RSS], capture_output=True
        )
        if cp.returncode != 0:
            return None
        raw = cp.stdout.decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return None
    for m in re.finditer(r"<title>([^<]*)</title>", raw):
        t = m.group(1).replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"')
        if "活潑的生命" not in t or ymd not in t:
            continue
        mm = re.search(
            r"[（(]\s*([^（）()]+?)\s*(\d+)\s*[：:]\s*(\d+)\s*[~∼\-–]\s*(?:(\d+)\s*[：:])?\s*(\d+)\s*[）)]",
            t,
        )
        if not mm:
            continue
        book, ch1, v1, ch2, v2 = mm.groups()
        book = book.strip()
        return f"{book}{ch1}：{v1}∼{ch2}：{v2}" if ch2 else f"{book}{ch1}：{v1}∼{v2}"
    return None


def get_daily_reference(date: str | None) -> dict:
    today = taipei_today()
    target_date = date or today
    # 1) 查「今天」時先直抓 duranno.tw 官網（duranno /daily 永遠只回今天，歷史日期略過）
    #    註：duranno.tw 憑證缺 SKID，Python/OpenSSL 會拒收，改用 curl 抓
    if target_date == today:
        try:
            cp = subprocess.run(["curl", "-sS", "-m", "40", "-A", UA, DURANNO_URL], capture_output=True)
            if cp.returncode != 0:
                raise RuntimeError(cp.stderr.decode("utf-8", "replace")[:200] or f"curl exit {cp.returncode}")
            html = cp.stdout.decode("utf-8", errors="replace")
            m = re.search(r'<div class="range">\s*([^<]+?)\s*</div>', html)
            if m and m.group(1).strip():
                ref = m.group(1).strip()
                print("  （來源：duranno.tw 直抓）")
                return {"status": "success", "reference": ref, "sourceUrl": DURANNO_URL, "source": "duranno-direct"}
            print("  ⚠️ duranno.tw 直抓解析失敗（可能維護中），改用 CGN 頻道")
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️ duranno.tw 直抓失敗（{e}），改用 CGN 頻道")
    # 2) 備援：CGN 中文《活潑的生命》YouTube 頻道標題（duranno 維護時最有用）
    cgn_ref = get_cgn_reference(date)
    if cgn_ref:
        print(f"  （來源：CGN 活潑的生命 YouTube）{cgn_ref}")
        return {
            "status": "success",
            "reference": cgn_ref,
            "sourceUrl": CGN_RSS,
            "source": "cgn-youtube",
        }
    print("  ⚠️ CGN 頻道也找不到今日進度，改用自家 /api/daily-reference")
    # 3) 退回自家 API（Cloudflare Pages Function，cmtc.tw）
    url = DAILY_REFERENCE_URL
    if date:
        url = f"{url}?date={date}"
    data = json.loads(http_get(url).decode("utf-8"))
    if data.get("status") != "success" or not data.get("reference"):
        raise RuntimeError(f"當日進度 API 回應異常：{data}")
    data["source"] = "cmtc-api"
    return data


# ---------------------------------------------------------------- 經文
def parse_reference(ref: str) -> dict:
    m = REF_RE.match(ref.strip())
    if not m:
        raise RuntimeError(f"無法解析經文範圍：{ref!r}")
    ch1, v1 = int(m.group("ch1")), int(m.group("v1"))
    ch2 = int(m.group("ch2")) if m.group("ch2") else ch1
    v2 = int(m.group("v2"))
    return {"book": m.group("book"), "ch1": ch1, "v1": v1, "ch2": ch2, "v2": v2}


def fetch_verses(parsed: dict) -> list[dict]:
    code = NAME2CODE.get(parsed["book"])
    if not code:
        raise RuntimeError(f"書卷對照表找不到：{parsed['book']}")
    out: list[dict] = []
    for chap in range(parsed["ch1"], parsed["ch2"] + 1):
        first = parsed["v1"] if chap == parsed["ch1"] else 1
        last = parsed["v2"] if chap == parsed["ch2"] else 200
        sec_param = str(first) if first == last else f"{first}-{last}"
        q = urllib.parse.urlencode({"chineses": code, "chap": chap, "sec": sec_param, "version": "unv"})
        data = json.loads(http_get(f"{FHL_URL}?{q}").decode("utf-8"))
        recs = data.get("record") or []
        if not recs:
            if chap == parsed["ch1"]:
                raise RuntimeError(f"FHL 查無經文：{code} {chap}:{sec_param}")
            break
        chap_verses = [
            {"chap": int(r["chap"]), "sec": int(r["sec"]), "text": r["bible_text"]}
            for r in recs
            if first <= int(r["sec"]) <= last
        ]
        chap_verses.sort(key=lambda v: v["sec"])
        out.extend(chap_verses)
        if chap < parsed["ch2"]:
            time.sleep(0.15)
    if not out:
        raise RuntimeError("FHL 未回傳任何經文")
    return out


# ---------------------------------------------------------------- 典藏比對
def load_archive_index() -> list[dict]:
    items = []
    for d in ARCHIVE_DIRS:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            try:
                with f.open(encoding="utf-8", errors="replace") as fh:
                    head = [next(fh) for _ in range(6)]
            except (StopIteration, OSError):
                continue
            title = ""
            for line in head:
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"')
                    break
            m = TITLE_RE.search(title)
            if not m:
                continue
            ch1, v1 = int(m.group("ch1")), int(m.group("v1"))
            ch2 = int(m.group("ch2")) if m.group("ch2") else ch1
            v2 = int(m.group("v2"))
            items.append({
                "path": f, "title": title, "book": m.group("book"),
                "start": (ch1, v1), "end": (ch2, v2),
                "date": f.stem,
            })
    return items


def _lin(pos: tuple[int, int]) -> int:
    return pos[0] * 1000 + pos[1]


def find_archive(parsed: dict, index: list[dict], allow_partial: bool = True) -> tuple[dict | None, str]:
    start = (parsed["ch1"], parsed["v1"])
    end = (parsed["ch2"], parsed["v2"])
    cands = [
        it for it in index
        if it["book"] == parsed["book"] and it["start"] <= start and it["end"] >= end
    ]
    if cands:
        # 優先完全相同範圍（多篇時取最新日期），其次涵蓋範圍最小、日期最新者
        exact = [c for c in cands if c["start"] == start and c["end"] == end]
        if exact:
            return max(exact, key=lambda c: c["date"]), "exact"
        best = min(
            cands,
            key=lambda c: (c["end"][0] - c["start"][0], c["end"][1] - c["start"][1], ""),
        )
        # 同等最小範圍時取最新日期
        min_span = (best["end"][0] - best["start"][0], best["end"][1] - best["start"][1])
        same_span = [
            c for c in cands
            if (c["end"][0] - c["start"][0], c["end"][1] - c["start"][1]) == min_span
        ]
        return max(same_span, key=lambda c: c["date"]), "cover"

    if not allow_partial:
        return None, "none"

    best_it, best_ov = None, 0
    s_lin, e_lin = _lin(start), _lin(end)
    for it in index:
        if it["book"] != parsed["book"]:
            continue
        ov = min(_lin(it["end"]), e_lin) - max(_lin(it["start"]), s_lin) + 1
        if ov > best_ov or (ov == best_ov and ov > 0 and best_it and it["date"] > best_it["date"]):
            best_ov, best_it = ov, it
    return (best_it, "partial") if best_it else (None, "none")


def split_article(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    body = text.split("---", 2)[-1] if text.startswith("---") else text
    marks = list(SECTION_RE.finditer(body))
    sections: dict[int, str] = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        sections[int(m.group("num"))] = body[m.end():end].strip()
    return sections


# ---------------------------------------------------------------- 產生頁面
def build_page(date_str: str, ref: str, parsed: dict, verses: list[dict],
               archive: dict | None, sections: dict[int, str], source_url: str,
               match_mode: str = "exact") -> str:
    # ref 本身已含書卷名，顯示時只留章節，避免「歷代志上 歷代志上29：10~19」
    if parsed["ch1"] == parsed["ch2"]:
        ref_short = f'{parsed["ch1"]}：{parsed["v1"]}~{parsed["v2"]}'
    else:
        ref_short = f'{parsed["ch1"]}：{parsed["v1"]}~{parsed["ch2"]}：{parsed["v2"]}'
    verse_lines = []
    for v in verses:
        verse_lines.append(f"> {v['chap']}：{v['sec']} {v['text']}  ")
    if archive:
        testament = "otqt" if "otqt" in str(archive["path"]) else "ntqt"
        link = f'<a href="/daily-qt/{testament}/{archive["date"]}/">{archive["date"]} 的 QT</a>'
        if match_mode == "partial":
            s, e = archive["start"], archive["end"]
            orig = f"{s[0]}：{s[1]}~{e[1]}" if s[0] == e[0] else f"{s[0]}：{s[1]}~{e[0]}：{e[1]}"
            src_note = (
                f"今日進度依《活潑的生命》每日讀經，分享內容參考 {link}（原範圍 {orig}，與今日進度部分重疊）。"
            )
        else:
            src_note = f"今日進度依《活潑的生命》每日讀經，分享內容沿用 {link}。"
    else:
        src_note = "今日進度依《活潑的生命》每日讀經；這段經文在過往 QT 典藏中尚無對應的分享文章，以下僅列經文。"

    def sec(num: int, default: str = "") -> str:
        return sections.get(num, "").strip() or default

    parts = [
        "---",
        f'title: "當日QT {date_str} {parsed["book"]} {ref_short}"',
        f"date: {date_str}T06:00:00+08:00",
        "draft: false",
        "type: today-qt",
        f'reference: "{parsed["book"]} {ref_short}"',
        f'archive_date: "{archive["date"] if archive else ""}"',
        f'source_url: "{source_url}"',
        "---",
        "",
        "![](/images/qt.jpg)",
        "",
        f'> {parsed["book"]} {ref_short}  ',
        *verse_lines,
        "",
        f'<p class="today-qt-note">{src_note}</p>',
        "",
        "**1. 經文誦讀**",
        "",
        sec(1, "（經文如上）"),
        "",
        "**2. 今天默想經文**",
        sec(2, "（今日經文如上）"),
        "",
        "**3. 分享默想經文**",
        sec(3, "（今日尚無對應的分享內容。）"),
        "",
        "**4. 今天的回應**",
        sec(4, "（今日尚無對應的回應內容。）"),
        "",
    ]
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD（預設：台北時間今天）")
    ap.add_argument("--reference", help="覆寫當日進度，例如 歷代志上29：10∼19")
    ap.add_argument("--dry-run", action="store_true", help="只印出結果，不寫檔")
    ap.add_argument("--archive-date", help="強制沿用指定日期的舊文章，例如 2018-03-02（上游故障時手動指定）")
    ap.add_argument("--no-partial", action="store_true", help="不允許部分重疊比對，只採用完全涵蓋舊文")
    args = ap.parse_args(argv)

    date_str = args.date or taipei_today()

    if args.reference:
        ref, source_url = args.reference, "(手動指定)"
    else:
        info = get_daily_reference(date_str)
        ref, source_url = info["reference"], info.get("sourceUrl", "")

    parsed = parse_reference(ref)
    print(f"[1/4] 當日進度：{ref}（{parsed}）")

    verses = fetch_verses(parsed)
    print(f"[2/4] 和合本經文：{len(verses)} 節（{verses[0]['chap']}:{verses[0]['sec']}–{verses[-1]['chap']}:{verses[-1]['sec']}）")

    index = load_archive_index()
    match_mode = "manual"
    if args.archive_date:
        archive = next((it for it in index if it["date"] == args.archive_date), None)
        if not archive:
            print(f"⚠️ 找不到 {args.archive_date} 的舊文章，改回自動比對")
            archive, match_mode = find_archive(parsed, index, allow_partial=not args.no_partial)
    else:
        archive, match_mode = find_archive(parsed, index, allow_partial=not args.no_partial)
    if archive:
        sections = split_article(archive["path"])
        print(f"[3/4] 對應舊文章（{match_mode}）：{archive['date']} {archive['title']}"
              f"（段落 {sorted(sections)}）")
    else:
        sections = {}
        print("[3/4] 找不到對應的舊文章，只輸出經文")

    page = build_page(date_str, ref, parsed, verses, archive, sections, source_url, match_mode=match_mode)

    if args.dry_run:
        print("[4/4] dry-run，未寫檔。內容預覽：\n" + "-" * 60)
        print(page[:1500])
        return 0

    OUT_FILE.write_text(page, encoding="utf-8")
    LAST_RUN.write_text(json.dumps({
        "date": date_str, "reference": ref,
        "archive": archive["date"] if archive else None,
        "match_mode": match_mode,
        "verses": len(verses),
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[4/4] 已寫入 {OUT_FILE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"錯誤：{exc}", file=sys.stderr)
        sys.exit(1)
