"""SCOUT-1123 SQZR1: day-2 fade of a large one-day jump (backlog scout-1123-day2-jump-fade).

PRE-REGISTERED 2026-11-23 (evening, after the close), before any read of the result. Educational only - not financial advice.
Source idea: large one-day price jumps in liquid (heavily shorted) stocks reverse the next day; the squeeze pressure
lasts about a day and a half, then fades (academic study seen via WebSearch summary; S&P Global / Bespoke squeeze
commentary). No short-interest data on disk, so this is the proxy-free form: every liquid non-ETP stock.
Rule: prior-day close-to-close move J1 = close(t-1)/close(t-2) - 1.
  FADE-SHORT: J1 >= +J -> short on session t; FADE-LONG (mirror, the long form): J1 <= -J -> buy on session t.
  Trigger T0: the 09:50 bar close. Trigger T1 (confirmation): first bar 09:50..11:00 with fromOpen < 0 and below VWAP
  (short) / fromOpen > 0 and above VWAP (long). Stop 0.25 x daily ATR, target 1R (t1s1), else flat 15:55.
Universe: lab frames, adv20 >= $95M, price >= $5, ETPs excluded (universe.csv name regex). One trade per symbol-day.
Grid (configs 8): J {8%, 15%} x trigger {T0, T1} x side {fade-short, fade-long}.
Costs: production + time-of-day (gates.lab_trades). Locked block 2024-11-01..2025-02-28 never read (lib.months()).
Pass (Testing bar, N = 8): day-clustered t >= 0.9 x max(1.5, t_required(8)); TRAIN > 0 and VALID > 0; avg R w/o best
day > 0 and best day's share of total R < 50%; walk-forward positive months >= 54%; beats random entries (rule avg >=
90th pct of 200 draws: same symbol-days, random entry bar 10:00..15:00, same side/exit) AND beats the day-matched
baseline (same side at the same trigger bar on every eligible name that day, T0 only); >= 0.2 trade/session.
Usage: python sqzr_bt.py -> sqzr_bt_out.txt
"""
import re, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402
HERE = Path(__file__).resolve().parent
JS, TRIGS, SIDES = (0.08, 0.15), ("T0", "T1"), ("short", "long")
N_CFG = 8; TBAR = round(max(1.35, 0.9 * G.t_required(N_CFG)), 3); NDRAW = 200
rng = np.random.default_rng(20261123)
U = pd.read_csv(ROOT / "data/universe.csv", usecols=["symbol", "name"])
ETP = re.compile(r"ETF|ETN|Fund|Trust|ProShares|Direxion|GraniteShares|Tradr|Defiance|T-Rex|Leverage|2X|3X|Bull|Bear|iShares|SPDR|Invesco|Vanguard|Daily|Index", re.I)
STOCKS = set(U[~U.name.fillna("").str.contains(ETP)].symbol.astype(str))
D_ = lib.daily().sort_values(["symbol", "date"]); D_["date"] = D_.date.astype(str)
D_["j1"] = D_.groupby("symbol").close.pct_change().groupby(D_.symbol).shift(1)   # close(t-1)/close(t-2)-1, known pre-open
J1 = D_.set_index(["symbol", "date"]).j1
sp = D_[D_.symbol == "SPY"].set_index("date"); oc = (sp.close / sp.open - 1) * 100
dtype = pd.Series(np.where(oc > 1.0, "up>1%", np.where(oc > .25, "up", np.where(oc < -.25, "down", "quiet"))), index=oc.index)
cols = ["symbol", "date", "tod", "close", "fromOpen", "vwapDistPct", "atr_d", "adv20",
        "r_long_t1s1", "win_long_t1s1", "r_short_t1s1", "win_short_t1s1"]
