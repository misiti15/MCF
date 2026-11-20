"""Replay every live signal of the LATE pullback setup on 1-min bars (Alpaca SIP via mcf.data.alpaca_data)."""
import json, os, sqlite3, sys
from datetime import datetime, timedelta
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research.gates import tod_cost_mult
from mcf.data.alpaca_data import fetch_bars
W = sys.argv[1]
K = "GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long"
rows = []
for a in ("gen", "testinge"):
    c = sqlite3.connect(f"{W}/{a}.db")
    for r in c.execute("select day, ts, symbol, status, reason, ref_price, stop, target, info from signals where run_id=1 and strategy=?", (K,)):
        rows.append((a,) + r)
    tr = pd.read_sql("select symbol, date, entry, stop, target, exit, exit_reason, r_multiple, exit_time from trades where run_id=1 and strategy=?", c, params=(K,))
    tr["acct"] = a
    tr.to_csv(f"{W}/live_trades_{a}.csv", index=False)
S = pd.DataFrame(rows, columns=["acct", "day", "ts", "symbol", "status", "reason", "ref", "stop", "tgt", "info"])
def cat(r):
    s, x = r.status, str(r.reason)
    if s == "submitted": return "TAKEN"
    if x == "halted": return "account halted (Gen, 11-04)"
    if "buying_power" in x: return "broker reject: no buying power (Gen)"
    if x.startswith("spread"): return "spread > 30 bps"
    if x.startswith("cost filter"): return "stop-cost filter > 0.15R"
    return x.split(":")[0]
S["cat"] = S.apply(cat, axis=1)
S["t"] = pd.to_datetime(S.ts, utc=True).dt.tz_convert("America/New_York")
S["tod"] = S["info"].map(lambda s: int(json.loads(s).get("bar_time", 0) or 0))
S.loc[S.tod == 0, "tod"] = S.t.dt.hour * 100 + S.t.dt.minute
S["spread_bps"] = S["info"].map(lambda s: json.loads(s).get("spread_bps"))
bars = {}
cachef = f"{W}/bars.pkl"
if os.path.exists(cachef):
    bars = pd.read_pickle(cachef)
need = [(d, g.symbol.unique().tolist()) for d, g in S.groupby("day")]
for d, syms in need:
    miss = [s for s in syms if (d, s) not in bars]
    if not miss: continue
    st = datetime.fromisoformat(d + "T13:30:00+00:00"); en = st + timedelta(hours=8)
    got = fetch_bars(miss, st, en, feed="sip")
    for s in miss:
        bars[(d, s)] = got.get(s)
pd.to_pickle(bars, cachef)
out = []
for r in S.itertuples():
    b = bars.get((r.day, r.symbol))
    px = kd = xt = np.nan
    if b is not None and len(b):
        b = b.copy(); b.index = pd.DatetimeIndex(b.index).tz_convert("America/New_York")
        hm = b.index.hour * 100 + b.index.minute
        sigm = r.t.hour * 100 + r.t.minute
        sel = np.flatnonzero((hm >= sigm) & (hm < 1555)); after = np.flatnonzero(hm >= 1555)
        O, H, L, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        for k in sel:
            if L[k] <= r.stop: px, kd, xt = min(O[k], r.stop), 1, hm[k]; break
            if H[k] >= r.tgt + 0.01: px, kd, xt = r.tgt, 2, hm[k]; break
        if np.isnan(px):
            if len(after): px, kd, xt = O[after[0]], 0, 1555
            elif len(sel): px, kd, xt = C[sel[-1]], 0, hm[sel[-1]]
    out.append((px, kd, xt))
S[["px", "kind", "xt"]] = pd.DataFrame(out, index=S.index)
e = S.ref; risk = (e - S.stop).abs()
tier = np.where(e < 5, 3.0, 1.0)
ec = (0.01 + e * 1e-4) * tod_cost_mult(S.tod.to_numpy())
xc = np.where(S.kind == 2, 0.0, 0.01 + S.px * 1e-4) + np.where(S.kind == 1, 0.02, 0.0)
S["r_gross"] = (S.px - e) / risk
S["r"] = (S.px - e - tier * (ec + xc)) / risk
# realistic extra: half-spread paid on entry for the wide-spread names (market order)
S["r_spread"] = S.r - (S.spread_bps.fillna(0) / 2e4 * e) / risk
S.drop(columns=["info"]).to_csv(f"{W}/replay.csv", index=False)
print(S.groupby("cat").agg(n=("r", "size"), days=("day", "nunique"), replayed=("r", "count"), avg_r=("r", "mean"),
      med=("r", "median"), win=("kind", lambda k: (k == 2).mean()), avg_r_halfspread=("r_spread", "mean")).round(3).to_string())
print("TOTAL", len(S))
