"""Step 3: per-trade diagnosis over all complete sessions (P 10-06..10-16, T1 10-09..10-16, T2 10-12..10-16).
MFE/MAE on SIP 1-min bars (entry minute to exit minute, as in nightly1016), time to MFE, 1-min ATR(14) noise at entry vs
stop distance, stopped-then-reversed (after a stop, price reached the target / got back to entry before 15:55),
entry hour, latency and slippage. Writes trades_diag.csv, diag_out.txt. Educational only - not financial advice."""
import numpy as np
import pandas as pd

from common import ACCTS, NAMES, OUT, bars, load_trades, TZ

T = load_trades()
cols = {k: [] for k in ("mfe", "mae", "t_mfe", "atr1m", "rev_target", "rev_entry", "post_mfe")}
for r in T.itertuples():
    b = bars(r.date, r.symbol)
    v = dict(mfe=np.nan, mae=np.nan, t_mfe=np.nan, atr1m=np.nan, rev_target=False, rev_entry=False, post_mfe=np.nan)
    if b is not None and r.R > 0:
        s = r.side
        w = b[(b.index >= r.nt.floor("1min")) & (b.index <= r.et.floor("1min"))]
        if len(w):
            fav = (w.high - r.entry) * s if s == 1 else (r.entry - w.low)
            adv = (r.entry - w.low) if s == 1 else (w.high - r.entry)
            v["mfe"], v["mae"] = fav.max() / r.R, adv.max() / r.R
            v["t_mfe"] = (fav.idxmax() - r.nt.floor("1min")).total_seconds() / 60
        pre = b[b.index < r.nt.floor("1min")].tail(15)
        if len(pre) >= 5:
            tr = np.maximum(pre.high - pre.low, np.maximum((pre.high - pre.close.shift()).abs(), (pre.low - pre.close.shift()).abs()))
            v["atr1m"] = tr.iloc[1:].mean()
        after = b[(b.index > r.et.floor("1min")) & (b.index < pd.Timestamp(f"{r.date} 15:55", tz=TZ))]
        if len(after):
            bestafter = (after.high.max() - r.entry) * s if s == 1 else (r.entry - after.low.min())
            v["post_mfe"] = bestafter / r.R
            if r.exit_reason == "stop":
                v["rev_entry"] = bestafter >= 0
                v["rev_target"] = (not pd.isna(r.target)) and bestafter >= abs(r.target - r.entry)
    for k in cols:
        cols[k].append(v[k])
for k in cols:
    T[k] = cols[k]
T["stop_atr"] = T.R / T.atr1m
T["lat"] = (T.nt - T.st).dt.total_seconds()
T["win"] = T.pnl_adj > 0
T["tgt_r"] = (T.target - T.entry).abs() / T.R
T.drop(columns=["meta"]).to_csv(OUT / "trades_diag.csv", index=False)

out = []
P = lambda *x: out.append(" ".join(str(y) for y in x))
pd.set_option("display.width", 250)
for a in ACCTS:
    d = T[T.acct == a]
    L, W = d[~d.win], d[d.win]
    st = d[d.exit_reason == "stop"]
    P(f"\n===== {NAMES[a]}: {len(d)} trades, {d.date.nunique()} sessions, win {d.win.mean()*100:.0f}%, avg R (costs in) {d.radj.mean():+.3f}, P/L adj {d.pnl_adj.sum():+.0f}")
    P(f" exits: {d.exit_reason.value_counts().to_dict()}; target distance median {d.tgt_r.median():.2f}R")
    P(f" LOSERS {len(L)}: MFE median {L.mfe.median():.2f}R; reached >=0.25R {int((L.mfe>=.25).sum())}, >=0.5R {int((L.mfe>=.5).sum())} ({(L.mfe>=.5).mean()*100:.0f}%), >=1R {int((L.mfe>=1).sum())}; "
      f"never worked (MFE<0.2R) {int((L.mfe<.2).sum())} ({(L.mfe<.2).mean()*100:.0f}%) $ {L[L.mfe<.2].pnl_adj.sum():.0f}; $ of losers that reached 0.5R {L[L.mfe>=.5].pnl_adj.sum():.0f}")
    P(f" WINNERS {len(W)}: MFE median {W.mfe.median():.2f}R, realized median {W.radj.median():.2f}R, giveback (MFE-realized) median {(W.mfe-W.radj).median():.2f}R, mean {(W.mfe-W.radj).mean():.2f}R; time to MFE median {W.t_mfe.median():.0f} min")
    P(f" Losers time to MFE median {L.t_mfe.median():.0f} min, hold median {L.hold.median():.0f} min; winners hold median {W.hold.median():.0f} min")
    P(f" STOP vs NOISE: stop distance / 1-min ATR(14) median {d.stop_atr.median():.2f} (p25 {d.stop_atr.quantile(.25):.2f}, p75 {d.stop_atr.quantile(.75):.2f}); "
      f"stops < 2 ATR1m: {int((d.stop_atr<2).sum())} trades")
    q = pd.qcut(d.stop_atr, 4, duplicates="drop")
    P(" by stop/ATR1m quartile:", d.groupby(q, observed=True).agg(n=("uid", "size"), win=("win", "mean"), avgR=("radj", "mean"), pnl=("pnl_adj", "sum"), stop_rate=("exit_reason", lambda x: (x == "stop").mean())).round(3).to_string().replace("\n", " | "))
    P(f" STOPPED THEN REVERSED: {len(st)} stops; price came back to entry before 15:55 {int(st.rev_entry.sum())} ({st.rev_entry.mean()*100:.0f}%); went on to the original target {int(st.rev_target.sum())} ({st.rev_target.mean()*100:.0f}%)")
    P(f"   (base rate check: the target is {d.tgt_r.median():.2f}R away; a wider stop only helps if the extra room is not hit first - tested in replay vi)")
    P(" by entry hour:", d.groupby("hour").agg(n=("uid", "size"), win=("win", "mean"), avgR=("radj", "mean"), pnl=("pnl_adj", "sum"), mfeL=("mfe", lambda x: x[~d.loc[x.index, "win"]].median())).round(3).to_string().replace("\n", " | "))
    P(" by side:", d.groupby("side").agg(n=("uid", "size"), win=("win", "mean"), avgR=("radj", "mean"), pnl=("pnl_adj", "sum")).round(3).to_dict("index"))
    P(f" LATENCY signal->fill median {d.lat.median():.1f}s, p90 {d.lat.quantile(.9):.1f}s; slippage vs ref median {d.slip_bps.median():.1f} bps, mean {d.slip_bps.mean():.1f} bps "
      f"(= {(d.slip_bps.mean()/1e4*d.entry/d.R).mean():.3f}R mean)")
    P(" slippage tercile vs outcome:", d.groupby(pd.qcut(d.slip_bps, 3, duplicates="drop"), observed=True).agg(n=("uid", "size"), avgR=("radj", "mean")).round(3).to_dict("index"))
    P(" winners: realized/MFE share by exit:", W.groupby("exit_reason").apply(lambda x: pd.Series(dict(n=len(x), mfe=x.mfe.median(), real=x.radj.median())), include_groups=False).round(2).to_dict("index"))
    P(" flatten exits (time/EOD):", d[d.exit_reason == "flatten"].agg({"radj": ["count", "mean"], "pnl_adj": "sum", "mfe": "median"}).round(3).to_dict())
open(OUT / "diag_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
print("\n".join(out))
