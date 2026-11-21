"""top5_1121 step 1-2: rank setups by live trade count over the last 5 sessions (11-16..11-20) in Primary, On Deck
(testing, old "Testing 1") and Testing A (testing2, old "Testing 2"); S6 and GEN-* out; "-FD" / "-WBn" copies are their
own setup. Trades from fetch_live.py (journal run_id 1, R on the LR8 cost basis, cross-account duplicates counted once).
Describes the chosen 5 live. Live = paper fills (rule 7).

    python live_rank.py <scratch> [setup ...]
Educational only - not financial advice."""
import sys
from pathlib import Path

import pandas as pd

S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent
DAYS = ("2026-11-16", "2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20")
TZ = "America/New_York"


def load():
    t = pd.read_parquet(S / "trades.parquet")
    t = t[t.date.isin(DAYS) & t.acct.isin(["primary", "testing", "testing2"])]
    t = t[~t.strategy.str.startswith("S6") & ~t.strategy.str.upper().str.startswith("GEN")].copy()
    t["nt"] = pd.to_datetime(t["entry_time"], utc=True, format="mixed").dt.tz_convert(TZ)
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
    rows, txt = [], []
    for s in sys.argv[2:]:
        d = t[t.strategy == s].copy()
        r = d["r_multiple"]
        w, l = d[r > 0], d[r <= 0]
        mfe = d["mfe_r"].abs()
        day = d.groupby("date").r_multiple.sum()
        rows.append({"setup": s, "acct": ",".join(sorted(set(d.acct))), "n": len(d), "days": d.date.nunique(),
                     "side": "long" if (d.side > 0).all() else "short" if (d.side < 0).all() else "mixed",
                     "win": round((r > 0).mean(), 3), "avg_r": round(r.mean(), 3), "tot_r": round(r.sum(), 2),
                     "avg_r_wo_best_day": round((r.sum() - day.max()) / max(len(d[d.date != day.idxmax()]), 1), 3),
                     "best_day": day.idxmax(), "best_day_share": round(day.max() / r.sum(), 2) if r.sum() > 0 else None,
                     "avg_win_r": round(w.r_multiple.mean(), 3), "avg_loss_r": round(l.r_multiple.mean(), 3),
                     "be_win": round(-l.r_multiple.mean() / (w.r_multiple.mean() - l.r_multiple.mean()), 3),
                     "med_mfe": round(mfe.median(), 2), "med_mae": round(d["mae_r"].abs().median(), 2),
                     "losers": len(l), "losers_never_worked_mfe_lt_02": int((l["mfe_r"].abs() < 0.2).sum()),
                     "losers_mfe_ge_05": int((l["mfe_r"].abs() >= 0.5).sum()),
                     "giveback_losers_mean": round((l["mfe_r"].abs() - l["r_multiple"]).mean(), 2),
                     "giveback_winners_mean": round((w["mfe_r"].abs() - w["r_multiple"]).mean(), 2),
                     "winners_mae_ge_075": int((w["mae_r"].abs() >= 0.75).sum()),
                     "stop": int((d.exit_reason == "stop").sum()), "target": int((d.exit_reason == "target").sum()),
                     "other": int((~d.exit_reason.isin(["stop", "target"])).sum())})
        txt.append(f"=== {s}  (live paper, {len(d)} trades, LR8 R)")
        txt.append("by date:\n" + d.groupby("date")["r_multiple"].agg(["size", "mean", lambda x: (x > 0).mean(), "sum"]).round(3).to_string())
        b = pd.cut(d["tod"], [0, 1000, 1030, 1130, 1300, 1400, 1600],
                   labels=["09:50-10:00", "10:00-10:30", "10:30-11:30", "11:30-13:00", "13:00-14:00", "14:00-16:00"])
        txt.append("by entry time:\n" + d.groupby(b, observed=True)["r_multiple"].agg(["size", "mean", lambda x: (x > 0).mean()]).round(3).to_string())
        txt.append("losers by MFE reached (R):\n" + l.groupby(pd.cut(l["mfe_r"].abs(), [-.01, .1, .2, .3, .5, 5]), observed=True)["r_multiple"].agg(["size", "mean"]).round(3).to_string())
        txt.append("winners by MAE (R):\n" + w.groupby(pd.cut(w["mae_r"].abs(), [-.01, .25, .5, .75, 5]), observed=True)["r_multiple"].agg(["size", "mean"]).round(3).to_string())
        txt.append("by exit reason:\n" + d.groupby("exit_reason")["r_multiple"].agg(["size", "mean"]).round(3).to_string())
        txt.append("by account:\n" + d.groupby("acct")["r_multiple"].agg(["size", "mean", "sum"]).round(3).to_string())
        txt.append("")
    if rows:
        pd.DataFrame(rows).to_csv(OUT / "live_top5.csv", index=False)
        (OUT / "live_top5_detail.txt").write_text("Educational only - not financial advice. Live paper trades (LR8 R), 5 sessions "
                                                  + ", ".join(DAYS) + ".\n\n" + "\n".join(txt))
        print(pd.DataFrame(rows).T.to_string())
        print("\n".join(txt))


if __name__ == "__main__":
    main()
