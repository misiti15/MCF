"""WT1 wide-target forward shadow (owner "WT yes" 2026-11-25). Rule frozen 2026-11-25 - see RULE.md.

    python research/forward/wide_target/shadow.py --date YYYY-MM-DD [--date ...]   # idempotent per date (after 16:15 ET)
    python research/forward/wide_target/shadow.py --score                          # running tally vs the pass bar

RESEARCH ONLY - journal-only, never changes trading: reads the account journals (git show origin/<data branch>:journal.db,
runs of kind whatif / shadow excluded) and read-only Alpaca 1-minute SIP bars (mcf.replay.store._fetch_bars: market-data
GET only, no trading endpoint; credentials come from the environment and are never written anywhere). No order, no
config, no runner input. For every closed live lot of RW3 / RW5 (Primary) or their copies it asks: with the take-profit
at 1.25x the live target distance (everything else identical), what would the lot have made? Writes forward.csv (one
row per lot, upsert by date) and days.csv (one row per session). Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
OUT, DAYS = HERE / "forward.csv", HERE / "days.csv"
GIT = os.environ.get("MCF_GIT_DIR", str(ROOT))           # repo whose origin/* data branches are read
TZ = "America/New_York"
FROZEN = "2026-11-25"
FORWARD_FROM = "2026-11-23"                               # C3 rule epoch; 11-12..11-20 = sanity backfill, never counted
LOCK_A, LOCK_B = "2024-11-01", "2025-02-28"

# ---- frozen rule (RULE.md section 1)
MULT = 1.25                                               # wide target = 1.25 x the live target distance
THR_BPS, THR_MIN = 3.0, 0.01                              # a limit fills only on a touch-through of max(1c, 3 bp)
FLAT_MIN = 385                                            # 15:55 flatten (minute index 0 = the 09:30 bar)
PARENTS = {"RW3-gapdn-rsi5pop-flowsell-short-FD": "RW3", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "RW5"}
SPY_EXIT = {"RW3-gapdn-rsi5pop-flowsell-short-FD-WB4": 0.30,     # copies with an SPY-since-entry exit (config, frozen)
            "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB4": 0.40}
BRANCHES = {"primary": "mcf-data", "testing": "mcf-data-testing", "testing2": "mcf-data-testing2",
            "explore1": "mcf-data-explore1", "livelab": "mcf-data-livelab", "testingd": "mcf-data-testingd",
            "testinge": "mcf-data-testinge", "testingf": "mcf-data-testingf", "gen": "mcf-data-gen",
            "graveyard": "mcf-data-graveyard"}

# ---- pass bar (RULE.md section 4)
MIN_SESSIONS, MIN_TRADES, T_BAR = 20, 60, 1.5
HARM_SESSIONS, HARM_T = 10, -2.0

COLS = ["date", "account", "setup", "family", "trade_id", "symbol", "side", "entry_et", "entry", "stop", "target",
        "wide_target", "shares", "live_exit_et", "live_exit", "live_reason", "wide_exit_et", "wide_exit", "wide_reason",
        "R_live", "R_parent", "R_wide", "dR", "bars_check", "dup", "status", "frozen"]
DCOLS = ["date", "lots", "lots_scored", "target_lots", "changed", "dR_sum", "R_parent_sum", "R_wide_sum", "status",
         "frozen"]


def family_of(setup: str) -> str | None:
    """RW3 / RW5 for the parent or any copy of it (name = parent + '-suffix'), else None."""
    for p, f in PARENTS.items():
        if setup == p or str(setup).startswith(p + "-"):
            return f
    return None


def wide_target(stop: float, target: float, side: int) -> float:
    """t1s1 is symmetric around the signal price, so the signal reference = (stop + target) / 2 and the live target
    distance = |target - ref|. Wide = ref + side x 1.25 x distance, rounded to the cent toward the entry (live rounding)."""
    ref = (stop + target) / 2.0
    w = ref + side * MULT * abs(target - ref)
    tick = 0.01 if w >= 1 else 1e-4
    return (math.floor(w / tick + 1e-9) if side > 0 else math.ceil(w / tick - 1e-9)) * tick


def thr(px: float) -> float:
    return max(THR_MIN, THR_BPS * 1e-4 * px)


def _minute(ts: pd.Timestamp) -> float:
    return ts.hour * 60 + ts.minute - 570 + ts.second / 60


def walk(bars: pd.DataFrame, side: int, stop: float, wide: float, start_min: float, spy: pd.DataFrame | None = None,
         spy_ref: float | None = None, spy_pct: float | None = None) -> tuple[float, str, int] | None:
    """Continue a lot whose live target filled in minute `start_min`, now aiming at `wide`. Per bar, from the fill bar:
    SPY-since-entry exit at the bar open (copies with spy_exit_pct; from the next bar), stop (fill bar: at the stop
    price; later bars: at the stop or the open if it gapped through), wide target (touch-through), 15:55 flatten at
    the open. A stop is taken before a target inside the same bar. Returns (price, reason, minute) or None (bars end)."""
    m0 = int(math.floor(start_min))
    mi = ((bars.index.hour * 60 + bars.index.minute) - 570).to_numpy()
    spyc = {}
    if spy is not None and spy_pct:
        spyc = dict(zip(((spy.index.hour * 60 + spy.index.minute) - 570).tolist(), spy.close.astype(float).tolist()))
    for m, o, h, l in zip(mi, bars.open.to_numpy(float), bars.high.to_numpy(float), bars.low.to_numpy(float)):
        if m < m0:
            continue
        if m >= FLAT_MIN:
            return float(o), "flatten", int(m)
        if m > m0 and spy_pct and spy_ref:
            sp = spyc.get(int(m) - 1)
            if sp is not None and side * (sp / spy_ref - 1) * 100 <= -spy_pct + 1e-9:
                return float(o), "spy_exit", int(m)
        if (side < 0 and h >= stop) or (side > 0 and l <= stop):
            px = stop if m == m0 else (max(o, stop) if side < 0 else min(o, stop))
            return float(px), "stop", int(m)
        if (side < 0 and l <= wide - thr(wide)) or (side > 0 and h >= wide + thr(wide)):
            return float(wide), "target", int(m)
    return None


# ------------------------------------------------------------------------------------------------------- data
def _git_show(ref: str) -> bytes | None:
    r = subprocess.run(["git", "-C", GIT, "show", ref], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def _fetch_branches() -> None:
    for b in BRANCHES.values():
        subprocess.run(["git", "-C", GIT, "fetch", "-q", "origin", f"+refs/heads/{b}:refs/remotes/origin/{b}"],
                       capture_output=True)


def journal_trades(day: str) -> pd.DataFrame:
    out = []
    for acct, br in BRANCHES.items():
        raw = _git_show(f"origin/{br}:journal.db")
        if not raw:
            continue
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.write(raw)
        try:
            c = sqlite3.connect(f.name)
            t = pd.read_sql("SELECT t.id, t.date, t.symbol, t.strategy, t.side, t.signal_time, t.entry_time, t.exit_time, "
                            "t.entry, t.stop, t.target, t.exit, t.exit_reason, t.shares, t.pnl, t.pnl_adj, t.meta "
                            "FROM trades t JOIN runs r ON r.id = t.run_id "
                            "WHERE r.kind NOT IN ('whatif', 'shadow') AND t.date = ? AND (t.strategy LIKE 'RW3-%' "
                            "OR t.strategy LIKE 'RW5-%')", c, params=(day,))
            c.close()
        finally:
            os.unlink(f.name)
        t = t[t.strategy.map(family_of).notna()]
        t["account"] = acct
        out.append(t)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def fetch_bars(day: str, syms: list[str]) -> dict[str, pd.DataFrame]:
    """symbol -> RTH 1-minute SIP bars (ET index); read-only Alpaca market data."""
    from mcf.replay.store import _fetch_bars              # read-only market data (GET), no trading endpoint
    x = _fetch_bars(sorted(set(syms)), f"{day}T13:30:00Z", f"{day}T21:00:00Z", "1Min")
    if not len(x):
        return {}
    x = x.set_index(pd.DatetimeIndex(x.pop("ts")).tz_convert(TZ))
    out = {}
    for s, g in x.groupby("symbol"):
        mm = g.index.hour * 60 + g.index.minute
        out[str(s)] = g[(mm >= 570) & (mm < 960)][["open", "high", "low", "close"]].astype(float).sort_index()
    return out


def _et(ts) -> pd.Timestamp | None:
    if ts is None or (isinstance(ts, float) and np.isnan(ts)) or ts == "":
        return None
    t = pd.Timestamp(ts)
    t = t.tz_localize("UTC") if t.tzinfo is None else t
    return t.tz_convert(TZ)


# ------------------------------------------------------------------------------------------------------- one lot
def score_lot(t, bars: dict[str, pd.DataFrame], model: dict) -> dict:
    """Both arms with the same LR8 cost model: parent = the live exit parts, wide = the live parts with every target
    part re-walked to the wide target. A non-target exit is identical in both arms (the wider target lies beyond the
    live one, so it cannot fill first): dR = 0 without bars."""
    from mcf.costs import lot_costs, parts_from_row
    side, e, stop, tgt = int(np.sign(t.side)), float(t.entry), float(t.stop), float(t.target)
    q = abs(float(t.shares or 0))
    risk = abs(e - stop) * q
    wide = wide_target(stop, tgt, side)
    ent, ex = _et(t.entry_time), _et(t.exit_time)
    row = dict(entry_et=f"{ent:%H:%M:%S}" if ent is not None else "", entry=e, stop=stop, target=tgt,
               wide_target=round(wide, 4), shares=int(q), live_exit_et=f"{ex:%H:%M:%S}" if ex is not None else "",
               live_exit=t.exit if pd.notna(t.exit) else "", live_reason=t.exit_reason or "")
    if ex is None or pd.isna(t.exit) or not risk > 0:
        row.update(status="open or no risk (not scored)")
        return row
    pnl = t.pnl_adj if pd.notna(t.pnl_adj) else t.pnl
    row["R_live"] = round(float(pnl) / risk, 4) if pd.notna(pnl) else ""
    parts = parts_from_row({"meta": t.meta, "exit_reason": t.exit_reason, "shares": q, "exit": t.exit})

    def r_of(pp, target):
        gross = sum(side * (px - e) * qq for qq, px, _ in pp)
        return (gross - lot_costs(side, e, q, pp, target, t.date, model)["total"]) / risk

    r_par = r_of(parts, tgt)
    row["R_parent"] = round(r_par, 4)
    if not any(w == "target" for _, _, w in parts):
        row.update(wide_exit_et=row["live_exit_et"], wide_exit=row["live_exit"], wide_reason=row["live_reason"],
                   R_wide=round(r_par, 4), dR=0.0, status="done")
        return row
    b = bars.get(t.symbol)
    if b is None or not len(b):
        row.update(status="pending: no bars for the symbol")
        return row
    fm = _minute(ex)
    lo_fill = b[((b.index.hour * 60 + b.index.minute) - 570) == int(math.floor(fm))]
    row["bars_check"] = ("ok" if len(lo_fill) and ((side < 0 and lo_fill.low.iloc[0] <= tgt + thr(tgt)) or
                                                   (side > 0 and lo_fill.high.iloc[0] >= tgt - thr(tgt)))
                         else "fill bar does not reach the live target")
    pct = SPY_EXIT.get(t.strategy)
    spy, spy_ref = None, None
    if pct:
        spy = bars.get("SPY")
        em = int(math.floor(_minute(ent))) - 1
        if spy is not None:
            s = spy[((spy.index.hour * 60 + spy.index.minute) - 570) == em]
            spy_ref = float(s.close.iloc[0]) if len(s) else None
    w = walk(b, side, stop, wide, fm, spy, spy_ref, pct)
    if w is None:
        row.update(status="pending: bars end before the lot closes")
        return row
    px, why, m = w
    new = [(qq, px, why) if r == "target" else (qq, p0, r) for qq, p0, r in parts]
    r_w = r_of(new, wide)
    mm = 570 + m
    row.update(wide_exit_et=f"{mm // 60:02d}:{mm % 60:02d}", wide_exit=round(px, 4), wide_reason=why,
               R_wide=round(r_w, 4), dR=round(r_w - r_par, 4), status="done")
    return row


def mark_dups(tr: pd.DataFrame, window_s: float = 300.0) -> list[int]:
    """The same signal taken in more than one account is scored once: a lot is a dup (1) when an account earlier in
    BRANCHES order (Primary first) already holds a lot of the same family, symbol and side signalled within 5 minutes.
    Rows must be sorted by account order; columns account, strategy, symbol, side, sig (ET timestamp or None)."""
    seen, out = [], []
    for _, t in tr.iterrows():
        key = (family_of(t.strategy), t.symbol, int(np.sign(t.side)))
        d = int(any(k == key and a != t.account and s is not None and t.sig is not None
                    and abs((t.sig - s).total_seconds()) <= window_s for k, a, s in seen))
        seen.append((key, t.account, t.sig))
        out.append(d)
    return out


# ------------------------------------------------------------------------------------------------------- run
def run(day: str, fetch: bool = True) -> dict:
    if LOCK_A <= day <= LOCK_B:
        raise SystemExit("locked block - never read")
    now = pd.Timestamp.now(tz=TZ)
    if str(now.date()) == day and now.hour * 60 + now.minute < 16 * 60 + 15:
        drow = dict(date=day, status="pending: run after 16:15 ET (the live job owns the market-data quota)",
                    frozen=FROZEN)
        upsert(DAYS, DCOLS, [drow], day)
        return drow
    if fetch:
        _fetch_branches()
    from mcf.config import load_config
    from mcf.costs import live_model
    model = live_model(load_config())
    tr = journal_trades(day)
    rows = []
    if len(tr):
        need = tr.exit_reason.fillna("").str.contains("target") | tr.meta.fillna("").str.contains("target:")
        syms = sorted(set(tr[need].symbol)) + (["SPY"] if tr[need].strategy.isin(SPY_EXIT).any() else [])
        bars = fetch_bars(day, syms) if syms else {}
        acc_order = {a: i for i, a in enumerate(BRANCHES)}
        tr["ak"] = tr.account.map(acc_order)
        tr["sig"] = [_et(x) for x in tr.signal_time]
        tr = tr.sort_values(["ak", "id"])
        tr["dup"] = mark_dups(tr)
        for _, t in tr.iterrows():
            r = dict(date=day, account=t.account, setup=t.strategy, family=family_of(t.strategy), trade_id=int(t.id),
                     symbol=t.symbol, side=int(t.side), dup=int(t.dup), frozen=FROZEN)
            r.update(score_lot(t, bars, model))
            rows.append(r)
    upsert(OUT, COLS, rows, day)
    done = [r for r in rows if r.get("status") == "done"]
    pend = [r for r in rows if str(r.get("status", "")).startswith("pending")]
    sc = [r for r in done if not r["dup"]]
    status = "done" if not pend else f"partial: {len(pend)} lot(s) pending"
    if not rows:
        status = "done (no RW3/RW5 lots)"
    drow = dict(date=day, lots=len(rows), lots_scored=len(sc),
                target_lots=sum(1 for r in sc if "target" in str(r["live_reason"])),
                changed=sum(1 for r in sc if abs(float(r["dR"])) > 1e-9),
                dR_sum=round(sum(float(r["dR"]) for r in sc), 3),
                R_parent_sum=round(sum(float(r["R_parent"]) for r in sc), 3),
                R_wide_sum=round(sum(float(r["R_wide"]) for r in sc), 3), status=status, frozen=FROZEN)
    upsert(DAYS, DCOLS, [drow], day)
    return drow


def upsert(path: Path, cols: list[str], rows: list[dict], day: str) -> None:
    old = []
    if path.exists():
        with open(path, newline="") as f:
            old = [r for r in csv.DictReader(f) if r["date"] != day]
    old += [{k: r.get(k, "") for k in cols} for r in rows]
    old.sort(key=lambda r: (r["date"], r.get("account", ""), str(r.get("trade_id", "")).zfill(9)))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(old)


# ------------------------------------------------------------------------------------------------------- score
def clustered(df: pd.DataFrame, col: str) -> tuple[float, float]:
    """Per-trade mean of `col` and its day-clustered standard error (trades within a session are not independent)."""
    d = df.groupby("date")[col].agg(["sum", "size"])
    n, k = d["size"].sum(), len(d)
    th = d["sum"].sum() / n
    if k < 2:
        return float(th), float("nan")
    se = math.sqrt(k / (k - 1) * ((d["sum"] - d["size"] * th) ** 2).sum()) / n
    return float(th), float(se)


def wo_best(df: pd.DataFrame, col: str) -> tuple[float | None, float | None, str | None]:
    """(avg per trade without the best session, best session's share of the total, best session)."""
    d = df.groupby("date")[col].sum()
    if not len(d):
        return None, None, None
    bd = d.idxmax()
    rest = df[df.date != bd]
    tot = d.sum()
    return (float(rest[col].mean()) if len(rest) else None), (float(d.max() / tot) if tot > 0 else None), bd


def score(start: str = FORWARD_FROM, end: str = "9999", path: Path = OUT, days_path: Path = DAYS) -> dict:
    f = pd.read_csv(path)
    d = pd.read_csv(days_path)
    sess = d[(d.date >= start) & (d.date <= end) & d.status.astype(str).str.startswith("done")]
    f = f[(f.date >= start) & (f.date <= end) & (f.status == "done") & (f.dup == 0)].copy()
    for c in ("R_parent", "R_wide", "dR"):
        f[c] = f[c].astype(float)
    out = dict(window=f"{start}..{end}", sessions=int(len(sess)), trades=int(len(f)))
    if not len(f):
        out["verdict"] = "no scored trades yet"
        return out
    th, se = clustered(f, "dR")
    t = th / se if se and se > 0 else float("nan")
    dwo, dsh, dbd = wo_best(f, "dR")
    pwo, psh, _ = wo_best(f, "R_parent")
    wwo, wsh, _ = wo_best(f, "R_wide")
    fam = {k: dict(n=int(len(g)), parent_avg=round(g.R_parent.mean(), 3), wide_avg=round(g.R_wide.mean(), 3),
                   dR_avg=round(g.dR.mean(), 4), dR_sum=round(g.dR.sum(), 2), better=int((g.dR > 1e-9).sum()),
                   worse=int((g.dR < -1e-9).sum())) for k, g in f.groupby("family")}
    acct = {k: dict(n=int(len(g)), dR_sum=round(g.dR.sum(), 2), better=int((g.dR > 1e-9).sum()),
                    worse=int((g.dR < -1e-9).sum())) for k, g in f.groupby("account")}
    prim = f[f.account == "primary"]
    out.update(target_lots=int(f.live_reason.astype(str).str.contains("target").sum()),
               changed=int((f.dR.abs() > 1e-9).sum()),
               wide_reasons=f[f.dR.abs() > 1e-9].wide_reason.value_counts().to_dict(),
               parent_avg=round(f.R_parent.mean(), 4), wide_avg=round(f.R_wide.mean(), 4),
               parent_avg_wo_best_day=round(pwo, 4) if pwo is not None else None,
               wide_avg_wo_best_day=round(wwo, 4) if wwo is not None else None,
               parent_best_day_share=round(psh, 2) if psh is not None else None,
               wide_best_day_share=round(wsh, 2) if wsh is not None else None,
               dR_per_trade=round(th, 4), dR_se=round(se, 4) if se == se else None, dR_t=round(t, 2) if t == t else None,
               dR_total=round(f.dR.sum(), 2), dR_wo_best_day=round(dwo, 4) if dwo is not None else None,
               dR_best_day=dbd, dR_best_day_share=round(dsh, 2) if dsh is not None else None,
               primary_n=int(len(prim)), primary_dR_sum=round(prim.dR.sum(), 2), by_family=fam, by_account=acct)
    checks = dict(
        dR_positive=bool(th > 0),
        dR_t=bool(t == t and t >= T_BAR),
        dR_wo_best_day=bool(dwo is not None and dwo > 0),
        best_day_lt_half=bool(dsh is not None and dsh < 0.5),
        RW3_not_worse=bool(f[f.family == "RW3"].dR.sum() >= 0),
        RW5_not_worse=bool(f[f.family == "RW5"].dR.sum() >= 0),
        primary_dR_positive=bool(float(prim.dR.sum()) > 0))
    out["pass_checks"] = checks
    ready = out["sessions"] >= MIN_SESSIONS and out["trades"] >= MIN_TRADES
    harm = out["sessions"] >= HARM_SESSIONS and th < 0 and t == t and t <= HARM_T
    if ready:
        out["verdict"] = ("PASS - write up as a DECISION for the owner (Primary exit change only via the Friday epoch)"
                          if all(checks.values()) else "FAIL - retire WT1 (no re-tune on the same forward data)")
    elif harm:
        out["verdict"] = f"HARM STOP - dR t {t:.2f} <= {HARM_T} after >= {HARM_SESSIONS} sessions: retire WT1"
    else:
        out["verdict"] = (f"not scored yet (needs >= {MIN_SESSIONS} sessions and >= {MIN_TRADES} trades; "
                          f"have {out['sessions']} / {out['trades']})")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", action="append", default=[])
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--start", default=FORWARD_FROM)
    ap.add_argument("--end", default="9999")
    a = ap.parse_args()
    for i, dd in enumerate(a.date):
        print(json.dumps(run(dd, fetch=(i == 0))))
    if a.score:
        print(json.dumps(score(a.start, a.end), indent=1, default=str))
