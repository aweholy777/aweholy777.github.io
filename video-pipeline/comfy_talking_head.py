#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""comfy_talking_head.py — 透過 ComfyUI API 用 InfiniteTalk 生成數位主播影片

特點：直接吃 UI 格式的工作流 JSON（example_workflows 那種），
在執行時用 ComfyUI 的 /object_info 自動轉成 API 格式，
不需要在 GUI 手動「匯出 (API)」。

前提：Comfy Desktop 正在執行（API 在 127.0.0.1:8000 或 8188）。
"""
import json
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

COMFY_URLS = ["http://127.0.0.1:8000", "http://127.0.0.1:8188"]
LAN_URL = "http://192.168.68.61:8188"   # MS-S1 MAX（Ubuntu，57GB VRAM）
COMFY_INPUT_DIR = Path(r"C:\Users\aweholy\ComfyUI-Shared\input")
DEFAULT_WORKFLOW = Path(__file__).parent / "workflows" / "wanvideo_2_1_14B_I2V_InfiniteTalk_example_03.json"

VIRTUAL = {"Note", "MarkdownNote", "SetNode", "GetNode", "PreviewAny"}
SEED_CONTROL = {"fixed", "increment", "decrement", "randomize"}


def _get(base, path, timeout=60):
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return json.loads(r.read())


def _post(base, path, payload, timeout=120):
    req = urllib.request.Request(base + path, data=json.dumps(payload).encode(),
                                 method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {e.code} {path}：{body[:2000]}")


def find_server(server=None):
    """server 可為 'lan'、'local' 或完整 URL；None 則依序嘗試本機"""
    if server == "lan":
        candidates = [LAN_URL]
    elif server in (None, "local"):
        candidates = COMFY_URLS
    else:
        candidates = [server]
    for u in candidates:
        try:
            _get(u, "/system_stats", timeout=5)
            return u
        except Exception:
            continue
    raise RuntimeError(f"找不到 ComfyUI API（嘗試過 {candidates}）")


def upload_file(base, filepath: Path) -> str:
    """透過 API 上傳檔案到 ComfyUI 的 input 目錄（遠端主機用），回傳檔名"""
    boundary = uuid.uuid4().hex
    name = filepath.name
    body = (f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="image"; filename="{name}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n").encode() \
        + filepath.read_bytes() \
        + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(base + "/upload/image", data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["name"]


def ui_to_api(ui: dict, object_info: dict) -> dict:
    """UI 格式工作流 → /prompt 用的 API 格式。
    處理 SetNode/GetNode 虛擬連線、widget 轉 input、seed 控制欄位、可達性修剪。"""
    nodes = {n["id"]: n for n in ui["nodes"]}
    links = {l[0]: l for l in ui.get("links", [])}  # id:[id,src,sslot,dst,dslot,type]

    setmap = {}  # Set 名稱 → (src_node, src_slot)
    for n in ui["nodes"]:
        if n["type"] == "SetNode":
            ln = n["inputs"][0].get("link")
            if ln is not None:
                l = links[ln]
                setmap[n["widgets_values"][0]] = (l[1], l[2])

    def resolve(src, slot):
        seen = 0
        while seen < 20:
            n = nodes[src]
            if n["type"] == "GetNode":
                src, slot = setmap[n["widgets_values"][0]]
            elif n["type"] == "SetNode":
                l = links[n["inputs"][0]["link"]]
                src, slot = l[1], l[2]
            else:
                return src, slot
            seen += 1
        raise RuntimeError("Set/Get 解析迴圈")

    api = {}
    for nid, n in nodes.items():
        if n["type"] in VIRTUAL or n.get("mode") in (2, 4):
            continue
        info = object_info.get(n["type"])
        if info is None:
            # 未安裝的節點：直接略過。若它在可達路徑上，/prompt 驗證會給出明確錯誤
            print(f"  （略過未安裝節點 {n['type']}，預期會被修剪）", flush=True)
            continue

        # 此節點各輸入的連線（解析過虛擬節點）
        linkbyname = {}
        widget_linked = set()
        for inp in n.get("inputs", []):
            if inp.get("link") is not None:
                l = links[inp["link"]]
                linkbyname[inp["name"]] = resolve(l[1], l[2])
                if inp.get("widget"):
                    widget_linked.add(inp["name"])

        wv = n.get("widgets_values")
        inputs = {}
        if isinstance(wv, dict):  # 如 VHS_VideoCombine
            for k, v in wv.items():
                if k != "videopreview":
                    inputs[k] = v
            for name, (s, sl) in linkbyname.items():
                inputs[name] = [str(s), sl]
        else:
            queue = list(wv or [])
            spec = info.get("input", {})
            for section in ("required", "optional"):
                for name, conf in (spec.get(section) or {}).items():
                    t = conf[0] if isinstance(conf, (list, tuple)) else conf
                    is_widget = isinstance(t, list) or (
                        isinstance(t, str) and t in ("INT", "FLOAT", "STRING",
                                                     "BOOLEAN", "COMBO"))
                    if name in linkbyname:
                        s, sl = linkbyname[name]
                        inputs[name] = [str(s), sl]
                        if name in widget_linked and queue:
                            queue.pop(0)  # 被轉成連線的 widget 仍佔一格
                            if name in ("seed", "noise_seed") and queue and \
                               isinstance(queue[0], str) and queue[0] in SEED_CONTROL:
                                queue.pop(0)
                    elif is_widget and queue:
                        inputs[name] = queue.pop(0)
                        if name in ("seed", "noise_seed") and queue and \
                           isinstance(queue[0], str) and queue[0] in SEED_CONTROL:
                            queue.pop(0)
        api[str(nid)] = {"class_type": n["type"], "inputs": inputs}

    # 可達性修剪：從 output 節點往回走，未用到的載入器一律剔除
    roots = [nid for nid, e in api.items()
             if object_info.get(e["class_type"], {}).get("output_node")]
    keep, stack = set(), list(roots)
    while stack:
        cur = stack.pop()
        if cur in keep:
            continue
        keep.add(cur)
        for v in api[cur]["inputs"].values():
            if isinstance(v, list) and len(v) == 2 and str(v[0]) in api:
                stack.append(str(v[0]))
    return {k: v for k, v in api.items() if k in keep}


def generate(image_path, audio_path, workflow_json=None, out_path=None,
             timeout_min=1800, poll_sec=20, server=None) -> Path:
    """跑一次 InfiniteTalk，回傳下載好的影片路徑"""
    image_path, audio_path = Path(image_path), Path(audio_path)
    out_path = Path(out_path)
    base = find_server(server)

    is_local = "127.0.0.1" in base or "localhost" in base
    if is_local:
        # 本機：直接複製進 input 目錄（最可靠）
        img_name = "qt_" + image_path.name
        aud_name = "qt_" + audio_path.stem + audio_path.suffix
        COMFY_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy(image_path, COMFY_INPUT_DIR / img_name)
        shutil.copy(audio_path, COMFY_INPUT_DIR / aud_name)
    else:
        # 遠端（LAN 主機）：用 API 上傳
        img_name = upload_file(base, image_path)
        aud_name = upload_file(base, audio_path)

    if workflow_json is None and not is_local:
        lan_wf = Path(__file__).parent / "workflows" / "infinitetalk_lan.json"
        if lan_wf.exists():
            workflow_json = lan_wf

    ui = json.loads(Path(workflow_json or DEFAULT_WORKFLOW).read_text(encoding="utf-8"))
    # 執行期修補：圖片、音訊、輸出檔名前綴
    for n in ui["nodes"]:
        if n["type"] == "LoadImage":
            n["widgets_values"][0] = img_name
        elif n["type"] == "LoadAudio":
            n["widgets_values"][0] = aud_name
        elif n["type"] == "VHS_VideoCombine" and isinstance(n.get("widgets_values"), dict):
            n["widgets_values"]["filename_prefix"] = "qt_head_" + audio_path.stem

    object_info = _get(base, "/object_info", timeout=120)
    prompt = ui_to_api(ui, object_info)
    (Path(__file__).parent / "_last_prompt.json").write_text(
        json.dumps(prompt, ensure_ascii=False, indent=1), encoding="utf-8")

    res = _post(base, "/prompt", {"prompt": prompt})
    if "prompt_id" not in res:
        raise RuntimeError("排隊失敗：" + json.dumps(res)[:500])
    pid = res["prompt_id"]
    t0 = time.time()
    print(f"  ComfyUI 任務 {pid} 已排隊（3060 全文生成可能要數小時，可看 ComfyUI 視窗進度）",
          flush=True)

    deadline = time.time() + timeout_min * 60
    while time.time() < deadline:
        time.sleep(poll_sec)
        hist = _get(base, f"/history/{pid}", timeout=60)
        if pid not in hist:
            continue
        entry = hist[pid]
        st = entry.get("status", {})
        if st.get("status_str") == "error":
            msgs = [m for m in st.get("messages", []) if m[0] == "execution_error"]
            detail = msgs[-1][1].get("exception_message", "") if msgs else ""
            raise RuntimeError(f"ComfyUI 執行錯誤：{detail[:400]}")
        vids = [f for o in entry.get("outputs", {}).values()
                for f in o.get("gifs", []) + o.get("videos", [])]
        if vids:
            v = vids[0]
            q = urllib.parse.urlencode({"filename": v["filename"],
                                        "subfolder": v.get("subfolder", ""),
                                        "type": v.get("type", "output")})
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(f"{base}/view?{q}", timeout=1800) as r, \
                 open(out_path, "wb") as f:
                shutil.copyfileobj(r, f)
            mins = (time.time() - t0) / 60
            print(f"  生成完成，耗時 {mins:.1f} 分鐘", flush=True)
            return out_path
    raise TimeoutError(f"等待 {timeout_min} 分鐘仍未完成")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--workflow", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout-min", type=int, default=1800)
    ap.add_argument("--server", default=None, help="local / lan / 完整URL")
    a = ap.parse_args()
    print(generate(a.image, a.audio, a.workflow, a.out, a.timeout_min, server=a.server))
