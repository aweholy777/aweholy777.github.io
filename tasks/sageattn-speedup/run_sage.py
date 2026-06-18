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
LOADER = "WanVideoModelLoader"             # 輸出 WANVIDEOMODEL；sage 透過它的 attention_mode 啟用
ATTN_FIELD = "attention_mode"
DEFAULT_BACKEND = "sageattn"               # WanVideoWrapper 的 sage 模式（非 KJNodes 通用 MODEL patch）


def prep_input():
    if MP3.exists() and SRT.exists():
        print("test input 已存在，沿用（與 teacache 那輪同一段，確保跨測試可比）")
        return
    info = extract_text.extract(ART)
    narr = info["narration"][:800]          # 前 ~800 字 ≈ 3 分鐘
    asyncio.run(mv.tts_with_subs(narr, MP3, SRT, mv.DEFAULT_VOICE, mv.DEFAULT_RATE))
    print("prepared test input, audio sec =", round(mv._audio_seconds(MP3), 1))


def _attn_options(object_info):
    spec = object_info[LOADER]["input"]
    for sec in ("required", "optional"):
        conf = (spec.get(sec) or {}).get(ATTN_FIELD)
        if conf:
            return conf[0]
    raise RuntimeError(f"{LOADER} 找不到 {ATTN_FIELD} 輸入")


def add_sage(w, backend, object_info):
    """設 WanVideoModelLoader 的 attention_mode = backend（sage 模式）。回傳 loader 的 UI node id。"""
    opts = _attn_options(object_info)
    if backend not in opts:
        raise RuntimeError(f"attention_mode {backend} 不在可選 {opts}")
    loader = next((n for n in w["nodes"] if n.get("type") == LOADER), None)
    if loader is None:
        raise RuntimeError(f"workflow 找不到 {LOADER} 節點")
    wv = loader.get("widgets_values")
    if not isinstance(wv, list):
        raise RuntimeError(f"{LOADER} 無 widgets_values（無法設 {ATTN_FIELD}）")
    # 在 widgets_values 找目前是 attention_mode 選項值的那格（預設 sdpa）改成 backend
    idx = next((i for i, val in enumerate(wv) if val in opts), None)
    if idx is None:
        raise RuntimeError(f"{LOADER}.widgets_values 找不到 attention_mode 欄（現值 {wv}）")
    old = wv[idx]; wv[idx] = backend
    print(f"  {LOADER}(node {loader['id']}).{ATTN_FIELD}: {old} → {backend}")
    return loader["id"]


def preflight(w, object_info, loader_nid, backend):
    api = cth.ui_to_api(w, object_info)
    le = next((e for e in api.values() if e["class_type"] == LOADER), None)
    if le is None:
        raise RuntimeError("pre-flight 失敗：ui_to_api 後找不到 loader")
    got = le["inputs"].get(ATTN_FIELD)
    if got != backend:
        raise RuntimeError(f"pre-flight 失敗：{LOADER}.{ATTN_FIELD}={got}（期望 {backend}）")
    print(f"  pre-flight OK：{LOADER}.{ATTN_FIELD} = {backend}")


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
        preflight(w, object_info, nid, backend)
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
