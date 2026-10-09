"""Pull multi-year Reddit posts (and comments on the top posts) for trading subreddits from the public Arctic Shift
archive (https://arctic-shift.photon-reddit.com, a Pushshift successor; no account or API app needed).
Runs in GitHub Actions (.github/workflows/reddit-archive.yml) because the dev container's proxy blocks the host.
Output: <out>/<subreddit>/posts_<year>.jsonl.gz and comments_<year>.jsonl.gz (gzip JSON lines, trimmed fields).
Research input only (BDI, owner request 2026-10-09). Educational only - not financial advice.
    python scripts/reddit_archive.py --subs Daytrading algotrading --since 2019-01-01 --out reddit_data"""
from __future__ import annotations

import argparse
import gzip
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "https://arctic-shift.photon-reddit.com/api"
PULLPUSH = "https://api.pullpush.io/reddit/search"   # fallback archive (also Pushshift-style, no account)
UA = {"User-Agent": "mcf-research/0.1 (educational backtesting research)"}
POST_FIELDS = ("id", "title", "selftext", "score", "num_comments", "created_utc", "link_flair_text", "author", "permalink")
COMMENT_FIELDS = ("id", "link_id", "parent_id", "body", "score", "created_utc", "author")


STATS = {"arctic": 0, "pullpush": 0, "failed": 0}


def _pullpush(path: str, params: dict):
    """Same query against PullPush: /posts/search -> /submission/, /comments/search -> /comment/."""
    kind = "submission" if path.startswith("/posts") else "comment"
    q = {"subreddit": params.get("subreddit"), "after": params.get("after"), "before": params.get("before"),
         "size": 100, "sort": "asc" if params.get("sort") == "asc" else "desc",
         "sort_type": "score" if params.get("sort_type") == "score" else "created_utc", "link_id": params.get("link_id")}
    r = requests.get(f"{PULLPUSH}/{kind}/", params={k: v for k, v in q.items() if v is not None}, headers=UA, timeout=60)
    r.raise_for_status()
    return r.json().get("data") or []


DOWN = {"arctic_fails": 0}


def get(path: str, params: dict, tries: int = 4):
    if DOWN["arctic_fails"] >= 5:          # circuit breaker: Arctic Shift is down, go straight to PullPush
        for i in range(tries):
            try:
                STATS["pullpush"] += 1
                return _pullpush(path, params)
            except Exception as e:  # noqa: BLE001
                print(f"  pullpush retry {i + 1}/{tries} after {e}", flush=True)
                time.sleep(2 ** i)
        STATS["failed"] += 1
        return []
    for i in range(tries):
        try:
            STATS["arctic"] += 1
            r = requests.get(f"{API}{path}", params=params, headers=UA, timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                raise RuntimeError(f"HTTP {r.status_code}")
            r.raise_for_status()
            DOWN["arctic_fails"] = 0
            return r.json().get("data") or []
        except Exception as e:  # noqa: BLE001 - network hiccups: back off and retry
            DOWN["arctic_fails"] += 1
            wait = 2 ** i
            print(f"  arctic retry {i + 1}/{tries} after {e} ({wait}s)", flush=True)
            time.sleep(wait)
            try:  # fall back to PullPush before the next Arctic attempt
                STATS["pullpush"] += 1
                return _pullpush(path, params)
            except Exception as e2:  # noqa: BLE001
                print(f"  pullpush failed too: {e2}", flush=True)
    STATS["failed"] += 1
    return []


def trim(d: dict, fields, maxlen: int = 6000) -> dict:
    out = {k: d.get(k) for k in fields}
    for k in ("selftext", "body"):
        if isinstance(out.get(k), str) and len(out[k]) > maxlen:
            out[k] = out[k][:maxlen]
    return out


def posts(sub: str, since: int, until: int, min_score: int):
    """Monthly windows keep each archive query small (the archives time out on whole-subreddit scans)."""
    month = 31 * 86400
    lo = since
    while lo < until:
        yield from _posts(sub, lo, min(lo + month, until), min_score)
        lo += month


def _posts(sub: str, since: int, until: int, min_score: int):
    after = since
    while after < until:
        batch = get("/posts/search", {"subreddit": sub, "after": after, "before": until, "limit": 100, "sort": "asc"})
        if not batch:
            break
        for p in batch:
            if (p.get("score") or 0) >= min_score:
                yield trim(p, POST_FIELDS)
        nxt = int(max(p.get("created_utc") or 0 for p in batch))
        if nxt <= after:
            break
        after = nxt
        time.sleep(0.4)


def comments(link_id: str, min_score: int, cap: int = 200):
    got = get("/comments/search", {"link_id": link_id, "limit": 100, "sort": "desc", "sort_type": "score"})
    out = [trim(c, COMMENT_FIELDS, 3000) for c in got if (c.get("score") or 0) >= min_score]
    return out[:cap]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subs", nargs="+", required=True)
    ap.add_argument("--since", default="2019-01-01")
    ap.add_argument("--until", default=None)
    ap.add_argument("--min-score", type=int, default=5)
    ap.add_argument("--comment-posts", type=int, default=400, help="top posts per subreddit-year whose comments are pulled")
    ap.add_argument("--comment-min-score", type=int, default=3)
    ap.add_argument("--out", default="reddit_data")
    a = ap.parse_args()
    since = int(datetime.fromisoformat(a.since).replace(tzinfo=timezone.utc).timestamp())
    until = int(datetime.fromisoformat(a.until).replace(tzinfo=timezone.utc).timestamp()) if a.until else int(time.time())
    summary = {}
    for sub in a.subs:
        d = Path(a.out) / sub
        d.mkdir(parents=True, exist_ok=True)
        by_year: dict[int, list] = {}
        for p in posts(sub, since, until, a.min_score):
            by_year.setdefault(datetime.fromtimestamp(p["created_utc"], timezone.utc).year, []).append(p)
        for yr, ps in sorted(by_year.items()):
            with gzip.open(d / f"posts_{yr}.jsonl.gz", "wt") as f:
                for p in ps:
                    f.write(json.dumps(p) + "\n")
            top = sorted(ps, key=lambda p: p.get("score") or 0, reverse=True)[:a.comment_posts]
            n_c = 0
            with gzip.open(d / f"comments_{yr}.jsonl.gz", "wt") as f:
                for p in top:
                    for c in comments(f"t3_{p['id']}", a.comment_min_score):
                        f.write(json.dumps(c) + "\n")
                        n_c += 1
                    time.sleep(0.3)
            summary[f"{sub}/{yr}"] = {"posts": len(ps), "comments": n_c}
            print(f"{sub} {yr}: {len(ps)} posts (score >= {a.min_score}), {n_c} comments", flush=True)
    summary["_requests"] = STATS
    (Path(a.out) / "SUMMARY.json").write_text(json.dumps(summary, indent=1))
    print("requests:", STATS, flush=True)
    if not any(v.get("posts") for k, v in summary.items() if not k.startswith("_")):
        raise SystemExit("no posts retrieved from either archive - failing the job so it is not mistaken for success")


if __name__ == "__main__":
    main()
