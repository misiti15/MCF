"""eu1103/edge Q1: decompose live R (run_id 1, 5 accounts, 2026-10-06..11-02) into market beta, stock-day drift,
timing, and costs / fill quality; one-big-day share; live fills vs signal price, quote mid and the 1-minute bar.

Usage: python decompose.py <scratch>   (scratch holds <branch>.db and live_bars.parquet from fetch_live_bars.py)
Writes per_trade.csv.gz (scratch), by_setup.csv and results.json (this folder).

Definitions (per trade; rps = |entry - stop| risk per share, side +1 long / -1 short):
  R_net    = pnl_adj / (rps * shares)                       (the journal's live R, costs in)
  R_gross  = side * (exit - entry) / rps                   (broker fill to broker fill)
  cost_adj = R_gross - R_net                                (the 2c stop-exit haircut pnl_adj adds)
  entry_slip_sig = side * (entry - signal ref_price) / rps  (fill vs the price when the signal fired; >0 = paid)
  entry_slip_mid = side * (entry - signal mid quote) / rps  (fill vs the NBBO mid at the signal; >0 = paid)
  entry_vs_bar   = side * (entry - open of the next 1-min bar after the signal) / rps
  R_mid    = side * (exit - mid_at_signal) / rps            (what the trade made from the mid: before entry friction)
  mkt      = side * beta * SPY_ret(entry min -> exit min) * entry / rps   (beta: 5-min returns vs SPY, shrunk to 1)
  drift    = side * (idio stock return open->15:55 that day) * (minutes held / 385) * entry / rps
  timing   = R_mid - mkt - drift - (exit friction is inside R_mid)        (= what entry/exit timing added on the stock)
  fade     = entry against the stock's prior 30-minute move (side * ret_30m_before < 0), else momentum
Educational only - not financial advice."""
import json, sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd

S = Path(sys.argv[1]); OUT = Path(__file__).parent
A = {"primary": "mcf-data", "testing1": "mcf-data-testing", "testing2": "mcf-data-testing2",
     "graveyard": "mcf-data-graveyard", "gen": "mcf-data-gen"}
T = []
for a, b in A.items():
    c = sqlite3.connect(S / f"{b}.db")
    t = pd.read_sql("select * from trades where run_id=1", c)
    s = pd.read_sql("select broker_order_id, ts as sig_ts, ref_price, entry_type, info from signals "
                    "where run_id=1 and status='submitted'", c).drop_duplicates("broker_order_id")
    t = t.merge(s, on="broker_order_id", how="left"); t["account"] = a; T.append(t)
T = pd.concat(T, ignore_index=True)
T["rps"] = (T.entry - T.stop).abs()
T = T[(T.rps > 0) & T.pnl_adj.notna() & T.exit.notna()].copy()
T["R_net"] = T.pnl_adj / (T.rps * T.shares)
T["R_gross"] = T.side * (T.exit - T.entry) / T.rps
T["cost_adj"] = T.R_gross - T.R_net
inf = T["info"].fillna("{}").map(json.loads)
T["bid"] = inf.map(lambda d: d.get("bid")).astype(float); T["ask"] = inf.map(lambda d: d.get("ask")).astype(float)
T["mid"] = np.where((T.bid > 0) & (T.ask >= T.bid), (T.bid + T.ask) / 2, np.nan)
T["spread_R"] = (T.ask - T.bid) / T.rps
T["entry_slip_sig"] = T.side * (T.entry - T.ref_price) / T.rps
T["entry_slip_mid"] = T.side * (T.entry - T.mid) / T.rps
T["R_mid"] = T.side * (T.exit - T.mid) / T.rps
for c in ("signal_time", "entry_time", "exit_time"):
    T[c] = pd.to_datetime(T[c], utc=True, format="mixed").dt.tz_convert("America/New_York")
T["sig_ts"] = pd.to_datetime(T["sig_ts"], utc=True, format="mixed").dt.tz_convert("America/New_York")

# ---- bars
X = pd.read_parquet(S / "live_bars.parquet")
X["ts"] = pd.to_datetime(X.ts, utc=True).dt.tz_convert("America/New_York")
X["date"] = X.ts.dt.strftime("%Y-%m-%d")
X = X.set_index(["symbol", "ts"]).sort_index()
spy = X.loc["SPY"]
# beta per symbol: 5-minute returns 09:35-15:55 on every live day we have bars for, vs SPY; shrink toward 1 by days
def five(g):
    g = g[(g.index.time >= pd.Timestamp("09:35").time()) & (g.index.time <= pd.Timestamp("15:55").time())]
    return g.close.resample("5min").last().pct_change()
