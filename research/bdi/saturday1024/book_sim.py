"""saturday1024: book-level risk / give-back rules on two years of history (PLAN.md, 23 configs).

Uses the gates1021 cached signal tables (costs in, R per trade, entry tod, exit_tod). The locked block is never read
(load_sig asserts it). Usage: python book_sim.py <exits.parquet> [<lock.parquet>] > book_sim_out.txt
Educational only - not financial advice."""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "gates1021" / "scripts"))
from common import account_cfg  # noqa: E402
from load import day_delta, load_sig  # noqa: E402
from mcf.execution.risk import twin_groups, twin_key  # noqa: E402

N_LINEAGE = 1311 + 29   # 23 (PLAN) + 6 (addendum L)
BAR = round(max(1.5, math.sqrt(2 * math.log(N_LINEAGE))), 2)
ASG = json.loads((ROOT / "docs/live/assignments.json").read_text())["accounts"]
U = pd.read_csv(HERE.parent / "gates1021" / "setups_scored.csv").set_index("setup")
BOOKS = {  # book: (assignments key, config key, per-setup open cap, book daily stop R, G3 peak X)
    "Primary": ("primary", "primary", 100, 20, 3.0),
    "Testing 1": ("testing", "testing", 150, 120, 10.0),
    "Testing 2": ("testing2", "testing2", 50, 120, 10.0),
}


LOCK = sys.argv[2] if len(sys.argv) > 2 else None


def configs(book):
    c = [("B0", {})]
    if book == "Primary":
        c += [("S1.5", {"S": 1.5}), ("S2", {"S": 2.0}), ("S3", {"S": 3.0})]
    else:
        c += [("S2", {"S": 2.0})]
    c += [("SO", {"S": 2.0, "SO": 3.0}), ("G1", {"G1": True}), ("G2k3", {"G2": 3}), ("G2k5", {"G2": 5}),
          ("G3f50", {"G3": 0.5}), ("G3f33", {"G3": 0.33})]
    if LOCK is not None:
        c += [("L1500", {"L": "L1500"}), ("L1430", {"L": "L1430"})]
    return c


def sim_day(d: pd.DataFrame, rule: dict, cap: int, book_stop: float, X: float, groups: dict):
    """d sorted by tod, symbol. Returns (accepted mask, list of (exit_tod, r) realized curve)."""
    st = d["setup"].to_numpy(); sy = d["symbol"].to_numpy(); sd = d["side_i"].to_numpy()
    td = d["tod"].to_numpy(); xt = d["exit_tod"].to_numpy(); rr = d["r"].to_numpy()
    tk = [twin_key(s, groups) for s in st]
    acc = np.zeros(len(d), bool)
    open_ = []                      # (exit_tod, idx)
    lots = defaultdict(list)        # symbol -> [(setup, side, twin, idx)]
    open_by = defaultdict(int)
    real_by = defaultdict(float)
    stopped = set()
    real = 0.0; peak = 0.0; since = {1: 0.0, -1: 0.0}; braked = set(); halted = False
    clus = defaultdict(int)
    curve = []

    def close_until(t):
        nonlocal real, peak, open_
        keep = []
        for e in sorted(open_):
            et, j = e
            if et <= t:
                real += rr[j]; real_by[st[j]] += rr[j]; open_by[st[j]] -= 1
                lots[sy[j]] = [x for x in lots[sy[j]] if x[3] != j]
                curve.append((et, real))
                if rule.get("S") and real_by[st[j]] <= -rule["S"]:
                    stopped.add(st[j])
                if real > peak:
                    peak = real; since[1] = since[-1] = 0.0
                else:
                    since[sd[j]] += rr[j]
                if rule.get("G3") and peak >= X and real <= (1 - rule["G3"]) * peak:
                    w = min(since, key=since.get)
                    if since[w] < 0:
                        braked.add(w)
            else:
                keep.append(e)
        open_ = keep

    for i in range(len(d)):
        close_until(td[i])
        if halted or real <= -book_stop:
            halted = True; continue
        s = st[i]
        if s in stopped:
            continue
        if rule.get("SO") and real_by[s] - open_by[s] <= -rule["SO"]:
            continue
        if sd[i] in braked:
            continue
        if rule.get("G2") and clus[(s, td[i])] >= rule["G2"]:
            continue
        if open_by[s] >= cap:
            continue
        L = lots[sy[i]]
        if L:
            if rule.get("G1"):
                continue
            if any(x[1] != sd[i] for x in L):
                continue
            if any(x[0] != s and x[2] == tk[i] for x in L):
                continue
            if len(L) >= 3:
                continue
        acc[i] = True
        clus[(s, td[i])] += 1
        open_by[s] += 1
        L.append((s, sd[i], tk[i], i))
        open_.append((xt[i], i))
    close_until(10 ** 6)
    return acc, curve


def gb_stats(par_days: dict, X: float):
    gb, sw, worst, pk = [], 0, [], 0
    for dte, cur in par_days.items():
        vals = [v for _, v in cur]
        peak = max([0.0] + vals); close = vals[-1] if vals else 0.0
        gb.append(peak - close); worst.append(close)
        if peak >= X:
            pk += 1
            sw += close <= 0
    gb = np.array(gb) if gb else np.zeros(1)
    return {"gb_mean": round(float(gb.mean()), 3), "gb_p90": round(float(np.percentile(gb, 90)), 2),
            "peak_days": pk, "swing_days": int(sw), "worst_day": round(float(min(worst)), 2) if worst else None}


