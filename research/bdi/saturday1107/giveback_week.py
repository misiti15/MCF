"""saturday1107: weekly give-back review 11-02..11-06, all 7 accounts (Explore 1 / Live Lab from 11-05), from the nightly
peak attribution (research/bdi/nightly11xx/giveback_attr.csv: each trade's $ contribution from the marked intraday peak
to the close; cat = a_open_winner (open at the peak, in profit, ended lower), a2_open_loser, b_after_peak (entered after
the peak), closed_before_peak; late = exited by the late flatten) and trades.csv (twin flag). Also the peak time vs the
day's swing (SPY / QQQ peak -> close). Paper, costs in.  Usage: python giveback_week.py
Educational only - not financial advice."""
from pathlib import Path
import pandas as pd
OUT = Path(__file__).resolve().parent
AC = {"p": "Primary", "t1": "Testing 1", "t2": "Testing 2", "gy": "Graveyard", "gen": "Gen", "ex1": "Explore 1", "ll": "Live Lab"}
rows = []
for d in ("1102", "1103", "1104", "1105", "1106"):
    base = Path(f"/home/user/MCF/research/bdi/nightly{d}")
    pk = pd.read_csv(base / "daily_peak.csv").set_index("acct")
    g = pd.read_csv(base / "giveback_attr.csv")
    t = pd.read_csv(base / "trades.csv", usecols=["acct", "symbol", "strategy", "twin", "pnl_adj"])
    g = g.merge(t.drop_duplicates(["acct", "symbol", "strategy", "pnl_adj"]), on=["acct", "symbol", "strategy", "pnl_adj"], how="left")
    for a in AC:
        if a not in pk.index: continue
        x = g[g.acct == a]
        c = x.groupby("cat").contrib.sum()
        aft = x[x.cat == "b_after_peak"]
        top = aft.groupby("strategy").contrib.sum().sort_values().head(1)
        topo = x[x.cat == "a_open_winner"].groupby("strategy").contrib.sum().sort_values().head(1)
        rows.append(dict(day=f"11-{d[2:]}", acct=AC[a], peak=pk.loc[a, "peak"], peak_t=pk.loc[a, "peak_t"], close=pk.loc[a, "close"],
                         giveback=pk.loc[a, "giveback"], after_peak=c.get("b_after_peak", 0.0), n_after=len(aft),
                         open_winners=c.get("a_open_winner", 0.0), open_losers=c.get("a2_open_loser", 0.0),
                         late_flatten=x[x.late == True].contrib.sum(), twins=x[x.twin == True].contrib.sum(),
                         spy_pk_close=pk.loc[a, "spy_peak_to_close"] if "spy_peak_to_close" in pk else None,
                         qqq_pk_close=pk.loc[a, "qqq_peak_to_close"] if "qqq_peak_to_close" in pk else None,
                         worst_after=f"{top.index[0]} {top.iloc[0]:+.0f}" if len(top) else "",
                         worst_open=f"{topo.index[0]} {topo.iloc[0]:+.0f}" if len(topo) else ""))
R = pd.DataFrame(rows)
R[[c for c in R.columns if R[c].dtype != object]] = R[[c for c in R.columns if R[c].dtype != object]].round(2)
R.to_csv(OUT / "giveback_week.csv", index=False)
pd.set_option("display.width", 320); pd.set_option("display.max_colwidth", 80)
txt = R.to_string(index=False)
s = R.groupby("acct", sort=False)[["giveback", "after_peak", "open_winners", "open_losers", "late_flatten", "twins"]].sum().round(0)
txt += "\n\nweek sums ($, peak -> close contributions; Explore 1 / Live Lab 2 sessions):\n" + s.to_string()
sw = R[(R.peak >= 100) & (R.close < 0)]
txt += "\n\nswing days (peak >= +$100 and close < 0): " + str(sw[["day", "acct", "peak", "peak_t", "close"]].values.tolist())
open(OUT / "giveback_week_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n")
print(txt)
