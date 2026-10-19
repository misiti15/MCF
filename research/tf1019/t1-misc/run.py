"""tf1019/t1-misc runner (adapted from research/tf1019/primary/run.py): 14 Testing-1 setups x decision bars 1/3/5/10/15 min x {as-is, time-equivalent} (PLAN.md).
    python research/tf1019/t1-misc/te_build.py --out $S          # TE indicator columns (scratch)
    python research/tf1019/t1-misc/run.py --scratch $S           # trades -> $S/trades/*.parquet, results.csv here
Educational only - not financial advice."""
from __future__ import annotations

import argparse
import json
import sys
import types
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from mcf.research import gates  # noqa: E402
from mcf.research import timeframes as tf  # noqa: E402

HERE = Path(__file__).resolve().parent
FD = "research/bdi/fullday/"
SETUPS = {  # name: (module, window, min_adv) - config/account_testing.yaml (Testing 1) / config/default.yaml
    "NS1-FD": (FD + "NS1-rsidip-rsi5pop-long-FD.py", (950, 1500), 95e6),
    "NS2-FD": (FD + "NS2-sma50break-overbought-short-FD.py", (950, 1500), 95e6),
    "NS3-FD": (FD + "NS3-failed-vwap-reclaim-short-FD.py", (950, 1500), 95e6),
    "NS4-FD": (FD + "NS4-pm-vwap-reclaim-oversold-short-FD.py", (950, 1500), 95e6),
    "NS5-FD": (FD + "NS5-sma50-flush-oversold-long-FD.py", (950, 1500), 95e6),
    "MF1-FD": (FD + "MF1-945-flowsell-vwapup-FD.py", (950, 1500), 95e6),
    "MF2-FD": (FD + "MF2-open-rsimidhi-flowsell-FD.py", (950, 1500), 95e6),
    "MF3-FD": (FD + "MF3-open-flowsell-rsi5hi-FD.py", (950, 1500), 95e6),
    "MF4-FD": (FD + "MF4-h40-open-flowsell-FD.py", (950, 1500), 95e6),
    "MF5-FD": (FD + "MF5-flowsell-vwapup-rsi5hi-FD.py", (950, 1500), 95e6),
    "heat_fade_short": ("research/heat/candidates/regime_9.py", (950, 1030), 125e6),
    "heat_fade_long": ("research/heat/candidates/regime_5.py", (1105, 1330), 125e6),
    "heat_fade_short-FD": (FD + "heat_fade_short-FD.py", (950, 1500), 125e6),
    "heat_fade_long-FD": (FD + "heat_fade_long-FD.py", (950, 1500), 125e6),
}
N_TASK = 126
N_PRIMARY = 108  # tf1019/primary, same MF/NS lineages
PRIOR = {k: (82068 + N_PRIMARY if k.startswith("MF") else 81430 + N_PRIMARY if k.startswith("NS") else 19200 + 74056)
         for k in SETUPS}
TE_COLS = ["rsi", "rsi5", "buyPressure", "sma50_dist_pct", "heat", "rsiHeat", "momentumHeat", "priceActionHeat", "vwapHeat"]
LOOKBACK = {"rsi": 14, "rsi5": 5, "buyPressure": 19, "sma50_dist_pct": 50}


def load(path):
    """Lab module, or a heat formula wrapped as one (HeatStrategy: long >= LONG_AT / short <= SHORT_AT; stop 1R,
    target 1R, R = 0.25 x daily ATR -> geometry t1s1)."""
    mod = tf.load_module(path)
    if hasattr(mod, "mask"):
        return mod
    side = "long" if getattr(mod, "LONG_AT", None) is not None else "short"

    def mask(df):
        sc = mod.score(df)
        with np.errstate(invalid="ignore"):
            return (sc >= mod.LONG_AT) if side == "long" else (sc <= mod.SHORT_AT)
    return types.SimpleNamespace(SIDE=side, GEOM="t1s1", mask=mask)


S: Path = Path(".")


