"""Step 4: the 21 x 3 = 63 pre-declared counterfactual replays of PLAN.md on the actual live trades (SIP 1-min bars,
costs in). Writes replay_trades.csv (per trade per config), replay_daily.csv, replay_results.csv, replay_out.txt.
Educational only - not financial advice."""
import math

import numpy as np
import pandas as pd

from common import ACCTS, NAMES, OUT, RUNIT, bars, load_trades, marked_matrix, mkt_cost, simulate

T = load_trades()
dg = pd.read_csv(OUT / "trades_diag.csv", usecols=["uid", "atr1m"])
T = T.merge(dg, on="uid", how="left")

PER_TRADE = {
    "BE050": dict(be_at=0.5), "BE075": dict(be_at=0.75), "BE100": dict(be_at=1.0),
    "TR1-05": dict(trail_after=1.0, trail_r=0.5), "TR1-10": dict(trail_after=1.0, trail_r=1.0),
    "TS30": dict(time_n=30), "TS60": dict(time_n=60),
    "WIDE125": dict(stop_mult=1.25), "WIDE150": dict(stop_mult=1.5),
    "SO05": dict(scale_at=0.5), "SO05BE": dict(scale_at=0.5, scale_be=True),
}
ORDER = ["BE050", "BE075", "BE100", "TR1-05", "TR1-10", "LKG30-H", "LKG50-H", "LKG30-F", "LKG50-F", "LKZ5-H", "LKZ10-H",
         "CUT1100", "CUT1200", "CUT1330", "TS30", "TS60", "WIDE125", "WIDE150", "SO05", "SO05BE", "NOISE4"]
N_CONF = 63
BAR = max(1.5, math.sqrt(2 * math.log(N_CONF)))

# ---- per-trade simulations
base, fid = [], []
cf = {k: [] for k in PER_TRADE}
for r in T.itertuples():
    b0 = simulate(r)
    base.append(np.nan if b0 is None else b0[0])
    fid.append(None if b0 is None else b0[1])
    for k, kw in PER_TRADE.items():
        v = simulate(r, **kw)
        cf[k].append(r.pnl_adj if (v is None or b0 is None) else r.pnl_adj + (v[0] - b0[0]))
T["sim_base"], T["sim_reason"] = base, fid
R = pd.DataFrame({"uid": T.uid, "acct": T.acct, "date": T.date, "risk": T.risk, "ACTUAL": T.pnl_adj})
for k in PER_TRADE:
    R[k] = cf[k]
R["CUT1100"] = np.where(T.nt.dt.strftime("%H:%M") >= "11:00", np.nan, T.pnl_adj)
R["CUT1200"] = np.where(T.nt.dt.strftime("%H:%M") >= "12:00", np.nan, T.pnl_adj)
R["CUT1330"] = np.where(T.nt.dt.strftime("%H:%M") >= "13:30", np.nan, T.pnl_adj)
R["NOISE4"] = np.where(T.R < 4 * T.atr1m, np.nan, T.pnl_adj)          # NaN atr (no pre-bars) -> kept

# ---- account-level locks (marked curve, minute by minute)
locks = {"LKG30-H": ("g", .30, False), "LKG50-H": ("g", .50, False), "LKG30-F": ("g", .30, True), "LKG50-F": ("g", .50, True),
         "LKZ5-H": ("z", 5, False), "LKZ10-H": ("z", 10, False)}
for k in locks:
    R[k] = T.pnl_adj.values
