"""One-time locked-holdout scoring of the 10 owner-directed setups of 2026-10-08 (5 MarcoFlow, 5 NS). Production costs.
Reported for information: the owner directed deployment regardless. Educational only - not financial advice."""
import importlib.util, json, sys
from pathlib import Path
import numpy as np, pandas as pd
GEOMK = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5)}
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


LOCK = Path(sys.argv[1])
mods = sorted(Path("research/owner1008").glob("NS*.py")) + [Path(f"research/primitives/marcoflow/{m}.py") for m in (
    "MF-945-flowsell-vwapup", "MF-open-rsimidhi-flowsell", "MF-open-flowsell-rsi5hi", "MF-h40-open-flowsell", "MF-flowsell-vwapup-rsi5hi")]
frames = {}
for s in ("test", "holdout_q2"):
    f = pd.read_parquet(LOCK / f"{s}.parquet").sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
    f["date"] = pd.to_datetime(f["date"]).dt.date
    frames[s] = f
out = {}
for p in mods:
    spec = importlib.util.spec_from_file_location(p.stem.replace("-", "_"), p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    out[p.stem] = {s: score(df, m.mask(df), m.SIDE, m.GEOM) for s, df in frames.items()}
    print(p.stem, {s: {k: out[p.stem][s].get(k) for k in ("n", "exp_r", "t")} for s in out[p.stem]}, flush=True)
json.dump(out, open("research/owner1008/holdouts.json", "w"), indent=1, default=str)
