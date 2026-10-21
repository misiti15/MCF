"""reddit1021 runner: score every pre-declared configuration (PLAN.md) for a group.

    python run.py idx [stage2]
    python run.py stk [stage2]
Writes <scratch>/trades_<group>_<stage>.parquet (every trade, with its random-day control) and appends rows to
research/bdi/reddit1021/results_<group>_<stage>.csv. Educational only - not financial advice."""
from __future__ import annotations

import json
import zlib
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

from common import HERE, SCR, assert_open, split_of
import engine as E

import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

PREP = SCR / "prep"
FAMS = ["OR", "PM", "AH", "PD", "SW"]
TYPES = {0: "C", 1: "R"}


def base_configs():
    out = []
    for t in (0, 1):
        for fib in (0.5, 0.618):
            for m in (1.5, 2.0, 3.0):
                for ex in (0, 1):
                    out.append((f"{TYPES[t]}-f{fib}-t{m}-{'eod' if ex == 0 else 'ts1130'}", "base",
                                dict(type_=t, fib=fib, mult=m, exit_=ex)))
    for t in (0, 1):
        pre = f"{TYPES[t]}-f0.5-t2.0-eod"
        v = [(f"fam{FAMS[i]}", dict(fammask=1 << i)) for i in range(5)]
        v += [("vol_off", dict(vol=0)), ("vol_1.5x", dict(vol=2)), ("vol_avg20", dict(vol=3))]
        v += [("trend_vwap", dict(trend=1)), ("trend_ema20", dict(trend=2)), ("any_level", dict(fresh=0)),
              ("first_only", dict(first=1)), ("tb_0950_1015", dict(klo=3, khi=8)), ("tb_1020_1045", dict(klo=9, khi=14)),
              ("tb_1050_1130", dict(klo=15, khi=23)), ("k1.0", dict(k=1.0)), ("k2.0", dict(k=2.0)),
              ("touch_fill", dict(entry=1)), ("market_close", dict(entry=2)), ("lab_5mclose", dict(entry=3))]
        for tag, kw in v:
            out.append((f"{pre}+{tag}", "variant", dict(type_=t, **kw)))
    return out


KNOBS = {"vol_off": dict(vol=0), "vol_1.5x": dict(vol=2), "vol_avg20": dict(vol=3), "trend_vwap": dict(trend=1),
         "trend_ema20": dict(trend=2), "any_level": dict(fresh=0), "first_only": dict(first=1), "k1.0": dict(k=1.0),
         "k2.0": dict(k=2.0)}
KGROUP = {"vol_off": "vol", "vol_1.5x": "vol", "vol_avg20": "vol", "trend_vwap": "trend", "trend_ema20": "trend",
          "any_level": "fresh", "first_only": "first", "k1.0": "k", "k2.0": "k"}


def stage2_configs(group):
    """Pre-declared stage 2: knobs (volume, trend, freshness, first-of-day, k) whose one-knob variant raised TRAIN avg
    R by >= 0.02 over the primary with >= 30% of its trades; top 4 by train gain (at most one per knob family); all
    pairs + the all-4 combination."""
    from itertools import combinations
    R = pd.read_csv(HERE / f"results_{group}_s1.csv")
    out = []
    for t in (0, 1):
        pre = f"{TYPES[t]}-f0.5-t2.0-eod"
        p = R[R.cfg == pre].iloc[0]
        cand = []
        for tag in KNOBS:
            r = R[R.cfg == f"{pre}+{tag}"]
            if not len(r):
                continue
            r = r.iloc[0]
            if r.train_n >= 0.3 * p.train_n and r.train_exp - p.train_exp >= 0.02:
                cand.append((r.train_exp - p.train_exp, tag))
        cand.sort(reverse=True)
        top, seen = [], set()
        for g, tag in cand:
            if KGROUP[tag] in seen:
                continue
            seen.add(KGROUP[tag]); top.append(tag)
        top = top[:4]
        combos = list(combinations(top, 2)) + ([tuple(top)] if len(top) >= 3 else [])
        for cb in combos:
            kw = dict(type_=t)
            for tag in cb:
                kw.update(KNOBS[tag])
            out.append((f"{pre}+" + "+".join(cb), "stage2", kw))
    return out


