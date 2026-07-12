const fs = require("fs");
const path = require("path");

const ROOT = __dirname;
const OT_SECTION = "otqt";
const NT_SECTION = "ntqt";

const BOOKS = [
  "創世記", "出埃及記", "利未記", "民數記", "申命記",
  "約書亞記", "士師記", "路得記", "撒母耳記上", "撒母耳記下",
  "列王紀上", "列王紀下", "歷代志上", "歷代志下", "以斯拉記",
  "尼希米記", "以斯帖記", "約伯記", "詩篇", "箴言",
  "傳道書", "雅歌", "以賽亞書", "耶利米書", "耶利米哀歌",
  "以西結書", "但以理書", "何西阿書", "約珥書", "阿摩司書",
  "俄巴底亞書", "約拿書", "彌迦書", "那鴻書", "哈巴谷書",
  "西番雅書", "哈該書", "撒迦利亞書", "瑪拉基書", "馬太福音",
  "馬可福音", "路加福音", "約翰福音", "使徒行傳", "羅馬書",
  "哥林多前書", "哥林多後書", "加拉太書", "以弗所書", "腓立比書",
  "歌羅西書", "帖撒羅尼迦前書", "帖撒羅尼迦後書", "提摩太前書",
  "提摩太後書", "提多書", "腓利門書", "希伯來書", "雅各書",
  "彼得前書", "彼得後書", "約翰壹書", "約翰貳書", "約翰參書",
  "猶大書", "啟示錄",
];

const OLD_TESTAMENT_BOOKS = new Set(BOOKS.slice(0, BOOKS.indexOf("馬太福音")));
const NEW_TESTAMENT_BOOKS = new Set(BOOKS.slice(BOOKS.indexOf("馬太福音")));
const BOOK_INDEX = new Map(BOOKS.map((book, index) => [book, index]));

const ALIASES = new Map(BOOKS.map((book) => [book, book]));
[
  ["詩", "詩篇"],
  ["箴言書", "箴言"],
  ["西番亞書", "西番雅書"],
  ["撒上", "撒母耳記上"],
  ["撒下", "撒母耳記下"],
  ["王上", "列王紀上"],
  ["王下", "列王紀下"],
  ["代上", "歷代志上"],
  ["代下", "歷代志下"],
  ["約壹", "約翰壹書"],
  ["約貳", "約翰貳書"],
  ["約參", "約翰參書"],
].forEach(([alias, book]) => ALIASES.set(alias, book));

const escapeRegExp = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
// 本站 Goldmark 把單一 ~ 當刪除線符號，寫進 _index.md 前必須把標題的 ~ 跳脫成 \~
const escapeTilde = (value) => value.replace(/(?<!\\)~/g, "\\~");
const BOOK_PATTERN = [...ALIASES.keys()]
  .sort((a, b) => b.length - a.length)
  .map(escapeRegExp)
  .join("|");

const TITLE_REF_RE = new RegExp(
  `QT\\s+(?<book>${BOOK_PATTERN})\\s*(?<chap>\\d+)?\\s*(?:[：:]|篇)?\\s*` +
    `(?<start>\\d+)?(?:\\s*(?:[~～-]|\\\\~)\\s*(?:(?<endchap>\\d+)\\s*[：:])?(?<end>\\d+))?(?:節)?`
);
const INDEX_LINK_RE = /^- \[(?<title>.+?)\]\((?<href>[^)]+)\)/;

function walkDateFiles(dir) {
  const files = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walkDateFiles(fullPath));
    } else if (entry.isFile() && /^\d{4}-\d{2}-\d{2}\.md$/.test(entry.name)) {
      files.push(fullPath);
    }
  }
  return files;
}

function titleFrom(markdown) {
  return markdown.match(/^title:\s*"([^"]+)"/m)?.[1] || "";
}

function frontMatter(markdown, title) {
  const match = markdown.match(/^(---[\s\S]*?---)\s*/);
  if (match) return match[1];

  return `---\ntitle: "${title}"\ndraft: false\n---`;
}

function parseReference(title) {
  const match = title.match(TITLE_REF_RE);
  if (!match?.groups?.book || !match.groups.chap) return null;

  return {
    book: ALIASES.get(match.groups.book),
    chap: Number(match.groups.chap),
    start: Number(match.groups.start || 1),
    endchap: Number(match.groups.endchap || match.groups.chap),
    end: Number(match.groups.end || match.groups.start || 999),
  };
}

function sectionFor(book) {
  if (OLD_TESTAMENT_BOOKS.has(book)) return OT_SECTION;
  if (NEW_TESTAMENT_BOOKS.has(book)) return NT_SECTION;
  return "";
}

function sortItems(a, b) {
  return (
    BOOK_INDEX.get(a.ref.book) - BOOK_INDEX.get(b.ref.book) ||
    a.ref.chap - b.ref.chap ||
    a.ref.start - b.ref.start ||
    a.ref.endchap - b.ref.endchap ||
    a.ref.end - b.ref.end ||
    a.date.localeCompare(b.date)
  );
}

