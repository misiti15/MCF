"""FWDREP: forward-replay rep ledger (research only; no config / setup / assignment / ledger change).

A forward rep = a trade simulated by the as-live replay engine (mcf.report.team -> mcf.replay.harness.run_session, the
real PaperRunner loop, fills=costs, limit_fill=through, spread pool from the live journals) on a real session that came
AFTER the setup's rule was frozen (first snapshot of its current `strategies:` block on any account's data branch, and
for GEN ids not before the id date), with the rule unchanged since. Out-of-sample sessions, not backtests: no tuning on them.

Each session, per home account, the setups of that account run in ISOLATED pooled books (one runner per account x side)
under that account's own rules (current config/account_<acc>.yaml + that session's frozen live/shorts/exits sections
when the account published them), on the full Primary universe of the session (mcf-data universe.csv minus the PTP
denylist and the live earnings blackout; Testing A's top-500 pool is NOT applied). Isolation = every cross-setup
interaction switched off so a pooled book equals running each setup alone: unlimited lots per symbol, no twin block, no
concurrent-position / trade-count cap, no account -R halt (the per-setup -2R latch and per-setup position cap stay, they
are per setup). One book per account: the simulated broker nets one position per symbol, so the one interaction left
is "opposite side held" (a long setup and a short setup of the same account on the same symbol at the same time); those
blocked signals are counted per setup (FWDREP_SPLIT_SIDES=1 runs longs / shorts in separate books instead, 2x runtime).

    python research/fwdrep/run.py --date 2026-11-10                 # one session, every account (cached inputs only)
    python research/fwdrep/run.py --date 2026-11-10 --fetch         # may fetch bars / priors (read-only market data; after 16:05 ET)
    python research/fwdrep/run.py --dates 2026-10-23..2026-11-10 --accounts gen --jobs 4
    python research/fwdrep/run.py --date 2026-11-11 --fetch --then-report   # nightly: replay + rebuild the ledger

Outputs: research/fwdrep/trades/<date>.csv (every forward-replay trade of the session; rewritten for that date) and
data/fwdrep/<date>/<acc>-<side>.json partials (git-ignored, resume). Paper simulation. Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import pickle
import re
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = Path("/home/user/MCF")   # FWDCAL vendor copy: the only change (was HERE.parents[1])
sys.path.insert(0, str(ROOT))
NY = "America/New_York"
DATA = Path(os.environ.get("FWDREP_DATA", ROOT / "data"))          # shared caches: data/team (bars, priors), data/replay
PART = DATA / "fwdrep"
TEAM_CACHE = Path(os.environ.get("MCF_TEAM_CACHE", DATA / "team"))
os.environ.setdefault("MCF_TEAM_CACHE", str(TEAM_CACHE))
os.environ.setdefault("MCF_REPLAY_STORE", str(DATA / "replay"))
TRADES = HERE / "trades"
ACC_ORDER = ["primary", "testing", "testing2", "explore1", "livelab", "graveyard", "gen"]
BRANCH = {"primary": "mcf-data", "testing": "mcf-data-testing", "testing2": "mcf-data-testing2", "gen": "mcf-data-gen",
          "graveyard": "mcf-data-graveyard", "explore1": "mcf-data-explore1", "livelab": "mcf-data-livelab"}
TAG = {"primary": "Primary", "testing": "On Deck", "testing2": "Testing A", "explore1": "Testing B", "livelab": "Testing C",
       "graveyard": "Graveyard", "gen": "Generator"}
NOHASH = ("enabled", "tags", "note", "notes", "comment")
BIG = 10 ** 6
SPLIT_SIDES = os.environ.get("FWDREP_SPLIT_SIDES") == "1"   # default: one book per account (runtime); see NOTES


def git(*a, text=True):
    r = subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=text)
    return r.stdout if r.returncode == 0 else None


def bjson(branch, path):
    raw = git("show", f"origin/{branch}:{path}")
    try:
        return json.loads(raw) if raw else None
    except ValueError:
        return None


def block_hash(blk: dict) -> str:
    core = {k: v for k, v in blk.items() if k not in NOHASH}
    return hashlib.md5(json.dumps(core, sort_keys=True, default=str).encode()).hexdigest()[:10]


# ------------------------------------------------------------------------------------------------------------ inventory
def snapshots(asof: str) -> pd.DataFrame:
    """Every (setup, account, date, enabled, hash) in the accounts' frozen setups/<date>.json up to `asof`."""
    rows = []
    for acc, br in BRANCH.items():
        for p in (git("ls-tree", "--name-only", f"origin/{br}", "setups/") or "").split():
            d = Path(p).stem[:10]
            if len(d) != 10 or d > asof:
                continue
            j = bjson(br, p) or {}
            for sid, blk in (j.get("strategies") or {}).items():
                rows.append((sid, acc, d, bool(blk.get("enabled", True)), block_hash(blk)))
    return pd.DataFrame(rows, columns=["setup", "acc", "date", "enabled", "hash"])


