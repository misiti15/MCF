"""SCOUT-1127 ASYMREV1: asymmetric idiosyncratic reversal, long-only, intraday (backlog scout-1127-asymrev1-*).

PRE-REGISTERED 2026-11-27 (evening, market closed), before any trade below was built or scored.
Educational only - not financial advice.
Source (WebSearch summaries; nber.org is outside the session network, not worked around): Baldi-Lanfranchi, Collin-Dufresne
& Daniel, "Asymmetric Reversals" (NBER WP 35840 / SFI RP 26-66, 2026): split returns into a systematic (beta x market) part
and an idiosyncratic residual; the residual REVERSES while the systematic part trends, and NEGATIVE residual shocks reverse
FASTER than positive ones; the factor absorbs short-horizon anomalies. Intraday translation (long side = the fast-reverting
side): at decision time T, residual e = R_stock - beta x R_SPY (beta = 60-session daily close-to-close beta vs SPY, known at
the prior close), z = e / daily ATR%. LONG the 10 most negative z per day with z <= -1.0 (a real negative idiosyncratic
shock), regardless of the market move. Differs from the parked sw-w2-rv-stock-etf (two-leg spread z, hedged; PAIRS-1127
failed on the hedge leg's cost): one leg, unhedged, long only, residual from a beta model.
Grid (6 configs, all counted): base {CLOSE: R from prior close incl. gap, OPEN: R from the 09:30 open} x T {11:00, 13:00}
long (4); mirror SHORT of the 10 most positive z >= +1.0 at 11:00 CLOSE (1, the paper says it should be weaker); RAW-L
control = same selection on raw R/ATR% (no beta) at 11:00 CLOSE (1, mechanism check: does the residual add over raw?).
Universe/engine: lab frames (2-year, 22 months), adv20 >= $95M, price >= $5, non-ETP (as SCOUT-1125), entry at the T bar,
exit t1s1 (stop 0.25 x daily ATR, 1R target, flat 15:55), production + time-of-day costs (gates.lab_trades). Locked block
2024-11-01..2025-02-28 never read (lib.months()).
Controls: excess over the day-matched all-stock long at the same T; random entry bar on the same symbol-days (10:00-15:00,
200 draws) >= 90th pct; and the residual configs must beat RAW-L.
Pass (Testing bar): t >= 0.9 x max(1.5, t_req(14)) = run total with MEREB1 8 (also within-lineage 0.9 x t_req(6)); TRAIN and
VALID > 0; avg R w/o best day > 0, best-day share < 50%; WF positive months >= 54%; controls as above; >= 0.2 trade/session.
Usage: python asymrev_bt.py -> asymrev_bt_out.txt
"""
import re, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402
HERE = Path(__file__).resolve().parent
NDRAW = 200; rng = np.random.default_rng(20261127); K = 10
TB = round(max(1.35, 0.9 * G.t_required(14)), 3); TB6 = round(max(1.35, 0.9 * G.t_required(6)), 3)
U = pd.read_csv(ROOT / "data/universe.csv", usecols=["symbol", "name"])
ETP = re.compile(r"ETF|ETN|Fund|Trust|ProShares|Direxion|GraniteShares|Tradr|Defiance|T-Rex|Leverage|2X|3X|Bull|Bear|iShares|SPDR|Invesco|Vanguard|Daily|Index", re.I)
STOCKS = set(U[~U.name.fillna("").str.contains(ETP)].symbol.astype(str))
D = lib.daily().sort_values(["symbol", "date"]).reset_index(drop=True); D["date"] = D.date.astype(str); D["dt"] = pd.to_datetime(D.date)
g = D.groupby("symbol"); ok = (D.dt - g.dt.shift(1)).dt.days <= 5
D["ret"] = np.where(ok, D.close / g.close.shift(1) - 1, np.nan)
spr = D[D.symbol == "SPY"].set_index("date").ret; D["mkt"] = D.date.map(spr)
def beta(x):
    c = x.ret.rolling(60, min_periods=40).cov(x.mkt); v = x.mkt.rolling(60, min_periods=40).var()
    return (c / v).shift(1)
