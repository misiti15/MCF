"""Re-price lots the journal closed at ANOTHER lot's leg fill (flatten-path mispairing). Bars: stop-first, else 15:55 close.
Educational only."""
import sys, pandas as pd
S = sys.argv[1]
m = pd.read_csv(f"{S}/mispaired.csv", parse_dates=["nt", "et"])
out = []
for _, r in m.iterrows():
    b = pd.read_parquet(f"{S}/bars/{r.symbol}.parquet")
    b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York")
    after = b[(b.index >= pd.Timestamp(r.et).floor("1min")) & (b.index.strftime("%H:%M") < "15:56")]
    px, why, tt = after.close.iloc[-1], "flatten~15:55", after.index[-1]
    for t, x in after.iterrows():
        hit_s = x.high >= r.stop if r.side == -1 else x.low <= r.stop
        hit_t = x.low <= r.target if r.side == -1 else x.high >= r.target
        if hit_s: px, why, tt = r.stop, "stop", t; break
        if hit_t: px, why, tt = r.target, "target", t; break
    pnl = r.side * (px - r.entry) * r.shares
    out.append(dict(acct=r.acct, symbol=r.symbol, strategy=r.strategy, shares=r.shares, journal_exit=r.exit,
                    journal_pnl=round(r.pnl, 2), sim_exit=round(px, 2), sim_reason=why, sim_time=str(tt)[11:16],
                    sim_pnl=round(pnl, 2), diff=round(pnl - r.pnl, 2)))
o = pd.DataFrame(out); print(o.to_string()); print(o.groupby("acct")[["journal_pnl", "sim_pnl", "diff"]].sum())
o.to_csv(sys.argv[2], index=False)
