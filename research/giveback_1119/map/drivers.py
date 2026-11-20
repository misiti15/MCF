"""(b) drivers of account-day reversals: lot-level split of the peak->close giveback. Usage: python drivers.py SCRATCH OUT.md
Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from common import md
S, OUT = sys.argv[1], sys.argv[2]; M0 = 570
P = pd.read_parquet(f"{S}/live_paths.parquet"); A = pd.read_csv(f"{S}/account_days2.csv")
B = pd.read_parquet(f"{S}/live_bars.parquet")
need = set(zip(A.date, ["SPY"] * len(A)))
cl = {}
for (day, sym), g in B[B.symbol.isin(set(P.symbol) | {"SPY"})].groupby(["day", "symbol"]):
    a = np.full(390, np.nan, dtype=np.float32); i = g.m.to_numpy() - M0; ok = (i >= 0) & (i < 390); a[i[ok]] = g.c.to_numpy()[ok]
    cl[(day, sym)] = pd.Series(a).ffill().bfill().to_numpy()
acc_mean = P.groupby("account").R.mean()
rows, days = [], []
for a in A[(A.peak >= 5) & (A.give >= 5)].itertuples():
    g = P[(P.account == a.account) & (P.date == a.date)]; ip = a.peak_m - M0; spy = cl[(a.date, "SPY")]
    op = g[(g.m_in - M0 <= ip) & (g.m_out - M0 > ip)]
    for r in op.itertuples():
        c = cl.get((r.date, r.symbol)); rps = abs(r.entry - r.stop)
        if c is None or not rps > 0: continue
        mk = r.side * (c[ip] - r.entry) / rps
        rows.append(dict(account=a.account, date=a.date, family=r.family, side=r.side, mark=mk, R=r.R, chg=r.R - mk, exit=r.exit_reason,
                         spy=r.side * (spy[min(r.m_out - M0, 389)] / spy[ip] - 1) * 100, maj=np.sign(r.side) == a.netdir))
    late = g[g.m_in - M0 > ip]; mu = P[(P.account == a.account) & (P.date != a.date)].R.mean()
    days.append(dict(account=a.account, date=a.date, give=a.give, late_n=len(late), late_R=late.R.sum(), late_exp=len(late) * mu))
L = pd.DataFrame(rows); D = pd.DataFrame(days)
o = []
def p(s=""): o.append(s)
p(f"Account-days with peak >= +5R and giveback >= 5R: {len(D)}; open-at-peak lots {len(L)}.")
p(f"- Open-at-peak lots: mark at peak avg {L.mark.mean():+.2f}R, final avg {L.R.mean():+.2f}R, change {L.chg.mean():+.2f}R per lot ({L.chg.sum():.0f}R total); "
  f"ended at stop {L.exit.eq('stop').mean():.0%}, target {L.exit.eq('target').mean():.0%}, flatten {L.exit.eq('flatten').mean():.0%}.")
b = np.polyfit(L.spy, L.chg, 1); r2 = np.corrcoef(L.spy, L.chg)[0, 1] ** 2
p(f"- Lot change vs SPY move (peak -> lot exit, signed by lot side): slope {b[0]:+.2f}R per 1% SPY, intercept {b[1]:+.2f}R, R^2 {r2:.2f}. "
  f"Lots whose SPY move was against them (< -0.2%): {int((L.spy < -.2).sum())} lots, change {L[L.spy < -.2].chg.sum():.0f}R; with them (> +0.2%): {int((L.spy > .2).sum())}, {L[L.spy > .2].chg.sum():+.0f}R; flat: {int(L.spy.abs().le(.2).sum())}, {L[L.spy.abs() <= .2].chg.sum():+.0f}R.")
p(f"- Majority-direction lots (same side as the book's net side at the peak): {L.maj.mean():.0%} of lots, {L[L.maj].chg.sum():.0f}R of the {L.chg.sum():.0f}R open-lot change.")
p(f"- Late entries (after the peak): {int(D.late_n.sum())} trades, {D.late_R.sum():.0f}R; expected at each account's own average R on its other days: {D.late_exp.sum():.0f}R "
  f"(so {D.late_R.sum() - D.late_exp.sum():+.0f}R is worse than the account's normal rate).")
fam = L.groupby(["family", "side"]).agg(lots=("chg", "size"), mark=("mark", "mean"), final=("R", "mean"), change=("chg", "sum"), spy=("spy", "mean")).reset_index().sort_values("change").head(12)
p(); p("Open-at-peak lots, families with the largest giveback:"); p(md(fam, "{:.2f}"))
for acc in ("Primary", "Testing1", "Testing2"):
    x = L[L.account == acc]; d = D[D.account == acc]
    if len(d): p(f"- {acc}: {len(d)} days, giveback {d.give.sum():.0f}R = open lots {x.chg.sum():+.0f}R + late {d.late_R.sum():+.0f}R (late expected {d.late_exp.sum():+.0f}R); "
                 f"open-lot change vs SPY slope {np.polyfit(x.spy, x.chg, 1)[0]:+.2f}R/1%, R^2 {np.corrcoef(x.spy, x.chg)[0,1]**2:.2f}")
L.to_csv(f"{S}/peak_lots.csv", index=False)
open(OUT, "w").write("\n".join(o) + "\n"); print("\n".join(o))
