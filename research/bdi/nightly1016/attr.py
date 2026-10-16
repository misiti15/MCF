"""Per-setup P/L marked at a given time (realized + open lots marked to the SIP 1-min close). Educational only."""
import sys, pandas as pd
S = sys.argv[1]
T = pd.read_csv("trades.csv", parse_dates=["nt", "et"])
T["nt"] = pd.to_datetime(T.nt, utc=True).dt.tz_convert("America/New_York"); T["et"] = pd.to_datetime(T.et, utc=True).dt.tz_convert("America/New_York")
bars = {}
def px(s, t):
    if s not in bars:
        b = pd.read_parquet(f"{S}/bars/{s}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York"); bars[s] = b
    b = bars[s]; b = b[b.index < t]
    return b.close.iloc[-1]
def at(acct, hhmm):
    t = pd.Timestamp(f"2026-10-16 {hhmm}", tz="America/New_York")
    d = T[(T.acct == acct) & (T.nt < t)].copy()
    d["v"] = [r.pnl if r.et <= t else r.side * (px(r.symbol, t) - r.entry) * r.shares for r in d.itertuples()]
    return d.groupby("strategy").v.sum().sort_values()
grid = [f"{h:02d}:{m:02d}" for h in range(9, 16) for m in range(0, 60, 5) if "09:50" <= f"{h:02d}:{m:02d}" <= "15:55"]
for acct in ("p", "t1", "t2"):
    curve = pd.Series({hh: at(acct, hh).sum() for hh in grid})
    pk, mn = curve.idxmax(), curve.idxmin()
    green = [hh for hh in grid if curve[hh] > 0]
    print(f"== {acct}: peak {curve[pk]:.1f} at {pk}; min {curve[mn]:.1f} at {mn}; green 5-min marks: {len(green)} ({green[:1]}..{green[-1:]})")
    for hh in (pk, mn):
        s = at(acct, hh); print(f"  at {hh}: total {s.sum():.2f}"); print("   top:", s.tail(5).round(1).to_dict()); print("   bottom:", s.head(4).round(1).to_dict())
for k in ["SPY", "QQQ", "IWM"]:
    b = pd.read_parquet(f"{S}/bars/{k}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York")
    b = b.between_time("09:30", "15:59"); o = b.open.iloc[0]
    r = (b.close / o - 1) * 100
    print(k, "close %+.2f%%" % r.iloc[-1], "hi %+.2f%% at %s" % (r.max(), r.idxmax().strftime("%H:%M")), "lo %+.2f%% at %s" % (r.min(), r.idxmin().strftime("%H:%M")),
          {h: round(r.asof(pd.Timestamp(f"2026-10-16 {h}", tz="America/New_York")), 2) for h in ["10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "12:55", "14:15", "15:00", "15:55"]})
# Open path (09:30-11:00) for the index dip-bounce setups that start in Testing 1 on 10-16; SIP gap 12:57-14:10 noted separately.
for k in ["SPY", "QQQ", "IWM"]:
    b = pd.read_parquet(f"{S}/bars/{k}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York")
    pc = b.between_time("04:00", "09:29")
    rth = b.between_time("09:30", "15:59"); o = rth.open.iloc[0]
    w = rth.between_time("09:30", "10:59"); lo_t = w.low.idxmin(); hi_pre = w[w.index < lo_t].high.max()
    after = w[w.index > lo_t]
    print(f"{k} open {o:.2f} (pre-mkt last {pc.close.iloc[-1] if len(pc) else float('nan'):.2f}); open-path low {w.low.min():.2f} = {(w.low.min()/o-1)*100:+.2f}% at {lo_t:%H:%M}; "
          f"high before the low {(hi_pre/o-1)*100:+.2f}%; back to the open at {next((t.strftime('%H:%M') for t, r in after.iterrows() if r.close >= o), 'never')}; "
          f"recovered half the drop by {next((t.strftime('%H:%M') for t, r in after.iterrows() if r.close >= (o + w.low.min())/2), 'never')}; "
          f"10:30 {(w.close.asof(pd.Timestamp('2026-10-16 10:30', tz='America/New_York'))/o-1)*100:+.2f}%, 11:00 {(rth.close.asof(pd.Timestamp('2026-10-16 11:00', tz='America/New_York'))/o-1)*100:+.2f}%")
    print("  5-min closes vs open (%):", {t.strftime('%H:%M'): round((v/o-1)*100, 2) for t, v in w.close.resample('5min', label='right', closed='left').last().items()})