spy5 = spy.groupby(spy.date).apply(lambda g: five(g)).droplevel(0)
beta = {}
for sym, g in X.groupby(level=0):
    g = g.droplevel(0)
    r = g.groupby(g.date, group_keys=False).apply(five)
    j = pd.concat([r, spy5], axis=1, keys=["s", "m"]).dropna()
    nd = g.date.nunique()
    if len(j) < 20 or j.m.var() == 0:
        beta[sym] = 1.0; continue
    b = j.s.cov(j.m) / j.m.var()
    beta[sym] = float((nd * np.clip(b, -1, 4) + 3 * 1.0) / (nd + 3))
T["beta"] = T.symbol.map(beta).fillna(1.0)

def px_at(sym, ts, field="open"):
    """open of the 1-min bar starting at floor(ts) (price at ts), NaN if missing"""
    try:
        return X.at[(sym, ts.floor("min")), field]
    except KeyError:
        return np.nan

rows = []
day_ref = {}
for (sym, d), g in X.groupby([X.index.get_level_values(0), "date"]):
    g = g.droplevel(0)
    o = g.open.iloc[0]; c = g.close[g.index.time <= pd.Timestamp("15:54").time()]
    day_ref[(sym, d)] = (o, c.iloc[-1] if len(c) else np.nan)
for i, r in T.iterrows():
    et, xt = r.entry_time, r.exit_time
    s_e, s_x = px_at("SPY", et), px_at("SPY", min(xt, xt.normalize() + pd.Timedelta(hours=15, minutes=59)))
    nb = px_at(r.symbol, (r.sig_ts if pd.notna(r.sig_ts) else r.signal_time).floor("min") + pd.Timedelta(minutes=1))
    p30 = px_at(r.symbol, et - pd.Timedelta(minutes=30), "close"); p0 = px_at(r.symbol, et - pd.Timedelta(minutes=1), "close")
    so, sc = day_ref.get(("SPY", r.date), (np.nan, np.nan)); o, cl = day_ref.get((r.symbol, r.date), (np.nan, np.nan))
    rows.append((s_x / s_e - 1, nb, p0 / p30 - 1, (cl / o - 1) - r.beta * (sc / so - 1), sc / so - 1))
Z = pd.DataFrame(rows, index=T.index, columns=["spy_ret", "next_open", "ret30", "idio_day", "spy_oc"])
T = T.join(Z)
T["entry_vs_bar"] = T.side * (T.entry - T.next_open) / T.rps
held = ((T.exit_time - T.entry_time).dt.total_seconds() / 60).clip(0, 385)
T["held_min"] = held
T["mkt"] = T.side * T.beta * T.spy_ret * T.entry / T.rps
T["drift"] = T.side * T.idio_day * held / 385 * T.entry / T.rps
T["timing"] = T.R_mid - T.mkt - T.drift
T["fade"] = np.where(T.ret30.isna(), np.nan, (T.side * T.ret30 < 0).astype(float))
T["daytype"] = np.select([T.spy_oc >= 0.0025, T.spy_oc <= -0.0025], ["up", "down"], "quiet")
T["tod"] = T.entry_time.dt.hour * 100 + T.entry_time.dt.minute
T["fric"] = T.R_mid - T.R_net            # entry friction from mid + stop haircut (exit friction is in both)
T.drop(columns=["info", "meta"]).to_csv(S / "per_trade.csv.gz", index=False)

# ---- per setup x account
def best_share(g):
    d = g.groupby("date").R_net.sum(); tot = d.sum(); b = d.max()
    nb = g[g.date == d.idxmax()].shape[0]
    return pd.Series({"best_day_R": b, "best_share": b / tot if tot > 0 else np.nan,
                      "avgR_wo_best": (tot - b) / max(1, len(g) - nb)})
K = ["R_net", "R_gross", "R_mid", "mkt", "drift", "timing", "fric", "entry_slip_sig", "entry_slip_mid", "entry_vs_bar",
     "spread_R", "cost_adj"]
