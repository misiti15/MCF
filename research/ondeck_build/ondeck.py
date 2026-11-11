"""ONDECK build 2026-11-11: On Deck entry rule variants, today's roster, walk-forward check, exposure check.

Input: a scratch dir with p/t1/t2/gy/gen/ex1/ll journal.db (11-10 nightly, read-only copies).
Scope = the 72 setups of research/rotation_design/inventory.csv (Testing 1 / Testing 2 / Explore 1 / Live Lab after TEAM-6);
their 2y, ex-market and Primary-rules columns come from that inventory (same 11-10 data).
Live record = every closed run_id=1 trade of the setup in ANY account, merged by setup id. R after costs =
pnl_adj / (|entry - stop| x shares). Paper results. Educational only - not financial advice."""
import sys, json, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
S = Path(sys.argv[1])
AC = {"p": "primary", "t1": "testing", "t2": "testing2", "gy": "graveyard", "gen": "gen", "ex1": "explore1", "ll": "livelab"}
I = pd.read_csv(ROOT / "research/rotation_design/inventory.csv").set_index("setup")
rows = []
for a, lab in AC.items():
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, strategy, symbol, side, entry_time, exit_time, entry, stop, shares, pnl, pnl_adj from trades "
                    "where run_id=1 and exit is not null", c)
    t["acct"] = lab; rows.append(t)
T = pd.concat(rows, ignore_index=True)
T["pnl_adj"] = T.pnl_adj.fillna(T.pnl)
T["risk"] = (T.entry - T.stop).abs() * T.shares
T = T[T.risk > 0].copy(); T["R"] = T.pnl_adj / T.risk; T["date"] = T.date.astype(str)
T["et"] = pd.to_datetime(T.entry_time, utc=True, format="mixed"); T["xt"] = pd.to_datetime(T.exit_time, utc=True, format="mixed")
TALL = T[~T.strategy.str.startswith("GEN-")].copy()
T = T[T.strategy.isin(I.index)]
DATES = sorted(T.date.unique())


def stats(g):
    n = len(g)
    if not n: return dict(trades=0, sessions=0)
    day = g.groupby("date").R.sum(); k = len(day); tot = g.R.sum()
    bd = day.idxmax(); bn = int((g.date == bd).sum())
    exb = (tot - day.max()) / (n - bn) if k >= 2 and n > bn else np.nan
    share = day.max() / tot if tot > 0 and k >= 2 and day.max() > 0 else np.nan
    l5 = g[g.date.isin(sorted(day.index)[-5:])].R.mean()
    return dict(trades=n, sessions=k, avgR=tot / n, shrunk=tot / (n + 20), exbest=exb, share=share, last5=l5)


# ---- rule variants (all reported) ----
RULES = {
    # owner's example: lower minimums than the Candidate bar, positive and not one-day
    "E0 owner example": dict(ses=5, n=15, shrunk=0.0, exbest=0.0, share=0.60, bt=-0.10, last5=None),
    "E1 positive, loose one-day": dict(ses=5, n=15, shrunk=0.0, exbest=-0.10, share=None, bt=-0.10, last5=None),
    "E2 near-even (recommended)": dict(ses=5, n=15, shrunk=-0.02, exbest=-0.10, share=None, bt=-0.10, last5=-0.30),
    "E3 near-even, wider": dict(ses=5, n=15, shrunk=-0.05, exbest=-0.15, share=None, bt=-0.15, last5=-0.30),
    "E4 E2 + 8 traded sessions": dict(ses=8, n=15, shrunk=-0.02, exbest=-0.10, share=None, bt=-0.10, last5=-0.30),
    "E5 break-even, one-day -0.20": dict(ses=5, n=15, shrunk=-0.02, exbest=-0.20, share=None, bt=-0.15, last5=-0.30),
    "E6 positive only, no one-day gate": dict(ses=5, n=15, shrunk=0.0, exbest=-9, share=None, bt=-0.15, last5=None),
    "E7 E5 without last-5": dict(ses=5, n=15, shrunk=-0.02, exbest=-0.20, share=None, bt=-0.15, last5=None),
}