def side_of(sid: str, live_sides: dict) -> str:
    s = sid.lower()
    if re.search(r"(^|-)short($|-)", s) or s.endswith("short") or "_short" in s:
        return "short"
    if re.search(r"(^|-)long($|-)", s) or s.endswith("long") or "_long" in s:
        return "long"
    return live_sides.get(sid, "both")


def inventory(asof: str, live_sides: dict | None = None) -> pd.DataFrame:
    """Setups enabled in some account on the newest snapshot <= asof: home account, current block hash, freeze date
    (first session from which the block has been unchanged on every account), side, group."""
    S = snapshots(asof)
    last = S[S.date == S.groupby("acc").date.transform("max")]
    on = last[last.enabled]
    out = []
    for sid, g in on.groupby("setup"):
        accs = sorted(g.acc, key=ACC_ORDER.index)
        home = accs[0]
        h = g[g.acc == home].hash.iloc[0]
        hist = S[S.setup == sid].sort_values("date")
        diff = hist[hist.hash != h]
        later = hist[(hist.hash == h) & (hist.date > (diff.date.max() if len(diff) else ""))]
        freeze = later.date.min()
        m = re.match(r"GEN-26(\d\d)(\d\d)-", sid)
        if m:
            freeze = max(freeze, f"2026-{m.group(1)}-{m.group(2)}")
        m = re.match(r"GEN-POD(\d\d)(\d\d)-", sid)
        if m:
            freeze = max(freeze, f"2026-{m.group(1)}-{m.group(2)}")
        out.append(dict(setup=sid, home=home, home_tag=TAG[home], also=",".join(a for a in accs[1:]), hash=h,
                        freeze=freeze, changed_before=(diff.date.max() if len(diff) else ""),
                        side=side_of(sid, live_sides or {}), gen=sid.startswith("GEN-")))
    return pd.DataFrame(out).sort_values(["home", "setup"]).reset_index(drop=True)


def live_sides() -> dict:
    """setup -> long / short / both from the live paper journals (run 1) of every account."""
    import sqlite3
    import tempfile

    sides: dict[str, set] = {}
    for br in BRANCH.values():
        raw = git("show", f"origin/{br}:journal.db", text=False)
        if not raw:
            continue
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.write(raw)
        try:
            c = sqlite3.connect(f.name)
            for st, sd in c.execute("select distinct strategy, side from signals where run_id=1"):
                sides.setdefault(st, set()).add(int(sd))
            c.close()
        finally:
            os.unlink(f.name)
    return {k: ("long" if v == {1} else "short" if v == {-1} else "both") for k, v in sides.items()}


# ------------------------------------------------------------------------------------------------------------ config
def account_cfg(acc: str, day: str, ids: list[str], blocks: dict) -> dict:
    """The home account's own rules (current config + that session's frozen live/shorts/exits when published), only
    `ids` enabled with their current blocks, full Primary universe, every cross-setup interaction off (isolation)."""
    from mcf.config import load_config

    old = os.environ.get("MCF_ACCOUNT")
    os.environ["MCF_ACCOUNT"] = acc
    try:
        cfg = load_config()
    finally:
        if old is None:
            os.environ.pop("MCF_ACCOUNT", None)
        else:
            os.environ["MCF_ACCOUNT"] = old
    snap = bjson(BRANCH[acc], f"setups/{day}.json") or {}
    for k in ("live", "shorts", "exits"):
        if isinstance(snap.get(k), dict):
            cfg[k] = {**(cfg.get(k) or {}), **snap[k]}
    order = [x for x in ((cfg.get("live") or {}).get("setup_order") or []) if x in ids]
    order += [x for x in ids if x not in order]
    cfg["strategies"] = {i: {**blocks[i], "enabled": True} for i in ids}
    live = cfg.setdefault("live", {})
    live.update(setup_order=order, max_lots_per_symbol=BIG, block_twin_same_symbol=False, scale_out_max_per_day=BIG)
    a = cfg["account"]
    a.update(max_concurrent_positions=BIG, max_daily_loss_r=BIG, max_trades_per_day=BIG)
    a.setdefault("slots", 77)                       # slot_notional keeps the account's own per-trade notional cap
    uni = cfg.setdefault("universe", {})
    uni.pop("top_n", None)                          # full Primary universe (Testing A's UNI1 top-500 pool not applied)
    uni.pop("top_n_min_adv", None)
    cfg["account_name"] = f"fwdrep-{acc}"
    return cfg