trig_log = []
for a in ACCTS:
    U = RUNIT[a]
    for day, d in T[T.acct == a].groupby("date"):
        g, M = marked_matrix(d.reset_index(drop=True), day)
        cur = M.sum(0)
        for k, (kind, y, flat) in locks.items():
            tg = None
            if kind == "g":
                pk = np.maximum.accumulate(cur)
                hit = (pk >= 5 * U) & (cur <= (1 - y) * pk)
            else:
                hit = cur >= y * U
            if hit.any():
                tg = g[int(np.argmax(hit))]
            if tg is None:
                continue
            trig_log.append(dict(acct=a, date=day, config=k, at=tg.strftime("%H:%M"), marked=round(cur[int(np.argmax(hit))], 2)))
            idx = d.index
            vals = d.pnl_adj.values.astype(float).copy()
            vals[(d.nt >= tg).values] = np.nan                                  # halted: later entries not taken
            if flat:
                for j, r in enumerate(d.itertuples()):
                    if r.nt < tg < r.et:
                        b = bars(day, r.symbol)
                        bb = None if b is None else b[b.index >= tg]
                        if bb is not None and len(bb):
                            o = bb.open.values[0]
                            vals[j] = r.side * (o - r.entry) * r.shares - mkt_cost(o, r.shares)
            R.loc[idx, k] = vals
R.to_csv(OUT / "replay_trades.csv", index=False)
pd.DataFrame(trig_log).to_csv(OUT / "replay_lock_triggers.csv", index=False)

# ---- stats
def tstat(x):
    x = np.asarray(x, float)
    if len(x) < 2 or x.std(ddof=1) == 0:
        return np.nan
    return x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))

rows, daily = [], []
out = []
P = lambda *x: out.append(" ".join(str(y) for y in x))
for a in ACCTS:
    x = R[R.acct == a]
    dd = x.groupby("date")[["ACTUAL"] + ORDER].sum(min_count=0)
    for c in ["ACTUAL"] + ORDER:
        v = x[c]
        tk = v.notna()
        delta = dd[c] - dd["ACTUAL"]
        best = delta.idxmax()
        rows.append(dict(acct=a, config=c, trades=int(tk.sum()), win=round((v[tk] > 0).mean() * 100, 1),
                         avgR=round((v[tk] / x.risk[tk]).mean(), 3), total=round(v.sum(), 2),
                         chg=round(v.sum() - x.ACTUAL.sum(), 2), days=len(dd), better=int((delta > 0.005).sum()),
                         worse=int((delta < -0.005).sum()), t_day=round(tstat(delta), 2) if c != "ACTUAL" else np.nan,
                         chg_ex_best=round(delta.drop(best).sum(), 2) if c != "ACTUAL" else np.nan))
    dd.insert(0, "acct", a)
    daily.append(dd.round(2))
Res = pd.DataFrame(rows)
D = pd.concat(daily)
D.to_csv(OUT / "replay_daily.csv")
# pooled across the 20 account-days (secondary)
pool = []
for c in ORDER:
    delta = D[c] - D["ACTUAL"]
    pool.append(dict(config=c, chg=round(delta.sum(), 2), better=int((delta > .005).sum()), worse=int((delta < -.005).sum()),
                     t_pooled=round(tstat(delta), 2)))
Pool = pd.DataFrame(pool)
Res = Res.merge(Pool.rename(columns={"chg": "chg_all", "better": "better_all", "worse": "worse_all"}), on="config", how="left")
Res.to_csv(OUT / "replay_results.csv", index=False)

pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
P(f"Configurations: {N_CONF} (21 x 3 accounts); bar max(1.5, sqrt(2 ln N)) = {BAR:.2f}")
for a in ACCTS:
    x = T[T.acct == a]
    ok = x.sim_reason.notna()
    m = (x.sim_reason[ok].replace({"eod": "flatten", "time": "flatten"}) == x.exit_reason[ok]).mean()
    P(f"{NAMES[a]} simulator fidelity: exit reason matches {m*100:.0f}% of {ok.sum()} trades; sum sim_base {x.sim_base.sum():.0f} vs pnl_adj {x.pnl_adj.sum():.0f}")
for a in ACCTS:
    P(f"\n=== {NAMES[a]}")
    P(Res[Res.acct == a].drop(columns=["acct"]).to_string(index=False))
P("\n=== pooled over 20 account-days (secondary; accounts share market days)")
P(Pool.sort_values("t_pooled", ascending=False).to_string(index=False))
P("\nlock triggers:")
P(pd.DataFrame(trig_log).to_string(index=False) if trig_log else "none")
open(OUT / "replay_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
print("\n".join(out))
