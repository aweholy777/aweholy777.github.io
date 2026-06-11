#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""smoke_test.py — 數位主播煙霧測試：10 秒短音訊跑通 InfiniteTalk 全鏈"""
import asyncio
import sys
import time
from pathlib import Path

import edge_tts

sys.path.insert(0, str(Path(__file__).parent))
from comfy_talking_head import generate

HERE = Path(__file__).parent
SERVER = sys.argv[1] if len(sys.argv) > 1 else None   # 可帶 lan / local
AUDIO = HERE / "assets" / "smoke.mp3"
IMAGE = HERE / "assets" / "presenter.png"
SUFFIX = ("_" + SERVER) if SERVER else ""
OUT = HERE.parent / "video-output" / "smoke" / f"head_smoke{SUFFIX}.mp4"

TEXT = "今天的經文進度是：創世記一章一到十節。起初，神創造天地。"


async def tts():
    c = edge_tts.Communicate(TEXT, "zh-TW-HsiaoChenNeural", rate="+10%")
    await c.save(str(AUDIO))


if __name__ == "__main__":
    if not IMAGE.exists():
        print(f"找不到主播圖：{IMAGE}\n請先把人物圖存成這個檔名。")
        sys.exit(1)
    AUDIO.parent.mkdir(parents=True, exist_ok=True)
    print("[1/2] 產生 10 秒測試音訊...")
    asyncio.run(tts())
    print("[2/2] 呼叫 ComfyUI InfiniteTalk（短片約 5~20 分鐘）...")
    t0 = time.time()
    out = generate(IMAGE, AUDIO, None, OUT, timeout_min=60, server=SERVER)
    print(f"完成：{out}（{(time.time()-t0)/60:.1f} 分鐘）")
