"""tf1019/t2-cwt14 runner: 11 Testing-2 CWT14-failbrk setups x decision bars 1/3/5/10/15 min x {as-is, TE} (PLAN.md).
    python research/tf1019/t2-cwt14/run.py --scratch $S     # trades -> $S/trades/*.parquet, results.csv here
Educational only - not financial advice."""
from __future__ import annotations

import argparse
import json
import math
import sys
import types
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/bdi/cwt/live"))
import cwt_live_lib as L  # noqa: E402
from mcf.research import gates  # noqa: E402
from mcf.research import timeframes as tf  # noqa: E402

HERE = Path(__file__).resolve().parent
LIVE = "research/bdi/cwt/live/"
#        name: (level, p, lowvol, side, window)
SETUPS = {
    "CWT14-failbrk-orl-p05-long": ("OR", 0.05, False, "long", (950, 1500)),
    "CWT14-failbrk-orl-p05-lowvol-long": ("OR", 0.05, True, "long", (950, 1500)),
    "CWT14-failbrk-orl-p10-long": ("OR", 0.10, False, "long", (950, 1200)),
    "CWT14-failbrk-orl-p10-lowvol-long": ("OR", 0.10, True, "long", (950, 1500)),
    "CWT14-failbrk-pdl-p05-long": ("PD", 0.05, False, "long", (950, 1500)),
    "CWT14-failbrk-pdl-p05-lowvol-long": ("PD", 0.05, True, "long", (950, 1500)),
    "CWT14-failbrk-pdl-p10-long": ("PD", 0.10, False, "long", (950, 1500)),
    "CWT14-failbrk-pdl-p10-lowvol-long": ("PD", 0.10, True, "long", (950, 1500)),
    "CWT14-failbrk-pdh-p05-lowvol-short": ("PD", 0.05, True, "short", (950, 1500)),
    "CWT14-failbrk-pdh-p10-lowvol-short": ("PD", 0.10, True, "short", (950, 1500)),
    "CWT14-failbrk-pdh-p10-short": ("PD", 0.10, False, "short", (950, 1200)),
}
MIN_ADV = 95e6
N_TASK = 99
N_PRIOR = 379935
N_LIN = N_PRIOR + N_TASK


def k_te(m: int) -> int:
    return max(1, int(math.floor(15 / m + 0.5)))


def b3k(df, level, p, lowvol, side, k=3):
    """cwt_live_lib.b3 with the reclaim window k bars as a parameter (k=3 == L.b3)."""
    x = L.arrays(df)
    upper = side == "short"
    if level == "PD":
        Lv = x.pdh if upper else x.pdl
        lo_ok = np.ones(x.n, bool)
    else:
        at10 = np.where(x.tod == 1000, x.hod if upper else x.lod, np.nan)
        Lv = pd.Series(at10).groupby(x.seg).ffill().to_numpy(float)
        lo_ok = x.tod >= 1005
    thr = (Lv + p * x.atr) if upper else (Lv - p * x.atr)
    beyond_a = (x.h >= thr) if upper else (x.l <= thr)
    inside_a = (x.c < Lv) if upper else (x.c > Lv)
    valid = lo_ok & ~np.isnan(Lv)
    vlow = x.vr < 1
    new, beyond_a, inside_a, valid, vlow = (a.tolist() for a in (x.new, beyond_a, inside_a, valid, vlow))
    flag = [False] * x.n
    inexc = stale = False
    st = 0
    v0 = False
    for i in range(x.n):
        if new[i]:
            inexc = stale = False
        if not valid[i]:
            continue
        beyond, inside = beyond_a[i], inside_a[i]
        if not inexc and not stale and beyond:
            inexc = True
            st = i
            v0 = vlow[i]
        if inexc:
            if inside:
                if i - st <= k and (not lowvol or v0):
                    flag[i] = True
                inexc = False
            elif i - st > k:
                inexc = False
                stale = True
        elif stale and inside:
            stale = False
    return np.array(flag, bool)


def make_mod(name, k):
    level, p, lowvol, side, _ = SETUPS[name]
    return types.SimpleNamespace(SIDE=side, GEOM="t05s1", mask=lambda df: b3k(df, level, p, lowvol, side, k))


S: Path = Path(".")


def job(args):
    name, m, variant = args
    k = 3 if variant == "asis" else k_te(m)
    win = SETUPS[name][4]
    t = tf.run_module_tf(make_mod(name, k), m, window=win, split="open", symbols="core", min_adv=MIN_ADV)
    t.to_parquet(S / "trades" / f"{name}_{m}_{variant}.parquet", index=False)
    return name, m, variant, len(t)


