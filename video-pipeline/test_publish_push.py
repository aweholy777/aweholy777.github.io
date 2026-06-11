#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性測試：把已上傳的 2026-05-30 嵌入推送到發布副本"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from yt_publish import publish_push, REPO

md = REPO / "content" / "daily-qt" / "ntqt" / "2026-05-30.md"
result = publish_push([(md, "jhTdaflDIpo")])
out = Path(__file__).parent / "_pubpush_test.txt"
out.write_text(result, encoding="utf-8")
print(result)
