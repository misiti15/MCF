"""Live-session bar storage (owner "storage yes", 2026-11-16): one Parquet pack per session for the FULL live universe.

    python -m mcf.replay.packs build --start 2026-10-06 --end 2026-11-16 --out packs_out
    python -m mcf.replay.packs build --start 2025-03 --end 2025-03 --out packs_out     # 2-year history, one month
    python -m mcf.replay.packs capacity --manifest packs_out/manifest.jsonl --releases releases.json \
        --out docs/live/storage.json

`build` reads read-only Alpaca SIP market data (split-adjusted, as the live code reads it; keys from ALPACA_API_KEY /
ALPACA_SECRET_KEY, never logged) for every symbol of the live universe.csv the live prep used that day (latest version
committed on or before the session on the data branch), plus the lab list. For the "2-year history" tier (before the
first live session) the universe is rebuilt POINT-IN-TIME per session with the live universe filters of
mcf/data/universe.py (price >= $5, 20-session ADV >= the extended floor, >= 15 days, ATR >= 1% of price) over every
Alpaca US-equity asset on a major exchange, ACTIVE AND INACTIVE (delisted / merged names whose bars exist), so the
history is not limited to names that survived to today (survivorship). It writes
    1min-<day>.parquet   RTH 1-minute bars (symbol, ts UTC, OHLCV), zstd; schema metadata mcf_pack {universe, ...}
    1day-<day>.parquet   daily bars of the same symbols for the ~80 calendar days up to and including the session
The store-bars workflow uploads both to the GitHub Release bars-<YYYY-MM> (mcf/replay/store.py reads them back).
Two tiers (meta "tier" / "weight"): live sessions (2026-10-06 on, weight 1.0) and the 2-year history
2024-09-16..2026-10-05 (owner "2-year .175 yes" 2026-11-16: weight 0.175, screening / experience only).
`capacity` writes the storage capacity file. The locked block 2024-11-01..2025-02-28 is never fetched or stored.
Research/ops infrastructure only: no trading endpoint, no setup or exit logic. Educational only - not financial advice.
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from ..config import ROOT
from ..data.bars import TZ
from . import store

DAILY_DAYS = store.LOOKBACK_DAYS + 30
ASSET_LIMIT_MB = 2048            # GitHub Release asset limit: 2 GB per file
HIST_START = date(2024, 9, 16)   # 2-year history packs start here (owner 2026-11-16)
HIST_WEIGHT = 0.175              # 2-year sessions: screening / experience weight (owner "2-year .175 yes")


TIER_NAMES = {"live": "Live session", "2y": "2-year history"}     # docs/GLOSSARY.md


def tier(d) -> tuple[str, float]:
    return ("live", 1.0) if store._d(d) >= store.PACK_START else ("2y", HIST_WEIGHT)


def day_universe(d, branch: str = "origin/mcf-data") -> tuple[list[str], list[str], str]:
    """(symbols to store, the live universe list, source note) for session d."""
    d = store._d(d)
    uni, src = None, None
    r = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%H %ad", "--date=short", branch, "--", "universe.csv"],
                       capture_output=True, text=True)
    lines = r.stdout.splitlines()
    for i, line in enumerate(lines):
        sha, day = line.split()
        if store._d(day) <= d or i == len(lines) - 1:      # history before the first live copy: the earliest copy
            csv = subprocess.run(["git", "-C", str(ROOT), "show", f"{sha}:universe.csv"], capture_output=True,
                                 text=True).stdout
            try:
                u = pd.read_csv(io.StringIO(csv))
                uni = sorted(set(u["symbol"].astype(str)))
                src = f"{branch}:universe.csv @ {sha[:9]} ({day}, built {str(u['built_at'].iloc[0])[:10]})"
                if store._d(day) > d:
                    src += " - earliest live copy (survivorship: names gone before it are missing)"
            except Exception:
                uni = None
            break
    if not uni:
        f = ROOT / "data" / "universe.csv"
        if f.exists():
            uni = sorted(set(pd.read_csv(f)["symbol"].astype(str)))
            src = "data/universe.csv (current; no dated live copy on the data branch)"
    uni = uni or []
    lab = store.symbols() if store.SYMBOLS_FILE.exists() else []
    return sorted(set(uni) | set(lab)), uni, src or "lab symbols only"


def candidate_assets(log=print) -> pd.DataFrame:
    """Every Alpaca US-equity asset on a major exchange, active and inactive (symbol, status), PTPs and '.'/'/'
    symbols dropped as the live universe does. Read-only GET of the /v2/assets reference list (no order endpoint)."""
    import os

    import requests

    from ..data.universe import EXCHANGES, is_ptp

    h = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
    rows = []
    for status in ("active", "inactive"):
        r = requests.get("https://paper-api.alpaca.markets/v2/assets", headers=h, timeout=120,
                         params={"status": status, "asset_class": "us_equity"})
        r.raise_for_status()
        for a in r.json():
            sym, ex = str(a.get("symbol", "")), str(a.get("exchange", ""))
            if ex not in EXCHANGES or "." in sym or "/" in sym or not sym:
                continue
            if status == "active" and not a.get("tradable"):
                continue
            if is_ptp(a.get("attributes"), sym):
                continue
            rows.append((sym, status))
    df = pd.DataFrame(rows, columns=["symbol", "status"]).drop_duplicates("symbol", keep="first")
    log(f"packs: candidates {int((df.status == 'active').sum())} active + {int((df.status == 'inactive').sum())} inactive")
    return df


def pit_universe(daily: pd.DataFrame, d, min_price: float = 5.0, floor: float = 1e6, min_atr_pct: float = 1.0,
                 min_days: int = 15) -> tuple[list[str], str]:
    """Point-in-time universe of session d from daily bars strictly before d (the live filters of
    mcf/data/universe.py on the last 20 sessions). When the locked block truncates the look-back (early March 2025:
    fewer than `min_days` post-block sessions before d), the first 20 post-block sessions are used instead (noted)."""
    d = store._d(d)
    t = pd.DatetimeIndex(daily["ts"]).tz_convert(TZ).date
    x = daily.assign(day=t)
    note = "point-in-time (last 20 sessions before the session)"
    prior = x[x.day < d]
    post = sorted(set(x.day[x.day > store.LOCK_B]))
    if d > store.LOCK_B and len([q for q in post if q < d]) < min_days:
        prior = x[x.day.isin(post[:20])]
        note = f"point-in-time from the first 20 post-block sessions {post[0]}..{post[min(19, len(post) - 1)]} " \
               "(locked block truncates the look-back)"
    prior = prior.sort_values(["symbol", "day"])
    keep = []
    for sym, g in prior.groupby("symbol", sort=False):
        g = g.tail(20)
        if len(g) < min_days:
            continue
        pc = g["close"].shift()
        tr = pd.concat([g["high"] - g["low"], (g["high"] - pc).abs(), (g["low"] - pc).abs()], axis=1).max(axis=1)
        price = float(g["close"].iloc[-1])
        if price >= min_price and float((g["close"] * g["volume"]).mean()) >= floor and \
                float(tr.tail(14).mean()) / price * 100 >= min_atr_pct:
            keep.append(str(sym))
    return sorted(keep), note


_HIST: dict = {}


def hist_month_daily(d, log=print) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(candidate assets, daily bars of all candidates for the session's month and its ~80-day look-back, never the
    locked block). Cached per month in-process."""
    d = store._d(d)
    key = f"{d:%Y-%m}"
    if key not in _HIST:
        _HIST.clear()
        cand = candidate_assets(log=log)
        first = d.replace(day=1)
        last = (pd.Timestamp(first) + pd.offsets.MonthEnd(0)).date()
        lo = first - timedelta(days=DAILY_DAYS)
        if first > store.LOCK_B:
            lo = max(lo, store.LOCK_B + timedelta(days=1))
        hi = min(last, store.LOCK_A - timedelta(days=1)) if last < store.LOCK_A else last
        dl = fetch_safe(cand["symbol"].tolist(), f"{lo}T00:00:00Z", f"{hi + timedelta(days=1)}T00:00:00Z", "1Day",
                        batch=200, log=log)
        _HIST[key] = (cand, dl)
        log(f"packs: {key} daily bars {dl['symbol'].nunique()} symbols {len(dl)} rows")
    return _HIST[key]


