"""SCOUT-1125 ONGATE1 + TOWID1: overnight/intraday clientele ideas (backlog scout-1125-*).

PRE-REGISTERED 2026-11-25 (evening, after the close), before any read of the result. Educational only - not financial advice.
Sources (WebSearch summaries; the FMG/LSE PDFs were not opened - fmg.ac.uk is outside the session network, not worked around):
  Lou, Polk & Skouras (2026 version, "The Day Destroys the Night, Night Extends the Day"; FMG DP961 2026-07): smoothed
  PAST overnight market returns negatively forecast the INTRADAY component of the market return (clientele story: retail
  demand shows up overnight, institutional flow intraday). Lou, Polk & Skouras "A Tug of War" (JFE 2019): firm-level
  intraday returns continue intraday, overnight continue overnight, and the two components reverse each other.

IDEA A - ONGATE1 (pre-open market-level gate that predicts the CLOSE, not the moment):
  ON_K(t) = mean of SPY overnight returns open(d)/close(d-1)-1 over the K sessions BEFORE t (today's gap excluded; any
  pair straddling a calendar gap > 5 days is dropped, so no locked-block value is used). Known before 09:30.
  LONG use: on days with ON_K < 0 go long. SHORT-VETO use (mirror, Primary is ~80% short): on days with ON_K > 0 go short.
  Vehicle IDX: SPY, QQQ, IWM at the 09:50 bar; vehicle STK: every eligible non-ETP stock at the 09:50 bar (a basket that
  shows whether the gate moves the whole long book). Exit t1s1 (stop 0.25 x daily ATR, 1R target), flat 15:55.
  Grid: K {5, 20} x vehicle {IDX, STK} x use {LONG, SHORT} = 8 configs.
  Control: same vehicle and side on 200 random draws of the same number of sessions (rule must be >= 90th pct) and the
  complement (non-gate days) reported.
IDEA B - TOWID1 (stock-level intraday tug of war, long only):
  ID_K - ON_K per stock over the K sessions before t (intraday = close/open-1, overnight = open/close(prev)-1).
  Leg TOP: long the top decile of (ID_K - ON_K) among eligible names each day. Leg LOWON: long the bottom decile of ON_K
  ("day destroys the night"). Entry 09:50 bar, t1s1, flat 15:55. Grid: K {10, 20} x leg {TOP, LOWON} = 4 configs.
  Control: day-matched baseline (every eligible name long at 09:50 that day) and random entry bars on the same
  symbol-days (10:00-15:00, 200 draws).
Universe: lab frames, adv20 >= $95M, price >= $5, non-ETP per universe.csv names (as SQZR1). One trade per symbol-day.
Configs this run: 12 (A 8, B 4). Bars: per idea t_required(N) and the run total t_required(12) reported.
Costs: production + time-of-day (gates.lab_trades). Locked block 2024-11-01..2025-02-28 never read (lib.months()).
Pass (Testing bar): day-clustered t >= 0.9 x max(1.5, t_required(N)); TRAIN > 0 and VALID > 0; avg R w/o best day > 0
and best day's share < 50%; walk-forward positive months >= 54%; beats its control (>= 90th pct; B also > day baseline);
>= 0.2 trade/session.
Usage: python onid_bt.py -> onid_bt_out.txt
"""
import re, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402
HERE = Path(__file__).resolve().parent
NDRAW = 200; rng = np.random.default_rng(20261125)
TB = lambda n: round(max(1.35, 0.9 * G.t_required(n)), 3)
U = pd.read_csv(ROOT / "data/universe.csv", usecols=["symbol", "name"])
ETP = re.compile(r"ETF|ETN|Fund|Trust|ProShares|Direxion|GraniteShares|Tradr|Defiance|T-Rex|Leverage|2X|3X|Bull|Bear|iShares|SPDR|Invesco|Vanguard|Daily|Index", re.I)
STOCKS = set(U[~U.name.fillna("").str.contains(ETP)].symbol.astype(str)); IDX = ["SPY", "QQQ", "IWM"]
D = lib.daily().sort_values(["symbol", "date"]).reset_index(drop=True); D["dt"] = pd.to_datetime(D.date); D["date"] = D.date.astype(str)
g = D.groupby("symbol")
pc, pdt = g.close.shift(1), g.dt.shift(1)
ok = (D.dt - pdt).dt.days <= 5
D["on"] = np.where(ok, D.open / pc - 1, np.nan); D["id"] = D.close / D.open - 1
for K in (5, 10, 20):   # trailing means over the K sessions BEFORE t (shift 1), need >= K-1 valid values
    for c in ("on", "id"):
        D[f"{c}{K}"] = D.groupby("symbol")[c].transform(lambda s: s.shift(1).rolling(K, min_periods=K - 1).mean())
