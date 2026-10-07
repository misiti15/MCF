"""Autopsy of heat_fade_long (regime_5) and orb-style longs on the lab frame: which metrics separate winners
from losers? Train + valid only. Educational only - not financial advice.
    python research/primitives/escalation/autopsy.py
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lab import Split, evaluate, ROOT  # noqa: E402
import importlib.util

spec = importlib.util.spec_from_file_location("regime_5", ROOT / "research/heat/candidates/regime_5.py")
R5 = importlib.util.module_from_spec(spec); spec.loader.exec_module(R5)

FEATS = ["rsi", "rsi5", "momentum", "emaDiff", "macdPct", "volumeRatio", "volumeSurge", "pricePosition", "vwapDistPct",
         "vwap_atr", "buyPressure", "rsiSlope", "gap", "fromOpen", "fo_atr", "tod", "atr_d", "dist_pdh_atr", "dist_pdl_atr",
         "dist_hod_atr", "dist_lod_atr", "sma20_dist_pct", "sma50_dist_pct", "sma20_slope_pct", "flow3", "flow9prev",
         "flowflip", "vol_climax", "bear_div", "bull_div", "upper_wick", "lower_wick", "heat"]


class DF(dict):
    def __getitem__(self, k):
        return _W(dict.__getitem__(self, k))


class _W:
    def __init__(self, a): self.a = a
    def to_numpy(self, dtype=None): return self.a.astype(dtype) if dtype else self.a


def auc(x, y):
    ok = np.isfinite(x)
    x, y = x[ok], y[ok]
    if y.sum() == 0 or (1 - y).sum() == 0:
        return float("nan")
    rk = np.argsort(np.argsort(x)).astype(float) + 1
    n1 = y.sum(); n0 = len(y) - n1
    return float((rk[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def autopsy(S, idx, side, geom, label):
    r = S.r[(side, geom)][idx].astype(float)
    y = (r > 0).astype(int)
    rows = {}
    for f in FEATS:
        x = S.c[f][idx].astype(float)
        a = auc(x, y)
        q = np.nanquantile(x, [0.33, 0.67])
        lo, mid, hi = x <= q[0], (x > q[0]) & (x <= q[1]), x > q[1]
        rows[f] = {"auc": round(a, 3), "win_mean": round(float(np.nanmean(x[y == 1])), 3),
                   "lose_mean": round(float(np.nanmean(x[y == 0])), 3),
                   "tercile_exp_r": [round(float(np.nanmean(r[s])), 3) for s in (lo, mid, hi)],
                   "tercile_cut": [round(float(v), 3) for v in q]}
    return {"label": label, "n": len(idx), "exp_r": round(float(r.mean()), 4), "win_share": round(float(y.mean()), 3), "features": rows}


def main():
    out = {}
    for name in ("train", "valid"):
        S = Split(name)
        import pandas as pd
        d = pd.DataFrame({k: S.c[k] for k in ("rsiHeat", "priceActionHeat", "momentumHeat", "vwapHeat", "fromOpen", "gap", "atr_d", "tod")})
        sc = R5.score(d)
        m = np.nan_to_num(sc, nan=-1e9) >= R5.LONG_AT
        idx = S.first_idx(m & np.isfinite(S.r[("long", "t1s1")]))
        out[f"heat_fade_long_{name}"] = {"eval": evaluate(S, m, "long", "t1s1"), **autopsy(S, idx, "long", "t1s1", "regime_5")}
        # the mirror: same signal traded SHORT
        out[f"heat_fade_long_as_short_{name}"] = {"eval": evaluate(S, m, "short", "t1s1")}
        # first-hour orb-style longs: new high of day, above vwap, volumeRatio>1.5, 09:50-11:30
        c = S.c
        orb = (c["tod"] >= 950) & (c["tod"] <= 1130) & (c["dist_hod_atr"] <= 0.02) & (c["vwapDistPct"] > 0) & (c["volumeRatio"] > 1.5) & (c["fromOpen"] > 0)
        idx2 = S.first_idx(orb & np.isfinite(S.r[("long", "t1s1")]))
        out[f"orb_style_long_{name}"] = {"eval": evaluate(S, orb, "long", "t1s1"), **autopsy(S, idx2, "long", "t1s1", "orb-style")}
        del S, d
    (Path(__file__).resolve().parent / "autopsy.json").write_text(json.dumps(out, indent=1, default=float))
    for k, v in out.items():
        print(k, v["eval"])
        if "features" in v:
            fs = sorted(v["features"].items(), key=lambda kv: -abs((kv[1]["auc"] if kv[1]["auc"] == kv[1]["auc"] else .5) - .5))[:12]
            for f, s in fs:
                print("   ", f, s["auc"], "W", s["win_mean"], "L", s["lose_mean"], "terciles", s["tercile_exp_r"], s["tercile_cut"])


if __name__ == "__main__":
    main()