def fetch_safe(syms: list[str], start: str, end: str, timeframe: str, batch: int = 100, log=print) -> pd.DataFrame:
    """store._fetch_bars per batch; a batch the API rejects (e.g. one malformed symbol) is split until the bad name is
    isolated and skipped."""
    import requests

    parts = []

    def go(chunk):
        try:
            parts.append(store._fetch_bars(chunk, start, end, timeframe, batch=len(chunk)))
        except requests.HTTPError as e:
            if len(chunk) == 1:
                log(f"packs: skipped {chunk[0]} ({e.response.status_code if e.response is not None else 'error'})")
                return
            h = len(chunk) // 2
            go(chunk[:h])
            go(chunk[h:])

    for i in range(0, len(syms), batch):
        go(syms[i:i + batch])
    parts = [p for p in parts if len(p)]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=store.PACK_COLS)


def build_session(d, out: Path, branch: str = "origin/mcf-data", log=print) -> dict | None:
    """Fetch and write the two packs of session d into `out`. None when the market was closed (no bars)."""
    d = store._d(d)          # (not check_dates: a pack only stores the session's own bars and post-block daily bars)
    if store.LOCK_A <= d <= store.LOCK_B:
        raise ValueError(f"{d} is in the locked block (rule 19)")
    tr, w = tier(d)
    extra = {}
    t0 = pd.Timestamp.now()
    if tr == "2y":
        cand, mdl = hist_month_daily(d, log=log)
        uni, src = pit_universe(mdl, d)
        inactive = sorted(set(uni) & set(cand.loc[cand.status == "inactive", "symbol"]))
        lab = store.symbols() if store.SYMBOLS_FILE.exists() else []
        syms = sorted(set(uni) | set(lab))
        extra = {"inactive_now": inactive, "candidates": len(cand)}
    else:
        syms, uni, src = day_universe(d, branch)
    m = fetch_safe(syms, f"{d}T13:00:00Z", f"{d}T21:00:00Z", "1Min", log=log)
    if m.empty:
        log(f"packs: {d} no bars (market closed?)")
        return None
    t = pd.DatetimeIndex(m["ts"]).tz_convert(TZ)
    m = m[(t.date == d) & (t.time >= pd.Timestamp("09:30").time()) & (t.time < pd.Timestamp("16:00").time())]
    lo = d - timedelta(days=DAILY_DAYS)
    if d > store.LOCK_B:
        lo = max(lo, store.LOCK_B + timedelta(days=1))
    if tr == "2y":   # slice of the month's candidate daily bars (no second fetch)
        dt = pd.DatetimeIndex(mdl["ts"]).tz_convert(TZ).date
        dl = mdl[mdl["symbol"].isin(set(syms)) & (dt >= lo) & (dt <= d)]
    else:
        dl = fetch_safe(syms, f"{lo}T00:00:00Z", f"{d + timedelta(days=1)}T00:00:00Z", "1Day", log=log)
    meta = {"session": str(d), "tier": tr, "tier_name": TIER_NAMES[tr], "weight": w, "universe_source": src, **extra, "universe": uni, "asked": len(syms), "feed": "sip",
            "adjustment": "split", "fetched_at": str(pd.Timestamp.now(tz=TZ))}
    out.mkdir(parents=True, exist_ok=True)
    p1 = store.write_pack(m, out / store.pack_name(d, "1min"), meta)
    p2 = store.write_pack(dl, out / store.pack_name(d, "1day"), {**meta, "universe": [], "from": str(lo)})
    row = {"session": str(d), "symbols": int(m["symbol"].nunique()), "asked": len(syms), "universe": len(uni),
           "rows_1min": len(m), "mb_1min": round(p1.stat().st_size / 1e6, 2), "mb_1day": round(p2.stat().st_size / 1e6, 2),
           "release": store.release_tag(d), "tier": tr, "weight": w, "universe_source": src,
           "inactive_now": len(extra.get("inactive_now", [])),
           "fetch_s": round((pd.Timestamp.now() - t0).total_seconds())}
    log(json.dumps(row))
    with open(out / "manifest.jsonl", "a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def capacity(rows: list[dict], releases: list[dict] | None, old: dict | None = None) -> dict:
    """The capacity file: per-session rows (newest wins), totals from the Release listing when given."""
    by = {r["session"]: r for r in (old or {}).get("sessions", [])}
    for r in rows:
        by[r["session"]] = {k: r[k] for k in ("session", "symbols", "universe", "rows_1min", "mb_1min", "mb_1day",
                                              "release", "tier", "weight", "inactive_now") if k in r}
    sess = [by[k] for k in sorted(by)]
    assets = [a for rel in (releases or []) if str(rel.get("tag_name", "")).startswith("bars-")
              for a in rel.get("assets", [])]
    if assets:
        total_mb = sum(a["size"] for a in assets) / 1e6
        biggest = max(a["size"] for a in assets) / 1e6
        on_release = sorted({a["name"][5:15] for a in assets if a["name"].startswith("1min-")})
    else:
        total_mb = sum(r.get("mb_1min", 0) + r.get("mb_1day", 0) for r in sess)
        biggest = max([r.get("mb_1min", 0) for r in sess] or [0])
        on_release = [r["session"] for r in sess]
    per = [r["mb_1min"] + r.get("mb_1day", 0) for r in sess if "mb_1min" in r]
    avg = sum(per) / len(per) if per else 0.0
    today = pd.Timestamp.now(tz=TZ).date()
    want = {"live": [d for d in store.sessions(store.PACK_START, today)],
            "2y": [d for d in store.sessions(HIST_START, store.PACK_START - timedelta(days=1))
                   if not (store.LOCK_A <= d <= store.LOCK_B)]}
    have = set(on_release)
    progress = {}
    for k, days in want.items():   # weekday counts (exchange holidays have no pack, so ~9 per year stay "missing")
        got = [d for d in days if str(d) in have]
        months = sorted({f"{d:%Y-%m}" for d in days})
        mine = [r for r in sess if r.get("tier", "live") == k]
        mb = [r["mb_1min"] + r.get("mb_1day", 0) for r in mine if "mb_1min" in r]
        progress[k] = {"name": TIER_NAMES[k], "weight": 1.0 if k == "live" else HIST_WEIGHT,
                       "weekdays": len(days), "stored": len(got),
                       "symbols_per_session": round(sum(r["symbols"] for r in mine) / len(mine)) if mine else None,
                       "inactive_now_per_session": round(sum(r.get("inactive_now", 0) for r in mine) / len(mine))
                       if mine and k == "2y" else None,
                       "mb_per_session": round(sum(mb) / len(mb), 1) if mb else None,
                       "months_done": [m for m in months if any(f"{d:%Y-%m}" == m and str(d) in have for d in days)],
                       "est_total_gb": round(len(days) * 0.96 * ((sum(mb) / len(mb)) if mb else avg) / 1e3, 1)}
    return {
        "generated": str(pd.Timestamp.now(tz=TZ).floor("s")),
        "what": "Live-session bar packs (RTH 1-minute SIP bars, full live universe + daily bars) on GitHub Releases "
                "bars-<YYYY-MM>, assets 1min-<day>.parquet / 1day-<day>.parquet (store-bars workflow)",
        "sessions_stored": len(on_release),
        "first": on_release[0] if on_release else None,
        "last": on_release[-1] if on_release else None,
        "symbols_per_session": round(sum(r["symbols"] for r in sess) / len(sess)) if sess else 0,
        "mb_per_session": round(avg, 1),
        "total_gb": round(total_mb / 1e3, 3),
        "largest_asset_mb": round(biggest, 1),
        "headroom": f"GitHub Release assets: 2 GB per file limit; largest asset {biggest:.0f} MB "
                    f"({100 * biggest / ASSET_LIMIT_MB:.1f}% of the limit). One release per month keeps each release "
                    f"to ~21 sessions (~{21 * avg / 1e3:.2f} GB/month at the current size); no total-size limit is "
                    f"documented for releases, ~{252 * avg / 1e3:.1f} GB/year.",
        "progress": progress,
        "locked_block": "2024-11-01..2025-02-28 never fetched or stored (rule 19)",
        "sessions": sess,
        "note": "Educational only - not financial advice.",
    }


def month_bounds(start: str, end: str) -> tuple[date, date]:
    """YYYY-MM-DD or YYYY-MM (a whole month) -> (first, last) day."""
    lo = pd.Timestamp(start + "-01" if len(start) == 7 else start).date()
    e = pd.Timestamp(end + "-01" if len(end) == 7 else end)
    hi = (e + pd.offsets.MonthEnd(0)).date() if len(end) == 7 else e.date()
    return lo, hi


def main(argv=None):
    ap = argparse.ArgumentParser(description="live-session bar packs")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--start", required=True)
    b.add_argument("--end", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--branch", default="origin/mcf-data")
    b.add_argument("--skip", default="", help="file listing sessions already on the release (one per line)")
    c = sub.add_parser("capacity")
    c.add_argument("--manifest", default=None)
    c.add_argument("--releases", default=None, help="JSON of GET /repos/{repo}/releases")
    c.add_argument("--out", default=str(ROOT / "docs" / "live" / "storage.json"))
    a = ap.parse_args(argv)
    if a.cmd == "build":
        lo, hi = month_bounds(a.start, a.end)
        days = [d for d in store.sessions(lo, min(hi, date.today())) if not (store.LOCK_A <= d <= store.LOCK_B)]
        if not days:
            raise SystemExit("no session outside the locked block 2024-11-01..2025-02-28 (rule 19)")
        skip = set(Path(a.skip).read_text().split()) if a.skip and Path(a.skip).exists() else set()
        for d in days:
            if str(d) in skip:
                print(f"packs: {d} already on the release")
                continue
            build_session(d, Path(a.out), a.branch)
    else:
        rows = [json.loads(x) for x in Path(a.manifest).read_text().splitlines() if x.strip()] \
            if a.manifest and Path(a.manifest).exists() else []
        rel = json.loads(Path(a.releases).read_text()) if a.releases and Path(a.releases).exists() else None
        if isinstance(rel, list) and rel and isinstance(rel[0], list):      # gh api --paginate --slurp
            rel = [x for page in rel for x in page]
        out = Path(a.out)
        old = json.loads(out.read_text()) if out.exists() else None
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(capacity(rows, rel, old), indent=1) + "\n")
        print(f"capacity: {out}")


if __name__ == "__main__":
    main()
