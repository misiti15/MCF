"""tf1019/t2-cwt runner: 16 Testing-2 CWT04/05/09/12/13 setups x decision bars 1/3/5/10/15 min x {as-is, TE} (PLAN.md).
    python research/tf1019/t2-cwt/run.py --scratch $S --parity   # kernels vs cwt_live_lib at parent parameters
    python research/tf1019/t2-cwt/run.py --scratch $S            # trades -> $S/trades/*.parquet, results.csv here
Educational only - not financial advice."""
from __future__ import annotations

import argparse
import json
import math
import sys
import types
from multiprocessing import Pool
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/bdi/cwt/live"))
sys.path.insert(0, str(ROOT / "research/swarm1017/rework-cwt"))
import cwt_live_lib as L  # noqa: E402
import kern as K  # noqa: E402  (numba ports, parity-checked in research/swarm1017/rework-cwt/parity.json)
from mcf.research import gates  # noqa: E402
from mcf.research import timeframes as tf  # noqa: E402

HERE = Path(__file__).resolve().parent
LIVE = "research/bdi/cwt/live/"
# name: (kernel, params, side, geom, window, min_adv, lineage)
SETUPS = {
    "CWT04-backside-lh-a25-short": ("b1", dict(a=2.5, trig=2), "short", "t1s1", (1030, 1500), 95e6, "B1"),
    "CWT04-backside-lh-a15-short": ("b1", dict(a=1.5, trig=2), "short", "t1s1", (1030, 1500), 95e6, "B1"),
    "CWT04-backside-vwaptest-a25-short": ("b1", dict(a=2.5, trig=1), "short", "t1s1", (950, 1500), 95e6, "B1"),
    "CWT04-backside-vwaptest-a15-short": ("b1", dict(a=1.5, trig=1), "short", "t1s05", (950, 1500), 95e6, "B1"),
    "CWT05-flush-m075-v5-long": ("b5", dict(m=0.75, v=5), "long", "t05s1", (950, 1500), 95e6, "B5"),
    "CWT05-flush-m05-v5-long": ("b5", dict(m=0.5, v=5), "long", "t05s1", (950, 1500), 95e6, "B5"),
    "CWT05-flush-m05-v3-long": ("b5", dict(m=0.5, v=3), "long", "t05s1", (950, 1500), 95e6, "B5"),
    "CWT05-flush-m075-v3-long": ("b5", dict(m=0.75, v=3), "long", "t05s1", (950, 1500), 95e6, "B5"),
    "CWT09-gapdn-vwaploss-g5-short": ("a7", dict(gap=5, trig=1), "short", "t1s05", (1030, 1500), 1e6, "A7"),
    "CWT12-coil-k4-long": ("b4a", dict(nco=4), "long", "t05s1", (950, 1130), 95e6, "B4"),
    "CWT12-coil-k6-long": ("b4a", dict(nco=6), "long", "t1s05", (950, 1130), 95e6, "B4"),
    "CWT12-flag-s1-long": ("b4b", dict(s=1.0), "long", "t05s1", (950, 1500), 95e6, "B4"),
    "CWT13-vwapstretch-z075-long": ("b2", dict(z=0.75, side="long"), "long", "t1s1", (950, 1500), 95e6, "B2"),
    "CWT13-vwapstretch-z05-long": ("b2", dict(z=0.5, side="long"), "long", "t05s1", (1100, 1500), 95e6, "B2"),
    "CWT13-vwapstretch-z075-short": ("b2", dict(z=0.75, side="short"), "short", "t1s1", (1100, 1500), 95e6, "B2"),
    "CWT13-vwapstretch-z05-short": ("b2", dict(z=0.5, side="short"), "short", "t1s1", (1100, 1500), 95e6, "B2"),
}
NOT_RUN = {n: "geometry S (structural stop) has no frame outcome" for n in
           ("CWT09-gapdn-bounce-g10-lowerhalf-short", "CWT09-gapdn-bounce-g5-lowerhalf-short",
            "CWT09-gapdn-vwaploss-g10-short")}
TE_KERNELS = ("b4a", "b5")
N_TASK = 104
PRIOR = {"B1": 389621, "B2": 18016, "B4": 32654, "B5": 47450, "A7": 99060}  # rework-cwt counts.json prior + swarm
N_LIN = {k: v + N_TASK for k, v in PRIOR.items()}