T, POOL, BASE, NSESS = [], [], [], 0
for m in lib.months():
    assert m not in lib.LOCKED_MONTHS
    f = lib.load_month(m, columns=cols); f["date"] = f.date.astype(str); f["symbol"] = f.symbol.astype(str)
    NSESS += f[f.symbol == "SPY"].date.nunique()
    e = f[f.symbol.isin(STOCKS) & (f.adv20 >= 95e6) & (f.close >= 5) & (f.tod >= 950)].reset_index(drop=True); del f
    e["j1"] = J1.reindex(pd.MultiIndex.from_arrays([e.symbol, e.date])).to_numpy()
    for side in SIDES:   # day-matched baseline: every eligible name at 09:50, same side
        b = G.lab_trades(e, (e.tod == 950).to_numpy(), side, "t1s1"); b["date"] = b.date.astype(str); b["side"] = side
        BASE.append(b.groupby(["date", "side"]).r.mean().reset_index())
    sel = e[(e.j1.abs() >= min(JS))].reset_index(drop=True)
    for side in SIDES:
        ok = np.isfinite(sel[f"r_{side}_t1s1"].to_numpy(float)) & (sel.atr_d.to_numpy(float) > 0)
        pr = np.where(ok, G.prod_r(sel[f"r_{side}_t1s1"], sel[f"win_{side}_t1s1"], sel.close, sel.atr_d, "t1s1", tod=sel.tod.to_numpy(float)), np.nan)
        POOL.append(pd.DataFrame({"symbol": sel.symbol, "date": sel.date, "side": side, "pr": pr})[(sel.tod >= 1000).to_numpy() & (sel.tod <= 1500).to_numpy() & ok])
        sgn = 1 if side == "short" else -1
        for J in JS:
            jm = (sgn * sel.j1 >= J).to_numpy()
            conf = ((sgn * sel.fromOpen < 0) & (sgn * sel.vwapDistPct < 0) & (sel.tod <= 1100)).to_numpy()
            for trig, mk in (("T0", jm & (sel.tod == 950).to_numpy()), ("T1", jm & conf)):
                t = G.lab_trades(sel, mk, side, "t1s1"); t["date"] = t.date.astype(str); t["cfg"] = f"{side}_J{int(J*100)}_{trig}"; t["side"] = side
                T.append(t)
    print(m, flush=True)
T = pd.concat(T, ignore_index=True); assert not T.date.between(*lib.LOCKED).any()
P = pd.concat(POOL, ignore_index=True); grp = {k: v.pr.to_numpy() for k, v in P.groupby(["symbol", "date", "side"])}
B = pd.concat(BASE, ignore_index=True).set_index(["date", "side"]).r
T["split"] = np.where(T.date <= "2025-12-31", "TRAIN", np.where(T.date <= "2026-10-05", "VALID", "LATE"))
T["dt"] = T.date.map(dtype).fillna("?")
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(out[-1], flush=True)
p(f"SQZR1 | E2 2-year screen (lab frames + gates), production + TOD costs | configs {N_CFG} | Testing bar t {TBAR} "
  f"(full bar {G.t_required(N_CFG)}) | sessions {NSESS} | stocks in universe.csv non-ETP {len(STOCKS)} | locked block not read")
for cfg, X in T.groupby("cfg", sort=False):
    s = G.summary(X); side = X.side.iloc[0]
    if s["n"] < 5: p(f"== {cfg}: n {s['n']} (too few)"); continue
    g_ = X.groupby("date").r.sum(); share = g_.max() / g_.sum() if g_.sum() > 0 else float("nan")
    keys = [(a, b, side) for a, b in zip(X.symbol, X.date)]
    draws = np.array([np.nanmean([rng.choice(grp[k]) for k in keys if k in grp]) for _ in range(NDRAW)])
    pct = float((draws < s["exp_r"]).mean())
    base = B.reindex(pd.MultiIndex.from_arrays([X.date, [side] * len(X)])).to_numpy(); exc = X.r.to_numpy() - base
    sp_ = {k: G.summary(X[X.split == k]) for k in ("TRAIN", "VALID", "LATE")}
    dts = {k: (len(v), round(v.r.mean(), 3)) for k, v in X.groupby("dt")}
    mo = X.assign(mo=X.date.str[:7]).groupby("mo").r.mean(); wf = float((mo > 0).mean())
    p(f"== {cfg}: n {s['n']} sessions {s['days']} ({s['n'] / NSESS:.2f}/session) avg {s['exp_r']:+.3f} t {s['t']} win {s['win_rate']} "
      f"green {s['green_days']} w/o best {s['ex_best_day']:+.3f} best-day share {share:.0%}")
    for k, v in sp_.items():
        p(f"   {k}: n {v.get('n')} avg {v.get('exp_r')} t {v.get('t')} w/o best {v.get('ex_best_day')}")
    p(f"   SPY day type: {dts} | WF positive months {wf:.0%} ({len(mo)})")
    p(f"   random entry bar (same symbol-days, 10:00-15:00, {NDRAW} draws): mean {draws.mean():+.3f} p90 {np.quantile(draws, .9):+.3f} -> rule pct {pct:.0%}")
    p(f"   excess over day-matched 09:50 baseline (all eligible names, same side): {np.nanmean(exc):+.3f}R")
    g = lambda k: (sp_[k].get("exp_r") or -1)
    ok = ((s["t"] or 0) >= TBAR and g("TRAIN") > 0 and g("VALID") > 0 and s["ex_best_day"] > 0 and (share < .5)
          and wf >= 0.54 and pct >= 0.9 and np.nanmean(exc) > 0 and s["n"] / NSESS >= 0.2)
    p(f"   PASS (Testing bar) {ok}")
p("Educational only - not financial advice.")
(HERE / "sqzr_bt_out.txt").write_text("\n".join(out) + "\n")
