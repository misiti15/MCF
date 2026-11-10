"""Observer: GATE2's selector book-wide. Are live entries at a FRESH EXTENSION worse before costs than entries after a pullback?
Lead lead-20261109-2100-4. Descriptive, 0 configs (one pre-declared definition + one sensitivity line, both counted as looks).
Inputs: live paper journals (all 7 accounts, run_id 1, 10-06..11-06, joined to signals as costgap.py) + 1-min SIP bars
(data/cache_hist/1Min, downloaded after 16:00 ET via guild research/data/dl.py).
Definitions (pre-declared before scoring):
  ATR = mean daily true range (RTH, from 1-min bars) over the prior <= 10 sessions, >= 5 required.
  'day extreme in trade direction' = HOD (long) / LOD (short) from 09:30 to the last CLOSED minute before the entry minute.
  EXT  = that extreme was set within the last 15 closed minutes AND |entry - extreme| <= 0.10 ATR.
  PB   = entry >= 0.30 ATR away from that extreme (a pullback / not at the high for longs). MID = the rest.
  gross R = net R + paper cost (entry slip vs signal, stop-exit slip, realism haircut); move_atr = side*(exit-entry)/ATR.
Retention test (BDI charter): dropping EXT keeps >= 80% of trades and >= 90% of each family's top-decile winners?
usage: python extension.py <journal_dir> [ext_atr=0.10]. Educational only - not financial advice."""
import sys, glob, os, json, sqlite3, numpy as np, pandas as pd
from pathlib import Path
pd.set_option("display.width", 250)
J = sys.argv[1]; EXT = float(sys.argv[2]) if len(sys.argv) > 2 else 0.10
TZ = "America/New_York"; BARS = Path("data/cache_hist/1Min")
R = []
for f in sorted(glob.glob(os.path.join(J, "*.db"))):
    if "_" in os.path.basename(f): continue
    a = os.path.basename(f).replace("mcf-data-", "").replace(".db", "").replace("journal", "primary"); c = sqlite3.connect(f)
    t = pd.read_sql("select t.date,t.symbol,t.strategy,t.side,t.entry_time,t.entry,t.stop,t.exit,t.exit_reason,t.shares,t.pnl,t.pnl_adj,"
                    "s.ref_price from trades t join signals s on s.broker_order_id=t.broker_order_id "
                    "where t.run_id=1 and s.run_id=1 and t.date between '2026-10-06' and '2026-11-06' and t.exit is not null", c)
    t["acct"] = a; R.append(t)
T = pd.concat(R, ignore_index=True)
T["risk"] = (T.entry - T.stop).abs(); T = T[(T.risk > 0) & T.ref_price.notna()].copy()
T["et"] = pd.to_datetime(T.entry_time, utc=True, format="mixed").dt.tz_convert(TZ)
T["net"] = T.pnl_adj / (T.risk * T.shares)
stop_x = T.exit_reason.fillna("").str.contains("stop")
T["gross"] = T.net + (T.side * (T.entry - T.ref_price) + np.where(stop_x, T.side * (T.stop - T.exit), 0.0) + (T.pnl - T.pnl_adj) / T.shares) / T.risk
out = []
for sym, g in T.groupby("symbol"):
    p = BARS / f"{sym}.parquet"
    if not p.exists(): continue
    b = pd.read_parquet(p)
    idx = b.index if isinstance(b.index, pd.DatetimeIndex) else pd.to_datetime(b["timestamp"] if "timestamp" in b else b.iloc[:, 0], utc=True)
    b.index = pd.DatetimeIndex(idx).tz_convert(TZ) if pd.DatetimeIndex(idx).tz is not None else pd.DatetimeIndex(idx).tz_localize("UTC").tz_convert(TZ)
    b.columns = [c.lower()[0] if c.lower() in ("open", "high", "low", "close", "volume") else c.lower() for c in b.columns]
    b = b.between_time("09:30", "15:59")
    b["d"] = b.index.date
    day = b.groupby("d").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    day["tr"] = np.maximum(day.h, day.c.shift(1)) - np.minimum(day.l, day.c.shift(1))
    day["atr"] = day.tr.shift(1).rolling(10, min_periods=5).mean()
    for i, r in g.iterrows():
        d = r.et.date()
        if d not in day.index or not np.isfinite(day.at[d, "atr"]): continue
        atr = day.at[d, "atr"]
        x = b[(b.d == d) & (b.index < r.et.floor("min"))]          # closed minutes before the entry minute
        if len(x) < 5: continue
        if r.side == 1: ext_px, ext_t = x.h.max(), x.h.idxmax()
        else: ext_px, ext_t = x.l.min(), x.l.idxmin()
        dist = abs(r.entry - ext_px) / atr
        recent = ext_t >= x.index[-1] - pd.Timedelta(minutes=14)
        out.append(dict(i=i, atr=atr, dist=dist, recent=recent, mins_since_ext=(x.index[-1] - ext_t).total_seconds() / 60,
                        move_atr=r.side * (r.exit - r.entry) / atr, risk_atr=r.risk / atr))
