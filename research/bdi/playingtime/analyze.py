"""Playing-time capacity analysis (owner 2026-10-12). Educational only - not financial advice.

Question: do our accounts run too many setups for each to get enough trades? Two sources:
  A. Live journals (state branches mcf-data / mcf-data-testing): what each setup actually got, and what it lost
     because another setup already held the symbol (mcf/report/playing_time.py).
  B. Lab competition replay on the open two-year history (research/bdi/timeofday/data/trades.parquet: every setup's
     first qualifying bar per symbol-day, locked block excluded). Only entry COUNTS are used - no R, no holdout -
     so this spends no look on any setup. The replay applies the live rule: one position per symbol across setups,
     earlier signal wins, same bar -> setup_order wins, a skipped setup does not retry that symbol that day.
     Holding time is an assumption (scenarios: same bar only / 120 min = live mean / until 15:55).

Usage: python research/bdi/playingtime/analyze.py --primary <primary journal.db> --testing <testing journal.db>
       [--state-primary DIR] [--state-testing DIR]   (setups/<date>.json snapshots for the live part)
Writes results.json and tables/*.csv next to this file.
"""
from __future__ import annotations

import argparse
import json
import random
import sqlite3
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from mcf.report import playing_time as pt  # noqa: E402

LAB = ROOT / "research" / "bdi" / "timeofday" / "data" / "trades.parquet"
FLAT = 15 * 60 + 55
HOLDS = {"same_bar": 0, "hold_120m": 120, "to_close": None}
TARGET = pt.TARGET_PER_WEEK


def _cfg(account: str) -> dict:
    import os

    from mcf.config import load_config

    old = os.environ.get("MCF_ACCOUNT")
    os.environ["MCF_ACCOUNT"] = account
    try:
        return load_config()
    finally:
        if old is None:
            os.environ.pop("MCF_ACCOUNT", None)
        else:
            os.environ["MCF_ACCOUNT"] = old


def live_setups(account: str) -> list[str]:
    cfg = _cfg(account)
    return pt._rank(cfg["strategies"], cfg["live"].get("setup_order"))


