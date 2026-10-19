"""Extend the 2-year 1-minute SIP cache (data/cache_hist/1Min) through --end with the repo's own downloader
(research/history2y/download.py `fetch`, Alpaca market data, read-only GET; keys from env, never logged).

Fetches [--start, --end) into a scratch BarStore (the downloader's own format), then appends the new sessions to the
cache parquet. The fetch starts one session early (2026-10-07, already cached) as an overlap check: if the overlap
closes disagree by a median > 0.5% (a split/adjustment change inside the new window) the symbol is NOT extended and is
listed in research/tf1019/data/extend_report.json. Otherwise the overlap day is REPLACED by the fresh fetch (the
original download left 2026-10-07 with gaps) and 10-08.. are appended. New sessions 2026-10-08..2026-10-16 are forward/valid data (never train).

    python research/tf1019/data/extend_1min.py --scratch <dir> [--start 2026-10-07] [--end 2026-10-17] [--workers 4]
Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import download  # noqa: E402  (the repo's downloader)
from mcf.data.store import BarStore  # noqa: E402

CACHE = ROOT / "data" / "cache_hist"


def merge(sym: str, scratch: Path, overlap_day: str) -> tuple[str, str, int]:
    new_p = BarStore(scratch).path(sym)
    if not new_p.exists():
        return sym, "no_new_data", 0
    old_p = BarStore(CACHE).path(sym)
    if not old_p.exists():
        return sym, "no_cache", 0
    old, new = pd.read_parquet(old_p), pd.read_parquet(new_p)
    cut = pd.Timestamp(overlap_day, tz=old.index.tz)
    j = old.loc[old.index >= cut, ["close"]].join(new.loc[new.index < cut + pd.Timedelta(days=1), ["close"]],
                                                   rsuffix="_new", how="inner")
    if len(j):
        dev = float(((j["close_new"] / j["close"]) - 1).abs().median())
        if dev > 0.005:      # split / adjustment change inside the new window: do not splice
            return sym, f"overlap_mismatch median {dev:.4f}", 0
    # the overlap day is replaced by the fresh fetch (the 2026-10-08 download left 10-07 with gaps, e.g. SPY 357/390)
    keep = old[old.index < cut]
    add = new[new.index >= cut]
    if add.empty:
        return sym, "nothing_after_cache", 0
    out = pd.concat([keep, add.astype(old.dtypes.to_dict())])
    out = out[~out.index.duplicated(keep="last")].sort_index()
    tmp = old_p.with_suffix(".tmp")
    out.to_parquet(tmp)
    tmp.replace(old_p)
    return sym, "extended", len(add)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-10-07")
    ap.add_argument("--end", default="2026-10-17")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--symbols", default=str(ROOT / "research" / "lab_symbols.txt"))
    a = ap.parse_args()
    scratch = Path(a.scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    download.OUT = scratch                                   # fetch into scratch (fork inherits the module globals)
    download.STOP_UTC = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)   # done well before the 08:35 ET live job
    syms = Path(a.symbols).read_text().split()
    args = {"start": f"{a.start}T00:00:00Z", "end": f"{a.end}T00:00:00Z"}
    t0, res = time.time(), {}
    with Pool(a.workers, initializer=download._init, initargs=(args,)) as pool:
        for i, (sym, status, n) in enumerate(pool.imap_unordered(download.fetch, syms), 1):
            res[sym] = {"fetch": status, "bars": n}
            if i % 100 == 0:
                print(f"fetch {i}/{len(syms)} ({time.time() - t0:.0f}s)", flush=True)
    todo = [s for s in syms if res[s]["fetch"] in ("ok", "skip")]   # skip = fetched into scratch on an earlier run
    with Pool(a.workers) as pool:
        for sym, st, n in pool.starmap(merge, [(s, scratch, a.start) for s in todo]):
            res[sym].update(merge=st, added=n)
    for sym in syms:
        res[sym].setdefault("merge", "skipped")
        res[sym].setdefault("added", 0)
    summ = pd.Series([v["merge"].split(" ")[0] for v in res.values()]).value_counts().to_dict()
    rep = {"start": a.start, "end_exclusive": a.end, "symbols": len(syms), "merge_counts": summ,
           "not_extended": {k: v for k, v in res.items() if v["merge"] != "extended"}, "seconds": round(time.time() - t0)}
    (Path(__file__).parent / "extend_report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: rep[k] for k in ("symbols", "merge_counts", "seconds")}), flush=True)
