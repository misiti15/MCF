"""swing1022 runner: score every pre-declared configuration (PLAN.md) for a group.

    python run.py idx|lev|stk [stage2]
Writes <scratch>/trades_<group>_<stage>.parquet (every trade + its random-day control) and
research/bdi/swing1022/results_<group>_<stage>.csv. Educational only - not financial advice."""
from __future__ import annotations

import json
import os
import sys
import zlib
from itertools import combinations
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prep as PR  # noqa: E402
from prep import HERE, assert_open, split_of  # noqa: E402
import sw_engine as E  # noqa: E402

import lib  # noqa: E402  (research/history2y, on sys.path via reddit1021 common)
from mcf.research import gates  # noqa: E402

SCR = Path(os.environ.get("SW22SCR", "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/sw1022"))
SCR.mkdir(parents=True, exist_ok=True)
TYPES = {0: "BR", 1: "REJ"}
GROUP_SYMS = {"idx": ["SPY", "QQQ"], "lev": ["SPXL", "TQQQ"]}


def one_knob(t: int, ext_ok: bool):
    v = [("N1", dict(n=1)), ("N3", dict(n=3)),
         ("lev+PD", dict(levpd=1)), ("lev+RN", dict(levrn=1)), ("lev+SW", dict(levsw=1))]
    if t == 0:
        v += [("tol0", dict(tol=0.0)), ("tol0.25", dict(tol=0.25)), ("M2", dict(m=2)), ("M8", dict(m=8))]
    else:
        v += [("rej_touch", dict(rejmode=1)), ("rej_wick0.1", dict(rejmode=2)), ("nrej2", dict(nrej=2)),
              ("nrej4", dict(nrej=4))]
    v += [("limit", dict(entry=1)),
          ("tgt_fix1.5R", dict(tmode=1, tmult=1.5)), ("tgt_fix2R", dict(tmode=1, tmult=2.0)),
          ("tgt_fix3R", dict(tmode=1, tmult=3.0)), ("tgt_first>=2R", dict(tmode=2, tmult=2.0)),
          ("tgt_next>=1.5R", dict(tmode=0, tmult=1.5)),
          ("sbuf0", dict(sbuf=0.0)), ("sbuf0.25", dict(sbuf=0.25)), ("fullday", dict(khi=21)),
          ("vol1.0", dict(vol=1.0)), ("vol1.5", dict(vol=1.5)), ("trend_vwap", dict(trend=1)),
          ("trend_open", dict(trend=2)), ("long_only", dict(side=1)), ("short_only", dict(side=-1)),
          ("fresh", dict(fresh=1)), ("choch_only", dict(choch=1)), ("bos_only", dict(choch=2))]
    if ext_ok:
        v += [("ext_swings", dict(src="ext"))]
    return v


FAMILY = {"N1": "N", "N3": "N", "lev+PD": "levpd", "lev+RN": "levrn", "lev+SW": "levsw", "tol0": "tol",
          "tol0.25": "tol", "M2": "M", "M8": "M", "rej_touch": "rej", "rej_wick0.1": "rej", "nrej2": "nrej",
          "nrej4": "nrej", "limit": "entry", "tgt_fix1.5R": "tgt", "tgt_fix2R": "tgt", "tgt_fix3R": "tgt",
          "tgt_first>=2R": "tgt", "tgt_next>=1.5R": "tgt", "sbuf0": "sbuf", "sbuf0.25": "sbuf", "fullday": "win",
          "vol1.0": "vol", "vol1.5": "vol", "trend_vwap": "trend", "trend_open": "trend", "long_only": "side",
          "short_only": "side", "fresh": "fresh", "choch_only": "choch", "bos_only": "choch", "ext_swings": "src"}


def base_configs(group):
    ext_ok = group in ("idx", "lev")
    out = []
    for t in (0, 1):
        pre = f"{TYPES[t]}-primary"
        out.append((pre, "primary", dict(type_=t)))
        for tag, kw in one_knob(t, ext_ok):
            out.append((f"{pre}+{tag}", "variant", dict(type_=t, **kw)))
    return out


