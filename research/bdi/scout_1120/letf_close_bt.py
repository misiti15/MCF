"""SCOUT-1120 LETF1: leveraged-ETP rebalance-flow continuation into the close (backlog scout-1120-letf-rebalance-close-long).

PRE-REGISTERED 2026-11-20 ~21:30 ET, before any read of the result. Educational only - not financial advice.
Source idea: leveraged / inverse ETPs rebalance near the close in the direction of the day's move (hedge flow ~ L(L-1) x AUM
x move), so a large intraday move tends to extend into the close (Cheng-Madhavan; Rodier-Haryanto-Shum-Hejazi 2012;
Chan 2013 "buy the leveraged ETF after a large intraday move, hold to the close"; 2026 JPM/Bloomberg coverage of $150B
of rebalance selling). Long-only form (no borrow): buy the ETP that is already UP by >= |L| x X % from the open at the
entry bar (the bull fund on an up day, the inverse fund on a down day), stop 0.25 x daily ATR (t1s1), else flat 15:55.

Universe: equity leveraged / inverse ETPs in the lab (index, sector, single-stock; -1x inverse index funds included since
they rebalance too); crypto, bond, commodity and VIX ETPs excluded. adv20 >= $95M, price >= $5. One trade per symbol-day.
Grid (configs 4): X {0.75, 1.25} x entry bar close {14:30, 15:00}.
Costs: production + time-of-day (gates.lab_trades). Locked block 2024-11-01..2025-02-28 never read (lib.months()).
Pass (Testing bar, rule 22, N = 4): day-clustered t >= 0.9 x max(1.5, sqrt(2 ln 4)) = 1.50; TRAIN > 0 and VALID > 0;
> 0 on SPY up AND down sessions; avg R w/o best day > 0; walk-forward positive months >= 54%; beats random entries
(rule avg >= 90th pct of 200 draws: same symbol-days, random entry bar 10:00..15:00, same exit); >= 0.5 trade/session.
Usage: python letf_close_bt.py -> letf_close_bt_out.txt
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402
HERE = Path(__file__).resolve().parent
LEV = {  # family, leverage
    "TQQQ": ("index", 3), "SQQQ": ("index", -3), "QLD": ("index", 2), "QID": ("index", -2), "SPXL": ("index", 3),
    "SPXS": ("index", -3), "UPRO": ("index", 3), "SPXU": ("index", -3), "SSO": ("index", 2), "SDS": ("index", -2),
    "UDOW": ("index", 3), "SDOW": ("index", -3), "TNA": ("index", 3), "TZA": ("index", -3),
    "PSQ": ("index", -1), "SPDN": ("index", -1), "RWM": ("index", -1),
    "SOXL": ("sector", 3), "SOXS": ("sector", -3), "TECL": ("sector", 3), "LABD": ("sector", -3), "ERY": ("sector", -2),
    "NUGT": ("sector", 2),
    "AMDL": ("single", 2), "CONL": ("single", 2), "NVDL": ("single", 2), "TSLL": ("single", 2), "TSLQ": ("single", -2),
    "GGLL": ("single", 2), "METU": ("single", 2), "MSFU": ("single", 2), "MSTU": ("single", 2), "MSTX": ("single", 2)}
XS, TODS = (0.75, 1.25), (1430, 1500)
N_CFG = 4; TBAR = round(max(1.35, 0.9 * G.t_required(N_CFG)), 3); NDRAW = 200
rng = np.random.default_rng(20261120)
D_ = lib.daily(); sp = D_[D_.symbol == "SPY"].sort_values("date").set_index("date")
oc = (sp.close / sp.open - 1) * 100; oc.index = oc.index.astype(str)
dtype = pd.Series(np.where(oc > .25, "up", np.where(oc < -.25, "down", "quiet")), index=oc.index)
cols = ["symbol", "date", "tod", "close", "fromOpen", "atr_d", "adv20", "r_long_t1s1", "win_long_t1s1"]
T, POOL, NSESS = [], [], 0
for m in lib.months():
    assert m not in lib.LOCKED_MONTHS
    f = lib.load_month(m, columns=cols); f["date"] = f.date.astype(str); f["symbol"] = f.symbol.astype(str)
    NSESS += f[f.symbol == "SPY"].date.nunique()
    e = f[f.symbol.isin(list(LEV)) & (f.adv20 >= 95e6) & (f.close >= 5)].sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
    del f
    lev = e.symbol.map(lambda s: abs(LEV[s][1])).to_numpy(float)
    ok = np.isfinite(e.r_long_t1s1.to_numpy(float)) & (e.atr_d.to_numpy(float) > 0)
    e["pr"] = np.where(ok, G.prod_r(e.r_long_t1s1, e.win_long_t1s1, e.close, e.atr_d, "t1s1", tod=e.tod.to_numpy(float)), np.nan)
    POOL.append(e.loc[(e.tod >= 1000) & (e.tod <= 1500) & ok, ["symbol", "date", "tod", "pr"]])
    for x in XS:
        for tod in TODS:
            mk = ((e.tod == tod) & (e.fromOpen >= lev * x)).to_numpy()
            t = G.lab_trades(e, mk, "long", "t1s1"); t["date"] = t.date.astype(str); t["cfg"] = f"X{x}_{tod}"
            T.append(t)
    print(m, flush=True)
T = pd.concat(T, ignore_index=True); assert not T.date.between(*lib.LOCKED).any()
P = pd.concat(POOL, ignore_index=True); grp = {k: v.pr.to_numpy() for k, v in P.groupby(["symbol", "date"])}
T["split"] = np.where(T.date <= "2025-12-31", "TRAIN", np.where(T.date <= "2026-10-05", "VALID", "LATE"))
T["dt"] = T.date.map(dtype).fillna("?"); T["fam"] = T.symbol.map(lambda s: LEV[s][0])
T["side"] = T.symbol.map(lambda s: "inverse" if LEV[s][1] < 0 else "bull")
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(out[-1], flush=True)
p(f"LETF1 | E2 2-year screen (lab frames + gates), production + TOD costs | configs {N_CFG} | Testing bar t {TBAR} "
  f"(full bar {G.t_required(N_CFG)}) | sessions {NSESS} | locked block not read")
for cfg, X in T.groupby("cfg", sort=False):
    s = G.summary(X)
    keys = list(zip(X.symbol, X.date))
    draws = np.array([np.nanmean([rng.choice(grp[k]) for k in keys if k in grp]) for _ in range(NDRAW)])
    pct = float((draws < s["exp_r"]).mean())
    sp_ = {k: G.summary(X[X.split == k]) for k in ("TRAIN", "VALID", "LATE")}
    dts = {k: (len(v), round(v.r.mean(), 3)) for k, v in X.groupby("dt")}
    mo = X.assign(mo=X.date.str[:7]).groupby("mo").r.mean(); wf = float((mo > 0).mean())
    p(f"== {cfg}: n {s['n']} sessions {s['days']} ({s['n'] / NSESS:.2f}/session) avg {s['exp_r']:+.3f} t {s['t']} win {s['win_rate']} "
      f"green {s['green_days']} w/o best {s['ex_best_day']:+.3f}")
    for k, v in sp_.items():
        p(f"   {k}: n {v.get('n')} avg {v.get('exp_r')} t {v.get('t')} w/o best {v.get('ex_best_day')}")
    p(f"   SPY day type: {dts} | WF positive months {wf:.0%} ({len(mo)})")
    p(f"   random entry bar (same symbol-days, 10:00-15:00, {NDRAW} draws): mean {draws.mean():+.3f} p90 {np.quantile(draws, .9):+.3f} -> rule pct {pct:.0%}")
    p("   by family: " + ", ".join(f"{k} n {len(v)} {v.r.mean():+.3f}" for k, v in X.groupby("fam")) +
      " | by side: " + ", ".join(f"{k} n {len(v)} {v.r.mean():+.3f}" for k, v in X.groupby("side")))
    ps = X.groupby("date").r.mean()
    p(f"   as one bet per session: {ps.mean():+.3f}R, green {(ps > 0).mean():.0%}, t {ps.mean() / (ps.std(ddof=1) / np.sqrt(len(ps))):.2f}")
    g = lambda k: (sp_[k].get("exp_r") or -1)
    ok = ((s["t"] or 0) >= TBAR and g("TRAIN") > 0 and g("VALID") > 0 and dts.get("up", (0, -1))[1] > 0
          and dts.get("down", (0, -1))[1] > 0 and s["ex_best_day"] > 0 and wf >= 0.54 and pct >= 0.9 and s["n"] / NSESS >= 0.5)
    p(f"   PASS (Testing bar) {ok}")
p("Educational only - not financial advice.")
(HERE / "letf_close_bt_out.txt").write_text("\n".join(out) + "\n")