# ------------------------------------------------------------------------------------------------------------ inputs
def cached_inputs(day: str, fetch: bool, log=print):
    """(universe frame, symbols, notes, priors, bars) from data/team caches; fetches only with fetch=True."""
    from mcf.report import team as T

    cfg0 = account_cfg("primary", day, [], {})
    uni, unote = T.primary_universe(day)
    syms, notes = T.team_symbols(cfg0, uni, day)
    pp = TEAM_CACHE / "priors" / f"{day}.pkl.gz"
    bp = TEAM_CACHE / "1Min" / f"{day}.parquet"
    if fetch:
        throttle()
        pri = T.get_priors(syms, day, [], log=log)
        bars = T.get_bars(syms, day, None, log=log)
    else:
        if not (pp.exists() and bp.exists()):
            raise FileNotFoundError(f"no cached bars/priors for {day} (run with --fetch after 16:05 ET)")
        with gzip.open(pp, "rb") as f:
            pri = {k: v for k, v in pickle.load(f).items() if k != "_asked"}
        x = pd.read_parquet(bp)
        ts = pd.DatetimeIndex(x["ts"]).tz_convert(NY)
        x = x.drop(columns="ts").set_index(ts)
        bars = {str(s): g[["open", "high", "low", "close", "volume"]].astype(float) for s, g in x.groupby("symbol", observed=True)}
    missing = len(set(syms) - set(pri))
    notes["priors_missing"] = missing
    shortable = {str(s): (bool(a), bool(b)) for s, a, b in zip(uni.symbol, uni.shortable, uni.easy_to_borrow)}
    return uni, unote, syms, notes, pri, bars, shortable


def throttle(gap: float = float(os.environ.get("FWDREP_FETCH_GAP_S", "0.4"))) -> None:
    """Polite read-only market-data fetches: at most one request every `gap` seconds (~150/min, under Alpaca's 200/min),
    on top of the store's own 429 back-off. The live trading keys share the limit, so fetch only after 16:05 ET."""
    import requests

    if getattr(requests.Session, "_fwdrep_throttled", False):
        return
    orig = requests.Session.get
    last = [0.0]

    def get(self, *a, **k):
        w = last[0] + gap - time.time()
        if w > 0:
            time.sleep(w)
        last[0] = time.time()
        return orig(self, *a, **k)

    requests.Session.get = get
    requests.Session._fwdrep_throttled = True


_CTX: dict = {}


def load_day(day: str, fetch: bool = False, log=print) -> None:
    """Point _CTX at `day`'s inputs (a worker switching sessions reloads; ~30-60 s from the caches)."""
    from mcf.report import team as T

    if _CTX.get("day") == day:
        return
    uni, unote, syms, notes, pri, bars, shortable = cached_inputs(day, fetch, log=log)
    _CTX.update(day=day, syms=syms, priors=pri, bars=bars, shortable=shortable, spreads=T.get_spreads(),
                unote=unote, notes=notes)


def book_path(job) -> Path:
    day, acc, side, ids = job
    key = hashlib.md5(json.dumps(sorted(ids)).encode()).hexdigest()[:8]
    return PART / day / f"{acc}-{side}-{key}.json"