def stage2_configs(group):
    R = pd.read_csv(HERE / f"results_{group}_s1.csv")
    ext_ok = group in ("idx", "lev")
    out = []
    for t in (0, 1):
        pre = f"{TYPES[t]}-primary"
        p = R[R.cfg == pre].iloc[0]
        knobs = dict(one_knob(t, ext_ok))
        cand = []
        for tag in knobs:
            r = R[R.cfg == f"{pre}+{tag}"]
            if not len(r) or not np.isfinite(r.iloc[0].get("train_exp", np.nan)):
                continue
            r = r.iloc[0]
            if r.train_n >= 0.3 * p.train_n and r.train_exp - p.train_exp >= 0.02:
                cand.append((r.train_exp - p.train_exp, tag))
        cand.sort(reverse=True)
        top, seen = [], set()
        for g, tag in cand:
            if FAMILY[tag] in seen:
                continue
            seen.add(FAMILY[tag]); top.append(tag)
        top = top[:3]
        combos = list(combinations(top, 2)) + ([tuple(top)] if len(top) == 3 else [])
        for cb in combos:
            kw = dict(type_=t)
            for tag in cb:
                kw.update(knobs[tag])
            out.append((f"{pre}+" + "+".join(cb), "stage2", kw))
    return out


SPY = None


def spy_trend(z, spy):
    """SPY close vs its session VWAP / vs its open at each 15m close, aligned to z's days."""
    tv = np.nan_to_num(np.sign(spy["f_c"] - spy["f_vwap"]))
    to = np.nan_to_num(np.sign(spy["f_c"] - spy["f_o"][:, :1]))
    idx = {d: i for i, d in enumerate(spy["days"])}
    ov = np.zeros_like(z["f_c"]); oo = np.zeros_like(z["f_c"])
    for i, d in enumerate(z["days"]):
        j = idx.get(d)
        if j is not None:
            ov[i] = tv[j]; oo[i] = to[j]
    return ov, oo


def run_cfgs(z, sym, cfgs, elig, ncontrol, seed):
    days = z["days"]
    sp = split_of(days)
    tv, to = spy_trend(z, SPY)
    rng = np.random.default_rng(seed)
    res = []
    for name, kind, kw in cfgs:
        kw = dict(kw)
        src = kw.pop("src", "rth")
        n = kw.get("n", 2)
        P = E.params(**kw)
        tr = E.run(P, z["start"], z["m_o"], z["m_h"], z["m_l"], z["m_c"], z["m_min"], z["f_o"], z["f_h"], z["f_l"],
                   z["f_c"], z["f_v"], z["f_atr"], z["f_v20"], z[f"SH_{src}{n}"], z[f"SL_{src}{n}"],
                   z[f"CH_{src}{n}"].astype(np.int64), z[f"FR_{src}{n}"].astype(np.int64), z[f"POI_{src}{n}"],
                   z["PD"], z["PM"], z["step"], z["tier"], elig, tv, to)
        if not len(tr):
            continue
        pick = np.full((len(tr), ncontrol), -1, np.int64)
        for s in ("train", "valid"):
            pool = np.flatnonzero((sp == s) & elig)
            for i in np.flatnonzero(sp[tr[:, 0].astype(int)] == s):
                cand = pool[pool != int(tr[i, 0])]
                if len(cand):
                    pick[i, :min(ncontrol, len(cand))] = rng.choice(cand, min(ncontrol, len(cand)), replace=False)
        ctl = E.control(tr, pick, z["start"], z["m_o"], z["m_h"], z["m_l"], z["m_c"], z["m_min"], z["tier"])
        df = pd.DataFrame(tr, columns=["d", "k", "side", "lev", "r", "gross", "kind", "fill_min", "rfrac", "entry",
                                       "exit_min", "cost", "tier", "tgt_r", "choch", "stop"])
        df["ctrl"] = ctl
        df["date"] = days[df.d.astype(int)]
        df["symbol"] = sym
        df["cfg"] = name
        res.append(df)
    return pd.concat(res) if res else None


