#!/usr/bin/env python
# SageAttention 2.x 加速 A/B 單輪測試（沿用 teacache 那輪的 3 分鐘測試片與計時框架）。
# 用法：
#   python run_sage.py base                                  # 對照（不接 sage 節點＝sdpa）
#   python run_sage.py sage                                  # 接 KJNodes Patch Sage（預設後端 cuda）
#   python run_sage.py sage:sageattn_qk_int8_pv_fp16_cuda    # 指定後端
# 重點：
#   - 導向「隔離 ComfyUI」（預設 http://127.0.0.1:8189，venv python 內含 sage 2.2）；正式 8188 不碰。
#   - sage 用 KJNodes「PathchSageAttentionKJ」節點（夾在 sampler 的 model 輸入之前），不用 --use-sage-attention 旗標。
#   - 生成前 pre-flight：確認 patch 節點存活於 ui_to_api 結果、且 sampler.model → patch → loader。
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
RES = HERE / "_results_sage.csv"
PRES = VP / "assets" / "presenter.png"
WF = VP / "workflows" / "wanvideo_2_1_14B_I2V_InfiniteTalk_example_03.json"
ART = VP.parent / "content" / "daily-qt" / "ntqt" / "2026-01-25.md"

SERVER = "http://127.0.0.1:8189"          # 隔離 ComfyUI（sage 2.2 在這）
SAMPLER = "WanVideoSampler"
MODEL_INPUT = "model"                       # sampler 上接 MODEL 的輸入名
SAGE_NODE = "PathchSageAttentionKJ"
DEFAULT_BACKEND = "sageattn_qk_int8_pv_fp16_cuda"


def prep_input():
    if MP3.exists() and SRT.exists():
        print("test input 已存在，沿用（與 teacache 那輪同一段，確保跨測試可比）")
        return
    info = extract_text.extract(ART)
    narr = info["narration"][:800]          # 前 ~800 字 ≈ 3 分鐘
    asyncio.run(mv.tts_with_subs(narr, MP3, SRT, mv.DEFAULT_VOICE, mv.DEFAULT_RATE))
    print("prepared test input, audio sec =", round(mv._audio_seconds(MP3), 1))


def add_sage(w, backend, object_info):
    """把 PathchSageAttentionKJ 夾在 sampler 的 model 輸入前：loader → sage → sampler。"""
    nodes = w["nodes"]; links = w["links"]
    if SAGE_NODE not in object_info:
        raise RuntimeError(f"object_info 找不到 {SAGE_NODE}（KJNodes 未裝？）")
    backends = object_info[SAGE_NODE]["input"]["required"]["sage_attention"][0]
    if backend not in backends:
        raise RuntimeError(f"後端 {backend} 不在可選清單 {backends}")

    sampler = next(n for n in nodes if n.get("type") == SAMPLER)
    min_ = next(i for i in sampler["inputs"] if i["name"] == MODEL_INPUT)
    old_lid = min_["link"]                  # sampler.model 目前的 link（來自 loader/上游）
    old_link = next(l for l in links if l[0] == old_lid)
    src_node, src_slot = old_link[1], old_link[2]

    new_nid = max(n["id"] for n in nodes) + 1
    new_lid = max((l[0] for l in links), default=0) + 1

    sage = {
        "id": new_nid, "type": SAGE_NODE, "pos": [100, 100], "size": [320, 100],
        "flags": {}, "order": 0, "mode": 0,
        "inputs": [{"name": "model", "type": "MODEL", "link": old_lid}],
        "outputs": [{"name": "MODEL", "type": "MODEL", "links": [new_lid]}],
        "widgets_values": [backend],
    }
    nodes.append(sage)
    # 1) 原本 loader→sampler 的 link 改為 loader→sage
    old_link[3], old_link[4] = new_nid, 0
    # 2) 新增 sage→sampler 的 link
    dst_slot = sampler["inputs"].index(min_)
    links.append([new_lid, new_nid, 0, sampler["id"], dst_slot, "MODEL"])
    min_["link"] = new_lid
    print(f"  插入 {SAGE_NODE} (node {new_nid}) backend={backend}: "
          f"node{src_node}.{src_slot} → sage → {SAMPLER}.model")
    return new_nid


def preflight(w, object_info, sage_nid):
    api = cth.ui_to_api(w, object_info)
    if str(sage_nid) not in api:
        raise RuntimeError(f"pre-flight 失敗：sage 節點 {sage_nid} 被修剪掉（未接上）")
    samp = next(e for e in api.values() if e["class_type"] == SAMPLER)
    ref = samp["inputs"].get(MODEL_INPUT)
    if not (isinstance(ref, list) and ref[0] == str(sage_nid)):
        raise RuntimeError(f"pre-flight 失敗：{SAMPLER}.model 未指向 sage（得到 {ref}）")
    sref = api[str(sage_nid)]["inputs"].get("model")
    if not isinstance(sref, list):
        raise RuntimeError(f"pre-flight 失敗：sage.model 未接上游（得到 {sref}）")
    print(f"  pre-flight OK：{SAMPLER}.model → sage{sage_nid} → node{sref[0]}")


def parse_cfg(arg):
    if arg == "base":
        return "base", None
    if arg == "sage" or arg.startswith("sage:"):
        be = arg.split(":", 1)[1] if ":" in arg else DEFAULT_BACKEND
        return f"sage_{be}", be
    raise SystemExit(f"未知 config: {arg}（用 base | sage | sage:<backend>）")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "base"
    cfg, backend = parse_cfg(arg)
    prep_input()
    base = cth.find_server(SERVER)
    print("server:", base)

    if backend is None:
        wf = WF
    else:
        object_info = cth._get(base, "/object_info", timeout=120)
        w = json.loads(WF.read_text(encoding="utf-8"))
        nid = add_sage(w, backend, object_info)
        preflight(w, object_info, nid)
        wf = WFDIR / f"{cfg}.json"
        wf.write_text(json.dumps(w, ensure_ascii=False, indent=2), encoding="utf-8")

    vid_sec = mv._audio_seconds(MP3)
    out = OUT / f"{cfg}.mp4"
    print(f"=== RUN {cfg} === workflow={Path(wf).name} video_sec={vid_sec:.1f} server={base}")
    t0 = time.time()
    cth.generate(PRES, MP3, wf, out, server=SERVER)
    el = time.time() - t0
    ratio = el / vid_sec if vid_sec else 0
    if not RES.exists():
        RES.write_text("config,backend,video_sec,elapsed_sec,elapsed_min,ratio\n", encoding="utf-8")
    with open(RES, "a", encoding="utf-8") as f:
        f.write(f"{cfg},{backend},{vid_sec:.1f},{el:.1f},{el/60:.1f},{ratio:.2f}\n")
    print(f"DONE {cfg}: {el/60:.1f} 分, ratio={ratio:.2f}, out={out}")


if __name__ == "__main__":
    main()
