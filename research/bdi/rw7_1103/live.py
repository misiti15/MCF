"""RW7-gapdn-bounce-early-short-FD live record (Testing 1 paper, run 1, every session it traded) + drill-downs.
R per trade = pnl_adj / (|entry - stop| x shares)  (after costs, the journal's adjusted P/L).
Ex-market = BETA1 (mcf.analytics.market_beta): OLS of R on SPY's % move over each trade's own holding window.
Day type = SPY open-to-close (up > +0.25%, down < -0.25%, else quiet). Account red/green = that account's run-1 P/L.
Path stats (MFE / MAE / give-back / hold-to-15:55) on SIP 1-min bars from the minute after the fill.
Usage: python live.py <scratch>   (fetch.py first). Educational only - not financial advice."""
import sys, sqlite3, json
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from mcf.analytics import market_beta as MB

S = Path(sys.argv[1]); TZ = "America/New_York"; HERE = Path(__file__).resolve().parent
SET = "RW7-gapdn-bounce-early-short-FD"
SIS = ("RW1", "RW3", "RW5", "MF2", "RW3S")
q = lambda a, sql, p=(): pd.read_sql(sql, sqlite3.connect(S / a / "journal.db"), params=p)
T = q("t1", "select * from trades where strategy=? and run_id=1", (SET,))
T["risk"] = (T.entry - T.stop).abs() * T.shares
T["R"] = T.pnl_adj / T.risk
T["Rg"] = T.r_multiple
for c in ("entry_time", "exit_time"):
    T[c] = pd.to_datetime(T[c], utc=True, format="mixed").dt.tz_convert(TZ)
U = pd.read_csv(S / "universe.csv").set_index("symbol")
DLY = pd.read_parquet(S / "daily.parquet"); DLY["d"] = pd.to_datetime(DLY.timestamp).dt.tz_convert(TZ).dt.date.astype(str)
DLY = DLY.sort_values(["symbol", "d"])
DLY["pc"] = DLY.groupby("symbol").close.shift()
DLY["tr"] = np.maximum(DLY.high, DLY.pc) - np.minimum(DLY.low, DLY.pc)
DLY["atr14"] = DLY.groupby("symbol").tr.transform(lambda s: s.rolling(14).mean().shift())
DLY["adv20"] = DLY.groupby("symbol").apply(lambda g: (g.close * g.volume).rolling(20).mean().shift()).reset_index(level=0, drop=True)
DK = DLY.set_index(["symbol", "d"])


def bars(d, s):
    f = S / "bars" / d / f"{s}.parquet"
    if not f.exists():
        return None
    b = pd.read_parquet(f); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
    return b.between_time("09:30", "15:59")


def rsi(c, n=14):
    d = c.diff(); up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


rows = []
for k, r in T.iterrows():
    d = r.date; b = bars(d, r.symbol); o = {}
    try:
        dk = DK.loc[(r.symbol, d)]; o["gap"] = (dk.open / dk.pc - 1) * 100; o["atrp"] = dk.atr14 / dk.pc * 100; o["adv"] = dk.adv20 / 1e6
    except KeyError:
        o.update(gap=np.nan, atrp=np.nan, adv=np.nan)
    if b is not None and len(b):
        R1 = abs(r.entry - r.stop); px = r.entry
        path = b[b.index >= r.entry_time.floor("1min") + pd.Timedelta(minutes=1)]
        held = path[path.index <= r.exit_time.floor("1min")]
        if len(held):
            o["mfe"] = (px - held.low.min()) / R1; o["mae"] = (held.high.max() - px) / R1
        else:
            o["mfe"] = o["mae"] = 0.0
        to_close = path[path.index <= pd.Timestamp(f"{d} 15:55", tz=TZ)]
        o["hold_r"] = (px - to_close.close.iloc[-1]) / R1 if len(to_close) else np.nan   # gross, no stop
        pre = b[b.index < r.entry_time.floor("1min")]
        o["fo"] = (pre.close.iloc[-1] / b.open.iloc[0] - 1) * 100 if len(pre) else np.nan
        tp = (pre.high + pre.low + pre.close) / 3
        o["vwapdev"] = (pre.close.iloc[-1] / ((tp * pre.volume).sum() / pre.volume.sum()) - 1) * 100 if len(pre) else np.nan
        c5 = pre.close.resample("5min", label="right", closed="left").last().dropna()
        o["rsi_sess"] = float(rsi(c5).iloc[-1]) if len(c5) >= 15 else np.nan   # same-day-only RSI(14) on 5-min (no warm-up)
    sp = bars(d, "SPY")
    if sp is not None:
        pre = sp[sp.index < r.entry_time.floor("1min")]
        o["spy_fo"] = (pre.close.iloc[-1] / sp.open.iloc[0] - 1) * 100 if len(pre) else np.nan
        o["spy_oc"] = (sp.close.iloc[-1] / sp.open.iloc[0] - 1) * 100
    rows.append(o)