def run_book(job):
    """One isolated pooled book: (day, acc, side, ids). Cached in data/fwdrep/<day>/<acc>-<side>-<hash>.json."""
    from mcf.report import team as T
    from mcf.report.playing_time import classify

    day, acc, side, ids = job
    f = book_path(job)
    if f.exists():
        return json.loads(f.read_text())
    load_day(day, _CTX.get("fetch", False), log=lambda *a: None)
    t0 = time.time()
    cfg = account_cfg(acc, day, ids, _CTX["blocks"])
    from mcf.backtest.engine import pinned_symbols

    ss = set(_CTX["syms"]) | pinned_symbols(cfg)
    sim = T.simulate(cfg, day, {s: b for s, b in _CTX["bars"].items() if s in ss},
                     {s: p for s, p in _CTX["priors"].items() if s in ss}, None, _CTX["shortable"], _CTX["spreads"],
                     log=lambda *a: None)
    sig = sim["signals"]
    sk: dict = {}
    if hasattr(sig, "groupby") and len(sig) and "status" in sig:
        for st, status, reason in zip(sig.strategy, sig.status, sig.get("reason", [None] * len(sig))):
            b = classify(status, reason)
            sk.setdefault(str(st), {}).setdefault(b, 0)
            sk[str(st)][b] += 1
            if str(reason) == "opposite side held":     # the one cross-setup interaction a pooled book keeps
                sk[str(st)]["opposite_side_held"] = sk[str(st)].get("opposite_side_held", 0) + 1
    rep = {"day": day, "acc": acc, "side": side, "setups": ids, "trades": sim["trades"], "signals": sk,
           "seconds": round(time.time() - t0, 1), "universe": _CTX.get("unote"),
           "notes": {k: str(v) for k, v in (_CTX.get("notes") or {}).items()}}
    f.parent.mkdir(parents=True, exist_ok=True)
    f.with_suffix(".tmp").write_text(json.dumps(rep, default=str))
    f.with_suffix(".tmp").replace(f)
    print(f"fwdrep book {day} {acc}/{side}: {len(ids)} setups, {len(sim['trades'])} trades, {rep['seconds']} s", flush=True)
    return rep


def trading_days(a: str, b: str) -> list[str]:
    """Sessions with a Primary universe.csv / snapshot published (the live system ran), a..b inclusive."""
    names = (git("ls-tree", "--name-only", "origin/mcf-data", "setups/") or "").split()
    ds = sorted(Path(p).stem[:10] for p in names)
    out = [d for d in ds if a <= d <= b]
    if b not in out and pd.Timestamp(b).dayofweek < 5:
        out.append(b)                               # today, before its snapshot is listed
    return sorted(set(out))


def books_for(day: str, inv: pd.DataFrame, accounts) -> list[tuple]:
    elig = inv[(inv.freeze <= day) & inv.home.isin(accounts) & inv.setup.isin(_CTX["blocks"])]
    jl = []
    for acc, g in elig.groupby("home"):
        if SPLIT_SIDES:
            for side, h in g.groupby("side"):
                jl.append((day, acc, side, sorted(h.setup)))
        else:   # one book per account: the only cross-setup block left is "opposite side held" (counted per setup)
            jl.append((day, acc, "all", sorted(g.setup)))
    return jl


def finalize_day(day: str, inv: pd.DataFrame) -> pd.DataFrame | None:
    """research/fwdrep/trades/<day>.csv + .meta.json from every finished book of the current inventory (all accounts)."""
    res = [json.loads(book_path(j).read_text()) for j in books_for(day, inv, ACC_ORDER) if book_path(j).exists()]
    if not res:
        return None
    rows = [{"date": day, "setup": t["strategy"], "home": r["acc"], **{k: t[k] for k in (
        "symbol", "side", "entry_time", "entry", "stop", "exit", "exit_time", "exit_reason", "shares", "pnl", "r")}}
        for r in res for t in r["trades"]]
    df = pd.DataFrame(rows, columns=["date", "setup", "home", "symbol", "side", "entry_time", "entry", "stop", "exit",
                                     "exit_time", "exit_reason", "shares", "pnl", "r"])
    TRADES.mkdir(parents=True, exist_ok=True)
    sig = [{"date": day, "setup": s, "home": r["acc"], **c} for r in res for s, c in r["signals"].items()]
    meta = {"date": day, "asof_inventory": inv.attrs.get("asof"),
            "books": [{"acc": r["acc"], "side": r["side"], "seconds": r["seconds"], "n_setups": len(r["setups"])} for r in res],
            "setups": sorted(s for r in res for s in r["setups"]), "universe": res[0].get("universe"),
            "notes": res[0].get("notes"), "signals": sig,
            "label": "FORWARD REPLAY (simulated, as-live engine) - not live; never mixed with live records"}
    df.to_csv(TRADES / f"{day}.csv", index=False, float_format="%.6g")
    (TRADES / f"{day}.meta.json").write_text(json.dumps(meta, default=str))
    return df