def passes(m, r, bt):
    if m.get("trades", 0) < r["n"] or m.get("sessions", 0) < r["ses"]: return False
    if not m["shrunk"] > r["shrunk"]: return False
    if not (m["exbest"] == m["exbest"] and m["exbest"] >= r["exbest"]): return False
    if r["share"] is not None and m["share"] == m["share"] and m["share"] > r["share"]: return False
    if r["last5"] is not None and not m["last5"] > r["last5"]: return False
    if bt == bt and bt < r["bt"]: return False
    return True


today = {s: stats(T[T.strategy == s]) for s in I.index}
out = []
for s in I.index:
    m = today[s]; bt = I.loc[s, "bt2y"]
    out.append(dict(setup=s, name=I.loc[s, "name"], home=I.loc[s, "home"], ex_primary=I.loc[s, "ex_primary"], side=I.loc[s, "side"],
                    **{k: m.get(k) for k in ("sessions", "trades", "avgR", "shrunk", "exbest", "share", "last5")},
                    exmkt=I.loc[s, "exmkt"], bt2y=bt, prim_rules=I.loc[s, "prim_rules_avgR"],
                    sig_ps=I.loc[s, "pt_signals_per_session"], ent_ps=I.loc[s, "pt_entries_per_session"],
                    **{k.split()[0]: passes(m, r, bt) for k, r in RULES.items()}))
O = pd.DataFrame(out).sort_values(["shrunk", "sessions"], ascending=[False, False])
O.to_csv(HERE / "candidates.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print("sessions", len(DATES), DATES[0], DATES[-1])
print("counts today:", {k: int(O[k.split()[0]].sum()) for k in RULES})
print(O[O.sessions >= 5].round(3).to_string(index=False))

# ---- walk-forward: checkpoints after sessions 10,12,...,24; forward = next 5 sessions ----
wf = []
for k in range(9, len(DATES) - 2, 2):
    D = DATES[k]; fw = DATES[k + 1:k + 6]
    past = TALL[TALL.date <= D]; fut = TALL[TALL.date.isin(fw)]
    for s in sorted(TALL.strategy.unique()):
        m = stats(past[past.strategy == s]); f = fut[fut.strategy == s]
        if m.get("trades", 0) == 0 or not len(f): continue
        rec = dict(D=D, setup=s, f_n=len(f), f_R=f.R.sum())
        for name, r in RULES.items(): rec[name.split()[0]] = passes(m, r, I.loc[s, "bt2y"] if s in I.index else np.nan)
        wf.append(rec)
W = pd.DataFrame(wf); W.to_csv(HERE / "walkforward.csv", index=False, float_format="%.4f")
print("\nwalk-forward (checkpoints", W.D.nunique(), W.D.min(), "..", W.D.max(), "): next-5-session avg R after costs")
res = []
for name in RULES:
    c = name.split()[0]
    a = W[W[c]]; b = W[~W[c]]
    per = W.groupby(["D", c]).apply(lambda x: x.f_R.sum() / x.f_n.sum()).unstack()
    beat = int((per.get(True) > per.get(False)).sum()) if True in per else 0
    ck = int(per.get(True).notna().sum()) if True in per else 0
    res.append(dict(rule=name, setup_dates=len(a), trades=int(a.f_n.sum()), avgR_in=a.f_R.sum() / max(a.f_n.sum(), 1),
                    rest_trades=int(b.f_n.sum()), avgR_rest=b.f_R.sum() / b.f_n.sum(), beat=f"{beat} of {ck}",
                    setups_pos=f"{int((a.groupby('setup').f_R.sum() > 0).sum())} of {a.setup.nunique()}"))
R = pd.DataFrame(res); print(R.round(3).to_string(index=False)); R.to_csv(HERE / "walkforward_summary.csv", index=False, float_format="%.4f")
json.dump({"dates": DATES}, open(HERE / "dates.json", "w"))
T.drop(columns=["et", "xt"]).to_parquet(S / "ondeck_trades.parquet")