D["tow10"], D["tow20"] = D.id10 - D.on10, D.id20 - D.on20
FEAT = D.set_index(["symbol", "date"])[["on10", "on20", "tow10", "tow20"]]
sp = D[D.symbol == "SPY"].set_index("date"); GATE = sp[["on5", "on20"]]
oc = (sp.close / sp.open - 1) * 100
dtype = pd.Series(np.where(oc > 1.0, "up>1%", np.where(oc > .25, "up", np.where(oc < -.25, "down", "quiet"))), index=oc.index)
cols = ["symbol", "date", "tod", "close", "atr_d", "adv20", "r_long_t1s1", "win_long_t1s1", "r_short_t1s1", "win_short_t1s1"]
DAYR = {"IDX_long": [], "IDX_short": [], "STK_long": [], "STK_short": []}   # per-trade 09:50 trades, all days
TB_, POOL, NSESS = [], [], 0
for m in lib.months():
    assert m not in lib.LOCKED_MONTHS
    f = lib.load_month(m, columns=cols); f["date"] = f.date.astype(str); f["symbol"] = f.symbol.astype(str)
    NSESS += f[f.symbol == "SPY"].date.nunique()
    f = f[(f.tod >= 950) & (f.adv20 >= 95e6) & (f.close >= 5)].reset_index(drop=True)
    ix, st = f[f.symbol.isin(IDX)].reset_index(drop=True), f[f.symbol.isin(STOCKS)].reset_index(drop=True); del f
    for side in ("long", "short"):
        for nm, fr in (("IDX", ix), ("STK", st)):
            t = G.lab_trades(fr, (fr.tod == 950).to_numpy(), side, "t1s1"); t["date"] = t.date.astype(str); DAYR[f"{nm}_{side}"].append(t)
    k = pd.MultiIndex.from_arrays([st.symbol, st.date]); ft = FEAT.reindex(k)
    for c in FEAT.columns: st[c] = ft[c].to_numpy()
    o = (st.tod == 950).to_numpy(); s0 = st[o]
    for K in (10, 20):
        for leg, col, top in (("TOP", f"tow{K}", True), ("LOWON", f"on{K}", False)):
            q = s0.groupby("date")[col].transform(lambda x: x.rank(pct=True))
            pick = set(zip(s0.symbol[(q >= .9) if top else (q <= .1)], s0.date[(q >= .9) if top else (q <= .1)]))
            mk = o & np.array([(a, b) in pick for a, b in zip(st.symbol, st.date)])
            t = G.lab_trades(st, mk, "long", "t1s1"); t["date"] = t.date.astype(str); t["cfg"] = f"B_K{K}_{leg}"; TB_.append(t)
            pool = np.array([(a, b) in pick for a, b in zip(st.symbol, st.date)]) & (st.tod >= 1000).to_numpy() & (st.tod <= 1500).to_numpy()
            pr = G.prod_r(st.r_long_t1s1[pool], st.win_long_t1s1[pool], st.close[pool], st.atr_d[pool], "t1s1", tod=st.tod[pool].to_numpy(float))
            POOL.append(pd.DataFrame({"cfg": f"B_K{K}_{leg}", "symbol": st.symbol[pool].to_numpy(), "date": st.date[pool].to_numpy(), "pr": pr}))
    print(m, flush=True)
