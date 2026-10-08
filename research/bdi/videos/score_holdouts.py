"""ONE-TIME locked-holdout scoring of the 10 video-digest rules (VID1-VID8 as committed + 2 extra passers), lead-authorized
2026-10-08. No tuning: the modules, rules and exits are used exactly as committed. Educational only - not financial advice.

Holdouts: test 2026-09-16..10-05 (data/cache/1Min, timestamps < 2026-10-06) and q2 2026-04-01..06-30 (data/cache_q2/1Min,
< 2026-07-01). Features are built with the research code (build.one / build2.one: 40 prior 5-minute bars, prior-session and
prior-week 1-minute bars from the same cache) and joined to the locked lab frames.
Costs: lab geometries use research/owner1008/score_holdouts.py `prod`; structural exits (tx, avw) use build.py's
1-minute simulator (1c + 1 bps per side, +2c on stops; tx exits at the 15:55 bar open and pays exit costs).
Usage: python research/bdi/videos/score_holdouts.py <lock dir>"""
import importlib.util
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import build  # noqa: E402
import build2  # noqa: E402
from vid_rules import layer, trig  # noqa: E402

HOLD = {"test": dict(cache="data/cache/1Min", cut="2026-10-06", first="2026-09-16", frame="test.parquet"),
        "q2": dict(cache="data/cache_q2/1Min", cut="2026-07-01", first="2026-04-01", frame="holdout_q2.parquet")}
EXTRA = {
    "X1-pwr-pwl-gap_with-dsma20_with-short-pm-t1s1": dict(fam="PWR", var={"anchor": "pwl", "delta": "any"}, params={"d": 30},
                                                          layers=["gap_with", "dsma20_with"], window=(1130, 1500), side="short", exit="t1s1"),
    "X2-avf-pdhv-20-rvol15-gap_with-short-all-avw": dict(fam="AVF", var={"anchor": "pdhv", "k": 2.0}, params={},
                                                         layers=["rvol15", "gap_with"], window=(950, 1500), side="short", exit="avw"),
}
GEOMK = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5)}


def setup(h):
    c = HOLD[h]
    build.CACHE = Path(c["cache"])
    build.CUT = pd.Timestamp(c["cut"], tz="America/New_York")
    build.FIRST = build2.FIRST = pd.Timestamp(c["first"]).date()
    build.OUT = HERE / "data" / f"hold_{h}" / "parts"
    build2.OUT = HERE / "data" / f"hold_{h}" / "parts2"


def work(args):
    h, path = args
    setup(h)
    try:
        build.one(path)
        build2.one(path)
        m = build.load_symbol(path)
    except Exception as e:  # noqa: BLE001
        return {"err": f"{path.stem}: {e}"}
    g = m.groupby(m.index.date).agg(o=("open", "first"), c=("close", "last"))
    g = g[g.index >= build.FIRST]
    return {"o2c": ((g.c / g.o - 1) * 100).tolist(), "dates": [str(d) for d in g.index]}


def frame(h, lock):
    keys = ["symbol", "date", "tod"]
    cols = keys + ["close", "rsi5", "buyPressure", "gap", "vwapDistPct", "volumeRatio", "dist_pdh_atr", "dist_pdl_atr", "atr_d"] + \
        [f"{a}_{s}_{g}" for a in ("r", "win") for s in ("long", "short") for g in GEOMK]
    lab = pd.read_parquet(Path(lock) / HOLD[h]["frame"], columns=cols).sort_values(keys).reset_index(drop=True)
    lab["date"] = pd.to_datetime(lab["date"]).dt.date
    out = []
    for sub in ("parts", "parts2"):
        dset = ds.dataset(str(HERE / "data" / f"hold_{h}" / sub), format="parquet")
        skip = ("bk", "bp", "x_long_", "x_short_blk", "sw", "rtL_", "airU", "airD")
        t = dset.to_table(columns=[c for c in dset.schema.names if not c.startswith(skip) or c.startswith("swS_")])
        x = t.to_pandas()
        x["date"] = pd.to_datetime(x["date"]).dt.date
        out.append(x)
    df = lab
    for x in out:
        df = df.merge(x, on=keys, how="left", suffixes=("", f"_dup"))
    miss = int(df["c5"].isna().sum())
    df = df[df["c5"].notna()].reset_index(drop=True)
    return df, miss


def prod(df, side, geom, idx):
    up, dn = GEOMK[geom]
    R = 0.25 * df["atr_d"].to_numpy()[idx]
    px = df["close"].to_numpy()[idx]
    lab = df[f"r_{side}_{geom}"].to_numpy()[idx]
    win = df[f"win_{side}_{geom}"].to_numpy()[idx] == 1
    gross = lab + 0.02 / R
    stop = (~win) & (gross <= -dn + 1e-6)
    cost = (0.01 + px * 1e-4) + np.where(win, 0.0, 0.01 + px * 1e-4) + np.where(stop, 0.02, 0.0)
    return gross - cost / R


def outcome(df, side, ex, anchor=None):
    if ex in GEOMK:
        return None
    if ex == "avw":
        return df[f"x_{side}_avw_{anchor}"].to_numpy(float)
    return df[f"x_{side}_{ex}"].to_numpy(float)


