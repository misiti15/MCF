"""top5_1015 step 1-2: rank setups by live trade count over the last 5 sessions (Primary, Testing 1, Testing 2,
run_id=1 real trades, S6 excluded, "-FD" copies are their own setup) and describe the top 5 live.
Live = paper fills (rule 7). Educational only - not financial advice.

    python research/bdi/top5_1015/live_top5.py   # -> live_rank.csv, live_top5.csv, live_top5_detail.txt
"""
import sqlite3
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
OUT = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/top5_1015")
DAYS = ("2026-10-09", "2026-10-12", "2026-10-13", "2026-10-14", "2026-10-15")
BR = {"p": "mcf-data", "t1": "mcf-data-testing", "t2": "mcf-data-testing2"}


def journal(a):
    SCR.mkdir(parents=True, exist_ok=True)
    p = SCR / f"{a}.db"
    p.write_bytes(subprocess.check_output(["git", "-C", str(ROOT), "show", f"origin/{BR[a]}:journal.db"]))
    t = pd.read_sql(f"select * from trades where run_id=1 and date in {DAYS}", sqlite3.connect(p))
    t["acct"] = a
    return t


def main():
    t = pd.concat([journal(a) for a in BR], ignore_index=True)
    t = t[~t["strategy"].str.startswith("S6")]
    t["nt"] = pd.to_datetime(t["entry_time"], utc=True, format="mixed").dt.tz_convert("America/New_York")
    t["tod"] = t["nt"].dt.hour * 100 + t["nt"].dt.minute
    rank = t.groupby("strategy").agg(n=("id", "size"), accounts=("acct", lambda x: ",".join(sorted(set(x)))),
                                     days=("date", "nunique"), win=("r_multiple", lambda r: (r > 0).mean()),
                                     avg_r=("r_multiple", "mean"), pnl=("pnl", "sum")).sort_values("n", ascending=False)
    rank.round(4).to_csv(OUT / "live_rank.csv")
    top = list(rank.index[:5])
    rows, txt = [], []
    for s in top:
        d = t[t.strategy == s].copy()
        r = d["r_multiple"]
        mfe, mae = d["mfe_r"].abs(), d["mae_r"].abs()
        w, l = d[r > 0], d[r <= 0]
        rows.append({"setup": s, "acct": ",".join(sorted(set(d.acct))), "n": len(d), "days": d.date.nunique(),
                     "side": "long" if (d.side > 0).all() else "short" if (d.side < 0).all() else "mixed",
                     "win": round((r > 0).mean(), 3), "avg_r": round(r.mean(), 3), "pnl": round(d.pnl.sum(), 2),
                     "avg_win_r": round(w.r_multiple.mean(), 3), "avg_loss_r": round(l.r_multiple.mean(), 3),
                     "be_win": round(-l.r_multiple.mean() / (w.r_multiple.mean() - l.r_multiple.mean()), 3),
                     "win_mfe_med": round(w["mfe_r"].abs().median(), 2), "loss_mae_med": round(l["mae_r"].abs().median(), 2),
                     "winners_mae_ge_05": int((w["mae_r"].abs() >= 0.5).sum()),
                     "med_mfe": round(mfe.median(), 2), "med_mae": round(mae.median(), 2),
                     "losers_mfe_ge_05": int((l["mfe_r"].abs() >= 0.5).sum()), "losers": len(l),
                     "losers_never_worked_mfe_lt_02": int((l["mfe_r"].abs() < 0.2).sum()),
                     "giveback_losers_mean": round((l["mfe_r"].abs() - l["r_multiple"]).mean(), 2),
                     "stop": int((d.exit_reason == "stop").sum()), "target": int((d.exit_reason == "target").sum()),
                     "flat": int((~d.exit_reason.isin(["stop", "target"])).sum())})
        txt.append(f"=== {s}  (live paper, {len(d)} trades)")
        txt.append("by date:\n" + d.groupby("date")["r_multiple"].agg(["size", "mean", lambda x: (x > 0).mean(), "sum"]).round(3).to_string())
        b = pd.cut(d["tod"], [0, 1000, 1030, 1130, 1300, 1400, 1600], labels=["09:50-10:00", "10:00-10:30", "10:30-11:30", "11:30-13:00", "13:00-14:00", "14:00-15:00"])
        txt.append("by entry time:\n" + d.groupby(b, observed=True)["r_multiple"].agg(["size", "mean", lambda x: (x > 0).mean()]).round(3).to_string())
        txt.append("losers by MFE reached (R):\n" + l.groupby(pd.cut(l["mfe_r"].abs(), [-.01, .1, .2, .3, .5, 5]), observed=True)["r_multiple"].agg(["size", "mean"]).round(3).to_string())
        txt.append("winners by MAE (R):\n" + w.groupby(pd.cut(w["mae_r"].abs(), [-.01, .25, .5, .75, 5]), observed=True)["r_multiple"].agg(["size", "mean"]).round(3).to_string())
        txt.append("by exit reason:\n" + d.groupby("exit_reason")["r_multiple"].agg(["size", "mean"]).round(3).to_string())
        txt.append("")
    pd.DataFrame(rows).to_csv(OUT / "live_top5.csv", index=False)
    (OUT / "live_top5_detail.txt").write_text("Educational only - not financial advice. Live paper trades, 5 sessions.\n\n" + "\n".join(txt))
    print(rank.head(12).round(3).to_string())
    print(pd.DataFrame(rows).to_string())
    print("\n".join(txt))


if __name__ == "__main__":
    main()
