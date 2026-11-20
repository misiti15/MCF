"""Collect BEG-04 results -> results.json + printed tables and verdicts. Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
W = Path(sys.argv[1])
TH = {"comb_avg": -0.0383, "chk_avg": -0.0464, "comb_wo": -0.0674, "chk_wo": -0.0781, "comb_rps": -0.4862,
      "chk_rps": -0.5218, "t2_avg": -0.1048}


def L(p):
    f = W / p
    return json.loads(f.read_text()) if f.exists() else None


def legs(c, k, t2):
    v = {"comb_avg": c["avg_r"], "chk_avg": k["avg_r"], "comb_wo": c["avg_r_wo_best_day"],
         "chk_wo": k["avg_r_wo_best_day"], "comb_rps": c["total_r_per_session"], "chk_rps": k["total_r_per_session"],
         "t2_avg": t2["avg_r"]}
    gap = {x: round(v[x] - TH[x], 4) for x in TH}
    fails = {x: g for x, g in gap.items() if g < 0}
    enough = k["trades"] >= 20 and t2["trades"] >= 20
    tier = "MEETS" if not fails and enough else ("NEAR" if all(g >= -0.02 for g in fails.values()) else "FAIL")
    return tier, v, gap


def combine(fit, chk):
    """T1 combined from fit+check stats (trade-weighted avg; R/session over 446)."""
    n = fit["trades"] + chk["trades"]
    tot = fit["total_r"] + chk["total_r"]
    return {"trades": n, "avg_r": round(tot / n, 4), "total_r_per_session": round(tot / 446, 4)}


out = {}
base = L("res_base_all.json")
out["base"] = base
ctl = {}
for c in ("same", "univ"):
    rows = [L(f"res_base_rnd{s}{c}_all.json") for s in (1, 2, 3)]
    rows = [r for r in rows if r]
    if rows:
        ctl[c] = {k: {m: round(float(np.mean([r[k][m] for r in rows if k in r])), 4)
                      for m in ("trades", "avg_r", "avg_r_wo_best_day", "total_r_per_session")}
                  for k in ("T1_fit", "T1_check", "T1_combined", "T2")}
out["controls"] = ctl
tw = {v: L(f"res_{v}_fit.json") for v in json.loads((HERE / "variants.json").read_text())}
out["tweaks_fit"] = tw
for v, r in tw.items():
    if r:
        f = r["T1_fit"]
        print(f"{v:8s} FIT n {f['trades']} avg {f['avg_r']:+.4f} wo {f['avg_r_wo_best_day']:+.4f} rps "
              f"{f['total_r_per_session']:+.3f} t {f['t_day_clustered']} share {f['best_day_share']}")
tier, v, gap = legs(base["T1_combined"], base["T1_check"], base["T2"])
out["base_verdict"] = {"tier": tier, "values": v, "margin": gap}
print("BASE", tier, gap)
pick = (W / "pick.txt").read_text().strip() if (W / "pick.txt").exists() else None
if pick:
    ck, t2 = L(f"res_{pick}_check.json"), L(f"res_{pick}_t2.json")
    if ck and t2:
        comb = combine(tw[pick]["T1_fit"], ck["T1_check"])
        # w/o best day on combined needs the trade list
        import pandas as pd
        bk = pd.concat([pd.read_parquet(W / f"bk_{pick}_fit.parquet"), pd.read_parquet(W / f"bk_{pick}_check.parquet")])
        bk = bk[bk.test == "t1"]
        day = bk.groupby("date").r.sum()
        comb["avg_r_wo_best_day"] = round(float(bk.loc[bk.date != day.idxmax(), "r"].mean()), 4)
        comb["best_day_share"] = round(float(day.max() / day.sum()), 3) if day.sum() > 0 else None
        e = bk.r - bk.r.mean()
        comb["t_day_clustered"] = round(float(bk.r.mean() / (np.sqrt((e.groupby(bk.date).sum() ** 2).sum()) / len(bk))), 2)
        tier2, v2, gap2 = legs(comb, ck["T1_check"], t2["T2"])
        out["pick"] = {"name": pick, "T1_fit": tw[pick]["T1_fit"], "T1_check": ck["T1_check"], "T1_combined": comb,
                       "T2": t2["T2"], "tier": tier2, "values": v2, "margin": gap2}
        print("PICK", pick, tier2, gap2, comb)
(HERE / "results.json").write_text(json.dumps(out, indent=1, default=float))
print(json.dumps(ctl, indent=0))
