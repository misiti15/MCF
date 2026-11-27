"""Index open-dip forward shadow (IDXFWD-1127). Rules frozen 2026-11-27 - see RULE.md.

    python research/forward/idx_dip/shadow.py --date YYYY-MM-DD [--date ...]
    python research/forward/idx_dip/shadow.py --from 2026-11-05 --to 2026-11-27     (backfill, weekdays)
    python research/forward/idx_dip/shadow.py --score
    python research/forward/idx_dip/shadow.py --verify      (re-scores the cached FIT+CHECK history vs idxdip_1127)

Two frozen rules, ported line for line from research/idxdip_1127/idx_sim.py (engine E4 = qqqopen_1127 qo_sim):
  IDX6  QQQ down >= 1.5% from the open on a bar closed by 09:55 -> long TQQQ, 20% bounce trigger, 1R trail.
  IWM45 IWM down >= 0.75% from the open on a bar closed by 09:45 -> long TNA, 20% bounce trigger, 1R trail.
Fetches that session's 1-minute SIP bars read-only (mcf.replay.store._fetch_bars: market-data GET only, no trading
endpoint), simulates fill + exit, applies LIVE-L costs (main) and LR8 (alongside) plus the S12 stress (+1 minute entry,
+2 bp a side), and upserts one row per (date, rule) into forward.csv (idempotent: re-running a date replaces its rows).
Research only - nothing here places orders or changes any config. Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "forward.csv"
TZ = "America/New_York"
FROZEN = "2026-11-27"
FIRST_DAY = "2026-11-05"                         # first session after the CHECK end (2026-11-04)
LOCK = ("2024-11-01", "2025-02-28")              # locked holdout: never read

# frozen rules (T = check time in minutes after midnight ET, bar close = bar start + 1 min)
RULES = {
    "IDX6": dict(sig="QQQ", trd="TQQQ", X=1.5, T=595, B=0.20, trail=True),
    "IWM45": dict(sig="IWM", trd="TNA", X=0.75, T=585, B=0.20, trail=True),
}
EXIT_MIN, HALF_BUF = 955, 5                      # flat 15:55; half days: last bar close - 5 min
STOP_FRAC = 0.10
COLS = ["date", "rule", "sig", "trd", "signal", "idx_low_pct", "trigger_time", "entry_time", "entry", "stop",
        "stop_pct", "exit_time", "exit", "kind", "R_gross", "R_livel", "R_lr8", "R_s12", "status", "frozen"]
KIND = {0: "market", 1: "stop", 2: "target"}
PB = [0, 5, 10, 20, 50, 100, 1e9]
PBL = ["<5", "5-10", "10-20", "20-50", "50-100", "100+"]
TOD_COST = ((935, 3.8), (950, 2.1), (1030, 1.4))  # = mcf.research.gates.TOD_COST (LR8 entry multiplier)


def _nolock(day: str) -> None:
    assert not (LOCK[0] <= str(day) <= LOCK[1]), "locked block day"


def tmin(idx) -> np.ndarray:
    return np.array([x.hour * 60 + x.minute for x in idx])


def _session(df: pd.DataFrame | None) -> pd.DataFrame | None:
    if df is None or df.empty:
        return None
    df = df[["open", "high", "low", "close"]].copy()
    df.index = pd.DatetimeIndex(df.index).tz_convert(TZ)
    df = df[~df.index.duplicated(keep="last")].sort_index().between_time("09:30", "15:59")
    return df


def simulate(o, h, l, c, mins, j, fill, stop, side, exit_min, trail):
    """idx_sim.simulate (tgt = 0): gross R, exit kind (0 market/time, 1 stop), exit bar, exit price, risk."""
    risk = side * (fill - stop)
    if risk <= 0:
        return None
    mfe = 0.0
    for k in range(j, len(o)):
        if mins[k] >= exit_min:
            return side * (o[k] - fill) / risk, 0, k, o[k], risk
        hit = (l[k] <= stop) if side == 1 else (h[k] >= stop)
        if hit:
            gap = (o[k] < stop) if side == 1 else (o[k] > stop)
            px = o[k] if (gap and k > j) else stop
            return side * (px - fill) / risk, 1, k, px, risk
        fav = h[k] if side == 1 else l[k]
        mfe = max(mfe, side * (fav - fill) / risk)
        if trail and mfe >= 1.0:
            tr = fill + side * (mfe - 1.0) * risk
            stop = max(stop, tr) if side == 1 else min(stop, tr)
    return side * (c[-1] - fill) / risk, 0, len(o) - 1, c[-1], risk


def _cells():
    return json.load(open(ROOT / "research/primshorts_1126/cells_live.json"))


def costs(entry, exit_px, risk, kind, tod, cells=None):
    """Per-trade costs in R, as research/idxdip_1127/idx_score.costs (long side): LIVE-L, LR8, extra +2 bp a side."""
    cells = cells or _cells()
    pb = PBL[int(np.searchsorted(PB, entry, side="right")) - 1]
    a, b = cells.get(f"{pb}|{KIND[kind]}", cells[f"*|{KIND[kind]}"])[:2]
    c_livel = a / (risk / entry * 1e4) + b
    mult = 1.0
    for edge, m in reversed(TOD_COST):
        if tod < edge:
            mult = m
    tier = 3.0 if entry < 5 else 1.0
    ec = (0.01 + entry * 1e-4) * mult
    xc = 0.01 + exit_px * 1e-4 + (0.02 if kind == 1 else 0.0)
    c_lr8 = tier * (ec + xc) / risk
    c_2bp = 2e-4 * (entry + exit_px) / risk
    return c_livel, c_lr8, c_2bp


def evaluate(ix: pd.DataFrame | None, tx: pd.DataFrame | None, rule: str, cells=None, complete: bool = True) -> dict:
    """The frozen rule on one session (index bars ix, traded 3x ETF bars tx). Returns the forward.csv fields."""
    cf = RULES[rule]
    row = {k: "" for k in COLS}
    row.update(rule=rule, sig=cf["sig"], trd=cf["trd"])
    ix, tx = _session(ix), _session(tx)
    if ix is None or tx is None:
        row.update(signal="", status="no bars (holiday or not yet open)")
        return row
    imin = tmin(ix.index); tmn = tmin(tx.index)
    if imin[0] != 570 or tmn[0] != 570:
        row.update(signal="", status="skipped: no 09:30 bar")
        return row
    io, ih, il, ic = (ix[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    to_, th, tl, tc = (tx[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    O = io[0]; tO = to_[0]; ends = imin + 1
    run_lo = np.minimum.accumulate(il)
    X, T, B = cf["X"], cf["T"], cf["B"]
    if imin[-1] + 1 < T + 10 and not complete:
        row.update(signal="", status=f"pending: {cf['sig']} bars to the decision window not yet available")
        return row
    low_by_T = run_lo[ends <= T]
    if len(low_by_T):
        row["idx_low_pct"] = round(float((low_by_T[-1] / O - 1) * 100), 3)
    if len(ix) < 60 or len(tx) < 60:
        row.update(signal="", status="skipped: < 60 bars")
        return row
    exit_min = min(EXIT_MIN, max(imin[-1], tmn[-1]) + 1 - HALF_BUF)
    dipped = (run_lo <= O * (1 - X / 100)) & (ends <= T)
    if not dipped.any():
        row.update(signal="no", status=f"no signal: {cf['sig']} low by {T // 60:02d}:{T % 60:02d} not >= {X}% below open")
        return row
    i0 = int(np.argmax(dipped)); trig = None
    for i in range(i0, len(ix)):
        if ends[i] > T + 10:
            break
        if ends[i] < T - 5:
            continue
        if ic[i] >= run_lo[i] + B * (O - run_lo[i]):
            trig = i; break
    if trig is None:
        row.update(signal="no", status="no signal: dip but no 20% bounce close in [T-5, T+10]")
        return row
    k = int(np.searchsorted(tmn, imin[trig], side="right")) - 1
    if k < 0 or k + 2 >= len(tx):
        row.update(signal="no", status="no signal: traded ETF bars missing after the trigger")
        return row
    seg_lo = tl[: k + 1].min(); px = tc[k]
    drop = tO - seg_lo
    if not (drop > 0 and px > seg_lo):
        row.update(signal="no", status="no signal: ETF not above its low / no ETF drop")
        return row
    stop = seg_lo - STOP_FRAC * drop
    tt = ends[trig]
    row.update(signal="yes", trigger_time=f"{tt // 60:02d}:{tt % 60:02d}")
    if not complete:
        row.update(status="pending: session not finished")
        return row
    res = {}
    for var, j in (("BASE", k + 1), ("S1", k + 2)):
        if tmn[j] >= exit_min:
            res[var] = None
            continue
        fill = to_[j]
        r = simulate(to_, th, tl, tc, tmn, j, fill, stop, 1, exit_min, cf["trail"])
        if r is None:                              # S1: already through the stop at the delayed fill
            res[var] = (-1.0, 1, j, fill, res["BASE"][4] if res.get("BASE") else None, fill, j)
        else:
            res[var] = (*r, fill, j)
    if res.get("BASE") is None:
        row.update(signal="no", status="no signal: entry at/after the exit time")
        return row
    g, kind, kx, xp, risk, fill, j = res["BASE"]
    tod = int(tx.index[j].hour * 100 + tx.index[j].minute)
    c_l, c_8, _ = costs(fill, xp, risk, kind, tod, cells)
    s12 = ""
    if res.get("S1") is not None and res["S1"][4]:
        g1, kind1, _, xp1, risk1, fill1, j1 = res["S1"]
        tod1 = int(tx.index[j1].hour * 100 + tx.index[j1].minute)
        cl1, _, c2 = costs(fill1, xp1, risk1, kind1, tod1, cells)
        s12 = round(float(g1 - cl1 - c2), 4)
    em, xm = tmn[j], tmn[kx]
    row.update(entry_time=f"{em // 60:02d}:{em % 60:02d}", entry=round(float(fill), 4), stop=round(float(stop), 4),
               stop_pct=round(float(risk / fill * 100), 3), exit_time=f"{xm // 60:02d}:{xm % 60:02d}",
               exit=round(float(xp), 4), kind=KIND[kind], R_gross=round(float(g), 4),
               R_livel=round(float(g - c_l), 4), R_lr8=round(float(g - c_8), 4), R_s12=s12, status="done")
    return row


def fetch(day: str) -> dict:
    sys.path.insert(0, str(ROOT))
    from mcf.replay.store import _fetch_bars       # read-only market data GET
    syms = sorted({s for r in RULES.values() for s in (r["sig"], r["trd"])})
    df = _fetch_bars(syms, f"{day}T13:00:00Z", f"{day}T21:30:00Z", "1Min")
    if df.empty:
        return {}
    df = df.set_index("ts")
    return {s: df[df.symbol == s] for s in syms}


def upsert(rows: list[dict], path: Path = OUT) -> None:
    days = {r["date"] for r in rows}
    old = []
    if path.exists():
        with open(path, newline="") as f:
            old = [r for r in csv.DictReader(f) if r["date"] not in days]
    allr = old + [{k: r.get(k, "") for k in COLS} for r in rows]
    allr.sort(key=lambda r: (r["date"], r["rule"]))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(allr)


def _complete(day: str) -> bool:
    now = pd.Timestamp.now(tz=TZ)
    return day < now.strftime("%Y-%m-%d") or (now.hour * 60 + now.minute) >= 16 * 60 + 15


def run(day: str, path: Path = OUT, bars: dict | None = None) -> list[dict]:
    _nolock(day)
    assert day >= FIRST_DAY, "forward log starts 2026-11-05 (after the CHECK end)"
    bars = fetch(day) if bars is None else bars
    cells = _cells()
    rows = []
    for name, cf in RULES.items():
        r = evaluate(bars.get(cf["sig"]), bars.get(cf["trd"]), name, cells, complete=_complete(day))
        r.update(date=day, frozen=FROZEN)
        rows.append(r)
    upsert(rows, path)
    return rows


def _st(x, d):
    x = np.asarray(x, float)
    if len(x) == 0:
        return dict(n=0, days=0)
    s = pd.Series(x).groupby(np.asarray(d)).sum()
    tot = float(x.sum()); best = float(s.max()); nd = len(s)
    sd = s.std(ddof=1) if nd > 1 else np.nan
    return dict(n=len(x), days=nd, mean=round(float(x.mean()), 3), tot=round(tot, 2),
                t=round(float(s.mean() / (sd / np.sqrt(nd))), 2) if nd > 1 and sd > 0 else None,
                best_share=round(best / tot, 3) if tot > 0 else None,
                wo_best=round((tot - best) / (len(x) - 1), 3) if len(x) > 1 else None,
                best_day=str(s.idxmax()))


def score(path: Path = OUT) -> dict:
    """Frozen pass bar (RULE.md) on the combined book of both rules; per rule reported alongside."""
    d = pd.read_csv(path, dtype=str)
    d = d[d.status == "done"].copy()
    for c in ("R_livel", "R_lr8", "R_s12"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    out = {"sessions_logged": int(pd.read_csv(path, dtype=str).date.nunique()),
           "book_livel": _st(d.R_livel, d.date), "book_lr8": _st(d.R_lr8, d.date),
           "book_s12": _st(d.R_s12.dropna(), d.date[d.R_s12.notna()])}
    for name in RULES:
        g = d[d.rule == name]
        out[name] = {"livel": _st(g.R_livel, g.date), "lr8": _st(g.R_lr8, g.date)}
    b, s = out["book_livel"], out["book_s12"]
    harm = b.get("days", 0) >= 8 and (b["tot"] <= -6.0 or b["mean"] <= -0.40)
    if harm:
        verdict = "HARM STOP: close the question (logged; no re-tune on the same forward data)"
    elif b.get("days", 0) < 15:
        verdict = f"WAITING: {b.get('days', 0)} of 15 signal days"
    else:
        ok = (b["mean"] > 0 and (b["t"] or 0) >= 2.0 and b["best_share"] is not None and b["best_share"] < 0.5
              and (b["wo_best"] or 0) > 0 and s.get("n", 0) and s["mean"] > 0)
        verdict = "PASS: write it up for the owner (decision)" if ok else "FAIL: close the question"
    out["verdict"] = verdict
    return out


def verify() -> None:
    """Re-score the cached FIT + CHECK history (cache_hist, locked block skipped) and compare with
    research/idxdip_1127/results.json (n and LIVE-L mean per split)."""
    main = Path(os.environ.get("MCF_ROOT", "/home/user/MCF"))
    ref = json.load(open(ROOT / "research/idxdip_1127/results.json"))["configs"]
    names = {"IDX6": "G1|L|QQQ|1.5|0955|B0.2|TRAIL", "IWM45": "G1|L|IWM|0.75|0945|B0.2|TRAIL"}
    cells = _cells()
    for rule, cf in RULES.items():
        g = {}
        for s in (cf["sig"], cf["trd"]):
            b = pd.read_parquet(main / "data/cache_hist/1Min" / f"{s}.parquet")
            b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
            dd = b.index.date
            b = b[~((dd >= date(2024, 11, 1)) & (dd <= date(2025, 2, 28)))]
            g[s] = {str(k): v for k, v in b.groupby(b.index.date)}
        res = {"FIT": [], "CHECK": []}
        for day in sorted(g[cf["sig"]]):
            _nolock(day)
            sp = ("FIT" if ("2024-10-01" <= day < "2024-11-01" or "2025-03-01" <= day < "2025-10-01")
                  else "CHECK" if "2025-10-01" <= day <= "2026-11-04" else None)
            if sp is None or day not in g[cf["trd"]]:
                continue
            r = evaluate(g[cf["sig"]][day], g[cf["trd"]][day], rule, cells)
            if r["status"] == "done":
                res[sp].append(r["R_livel"])
        for sp, x in res.items():
            want = ref[names[rule]][sp]
            print(f"{rule} {sp}: shadow n {len(x)} mean {np.mean(x) if x else float('nan'):+.3f} | "
                  f"study n {want['n']} mean {want['mean']:+.3f}")


def _days(a: str, b: str) -> list[str]:
    d0, d1 = date.fromisoformat(a), date.fromisoformat(b)
    return [str(d0 + timedelta(i)) for i in range((d1 - d0).days + 1) if (d0 + timedelta(i)).weekday() < 5]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", action="append", default=[])
    ap.add_argument("--from", dest="frm")
    ap.add_argument("--to")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.verify:
        verify()
    days = a.date + (_days(a.frm, a.to or a.frm) if a.frm else [])
    for d in days:
        for r in run(d):
            print(d, r["rule"], r["signal"], r["R_livel"], r["status"])
    if a.score:
        print(json.dumps(score(), indent=1))
