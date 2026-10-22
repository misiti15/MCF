"""pdh1022 step 1: live (paper) diagnosis of CWT14-failbrk-pdh-p10-short (Testing 2 10-12..10-20, Testing 1 10-21).
Reads reports/<date>.csv on origin/mcf-data-testing and origin/mcf-data-testing2 (run_id 1). Regime labels: regime1022
(regime.day_table). Live = paper fills (rule 7): a diagnosis, not evidence. Educational only - not financial advice.

    python research/bdi/pdh1022/live_diag.py    # -> live_detail.txt, live_trades.csv
"""
import io
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "research" / "bdi" / "regime1022" / "scripts"))
S = "CWT14-failbrk-pdh-p10-short"


def load():
    fr = []
    for b in ("mcf-data-testing", "mcf-data-testing2"):
        names = subprocess.check_output(["git", "-C", str(ROOT), "ls-tree", "--name-only", f"origin/{b}", "reports/"]).decode().split()
        for n in names:
            if n.endswith(".csv") and n.startswith("reports/20"):
                t = pd.read_csv(io.BytesIO(subprocess.check_output(["git", "-C", str(ROOT), "show", f"origin/{b}:{n}"])))
                t["acct"] = "T1" if b.endswith("testing") else "T2"
                fr.append(t[t.strategy == S])
    t = pd.concat(fr, ignore_index=True)
    t = t[t.run_id == 1].copy()
    t["nt"] = pd.to_datetime(t["entry_time"], utc=True, format="mixed").dt.tz_convert("America/New_York")
    t["tod"] = t["nt"].dt.hour * 100 + t["nt"].dt.minute
    return t


def main():
    import regime
    reg = regime.day_table()["regime"]
    reg.index = pd.Index(pd.to_datetime(reg.index).strftime("%Y-%m-%d"))
    t = load()
    t["regime"] = t["date"].map(reg)
    rr = t[t.r_multiple.notna()]
    r = rr.r_multiple
    w, l = rr[r > 0], rr[r <= 0]
    txt = [f"Educational only - not financial advice. LIVE PAPER trades of {S}, run_id 1, {rr.date.min()}..{rr.date.max()}.",
           f"rows {len(t)}, with R {len(rr)}, sessions {rr.date.nunique()}, win {(r > 0).mean():.3f}, avg R {r.mean():+.3f}, "
           f"sum R {r.sum():+.1f}; avg win {w.r_multiple.mean():+.3f}, avg loss {l.r_multiple.mean():+.3f}, "
           f"BE win {-l.r_multiple.mean() / (w.r_multiple.mean() - l.r_multiple.mean()):.3f}", ""]
    agg = lambda g: g["r_multiple"].agg(n="size", avg="mean", win=lambda x: (x > 0).mean(), sum="sum").round(3)  # noqa: E731
    txt.append("by date / account / regime:\n" + rr.groupby(["date", "acct", "regime"]).pipe(agg).to_string())
    txt.append("by regime:\n" + rr.groupby("regime").pipe(agg).to_string())
    b = pd.cut(rr["tod"], [0, 959, 1029, 1059, 1129, 1200, 1600], labels=["09:50-09:59", "10:00-10:29", "10:30-10:59", "11:00-11:29", "11:30-12:00", "after 12:00"])
    txt.append("by entry time:\n" + rr.groupby(b, observed=True).pipe(agg).to_string())
    txt.append("by exit reason:\n" + rr.groupby("exit_reason").pipe(agg).to_string())
    lots = rr.groupby(["date", "symbol"]).size()
    txt.append(f"lots per symbol-day: {lots.value_counts().sort_index().to_dict()} (max {lots.max()})")
    rr = rr.assign(k=rr.groupby(["date", "symbol"]).cumcount() + 1)
    txt.append("by lot number within symbol-day:\n" + rr.groupby("k").pipe(agg).to_string())
    txt.append("losers by MFE reached (R):\n" + l.groupby(pd.cut(l["mfe_r"].abs(), [-.01, .1, .2, .3, .5, 5]), observed=True)["r_multiple"].agg(["size", "mean"]).round(3).to_string())
    txt.append("losers by R (size of loss):\n" + l.groupby(pd.cut(l["r_multiple"], [-9, -1.5, -1.1, -0.9, -0.5, 0.01]), observed=True)["r_multiple"].agg(["size", "mean", "sum"]).round(3).to_string())
    txt.append("winners by R:\n" + w.groupby(pd.cut(w["r_multiple"], [0, .25, .45, .55, 1, 9]), observed=True)["r_multiple"].agg(["size", "mean", "sum"]).round(3).to_string())
    txt.append("winners by MAE (R):\n" + w.groupby(pd.cut(w["mae_r"].abs(), [-.01, .25, .5, .75, 5]), observed=True)["r_multiple"].agg(["size", "mean"]).round(3).to_string())
    txt.append(f"slippage bps: median {t.slip_bps.median():.1f}, mean {t.slip_bps.mean():.1f}")
    dd = rr.groupby("date")["r_multiple"].sum()
    txt.append(f"worst day {dd.idxmin()} {dd.min():+.1f}R; share of total loss: {dd.min() / r.sum():.2f}")
    (OUT / "live_detail.txt").write_text("\n\n".join(txt) + "\n")
    rr.drop(columns=["nt"]).to_csv(OUT / "live_trades.csv", index=False)
    print("\n\n".join(txt))


if __name__ == "__main__":
    main()
