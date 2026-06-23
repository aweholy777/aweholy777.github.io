# -*- coding: utf-8 -*-
"""產生新約/舊約影片進度表（依聖經卷序＋章節序；同經文取最新日期）。
狀態：已上傳(csv或文章已嵌shortcode) / 已生成未上傳(head或head/old有mp4) / 未生成。
輸出：tasks/progress/新約進度表.md、舊約進度表.md、_summary.txt
"""
import sys
from pathlib import Path

PIPE = Path(r"C:\Users\user\qtproject\video-pipeline")
sys.path.insert(0, str(PIPE))
import nightly_head as n  # noqa: E402

REPO = Path(r"C:\Users\user\qtproject")
HEAD = REPO / "video-output" / "head"
OLD = HEAD / "old"
OUT = REPO / "tasks" / "progress"
DONE = n._done_keys()


def status(sub, slug):
    md = REPO / "content" / "daily-qt" / sub / f"{slug}.md"
    uploaded = (f"{sub}/{slug}" in DONE) or (
        md.exists() and "{{< youtube" in md.read_text(encoding="utf-8"))
    if uploaded:
        return "已上傳"
    gen = (HEAD / f"{sub}_{slug}.mp4").exists() or (OLD / f"{sub}_{slug}.mp4").exists()
    return "已生成未上傳" if gen else "未生成"


def parse(sub):
    """回傳依首次出現序的 [(book_seq, book_name, passage, best_slug)]；同經文取最新日期。"""
    idx = REPO / "content" / "daily-qt" / sub / "_index.md"
    items = []          # (order_key) -> index into rows
    rows = []           # [book_seq, book_name, passage, best_slug]
    pos = {}            # norm_key -> row index
    seen_books = set()
    book_seq = 0
    cur_book = "(未標卷名)"
    for line in idx.read_text(encoding="utf-8").splitlines():
        bm = n.BOOK.search(line)
        if bm:
            cur_book = bm.group(1)
            if cur_book not in seen_books:
                seen_books.add(cur_book)
                book_seq += 1
            continue
        em = n.ENTRY.search(line)
        if not em:
            continue
        passage, slug = em.group(2).strip(), em.group(3)
        key = n.norm_key(passage)
        if key not in pos:
            pos[key] = len(rows)
            rows.append([book_seq, cur_book, passage, slug])
        else:
            r = rows[pos[key]]
            if slug > r[3]:
                r[3] = slug  # 取最新日期
    return rows


def jump_uploads():
    """全隊列依卷序掃描，找『插隊上傳』＝已出現『未生成』之後又出現的『已上傳』。
    回傳 {sub: [(slug, seq, passage), ...]}。這些是舊日期序留下的越級發布，
    已在 YouTube 上、勿重生重傳；新規則（按卷序上傳）之後不再發生。"""
    out = {"ntqt": [], "otqt": []}
    seen_pending = False
    for sub, slug, seq in n.build_queue():
        st = status(sub, slug)
        if st == "未生成":
            seen_pending = True
        elif st == "已上傳" and seen_pending:
            md = REPO / "content" / "daily-qt" / sub / f"{slug}.md"
            passage = ""
            for line in md.read_text(encoding="utf-8").splitlines():
                if line.startswith("title:"):
                    passage = line.split(":", 1)[1].strip().strip('"')
                    break
            out[sub].append((slug, seq, passage))
    return out


def write_table(sub, title, path, notes):
    rows = parse(sub)
    lines = [f"# {title}（依聖經卷序；同經文取最新日期）", ""]
    if notes:
        lines.append("> ⚠️ **已知插隊上傳（勿重生重傳）**：下列篇目因『舊日期升序上傳』被越級發布、")
        lines.append("> 已在 YouTube 上。生成/上傳流程會自動跳過（已在 csv＋文章已嵌 shortcode）。")
        lines.append("> 自 2026-06-23 起上傳已改『嚴格按聖經卷序』，之後不再發生越級。")
        for slug, seq, passage in notes:
            lines.append(f"> - 第{seq}卷 {passage}（{slug}）← 越級已上傳")
        lines.append("")
    from collections import OrderedDict
    by_book = OrderedDict()
    for seq, book, passage, slug in rows:
        by_book.setdefault((seq, book), []).append((passage, slug))
    tot = {"已上傳": 0, "已生成未上傳": 0, "未生成": 0}
    summary = []
    for (seq, book), entries in by_book.items():
        c = {"已上傳": 0, "已生成未上傳": 0, "未生成": 0}
        lines.append(f"\n## 第{seq}卷 {book}（{len(entries)} 篇）\n")
        lines.append("| # | 經文 | 日期(最新) | 狀態 |")
        lines.append("|---|---|---|---|")
        for i, (passage, slug) in enumerate(entries, 1):
            st = status(sub, slug)
            c[st] += 1
            tot[st] += 1
            lines.append(f"| {i} | {passage} | {slug} | {st} |")
        summary.append((seq, book, len(entries), c["已上傳"], c["已生成未上傳"], c["未生成"]))
    path.write_text("\n".join(lines), encoding="utf-8")
    return summary, tot, len(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jumps = jump_uploads()
    s_nt, t_nt, n_nt = write_table("ntqt", "新約 QT 影片進度表", OUT / "新約進度表.md", jumps["ntqt"])
    s_ot, t_ot, n_ot = write_table("otqt", "舊約 QT 影片進度表", OUT / "舊約進度表.md", jumps["otqt"])

    out = []
    def block(name, summ, tot, total):
        out.append(f"===== {name}（共 {total} 篇）=====")
        out.append(f"  總計：已上傳 {tot['已上傳']} / 已生成未上傳 {tot['已生成未上傳']} / 未生成 {tot['未生成']}")
        out.append("  卷 | 書卷 | 篇數 | 已上傳 | 已生成未上傳 | 未生成")
        for seq, book, n_, up, gen, no in summ:
            out.append(f"  {seq} | {book} | {n_} | {up} | {gen} | {no}")
        out.append("")
    block("新約 ntqt", s_nt, t_nt, n_nt)
    block("舊約 otqt", s_ot, t_ot, n_ot)
    allj = [("ntqt", *x) for x in jumps["ntqt"]] + [("otqt", *x) for x in jumps["otqt"]]
    out.append("===== 已知插隊上傳（勿重生重傳；新規則之後不再發生）=====")
    if allj:
        for sub, slug, seq, passage in allj:
            out.append(f"  {sub} 第{seq}卷 {passage}（{slug}）")
    else:
        out.append("  （無）")
    (OUT / "_summary.txt").write_text("\n".join(out), encoding="utf-8")
    print("done", n_nt, n_ot)


if __name__ == "__main__":
    main()
