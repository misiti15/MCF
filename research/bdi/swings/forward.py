"""Shadow-forward logging for the swing-autopsy hypotheses (research/bdi/swings/hypotheses.jsonl); run once per session
after the close by the BDI daily run. Read-only: journals and SIP bars in a scratch dir; nothing on the trading path.

Per hypothesis (rule fixed in hypotheses.jsonl; live journals, run 1, all five accounts, R = pnl_adj / $ risk, costs in):
  L1  NS5 longs (any account) split by the symbol's 20-session 5-min beta to SPY (<= -1.5 = class A)
  L2  rotation-turn trigger (QQQ new session high 10:30-11:30 while IWM >= +0.40% from open and >= 0.10% below its HOD
      for >= 5 min); tagged = RW3/RW5/MF2/MF4-family shorts entered 1-30 min after the trigger, non-tech names
  L3  qualifying up morning (SPY >= +0.15%, IWM >= +0.25% from open at the 10:00 bar): family shorts before / after the
      first 5-min SPY bar after 10:30 closing below the prior bar's low (10:50 if none)
  L6  counter-index entries (short with SPY >= +0.25% from open at the fill, long with SPY <= -0.25%) vs all others
Appends one row per hypothesis to research/bdi/swings/forward.csv (idempotent by date) and refreshes the running
forward n / avg R / t in hypotheses.jsonl (sessions flagged in_sample are excluded from the running numbers).
Usage: python forward.py <scratch> <day> [--in-sample]
  <scratch>/<acct>/journal.db, <scratch>/bars/<SYM>.parquet (1-min SIP; SPY, QQQ, IWM + traded symbols),
  optional <scratch>/mh/<day>/bars5.parquet (5-min, >= 20 sessions) for the L1 beta.
Educational only - not financial advice."""
import json, sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
S, D = Path(sys.argv[1]), sys.argv[2]; INS = "--in-sample" in sys.argv
HERE = Path(__file__).resolve().parent; TZ = "America/New_York"
FAMK = ("RW3", "RW5", "MF2", "MF4")
TECH = {"XLK", "SMH", "SOXX", "SOXL", "SOXS", "TQQQ", "SQQQ", "QQQ", "AAPL", "MSFT", "NVDA", "AMD", "AVGO", "MU", "INTC", "CRM",
        "ADBE", "ORCL", "NOW", "WDAY", "ZM", "INTU", "ADSK", "DOCU", "SNOW", "PLTR", "CRWD", "PANW", "TXN", "QCOM", "AMAT", "LRCX", "KLAC"}
def bars(s):
    f = S / "bars" / f"{s}.parquet"
    if not f.exists(): return None
    b = pd.read_parquet(f); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ); return b.between_time("09:30", "15:59")
T = []
for a in ("p", "t1", "t2", "gy", "gen"):
    t = pd.read_sql("select symbol, strategy, side, entry_time, entry, stop, shares, pnl_adj from trades where date=? and run_id=1",
                    sqlite3.connect(S / a / "journal.db"), params=(D,))
    t["acct"] = a; T.append(t)
T = pd.concat(T, ignore_index=True)
T["R"] = T.pnl_adj / ((T.entry - T.stop).abs() * T.shares).replace(0, np.nan)
T["et"] = pd.to_datetime(T.entry_time, utc=True, format="mixed").dt.tz_convert(TZ)
T["hm"] = T.et.dt.hour * 100 + T.et.dt.minute
spy, qqq, iwm = bars("SPY"), bars("QQQ"), bars("IWM")
fo = lambda b, t: (b[b.index < t].close.iloc[-1] / b.open.iloc[0] - 1) * 100 if len(b[b.index < t]) else np.nan   # last closed 1-min bar
fam = T[T.strategy.str.contains("|".join(FAMK)) & (T.side == -1)]
out = []
def row(h, n, r, extra=""):
    out.append(dict(date=D, hyp=h, n=int(n), avgR=round(float(r), 4) if n else None, note=extra, in_sample=INS))
# L1
ns5 = T[T.strategy.str.startswith("NS5") & (T.side == 1)].copy(); beta = {}
b5f = S / "mh" / D / "bars5.parquet"
if b5f.exists() and len(ns5):
    B5 = pd.read_parquet(b5f); B5 = B5[B5.index < pd.Timestamp(D, tz=TZ)]
    R5 = B5[B5.symbol.isin(set(ns5.symbol) | {"SPY"})].pivot_table(index=B5[B5.symbol.isin(set(ns5.symbol) | {"SPY"})].index, columns="symbol", values="close").pct_change(fill_method=None).tail(20 * 78)
    for s_ in set(ns5.symbol):
        x = R5[[s_, "SPY"]].dropna() if s_ in R5 else pd.DataFrame()
        beta[s_] = np.cov(x[s_], x.SPY)[0, 1] / x.SPY.var() if len(x) > 50 else np.nan