def stats(df, m, side, ex, anchor=None):
    x = outcome(df, side, ex, anchor)
    fin = np.isfinite(df[f"r_{side}_{ex}"].to_numpy(float)) if x is None else np.isfinite(x)
    idx = np.flatnonzero(np.asarray(m, bool) & fin)
    if not len(idx):
        return {"n": 0}
    key = df["symbol"].astype(str).to_numpy()[idx] + "|" + df["date"].astype(str).to_numpy()[idx]
    _, first = np.unique(key, return_index=True)
    idx = np.sort(idx[first])
    r = prod(df, side, ex, idx) if x is None else x[idx]
    d = df["date"].astype(str).to_numpy()[idx]
    g = pd.DataFrame({"d": d, "r": r}).groupby("d")["r"].agg(["sum", "size"])
    mu = r.mean()
    se = np.sqrt(((g["sum"] - g["size"] * mu) ** 2).sum()) / len(r)
    b = g["sum"].idxmax()
    exb = (g["sum"].sum() - g.loc[b, "sum"]) / max(1, len(r) - g.loc[b, "size"]) if len(g) > 1 else np.nan
    return {"n": int(len(r)), "days": int(len(g)), "win_rate": round(float((r > 0).mean()), 3), "exp_r": round(float(mu), 4),
            "t": round(float(mu / se), 2) if se > 0 else None, "ex_best_day": round(float(exb), 4),
            "green_days": round(float((g["sum"] > 0).mean()), 3)}


def load_mod(p):
    sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location(p.stem.replace("-", "_"), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


if __name__ == "__main__":
    lock = sys.argv[1]
    res, meta = {}, {}
    for h in HOLD:
        hf = sorted(Path(HOLD[h]["cache"]).glob("*.parquet"))
        if not (HERE / "data" / f"hold_{h}" / "parts").exists():
            o2c = []
            with Pool(4) as p:
                for k, r in enumerate(p.imap_unordered(work, [(h, f) for f in hf], chunksize=2)):
                    if "err" in r:
                        print("ERR", r["err"], flush=True)
                    else:
                        o2c += list(zip(r["dates"], r["o2c"]))
                    if k % 100 == 0:
                        print(h, k, len(hf), flush=True)
            pd.DataFrame(o2c, columns=["date", "o2c"]).to_parquet(HERE / "data" / f"hold_{h}" / "o2c.parquet")
        df, miss = frame(h, lock)
        o2c = pd.read_parquet(HERE / "data" / f"hold_{h}" / "o2c.parquet")
        sd = df.groupby(["symbol", "date"]).first()
        nopw = int(sd["av_pwh"].isna().sum())
        meta[h] = {"rows": int(len(df)), "lab_rows_without_features": miss, "sessions": int(df.date.nunique()),
                   "symbol_days": int(len(sd)), "symbol_days_without_prior_week_anchor (excluded for pwh/pwl rules)": nopw,
                   "median_open_to_close_pct (all symbol-days)": round(float(o2c.o2c.median()), 3),
                   "median_of_daily_median_open_to_close_pct": round(float(o2c.groupby("date").o2c.median().median()), 3),
                   "share_of_sessions_with_negative_median_o2c": round(float((o2c.groupby("date").o2c.median() < 0).mean()), 3)}
        tod = df.tod.to_numpy()
        allw = (tod >= 950) & (tod <= 1500)
        meta[h]["baseline_short_tx_random"] = round(float(np.nanmean(df["x_short_tx"].to_numpy()[allw])), 4)
        bi = np.flatnonzero(allw & np.isfinite(df["r_short_t1s1"].to_numpy()))
        meta[h]["baseline_short_t1s1_random"] = round(float(prod(df, "short", "t1s1", bi).mean()), 4)
        pm = (tod >= 1130) & (tod <= 1500)
        meta[h]["baseline_short_tx_random_pm"] = round(float(np.nanmean(df["x_short_tx"].to_numpy()[pm])), 4)
        bi = np.flatnonzero(pm & np.isfinite(df["r_short_t1s1"].to_numpy()))
        meta[h]["baseline_short_t1s1_random_pm"] = round(float(prod(df, "short", "t1s1", bi).mean()), 4)
        D = {k: df[k].to_numpy() for k in df.columns if k not in ("symbol", "date")}
        for p in sorted(HERE.glob("VID*.py")):
            mod = load_mod(p)
            m = mod.mask(df)
            res.setdefault(p.stem, {})[h] = stats(df, m, mod.SIDE, mod.EXIT, mod.SPEC["var"].get("anchor"))
            print(h, p.stem, res[p.stem][h], flush=True)
        for nm, sp in EXTRA.items():
            s = -1 if sp["side"] == "short" else 1
            m = np.asarray(trig(D, sp["fam"], s, sp["var"], sp["params"], sp["exit"]), bool)
            for ly in sp["layers"]:
                m &= np.asarray(layer(D, ly, s), bool)
            m &= (tod >= sp["window"][0]) & (tod <= sp["window"][1])
            res.setdefault(nm, {})[h] = stats(df, m, sp["side"], sp["exit"], sp["var"].get("anchor"))
            print(h, nm, res[nm][h], flush=True)
    for k, v in res.items():
        ok = all((v[h].get("t") or 0) >= 1.0 and v[h].get("exp_r", -1) > 0 and (v[h].get("ex_best_day") or -1) > 0 for h in HOLD)
        v["passes_look1"] = bool(ok)
    json.dump({"meta": meta, "rules": res}, open(HERE / "holdouts.json", "w"), indent=1, default=str)
    print(json.dumps(meta, indent=1))
