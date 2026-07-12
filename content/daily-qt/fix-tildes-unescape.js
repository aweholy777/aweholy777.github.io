// fix-tildes-unescape.js — 把 content/daily-qt 底下所有 .md 內文的 \~ 改回純 ~
// 原因：本站 Goldmark 用純 ~ 顯示正常（單一 ~ 不會變刪除線），\~ 反而會露出反斜線。
// 用法（在 repo 根目錄）： node content/daily-qt/fix-tildes-unescape.js
// byte 層級替換（0x5C 0x7E -> 0x7E），完整保留 BOM 與換行；front matter 用純 ~ 不受影響。
const fs = require("fs");
const path = require("path");
const ROOT = __dirname;

function walk(dir) {
  let out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out = out.concat(walk(p));
    else if (e.isFile() && e.name.endsWith(".md")) out.push(p);
  }
  return out;
}

let filesChanged = 0, tildesFixed = 0;
for (const f of walk(ROOT)) {
  const buf = fs.readFileSync(f);
  const out = [];
  let n = 0;
  for (let i = 0; i < buf.length; i++) {
    if (buf[i] === 0x5c && buf[i + 1] === 0x7e) { out.push(0x7e); i++; n++; }
    else out.push(buf[i]);
  }
  if (n > 0) {
    fs.writeFileSync(f, Buffer.from(out));
    filesChanged++; tildesFixed += n;
  }
}
console.log(JSON.stringify({ filesChanged, tildesFixed }, null, 2));
