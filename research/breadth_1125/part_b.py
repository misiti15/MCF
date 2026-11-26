"""BREADTH-1125 Part B: PYR4 book (Primary shorts + 2 gated longs) vs Primary's current book (PREREG.md).
Usage: python research/breadth_1125/part_b.py WORK BW ETB_PARQUET  -> BW/part_b.json. Educational only - not financial advice."""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402

SH = {"L3-gap-slope-fromopen-FD": "L3", "RW3-gapdn-rsi5pop-flowsell-short-FD": "RW3",
      "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "RW5"}
NM, GEN = "NM-ETF-late-dip-di-long", "GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long"


def sessions():
    spy = B.spy_t1()
    days = [d for d in spy.index if d <= "2026-11-04"]
    h = B.half(pd.Series(days))
    s2 = pd.read_parquet(B.FRESH / "spy_days.parquet")
    s2.index = s2.index.astype(str)
    return {"FIT": [d for d, x in zip(days, h) if x == "fit"], "CHECK": [d for d, x in zip(days, h) if x == "check"],
            "T2": [d for d in s2.index if B.T2_LO <= d <= B.T2_HI]}


def metrics(d):
    d = pd.Series(d, dtype=float)
    tot, best = d.sum(), d.max()
    return {"avg_day": round(d.mean(), 3), "worst5": round(d.nsmallest(5).mean(), 2), "red_pct": round(100 * (d < 0).mean(), 1),
            "days_le_m10": int((d <= -10).sum()), "avg_wo_best": round((tot - best) / (len(d) - 1), 3),
            "best_share": round(best / tot, 2) if tot > 0 else None, "best_day": str(d.idxmax()), "sessions": len(d)}


def paired(a, b):
    x = pd.Series(a) - pd.Series(b)
    s = x.std(ddof=1)
    return round(x.mean() / s * math.sqrt(len(x)), 2) if s > 0 else None


def main(W, bw, etbp):
    W, bw = Path(W), Path(bw)
    etb = pd.read_parquet(etbp).rate
    ses = sessions()
    spy = pd.read_parquet(bw / "spy.parquet")[["date", "T", "TT1", "src"]]
    dg = pd.read_parquet(bw / "day_gate.parquet").set_index("date").gate_on
    fz = json.load(open(bw / "frozen_gate.json"))
    out, daily = {"frozen_gate": fz}, {}
    for src, f in (("T1", "trades_t1.parquet"), ("T2", "trades_t2.parquet")):
        t = B.add_r(pd.read_parquet(W / f))
        t["date"] = t.date.astype(str)
        t["split"] = np.where(src == "T2", "T2", pd.Series(B.half(t.date)).map({"fit": "FIT", "check": "CHECK", "none": "none"}))
        t = t[t.split != "none"]
        B.no_locked(t.date.unique())
        t = t.merge(spy[spy.src == src].drop(columns="src").rename(columns={"T": "tod"}), on=["date", "tod"], how="left")
        t["TT1"] = t.TT1.fillna(False).astype(bool)
        t["BR"] = t.date.map(dg).fillna(False).astype(bool)
        legs = {}
        for s in list(SH) + [NM, GEN]:
            x = t[t.setup == s]
            variants = {"": x} if s in SH else {"": x, "+BR": x[x.BR], "+TT1": x[x.TT1]}
            for k, v in variants.items():
                legs[s + k] = B.book(v, B.BOOK["primary"], etb)
        for sp in ({"T1": ("FIT", "CHECK"), "T2": ("T2",)}[src]):
            dd = {k: v[v.split == sp].groupby("date").r.sum().reindex(ses[sp], fill_value=0.0) for k, v in legs.items()}
            daily[sp] = dd
            out.setdefault("legs", {})[sp] = {k: {"trades": int((v.split == sp).sum()), "total_r": round(dd[k].sum(), 1),
                                                   "avg_r": round(float(v[v.split == sp].r.mean()), 3) if (v.split == sp).any() else None}
                                               for k, v in legs.items()}
    books = {"PRIMARY": list(SH) + [NM], "PYR4-BR": list(SH) + [NM + "+BR", GEN + "+BR"],
             "PYR4-TT1": list(SH) + [NM + "+TT1", GEN + "+TT1"]}
    res = {}
    for sp, dd in daily.items():
        tot = {b: sum(dd[k] for k in ks) for b, ks in books.items()}
        res[sp] = {b: metrics(v) for b, v in tot.items()}
        for b in ("PYR4-BR", "PYR4-TT1"):
            res[sp][b]["paired_t_vs_primary"] = paired(tot[b], tot["PRIMARY"])
        sh = sum(dd[k] for k in SH)
        for lg in ("PRIMARY", "PYR4-BR", "PYR4-TT1"):
            lo = tot[lg] - sh
            res[sp][lg]["long_sleeve_total"] = round(lo.sum(), 1)
            res[sp][lg]["corr_long_short"] = round(float(np.corrcoef(lo, sh)[0, 1]), 2) if lo.std() > 0 else None
            w10 = sh.nsmallest(10).index
            res[sp][lg]["long_on_short_worst10"] = round(float(lo[w10].sum()), 1)
    for b in ("PYR4-BR", "PYR4-TT1"):
        ok = all(res[s][b]["worst5"] > res[s]["PRIMARY"]["worst5"] and res[s][b]["avg_day"] > res[s]["PRIMARY"]["avg_day"]
                 for s in ("CHECK", "T2")) and (res["CHECK"][b]["paired_t_vs_primary"] or 0) >= 2
        res[b + "_PASS"] = ok
    out["books"] = res
    json.dump(out, open(bw / "part_b.json", "w"), indent=1, default=float)
    for sp in ("FIT", "CHECK", "T2"):
        print("==", sp)
        print(pd.DataFrame(res[sp]).T.to_string())
        print(pd.DataFrame(out["legs"][sp]).T.to_string())
    print({k: v for k, v in res.items() if k.endswith("PASS")})


if __name__ == "__main__":
    main(*sys.argv[1:4])