G = T.groupby(["account", "strategy"])
B = G[K].mean().join(G.size().rename("n")).join(G.date.nunique().rename("sessions")).join(G.apply(best_share))
B["fade_share"] = G.fade.mean(); B["side"] = G.side.mean()
B = B.reset_index().sort_values("R_net", ascending=False)
B.round(4).to_csv(OUT / "by_setup.csv", index=False)

res = {"trades": int(len(T)), "sessions": int(T.date.nunique()), "window": [T.date.min(), T.date.max()],
       "quote_coverage": round(float(T.mid.notna().mean()), 3), "next_bar_coverage": round(float(T.next_open.notna().mean()), 3)}
def comp(df):
    o = {k: round(float(df[k].mean()), 4) for k in K}
    o["n"] = int(len(df)); o["sum_R"] = round(float(df.R_net.sum()), 1)
    d = df.groupby("date").R_net.sum(); o["best_day_share"] = round(float(d.max() / d.sum()), 3) if d.sum() > 0 else None
    o["avgR_wo_best_day"] = round(float((d.sum() - d.max()) / max(1, len(df) - (df.date == d.idxmax()).sum())), 4)
    return o
prof = B[(B.n >= 20) & (B.R_net > 0)]
key = set(zip(prof.account, prof.strategy))
P = T[[k in key for k in zip(T.account, T.strategy)]]
res["profitable_setups"] = {"rule": "setup x account with n >= 20 and live avg R > 0", "count": int(len(prof)),
                            "all": comp(P), "rest": comp(T.drop(P.index)), "book": comp(T)}
res["profitable_wo_best_day_positive"] = int((prof.avgR_wo_best > 0).sum())
res["profitable_best_share_ge_50"] = int((prof.best_share >= 0.5).sum())
res["by_account"] = {a: comp(g) for a, g in T.groupby("account")}
res["profitable_by_daytype"] = {k: comp(g) for k, g in P.groupby("daytype")}
res["book_by_daytype"] = {k: comp(g) for k, g in T.groupby("daytype")}
res["fade_vs_momentum"] = {("fade" if k == 1 else "momentum"): comp(g) for k, g in T.groupby("fade")}
res["fade_vs_momentum_profitable"] = {("fade" if k == 1 else "momentum"): comp(g) for k, g in P.groupby("fade")}
res["by_side"] = {("long" if k == 1 else "short"): comp(g) for k, g in T.groupby("side")}
res["by_exit"] = {k: comp(g) for k, g in T.groupby("exit_reason") if len(g) >= 30}
tb = pd.cut(T.tod, [930, 945, 1000, 1030, 1100, 1200, 1400, 1600], right=False)
res["by_entry_time"] = {str(k): comp(g) for k, g in T.groupby(tb, observed=True)}
# fill quality: share of entries better than the mid (paid for liquidity) / worse
e = T.entry_slip_mid.dropna()
res["fill_vs_mid"] = {"n": int(len(e)), "mean_R": round(float(e.mean()), 4), "median_R": round(float(e.median()), 4),
                      "share_better_than_mid": round(float((e < 0).mean()), 3), "share_at_or_worse_than_ask_bid": round(float(
                          (T.side * (T.entry - np.where(T.side > 0, T.ask, T.bid)) >= 0)[T.mid.notna()].mean()), 3),
                      "mean_half_spread_R": round(float((T.spread_R / 2).mean()), 4),
                      "mean_entry_bps_vs_mid": round(float((T.side * (T.entry / T.mid - 1) * 1e4).mean()), 2)}
# exits: stop fills vs stop price, flatten vs bar
st = T[T.exit_reason == "stop"]
res["stop_fill_vs_stop_R"] = round(float((T.side * (st.exit - st.stop) / st.rps).mean()), 4)
res["target_share_of_winners"] = round(float(((T.exit_reason == "target") & (T.R_net > 0)).sum() / (T.R_net > 0).sum()), 3)
res["corr_daily_R_spy"] = round(float(T.groupby("date").R_net.mean().corr(T.groupby("date").spy_oc.first())), 3)
json.dump(res, open(OUT / "results.json", "w"), indent=1, default=str)
print(json.dumps(res, indent=1, default=str)[:6000])
print(prof[["account", "strategy", "n", "sessions", "R_net", "R_mid", "mkt", "drift", "timing", "fric", "entry_slip_mid",
            "avgR_wo_best", "best_share", "fade_share"]].round(3).to_string())