X = T.join(pd.DataFrame(out).set_index("i"), how="inner")
X["grp"] = np.select([X.recent & (X.dist <= EXT), X.dist >= 0.30], ["EXT", "PB"], "MID")
X["fam"] = X.strategy.str.extract(r"^(GEN|[A-Za-z]+\d*)")[0]
print(f"EXT threshold {EXT} ATR | trades with bars+ATR {len(X)} of {len(T)} ({X.date.min()}..{X.date.max()}), setups {X.strategy.nunique()}, families {X.fam.nunique()}")
f = lambda g: pd.Series(dict(n=len(g), share=len(g) / len(X), gross=g.gross.mean(), net=g.net.mean(), move_atr=g.move_atr.mean(), days=g.date.nunique()))
print("\nALL by group:\n", X.groupby("grp").apply(f).round(3).to_string())
print("\nby side x group:\n", X.groupby(["side", "grp"]).apply(f).round(3).to_string())
d = X.groupby(["date", "grp"]).gross.mean().unstack(); dd = (d["EXT"] - d[["MID", "PB"]].mean(axis=1)).dropna()
print(f"\nday-clustered EXT minus non-EXT gross: mean {dd.mean():+.3f}R, t {dd.mean() / (dd.std() / np.sqrt(len(dd))):.2f}, days {len(dd)}, days EXT worse {int((dd < 0).sum())}")
# within setup: EXT vs non-EXT gross, per family
rows = []
for fam, g in X.groupby("fam"):
    e, o = g[g.grp == "EXT"], g[g.grp != "EXT"]
    if len(e) < 15 or len(o) < 15: continue
    top = g.gross >= g.gross.quantile(0.9)
    rows.append(dict(fam=fam, n=len(g), ext_n=len(e), ext_share=len(e) / len(g), ext_gross=e.gross.mean(), other_gross=o.gross.mean(),
                     diff=e.gross.mean() - o.gross.mean(), ext_move_atr=e.move_atr.mean(), other_move_atr=o.move_atr.mean(),
                     top_kept=1 - (top & (g.grp == "EXT")).sum() / max(top.sum(), 1), sides=",".join(sorted(g.side.astype(str).unique()))))
F = pd.DataFrame(rows).set_index("fam").sort_values("diff")
print(f"\nper family (>= 15 EXT and >= 15 other): {len(F)}; EXT worse in {int((F['diff'] < 0).sum())}; "
      f"trades-weighted diff {np.average(F['diff'], weights=F.ext_n):+.3f}R")
print(F.round(3).to_string())
keep = 1 - (X.grp == "EXT").mean(); topall = X.groupby("fam").gross.transform(lambda s: s >= s.quantile(0.9))
print(f"\nretention if EXT were dropped: trades kept {keep:.1%} (need >= 80%); top-decile winners kept {1 - (topall & (X.grp == 'EXT')).sum() / topall.sum():.1%} (need >= 90%)")
print("Educational only - not financial advice.")