def te_module(mod, m: int):
    """mod with its mask evaluated on the time-equivalent indicator columns (te_<m>min/<month>.parquet)."""
    def mask(df):
        mos = sorted(set(pd.Series(df["date"]).astype(str).str[:7]))
        te = pd.concat([pd.read_parquet(S / f"te_{m}min" / f"{mo}.parquet") for mo in mos], ignore_index=True)
        te["date"] = pd.to_datetime(te["date"]).dt.date
        k = df[["symbol", "date", "tod"]].copy()
        k["tod"] = k["tod"].astype("int16")
        j = k.merge(te, on=["symbol", "date", "tod"], how="left")
        assert len(j) == len(df)
        d2 = df.copy()
        for c in TE_COLS:
            d2[c] = j[c].to_numpy()
        return mod.mask(d2)
    return types.SimpleNamespace(SIDE=mod.SIDE, GEOM=getattr(mod, "GEOM", "t1s1"), mask=mask)


def job(args):
    name, m, variant = args
    path, win, adv = SETUPS[name]
    mod = load(path)
    if variant == "te":
        mod = te_module(mod, m)
    t = tf.run_module_tf(mod, m, window=win, split="open", symbols="core", min_adv=adv)
    t.to_parquet(S / "trades" / f"{name}_{m}_{variant}.parquet", index=False)
    return name, m, variant, len(t)


def summarize_all():
    reg = tf.regimes()
    rows = []
    for name in SETUPS:
        n_lin = PRIOR[name] + N_TASK
        for m in tf.MINUTES:
            for variant in ("asis", "te"):
                if variant == "te" and m == 5:
                    continue
                t = pd.read_parquet(S / "trades" / f"{name}_{m}_{variant}.parquet")
                s = tf.summarize(t, n_lin, reg)
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
                lb = {k: (v if variant == "asis" or m == 5 else max(2, round(v * 5 / m))) for k, v in LOOKBACK.items()}
                rows.append({"setup": name, "minutes": m, "variant": variant, "n": o.get("n", 0),
                             "exp_r": o.get("exp_r"), "t": o.get("t"), "win": o.get("win_rate"),
                             "n_train": tr.get("n", 0), "exp_train": tr.get("exp_r"), "t_train": tr.get("t"),
                             "n_valid": va.get("n", 0), "exp_valid": va.get("exp_r"), "t_valid": va.get("t"),
                             "n_fwd": fw.get("n", 0), "exp_fwd": fw.get("exp_r"),
                             "ctrl": rnd.get("ctrl_exp_r"), "excess": rnd.get("excess_exp_r"), "excess_t": rnd.get("excess_t"),
                             "up_n": rg.get("up", {}).get("n"), "up_r": rg.get("up", {}).get("exp_r"),
                             "down_n": rg.get("down", {}).get("n"), "down_r": rg.get("down", {}).get("exp_r"),
                             "regime_pass": s.get("regime_pass"), "wf_share": s.get("walk_forward", {}).get("share_positive"),
                             "n_lineage": n_lin, "t_required": s["t_required"], "t_family": gates.t_required(N_TASK),
                             "rsi_lookback_min": lb["rsi"] * m, "sma50_lookback_min": lb["sma50_dist_pct"] * m,
                             "bp_lookback_min": lb["buyPressure"] * m,
                             "pass_all": not fails, "fails": "; ".join(fails)})
    r = pd.DataFrame(rows)
    r.to_csv(HERE / "results.csv", index=False)
    return r


def main():
    global S
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--summarize-only", action="store_true")
    ap.add_argument("--only", default=None, help="asis or te: run only that variant (jobs already on disk are kept)")
    a = ap.parse_args()
    S = Path(a.scratch)
    if not a.summarize_only:
        (S / "trades").mkdir(exist_ok=True)
        jobs = [(n, m, v) for m in (1, 3, 5, 10, 15) for n in SETUPS for v in ("asis", "te") if not (v == "te" and m == 5)]
        assert len(jobs) == N_TASK
        if a.only:
            jobs = [j for j in jobs if j[2] == a.only]
            jobs = [j for j in jobs if not (S / "trades" / f"{j[0]}_{j[1]}_{j[2]}.parquet").exists()]
        with Pool(a.workers, initializer=_init, initargs=(str(S),)) as p:
            for res in p.imap_unordered(job, jobs):
                print(*res, flush=True)
    if a.only:
        return
    r = summarize_all()
    print(r[["setup", "minutes", "variant", "n", "exp_train", "exp_valid", "t", "excess", "regime_pass", "wf_share",
             "pass_all"]].to_string())
    print(json.dumps({"configs": len(r), "pass": int(r.pass_all.sum())}))


def _init(s):
    global S
    S = Path(s)


if __name__ == "__main__":
    main()