def sym_job(args):
    sym, group, cfgs, ncontrol = args
    try:
        z = PR.prep_symbol(sym, with_ext=group in ("idx", "lev"))
    except Exception as e:  # noqa: BLE001
        print(sym, "prep failed", type(e).__name__, e, flush=True)
        return None
    if z is None:
        return None
    if group == "stk":
        adv = ADV.get(sym)
        if adv is None:
            return None
        a = np.array([adv.get(d, np.nan) for d in z["days"]], float)
        elig = np.nan_to_num(a) >= 95e6
        if not elig.any():
            return None
    else:
        elig = np.ones(len(z["days"]), bool)
    return run_cfgs(z, sym, cfgs, elig, ncontrol, zlib.crc32(sym.encode()))


ADV = None


def _init(spy, adv):
    global SPY, ADV
    SPY, ADV = spy, adv


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
            rows.append(row)
            continue
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
            row[f"{g}_n"] = len(u)
            row[f"{g}_exp"] = round(float(u.r.mean()), 4) if len(u) else np.nan
        mo = t.groupby(t.date.str[:7]).r.agg(["mean", "size"])
        mo = mo[mo["size"] >= 5]
        row["wf_share"] = round(float((mo["mean"] > 0).mean()), 3) if len(mo) else np.nan
        row["long_share"] = round(float((t.side > 0).mean()), 3)
        row["stop_share"] = round(float((t.kind == 1).mean()), 3)
        row["tgt_share"] = round(float((t.kind == 2).mean()), 3)
        row["avg_cost_r"] = round(float(t.cost.mean()), 4)
        row["avg_tgt_r"] = round(float(t.tgt_r.mean()), 3)
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    group = sys.argv[1]
    stage = "s2" if len(sys.argv) > 2 and sys.argv[2] == "stage2" else "s1"
    cfgs = base_configs(group) if stage == "s1" else stage2_configs(group)
    spy = PR.prep_symbol("SPY", with_ext=False)
    adv = None
    if group == "stk":
        syms = [s for s in (PR.R21SCR / "stk_syms.txt").read_text().split() if s not in ("SPY", "QQQ")]
        if os.environ.get("SW22_LIMIT"):
            syms = syms[: int(os.environ["SW22_LIMIT"])]
        d = lib.daily()
        d = d[d.symbol.isin(syms)]
        adv = {s: dict(zip(g.date.astype(str), g.adv20)) for s, g in d.groupby("symbol")}
        ncontrol = 20
    else:
        syms = GROUP_SYMS[group]
        ncontrol = 60
    jobs = [(s, group, cfgs, ncontrol) for s in syms]
    parts = []
    with Pool(4, initializer=_init, initargs=(spy, adv)) as pool:
        for i, df in enumerate(pool.imap_unordered(sym_job, jobs, chunksize=2), 1):
            if df is not None:
                parts.append(df)
            if i % 100 == 0:
                print(i, len(syms), flush=True)
    T = pd.concat(parts, ignore_index=True)
    assert_open(T.date.unique())
    T.to_parquet(SCR / f"trades_{group}_{stage}.parquet")
    sp = split_of(spy["days"])
    n_sessions = {"train": int((sp == "train").sum()), "valid": int((sp == "valid").sum()), "all": len(sp)}
    S = summarise(T, cfgs, n_sessions, group)
    S.to_csv(HERE / f"results_{group}_{stage}.csv", index=False)
    if group != "stk":
        per = [summarise(T[T.symbol == s], cfgs, n_sessions, f"{group}-{s}") for s in syms]
        pd.concat(per).to_csv(HERE / f"results_{group}_per_ticker_{stage}.csv", index=False)
    json.dump({"group": group, "stage": stage, "configs": len(cfgs), "symbols": len(syms), "trades": len(T)},
              open(HERE / f"count_{group}_{stage}.json", "w"))
    pd.set_option("display.width", 250)
    print(S[["cfg", "train_n", "train_exp", "train_t", "valid_n", "valid_exp", "valid_t", "all_ctrl",
             "all_excess", "all_gross"]].to_string())


if __name__ == "__main__":
    main()
