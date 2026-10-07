"""One-time locked-holdout scoring of the audited finalists of the primitives/escalation swarm (lead, 2026-10-07).
Each finalist is scored ONCE on each holdout (Sep 16-Oct 5 test, Apr-Jun 2026), lab outcomes restated at production
costs (entry 1c+1bps; exit 1c+1bps, +2c on stop exits, none on target fills). New lineages: look 1 -> t >= 1.0 on both.
Same-window random baseline for comparison. Educational only - not financial advice."""
import importlib.util, json, sys
from pathlib import Path
import numpy as np, pandas as pd

LOCK = Path(sys.argv[1]); ROOT = Path(".")
GEOMK = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5)}
MODS = [ROOT / "research/primitives/P1-gap_V1-short-W4-t1s1.py",
        *sorted((ROOT / "research/primitives/layering/finalists").glob("L*.py")),
        *[ROOT / f"research/primitives/escalation/finalists/{n}.py" for n in ("x_gapfade_early_b", "x_bottom_div", "x_vwaploss_run")]]
SKIP = {"L2-gapV1+sma20slopepctD10-short-W4-t1s1"}       # not confirmed by the audit


def load_mod(p):
    sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location(p.stem.replace("-", "_").replace("+", "_"), p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def prod(df, side, geom, idx):
    up, dn = GEOMK[geom]
    R = 0.25 * df["atr_d"].to_numpy()[idx]; px = df["close"].to_numpy()[idx]
    lab = df[f"r_{side}_{geom}"].to_numpy()[idx]; win = df[f"win_{side}_{geom}"].to_numpy()[idx] == 1
    gross = lab + 0.02 / R
    stop = (~win) & (gross <= -dn + 1e-6)
    cost = (0.01 + px * 1e-4) + np.where(win, 0.0, 0.01 + px * 1e-4) + np.where(stop, 0.02, 0.0)
    return gross - cost / R


def score(df, m, side, geom):
    m = np.asarray(m, bool) & np.isfinite(df[f"r_{side}_{geom}"].to_numpy())
    idx = np.flatnonzero(m)
    if not len(idx):
        return {"n": 0}
    key = df["symbol"].astype(str).to_numpy()[idx] + "|" + df["date"].astype(str).to_numpy()[idx]
    _, first = np.unique(key, return_index=True); idx = idx[first]
    r = prod(df, side, geom, idx); d = df["date"].astype(str).to_numpy()[idx]
    g = pd.DataFrame({"d": d, "r": r}).groupby("d")["r"].agg(["sum", "size"])
    mu = r.mean(); se = np.sqrt(((g["sum"] - g["size"] * mu) ** 2).sum()) / len(r)
    b = g["sum"].idxmax()
    return {"n": int(len(r)), "days": int(len(g)), "win_rate": round(float((r > 0).mean()), 3), "exp_r": round(float(mu), 4),
            "t": round(float(mu / se), 2) if se > 0 else None, "green_days": round(float((g["sum"] > 0).mean()), 3),
            "ex_best_day": round(float((g["sum"].sum() - g.loc[b, "sum"]) / max(1, len(r) - g.loc[b, "size"])), 4)}


out = {}
frames = {s: pd.read_parquet(LOCK / f"{s}.parquet") for s in ("test", "holdout_q2")}
for f in frames.values():
    f["date"] = pd.to_datetime(f["date"]).dt.date
for p in MODS:
    if p.stem in SKIP:
        continue
    mod = load_mod(p); res = {}
    for s, df in frames.items():
        res[s] = score(df, mod.mask(df), mod.SIDE, mod.GEOM)
    out[p.stem] = {"side": mod.SIDE, "geom": mod.GEOM, **res,
                   "passes": all(res[s].get("n", 0) > 0 and res[s]["exp_r"] > 0 and (res[s]["t"] or 0) >= 1.0 for s in res)}
    print(p.stem, json.dumps({s: {k: res[s].get(k) for k in ("n", "exp_r", "t", "ex_best_day")} for s in res}), "PASS" if out[p.stem]["passes"] else "fail", flush=True)
for s, df in frames.items():   # same-window random baselines
    tod = df["tod"].to_numpy()
    out.setdefault("_baseline", {})[s] = {"short_1300_1430_t1s1": score(df, (tod >= 1300) & (tod <= 1430), "short", "t1s1"),
                                          "short_0950_1030_t1s05": score(df, (tod >= 950) & (tod <= 1030), "short", "t1s05")}
print(json.dumps(out["_baseline"], indent=0))
json.dump(out, open("research/primitives/holdout/results.json", "w"), indent=1, default=str)
