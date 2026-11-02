"""saturday1031 E: weekly give-back review 10-26..10-30 from the nightly peak attribution (research/bdi/nightly10xx/
giveback_attr.csv: each trade's contribution from the marked intraday peak to the close; cat = a_open_winner (open at the
peak, in profit, ended lower), a2_open_loser, b_after_peak (entered after the peak), closed_before_peak; late = exited by
the late flatten) and trades.csv (twin flag = another setup took the same symbol + side <= 3 min earlier).
Paper, costs in. Usage: python giveback_week.py   Educational only - not financial advice."""
from pathlib import Path
import pandas as pd
OUT = Path(__file__).resolve().parent
AC = {"p": "Primary", "t1": "Testing 1", "t2": "Testing 2", "gy": "Graveyard", "gen": "Gen"}
rows = []
for d in ("1026", "1027", "1028", "1029", "1030"):
    base = Path(f"/home/user/MCF/research/bdi/nightly{d}")
    pk = pd.read_csv(base / "daily_peak.csv").set_index("acct")
    g = pd.read_csv(base / "giveback_attr.csv")
    t = pd.read_csv(base / "trades.csv", usecols=["acct", "symbol", "strategy", "entry_time", "twin", "pnl_adj"])
    g = g.merge(t.rename(columns={"entry_time": "et_full"})[["acct", "symbol", "strategy", "pnl_adj", "twin"]].drop_duplicates(
        ["acct", "symbol", "strategy", "pnl_adj"]), on=["acct", "symbol", "strategy", "pnl_adj"], how="left")
    for a in AC:
        x = g[g.acct == a]
        c = x.groupby("cat").contrib.sum()
        aft = x[x.cat == "b_after_peak"]
        top = aft.groupby("strategy").contrib.sum().sort_values().head(1)
        topo = x[x.cat == "a_open_winner"].groupby("strategy").contrib.sum().sort_values().head(1)
        rows.append(dict(day=f"10-{d[2:]}", acct=AC[a], peak=pk.loc[a, "peak"], peak_t=pk.loc[a, "peak_t"], close=pk.loc[a, "close"],
                         giveback=pk.loc[a, "giveback"], after_peak=c.get("b_after_peak", 0.0), n_after=len(aft),
                         open_winners=c.get("a_open_winner", 0.0), open_losers=c.get("a2_open_loser", 0.0),
                         late_flatten=x[x.late == True].contrib.sum(), twins=x[x.twin == True].contrib.sum(),
                         worst_after=f"{top.index[0]} {top.iloc[0]:+.0f}" if len(top) else "",
                         worst_open=f"{topo.index[0]} {topo.iloc[0]:+.0f}" if len(topo) else ""))
R = pd.DataFrame(rows).round(0)
R.to_csv(OUT / "giveback_week.csv", index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 70)
txt = R.to_string(index=False)
s = R.groupby("acct")[["giveback", "after_peak", "open_winners", "open_losers", "late_flatten", "twins"]].sum()
txt += "\n\nweek sums ($, peak -> close contributions):\n" + s.to_string()
txt += "\n\nswing days (peak >= +$100 and close < 0): " + str(R[(R.peak >= 100) & (R.close < 0)][["day", "acct", "peak", "close"]].values.tolist())
open(OUT / "giveback_week_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n")
print(txt)
