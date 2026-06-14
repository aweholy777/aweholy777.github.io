#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_text.py — 把 QT markdown 解析成旁白文字（全文朗讀用）

用法：python extract_text.py <文章.md>          # 印出旁白文字（除錯用）
模組：from extract_text import extract           # 回傳 dict
"""
import re
import sys
from pathlib import Path

# 段落標題的口語化對照；值為 None 表示整個標題跳過不念
SECTION_MAP = {
    "經文誦讀": None,            # 不念經文誦讀（經文引用區塊也整段跳過）
    "今天默想經文": "今天默想經文。",
    "分享默想經文": "分享默想經文。",
    "今天的回應": "今天的回應。",
}


def _spoken_title(title: str) -> str:
    """'2016 – 12 – 24 QT 約翰福音 1：1～14' →
    '2016年12月24日，每日QT。今天的經文進度是：約翰福音1章1到14節。'"""
    m = re.match(r"^\s*(\d{4})\s*[–\-]\s*(\d{1,2})\s*[–\-]\s*(\d{1,2})\s*QT\s*(.+)$", title)
    if not m:
        return title
    y, mo, d, rest = m.groups()
    rest = rest.strip()
    # 1：1～14 → 1章1到14節；1：18~25 → 1章18到25節
    rest = re.sub(r"(\d+)\s*：\s*(\d+)\s*[～~]\s*(\d+)", r"\1章\2到\3節", rest)
    # 剩餘的 章：節 → 章x節
    rest = re.sub(r"(\d+)\s*：\s*(\d+)", r"\1章\2節", rest)
    return f"{y}年{int(mo)}月{int(d)}日，每日QT。今天的經文進度是：{rest}。"


# 時間詞：其後的「時：分」是鐘點時間，不可轉成「章節」（如「清晨5：30」）。
# 範圍／帶「節」字的引用不受影響，只防護裸 X：Y 那條規則。
_TIME_CTX = re.compile(r"(清晨|早晨|早上|上午|中午|下午|傍晚|晚上|凌晨|半夜)\s*\d{0,2}$")


def _spokenize_refs(s: str) -> str:
    """內文章節引用轉口語：'10：14~22' → '10章14到22節'，'林前 10：17' → '林前 10章17節'"""
    s = re.sub(r"(\d+)\s*：\s*(\d+)\s*[～~]\s*(\d+)\s*節?", r"\1章\2到\3節", s)
    s = re.sub(r"(\d+)\s*：\s*(\d+)\s*節", r"\1章\2節", s)

    def _bare(m):
        if _TIME_CTX.search(s[:m.start()]):   # 前文是時間詞 → 鐘點時間，保留原樣
            return m.group(0)
        return f"{m.group(1)}章{m.group(2)}節"
    s = re.sub(r"(\d+)\s*：\s*(\d+)(?![\d節])", _bare, s)
    return s


def extract(md_path) -> dict:
    """回傳 {title, spoken_title, date, narration, warnings:[...]}"""
    raw = Path(md_path).read_text(encoding="utf-8")
    warnings = []

    # --- front matter ---
    title, date = "", ""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.S)
    body = raw
    if m:
        fm, body = m.group(1), raw[m.end():]
        tm = re.search(r'^title:\s*"?(.*?)"?\s*$', fm, re.M)
        dm = re.search(r"^date:\s*(\S+)", fm, re.M)
        if tm:
            title = tm.group(1)
        if dm:
            date = dm.group(1)[:10]
    else:
        warnings.append("缺少 front matter")

    lines_out = []
    for line in body.splitlines():
        s = line.rstrip()
        # 圖片行
        if re.match(r"^\s*!\[.*\]\(.*\)\s*$", s):
            continue
        # 引用區（開頭的聖經經文）：整段跳過不朗讀
        if s.lstrip().startswith(">"):
            continue
        # 粗體標題 '**1.  經文誦讀**' → 口語段落名（None 表示跳過）
        hm = re.match(r"^\s*\*\*\s*\d*[\.、]?\s*(.+?)\s*\*\*\s*$", s)
        if hm:
            name = hm.group(1).strip()
            mapped = SECTION_MAP.get(name, name + "。")
            if mapped is None:
                continue
            s = mapped
        # 行內 markdown 清理
        s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)   # 連結→文字
        s = s.replace("**", "").replace("\\~", "～")
        s = re.sub(r"^#+\s*", "", s)                        # 標題井號
        s = _spokenize_refs(s)
        s = s.strip()
        if s:
            lines_out.append(s)

    narration_body = "\n".join(lines_out)
    ok = len(narration_body) >= 100      # 結構化旗標：內文足夠才算解析成功
    if not ok:
        warnings.append(f"內文過短（{len(narration_body)} 字），可能解析失敗")

    spoken_title = _spoken_title(title) if title else ""
    narration = (spoken_title + "\n" + narration_body).strip()

    return {
        "ok": ok,
        "title": title,
        "spoken_title": spoken_title,
        "date": date,
        "narration": narration,
        "warnings": warnings,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    info = extract(sys.argv[1])
    print(f"# title: {info['title']}")
    print(f"# warnings: {info['warnings']}")
    print(f"# 字數: {len(info['narration'])}")
    print("-" * 40)
    print(info["narration"])
