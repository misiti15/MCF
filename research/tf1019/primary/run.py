"""tf1019/primary runner: the 12 Primary setups x decision bars 1/3/5/10/15 min x {as-is, time-equivalent} (PLAN.md).
    python research/tf1019/primary/te_build.py --out $S          # TE indicator columns (scratch)
    python research/tf1019/primary/run.py --scratch $S           # trades -> $S/trades/*.parquet, results.csv here
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
SETUPS = {  # name: (module, window) - config/default.yaml, Primary, enabled
    "MF1": ("research/primitives/marcoflow/MF-945-flowsell-vwapup.py", (950, 1030)),
    "MF2": ("research/primitives/marcoflow/MF-open-rsimidhi-flowsell.py", (950, 1100)),
    "MF3": ("research/primitives/marcoflow/MF-open-flowsell-rsi5hi.py", (950, 1100)),
    "MF4": ("research/primitives/marcoflow/MF-h40-open-flowsell.py", (950, 1100)),
    "MF5": ("research/primitives/marcoflow/MF-flowsell-vwapup-rsi5hi.py", (950, 1500)),
    "MF3-FD": ("research/bdi/fullday/MF3-open-flowsell-rsi5hi-FD.py", (950, 1500)),
    "RW3-FD": ("research/bdi/fullday/RW3-gapdn-rsi5pop-flowsell-short-FD.py", (950, 1500)),
    "RW5-FD": ("research/bdi/fullday/RW5-heat30-flowsell-rsi5pop-gapdn-short-FD.py", (950, 1500)),
    "NS1": ("research/owner1008/NS1-rsidip-rsi5pop-long.py", (950, 1130)),
    "NS4": ("research/owner1008/NS4-pm-vwap-reclaim-oversold-short.py", (1130, 1500)),
    "NS5": ("research/owner1008/NS5-sma50-flush-oversold-long.py", (950, 1130)),
    "RW6G1": ("research/bdi/live1009/RW6G1-ns2-up3-vwap2sd-short.py", (950, 1130)),
}
PRIOR = {"MF1": 82068, "MF2": 82068, "MF3": 82068, "MF4": 82068, "MF5": 82068, "MF3-FD": 82068, "RW3-FD": 82068,
         "RW5-FD": 82068, "NS1": 81430, "NS4": 81430, "NS5": 81430, "RW6G1": 81950}
N_TASK = 108
MIN_ADV = 95_000_000
TE_COLS = ["rsi", "rsi5", "buyPressure", "sma50_dist_pct", "heat"]
LOOKBACK = {"rsi": 14, "rsi5": 5, "buyPressure": 19, "sma50_dist_pct": 50}
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
    path, win = SETUPS[name]
    mod = tf.load_module(path)
    if variant == "te":
        mod = te_module(mod, m)
    t = tf.run_module_tf(mod, m, window=win, split="open", symbols="core", min_adv=MIN_ADV)
    t.to_parquet(S / "trades" / f"{name}_{m}_{variant}.parquet", index=False)
    return name, m, variant, len(t)


def split_te_months():
    for m in (1, 3, 10, 15):
        d = S / f"te_{m}min"
        if d.exists():
            continue
        d.mkdir()
        x = pd.read_parquet(S / f"te_{m}min.parquet")
        mo = pd.Series(x["date"]).astype(str).str[:7]
        for k, g in x.groupby(mo):
            g.to_parquet(d / f"{k}.parquet", index=False)
        (S / f"te_{m}min.parquet").unlink()


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
                             "n_lineage": n_lin, "t_required": s["t_required"], "t_family108": gates.t_required(N_TASK),
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
    a = ap.parse_args()
    S = Path(a.scratch)
    if not a.summarize_only:
        split_te_months()
        (S / "trades").mkdir(exist_ok=True)
        jobs = [(n, m, v) for m in (1, 3, 5, 10, 15) for n in SETUPS for v in ("asis", "te") if not (v == "te" and m == 5)]
        assert len(jobs) == N_TASK
        with Pool(a.workers, initializer=_init, initargs=(str(S),)) as p:
            for res in p.imap_unordered(job, jobs):
                print(*res, flush=True)
    r = summarize_all()
    print(r[["setup", "minutes", "variant", "n", "exp_train", "exp_valid", "t", "excess", "regime_pass", "wf_share",
             "pass_all"]].to_string())
    print(json.dumps({"configs": len(r), "pass": int(r.pass_all.sum())}))


def _init(s):
    global S
    S = Path(s)


if __name__ == "__main__":
    main()
