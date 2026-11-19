"""H5V volume-track hunt backtest (round5/hunt_volume/PLAN.md). Reuses the round-4 chassis (round4/ULT-28/bt.py walk +
LR8 cost_R with borrow on shorts), round4/ULT-32/bt.py (earnings blackout set, ULT-32 features for E/M overlap) and
round3/ULT-23/bt.py (stats).
    python hunt.py WORK sig fit|check ; python hunt.py WORK walk fit|check ; python hunt.py WORK fit|check
Halves: FIT = 2024-10 + 2025-03..09; CHECK = 2025-10-01..latest. Locked 2024-11-01..2025-02-28 never read.
Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
U1119 = HERE.parents[1]
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(U1119 / "benchmark"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "never reads the locked block"

_s = importlib.util.spec_from_file_location("ult32bt", U1119 / "round4" / "ULT-32" / "bt.py")
B32 = importlib.util.module_from_spec(_s)
sys.modules["ult32bt"] = B32
_s.loader.exec_module(B32)
B28 = B32.B28
B28.EXITS = {"T": (1.0, 1.0), "H": (0.5, 1.0)}       # (target, stop) in u, walked in the workers
B28.MS = (0.25,)
B23 = B28.B23
stats, no_locked, m2, hhmm, sha = B23.stats, B23.no_locked, B23.m2, B23.hhmm, B23.sha
DATA = B28.DATA
MOD = HERE / "H5V.py"
SYMF = HERE / "H5V_symbols.json"
DAY_CAP = 30
N_PRIOR = 996
N_GRID = 40
COLS = ["symbol", "date", "tod", "close", "rsi", "buyPressure", "fromOpen", "atr_d", "adv20", "gap", "vol_climax",
        "lower_wick"]
GEOM2X = {"t1s1": "T", "t05s1": "H"}


def load_mod(name="h5v"):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def configs():
    """40 pre-declared configs (PLAN.md): name -> (leg, params)."""
    c = {}
    for rm in (30.0, 35.0):
        for bp in (True, False):
            for g in ("t1s1", "t05s1"):
                c[f"F-r{rm:g}-bp{int(bp)}-{g}"] = ("F", dict(rmax=rm, bp=bp, geom=g))
    for a in (500e6, 1e9):
        for rm in (70.0, 75.0):
            for g in ("t1s1", "t05s1"):
                c[f"S-a{a / 1e6:.0f}-r{rm:g}-{g}"] = ("S", dict(adv=a, rmin=rm, geom=g))
    for a in (500e6, 1e9):
        for sp in (False, True):
            c[f"C-a{a / 1e6:.0f}-spy{int(sp)}-t1s1"] = ("C", dict(adv=a, spy=sp, geom="t1s1"))
    for r3 in (0.5, 0.75):
        for g in ("t05s1", "t1s1"):
            c[f"X-r{r3:g}-{g}"] = ("X", dict(ret3=r3, geom=g))
    for u in ("EQB", "LEV"):
        for k in (0.2, 0.3):
            for g in ("t1s1", "t05s1"):
                c[f"K-{u}-k{k:g}-{g}"] = ("K", dict(univ=u, k=k, geom=g))
    for vc in (2.0, 3.0):
        for g in ("t1s1", "t05s1"):
            c[f"V-vc{vc:g}-{g}"] = ("V", dict(vc=vc, geom=g))
    for k in (0.5, 0.75):
        for g in ("t1s1", "t05s1"):
            c[f"Q-k{k:g}-{g}"] = ("Q", dict(k=k, geom=g))
    assert len(c) == N_GRID
    return c


def flag(name):
    return "f_" + name.replace(".", "p")


# ---------------------------------------------------------------- stage 1: signal superset
def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = DATA
    mod = load_mod()
    m32 = B32.load_mod()
    f = lib.load_month(month, context=True)
    f = f[[c for c in f.columns if not (c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower()
                                        or c.startswith("breadth") or c == "qqq_vwap")]].copy()
    assert not any(c.startswith(("win_", "r_long", "r_short", "breadth")) or "heat" in c.lower() for c in f.columns)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    no_locked(f["date"].unique())
    r = mod.features(f)
    fl = {}
    for name, (leg, p) in configs().items():
        fl[name] = mod.leg_mask(r, leg, p)
    # BOOK-EM legs for the overlap diagnostic (frozen ULT-32 module, 32e parameters)
    r32 = m32.features(f, adv_md=500e6)
    e32 = m32.leg_mask(r32, "E")
    mm32 = m32.leg_mask(r32, "M", rmax=30.0)
    out = []
    cf = configs()
    for side in (1, -1):
        names = [n for n, (lg, _) in cf.items() if (mod.SIDES[lg] == "long") == (side > 0)]
        mk = np.zeros(len(f), bool)
        for n in names:
            mk |= fl[n]
        s = f.loc[mk, ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap"]].copy()
        s["side"] = side
        for n in names:
            s[flag(n)] = fl[n][mk]
        s["cost_r"] = r["cost_r"][mk]
        out.append(s)
    S = pd.concat(out, ignore_index=True)
    # E / M symbol-sessions (any bar) for the overlap diagnostic
    em = f.loc[e32 | mm32, ["symbol", "date"]].drop_duplicates()
    days = sorted(str(x) for x in set(lib.load_context(month)["date"]))
    return month, S, em, days


def leg_of(name):
    return name.split("-", 1)[0]


# ---------------------------------------------------------------- stage 3: selection
def bind(S, g):
    k = "25" + g
    T = S.copy()
    T["r"], T["kd"], T["xmin"], T["r_sigclose"], T["r_u"] = T["r" + k], T["kd" + k], T["xmin" + k], T["rsc" + k], T["ru" + k]
    T["hold"] = T["xmin"] - m2(T.tod)
    T["exit"] = g
    return T


def select(S, name, cap=DAY_CAP):
    leg, p = configs()[name]
    m = S[flag(name)].fillna(False).to_numpy(bool) if flag(name) in S else np.zeros(len(S), bool)
    if leg in ("S", "C", "V"):
        m &= ~S.blackout.to_numpy(bool)
    T = bind(S[m], GEOM2X[p["geom"]])
    T["leg"] = leg
    return B32.chain(T, cap)


KEYS = B32.KEYS


def short(o):
    return {k: o.get(k) for k in KEYS + ("trades", "t_day_clustered")}


def random_control(sel, leg, seed=1119):
    rng = np.random.default_rng(seed)
    mod = load_mod()
    lo, hi = mod.WIN[leg]
    R = sel[["symbol", "date", "atr_d", "close", "tod", "adv20", "side"]].copy()
    R["evt"] = 0
    R["tod"] = [int(hhmm(rng.choice(np.arange(m2(lo), m2(hi) + 1, 5)))) for _ in range(len(R))]
    Wk = B28.walk(R, random=True)
    return bind(Wk, sel["exit"].iloc[0])


def rand_block(t, leg):
    Rc = random_control(t, leg)
    ok = Rc.r.notna().to_numpy() & t.r.notna().to_numpy()
    tr, rr = t.r.to_numpy()[ok], Rc.r.to_numpy()[ok]
    return {"random_avg_r": round(float(rr.mean()), 4), "signal_minus_random": round(float(tr.mean() - rr.mean()), 4),
            "random_n": int(ok.sum())}


def overlap(t, em):
    k = set(zip(em.symbol, em.date))
    return round(float(np.mean([(a, b) in k for a, b in zip(t.symbol, t.date)])), 3) if len(t) else None


def load_half(work, half):
    S = pd.read_parquet(Path(work) / f"walked_{half}.parquet")
    no_locked(S.date.unique())
    days = pd.read_parquet(Path(work) / f"days_{half}.parquet").date.tolist()
    no_locked(days)
    em = pd.read_parquet(Path(work) / f"em_{half}.parquet")
    return S, len(days), em


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[2]
    if stage in ("sig", "walk") and sys.argv[3] == "check":
        assert (HERE / "fitsel.json").exists(), "freeze fitsel.json before any check data is built"
        fs = json.loads((HERE / "fitsel.json").read_text())
        assert sha(MOD) == fs["sha256_module"] and sha(__file__) == fs["sha256_hunt"], "frozen files changed"
    if stage == "sig":
        half = sys.argv[3]
        sigs, ems, days = [], [], []
        with Pool(2) as p:
            for m, s, em, d in p.imap_unordered(month_job, B28.half_months(half)):
                print(m, len(s), int((s.side > 0).sum()), int((s.side < 0).sum()), flush=True)
                sigs.append(s); ems.append(em); days += d
        S = pd.concat(sigs, ignore_index=True)
        no_locked(S.date.unique()); no_locked(days)
        etb = B28.etb_set()
        S = S[(S.side > 0) | S.symbol.isin(etb)].reset_index(drop=True)      # shorts: easy-to-borrow only
        bo = B32.blackout_set()
        S["blackout"] = [(a, b) in bo for a, b in zip(S.symbol, S.date)]
        S.to_parquet(W / f"sig_{half}.parquet")
        pd.concat(ems, ignore_index=True).to_parquet(W / f"em_{half}.parquet")
        pd.DataFrame({"date": sorted(days)}).to_parquet(W / f"days_{half}.parquet")
    elif stage == "walk":
        half = sys.argv[3]
        S = pd.read_parquet(W / f"sig_{half}.parquet")
        S["evt"] = 0
        t0 = time.time()
        T = B28.walk(S)
        T.to_parquet(W / f"walked_{half}.parquet")
        print("walked", len(T), int(T.r25T.isna().sum()), "no path", round(time.time() - t0), "s")
    elif stage == "fit":
        S, n, em = load_half(W, "fit")
        res = {}
        for name in configs():
            t = select(S, name)
            o = stats(t, n)
            o["uncapped_trades"] = int(len(select(S, name, cap=0)))
            o["overlap_EM_symbol_session"] = overlap(t, em)
            res[name] = o
            print(f"{name:24s} n={o['trades']:5d} /s={o['trades_per_session']:.2f} avg={o.get('avg_r')} "
                  f"wo={o.get('avg_r_wo_best_day')} tot={o.get('total_r')} t={o.get('t_day_clustered')} "
                  f"ov={o['overlap_EM_symbol_session']}", flush=True)
        picks = {}
        for leg in "FSCXKVQ":
            names = [k for k in configs() if leg_of(k) == leg]
            best = max(names, key=lambda k: (res[k].get("total_r", -1e9) if res[k]["trades"] else -1e9, -names.index(k)))
            adv = res[best]["trades"] >= 15 and (res[best].get("total_r") or 0) > 0
            picks[leg] = {"pick": best, "params": configs()[best][1], "advance_to_check": bool(adv),
                          "fit": short(res[best])}
        (HERE / "fit_grid.json").write_text(json.dumps(res, indent=1, default=float))
        print(json.dumps({k: (v["pick"], v["advance_to_check"], v["fit"]["total_r"]) for k, v in picks.items()}, indent=1))
        (W / "picks_tmp.json").write_text(json.dumps(picks, indent=1, default=float))
    elif stage == "freeze":
        picks = json.loads((W / "picks_tmp.json").read_text())
        mod = load_mod()
        for leg, v in picks.items():
            assert mod.P[leg] == v["params"], f"set H5V.P[{leg}] to the fit pick first: {v['params']}"
        fs = {"note": "Educational only - not financial advice. H5V fit picks, frozen BEFORE any check data is built.",
              "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "picks": picks,
              "rule": "per leg: max FIT total R; advance if FIT total R > 0 and >= 15 trades (PLAN.md)",
              "sha256_module": sha(MOD), "sha256_hunt": sha(__file__), "sha256_symbols": sha(SYMF),
              "sha256_ult32_bt": sha(U1119 / "round4" / "ULT-32" / "bt.py"),
              "sha256_ult28_bt": sha(U1119 / "round4" / "ULT-28" / "bt.py"),
              "configs_counted_this_hunt": N_GRID, "n_cumulative_after": N_PRIOR + N_GRID}
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        print("frozen", fs["frozen_utc"])
    elif stage == "fitrandom":
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n, em = load_half(W, "fit")
        out = {}
        for leg, v in fs["picks"].items():
            t = select(S, v["pick"])
            if len(t):
                out[leg] = rand_block(t, leg)
                print(leg, out[leg], flush=True)
        (HERE / "fit_random.json").write_text(json.dumps(out, indent=1))
    elif stage == "check":
        fs = json.loads((HERE / "fitsel.json").read_text())
        assert not (HERE / "check_once.json").exists(), "check is scored once"
        S, n, em = load_half(W, "check")
        out = {"scored_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "legs": {}}
        trades = []
        for leg, v in fs["picks"].items():
            if not v["advance_to_check"]:
                continue
            t = select(S, v["pick"])
            o = stats(t, n)
            o["uncapped_trades"] = int(len(select(S, v["pick"], cap=0)))
            o["overlap_EM_symbol_session"] = overlap(t, em)
            o["random"] = rand_block(t, leg) if len(t) else None
            o["kept"] = bool(o.get("trades") and o["avg_r"] > 0 and (o.get("avg_r_wo_best_day") or -1) > 0)
            o["pick"] = v["pick"]
            out["legs"][leg] = o
            trades.append(t[["symbol", "date", "tod", "side", "leg", "exit", "r", "kd", "hold"]])
            print(leg, v["pick"], json.dumps(short(o), default=float), o["random"], "KEPT" if o["kept"] else "drop",
                  flush=True)
        (HERE / "check_once.json").write_text(json.dumps(out, indent=1, default=float))
        if trades:
            pd.concat(trades).to_csv(HERE / "check_trades.csv.gz", index=False)
