"""top5_1021 step 1-2: rank setups by live trade count over the last 5 sessions (reports/<date>.csv on
origin/mcf-data, origin/mcf-data-testing, origin/mcf-data-testing2; run_id=1; S6 and GEN-* excluded; "-FD" copies are
their own setup) and describe the chosen top 5 live. Live = paper fills (rule 7).
Caveat: Testing 1 report for 2026-10-19 was missing ~132 trades in the 10-19 run; re-checked here.
Educational only - not financial advice.

    python research/bdi/top5_1021/live_rank.py [setup ...]
"""
import io
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path("/home/user/MCF")
OUT = Path(__file__).resolve().parent
DAYS = ("2026-10-15", "2026-10-16", "2026-10-19", "2026-10-20", "2026-10-21")
BR = {"p": "mcf-data", "t1": "mcf-data-testing", "t2": "mcf-data-testing2"}


def load():
    fr = []
    for a, b in BR.items():
        for d in DAYS:
            try:
                raw = subprocess.check_output(["git", "-C", str(ROOT), "show", f"origin/{b}:reports/{d}.csv"],
                                              stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                print("missing", a, d)
                continue
            t = pd.read_csv(io.BytesIO(raw))
            t["acct"] = a
            fr.append(t)
    t = pd.concat(fr, ignore_index=True)
    t = t[t.run_id == 1]
    t = t[~t.strategy.str.startswith("S6") & ~t.strategy.str.upper().str.startswith("GEN")]
    t = t[t.r_multiple.notna()]
    t["nt"] = pd.to_datetime(t["entry_time"], utc=True, format="mixed").dt.tz_convert("America/New_York")
    t["tod"] = t["nt"].dt.hour * 100 + t["nt"].dt.minute
    return t


def main():
    t = load()
    print("trades per acct/day:\n", t.groupby(["acct", "date"]).size().unstack(0).to_string())
    rank = t.groupby("strategy").agg(n=("id", "size"), accounts=("acct", lambda x: ",".join(sorted(set(x)))),
                                     days=("date", "nunique"), win=("r_multiple", lambda r: (r > 0).mean()),
                                     avg_r=("r_multiple", "mean"), pnl=("pnl", "sum")).sort_values("n", ascending=False)
    rank.round(4).to_csv(OUT / "live_rank.csv")
    print(rank.head(25).round(3).to_string())
    top = sys.argv[1:]
    rows, txt = [], []
    for s in top:
        d = t[t.strategy == s].copy()
        r = d["r_multiple"]
        w, l = d[r > 0], d[r <= 0]
        mfe = d["mfe_r"].abs()
        rows.append({"setup": s, "acct": ",".join(sorted(set(d.acct))), "n": len(d), "days": d.date.nunique(),
                     "side": "long" if (d.side > 0).all() else "short" if (d.side < 0).all() else "mixed",
                     "win": round((r > 0).mean(), 3), "avg_r": round(r.mean(), 3), "pnl": round(d.pnl.sum(), 2),
                     "avg_win_r": round(w.r_multiple.mean(), 3), "avg_loss_r": round(l.r_multiple.mean(), 3),
                     "be_win": round(-l.r_multiple.mean() / (w.r_multiple.mean() - l.r_multiple.mean()), 3),
                     "med_mfe": round(mfe.median(), 2), "med_mae": round(d["mae_r"].abs().median(), 2),
                     "losers": len(l), "losers_never_worked_mfe_lt_02": int((l["mfe_r"].abs() < 0.2).sum()),
                     "losers_mfe_ge_05": int((l["mfe_r"].abs() >= 0.5).sum()),
                     "giveback_losers_mean": round((l["mfe_r"].abs() - l["r_multiple"]).mean(), 2),
                     "winners_mae_ge_075": int((w["mae_r"].abs() >= 0.75).sum()),
                     "stop": int((d.exit_reason == "stop").sum()), "target": int((d.exit_reason == "target").sum()),
                     "other": int((~d.exit_reason.isin(["stop", "target"])).sum())})
        txt.append(f"=== {s}  (live paper, {len(d)} trades)")
        txt.append("by date:\n" + d.groupby("date")["r_multiple"].agg(["size", "mean", lambda x: (x > 0).mean(), "sum"]).round(3).to_string())
        b = pd.cut(d["tod"], [0, 1000, 1030, 1130, 1300, 1400, 1600],
                   labels=["09:50-10:00", "10:00-10:30", "10:30-11:30", "11:30-13:00", "13:00-14:00", "14:00-16:00"])
        txt.append("by entry time:\n" + d.groupby(b, observed=True)["r_multiple"].agg(["size", "mean", lambda x: (x > 0).mean()]).round(3).to_string())
        txt.append("losers by MFE reached (R):\n" + l.groupby(pd.cut(l["mfe_r"].abs(), [-.01, .1, .2, .3, .5, 5]), observed=True)["r_multiple"].agg(["size", "mean"]).round(3).to_string())
        txt.append("winners by MAE (R):\n" + w.groupby(pd.cut(w["mae_r"].abs(), [-.01, .25, .5, .75, 5]), observed=True)["r_multiple"].agg(["size", "mean"]).round(3).to_string())
        txt.append("by exit reason:\n" + d.groupby("exit_reason")["r_multiple"].agg(["size", "mean"]).round(3).to_string())
        txt.append("")
    if top:
        pd.DataFrame(rows).to_csv(OUT / "live_top5.csv", index=False)
        (OUT / "live_top5_detail.txt").write_text("Educational only - not financial advice. Live paper trades, 5 sessions "
                                                  + ", ".join(DAYS) + ".\n\n" + "\n".join(txt))
        print(pd.DataFrame(rows).T.to_string())
        print("\n".join(txt))


if __name__ == "__main__":
    main()