DAYR = {k: pd.concat(v, ignore_index=True) for k, v in DAYR.items()}
for v in DAYR.values(): assert not v.date.between(*lib.LOCKED).any()
SPLIT = lambda d: np.where(d <= "2025-12-31", "TRAIN", np.where(d <= "2026-10-05", "VALID", "LATE"))
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(out[-1], flush=True)
def report(cfg, X, ctrl_pct, ctrl_txt, extra="", nbar=8):
    s = G.summary(X)
    if s.get("n", 0) < 5: p(f"== {cfg}: n {s.get('n')} (too few)"); return
    gd = X.groupby("date").r.sum(); share = gd.max() / gd.sum() if gd.sum() > 0 else float("nan")
    X = X.assign(split=SPLIT(X.date), dt=X.date.map(dtype).fillna("?"))
    sp_ = {k: G.summary(X[X.split == k]) for k in ("TRAIN", "VALID", "LATE")}
    dts = {k: (len(v), round(v.r.mean(), 3)) for k, v in X.groupby("dt")}
    yr = {k: (len(v), round(v.r.mean(), 3)) for k, v in X.groupby(X.date.str[:4])}
    mo = X.groupby(X.date.str[:7]).r.mean(); wf = float((mo > 0).mean())
    p(f"== {cfg}: n {s['n']} sessions {s['days']} ({s['n'] / NSESS:.2f}/session) avg {s['exp_r']:+.3f} t {s['t']} win {s['win_rate']} "
      f"green {s['green_days']} w/o best {s['ex_best_day']:+.3f} best-day share {share:.0%}")
    for k, v in sp_.items(): p(f"   {k}: n {v.get('n')} avg {v.get('exp_r')} t {v.get('t')} w/o best {v.get('ex_best_day')}")
    p(f"   by year {yr} | SPY day type {dts} | WF positive months {wf:.0%} ({len(mo)})")
    p(f"   {ctrl_txt} -> rule pct {ctrl_pct:.0%} {extra}")
    gg = lambda k: (sp_[k].get("exp_r") or -1)
    ok = ((s["t"] or 0) >= TB(nbar) and gg("TRAIN") > 0 and gg("VALID") > 0 and s["ex_best_day"] > 0 and share < .5
          and wf >= .54 and ctrl_pct >= .9 and s["n"] / NSESS >= .2)
    p(f"   PASS (Testing bar t {TB(nbar)}) {ok}")
p(f"SCOUT-1125 | E2 2-year screen (lab frames + gates), production + TOD costs | configs 12 (A 8, B 4; bar A {TB(8)}, B {TB(4)}, "
  f"run total {TB(12)}) | sessions {NSESS} | locked block not read")
gd_ = GATE.reindex(sorted(DAYR["IDX_long"].date.unique()))
p(f"Gate coverage: ON5<0 on {(gd_.on5 < 0).mean():.0%} of sessions, ON20<0 on {(gd_.on20 < 0).mean():.0%}; "
  f"by year share ON20<0: {gd_.on20.lt(0).groupby(gd_.index.str[:4]).mean().round(2).to_dict()}")
for K in (5, 20):
    gk = GATE[f"on{K}"]
    for veh in ("IDX", "STK"):
        for use, side, cond in (("LONG", "long", lambda x: x < 0), ("SHORT", "short", lambda x: x > 0)):
            A = DAYR[f"{veh}_{side}"]; v = A.date.map(gk); X = A[cond(v).fillna(False).to_numpy()]
            Y = A[(~cond(v).fillna(True)).to_numpy()]
            days = A.date.unique(); nd = X.date.nunique(); dm = A.groupby("date").r.mean()
            xm = X.groupby("date").r.mean().mean()
            draws = np.array([dm.loc[rng.choice(days, nd, replace=False)].mean() for _ in range(NDRAW)])
            report(f"A_ON{K}_{veh}_{use}", X, float((draws < xm).mean()),
                   f"random sessions (same vehicle/side, {nd} of {len(days)} days, {NDRAW} draws): day-mean {draws.mean():+.3f} p90 {np.quantile(draws, .9):+.3f} vs rule day-mean {xm:+.3f}",
                   f"| complement days avg {Y.r.mean():+.3f} (n {len(Y)}) | all days avg {A.r.mean():+.3f}")
TBd = pd.concat(TB_, ignore_index=True); P = pd.concat(POOL, ignore_index=True)
base = DAYR["STK_long"].groupby("date").r.mean()
for cfg, X in TBd.groupby("cfg", sort=False):
    grp = {k: v.pr.to_numpy() for k, v in P[P.cfg == cfg].groupby(["symbol", "date"])}
    keys = [k for k in zip(X.symbol, X.date) if k in grp]
    draws = np.array([np.mean([rng.choice(grp[k]) for k in keys]) for _ in range(NDRAW)])
    exc = X.r.to_numpy() - X.date.map(base).to_numpy()
    report(cfg, X, float((draws < X.r.mean()).mean()) if np.nanmean(exc) > 0 else 0.0,
           f"random entry bar (same symbol-days 10:00-15:00, {NDRAW} draws): mean {draws.mean():+.3f} p90 {np.quantile(draws, .9):+.3f}",
           f"| excess over day-matched all-stock 09:50 long {np.nanmean(exc):+.3f}R (control pct forced 0 if excess <= 0)", nbar=4)
p("Educational only - not financial advice.")
(HERE / "onid_bt_out.txt").write_text("\n".join(out) + "\n")
