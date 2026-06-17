#!/usr/bin/env python
# TeaCache 加速 A/B 單輪測試：固定 ~3 分鐘測試片，跑指定 config，計時寫入 _results.csv
# 用法:
#   python run_one.py base            # 對照基準（不改 workflow）
#   python run_one.py teacache:0.15   # 加 TeaCache，rel_l1 門檻 0.15
#   python run_one.py teacache:0.25   # 積極門檻
#
# 設計重點（跨 WanVideoWrapper 版本穩）：
#   不寫死 TeaCache 節點名。執行時向本機 ComfyUI /object_info 自動探測
#   「輸出型別 == WanVideoSampler.cache_args 輸入型別、且名稱含 Cache/Tea」的生產節點，
#   用其預設值建 widgets、只覆寫 rel_l1 門檻欄，接到 sampler 的 cache_args。
#   昂貴生成前先本地跑 ui_to_api 做 pre-flight，確認接線存活才生成。
import sys, time, json, asyncio
from pathlib import Path

HERE = Path(__file__).resolve().parent
VP = HERE.parent.parent / "video-pipeline"
sys.path.insert(0, str(VP))
import make_video as mv
import comfy_talking_head as cth
import extract_text

INP = HERE / "_input"; INP.mkdir(exist_ok=True)
OUT = HERE / "_out"; OUT.mkdir(exist_ok=True)
WFDIR = HERE / "_wf"; WFDIR.mkdir(exist_ok=True)
MP3, SRT = INP / "test.mp3", INP / "test.srt"
RES = HERE / "_results.csv"
PRES = VP / "assets" / "presenter.png"
WF = VP / "workflows" / "wanvideo_2_1_14B_I2V_InfiniteTalk_example_03.json"
ART = VP.parent / "content" / "daily-qt" / "ntqt" / "2026-01-25.md"

SAMPLER = "WanVideoSampler"
CACHE_INPUT = "cache_args"        # sampler 上接 TeaCache 的輸入名
THRESH_WIDGETS = ("rel_l1_thresh", "rel_l1", "threshold", "thresh")


def prep_input():
    if MP3.exists() and SRT.exists():
        return
    info = extract_text.extract(ART)
    narr = info["narration"][:800]          # 前 ~800 字 ≈ 3 分鐘，所有 config 共用同一段
    asyncio.run(mv.tts_with_subs(narr, MP3, SRT, mv.DEFAULT_VOICE, mv.DEFAULT_RATE))
    print("prepared test input, audio sec =", round(mv._audio_seconds(MP3), 1))


def _is_widget(t):
    return isinstance(t, list) or (isinstance(t, str) and t in
                                   ("INT", "FLOAT", "STRING", "BOOLEAN", "COMBO"))


def _cache_input_type(object_info):
    spec = object_info[SAMPLER]["input"]
    for section in ("required", "optional"):
        for name, conf in (spec.get(section) or {}).items():
            if name == CACHE_INPUT:
                return conf[0] if isinstance(conf, (list, tuple)) else conf
    raise RuntimeError(f"{SAMPLER} 找不到 {CACHE_INPUT} 輸入")


def _find_cache_producer(object_info, cache_type):
    """找輸出型別 == cache_type 且名稱含 Cache/Tea 的節點類別。優先含 Tea。"""
    cands = []
    for cls, info in object_info.items():
        outs = info.get("output") or []
        if cache_type in outs and ("cache" in cls.lower() or "tea" in cls.lower()):
            cands.append(cls)
    if not cands:
        raise RuntimeError(f"找不到輸出 {cache_type} 的 TeaCache 節點（已裝 WanVideoWrapper？）")
    cands.sort(key=lambda c: (0 if "tea" in c.lower() else 1, len(c)))
    return cands[0]


def _build_widgets(object_info, cls, thresh):
    """依 object_info 順序產生 widgets_values（只含 widget 型輸入），覆寫門檻欄。"""
    spec = object_info[cls]["input"]
    wv = []
    for section in ("required", "optional"):
        for name, conf in (spec.get(section) or {}).items():
            t = conf[0] if isinstance(conf, (list, tuple)) else conf
            if not _is_widget(t):
                continue
            default = None
            if isinstance(conf, (list, tuple)) and len(conf) > 1 and isinstance(conf[1], dict):
                default = conf[1].get("default")
            if isinstance(t, list) and default is None:        # COMBO 取第一項
                default = t[0] if t else None
            wv.append(thresh if name in THRESH_WIDGETS else default)
    # 覆寫第一個門檻欄（保險：若名稱不在 THRESH_WIDGETS，挑第一個 FLOAT widget）
    names = [n for sec in ("required", "optional") for n in (spec.get(sec) or {})
             if _is_widget((spec[sec][n][0] if isinstance(spec[sec][n], (list, tuple)) else spec[sec][n]))]
    if not any(n in THRESH_WIDGETS for n in names):
        for i, n in enumerate(names):
            conf = spec.get("required", {}).get(n) or spec.get("optional", {}).get(n)
            t = conf[0] if isinstance(conf, (list, tuple)) else conf
            if t == "FLOAT":
                wv[i] = thresh
                print(f"  （門檻欄名非預期，改寫第一個 FLOAT widget '{n}'）")
                break
    return wv


