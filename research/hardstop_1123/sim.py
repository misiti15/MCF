"""hardstop_1123 step 2: one minute-by-minute simulator of the 4-setup Primary book (bench10 lots, cap 30, <= 3 lots per
symbol per setup, -2R per-setup latch on closed cost-R, burst brake 30/10 min, -20R account halt on closed + open) with
the 17 pre-registered rules of PLAN.md layered on. Writes per-day x setup R for every configuration.
Usage: python sim.py WORKDIR [cfg,cfg,...].  Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

W = Path(sys.argv[1])
SETUPS = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
          "NM-ETF-late-dip-di-long"]
SI = {s: i for i, s in enumerate(SETUPS)}

CFGS = {"base": {}}
CHECKS = {"repro": dict(nohalt=True)}   # bench10 reproduction check only (no halt, no brake); not a rule
for x in (6, 8, 10, 12):
    CFGS[f"A{x}"] = dict(acct_stop=x)
for x in (2, 3):
    CFGS[f"L{x}"] = dict(set_latch=x)
    CFGS[f"LF{x}"] = dict(set_latch=x, set_flat=True)
for x in (4, 6, 8):
    CFGS[f"N{x}"] = dict(no_new=x)
for x in (1, 2):
    for y in (0, 2, 4):
        CFGS[f"S{x}_{y}"] = dict(spy_x=x, open_y=y)

if __name__ == "__main__":
    C = pd.read_parquet(W / "cand.parquet")
    PATH = np.load(W / "paths.npy")
    SPY = pd.read_parquet(W / "spy.parquet")
    SPYD = {d: dict(zip(g.m.values, g.spy_pct.values)) for d, g in SPY.groupby("date")}
    C["si"] = C.setup.map(SI)
    C = C.sort_values(["date", "em", "si", "symbol"], kind="mergesort").reset_index(drop=True)
COLS = ["si", "symbol", "side", "entry", "risk", "tier", "ecost", "borrow", "em", "xm", "r", "off", "n"]


def sim_day(g, cfg, spy):
    rec = g[COLS].to_dict("records")
    by_m = {}
    for k, r in enumerate(rec):
        by_m.setdefault(r["em"], []).append(k)
    realized = np.zeros(4)
    lots_r = np.zeros(4)          # final R per setup
    nlots = np.zeros(4, int)
    open_ = []                    # indices into rec
    exit_r = {}
    halted = stopped = noentry = False
    latch = np.zeros(4, bool)
    recent = [[] for _ in range(4)]
    prev_open = 0.0               # sum of open marks at the close of m-1
    fire_m = None
    m0 = min(by_m)
    last_entry_m = max(by_m)

    def realize(m):
        nonlocal open_
        keep = []
        for k in open_:
            r = rec[k]
            if r["xm"] <= m:
                realized[r["si"]] += r["r"]
                exit_r[k] = r["r"]
            else:
                keep.append(k)
        open_ = keep

    def marks(m):
        out = []
        for k in open_:
            r = rec[k]
            j = min(m - r["em"], r["n"] - 1)
            c = float(PATH[r["off"] + j]) if r["n"] > 0 else r["entry"]
            out.append((r["side"] * (c - r["entry"]) - r["tier"] * (r["ecost"] + 0.01 + c * 1e-4) - r["borrow"]) / r["risk"])
        return np.array(out)

    for m in range(m0, 956):
        if m > last_entry_m and not open_:
            break
        for k in by_m.get(m, ()):
            realize(m)
            r = rec[k]
            s = r["si"]
            if halted or stopped or noentry or latch[s]:
                continue
            if realized[s] <= -2.0 + 1e-12:
                continue
            ops = [rec[q] for q in open_]
            if sum(1 for q in ops if q["si"] == s) >= 30:
                continue
            if sum(1 for q in ops if q["si"] == s and q["symbol"] == r["symbol"]) >= 3:
                continue
            recent[s] = [t for t in recent[s] if t > m - 10]
            if len(recent[s]) >= 30 and not cfg.get("nohalt"):
                continue
            if cfg.get("spy_x") is not None and r["side"] < 0:
                sp = spy.get(m - 1, np.nan) if spy else np.nan
                if sp == sp and sp > cfg["spy_x"] and prev_open < -cfg["open_y"]:
                    continue
            recent[s].append(m)
            nlots[s] += 1
            open_.append(k)
        realize(m)
        if not open_:
            prev_open = 0.0
            continue
        mk = marks(m)
        sis = np.array([rec[k]["si"] for k in open_])
        tot = realized.sum() + mk.sum()
        if tot <= -20.0 + 1e-12 and not cfg.get("nohalt"):
            halted = True
        flat = np.zeros(len(open_), bool)
        if cfg.get("acct_stop") and not stopped and tot <= -cfg["acct_stop"] + 1e-12:
            stopped, flat[:] = True, True
            fire_m = fire_m or m
        if cfg.get("no_new") and not noentry and tot <= -cfg["no_new"] + 1e-12:
            noentry = True
            fire_m = fire_m or m
        if cfg.get("set_latch"):
            for s in range(4):
                if latch[s]:
                    continue
                v = realized[s] + mk[sis == s].sum()
                if v <= -cfg["set_latch"] + 1e-12:
                    latch[s] = True
                    fire_m = fire_m or m
                    if cfg.get("set_flat"):
                        flat |= sis == s
        if flat.any():
            keep = []
            for k, f, v in zip(open_, flat, mk):
                if f:
                    realized[rec[k]["si"]] += v
                    exit_r[k] = v
                else:
                    keep.append(k)
            open_ = keep
            mk = mk[~flat]
        prev_open = float(mk.sum())
    for k in open_:
        realized[rec[k]["si"]] += rec[k]["r"]
        exit_r[k] = rec[k]["r"]
    return realized, nlots, fire_m, exit_r


if __name__ == "__main__":
    want = sys.argv[2].split(",") if len(sys.argv) > 2 else list(CFGS)
    days = {d: g for d, g in C.groupby("date")}
    for name in want:
        cfg = {**CFGS, **CHECKS}[name]
        rows = []
        for d, g in days.items():
            R, N, fm, _ = sim_day(g, cfg, SPYD.get(d))
            for s in range(4):
                rows.append((name, d, SETUPS[s], R[s], N[s], fm))
        out = pd.DataFrame(rows, columns=["cfg", "date", "setup", "r", "lots", "fire_m"])
        out.to_csv(W / "runs" / f"{name}.csv.gz", index=False)
        print(name, round(out.r.sum(), 2), flush=True)
