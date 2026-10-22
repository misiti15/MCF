"""BDI 2026-10-22 (copy of research/bdi/bdi1021/trades_bdi.py, unchanged logic): per-trade review of every real trade (run 1) in all five
intraday accounts, on top of research/bdi/nightly<MMDD>/trades.csv (built by the nightly loop; not redone here).

Per trade, on SIP 1-min bars (path starts the minute after the fill; stop first inside a bar; 15:55 close):
  context at entry (last closed bar): stock from-open %, distance from session VWAP %, 15-min return %, SPY from-open %
  exit what-ifs in R after the trade's own cost (cost_R = journal r_multiple - pnl_adj / $risk, charged once per leg):
    orig   the original bracket (sanity check vs live)
    be05   stop to entry once +0.5R is reached
    t05    +0.5R target (original stop)        t1   +1R target (original stop)
    trail  after +0.5R trail the stop 0.5R behind the best price, no target
    hold   original stop, no target, out at 15:55
    sar    orig + on a stop, reverse at the stop price, 1R stop / 1R target (second leg pays the cost again)
    reent  orig + on a stop, one re-entry same side when a 1-min close is back through the entry within 60 min,
           same stop distance and same target multiple (second leg pays the cost again)
    opp    the opposite side at the entry price, 1R / 1R
  hindsight check for "the opposite side worked": was a rule known at entry pointing that way?
    flag_spy  = SPY from-open at entry >= +0.25% against a short / <= -0.25% against a long
    flag_fo   = the stock itself >= +1% from the open against a short / <= -1% against a long
  loss type (losers only): same classifier as research/bdi/nightly1019/patterns.py, in that order.
Writes per_trade_<MMDD>.csv, patterns_<MMDD>.csv (patterns.csv format) and prints the summary.
Usage: python trades_bdi.py <scratch-with-bars> <YYYY-MM-DD>     Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd

S = Path(sys.argv[1]); D = sys.argv[2]; MD = D[5:7] + D[8:10]; TZ = "America/New_York"
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
T = pd.read_csv(ROOT / "research" / "bdi" / f"nightly{MD}" / "trades.csv")
for c in ("nt", "et"):
    T[c] = pd.to_datetime(T[c], utc=True, format="mixed").dt.tz_convert(TZ)
bars = {}


def bar(s):
    if s not in bars:
        f = S / "bars" / f"{s}.parquet"
        if not f.exists():
            bars[s] = None
        else:
            b = pd.read_parquet(f); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
            b = b.between_time("09:30", "15:55")
            tp = (b.high + b.low + b.close) / 3
            b["vwap"] = (tp * b.volume).cumsum() / b.volume.cumsum().replace(0, np.nan)
            bars[s] = b
    return bars[s]


def sim(path, side, px, stop, tgt, be=None, trail=None):
    """R result of one leg (gross). be: R at which the stop moves to entry. trail: (activate R, distance R)."""
    R = abs(px - stop)
    if R <= 0: return 0.0, None
    best = 0.0; st = stop
    for ts, h, l, c in zip(path.index, path.high.values, path.low.values, path.close.values):
        fav = (h - px) / R if side == 1 else (px - l) / R
        if (l <= st) if side == 1 else (h >= st):
            return (st - px) * side / R, ts
        if tgt is not None and ((h >= tgt) if side == 1 else (l <= tgt)):
            return (tgt - px) * side / R, None
        best = max(best, fav)
        if be is not None and best >= be:
            st = max(st, px) if side == 1 else min(st, px)
        if trail is not None and best >= trail[0]:
            nst = px + side * (best - trail[1]) * R
            st = max(st, nst) if side == 1 else min(st, nst)
    return (path.close.values[-1] - px) * side / R if len(path) else 0.0, None


NM = {"p": "primary", "t1": "testing", "t2": "testing2", "gy": "graveyard", "gen": "generator"}
spy = bar("SPY")
out = []
for r in T.itertuples():
    b = bar(r.symbol)
    if b is None: continue
    side = int(r.side); px = float(r.entry); stop = float(r.stop)
    R = abs(px - stop)
    tgt = None if pd.isna(r.target) else float(r.target)
    tR = None if tgt is None else (tgt - px) * side / R
    cost = float(r.r_multiple) - float(r.radj)
    m0 = r.nt.floor("min")
    path = b[b.index > m0]
    pre = b[b.index < m0]
    last = pre.iloc[-1] if len(pre) else b.iloc[0]
    o = b.open.iloc[0]
    fo = (last.close / o - 1) * 100
    vw = (last.close / last.vwap - 1) * 100 if last.vwap == last.vwap else np.nan
    p15 = pre.close.iloc[-16] if len(pre) >= 16 else o
    r15 = (last.close / p15 - 1) * 100
    sp = spy[spy.index < m0]
    spy_fo = (sp.close.iloc[-1] / spy.open.iloc[0] - 1) * 100 if len(sp) else 0.0
    orig, tstop = sim(path, side, px, stop, tgt)
    be05, _ = sim(path, side, px, stop, tgt, be=0.5)
    t05, _ = sim(path, side, px, stop, px + side * 0.5 * R)
    t1, _ = sim(path, side, px, stop, px + side * 1.0 * R)
    trail, _ = sim(path, side, px, stop, None, trail=(0.5, 0.5))
    hold, _ = sim(path, side, px, stop, None)
    opp, _ = sim(path, -side, px, px + side * R, px - side * R)
    sar = orig - cost; reent = orig - cost; reent_n = 0
    if tstop is not None:
        p2 = path[path.index > tstop]
        sp_px = stop
        leg, _ = sim(p2, -side, sp_px, sp_px + side * R, sp_px - side * R)
        sar += leg - cost
        w = p2[p2.index <= tstop + pd.Timedelta(minutes=60)]
        back = w[(w.close < px) if side == -1 else (w.close > px)]
        if len(back):
            ts = back.index[0]; ep = float(back.close.iloc[0])
            p3 = path[path.index > ts]
            leg2, _ = sim(p3, side, ep, ep - side * R, None if tR is None else ep + side * tR * R)
            reent += leg2 - cost; reent_n = 1
    flag_spy = (side == -1 and spy_fo >= 0.25) or (side == 1 and spy_fo <= -0.25)
    flag_fo = (side == -1 and fo >= 1) or (side == 1 and fo <= -1)
    # loss type (losers only), classifier of nightly1019/patterns.py
    lt = "win"
    if r.pnl < 0:
        post = b[b.index > r.et.floor("min")]
        mfe = r.mfe if r.mfe == r.mfe else 0.0
        if r.exit_reason == "stop" and tgt is not None and len(post) and ((post.high.max() >= tgt) if side == 1 else (post.low.min() <= tgt)):
            lt = "stopped_then_reversed"
        elif abs(fo) >= 3 and opp > 0:
            lt = "wrong_side_after_big_swing"
        elif mfe >= 0.5: lt = "gave_back_gains"
        elif r.exit_reason == "flatten": lt = "late_hold"
        elif mfe < 0.15: lt = "never_worked"
        else: lt = "small MFE then failed (0.15-0.5R)"
    out.append(dict(acct=r.acct, account=NM[r.acct], symbol=r.symbol, setup=r.strategy, side=side, entry_t=f"{r.nt:%H:%M}",
                    exit_reason=r.exit_reason, lot=r.lot_no, cluster=r.cluster, pnl_adj=r.pnl_adj, live=r.radj, cost=cost,
                    mfe=r.mfe, mae=r.mae, t_mfe=r.t_mfe, fo=fo, vwap_dev=vw, r15=r15, spy_fo=spy_fo,
                    orig=orig - cost, be05=be05 - cost, t05=t05 - cost, t1=t1 - cost, trail=trail - cost, hold=hold - cost,
                    sar=sar, reent=reent, reent_n=reent_n, opp=opp - cost, opp_win=opp > 0, flag_spy=flag_spy, flag_fo=flag_fo,
                    loss_type=lt))
X = pd.DataFrame(out)
X.to_csv(HERE / f"per_trade_{MD}.csv", index=False, float_format="%.4f")
L = X[X.loss_type != "win"]
pd.DataFrame(dict(date=D, account=L.account, symbol=L.symbol, setup=L.setup, side=np.where(L.side == 1, "long", "short"),
                  loss_type=L.loss_type,
                  notes=[f"bdi{MD}; r {a:.2f}; mfe {m:.2f}; lot {lo}; opp1R {'win' if ow else 'loss'}; spyfo {s:+.2f}; entry {e}"
                         for a, m, lo, ow, s, e in zip(L.live, L.mfe, L.lot, L.opp_win, L.spy_fo, L.entry_t)])
             ).to_csv(HERE / f"patterns_{MD}.csv", index=False)
P = print
P(f"== {D}: {len(X)} trades with bars (of {len(T)}), losers {len(L)}")
W = ["live", "orig", "be05", "t05", "t1", "trail", "hold", "sar", "reent", "opp"]
P("\n== sum of R after costs by account (what-ifs on 1-min SIP; orig = sanity check vs live)")
P(X.groupby("account")[W].sum().round(1).to_string())
P("\n== day-clustering impossible (1 day); per-trade mean and se, all accounts")
P(pd.DataFrame({"mean": X[W].mean(), "se": X[W].std() / np.sqrt(len(X))}).round(3).T.to_string())
P("\n== loss types by account (count / $)")
P(L.pivot_table(index="loss_type", columns="account", values="pnl_adj", aggfunc=["size", "sum"], fill_value=0).round(0).to_string())
P("\n== opposite side 1R/1R: hindsight check (does a rule known at entry pick out the trades whose opposite won?)")
for f in ("flag_spy", "flag_fo"):
    g = X.groupby(f).agg(n=("opp", "size"), opp_win=("opp_win", "mean"), opp_R=("opp", "mean"), live_R=("live", "mean"))
    P(f"-- {f}"); P(g.round(3).to_string())
    for sd in (1, -1):
        g2 = X[X.side == sd].groupby(f).agg(n=("opp", "size"), opp_R=("opp", "mean"), live_R=("live", "mean"))
        P(f"   side {sd}: " + g2.round(3).to_string().replace("\n", " | "))
S2 = X.groupby("setup").agg(n=("live", "size"), accts=("acct", lambda s: "+".join(sorted(set(s)))), live=("live", "sum"),
                            be05=("be05", "sum"), t05=("t05", "sum"), t1=("t1", "sum"), trail=("trail", "sum"), hold=("hold", "sum"),
                            sar=("sar", "sum"), reent=("reent", "sum"), reent_n=("reent_n", "sum"), opp=("opp", "sum"),
                            never=("mfe", lambda m: int((m < 0.15).sum())), mfe_med=("mfe", "median"), mae_med=("mae", "median"),
                            tmfe_med=("t_mfe", "median"))
S2.round(3).sort_values("live").to_csv(HERE / f"by_setup_{MD}.csv")
P("\n== by setup (sum R after costs), 12 worst and 6 best by live")
cols = ["n", "accts", "live", "be05", "t05", "t1", "trail", "hold", "sar", "reent", "opp", "never", "mfe_med", "tmfe_med"]
P(pd.concat([S2.sort_values("live").head(12), S2.sort_values("live").tail(6)])[cols].round(2).to_string())
P("\nEducational only - not financial advice.")