T = pd.concat([T, pd.DataFrame(rows, index=T.index)], axis=1)
nm = U.name.reindex(T.symbol).fillna("").str.upper().to_numpy()
lev = pd.Series(nm).str.contains(r"2X|3X|ULTRA|LEVERAGED|DAILY .*BULL|DAILY .*BEAR|-1X|INVERSE|1\.5X|2\.0X")
etf = pd.Series(nm).str.contains(r"ETF|FUND|TRUST|SHARES|PORTFOLIO")
T["kind"] = np.where(lev, "leveraged", np.where(etf, "etf", "stock"))
T["adv_rank"] = U.adv_rank.reindex(T.symbol).to_numpy()
T["tod"] = T.entry_time.dt.hour * 100 + T.entry_time.dt.minute
spy_d = {d: bars(d, "SPY") for d in T.date.unique()}
spy_all = pd.concat([v for v in spy_d.values() if v is not None]).sort_index()
T["spy_win"] = MB.spy_moves(T, spy_all)
T["daytype"] = np.select([T.spy_oc > 0.25, T.spy_oc < -0.25], ["up", "down"], "quiet")

# account day P/L
acc = {}
for a in ("p", "t1", "t2"):
    acc[a] = q(a, "select date, sum(pnl_adj) pl from trades where run_id=1 group by 1").set_index("date").pl
T["p_day"] = T.date.map(acc["p"]); T["t1_day"] = T.date.map(acc["t1"])
T["t1_ex_day"] = T.t1_day - T.date.map(T.groupby("date").pnl_adj.sum())


def dstat(t):
    g = t.groupby("date").R.agg(["sum", "size"])
    n = len(t); m = t.R.mean()
    tm = g["sum"] / g["size"]   # per-day mean
    tc = t.R.sum() / g["size"].sum()
    # day-clustered t: sum of day R / sqrt(sum of (day R - day n * mean)^2)
    e = g["sum"] - g["size"] * m
    tcl = t.R.sum() / np.sqrt((e ** 2).sum()) if len(g) > 1 else np.nan
    best = g["sum"].idxmax(); share = g["sum"].max() / t.R.sum() if t.R.sum() > 0 else np.nan
    wo = t[t.date != best].R.mean()
    return dict(n=n, days=len(g), avgR=m, totR=t.R.sum(), pl=t.pnl_adj.sum(), win=(t.R > 0).mean(), t_cl=tcl,
                best=best, best_share=share, avgR_wo_best=wo)


out = []
P = lambda *a: (out.append(" ".join(str(x) for x in a)), print(*a))
P("# RW7-gapdn-bounce-early-short-FD live (Testing 1 paper, run 1). Educational only - not financial advice.")
P("\n## per session")
ps = T.groupby("date").agg(trades=("R", "size"), R=("R", "sum"), avgR=("R", "mean"), pl=("pnl_adj", "sum"), win=("R", lambda x: (x > 0).mean()),
                           spy_oc=("spy_oc", "first"), p_day=("p_day", "first"), t1_day=("t1_day", "first"), t1_ex=("t1_ex_day", "first"))
P(ps.round(3).to_string())
s = dstat(T); P("\n## overall", json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()}))
mk = MB.fit(MB.sums(T.spy_win, T.R)); P("BETA1 ex-market avg R", mk, "(n with SPY window", int(T.spy_win.notna().sum()), ")")
P("gross avg R (journal r_multiple)", round(T.Rg.mean(), 4), "| cost per trade R", round((T.Rg - T.R).mean(), 4))
P("green sessions", int((ps.R > 0).sum()), "of", len(ps), "| sessions with R>0 and P/L>0", int(((ps.R > 0) & (ps.pl > 0)).sum()))
P("\n## by SPY day type (open-to-close +-0.25%)")
P(T.groupby("daytype").agg(n=("R", "size"), days=("date", "nunique"), avgR=("R", "mean"), totR=("R", "sum")).round(3).to_string())
P("\n## by Primary day red/green, Testing 1 (rest of account, ex RW7) red/green")
T["p_rg"] = np.where(T.p_day > 0, "P green", "P red"); T["t1_rg"] = np.where(T.t1_ex_day > 0, "T1ex green", "T1ex red")
for c in ("p_rg", "t1_rg"):
    P(T.groupby(c).agg(n=("R", "size"), days=("date", "nunique"), avgR=("R", "mean"), totR=("R", "sum")).round(3).to_string())
