"""PRE1 (owner 2026-11-03): record borrow flags and FINRA daily short volume each morning, to learn from later.

Why: research/bdi/eu1103/preopen/NOTES.md - Alpaca's shortable / easy-to-borrow flags are "current state only, no
history", and FINRA Reg SHO short volume is free but must be collected. Recording both daily lets a short-side
borrow / short-pressure feature be back-tested in a few months. Research data only: nothing in the live path reads it.

What one run records (one gzipped CSV per trading day, `borrow/<day>.csv.gz` on the `mcf-data-borrow` branch):
  * Alpaca asset flags at ~09:08 ET, from ONE read-only GET /v2/assets (primary keys): shortable, easy_to_borrow,
    borrow_status, marginable, margin_requirement_short, maintenance_margin_requirement, ptp. Kept for every
    tradable common stock / ETF on a major exchange (the same candidate filter the universe builder uses, ~12k
    rows), so the file is a superset of today's universe. `in_universe` / `tier` / `adv_rank` come from the newest
    live universe.csv on `mcf-data` - that file is committed at the end of each session, so at 09:08 it is the
    PREVIOUS session's universe (its `built_at` is in index.jsonl). Today's exact universe is the universe.csv that
    mcf-data commits later the same day; join on symbol for an exact match.
  * FINRA Reg SHO consolidated daily short volume for the PRIOR session (CNMSshvol<YYYYMMDD>.txt, free CDN).
    That is short-sale VOLUME, not short interest. A missing file (holiday, late publication, CDN error) leaves
    the columns empty and is logged as finra_status in index.jsonl; the run still succeeds.
  * One summary line per day in `borrow/index.jsonl` (counts, statuses, run time).

Read-only: GET /v2/calendar and GET /v2/assets on Alpaca (the same urllib pattern as mcf.execution.session_guard),
one GET on cdn.finra.org. Keys are read from the environment and never printed or written.

Size / runtime (measured 2026-11-03 on the live /v2/assets response; see research/ops/pre1/NOTES.md): ~12k rows,
~215 KB gzipped per day (upper bound), ~55 MB per year; ~5 s of fetching; one ~0.5 runner-minute job a day.
Stdlib only, so the workflow needs no pip install. Educational only - not financial advice.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
ALPACA = "https://paper-api.alpaca.markets/v2"
FINRA_URL = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{d}.txt"
EXCHANGES = {"NYSE", "NASDAQ", "ARCA", "AMEX", "BATS"}       # as mcf.data.universe
BAD_SUFFIX = ("W", "WS", "U", "R")
WINDOW = ("08:45", "10:00")                                  # ET; outside it a scheduled run does nothing
COLUMNS = ["symbol", "exchange", "shortable", "easy_to_borrow", "borrow_status", "marginable", "margin_req_short",
           "maint_margin_req", "ptp", "in_universe", "tier", "adv_rank", "short_volume", "short_exempt_volume",
           "total_volume", "finra_market"]
README = """# MCF borrow / short-volume record (PRE1, owner 2026-11-03)

Written each trading morning (~09:08 ET) by .github/workflows/borrow-record.yml (mcf/data/borrow_record.py).

* `borrow/<day>.csv.gz` - one file per trading day: Alpaca asset flags at ~09:08 ET (shortable, easy_to_borrow,
  borrow_status, marginable, short margin requirement, PTP) for every tradable common stock / ETF on a major
  exchange, the previous session's universe tier, and the FINRA Reg SHO daily short volume of the prior session
  (short-sale VOLUME, not short interest). Booleans are 1/0; empty = not available.
* `borrow/index.jsonl` - one line per day: counts, finra_status (ok / missing / error), universe built_at, run time.

Retention: keep every day (about 200 KB a day, ~55 MB a year). If the branch passes ~250 MB, fold whole years
into one zstd parquet on `research-data` and drop the daily files of those years from this branch (history may then
be squashed). Nothing in the live trading path reads this branch.

