import re
import sys
import glob

PATTERN_REMOVE = re.compile(r"\n\n\{\{<\s*youtube\s+([\w-]+)\s*>\}\}\n\n")
PATTERN_FIND = re.compile(r"\{\{<\s*youtube\s+([\w-]+)\s*>\}\}")


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
    targets = sys.argv[1:] if len(sys.argv) > 1 else []
    if not targets:
        targets = glob.glob("content/daily-qt/ntqt/*.md") + glob.glob("content/daily-qt/otqt/*.md")
    results = {}
    for f in targets:
        r = process(f)
        results.setdefault(r.split()[0], []).append(f)
    for k, v in results.items():
        print(f"{k}: {len(v)}")
        if k != "OK":
            for f in v[:10]:
                print("   ", f)