def load(sym):
    z = np.load(PREP / f"{sym}.npz", allow_pickle=True)
    return {k: z[k] for k in z.files}


SPYT = None


def trend_arrays(z, spy):
    """+1 / -1 trend state at each 5m close: close vs session VWAP, close vs EMA20 (spy=None: own symbol)."""
    src = z if spy is None else spy
    tv = np.sign(src["f_c"] - src["f_vwap"])
    te = np.sign(src["f_c"] - src["f_ema20"])
    tv = np.nan_to_num(tv); te = np.nan_to_num(te)
    if spy is None:
        return tv, te
    idx = {d: i for i, d in enumerate(spy["days"])}
    out_v = np.zeros_like(z["f_c"]); out_e = np.zeros_like(z["f_c"])
    for i, d in enumerate(z["days"]):
        j = idx.get(d)
        if j is not None:
            out_v[i] = tv[j]; out_e[i] = te[j]
    return out_v, out_e


def sym_run(args):
    sym, group, cfgs, ncontrol = args
    z = load(sym)
    days = z["days"]
    sp = split_of(days)
    if group == "idx":
        elig = np.ones(len(days), bool)
        tv, te = trend_arrays(z, None)
    else:
        elig = np.nan_to_num(z["adv"]) >= 95e6
        tv, te = trend_arrays(z, SPYT)
    rng = np.random.default_rng(zlib.crc32(sym.encode()))
    res = []
    for name, kind, kw in cfgs:
        P = E.params(**kw)
        tr = E.run(P, z["start"], z["m_o"], z["m_h"], z["m_l"], z["m_c"], z["m_min"], z["LV"], z["tier"], elig,
                   z["f_o"], z["f_h"], z["f_l"], z["f_c"], z["f_v"], z["f_atr_prev"], z["f_ema20"], z["f_v20_prev"],
                   z["f_v_prev"], z["f_c_prev"], z["f_vwap"], tv, te)
        if not len(tr):
            continue
        # control days: other eligible sessions of the same split
        pick = np.full((len(tr), ncontrol), -1, np.int64)
        for s in ("train", "valid"):
            pool = np.flatnonzero((sp == s) & elig)
            for i in np.flatnonzero(sp[tr[:, 0].astype(int)] == s):
                cand = pool[pool != int(tr[i, 0])]
                if len(cand):
                    pick[i, :min(ncontrol, len(cand))] = rng.choice(cand, min(ncontrol, len(cand)), replace=False)
        ctl = E.control(tr, pick, z["start"], z["m_o"], z["m_h"], z["m_l"], z["m_c"], z["m_min"], z["tier"],
                        kw.get("mult", 2.0), kw.get("exit_", 0))
        df = pd.DataFrame(tr, columns=["d", "k", "side", "fam", "r", "gross", "kind", "fill_min", "rfrac", "entry",
                                       "exit_min", "cost", "tier", "rng_atr"])
        df["ctrl"] = ctl
        df["date"] = days[df.d.astype(int)]
        df["symbol"] = sym
        df["cfg"] = name
        res.append(df)
    return pd.concat(res) if res else None


def _init(spy):
    global SPYT
    SPYT = spy


