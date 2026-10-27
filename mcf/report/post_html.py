"""Owner 2026-10-27: the daily message-board post as a copy-ready page (post.html) next to post.md.

The owner copies the rendered page straight into the message board: bold shows as bold (no asterisks), one text style
throughout, a blank line between sections and tight bullet lists. Only the little markdown the template uses is
understood: **bold**, "- " bullets, blank-line paragraphs; a leading run of asterisks on a note line is dropped.

    python -m mcf.report.post_html docs/posts/2026-10-27/post.md      # -> docs/posts/2026-10-27/post.html
Educational only - not financial advice."""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

STYLE = """body{font:16px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#111;background:#fff;
max-width:760px;margin:24px auto;padding:0 16px}p{margin:0 0 14px}ul{margin:0 0 14px;padding-left:22px}li{margin:0 0 4px}
.hint{font-size:12px;color:#777;border-bottom:1px solid #eee;padding-bottom:8px;margin-bottom:16px}"""


def _inline(s: str) -> str:
    s = html.escape(s.strip())
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return s.replace("*", "")                      # no stray asterisks (owner 2026-10-27)


def to_html(md: str, title: str = "MCF daily post") -> str:
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    out, para, items = [], [], []

    def flush():
        if para:
            out.append("<p>" + "<br>".join(_inline(x) for x in para) + "</p>")
            para.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + "</ul>")
            items.clear()

    for line in md.splitlines():
        t = line.strip()
        if not t:
            flush()
            continue
        t = re.sub(r"^\*{3,}(?!\*)", "", t)        # owner's "***note" style -> plain note
        if t.startswith("- "):
            if para:
                flush()
            items.append(t[2:])
        else:
            if items:
                flush()
            para.append(t)
    flush()
    return (f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{STYLE}</style></head><body>"
            f"<div class='hint'>Select all below this line and copy - bold and spacing paste as shown.</div>"
            + "\n".join(out) + "</body></html>\n")


def main(argv=None):
    a = (argv or sys.argv[1:])
    src = Path(a[0])
    dst = src.with_suffix(".html")
    dst.write_text(to_html(src.read_text(), f"MCF post {src.parent.name}"))
    print(dst)


if __name__ == "__main__":
    main()