def add_teacache(w, thresh, object_info):
    nodes = w["nodes"]; links = w["links"]
    cache_type = _cache_input_type(object_info)
    cls = _find_cache_producer(object_info, cache_type)
    sampler = next(n for n in nodes if n.get("type") == SAMPLER)

    new_nid = max(n["id"] for n in nodes) + 1
    new_lid = max((l[0] for l in links), default=0) + 1
    wv = _build_widgets(object_info, cls, thresh)

    node = {
        "id": new_nid, "type": cls, "pos": [100, 100], "size": [300, 200],
        "flags": {}, "order": 0, "mode": 0,
        "inputs": [],
        "outputs": [{"name": cache_type.lower(), "type": cache_type, "links": [new_lid]}],
        "widgets_values": wv,
    }
    nodes.append(node)
    # link: [id, src_node, src_slot, dst_node, dst_slot, type]
    cin = next(i for i in sampler["inputs"] if i["name"] == CACHE_INPUT)
    dst_slot = sampler["inputs"].index(cin)
    links.append([new_lid, new_nid, 0, sampler["id"], dst_slot, cache_type])
    cin["link"] = new_lid
    print(f"  插入 {cls} (node {new_nid}) thresh={thresh} → {SAMPLER}.{CACHE_INPUT}; widgets={wv}")
    return cls, new_nid


def preflight(w, object_info, teacache_nid):
    """生成前驗證：TeaCache 節點存活於 ui_to_api 結果、且 sampler.cache_args 指向它。"""
    api = cth.ui_to_api(w, object_info)
    if str(teacache_nid) not in api:
        raise RuntimeError(f"pre-flight 失敗：TeaCache 節點 {teacache_nid} 被修剪掉（未接上）")
    samp = next(e for e in api.values() if e["class_type"] == SAMPLER)
    ref = samp["inputs"].get(CACHE_INPUT)
    if not (isinstance(ref, list) and ref[0] == str(teacache_nid)):
        raise RuntimeError(f"pre-flight 失敗：{SAMPLER}.{CACHE_INPUT} 未指向 TeaCache（得到 {ref}）")
    print(f"  pre-flight OK：{SAMPLER}.{CACHE_INPUT} → node {teacache_nid}")


def parse_cfg(arg):
    if arg == "base":
        return "base", 0.0
    if arg.startswith("teacache"):
        thr = float(arg.split(":", 1)[1]) if ":" in arg else 0.15
        return f"teacache_{str(thr).replace('.', '')}", thr
    raise SystemExit(f"未知 config: {arg}（用 base | teacache:0.15）")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "base"
    cfg, thresh = parse_cfg(arg)
    prep_input()
    base = cth.find_server("local")
    print("server:", base)

    if cfg == "base":
        wf = WF
    else:
        object_info = cth._get(base, "/object_info", timeout=120)
        w = json.loads(WF.read_text(encoding="utf-8"))
        _, nid = add_teacache(w, thresh, object_info)
        preflight(w, object_info, nid)          # 失敗即丟例外、不生成
        wf = WFDIR / f"{cfg}.json"
        wf.write_text(json.dumps(w, ensure_ascii=False, indent=2), encoding="utf-8")

    vid_sec = mv._audio_seconds(MP3)
    out = OUT / f"{cfg}.mp4"
    print(f"=== RUN {cfg} (thresh={thresh}) === workflow={Path(wf).name} video_sec={vid_sec:.1f}")
    t0 = time.time()
    cth.generate(PRES, MP3, wf, out, server="local")
    el = time.time() - t0
    ratio = el / vid_sec if vid_sec else 0
    line = f"{cfg},{thresh},{vid_sec:.1f},{el:.1f},{el/60:.1f},{ratio:.2f}\n"
    if not RES.exists():
        RES.write_text("config,thresh,video_sec,elapsed_sec,elapsed_min,ratio\n", encoding="utf-8")
    with open(RES, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"DONE {cfg}: {el/60:.1f} 分, ratio={ratio:.2f}, out={out}")


if __name__ == "__main__":
    main()
