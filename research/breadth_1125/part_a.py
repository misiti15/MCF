"""BREADTH-1125 Part A: 4 breadth close-gates x {11:00, 12:00, 13:00}; thresholds fitted on FIT only (PREREG.md).
Usage: python research/breadth_1125/part_a.py BW   -> BW/part_a.json, BW/frozen_gate.json. Educational only - not financial advice."""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LOCK = ("2024-11-01", "2025-02-28")
TS = (1100, 1200, 1300)
MEAS = ["pct_vwap", "pct_open", "ad30", "upvol", "nhnl"]
QS = (0.3, 0.4, 0.5, 0.6, 0.7, 0.8)


def split(d):
    d = pd.Series(d).astype(str)
    fit = ((d >= "2024-10-01") & (d <= "2024-10-31")) | ((d >= "2025-03-01") & (d <= "2025-09-30"))
    chk = (d >= "2025-10-01") & (d <= "2026-11-04")
    t2 = (d >= "2023-01-03") & (d <= "2024-09-13")
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any()
    return np.where(fit, "FIT", np.where(chk, "CHECK", np.where(t2, "T2", "none")))


def bz(hits, n, p0):
    return (hits - n * p0) / math.sqrt(n * p0 * (1 - p0)) if n > 0 else float("nan")


def table(bw):
    br = pd.read_parquet(Path(bw) / "breadth.parquet")
    spy = pd.read_parquet(Path(bw) / "spy.parquet")
    x = br.merge(spy, on=["date", "T", "src"])
    x["split"] = split(x.date)
    x = x[(x.split != "none") & ((x.src == "T2") == (x.split == "T2"))]
    x = x.sort_values(["date", "T"])
    x["thrust"] = x.pct_vwap - x.groupby("date").pct_vwap.shift(12)          # 12 x 5 min = 60 min
    x = x[x["T"].isin(TS) & x.y_close_up.notna()].copy()
    x["y"] = x.y_close_up.astype(bool)
    for t in TS:
        f = (x["T"] == t) & (x.split == "FIT")
        for m in MEAS:
            mu, sd = x.loc[f, m].mean(), x.loc[f, m].std()
            x.loc[x["T"] == t, "z_" + m] = (x.loc[x["T"] == t, m] - mu) / sd
    x["Z"] = x[["z_" + m for m in MEAS]].mean(1)
    return x


GATES = {"GA": ("VWAP breadth", "pct_vwap", False), "GB": ("composite Z", "Z", False),
         "GC": ("breadth thrust 60m", "thrust", False), "GD": ("TT1 + composite Z", "Z", True)}


def on(df, g, th):
    _, col, tt = GATES[g]
    m = df[col] >= th
    return (m & df.TT1.astype(bool)) if tt else m


def main(bw):
    x = table(bw)
    res, best = [], None
    for g, (label, col, tt) in GATES.items():
        for t in TS:
            d = x[x["T"] == t]
            fit = d[d.split == "FIT"]
            p0 = fit.y.mean()
            pool = fit[fit.TT1.astype(bool)] if tt else fit
            cands = [float(pool[col].quantile(q)) for q in QS] + ([-np.inf] if tt else [])
            sc = []
            for th in cands:
                o = on(fit, g, th)
                n, h = int(o.sum()), int(fit.y[o].sum())
                if n >= 15:
                    sc.append((bz(h, n, p0), th))
            z_fit, th = max(sc)
            row = {"gate": g, "label": label, "T": t, "theta": th, "fit_z": round(z_fit, 2)}
            for s in ("FIT", "CHECK", "T2"):
                e = d[d.split == s]
                o = on(e, g, th)
                n, h, base = int(o.sum()), int(e.y[o].sum()), e.y.mean()
                row[s] = {"days": int(len(e)), "on": n, "hit": round(h / n, 3) if n else None, "base": round(base, 3),
                          "lift_pp": round(100 * (h / n - base), 1) if n else None, "z": round(bz(h, n, base), 2) if n else None}
            row["useful"] = all(row[s]["lift_pp"] is not None and row[s]["lift_pp"] >= 5 and row[s]["z"] >= 2
                                for s in ("CHECK", "T2"))
            res.append(row)
            if best is None or z_fit > best["fit_z"]:
                best = row
    json.dump(res, open(Path(bw) / "part_a.json", "w"), indent=1, default=float)
    json.dump({"gate": best["gate"], "T": best["T"], "theta": best["theta"], "fit_z": best["fit_z"]},
              open(Path(bw) / "frozen_gate.json", "w"), default=float)
    # frozen day switch for Part B (all splits, computed only from bars < T)
    d = x[x["T"] == best["T"]]
    pd.DataFrame({"date": d.date, "gate_on": on(d, best["gate"], best["theta"]).values}).to_parquet(Path(bw) / "day_gate.parquet")
    for r in res:
        print(r["gate"], r["T"], "th=%.3f" % r["theta"], "fitz", r["fit_z"],
              *[f"{s}: on {r[s]['on']}/{r[s]['days']} hit {r[s]['hit']} base {r[s]['base']} lift {r[s]['lift_pp']} z {r[s]['z']}"
                for s in ("FIT", "CHECK", "T2")], "USEFUL" if r["useful"] else "")
    print("frozen:", best["gate"], best["T"], best["theta"])


if __name__ == "__main__":
    main(sys.argv[1])
