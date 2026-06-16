#!/usr/bin/env python
# 生成加速 A/B 單輪測試：固定 ~3 分鐘測試片，跑指定 config，計時寫入 _results.csv
# 用法: python run_one.py {base|fps20|fps16|fp8fast}
# 變更以「找值」方式改 workflow（比固定索引穩）；base 不改。
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


def prep_input():
    if MP3.exists() and SRT.exists():
        return
    info = extract_text.extract(ART)
    narr = info["narration"][:800]          # 取前 ~800 字 ≈ 3 分鐘，所有 config 共用同一段
    asyncio.run(mv.tts_with_subs(narr, MP3, SRT, mv.DEFAULT_VOICE, mv.DEFAULT_RATE))
    print("prepared test input, audio sec =", round(mv._audio_seconds(MP3), 1))


def _replace_in_node(nodes, ntype, oldval, newval):
    hit = 0
    for n in nodes:
        if n.get("type") == ntype:
            wv = n.get("widgets_values")
            if isinstance(wv, list):
                for i, v in enumerate(wv):
                    if v == oldval:
                        wv[i] = newval; hit += 1
    return hit


def mutate(cfg):
    if cfg == "base":
        return WF
    w = json.loads(WF.read_text(encoding="utf-8"))
    nodes = w["nodes"] if isinstance(w, dict) and "nodes" in w else w
    notes = []
    if cfg in ("fps20", "fps16"):
        fps = 20 if cfg == "fps20" else 16
        h1 = _replace_in_node(nodes, "MultiTalkWav2VecEmbeds", 25, fps)
        h2 = _replace_in_node(nodes, "VHS_VideoCombine", 25, fps)
        h3 = _replace_in_node(nodes, "VHS_VideoCombine", 25.0, fps)
        notes.append(f"fps 25->{fps} (wav2vec hit={h1}, vhs hit={h2+h3})")
    elif cfg == "fp8fast":
        h = _replace_in_node(nodes, "WanVideoModelLoader", "fp8_e4m3fn", "fp8_e4m3fn_fast")
        notes.append(f"quant fp8_e4m3fn->fp8_e4m3fn_fast (hit={h})")
    p = WFDIR / f"{cfg}.json"
    p.write_text(json.dumps(w, ensure_ascii=False, indent=2), encoding="utf-8")
    print("mutated:", "; ".join(notes))
    return p


def main():
    cfg = sys.argv[1] if len(sys.argv) > 1 else "base"
    prep_input()
    wf = mutate(cfg)
    vid_sec = mv._audio_seconds(MP3)
    out = OUT / f"{cfg}.mp4"
    print(f"=== RUN {cfg} === workflow={wf.name} video_sec={vid_sec:.1f}")
    t0 = time.time()
    cth.generate(PRES, MP3, wf, out, server="local")
    el = time.time() - t0
    ratio = el / vid_sec if vid_sec else 0
    line = f"{cfg},{vid_sec:.1f},{el:.1f},{el/60:.1f},{ratio:.2f}\n"
    if not RES.exists():
        RES.write_text("config,video_sec,elapsed_sec,elapsed_min,ratio\n", encoding="utf-8")
    with open(RES, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"DONE {cfg}: {el/60:.1f} 分, ratio={ratio:.2f}, out={out}")


if __name__ == "__main__":
    main()