def summarise(T: pd.DataFrame, cfgs, n_sessions: dict, group: str) -> pd.DataFrame:
    reg = lib.regimes()["regime"]
    reg = {str(k): v for k, v in reg.items()}
    rows = []
    kinds = {n: k for n, k, _ in cfgs}
    for name in [c[0] for c in cfgs]:
        t = T[T.cfg == name]
        row = {"group": group, "cfg": name, "kind": kinds[name]}
        if not len(t):
            row["all_n"] = 0
            rows.append(row); continue
        t = t.assign(split=split_of(t.date))
        for s in ("train", "valid", "all"):
            u = t if s == "all" else t[t.split == s]
            sm = gates.summary(u[["date", "r"]])
            row[f"{s}_n"] = sm.get("n", 0)
            row[f"{s}_exp"] = sm.get("exp_r", np.nan)
            row[f"{s}_t"] = sm.get("t", np.nan)
            row[f"{s}_win"] = sm.get("win_rate", np.nan)
            row[f"{s}_ctrl"] = round(float(u.ctrl.mean()), 4) if len(u) else np.nan
            row[f"{s}_excess"] = round(float((u.r - u.ctrl).mean()), 4) if len(u) else np.nan
            row[f"{s}_per_day"] = round(len(u) / n_sessions[s], 3)
            row[f"{s}_gross"] = round(float(u.gross.mean()), 4) if len(u) else np.nan
        sm = gates.summary(t[["date", "r"]])
        row["all_ex_best"] = sm.get("ex_best_day")
        row["green_days"] = sm.get("green_days")
        rg = t.date.map(lambda d: reg.get(str(d)))
        for g in ("up", "flat", "down"):
            u = t[rg == g]
            row[f"{g}_n"] = len(u); row[f"{g}_exp"] = round(float(u.r.mean()), 4) if len(u) else np.nan
        mo = t.groupby(t.date.str[:7]).r.agg(["mean", "size"])
        mo = mo[mo["size"] >= 5]
        row["wf_share"] = round(float((mo["mean"] > 0).mean()), 3) if len(mo) else np.nan
        row["long_share"] = round(float((t.side > 0).mean()), 3)
        row["stop_share"] = round(float((t.kind == 1).mean()), 3)
        row["tgt_share"] = round(float((t.kind == 2).mean()), 3)
        row["avg_cost_r"] = round(float(t.cost.mean()), 4)
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    group = sys.argv[1]
    stage = "s2" if len(sys.argv) > 2 and sys.argv[2] == "stage2" else "s1"
    cfgs = base_configs() if stage == "s1" else stage2_configs(group)
    if group == "idx":
        syms = ["SPY", "QQQ"]
        ncontrol = 60
        spy = None
    else:
        syms = sorted(p.stem for p in PREP.glob("*.npz") if p.stem not in ("SPY", "QQQ"))
        ncontrol = 20
        spy = load("SPY")
    jobs = [(s, group, cfgs, ncontrol) for s in syms]
    parts = []
    with Pool(4, initializer=_init, initargs=(spy,)) as pool:
        for i, df in enumerate(pool.imap_unordered(sym_run, jobs, chunksize=4), 1):
            if df is not None:
                parts.append(df)
            if i % 100 == 0:
                print(i, len(syms), flush=True)
    T = pd.concat(parts, ignore_index=True)
    assert_open(T.date.unique())
    T.to_parquet(SCR / f"trades_{group}_{stage}.parquet")
    # sessions per split (eligible symbol-days for STK, sessions for IDX)
    z = load("SPY")
    sp = split_of(z["days"])
    n_sessions = {"train": int((sp == "train").sum()), "valid": int((sp == "valid").sum()), "all": len(sp)}
    S = summarise(T, cfgs, n_sessions, group)
    S.to_csv(HERE / f"results_{group}_{stage}.csv", index=False)
    if group == "idx":
        per = []
        for sym in syms:
            s2 = summarise(T[T.symbol == sym], cfgs, n_sessions, f"idx-{sym}")
            per.append(s2)
        pd.concat(per).to_csv(HERE / f"results_idx_per_ticker_{stage}.csv", index=False)
    json.dump({"group": group, "stage": stage, "configs": len(cfgs), "symbols": len(syms), "trades": len(T)},
              open(SCR / f"count_{group}_{stage}.json", "w"))
    print(S[["cfg", "train_n", "train_exp", "train_t", "valid_n", "valid_exp", "valid_t", "all_excess"]].to_string())


if __name__ == "__main__":
    main()