function buildFallbackTitles() {
  const fallbackTitles = new Map();

  for (const indexPath of [
    path.join(ROOT, "_index.md"),
    path.join(ROOT, OT_SECTION, "_index.md"),
    path.join(ROOT, NT_SECTION, "_index.md"),
  ]) {
    if (!fs.existsSync(indexPath)) continue;

    const indexMarkdown = fs.readFileSync(indexPath, "utf8");
    for (const line of indexMarkdown.split(/\r?\n/)) {
      const match = line.match(INDEX_LINK_RE);
      if (!match) continue;

      const date = match.groups.href.match(/(\d{4}-\d{2}-\d{2})\//)?.[1];
      if (date) fallbackTitles.set(`${date}.md`, match.groups.title);
    }
  }

  return fallbackTitles;
}

function parseItems() {
  const fallbackTitles = buildFallbackTitles();
  const items = [];
  const unparsed = [];

  for (const filePath of walkDateFiles(ROOT)) {
    const rel = path.relative(ROOT, filePath).replace(/\\/g, "/");
    const date = path.basename(filePath, ".md");
    const markdown = fs.readFileSync(filePath, "utf8");

    let title = titleFrom(markdown);
    if (!parseReference(title) && fallbackTitles.has(`${date}.md`)) {
      title = fallbackTitles.get(`${date}.md`);
    }

    let ref = parseReference(title);
    if (!ref) {
      const originalUrl = markdown.match(/^# original_url:\s*(\S+)/m)?.[1] || "";
      try {
        const decoded = decodeURIComponent(originalUrl).replace(/-/g, " ");
        ref = parseReference(decoded.replace(/(\d{4}) (\d{2}) (\d{2}) qt /i, "$1 - $2 - $3 QT "));
        if (ref && !title) title = fallbackTitles.get(`${date}.md`) || decoded;
      } catch {
        // Leave this item in the unparsed group below.
      }
    }

    if (!ref) {
      unparsed.push({ rel, date, title, filePath });
    } else {
      const section = sectionFor(ref.book);
      items.push({ rel, date, title, ref, section, filePath });
    }
  }

  items.sort(sortItems);
  return { items, unparsed };
}

function ensureSectionDirs() {
  for (const section of [OT_SECTION, NT_SECTION]) {
    const dir = path.join(ROOT, section);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir);
  }
}

function moveItems(items) {
  ensureSectionDirs();
  let moved = 0;

  for (const item of items) {
    const target = path.join(ROOT, item.section, `${item.date}.md`);
    if (path.resolve(item.filePath) === path.resolve(target)) continue;
    if (fs.existsSync(target)) {
      throw new Error(`Target already exists: ${target}`);
    }
    fs.renameSync(item.filePath, target);
    moved += 1;
  }

  return moved;
}

function buildRootIndex(rootIndexMarkdown, otCount, ntCount, unparsed) {
  const fm = frontMatter(rootIndexMarkdown, "每日QT");
  let output = `${fm}\n\n# 每日QT\n\n`;
  output += "每日 QT 已依聖經分為舊約 QT 與新約 QT。\n\n";
  output += `- [otqt 舊約QT](${OT_SECTION}/) (${otCount} 篇)\n`;
  output += `- [ntqt 新約QT](${NT_SECTION}/) (${ntCount} 篇)\n`;

  if (unparsed.length) {
    output += "\n## 未辨識經文\n\n";
    for (const item of unparsed) {
      output += `- [${escapeTilde(item.title || item.date)}](${item.date}/)\n`;
    }
  }

  return output;
}

function buildSectionIndex(existingMarkdown, title, description, items) {
  const fm = frontMatter(existingMarkdown || "", title);
  let output = `${fm}\n\n# ${title}\n\n${description}\n\n`;

  let currentBook = "";
  for (const item of items) {
    if (item.ref.book !== currentBook) {
      currentBook = item.ref.book;
      output += `## ${currentBook}\n\n`;
    }
    output += `- [${escapeTilde(item.title)}](${item.date}/)\n`;
  }

  return output;
}

function writeIndexes(items, unparsed) {
  const otItems = items.filter((item) => item.section === OT_SECTION).sort(sortItems);
  const ntItems = items.filter((item) => item.section === NT_SECTION).sort(sortItems);

  const rootIndexPath = path.join(ROOT, "_index.md");
  const rootIndexMarkdown = fs.existsSync(rootIndexPath) ? fs.readFileSync(rootIndexPath, "utf8") : "";
  fs.writeFileSync(rootIndexPath, buildRootIndex(rootIndexMarkdown, otItems.length, ntItems.length, unparsed), "utf8");

  const otIndexPath = path.join(ROOT, OT_SECTION, "_index.md");
  const ntIndexPath = path.join(ROOT, NT_SECTION, "_index.md");
  const otMarkdown = fs.existsSync(otIndexPath) ? fs.readFileSync(otIndexPath, "utf8") : "";
  const ntMarkdown = fs.existsSync(ntIndexPath) ? fs.readFileSync(ntIndexPath, "utf8") : "";

  fs.writeFileSync(
    otIndexPath,
    buildSectionIndex(otMarkdown, "舊約QT", "以下清單依舊約聖經書卷順序排列；相同經文會排在一起。", otItems),
    "utf8"
  );
  fs.writeFileSync(
    ntIndexPath,
    buildSectionIndex(ntMarkdown, "新約QT", "以下清單依新約聖經書卷順序排列；相同經文會排在一起。", ntItems),
    "utf8"
  );

  return { otItems: otItems.length, ntItems: ntItems.length };
}

function main() {
  ensureSectionDirs();
  let { items, unparsed } = parseItems();
  const moved = moveItems(items);

  if (moved > 0) {
    ({ items, unparsed } = parseItems());
  }

  const counts = writeIndexes(items, unparsed);
  console.log(JSON.stringify({ moved, ...counts, unparsed: unparsed.map(({ rel, date, title }) => ({ rel, date, title })) }, null, 2));
}

main();
