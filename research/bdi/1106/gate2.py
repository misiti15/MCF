"""GATE2-A / GATE2-B (GATE2_PLAN.md, pre-registered): held-side pullback entries after a confirmed compass reading.
Usage: python gate2.py -> gate2_out.txt. Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF"); sys.path.insert(0, "/home/user/MCF/research/history2y")
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "never reads the locked block"
import lib  # noqa: E402
from mcf.research.gates import tod_cost_mult  # noqa: E402
HERE = Path(__file__).resolve().parent; LOCK = ("2024-11-01", "2025-02-28")
P = []
def pr(*a): P.append(" ".join(str(x) for x in a)); print(P[-1], flush=True)
COLS = ["symbol", "date", "tod", "close", "fromOpen", "vwapDistPct", "rsi5", "dist_hod_atr", "dist_lod_atr", "atr_d", "adv20", "r_long_t1s1", "r_short_t1s1"]
D = pd.read_parquet("/home/user/MCF/research/history2y/data/daily.parquet"); D["date"] = D.date.astype(str)
sd = D[D.symbol == "SPY"].set_index("date"); oc = (sd.close / sd.open - 1) * 100
dtype = pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index)
out = []
for m in lib.months():
    if m in lib.LOCKED_MONTHS: continue
    f = lib.load_month(m, columns=COLS); f = f[(f.tod >= 1030) & (f.tod <= 1400) & (f.adv20 >= 95e6) & (f.close >= 5)].copy()
    f["date"] = f.date.astype(str); f["symbol"] = f.symbol.astype(str)
    assert not ((f.date >= LOCK[0]) & (f.date <= LOCK[1])).any()
    cx = pd.read_parquet(f"/home/user/MCF/research/history2y/data/context/month={m}.parquet"); cx["date"] = cx.date.astype(str)
    s10 = cx[cx.tod == 1000].set_index("date").spy_fo
    f = f.merge(cx[["date", "tod", "spy_fo"]], on=["date", "tod"], how="left"); f["s10"] = np.where(f.date.map(s10) >= 0, "above", "below")
    sg = np.sign(f.spy_fo); conf = f.spy_fo.abs() >= 0.30
    L = sg > 0; Sh = sg < 0
    a_l = (f.fromOpen >= 0.5) & f.vwapDistPct.between(0, 0.20) & (f.rsi5 <= 40)
    a_s = (f.fromOpen <= -0.5) & f.vwapDistPct.between(-0.20, 0) & (f.rsi5 >= 60)
    b_l = f.fromOpen.between(0, 0.30) & (f.dist_hod_atr >= 0.5)
    b_s = f.fromOpen.between(-0.30, 0) & (f.dist_lod_atr >= 0.5)
    for cfg, ml, ms in (("A", a_l, a_s), ("B", b_l, b_s)):
        hit = (L & ml) | (Sh & ms)
        x = f[hit].copy(); x["side"] = np.where(L[hit], 1, -1); x["conf"] = conf[hit]; x["cfg"] = cfg
        x = x.sort_values("tod").drop_duplicates(["cfg", "conf", "symbol", "date"])     # first per symbol-day (per class)
        out.append(x)
X = pd.concat(out, ignore_index=True)
X["r0"] = np.where(X.side == 1, X.r_long_t1s1, X.r_short_t1s1); X = X[X.r0.notna()]
Ru = 0.25 * X.atr_d; e = X.close
X["r"] = X.r0 - (2 * (0.01 + e * 1e-4) * tod_cost_mult(X.tod.to_numpy()) - 0.02 + np.where(X.r0 < 0, 0.02, 0.0)) / Ru
X["half"] = np.where(X.date <= "2026-02-28", "TRAIN", "VALID"); X["dtype"] = X.date.map(dtype); X["month"] = X.date.str[:7]
def dt(x):
    g = x.groupby("date").r.mean(); return g.mean() / (g.std(ddof=1) / np.sqrt(len(g))) if len(g) > 2 else np.nan
res = {}
for cfg in ("A", "B"):
    c = X[(X.cfg == cfg) & X.conf]; u = X[(X.cfg == cfg) & ~X.conf]
    pr(f"\n=== GATE2-{cfg}: confirmed n {len(c):,} on {c.date.nunique()} days; avg R {c.r.mean():+.3f} (win {(c.r > 0).mean():.1%}), day-t {dt(c):.2f} | unconfirmed n {len(u):,} avg {u.r.mean():+.3f} | confirmed - unconfirmed {c.r.mean() - u.r.mean():+.3f}")
    for h in ("TRAIN", "VALID"):
        y = c[c.half == h]; pr(f"  {h}: n {len(y):,} avg {y.r.mean():+.3f} t {dt(y):.2f}; long {len(y[y.side == 1]):,} {y[y.side == 1].r.mean():+.3f}, short {len(y[y.side == -1]):,} {y[y.side == -1].r.mean():+.3f}")
    g = c.groupby(["dtype", "side"]).agg(n=("r", "size"), days=("date", "nunique"), avgR=("r", "mean")).round(3)
    pr("  QDAY split (confirmed; side +1 long on held-up, -1 short on held-down):\n" + g.to_string())
    g2 = c.groupby("s10").agg(n=("r", "size"), avgR=("r", "mean")).round(3); pr("  by SPY vs open at 10:00: " + g2.to_dict("index").__repr__())
    ds = c.groupby("date").r.sum().sort_values(); wo = c[c.date != ds.index[-1]].r.mean(); mo = c.groupby("month").r.mean()
    share = ds.iloc[-1] / ds.sum() if ds.sum() > 0 else float("nan")
    pr(f"  w/o best day {wo:+.3f} (best {ds.index[-1]} {ds.iloc[-1]:+.1f}R, share {share:.0%}); months positive {(mo > 0).mean():.0%} of {len(mo)}")
    gd = c.groupby("dtype").r.mean()
    ok = (c[c.half == "TRAIN"].r.mean() > 0 and c[c.half == "VALID"].r.mean() > 0 and dt(c) >= 1.50 and gd.get("up", -1) > 0 and gd.get("down", -1) > 0
          and (mo > 0).mean() >= 0.54 and wo > 0 and c.r.mean() > u.r.mean())
    pr(f"  VERDICT GATE2-{cfg} (BAR90 1.50, N = 4 tonight): {'PASS -> Live Lab candidate' if ok else 'FAIL'}")
pr("\nLocked block never read (asserted). Configurations: 2 (GATE2-A, GATE2-B). Educational only - not financial advice.")
(HERE / "gate2_out.txt").write_text("\n".join(P) + "\n")
