"""Build a single-file demo that runs with no server (all game logic in the browser).

    python scripts/build_demo.py              # -> dist/demo.html (fragment, for hosting as a Claude artifact)
    python scripts/build_demo.py --standalone # -> dist/demo.html you can open straight from disk
"""
import argparse
import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from trivia import config  # noqa: E402
from trivia.content import load  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--standalone", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "dist" / "demo.html"))
    args = ap.parse_args()

    lib, problems = load()
    if problems:
        sys.exit("fix content first:\n" + "\n".join(problems))
    topics = json.loads((config.CONTENT_DIR / "topics.json").read_text())
    questions = json.loads((config.CONTENT_DIR / "questions.json").read_text())
    images = {}
    for q in questions["questions"]:
        if q.get("image"):
            svg = (config.WEB_DIR / q["image"]).read_bytes()
            images[q["image"]] = "data:image/svg+xml;base64," + base64.b64encode(svg).decode()
    payload = {
        "config": {"brand": config.BRAND, "level_points": config.LEVEL_POINTS, "level_themes": config.LEVEL_THEMES,
                   "default_level_theme": config.DEFAULT_LEVEL_THEME, "drop_sizes": config.DROP_SIZES,
                   "bonus_per_day": config.BONUS_PER_DAY, "perfect_drop_bonus": config.PERFECT_DROP_BONUS,
                   "ramps": config.RAMPS, "streak_multipliers": config.STREAK_MULTIPLIERS},
        "topics": topics, "questions": questions, "images": images,
    }
    html = (config.WEB_DIR / "index.html").read_text()
    body = html.split("<body>")[1].split("</body>")[0]
    body = body.replace('<script src="/app.js"></script>', "")
    data = json.dumps(payload).replace("</", "<\\/")
    js = (config.WEB_DIR / "app.js").read_text()
    head = (f"<title>{config.BRAND}</title>\n"
            '<meta name="claude:viewport-fit-sides" content="cover">\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bungee&family=Figtree:wght@400;600;800&family=JetBrains+Mono:wght@500;700&display=swap">\n'
            f"<style>\n{(config.WEB_DIR / 'app.css').read_text()}</style>\n")
    page = head + body.replace("<!--DEMO-CONTENT-->", "") + f"<script>window.TRIVIA_CONTENT={data};</script>\n<script>\n{js}</script>\n"
    if args.standalone:
        page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">' + page.replace("<style>", "</head><body><style>", 1) + "</body></html>"
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    print(f"wrote {out} ({len(page) // 1024} KB)")


if __name__ == "__main__":
    main()