def _mins(tod: int) -> int:
    return (tod // 100) * 60 + tod % 100


def lab_events(names: list[str]) -> tuple[pd.DataFrame, list[str]]:
    """Lab first-qualifying-bar entries for the given live setup names; -FD -> 'full' set, else 'current'."""
    t = pd.read_parquet(LAB, columns=["date", "symbol", "tod", "setup", "set"])
    parts, missing = [], []
    for n in names:
        base, st = (n[:-3], "full") if n.endswith("-FD") else (n, "current")
        x = t[(t["setup"] == base) & (t["set"] == st)]
        if not len(x):
            missing.append(n)
            continue
        parts.append(x.assign(name=n)[["date", "symbol", "tod", "name"]])
    ev = pd.concat(parts, ignore_index=True)
    ev["m"] = ev["tod"].map(_mins)
    return ev, missing


def replay(ev: pd.DataFrame, order: list[str], hold: int | None, days=None, slots: int | None = None,
           per_setup_cap: int | None = None) -> pd.DataFrame:
    """Per event: taken or lost (and to whom). One position per symbol; earlier wins, same bar -> priority.
    With slots / per_setup_cap, an entry is also lost when that many positions are open ('slots' / 'cap')."""
    import heapq

    pri = {n: i for i, n in enumerate(order)}
    e = ev[ev["name"].isin(pri)]
    if days is not None:
        e = e[e["date"].isin(days)]
    e = e.assign(p=e["name"].map(pri)).sort_values(["date", "m", "p"], kind="stable")
    taken, by = [], []
    held: dict = {}
    openq: list = []
    per: dict = {}
    cur = None
    for d, sym, m, n in zip(e["date"].to_numpy(), e["symbol"].to_numpy(), e["m"].to_numpy(), e["name"].to_numpy()):
        if d != cur:
            held, openq, per, cur = {}, [], {}, d
        while openq and openq[0][0] <= m:
            _, nn = heapq.heappop(openq)
            per[nn] -= 1
        h = held.get(sym)
        if h is not None and h[0] > m:
            taken.append(False)
            by.append(h[1])
            continue
        if slots is not None and len(openq) >= slots:
            taken.append(False)
            by.append("(slots full)")
            continue
        if per_setup_cap is not None and per.get(n, 0) >= per_setup_cap:
            taken.append(False)
            by.append("(per-setup cap)")
            continue
        until = FLAT if hold is None else (m + max(hold, 1))     # hold 0: blocks only the same bar
        held[sym] = (until, n)
        heapq.heappush(openq, (until, n))
        per[n] = per.get(n, 0) + 1
        taken.append(True)
        by.append(None)
    return e.assign(taken=taken, lost_to=by)


def per_setup(r: pd.DataFrame, n_days: int, order: list[str], share_days: float = 1.0) -> pd.DataFrame:
    """share_days: fraction of sessions the setup runs (rotation: 1/k)."""
    g = r.groupby("name").agg(signals=("taken", "size"), taken=("taken", "sum"))
    lost = r[~r["taken"]].groupby(["name", "lost_to"]).size()
    out = []
    for n in order:
        if n not in g.index:
            out.append({"setup": n, "signals_per_day": 0.0, "taken_per_day": 0.0, "lost_share": 0.0, "top_taker": "", "per_week": 0.0})
            continue
        s, tk = int(g.loc[n, "signals"]), int(g.loc[n, "taken"])
        top = lost.loc[n].sort_values(ascending=False) if n in lost.index.get_level_values(0) else pd.Series(dtype=int)
        out.append({"setup": n, "signals_per_day": round(s / n_days, 2), "taken_per_day": round(tk / n_days, 2),
                    "lost_share": round(1 - tk / s, 3) if s else 0.0,
                    "top_taker": "; ".join(f"{k} {v / s:.0%}" for k, v in top.head(2).items()),
                    "per_week": round(tk / n_days * 5 * share_days, 1)})
    return pd.DataFrame(out)


def conflicts(r: pd.DataFrame) -> dict[tuple[str, str], int]:
    c: dict = {}
    for a, b in zip(r.loc[~r["taken"], "name"], r.loc[~r["taken"], "lost_to"]):
        if str(b).startswith("("):
            continue
        k = tuple(sorted((a, b)))
        c[k] = c.get(k, 0) + 1
    return c


def groups(order: list[str], conf: dict, k: int, weight: dict[str, float]) -> list[list[str]]:
    """Greedy split into k rotation groups: busiest-conflict setups first, each into the group where it collides
    least (ties: lighter group by standalone volume). Keeps priority order inside each group."""
    tot = {n: sum(v for (a, b), v in conf.items() if n in (a, b)) for n in order}
    gs: list[list[str]] = [[] for _ in range(k)]
    vol = [0.0] * k
    for n in sorted(order, key=lambda x: -tot[x]):
        cost = [sum(conf.get(tuple(sorted((n, m))), 0) for m in g) for g in gs]
        i = min(range(k), key=lambda j: (cost[j], vol[j], len(gs[j])))
        gs[i].append(n)
        vol[i] += weight.get(n, 0.0)
    pos = {n: i for i, n in enumerate(order)}
    return [sorted(g, key=pos.get) for g in gs]


def lab_account(account: str, ev_all: pd.DataFrame | None = None) -> dict:
    order = live_setups(account)
    ev, missing = lab_events(order)
    order_lab = [n for n in order if n not in missing]
    days = sorted(ev["date"].unique())
    nd = len(days)
    alone = {n: (ev["name"] == n).sum() / nd for n in order_lab}
    res: dict = {"account": account, "setups_live": len(order), "setups_in_lab": len(order_lab), "missing_from_lab": missing,
                 "sessions": nd, "scenarios": {}}
    tables = {}
    for lab, hold in HOLDS.items():
        r = replay(ev, order_lab, hold)
        t = per_setup(r, nd, order_lab)
        t["standalone_per_week"] = [round(alone[n] * 5, 1) for n in t["setup"]]
        tables[lab] = t
        res["scenarios"][lab] = {
            "signals_per_day": round(len(r) / nd, 1), "taken_per_day": round(r["taken"].sum() / nd, 1),
            "lost_share": round(1 - r["taken"].mean(), 3),
            "setups_below_target": int((t["per_week"] < TARGET).sum()),
            "setups_lost_over_25pct": int((t["lost_share"] >= 0.25).sum()),
        }
        if hold == 120:   # concurrency check against the account's slots
            tk = r[r["taken"]]
            peak = 0
            for _, g in tk.groupby("date"):
                ms = sorted(g["m"])
                j = 0
                for i, m in enumerate(ms):
                    while ms[j] <= m - 120:
                        j += 1
                    peak = max(peak, i - j + 1)
            res["peak_concurrent_hold_120m"] = int(peak)
    main = tables["hold_120m"]
    r120 = replay(ev, order_lab, 120)
    conf = conflicts(r120)
    res["top_conflicts"] = [{"pair": list(k), "lost_signals_per_week": round(v / nd * 5, 1)}
                            for k, v in sorted(conf.items(), key=lambda kv: -kv[1])[:15]]
    # random subsets: how preemption grows with the number of setups
    rnd = random.Random(20261012)
    curve = []
    for n in [x for x in (3, 5, 8, 11, 15, 20, 25, 30, len(order_lab)) if x <= len(order_lab)]:
        shares, worst = [], []
        for _ in range(1 if n == len(order_lab) else 20):
            sub = set(rnd.sample(order_lab, n))
            o = [x for x in order_lab if x in sub]
            rr = replay(ev, o, 120)
            shares.append(1 - rr["taken"].mean())
            worst.append(per_setup(rr, nd, o)["lost_share"].max())
        curve.append({"setups": n, "account_lost_share": round(sum(shares) / len(shares), 3),
                      "worst_setup_lost_share": round(sum(worst) / len(worst), 3)})
    res["setups_vs_preemption"] = curve
    # rotation: k groups on alternating sessions
    rot = {}
    for k in (2, 3):
        gs = groups(order_lab, conf, k, alone)
        rows = []
        for gi, g in enumerate(gs):
            rr = replay(ev, g, 120)
            t = per_setup(rr, nd, g, share_days=1 / k)
            t["group"] = gi + 1
            rows.append(t)
        t = pd.concat(rows).set_index("setup").reindex(order_lab).reset_index()
        tables[f"rotation_{k}"] = t
        rot[k] = {"groups": gs, "setups_below_target": int((t["per_week"] < TARGET).sum()),
                  "setups_lost_over_25pct": int((t["lost_share"] >= 0.25).sum()),
                  "taken_per_day": round(sum(t["taken_per_day"]) / k, 1)}
    # rare setups every day, the busy ones split into 2 alternating groups
    cfg = _cfg(account)
    slots, cap = cfg["account"]["max_concurrent_positions"], cfg["account"].get("max_positions_per_strategy")
    rare = [n for n in order_lab if alone[n] * 5 <= 40]
    busy = [n for n in order_lab if n not in rare]
    gs = groups(busy, {k: v for k, v in conf.items() if k[0] in busy and k[1] in busy}, 2, alone)
    rows = []
    for gi, g in enumerate(gs):
        grp = [n for n in order_lab if n in rare or n in g]
        rr = replay(ev, grp, 120, slots=slots, per_setup_cap=cap)
        t = per_setup(rr, nd, grp, share_days=0.5)
        t.loc[t["setup"].isin(rare), "per_week"] *= 2      # rare setups run every session
        rows.append(t)
    t = pd.concat(rows)
    t = t.groupby("setup", sort=False).agg(per_week=("per_week", "sum"), lost_share=("lost_share", "mean")).reindex(order_lab).reset_index()
    t["per_week"] = [round(w / (2 if n in rare else 1), 1) for n, w in zip(t["setup"], t["per_week"])]
    tables["rare_daily_busy_rotated"] = t
    rot["rare_daily_busy_rotated"] = {"rare_every_day": rare, "groups": gs, "setups_below_target": int((t["per_week"] < TARGET).sum()),
                                      "setups_lost_over_25pct": int((t["lost_share"] >= 0.25).sum())}
    res["rotation"] = rot
    # the account's own caps (slots, per-setup cap) on top of one-position-per-symbol, 120 min hold
    rc = replay(ev, order_lab, 120, slots=slots, per_setup_cap=cap)
    tc = per_setup(rc, nd, order_lab)
    tables["hold_120m_with_caps"] = tc
    res["with_account_caps"] = {"slots": slots, "per_setup_cap": cap, "taken_per_day": round(rc["taken"].sum() / nd, 1),
                                "lost_share": round(1 - rc["taken"].mean(), 3),
                                "lost_to_slots_per_day": round((rc["lost_to"] == "(slots full)").sum() / nd, 1),
                                "lost_to_setup_cap_per_day": round((rc["lost_to"] == "(per-setup cap)").sum() / nd, 1),
                                "sessions_with_slots_full": int(rc[rc["lost_to"] == "(slots full)"]["date"].nunique()),
                                "setups_below_target": int((tc["per_week"] < TARGET).sum())}
    out = HERE / "tables"
    out.mkdir(exist_ok=True)
    for lab, t in tables.items():
        t.to_csv(out / f"lab_{account}_{lab}.csv", index=False)
    res["per_setup_hold_120m"] = main.to_dict("records")
    return res


def live_part(db: str, account: str, state: str | None, day: str) -> dict:
    con = sqlite3.connect(db)
    sig = pd.read_sql("SELECT * FROM signals WHERE run_id=1 ORDER BY id", con)
    tr = pd.read_sql("SELECT * FROM trades WHERE run_id=1", con)
    exp = pt.expected_rates("primary")    # the setups in these journals ran in their windowed (primary) form
    rep = pt.build(sig, tr, day, account, state, None, expected=exp)
    taken = sig[sig["status"].isin(["submitted", "dry_run"])]
    stacked = taken.groupby(["day", "symbol"]).size()
    stacked = stacked[stacked > 1]
    rep["stacked_before_pending_fix"] = {"symbol_days": int(len(stacked)), "extra_entries": int((stacked - 1).sum()),
                                         "by_day": {d: int((g - 1).sum()) for d, g in stacked.groupby(level=0)}}
    # live vs lab frequency (signals/day live over lab expected/day, setups with an expected rate)
    rows = [r for r in rep["cumulative"]["setups"] if r["expected_per_day"]]
    live = sum(r["signals"] for r in rows)
    lab = sum(r["expected_per_day"] * r["sessions"] for r in rows)
    rep["live_over_lab_signal_ratio"] = round(live / lab, 2) if lab else None
    return rep


def trimmed_rates(skip_top: int = 5) -> dict:
    """Expected entries/day per setup for the playing-time report: two-year lab, first qualifying bar per symbol-day,
    the `skip_top` busiest sessions left out (RW6G1 put 226 of its 424 signals on 2025-04-07 alone)."""
    t = pd.read_parquet(LAB, columns=["date", "setup", "set"])
    nd = t["date"].nunique()
    out = {}
    for (s, st), g in t[t["set"].isin(["current", "full"])].groupby(["setup", "set"]):
        c = g.groupby("date").size().sort_values(ascending=False)
        key = s if st == "current" else f"{s}-FD"
        out[key] = {"per_day": round(float(c.iloc[skip_top:].sum()) / (nd - skip_top), 2),
                    "raw_per_day": round(float(c.sum()) / nd, 2),
                    "top_days_share": round(float(c.head(skip_top).sum() / c.sum()), 3)}
    return {"note": f"Two-year lab history (open part, locked block excluded), first qualifying bar per symbol-day, "
                    f"{skip_top} busiest sessions excluded; {nd} sessions. Counts only, no R. Educational only - not "
                    f"financial advice.", "skip_top_days": skip_top, "sessions": nd, "setups": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--primary")
    ap.add_argument("--testing")
    ap.add_argument("--state-primary")
    ap.add_argument("--state-testing")
    a = ap.parse_args()
    res = {"note": "Educational only - not financial advice. Entry counts only (no R); locked block excluded.",
           "target_per_week": TARGET, "live": {}, "lab": {}}
    if a.primary:
        res["live"]["primary"] = live_part(a.primary, "primary", a.state_primary, "2026-10-09")
    if a.testing:
        res["live"]["testing"] = live_part(a.testing, "testing", a.state_testing, "2026-10-09")
    for acct in ("primary", "testing"):
        res["lab"][acct] = lab_account(acct)
        print(acct, json.dumps(res["lab"][acct]["scenarios"]), res["lab"][acct].get("peak_concurrent_hold_120m"))
    (HERE / "expected_rates.json").write_text(json.dumps(trimmed_rates(), indent=1))
    (HERE / "results.json").write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