def rnd(x: float) -> int:
    return max(1, int(math.floor(x + 0.5)))


def te_params(kernel: str, m: int, base: dict) -> dict:
    """Bar-count parameters: as-is (5-min clock values in bars) or time-equivalent for minutes m."""
    if kernel == "b5":
        return dict(k6=rnd(30 / m), k3=rnd(15 / m))
    if kernel == "b4a":
        return dict(nco=rnd(base["nco"] * 5 / m), mrw=rnd(100 / m), warm=rnd(30 / m))
    return {}


ASIS = {"b5": dict(k6=6, k3=3), "b4a": dict(mrw=20, warm=6)}


@numba.njit(cache=True)
def b4a_g(new, c, h, l, hod, atr, nco, mrw, warm):
    """cwt_live_lib.b4a with the mean-range window (20) and warm-up (6) as parameters."""
    n = len(c)
    flag = np.zeros(n, np.bool_)
    s0 = 0
    for i in range(n):
        if new[i]:
            s0 = i
        if i - s0 + 1 < nco + warm:
            continue
        thr = hod[i] - 0.1 * atr[i]
        touches = 0
        for k in range(s0, i + 1):
            if h[k] >= thr:
                touches += 1
        if touches < 3:
            continue
        a = i - nco + 1
        m0 = max(s0, a - mrw)
        mr = 0.0
        for k in range(m0, a):
            mr += h[k] - l[k]
        mr = mr / (a - m0)
        ok = True
        lo = 1e18
        for k in range(a, i + 1):
            if not (h[k] - l[k] < 0.5 * mr and c[k] <= hod[i] and hod[i] - c[k] <= 0.25 * atr[i]):
                ok = False
                break
            lo = min(lo, l[k])
        if ok and lo < c[i]:
            flag[i] = True
    return flag


def mask_for(kernel: str, p: dict, extra: dict):
    def mask(df):
        if kernel == "b2":
            return L.b2(df, **p)
        if kernel == "a7":
            return L.a7(df, **p)
        x = L.arrays(df)
        if kernel == "b1":
            return K.b1k(x.new, x.c, x.h, x.l, x.vwap, x.open_d, x.atr, p["a"], 0.4, p["trig"])
        if kernel == "b4b":
            push, dep = K.b4bk(x.new, x.c, x.h, x.l, x.vwap, x.open_d, x.atr)
            with np.errstate(invalid="ignore"):
                return (push >= p["s"]) & (dep >= 0.3) & (dep <= 0.5)
        if kernel == "b4a":
            nco = extra.get("nco", p["nco"])
            return b4a_g(x.new, x.c, x.h, x.l, x.hod, x.atr, nco, extra["mrw"], extra["warm"])
        if kernel == "b5":
            k6, k3 = extra["k6"], extra["k3"]
            c6 = L.prev(x, x.c, k6)
            lodp = np.nan_to_num(L.prev(x, x.lod, 1), nan=-1e18)
            vc = np.nan_to_num(x.vc, nan=0.0)
            vc3 = vc.copy()
            for j in range(1, k3):
                vc3 = np.fmax(vc3, np.nan_to_num(L.prev(x, vc, j)))
            return K.b5k(x.new, x.c, x.h, c6, lodp, vc3, x.atr, p["m"], p["v"])
        raise ValueError(kernel)
    return mask


def make_mod(name, m, variant):
    kernel, p, side, geom = SETUPS[name][:4]
    extra = dict(ASIS.get(kernel, {})) if variant == "asis" else te_params(kernel, m, p)
    return types.SimpleNamespace(SIDE=side, GEOM=geom, mask=mask_for(kernel, p, extra)), extra


S: Path = Path(".")


def job(args):
    name, m, variant = args
    mod, _ = make_mod(name, m, variant)
    win, adv = SETUPS[name][4], SETUPS[name][5]
    t = tf.run_module_tf(mod, m, window=win, split="open", symbols="core", min_adv=adv)
    t.to_parquet(S / "trades" / f"{name}_{m}_{variant}.parquet", index=False)
    return name, m, variant, len(t)


