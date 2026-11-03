"""QD1 (BDI 2026-11-03 night, QDAY focus: a quiet-day / both-direction setup). New idea, pre-declared before scoring.

Why: L6 tonight (research/bdi/swings/leads_bt.py) found that counter-index entries of the lab setups make +0.274R on
QUIET days (n 4,188) but -0.099R on up days - the quiet-day label is hindsight. QD1 asks whether "quiet so far" is
knowable intraday and tradeable directly: on a day whose SPY range so far is small, fade extensions from the open,
both sides (shorts above the open, longs below), so the book has no fixed market direction.

  decision bars  every 5-min bar close 10:30 .. 14:30 (lab frames, 2 years, locked block 2024-11..2025-02 not in the frame
                 directory; asserted)
  quiet so far   SPY's session range at that bar (dist_hod_atr + dist_lod_atr, SPY daily-ATR units) <= c, c in {0.6, 0.8}
  trigger        the symbol's own move from the open in its daily-ATR units >= +q -> SHORT, <= -q -> LONG, q in {0.3, 0.5}
                 (first trigger per symbol-day)
  universe       IDX = SPY QQQ IWM DIA | STK = top 500 names per day by adv20 x ATR% (adv20 >= $95M, blackout removed)
  exit           t1s1 lab bracket (target 1R / stop 0.25 x ATR_d, out by the close), production costs, tod multiplier
Configs: c 2 x q 2 x universe 2 = 8. Train < 2025-09-01, valid after. Report R by SPY day type (open-to-close +-0.25%)
and by SPY vs its open at 10:00; precision of "quiet so far" for the final day type vs the base rate.
Pass (Testing, BAR90): t >= 0.9 x bar(N tonight), train AND valid > 0, > 0 on up, down AND quiet days. Light lane gate:
train and valid >= -0.02R, 1.5-25 trades/session (IDX can not reach 1.5/session: lane gate n/a, reported).
Usage: python qd1.py <N_tonight> > qd1_out.txt     Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib
from mcf.research import gates as G
from mcf.research.generator import data as GD
HERE = Path(__file__).resolve().parent; NT = int(sys.argv[1]) if len(sys.argv) > 1 else 8
SPLIT = "2025-09-01"; IDX = {"SPY", "QQQ", "IWM", "DIA"}
COLS = ["symbol", "date", "tod", "close", "atr_d", "fromOpen", "adv20", "dist_hod_atr", "dist_lod_atr",
        "r_long_t1s1", "win_long_t1s1", "r_short_t1s1", "win_short_t1s1"]
T = []; SPY10 = {}; QUIET = []
for mo in lib.months():
    f = lib.load_month(mo, columns=COLS); f["date"] = f.date.astype(str)
    assert not f.date.between(*lib.LOCKED).any()
    sp = f[f.symbol == "SPY"]
    SPY10.update(sp[sp.tod == 1000].set_index("date").fromOpen.to_dict())
    rng = (sp.dist_hod_atr + sp.dist_lod_atr).rename("spy_rng"); spr = sp[["date", "tod"]].assign(spy_rng=rng.to_numpy())
    f = f[(f.tod >= 1030) & (f.tod <= 1430) & (f.adv20 >= 95e6) & (f.atr_d > 0)].merge(spr, on=["date", "tod"], how="left")
    QUIET.append(spr[(spr.tod >= 1030) & (spr.tod <= 1430)])
    f["atr_pct"] = f.atr_d / f.close * 100; f["mv"] = f.fromOpen / f.atr_pct
    sc = f[f.tod == 1030].assign(score=lambda x: x.adv20 * x.atr_pct)
    top = sc[~sc.symbol.isin(IDX)].groupby("date").score.rank(ascending=False, method="first") <= 500
    k500 = set(zip(sc[~sc.symbol.isin(IDX)][top].symbol, sc[~sc.symbol.isin(IDX)][top].date))
    f["uni"] = np.where(f.symbol.isin(IDX), "IDX", np.where([(s, d) in k500 for s, d in zip(f.symbol, f.date)], "STK", ""))
    f = f[f.uni != ""]
    f["bl"] = GD._blackout(f.symbol.to_numpy(), pd.to_datetime(f.date).dt.date.to_numpy()) & (f.uni == "STK")
    f = f[~f.bl]
    for c in (0.6, 0.8):
        for q in (0.3, 0.5):
            m = (f.spy_rng <= c) & (f.mv.abs() >= q)
            g = f[m].sort_values(["symbol", "date", "tod"]).groupby(["symbol", "date"]).head(1)
            for side, sg in (("short", -1), ("long", 1)):
                x = g[np.sign(g.mv) == -sg]
                r = G.prod_r(x[f"r_{side}_t1s1"].to_numpy(), x[f"win_{side}_t1s1"].to_numpy(), x.close.to_numpy(), x.atr_d.to_numpy(), "t1s1", tod=x.tod.to_numpy())
                T.append(pd.DataFrame({"cfg": f"QD1-c{int(c * 10):02d}-q{int(q * 10):02d}", "uni": x.uni.to_numpy(), "date": x.date.to_numpy(), "symbol": x.symbol.to_numpy(),
                                       "tod": x.tod.to_numpy(), "side": side, "r": r}))
T = pd.concat(T, ignore_index=True); T = T[np.isfinite(T.r)]
D = lib.daily(); D["date"] = D.date.astype(str); sd = D[D.symbol == "SPY"].set_index("date"); oc = (sd.close / sd.open - 1) * 100
dtype = pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index)
T["dtype"] = T.date.map(dtype); T["s10"] = np.where(T.date.map(SPY10) >= 0, "above10", "below10")
Q = pd.concat(QUIET); Q["dtype"] = Q.date.map(dtype)
bar = G.t_required(NT); t90 = round(max(1.35, 0.9 * bar), 2)
print(f"QD1: N tonight {NT}, full bar {bar}, BAR90 {t90}; days {T.date.nunique()}")
for c in (0.6, 0.8):
    qq = Q[Q.spy_rng <= c].groupby("date").dtype.first()
    print(f"  'quiet so far' c {c}: flagged days {len(qq)} of {Q.date.nunique()}, final day type quiet {(qq == 'quiet').mean():.0%} vs base {(Q.groupby('date').dtype.first() == 'quiet').mean():.0%}")
rows = []
for (cfg, uni), t in T.groupby(["cfg", "uni"]):
    s = G.summary(t); tr, va = t[t.date < SPLIT].r.mean(), t[t.date >= SPLIT].r.mean()
    ty = t.groupby("dtype").r.mean(); s1 = t.groupby("s10").r.mean(); sd_ = t.groupby("side").r.mean()
    g = t.groupby("date").r.sum(); share = round(g.max() / g.sum(), 2) if g.sum() > 0 else None
    per = s["n"] / max(1, s["days"])
    row = dict(config=f"{cfg}-{uni}", n=s["n"], per_day=round(per, 2), exp_r=s["exp_r"], t=s["t"], ex_best=s["ex_best_day"], best_share=share,
               train=round(tr, 3), valid=round(va, 3), up=round(ty.get("up", np.nan), 3), down=round(ty.get("down", np.nan), 3), quiet=round(ty.get("quiet", np.nan), 3),
               above10=round(s1.get("above10", np.nan), 3), below10=round(s1.get("below10", np.nan), 3), long=round(sd_.get("long", np.nan), 3), short=round(sd_.get("short", np.nan), 3))
    row["bar90"] = bool((s["t"] or 0) >= t90 and tr > 0 and va > 0 and min(row["up"], row["down"], row["quiet"]) > 0)
    row["lane"] = bool(tr >= -0.02 and va >= -0.02 and 1.5 <= per <= 25)
    rows.append(row)
R = pd.DataFrame(rows); pd.set_option("display.width", 250); print(R.to_string(index=False))
print(f"configs {len(R)}, BAR90 pass {int(R.bar90.sum())}, lane pass {int(R.lane.sum())}")
R.to_csv(HERE / "qd1_results.csv", index=False)
print("Educational only - not financial advice.")
