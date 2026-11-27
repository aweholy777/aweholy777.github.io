import re
import glob

PATTERN = re.compile(r"\n\n\n\{\{<\s*youtube\s+([\w-]+)\s*>\}\}\n\Z")


def process(path):
    text = open(path, encoding="utf-8").read()
    if "{{< youtube" not in text:
        return "SKIP_NO_SHORTCODE"
    if text.count("{{< youtube") > 1:
        return "SKIP_MULTI"
    m = PATTERN.search(text)
    if not m:
        return "SKIP_PATTERN_NOT_MATCHED"
    vid = m.group(1)
    new_text = text[: m.start()].rstrip() + "\n\n\n\n" + f"{{{{< youtube {vid} >}}}}" + "\n"
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