def inv_asof(inv) -> str:
    return inv.attrs.get("asof")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date")
    ap.add_argument("--dates", help="A..B inclusive")
    ap.add_argument("--asof", help="inventory date: setups enabled on the newest snapshot <= this (default: the newest "
                    "Primary snapshot before the last date replayed, i.e. the rules in force going into it)")
    ap.add_argument("--accounts", default=",".join(ACC_ORDER))
    ap.add_argument("--jobs", type=int, default=int(os.environ.get("FWDREP_JOBS", "3")))
    ap.add_argument("--fetch", action="store_true", help="allow read-only market-data fetches (after 16:05 ET only)")
    ap.add_argument("--then-report", action="store_true")
    ap.add_argument("--force-fetch", action="store_true", help="allow --fetch during 09:25-16:05 ET (not recommended)")
    a = ap.parse_args(argv)
    now = pd.Timestamp.now(tz=NY)
    if a.fetch and not a.force_fetch and now.dayofweek < 5 and "09:25" <= now.strftime("%H:%M") < "16:05":
        sys.exit("fwdrep: --fetch refused during market hours (the live keys share the data rate limit); "
                 "run without --fetch (cached sessions only) or after 16:05 ET")
    git("fetch", "-q", "origin", *BRANCH.values())
    days = [a.date] if a.date else trading_days(*a.dates.split(".."))
    if not a.asof:
        snaps = sorted(Path(p).stem[:10] for p in (git("ls-tree", "--name-only", "origin/mcf-data", "setups/") or "").split())
        a.asof = max(x for x in snaps if x <= days[-1])
    invp = HERE / "inventory.csv"
    if invp.exists() and pd.read_csv(invp).get("asof", pd.Series([None])).iloc[0] == a.asof:
        inv = pd.read_csv(invp, keep_default_na=False)
    else:
        inv = inventory(a.asof, live_sides())
        inv["asof"] = a.asof
        inv.to_csv(invp, index=False)
    inv.attrs["asof"] = a.asof
    from mcf.report import team as T  # noqa: F401

    blocks = {}
    home = dict(zip(inv.setup, inv.home))
    for acc in ACC_ORDER:
        snap = bjson(BRANCH[acc], f"setups/{a.asof}.json") or {}
        for sid, blk in (snap.get("strategies") or {}).items():
            if home.get(sid) == acc:
                blocks[sid] = dict(blk)
    _CTX.update(blocks=blocks, fetch=a.fetch)
    accounts = a.accounts.split(",")
    ok_days = []
    for d in days:                                  # inputs first (a fetch happens here, in the parent, once per day)
        try:
            if a.fetch:
                load_day(d, True)
            elif not ((TEAM_CACHE / "priors" / f"{d}.pkl.gz").exists() and (TEAM_CACHE / "1Min" / f"{d}.parquet").exists()):
                raise FileNotFoundError(f"no cached bars/priors for {d} (run with --fetch after 16:05 ET)")
            ok_days.append(d)
        except FileNotFoundError as e:
            print(f"fwdrep {d}: SKIPPED - {e}", flush=True)
    jl = [j for d in ok_days for j in books_for(d, inv, accounts)]
    pri = {acc: i for i, acc in enumerate(["gen", "testing", "testing2", "explore1", "livelab", "primary", "graveyard"])}
    jl.sort(key=lambda j: (pri.get(j[1], 9), j[0]))   # Gen first (priority), then On Deck, Testing A/B/C, Primary, Graveyard
    todo = [j for j in jl if not book_path(j).exists()]
    print(f"fwdrep: {len(ok_days)} sessions, {len(jl)} books ({len(todo)} to run), jobs={a.jobs}", flush=True)
    t0 = time.time()
    if a.jobs > 1 and len(todo) > 1:
        import multiprocessing as mp

        with mp.get_context("fork").Pool(min(a.jobs, len(todo)), maxtasksperchild=4) as pool:
            for r in pool.imap_unordered(run_book, todo, chunksize=1):
                finalize_day(r["day"], inv)
    else:
        for j in todo:
            run_book(j)
            finalize_day(j[0], inv)
    for d in ok_days:
        finalize_day(d, inv)
    print(f"fwdrep: done in {time.time() - t0:.0f} s", flush=True)
    if a.then_report:
        subprocess.run([sys.executable, str(HERE / "report.py")], check=False)


if __name__ == "__main__":
    main()
