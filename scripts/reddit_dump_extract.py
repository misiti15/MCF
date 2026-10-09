"""Extract trading-subreddit posts/comments from Watchful1's per-subreddit Pushshift dumps (Academic Torrents,
zstandard ndjson: <name>_submissions.zst / <name>_comments.zst). Keeps posts from --since with score >= --min-score
and comments with score >= --comment-min-score, trimmed, written as <out>/<sub>/{posts,comments}_<year>.jsonl.gz.
Used by .github/workflows/reddit-dumps.yml (the live archive APIs refuse datacenter IPs). Research input only.
Educational only - not financial advice."""
from __future__ import annotations

import argparse
import gzip
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import zstandard

POST = ("id", "title", "selftext", "score", "num_comments", "created_utc", "link_flair_text", "author", "permalink")
COMMENT = ("id", "link_id", "parent_id", "body", "score", "created_utc", "author")


def lines(path: Path):
    with open(path, "rb") as fh:
        reader = zstandard.ZstdDecompressor(max_window_size=2 ** 31).stream_reader(fh)
        for line in io.TextIOWrapper(reader, encoding="utf-8", errors="replace"):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def trim(d, fields, n):
    out = {k: d.get(k) for k in fields}
    for k in ("selftext", "body"):
        if isinstance(out.get(k), str) and len(out[k]) > n:
            out[k] = out[k][:n]
    return out


def extract(src: Path, kind: str, sub: str, out: Path, since: float, min_score: int) -> dict:
    fields, cap = (POST, 6000) if kind == "posts" else (COMMENT, 3000)
    files, counts = {}, {}
    try:
        for d in lines(src):
            try:
                ts = float(d.get("created_utc") or 0)
            except (TypeError, ValueError):
                continue
            if ts < since or (d.get("score") or 0) < min_score:
                continue
            if kind == "posts" and d.get("selftext") in ("[removed]", "[deleted]") and (d.get("score") or 0) < 20:
                continue
            yr = datetime.fromtimestamp(ts, timezone.utc).year
            if yr not in files:
                (out / sub).mkdir(parents=True, exist_ok=True)
                files[yr] = gzip.open(out / sub / f"{kind}_{yr}.jsonl.gz", "wt")
            files[yr].write(json.dumps(trim(d, fields, cap)) + "\n")
            counts[yr] = counts.get(yr, 0) + 1
    finally:
        for f in files.values():
            f.close()
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="where the torrent files landed")
    ap.add_argument("--subs", nargs="+", required=True)
    ap.add_argument("--since", default="2019-01-01")
    ap.add_argument("--min-score", type=int, default=5)
    ap.add_argument("--comment-min-score", type=int, default=5)
    ap.add_argument("--out", default="reddit_data")
    a = ap.parse_args()
    since = datetime.fromisoformat(a.since).replace(tzinfo=timezone.utc).timestamp()
    found = {p.name.lower(): p for p in Path(a.dir).rglob("*.zst")}
    summary = {}
    for sub in a.subs:
        for kind, suffix, ms in (("posts", "submissions", a.min_score), ("comments", "comments", a.comment_min_score)):
            p = found.get(f"{sub.lower()}_{suffix}.zst")
            if p is None:
                summary[f"{sub}/{kind}"] = "not in the dump (not a top-40k subreddit?)"
                continue
            summary[f"{sub}/{kind}"] = extract(p, kind, sub, Path(a.out), since, ms)
            print(sub, kind, summary[f"{sub}/{kind}"], flush=True)
    Path(a.out).mkdir(exist_ok=True)
    (Path(a.out) / "SUMMARY.json").write_text(json.dumps(summary, indent=1))
    if not any(isinstance(v, dict) and v for v in summary.values()):
        raise SystemExit("nothing extracted")


if __name__ == "__main__":
    main()
