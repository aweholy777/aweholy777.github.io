#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""產生 LAN 主機（57GB VRAM）專用工作流：無 block swap、832×480"""
import json
from pathlib import Path

HERE = Path(__file__).parent / "workflows"
src = HERE / "wanvideo_2_1_14B_I2V_InfiniteTalk_example_03.json"
dst = HERE / "infinitetalk_lan.json"

ui = json.loads(src.read_text(encoding="utf-8"))
for n in ui["nodes"]:
    if n["type"] == "WanVideoBlockSwap":
        n["widgets_values"][0] = 0
    elif n["type"] == "INTConstant" and n.get("title") == "Width":
        n["widgets_values"][0] = 832
    elif n["type"] == "INTConstant" and n.get("title") == "Height":
        n["widgets_values"][0] = 480
dst.write_text(json.dumps(ui, ensure_ascii=False, indent=2), encoding="utf-8")

out = ["written " + str(dst)]
v = json.loads(dst.read_text(encoding="utf-8"))
for n in v["nodes"]:
    if n["type"] in ("WanVideoBlockSwap", "INTConstant"):
        out.append(f"{n['type']} {n.get('title','')} = {n['widgets_values'][0]}")
(Path(__file__).parent / "_lan_wf_result.txt").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))