def main():
    sig = load_sig(None)
    sig["side_i"] = np.where(sig["setup"].map(U["side"]) == "long", 1, -1)
    ex = pd.read_parquet(sys.argv[1])          # exits.py output: simulated exit bar per cached signal
    ex["date"] = pd.to_datetime(ex["date"]).dt.date
    sig = sig.merge(ex[["setup", "symbol", "date", "tod", "exit_sim"]].drop_duplicates(["setup", "symbol", "date", "tod"]),
                    on=["setup", "symbol", "date", "tod"], how="left")
    sig["exit_tod"] = sig["exit_tod"].fillna(sig["exit_sim"]).fillna(1555)
    if LOCK is not None:                       # late_lock.py output: R per signal under each late profit lock
        lk = pd.read_parquet(LOCK); lk["date"] = pd.to_datetime(lk["date"]).dt.date
        sig = sig.merge(lk.drop_duplicates(["setup", "symbol", "date", "tod"]), on=["setup", "symbol", "date", "tod"],
                        how="left")
        for k in ("L1500", "L1430"):
            sig[k] = sig[k].fillna(sig["r"])
    rows = []
    for book, (ak, ck, cap, bstop, X) in BOOKS.items():
        members = [s for s in ASG[ak] if s in U.index]
        groups = twin_groups(account_cfg(ck))
        s = sig[sig["setup"].isin(members)].sort_values(["date", "tod", "symbol", "setup"]).reset_index(drop=True)
        days = {dte: g for dte, g in s.groupby("date", sort=True)}
        base = None
        for name, rule in configs(book):
            acc = np.zeros(len(s), bool); curves = {}
            for dte, g in days.items():
                if rule.get("L"):
                    g = g.assign(r=g[rule["L"]])
                a, c = sim_day(g, rule, cap, bstop, X, groups)
                acc[g.index.to_numpy()] = a; curves[dte] = c
            if name == "B0":
                base = (acc.copy(), curves)
            r = {"book": book, "cfg": name, "setups": len(members)}
            for sp in ("train", "valid", "all"):
                m = np.ones(len(s), bool) if sp == "all" else (s["split"].to_numpy() == sp)
                par = s[m & base[0]]; var = s[m & acc]
                if rule.get("L"):
                    var = var.assign(r=var[rule["L"]])
                r[f"{sp}_n"] = int(len(var)); r[f"{sp}_kept"] = round(100 * len(var) / max(1, len(par)), 1)
                r[f"{sp}_avgR"] = round(float(var.r.mean()), 4) if len(var) else None
                r[f"{sp}_sumR"] = round(float(var.r.sum()), 1)
                dd = day_delta(var[["date", "r"]], par[["date", "r"]])
                r[f"{sp}_delta"], r[f"{sp}_t"] = dd["delta"], dd["t"]
                dsel = set(s.loc[m, "date"])
                r.update({f"{sp}_{k}": v for k, v in gb_stats({k2: v2 for k2, v2 in curves.items() if k2 in dsel},
                                                             X).items()})
            for reg in ("up", "down"):
                m = s["regime"].to_numpy() == reg
                v = s[m & acc]
                if rule.get("L"):
                    v = v.assign(r=v[rule["L"]])
                r[f"{reg}_delta"] = day_delta(v[["date", "r"]], s[m & base[0]][["date", "r"]])["delta"]
            rows.append(r)
            print(book, name, {k: r[k] for k in ("train_n", "train_avgR", "valid_n", "valid_avgR", "all_delta", "all_t",
                                                  "train_gb_mean", "valid_gb_mean")}, flush=True)
    R = pd.DataFrame(rows)

    def verdict(x):
        if x.cfg == "B0":
            return "baseline"
        b = R[(R.book == x.book) & (R.cfg == "B0")].iloc[0]
        nh = (x.train_kept >= 85 and x.valid_kept >= 85 and x.train_delta >= 0 and x.valid_delta >= 0
              and x.up_delta >= -0.005 and x.down_delta >= -0.005
              and x.train_gb_mean < b.train_gb_mean and x.valid_gb_mean < b.valid_gb_mean)
        if nh and x.train_delta > 0 and x.valid_delta > 0 and (x.all_t or 0) >= BAR:
            return "pass"
        return "no-harm" if nh else "fail"
    R["verdict"] = R.apply(verdict, axis=1)
    R.to_csv(HERE / "book_sim.csv", index=False)
    pd.set_option("display.width", 300); pd.set_option("display.max_columns", 60)
    print(f"\nconfigs scored (non-baseline): {int((R.cfg != 'B0').sum())}; bar {BAR} (lineage N {N_LINEAGE})")
    cols = ["book", "cfg", "train_n", "train_kept", "train_avgR", "valid_n", "valid_kept", "valid_avgR", "train_delta",
            "valid_delta", "all_t", "up_delta", "down_delta", "train_gb_mean", "valid_gb_mean", "valid_gb_p90",
            "train_peak_days", "train_swing_days", "valid_peak_days", "valid_swing_days", "valid_worst_day", "verdict"]
    print(R[cols].to_string(index=False))
    print("\nEducational only - not financial advice.")


if __name__ == "__main__":
    main()