ns5["A"] = ns5.symbol.map(beta) <= -1.5
row("L1", ns5.A.sum(), ns5[ns5.A].R.mean() if ns5.A.any() else 0, f"class B n {int((~ns5.A).sum())} avg {ns5[~ns5.A].R.mean():+.3f}" if len(ns5) else "no NS5 longs")
# L2
trig = None
if qqq is not None and iwm is not None:
    q, i = qqq.copy(), iwm.copy(); q["hod"] = q.high.cummax(); i["hod"] = i.high.cummax()
    i["fo"] = (i.close / i.open.iloc[0] - 1) * 100; i["below"] = (i.hod - i.close) / i.close * 100
    run = (i.below >= 0.10).astype(int); run = run.groupby((run == 0).cumsum()).cumsum()
    nh = q.high > q.hod.shift(1)
    m = nh & (i.fo.reindex(q.index) >= 0.40) & (run.shift(1).reindex(q.index) >= 5)
    m = m[(m.index.hour * 100 + m.index.minute >= 1030) & (m.index.hour * 100 + m.index.minute <= 1130)]
    trig = m[m].index.min() if m.any() else None
if trig is not None and trig == trig:
    tg = fam[(fam.et > trig) & (fam.et <= trig + pd.Timedelta(minutes=30)) & ~fam.symbol.isin(TECH)]
    oth = fam[~fam.index.isin(tg.index)]
    row("L2", len(tg), tg.R.mean() if len(tg) else 0, f"trigger {trig:%H:%M}; other family shorts n {len(oth)} avg {oth.R.mean():+.3f}")
else:
    row("L2", 0, 0, "no trigger")
# L3
s10 = fo(spy, spy.index[0].normalize() + pd.Timedelta(hours=10)); i10 = fo(iwm, iwm.index[0].normalize() + pd.Timedelta(hours=10))
if s10 >= 0.15 and i10 >= 0.25:
    s5 = spy.resample("5min", label="right", closed="left").agg({"close": "last", "low": "min"}).dropna()
    s5["pl"] = s5.low.shift(1); hm = s5.index.hour * 100 + s5.index.minute
    br = s5[(hm > 1030) & (s5.close < s5.pl)]
    cut = br.index[0] if len(br) else spy.index[0].normalize() + pd.Timedelta(hours=10, minutes=50)
    bf, af = fam[fam.et < cut], fam[fam.et >= cut]
    row("L3", len(fam), (af.R.mean() if len(af) else np.nan) - (bf.R.mean() if len(bf) else np.nan) if len(af) and len(bf) else 0,
        f"qualifying (SPY {s10:+.2f}%, IWM {i10:+.2f}% at 10:00); cut {cut:%H:%M}; before n {len(bf)} {bf.R.mean():+.3f}, after n {len(af)} {af.R.mean():+.3f}; avgR = after - before")
else:
    row("L3", 0, 0, f"not qualifying (SPY {s10:+.2f}%, IWM {i10:+.2f}% at 10:00)")
# L6
T["spy_fo"] = [fo(spy, t) for t in T.et]
T["counter"] = ((T.side == -1) & (T.spy_fo >= 0.25)) | ((T.side == 1) & (T.spy_fo <= -0.25))
c = T[T.counter]; o = T[~T.counter]
row("L6", len(c), c.R.mean() if len(c) else 0, f"others n {len(o)} avg {o.R.mean():+.3f}; counter minus others {c.R.mean() - o.R.mean():+.3f}")
F = pd.DataFrame(out); fp = HERE / "forward.csv"
if fp.exists():
    old = pd.read_csv(fp); old = old[old.date != D]; F = pd.concat([old, F], ignore_index=True)
F.to_csv(fp, index=False)
# refresh running forward numbers
hp = HERE / "hypotheses.jsonl"; hs = [json.loads(l) for l in hp.read_text().splitlines() if l.strip()]
for h in hs:
    x = F[(F.hyp == h["id"].split("-")[-1]) & (~F.in_sample.astype(bool)) & (F.n > 0)]
    n = int(x.n.sum()); mu = float((x.n * x.avgR).sum() / n) if n else None
    t = float(x.avgR.mean() / (x.avgR.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 and x.avgR.std() > 0 else None
    h["forward"] = dict(sessions=int(len(x)), n=n, avgR=round(mu, 4) if mu is not None else None, t=round(t, 2) if t is not None else None, through=D)
hp.write_text("".join(json.dumps(h) + "\n" for h in hs))
print(F[F.date == D].to_string(index=False)); print("Educational only - not financial advice.")