def parity():
    """Our masks (as-is) == the live module masks (cwt_live_lib) on 2026-09 core frames: 5-min all 80, 1-min 8 symbols."""
    out = {}
    for m, syms in ((5, tf.universe("core")), (1, tf.universe("core")[:8]), (15, tf.universe("core")[:20])):
        df = tf.load_tf(m, "2026-09", symbols=syms)
        for name in SETUPS:
            live = tf.load_module(LIVE + name + ".py")
            assert live.SIDE == SETUPS[name][2] and live.GEOM == SETUPS[name][3], name
            a = np.asarray(live.mask(df), bool)
            b = np.asarray(make_mod(name, m, "asis")[0].mask(df), bool)
            out[f"{name}@{m}"] = {"rows": len(df), "live_true": int(a.sum()), "mismatch": int((a != b).sum())}
            assert (a == b).all(), (name, m, int((a != b).sum()))
    (HERE / "parity.json").write_text(json.dumps(out, indent=1))
    print("parity ok", len(out))


def summarize_all():
    reg = tf.regimes()
    rows = []
    for name, (kernel, p, side, geom, win, adv, lin) in SETUPS.items():
        for m in tf.MINUTES:
            for variant in ("asis", "te"):
                if variant == "te" and (m == 5 or kernel not in TE_KERNELS):
                    continue
                t = pd.read_parquet(S / "trades" / f"{name}_{m}_{variant}.parquet")
                s = tf.summarize(t, N_LIN[lin], reg)
                o, bs = s.get("overall", {}), s.get("by_split", {})
                rn, rg = s.get("random_same_minute", {}), s.get("regime", {})
                tr, va, fw = bs.get("train", {}), bs.get("valid", {}), bs.get("forward", {})
                fails = list(s.get("fails", [])) if o.get("n") else ["n=0"]
                if (tr.get("exp_r") or -1) <= 0:
                    fails.append("train exp<=0")
                if (va.get("exp_r") or -1) <= 0:
                    fails.append("valid exp<=0")
                if (rn.get("excess_exp_r") or -1) <= 0:
                    fails.append("excess vs random<=0")
                extra = make_mod(name, m, variant)[1]
                ndays = t["date"].nunique() if len(t) else 0
                rows.append({"setup": name, "lineage": lin, "geom": geom, "window": f"{win[0]}-{win[1]}",
                             "minutes": m, "variant": variant,
                             "bar_params": json.dumps(extra) if extra else "",
                             "n": o.get("n", 0), "per_day": round(o.get("n", 0) / max(1, ndays), 2),
                             "exp_r": o.get("exp_r"), "t": o.get("t"), "win": o.get("win_rate"),
                             "n_train": tr.get("n", 0), "exp_train": tr.get("exp_r"), "t_train": tr.get("t"),
                             "n_valid": va.get("n", 0), "exp_valid": va.get("exp_r"), "t_valid": va.get("t"),
                             "n_fwd": fw.get("n", 0), "exp_fwd": fw.get("exp_r"),
                             "ctrl": rn.get("ctrl_exp_r"), "excess": rn.get("excess_exp_r"), "excess_t": rn.get("excess_t"),
                             "up_n": rg.get("up", {}).get("n"), "up_r": rg.get("up", {}).get("exp_r"),
                             "down_n": rg.get("down", {}).get("n"), "down_r": rg.get("down", {}).get("exp_r"),
                             "regime_pass": s.get("regime_pass"), "wf_share": s.get("walk_forward", {}).get("share_positive"),
                             "n_lineage": N_LIN[lin], "t_required": s["t_required"],
                             "pass_all": not fails, "fails": "; ".join(fails)})
    r = pd.DataFrame(rows)
    assert len(r) == N_TASK, len(r)
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
        jobs = [(n, m, v) for m in (1, 3, 5, 10, 15) for n in SETUPS for v in ("asis", "te")
                if not (v == "te" and (m == 5 or SETUPS[n][0] not in TE_KERNELS))]
        assert len(jobs) == N_TASK, len(jobs)
        jobs = [j for j in jobs if not (S / "trades" / f"{j[0]}_{j[1]}_{j[2]}.parquet").exists()]
        with Pool(a.workers, initializer=_init, initargs=(str(S),)) as pool:
            for res in pool.imap_unordered(job, jobs):
                print(*res, flush=True)
    r = summarize_all()
    print(r[["setup", "minutes", "variant", "n", "exp_train", "exp_valid", "t", "t_required", "excess", "regime_pass",
             "wf_share", "pass_all"]].to_string())
    print(json.dumps({"configs": len(r), "pass": int(r.pass_all.sum())}))


if __name__ == "__main__":
    main()
