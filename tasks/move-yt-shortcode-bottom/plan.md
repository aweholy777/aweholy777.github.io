# 任務：把已嵌入文章的 YouTube 影片從文章上方移到文章最下方

## 背景

`content/daily-qt/` 底下每篇 QT 文章目前若已上傳影片，`{{< youtube ID >}}` shortcode 是插在
文章開頭圖片行（`![](/images/qt.jpg)`）正下方。軍師（3060）要求全部改成：**影片放在文章最下方**
（四段結構「今天的回應」內容結束後），**影片前面先空兩行**。

現況：目前只有 `content/daily-qt/ntqt/` 下有 629 篇已嵌入（`otqt` 尚未開始上傳，0 篇），
但腳本請對 `ntqt` 與 `otqt` 兩個目錄都跑（`otqt` 現在跑了也不會有東西改到，是為未來已上傳的
otqt 文章預留同一套邏輯，不需另外派工）。

## 已驗證的轉換規則（3060 已用 3 個樣本檔案實測確認正確，直接套用即可，不必自行重新設計算法）

每個含 `{{< youtube ... >}}` 的檔案：
1. 用正則 `\n\n\{\{<\s*youtube\s+([\w-]+)\s*>\}\}\n\n` 找到並擷取影片 ID，把這段（含前後各一個
   空行）整段替換成 `\n\n`（也就是刪掉 shortcode 那一行，並把原本「圖片行—空行—shortcode—空行—
   經文引用」還原成「圖片行—空行—經文引用」，不留多餘空行）。
2. 把整個文字內容 `rstrip()`（去掉檔案結尾所有空白／換行），然後在最後加上
   `"\n\n\n" + f"{{{{< youtube {vid} >}}}}" + "\n"`（等於：內容結尾 + 兩個空行 + shortcode 行 + 檔尾換行）。
3. 若同一檔案有 **超過1個** `{{< youtube` 出現，或步驟1的正則找不到匹配，一律**跳過該檔、記錄下來**，
   不要用其他方式硬改——這代表檔案結構跟預期不同，需要回報給軍師人工看，不要自己發明別的處理方式。
4. 處理後務必檢查新內容裡 `{{< youtube` 出現次數仍是 1（防止誤刪或重複），不是 1 就整個檔案還原
   （不寫入），記錄為異常。

## 請直接使用下面這支已驗證過的 Python 腳本（不要自己重寫算法，內容照抄存檔即可）

存成 `tasks/move-yt-shortcode-bottom/move_yt_to_bottom.py`：

```python
import re
import sys
import glob

PATTERN_REMOVE = re.compile(r"\n\n\{\{<\s*youtube\s+([\w-]+)\s*>\}\}\n\n")


def process(path):
    text = open(path, encoding="utf-8").read()
    if "{{< youtube" not in text:
        return "SKIP_NO_SHORTCODE"
    if text.count("{{< youtube") > 1:
        return "SKIP_MULTI"

    m = PATTERN_REMOVE.search(text)
    if not m:
        return "SKIP_PATTERN_NOT_MATCHED"
    vid = m.group(1)
    new_text = PATTERN_REMOVE.sub("\n\n", text, count=1)
    new_text = new_text.rstrip() + "\n\n\n" + f"{{{{< youtube {vid} >}}}}" + "\n"

    if new_text.count("{{< youtube") != 1:
        return "ABORT_POST_CHECK_FAILED"

    open(path, "w", encoding="utf-8").write(new_text)
    return f"OK vid={vid}"


if __name__ == "__main__":
    targets = glob.glob("content/daily-qt/ntqt/*.md") + glob.glob("content/daily-qt/otqt/*.md")
    results = {}
    for f in targets:
        r = process(f)
        key = r.split()[0]
        results.setdefault(key, []).append(f)
    for k, v in results.items():
        print(f"{k}: {len(v)}")
        if k != "OK":
            for f in v:
                print("   ", f)
```

## 執行步驟

1. 在 repo 根目錄（`C:\Users\user\qtproject`）存檔上面那支腳本到
   `tasks/move-yt-shortcode-bottom/move_yt_to_bottom.py`。
2. 執行：`python tasks/move-yt-shortcode-bottom/move_yt_to_bottom.py`
   （Python 路徑：`C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe`）
3. 記下輸出的統計（`OK: N`、有無 `SKIP_*` / `ABORT_*` 及是哪些檔案）。
4. 跑 `hugo --buildFuture`（在 repo 根目錄）確認建置無錯誤。
5. 跑 `git diff --stat` 確認**只有** `content/daily-qt/ntqt/*.md`（理論上應該是那 629 篇被上傳過影片
   的檔案）被改動，**不應該**動到 `otqt`（目前是0篇）、`_index.md`、或任何非 QT 文章檔案。
6. **不要 commit / push**——改完、驗證完，只把結果寫進 `result.md`，讓軍師（3060）自己 review 後決定
   何時 commit。

## 驗收標準（軍師會檢查）

- `OK` 數量應該等於 629（目前已知的嵌入影片篇數；若跑的當下數字略有出入是因為期間又有新影片上傳，
  屬正常，不是錯誤）。
- 不應該有任何 `SKIP_MULTI` / `SKIP_PATTERN_NOT_MATCHED` / `ABORT_POST_CHECK_FAILED`（3060 已抽測
  3 個檔案結構完全一致，理論上不會有異常；如果真的出現，原樣記錄檔名，不要自己想辦法修，等軍師看）。
- 隨便抽 2~3 篇改完的檔案人工看一下：文章開頭應該只剩「圖片—空行—經文引用」（不再有 shortcode），
  文章結尾「今天的回應」內容之後應該是「空行、空行、`{{< youtube ID >}}`」。
- `hugo --buildFuture` 必須無錯誤（shortcode 語法沒有壞掉）。
- `git diff --stat` 範圍只在 `content/daily-qt/ntqt/*.md`（0 篇 otqt 不應出現在 diff 裡）。

## result.md 請包含

- `OK` / `SKIP_*` / `ABORT_*` 各自的數量
- 若有非 `OK` 的檔案，列出檔名清單
- `hugo --buildFuture` 是否成功
- `git diff --stat` 的總行數摘要（不用貼整份 diff）
- 抽查的 2~3 篇檔案，確認頭尾格式正確（一句話總結即可，不用貼全文）
