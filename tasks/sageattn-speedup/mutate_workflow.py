#!/usr/bin/env python
"""Backup / apply / restore the LOCAL default InfiniteTalk workflow for the
sageattn + blockswap speed test. ASCII only. Run by run_test.ps1.

Usage:
  python mutate_workflow.py backup
  python mutate_workflow.py apply      # attention sdpa->sageattn, blockswap 40->0
  python mutate_workflow.py restore
  python mutate_workflow.py show       # print current attention + blockswap
"""
import sys, json, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
WF = HERE.parent.parent / "video-pipeline" / "workflows" / "wanvideo_2_1_14B_I2V_InfiniteTalk_example_03.json"
BAK = HERE / "wanvideo_default.sage_bak.json"


def _load():
    w = json.loads(WF.read_text(encoding="utf-8"))
    return w, (w["nodes"] if isinstance(w, dict) and "nodes" in w else w)


def show():
    w, nodes = _load()
    att = bs = None
    for n in nodes:
        if n.get("type") == "WanVideoModelLoader":
            att = n["widgets_values"][4]
        elif n.get("type") == "WanVideoBlockSwap":
            bs = n["widgets_values"][0]
    print("attention=%s blockswap=%s" % (att, bs))


def backup():
    # Idempotent: never overwrite an existing backup (would clobber the pristine
    # original with an already-applied copy if a prior run was force-killed).
    if BAK.exists():
        print("backup already exists, keeping pristine original: %s" % BAK.name)
        return
    shutil.copy2(WF, BAK)
    print("backed up %s -> %s" % (WF.name, BAK.name))


def restore():
    if not BAK.exists():
        print("ERROR: backup missing, cannot restore: %s" % BAK)
        sys.exit(2)
    shutil.copy2(BAK, WF)
    print("restored %s from backup" % WF.name)


def apply():
    w, nodes = _load()
    changed = []
    for n in nodes:
        if n.get("type") == "WanVideoModelLoader":
            old = n["widgets_values"][4]
            n["widgets_values"][4] = "sageattn"
            changed.append("attention %s->sageattn" % old)
        elif n.get("type") == "WanVideoBlockSwap":
            old = n["widgets_values"][0]
            n["widgets_values"][0] = 0
            changed.append("blockswap %s->0" % old)
    WF.write_text(json.dumps(w, ensure_ascii=False, indent=2), encoding="utf-8")
    print("applied: " + "; ".join(changed))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    {"backup": backup, "apply": apply, "restore": restore, "show": show}.get(cmd, show)()
