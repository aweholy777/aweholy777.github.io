# 雙機信箱（git 非同步交接）

3060（軍師）與 5090（執行）各跑自己的 Claude Code，共用同一帳號但**是兩個獨立程序**，
彼此不即時互通，靠這個資料夾 + git 溝通。

## 規則（嚴格遵守，才不會 git 衝突）

- `3060-to-5090.md`：**只有 3060 寫**，5090 只讀。
- `5090-to-3060.md`：**只有 5090 寫**，3060 只讀。
- 單一寫入者 → 不會撞 merge conflict。
- 每次 `git pull --rebase` 後，**先讀「給自己的那一份」**，看有沒有新指令 / 回報。
- 寫完自己那一份，`git add` **只加自己那一個檔** → commit → `git pull --rebase --autostash` → push。
- 格式：**最新的放最上面**，每則開頭標 `## [YYYY-MM-DD] STATUS：TODO / DONE / BLOCKED / FYI`。

## 流程

3060 寫指令 → push → 5090 pull 讀到 → 執行 → 把結果寫進 5090-to-3060.md → push
→ 3060 pull 讀到 → 接著回應。如此往返。