Educational only - not financial advice.
"""


def _b(v) -> str:
    return "1" if v else "0"


def alpaca_get(path: str, params: dict | None = None, timeout: int = 60):
    """GET on the Alpaca trading API (read-only). Keys come from the environment and are never logged."""
    key, sec = os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"]
    q = ("?" + "&".join(f"{k}={v}" for k, v in params.items())) if params else ""
    req = urllib.request.Request(f"{ALPACA}{path}{q}", headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": sec})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def http_text(url: str, timeout: int = 30) -> tuple[int, str]:
    """(status, body) for a public URL; network errors -> (0, reason)."""
    req = urllib.request.Request(url, headers={"User-Agent": "MCF research recorder"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:  # noqa: BLE001 - a FINRA hiccup must not fail the run
        return 0, type(e).__name__


def sessions(day: date, get=alpaca_get) -> tuple[bool | None, date]:
    """(is `day` a market day, prior session). Calendar unreachable -> (None, previous weekday)."""
    try:
        cal = get("/calendar", {"start": (day - timedelta(days=14)).isoformat(), "end": day.isoformat()})
        days = sorted(date.fromisoformat(c["date"]) for c in cal)
        prior = [d for d in days if d < day]
        return (day in days), (prior[-1] if prior else _prev_weekday(day))
    except Exception as e:  # noqa: BLE001
        print(f"calendar unreachable ({type(e).__name__}); assuming a market day")
        return None, _prev_weekday(day)


def _prev_weekday(day: date) -> date:
    d = day - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def candidate_flags(assets: list[dict]) -> dict[str, dict]:
    """symbol -> flags, with mcf.data.universe.candidate_assets' filter (tradable, major exchange, no ./, no
    warrants / units / rights)."""
    out = {}
    for a in assets:
        sym, ex = str(a.get("symbol") or ""), str(a.get("exchange") or "")
        if not sym or not a.get("tradable") or ex not in EXCHANGES or "." in sym or "/" in sym:
            continue
        if len(sym) == 5 and sym.endswith(BAD_SUFFIX):
            continue
        attrs = a.get("attributes") or []
        out[sym] = {"symbol": sym, "exchange": ex, "shortable": _b(a.get("shortable")),
                    "easy_to_borrow": _b(a.get("easy_to_borrow")), "borrow_status": a.get("borrow_status") or "",
                    "marginable": _b(a.get("marginable")),
                    "margin_req_short": "" if a.get("margin_requirement_short") is None else str(a["margin_requirement_short"]),
                    "maint_margin_req": "" if a.get("maintenance_margin_requirement") is None
                    else str(a["maintenance_margin_requirement"]),
                    "ptp": _b(any("ptp" in str(x).lower() for x in attrs))}
    return out


def parse_finra(text: str) -> dict[str, dict]:
    """CNMSshvol file (Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market, then a trailer count line)."""
    out = {}
    rows = csv.reader(io.StringIO(text), delimiter="|")
    head = next(rows, None)
    if not head or "Symbol" not in head:
        return out
    ix = {h: i for i, h in enumerate(head)}
    for r in rows:
        if len(r) < len(head) or not r[ix["Date"]].strip().isdigit():
            continue          # trailer / blank lines
        out[r[ix["Symbol"]]] = {"short_volume": r[ix["ShortVolume"]], "short_exempt_volume": r[ix["ShortExemptVolume"]],
                                "total_volume": r[ix["TotalVolume"]], "finra_market": r[ix["Market"]] if "Market" in ix else ""}
    return out


def fetch_finra(prior: date, fetch=http_text) -> tuple[str, dict[str, dict]]:
    code, body = fetch(FINRA_URL.format(d=prior.strftime("%Y%m%d")))
    if code == 200:
        data = parse_finra(body)
        return ("ok" if data else "empty"), data
    return ("missing" if code in (403, 404) else f"error {code or body}"), {}


def load_universe(path: str | None) -> tuple[dict[str, tuple[str, str]], str | None]:
    """symbol -> (tier, adv_rank) and built_at from a live universe.csv; missing file -> ({}, None)."""
    if not path or not Path(path).exists():
        return {}, None
    uni, built = {}, None
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            uni[r["symbol"]] = (r.get("tier", ""), r.get("adv_rank", ""))
            built = built or r.get("built_at")
    return uni, built


def build_rows(flags: dict, finra: dict, uni: dict) -> list[dict]:
    rows = []
    for sym in sorted(flags):
        r = dict(flags[sym])
        tier, rank = uni.get(sym, ("", ""))
        r.update(in_universe=_b(sym in uni), tier=tier, adv_rank=rank)
        r.update(finra.get(sym) or {"short_volume": "", "short_exempt_volume": "", "total_volume": "", "finra_market": ""})
        rows.append(r)
    return rows


def write_gz_csv(path: Path, rows: list[dict]) -> int:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0, compresslevel=9) as gz:
        gz.write(buf.getvalue().encode())
    return path.stat().st_size


def in_window(now_et: datetime, window=WINDOW) -> bool:
    hm = now_et.strftime("%H:%M")
    return now_et.weekday() < 5 and window[0] <= hm < window[1]


def record(state_dir: str, universe: str | None = None, day: date | None = None, force: bool = False,
           now: datetime | None = None, get=alpaca_get, fetch=http_text, check_window: bool = True) -> dict:
    """One morning's record. Returns the index line (or a skip reason). Raises when the asset list cannot be read."""
    t0 = time.monotonic()
    now = (now or datetime.now(timezone.utc)).astimezone(NY)
    day = day or now.date()
    if check_window and not force and not in_window(now):
        return {"skipped": f"outside {WINDOW[0]}-{WINDOW[1]} ET weekdays ({now:%a %H:%M} ET)"}
    out = Path(state_dir) / "borrow" / f"{day.isoformat()}.csv.gz"
    if out.exists() and not force:
        return {"skipped": f"{out.name} already recorded"}
    is_open, prior = sessions(day, get)
    if is_open is False and not force:
        return {"skipped": f"{day} is not a market day"}
    flags = candidate_flags(get("/assets", {"status": "active", "asset_class": "us_equity"}) or [])
    if not flags:
        raise RuntimeError("empty asset list")
    finra_status, finra = fetch_finra(prior, fetch)
    uni, built = load_universe(universe)
    rows = build_rows(flags, finra, uni)
    size = write_gz_csv(out, rows)
    line = {"day": day.isoformat(), "fetched_at_et": now.strftime("%Y-%m-%d %H:%M:%S"), "rows": len(rows),
            "shortable": sum(r["shortable"] == "1" for r in rows), "easy_to_borrow": sum(r["easy_to_borrow"] == "1" for r in rows),
            "universe_rows": sum(r["in_universe"] == "1" for r in rows), "universe_built_at": built,
            "finra_date": prior.isoformat(), "finra_status": finra_status, "finra_rows": len(finra),
            "finra_matched": sum(r["total_volume"] != "" for r in rows), "bytes": size,
            "runtime_s": round(time.monotonic() - t0, 1), "calendar": "ok" if is_open is not None else "unreachable"}
    with open(out.parent / "index.jsonl", "a") as f:
        f.write(json.dumps(line) + "\n")
    readme = Path(state_dir) / "README.md"
    if not readme.exists() or "PRE1" not in readme.read_text():
        readme.write_text(README)
    return line


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="PRE1 borrow / short-volume recorder (read-only). Educational only.")
    ap.add_argument("--state-dir", default="state")
    ap.add_argument("--universe", default=None, help="live universe.csv (newest from mcf-data)")
    ap.add_argument("--day", default=None, help="YYYY-MM-DD (default: today ET)")
    ap.add_argument("--force", action="store_true", help="ignore the ET window / existing file / holiday check")
    ap.add_argument("--ignore-window", action="store_true", help="the caller (the workflow) already checked the ET window")
    a = ap.parse_args(argv)
    res = record(a.state_dir, a.universe, date.fromisoformat(a.day) if a.day else None, a.force,
                 check_window=not a.ignore_window)
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
