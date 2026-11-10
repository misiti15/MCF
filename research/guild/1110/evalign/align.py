"""EVALIGN (Skeptic skeptic-20261110-0705-1, Lead lead-20261110-0700-2): does the earnings_yf calendar land on the real
reaction session? 0 outcomes read (gap only = the open vs the prior close, known at the open). Reaction session:
BMO -> the report date; AMC -> the next session; dmh -> the report date (intraday; reported separately; drop or time-gate
for any 09:50 decision); weekend / holiday dates -> next session; duplicate (symbol, reaction session) dropped.
Median |gap| on the mapped reaction session vs the name's other sessions (ratio), and the WRONG mapping for contrast
(AMC on the report date, BMO on the next session). Open window only (locked block absent).  Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/history2y"); import lib
HERE = Path(__file__).resolve().parent
D = lib.daily().sort_values(["symbol", "date"])
D["pc"] = D.groupby("symbol").close.shift(1); gapd = pd.to_datetime(D.date).groupby(D.symbol).diff().dt.days > 5
D.loc[gapd, "pc"] = np.nan; D["agap"] = (D.open / D.pc - 1).abs() * 100
D["date"] = pd.to_datetime(D.date)
sess = np.array(sorted(D.date.unique()))
E = pd.read_parquet("/home/user/MCF/research/bdi/earnings/data/earnings_yf.parquet")
E["rd"] = pd.to_datetime(E.date)
E = E[(E.rd >= sess[0]) & (E.rd <= sess[-1] + pd.Timedelta(days=4))]
E = E[~((E.rd >= "2024-11-01") & (E.rd <= "2025-02-28"))]
E = E[E.symbol.isin(set(D.symbol))].copy()
n0 = len(E); wk = int((E.rd.dt.dayofweek >= 5).sum())
on_or_after = lambda d: sess[np.searchsorted(sess, d)] if np.searchsorted(sess, d) < len(sess) else pd.NaT
after = lambda d: sess[np.searchsorted(sess, d, side="right")] if np.searchsorted(sess, d, side="right") < len(sess) else pd.NaT
E["react"] = [after(d) if s == "amc" else on_or_after(d) for d, s in zip(E.rd, E.session)]
E["wrong"] = [on_or_after(d) if s == "amc" else after(d) for d, s in zip(E.rd, E.session)]
E = E.dropna(subset=["react"]); dup = int(E.duplicated(["symbol", "react"]).sum()); E = E.drop_duplicates(["symbol", "react"])
med = D.groupby("symbol").agap.median()
G = D.set_index(["symbol", "date"]).agap
E["g_react"] = G.reindex(list(zip(E.symbol, E.react))).to_numpy(); E["g_wrong"] = G.reindex(list(zip(E.symbol, E.wrong))).to_numpy()
E["g_norm"] = E.symbol.map(med)
print(f"events in the open window, lab names: {n0} (weekend report dates {wk}, mapped to the next session; duplicates dropped {dup})")
rows = []
for s, g in E.groupby("session"):
    rows.append(dict(session=s, n=len(g), med_gap_react=round(g.g_react.median(), 2), med_gap_wrong=round(g.g_wrong.median(), 2),
                     med_gap_normal=round(g.g_norm.median(), 2), ratio_react=round((g.g_react / g.g_norm).median(), 1),
                     ratio_wrong=round((g.g_wrong / g.g_norm).median(), 1), share_react_gt_wrong=round(float((g.g_react > g.g_wrong).mean()), 3),
                     surprise_nan=round(float(g.surprise_pct.isna().mean()), 3)))
T = pd.DataFrame(rows); print(T.to_string(index=False))
print("\n|gap| in %; 'normal' = the name's median |gap| over all its sessions; ratio = median of event |gap| / normal;"
      "\nreact = BMO same day / AMC next session / dmh same day; wrong = the opposite mapping.")
T.to_csv(HERE / "align_table.csv", index=False)
E[["symbol", "date", "session", "hour_et", "surprise_pct", "react", "g_react", "g_wrong", "g_norm"]].to_csv(HERE / "events_mapped.csv.gz", index=False)
print("Educational only - not financial advice.")