P("corr(per-session RW7 R, Primary day P/L) =", round(ps.R.corr(ps.p_day), 3), "| vs T1 ex-RW7 =", round(ps.R.corr(ps.t1_ex), 3),
  "| vs SPY o-c =", round(ps.R.corr(ps.spy_oc), 3))


def bucket(col, bins, labels=None):
    b = pd.cut(T[col], bins, labels=labels)
    return T.groupby(b, observed=True).agg(n=("R", "size"), days=("date", "nunique"), avgR=("R", "mean"), totR=("R", "sum"),
                                           win=("R", lambda x: (x > 0).mean())).round(3).to_string()


P("\n## time of day (entry ET)"); P(bucket("tod", [949, 1030, 1130, 1300, 1400, 1501]))
P("\n## gap % (open vs prior close)"); P(bucket("gap", [-50, -3, -1.5, -0.75, -0.3, 0, 50]))
P("\n## same-day RSI(14) 5-min at entry (no prior-day warm-up; approx)"); P(bucket("rsi_sess", [0, 50, 55, 60, 65, 70, 101]))
P("\n## stock from-open % at entry"); P(bucket("fo", [-50, -2, -1, -0.5, 0, 0.5, 50]))
P("\n## SPY from-open % at entry"); P(bucket("spy_fo", [-10, -0.5, -0.25, 0, 0.25, 0.5, 10]))
P("\n## ADV $M (20d)"); P(bucket("adv", [0, 150, 300, 700, 2000, 1e7]))
P("\n## ATR% (14d)"); P(bucket("atrp", [0, 2, 3, 5, 8, 100]))
P("\n## price"); P(bucket("entry", [0, 20, 50, 100, 300, 1e5]))
P("\n## adv rank (universe 11-03)"); P(bucket("adv_rank", [0, 100, 250, 500, 1000, 1e5]))
P("\n## kind"); P(T.groupby("kind").agg(n=("R", "size"), avgR=("R", "mean"), totR=("R", "sum")).round(3).to_string())
P("\n## exit reason"); P(T.groupby("exit_reason").agg(n=("R", "size"), avgR=("R", "mean"), totR=("R", "sum"), mfe=("mfe", "mean")).round(3).to_string())
P("\n## MFE / MAE / give-back")
P("mean MFE", round(T.mfe.mean(), 3), "median", round(T.mfe.median(), 3), "| mean MAE", round(T.mae.mean(), 3))
gb = T[(T.mfe >= 0.5) & (T.R <= 0)]; P("give-back (MFE >= 0.5R, closed <= 0):", len(gb), f"({len(gb) / len(T):.0%})", "R", round(gb.R.sum(), 2))
P("reached 0.5R:", f"{(T.mfe >= 0.5).mean():.0%}", "| reached 1R:", f"{(T.mfe >= 1).mean():.0%}", "| hold to 15:55 no stop (gross) avg R", round(T.hold_r.mean(), 3))
P("flatten exits: avg R", round(T[T.exit_reason == "flatten"].R.mean(), 3), "| median exit time", T[T.exit_reason == "flatten"].exit_time.dt.strftime("%H:%M").value_counts().head(5).to_dict())

# same-symbol stacking with sister setups (any account, same date, same symbol, short side)
sis = []
for a in ("p", "t1", "t2"):
    x = q(a, "select symbol, strategy, side, date, entry_time, pnl_adj, entry, stop, shares from trades where run_id=1 and side=-1")
    x = x[x.strategy.str.startswith(SIS) & (x.strategy != SET)]; x["acct"] = a; sis.append(x)
sis = pd.concat(sis)
key = set(zip(sis.date, sis.symbol))
T["stack"] = [(d, s) in key for d, s in zip(T.date, T.symbol)]
P("\n## same-symbol same-day with sister shorts (RW1/RW3/RW5/MF2 lineage, any account)")
P(T.groupby("stack").agg(n=("R", "size"), avgR=("R", "mean"), totR=("R", "sum")).round(3).to_string())
P("sister strategies hit:", sis[[(d, s) in set(zip(T.date, T.symbol)) for d, s in zip(sis.date, sis.symbol)]].strategy.value_counts().to_dict())
T["lot"] = T.sort_values("entry_time").groupby(["date", "symbol"]).cumcount() + 1
P("\n## RW7 own re-entries (lot # per symbol-day)"); P(T.groupby(np.minimum(T.lot, 3)).agg(n=("R", "size"), avgR=("R", "mean"), totR=("R", "sum")).round(3).to_string())
P("\n## top symbols by total R"); g = T.groupby("symbol").agg(n=("R", "size"), totR=("R", "sum")).sort_values("totR")
P(pd.concat([g.head(5), g.tail(5)]).round(2).to_string())
(HERE / "live_out.txt").write_text("\n".join(out) + "\n")
T.drop(columns=["meta"]).to_csv(HERE / "live_trades.csv", index=False)
