"""Pattern filters (entry-time information only) on the live trades: paired with vs without, live R (removed trade = 0).
Freed slots / caps are not modelled. Usage: python filters_live.py <scratch>"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); t = pd.read_parquet(S / "feat2.parquet").sort_values("entry_time").reset_index(drop=True)
t["sym_day_pos"] = t.groupby(["account", "date", "symbol"]).cumcount() + 1
# open-lot overlap: another lot in the same symbol (any setup) still open at this entry
t["sym_open"] = False
for _, g in t.groupby(["account", "date", "symbol"]):
    if len(g) < 2:
        continue
    et, xt = g.entry_time.values, g.exit_time.values
    for k, ix in enumerate(g.index):
        t.loc[ix, "sym_open"] = bool(((et[:k] <= et[k]) & (xt[:k] > et[k])).any())
ext = lambda th, tm: (t.etod >= tm) & (np.sign(t.spy_fo) == t.side) & (t.spy_fo.abs() >= th)
F = {
    "A_one_per_symbol_day": t.sym_day_pos > 1,
    "A2_no_second_open_lot": t.sym_open,
    "B_no_inverse_short": (t.ty == "inverse") & (t.side < 0),
    "B2_no_inverse_or_lev": t.ty.isin(["inverse", "lev"]),
    "C_late_with_extended_spy_1330_075": ext(0.75, "1330"),
    "C_n_1330_050": ext(0.50, "1330"), "C_n_1330_100": ext(1.00, "1330"), "C_n_1300_075": ext(0.75, "1300"), "C_n_1400_075": ext(0.75, "1400"),
    "E_stack_cap3_10min": t.clu_pos > 3,
    "E_n_stack_cap5": t.clu_pos > 5,
}
rows = []
for name, m in F.items():
    for a in ["primary", "testing1", "testing2", "graveyard", "gen", "ALL"]:
        x = t if a == "ALL" else t[t.account == a]
        mm = m.loc[x.index]
        dd = x.assign(cut=np.where(mm, x.R, 0.0)).groupby("date").cut.sum()  # R removed per day
        s = -dd  # change in day R when the flagged trades are skipped
        tt = s.mean() / (s.std(ddof=1) / np.sqrt(len(s))) if s.std() > 0 else np.nan
        rows.append(dict(filter=name, account=a, n=len(x), n_cut=int(mm.sum()), avgR_cut=x.R[mm].mean(), R_before=x.R.sum(),
                         R_after=x.R[~mm].sum(), avgR_after=x.R[~mm].mean(), avgR_before=x.R.mean(), day_t=tt, days_better=int((s > 0).sum())))
o = pd.DataFrame(rows); o.to_csv(Path(__file__).parent / "filters_live.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 200); print(o.round(3).to_string())
t.to_parquet(S / "feat3.parquet", index=False)