def parity():
    """b3k(k=3) == L.b3 (and == the live module's mask) on one month of 5- and 1-minute core frames."""
    for m in (5, 1):
        df = tf.load_tf(m, "2026-09", symbols=tf.universe("core"))
        for name, (level, p, lowvol, side, _) in SETUPS.items():
            mod = tf.load_module(LIVE + name + ".py")
            a = np.asarray(mod.mask(df), bool)
            b = b3k(df, level, p, lowvol, side, 3)
            assert (a == b).all(), (name, m, int((a != b).sum()))
    print("parity ok")


def summarize_all():
    reg = tf.regimes()
    rows = []
    for name in SETUPS:
        for m in tf.MINUTES:
            for variant in ("asis", "te"):
                if variant == "te" and m == 5:
                    continue
                t = pd.read_parquet(S / "trades" / f"{name}_{m}_{variant}.parquet")
                s = tf.summarize(t, N_LIN, reg)
                o, bs = s.get("overall", {}), s.get("by_split", {})
                rnd, rg = s.get("random_same_minute", {}), s.get("regime", {})
                tr, va, fw = bs.get("train", {}), bs.get("valid", {}), bs.get("forward", {})
                fails = list(s.get("fails", [])) if o.get("n") else ["n=0"]
                if (tr.get("exp_r") or -1) <= 0:
                    fails.append("train exp<=0")
                if (va.get("exp_r") or -1) <= 0:
                    fails.append("valid exp<=0")
                if (rnd.get("excess_exp_r") or -1) <= 0:
                    fails.append("excess vs random<=0")
                k = 3 if variant == "asis" else k_te(m)
                ndays = t["date"].nunique() if len(t) else 0
                rows.append({"setup": name, "minutes": m, "variant": variant, "reclaim_bars": k,
                             "reclaim_min": k * m, "vr_lookback_min": 20 * m, "n": o.get("n", 0),
                             "per_day": round(o.get("n", 0) / max(1, ndays), 2),
                             "exp_r": o.get("exp_r"), "t": o.get("t"), "win": o.get("win_rate"),
                             "n_train": tr.get("n", 0), "exp_train": tr.get("exp_r"), "t_train": tr.get("t"),
                             "n_valid": va.get("n", 0), "exp_valid": va.get("exp_r"), "t_valid": va.get("t"),
                             "n_fwd": fw.get("n", 0), "exp_fwd": fw.get("exp_r"),
                             "ctrl": rnd.get("ctrl_exp_r"), "excess": rnd.get("excess_exp_r"), "excess_t": rnd.get("excess_t"),
                             "up_n": rg.get("up", {}).get("n"), "up_r": rg.get("up", {}).get("exp_r"),
                             "down_n": rg.get("down", {}).get("n"), "down_r": rg.get("down", {}).get("exp_r"),
                             "regime_pass": s.get("regime_pass"), "wf_share": s.get("walk_forward", {}).get("share_positive"),
                             "n_lineage": N_LIN, "t_required": s["t_required"], "t_family": gates.t_required(N_TASK),
                             "pass_all": not fails, "fails": "; ".join(fails)})
    r = pd.DataFrame(rows)
    r.to_csv(HERE / "results.csv", index=False)
    return r


def _init(s):
    global S
    S = Path(s)


def main():
    global S
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--summarize-only", action="store_true")
    ap.add_argument("--parity", action="store_true")
    a = ap.parse_args()
    S = Path(a.scratch)
    if a.parity:
        parity()
        return
    if not a.summarize_only:
        (S / "trades").mkdir(exist_ok=True)
        jobs = [(n, m, v) for m in (1, 3, 5, 10, 15) for n in SETUPS for v in ("asis", "te") if not (v == "te" and m == 5)]
        assert len(jobs) == N_TASK
        jobs = [j for j in jobs if not (S / "trades" / f"{j[0]}_{j[1]}_{j[2]}.parquet").exists()]
        with Pool(a.workers, initializer=_init, initargs=(str(S),)) as pool:
            for res in pool.imap_unordered(job, jobs):
                print(*res, flush=True)
    r = summarize_all()
    print(r[["setup", "minutes", "variant", "n", "exp_train", "exp_valid", "t", "excess", "regime_pass", "wf_share",
             "pass_all"]].to_string())
    print(json.dumps({"configs": len(r), "pass": int(r.pass_all.sum())}))


if __name__ == "__main__":
    main()