D["beta"] = D.groupby("symbol", group_keys=False).apply(beta)
BETA = D.set_index(["symbol", "date"]).beta
CFG = [("L", "CLOSE", 1100), ("L", "OPEN", 1100), ("L", "CLOSE", 1300), ("L", "OPEN", 1300), ("S", "CLOSE", 1100), ("RAW", "CLOSE", 1100)]
cols = ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap", "fromOpen", "r_long_t1s1", "win_long_t1s1", "r_short_t1s1", "win_short_t1s1"]
TR, BASE, POOL, NSESS = [], {1100: [], 1300: []}, [], 0
for m in lib.months():
    assert m not in lib.LOCKED_MONTHS
    f = lib.load_month(m, columns=cols); f["date"] = f.date.astype(str); f["symbol"] = f.symbol.astype(str)
    NSESS += f[f.symbol == "SPY"].date.nunique()
    sp = f[f.symbol == "SPY"].set_index(["date", "tod"])
    f = f[(f.tod >= 1000) & (f.tod <= 1500) & (f.adv20 >= 95e6) & (f.close >= 5) & f.symbol.isin(STOCKS)].reset_index(drop=True)
    k = pd.MultiIndex.from_arrays([f.date, f.tod])
    for b, fn in (("CLOSE", lambda x: (1 + x.gap / 100) * (1 + x.fromOpen / 100) - 1), ("OPEN", lambda x: x.fromOpen / 100)):
        f[f"R_{b}"] = fn(f); f[f"M_{b}"] = fn(sp).reindex(k).to_numpy()
    f["beta"] = BETA.reindex(pd.MultiIndex.from_arrays([f.symbol, f.date])).to_numpy()
    atrp = f.atr_d / f.close
    for b in ("CLOSE", "OPEN"):
        f[f"z_{b}"] = (f[f"R_{b}"] - f.beta * f[f"M_{b}"]) / atrp
    f["zraw"] = f.R_CLOSE / atrp
    for T in (1100, 1300):
        t = G.lab_trades(f, (f.tod == T).to_numpy(), "long", "t1s1"); t["date"] = t.date.astype(str); BASE[T].append(t)
    for side, b, T in CFG:
        col = "zraw" if side == "RAW" else f"z_{b}"
        s0 = f[(f.tod == T) & f[col].notna()]
        s0 = s0[s0[col] >= 1.0] if side == "S" else s0[s0[col] <= -1.0]
        s0 = s0.sort_values(col, ascending=(side != "S")).groupby("date").head(K)
        pick = set(zip(s0.symbol, s0.date)); sd = "short" if side == "S" else "long"
        inpick = np.array([(a, c) in pick for a, c in zip(f.symbol, f.date)])
        t = G.lab_trades(f, inpick & (f.tod == T).to_numpy(), sd, "t1s1"); t["date"] = t.date.astype(str); t["cfg"] = f"ASYMREV1|{side}|{b}|{T}"; TR.append(t)
        pr = G.prod_r(f[f"r_{sd}_t1s1"][inpick], f[f"win_{sd}_t1s1"][inpick], f.close[inpick], f.atr_d[inpick], "t1s1", tod=f.tod[inpick].to_numpy(float))
        POOL.append(pd.DataFrame({"cfg": f"ASYMREV1|{side}|{b}|{T}", "symbol": f.symbol[inpick].to_numpy(), "date": f.date[inpick].to_numpy(), "pr": pr}))
    print(m, flush=True)
TR = pd.concat(TR, ignore_index=True); P = pd.concat(POOL, ignore_index=True); BASE = {k: pd.concat(v) for k, v in BASE.items()}
assert not TR.date.between(*lib.LOCKED).any()
sp = lib.daily(); sp = sp[sp.symbol == "SPY"].copy(); sp["date"] = sp.date.astype(str); sp = sp.set_index("date")
oc = (sp.close / sp.open - 1) * 100
dtype = pd.Series(np.where(oc > 1.0, "up>1%", np.where(oc > .25, "up", np.where(oc < -.25, "down", "quiet"))), index=oc.index)
SPLIT = lambda d: np.where(d <= "2025-12-31", "TRAIN", np.where(d <= "2026-10-05", "VALID", "LATE"))
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(out[-1], flush=True)
p(f"SCOUT-1127 ASYMREV1 | E2 2-year screen (lab frames + gates), production + TOD costs | configs 6 (run total 14; bar {TB}, within-lineage {TB6}) | sessions {NSESS} | locked block not read")
raw_avg = TR[TR.cfg == "ASYMREV1|RAW|CLOSE|1100"].r.mean()
for cfg, X in TR.groupby("cfg", sort=False):
    s = G.summary(X); T = int(cfg.split("|")[-1]); side = cfg.split("|")[1]
    gd = X.groupby("date").r.sum(); share = gd.max() / gd.sum() if gd.sum() > 0 else float("nan")
    X = X.assign(split=SPLIT(X.date), dt=X.date.map(dtype).fillna("?"))
    sp_ = {k: G.summary(X[X.split == k]) for k in ("TRAIN", "VALID", "LATE")}
    dts = {k: (len(v), round(v.r.mean(), 3)) for k, v in X.groupby("dt")}
    mo = X.groupby(X.date.str[:7]).r.mean(); wf = float((mo > 0).mean())
    base = BASE[T].groupby("date").r.mean()
    exc = float(np.nanmean(X.r.to_numpy() - X.date.map(base).to_numpy())) * (1 if side != "S" else np.nan)
    grp = {k: v.pr.to_numpy() for k, v in P[P.cfg == cfg].groupby(["symbol", "date"])}
    keys = [k for k in zip(X.symbol, X.date) if k in grp]
    draws = np.array([np.mean([rng.choice(grp[k]) for k in keys]) for _ in range(NDRAW)]); pct = float((draws < X.r.mean()).mean())
    p(f"== {cfg}: n {s['n']} sessions {s['days']} ({s['n'] / NSESS:.2f}/session) avg {s['exp_r']:+.3f} t {s['t']} win {s['win_rate']} w/o best {s['ex_best_day']:+.3f} best-day share {share:.0%}")
    for k, v in sp_.items(): p(f"   {k}: n {v.get('n')} avg {v.get('exp_r')} t {v.get('t')} w/o best {v.get('ex_best_day')}")
    p(f"   SPY day type {dts} | WF positive months {wf:.0%} ({len(mo)})")
    p(f"   excess over day-matched all-stock long @{T}: {exc:+.3f}R | random entry bar 10:00-15:00 ({NDRAW}): mean {draws.mean():+.3f} p90 {np.quantile(draws, .9):+.3f} -> pct {pct:.0%} | RAW-L avg {raw_avg:+.3f}")
    okk = ((s["t"] or 0) >= TB and (sp_["TRAIN"].get("exp_r") or -1) > 0 and (sp_["VALID"].get("exp_r") or -1) > 0 and s["ex_best_day"] > 0
           and share < .5 and wf >= .54 and pct >= .9 and s["n"] / NSESS >= .2 and (side == "S" or (exc > 0 and (side == "RAW" or s["exp_r"] > raw_avg))))
    p(f"   PASS (Testing bar t {TB}) {okk}{' (RAW-L is a control, not a candidate)' if side == 'RAW' else ''}")
p("Educational only - not financial advice.")
(HERE / "asymrev_bt_out.txt").write_text("\n".join(out) + "\n")
