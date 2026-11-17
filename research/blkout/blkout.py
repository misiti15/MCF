"""BLKOUT scorer (frozen with PLAN.md). Descriptive, 0 configs. Educational only - not financial advice.
  python research/blkout/blkout.py --selftest
  python research/blkout/blkout.py --run        (guild root; needs research/momside/data/trades_full.parquet + earnings_yf.parquet)"""
import sys, numpy as np, pandas as pd
from pathlib import Path
HERE = Path(__file__).resolve().parent; G = HERE.parents[1]; ROOT = Path("/home/user/MCF")
EARN = ROOT / "research/bdi/earnings/data/earnings_yf.parquet"
LB0, LB1 = "2024-11-01", "2025-02-28"; HALF = {"2025-07-03", "2025-11-28", "2025-12-24"}
TR_END, VA_END = "2025-09-30", "2026-10-07"
def offsets(trades, earn, sessions):
    """k = sessions from the nearest reaction session R0 to the trade date; NaN when the name has no report."""
    pos = {d: i for i, d in enumerate(sessions)}; sess = np.array(sessions)
    e = earn.copy(); e["date"] = pd.to_datetime(e["date"]).dt.strftime("%Y-%m-%d")
    e["i"] = np.searchsorted(sess, e["date"].to_numpy())                       # report date -> first session on/after
    e["i"] = e["i"] + np.where(e["session"].astype(str).str.lower() == "amc", 1, 0)
    e["trusted"] = e["session"].astype(str).str.lower().isin(["bmo", "amc"])
    e = e[(e.i >= 0) & (e.i < len(sess))]
    out_k = np.full(len(trades), np.nan); out_t = np.zeros(len(trades), bool); out_amc = np.zeros(len(trades), bool)
    by = {s: g.sort_values("i") for s, g in e.groupby("symbol")}
    ti = trades.date.map(pos).to_numpy()
    for s, idx in trades.groupby("symbol").indices.items():
        g = by.get(s)
        if g is None or not len(g): continue
        r0 = g.i.to_numpy(); j = np.searchsorted(r0, ti[idx]); j0 = np.clip(j - 1, 0, len(r0) - 1); j1 = np.clip(j, 0, len(r0) - 1)
        d0, d1 = ti[idx] - r0[j0], ti[idx] - r0[j1]; use1 = np.abs(d1) < np.abs(d0)
        jj = np.where(use1, j1, j0); out_k[idx] = np.where(use1, d1, d0)
        out_t[idx] = g.trusted.to_numpy()[jj]; out_amc[idx] = (g.session.astype(str).str.lower() == "amc").to_numpy()[jj]
    return out_k, out_t, out_amc
def primary(b, col):
    """within setup x ISO-week: mean(inside) - mean(outside), weighted by inside count; day-clustered SE on inside dates."""
    b = b.assign(wk=pd.to_datetime(b.date).dt.strftime("%G-%V"))
    rows = []
    for (s, w), g in b.groupby(["setup", "wk"]):
        ins, out = g[g.grp == "in"], g[g.grp == "out"]
        if len(ins) and len(out):
            mo = out[col].mean()
            for d, gi in ins.groupby("date"): rows.append((d, w, (gi[col] - mo).sum(), len(gi)))
    if not rows: return dict(diff=np.nan, t=np.nan, cells=0)
    x = pd.DataFrame(rows, columns=["date", "wk", "s", "n"]); day = x.groupby("date")[["s", "n"]].sum()
    m = day.s.sum() / day.n.sum(); res = day.s - m * day.n; G_ = len(day)
    se = np.sqrt(G_ / (G_ - 1) * (res ** 2).sum()) / day.n.sum() if G_ > 1 else np.nan
    wk = x.groupby("wk").s.sum(); best = wk.max() / wk.sum() if wk.sum() > 0 else np.nan
    return dict(diff=m, t=m / se if se else np.nan, MDE80=2.8 * se, n_in=int(day.n.sum()), days=G_, best_week_share=best)
def selftest():
    rng = np.random.default_rng(5); sess = [str(d.date()) for d in pd.bdate_range("2025-03-03", "2026-10-30")]
    syms = [f"S{i}" for i in range(60)]; earn = []
    for s in syms:
        off = int(rng.integers(0, 60))
        for q in range(7): earn.append(dict(symbol=s, date=sess[min(len(sess) - 1, off + q * 60)], session=rng.choice(["bmo", "amc", "dmh"])))
    earn = pd.DataFrame(earn); tr = []
    for _ in range(60000):
        s = rng.choice(syms); d = rng.choice(sess); tr.append(dict(setup=f"U{rng.integers(0, 20)}", side=1, symbol=s, date=d))
    t = pd.DataFrame(tr); k, tru, amc = offsets(t, earn, sess); t["k"] = k
    t["grp"] = np.where(np.abs(k) <= 4, "in", np.where(np.abs(k) >= 10, "out", "buf"))
    for planted in (0.0, -0.20):
        t["gross"] = rng.normal(0, 1, len(t)) + np.where(t.grp == "in", planted, 0)
        p = primary(t[t.grp != "buf"], "gross"); print(f"planted {planted:+.2f}: diff {p['diff']:+.3f} t {p['t']:+.2f} MDE80 {p['MDE80']:.3f} n_in {p['n_in']}")
        if planted: assert p["t"] < -3 and abs(p["diff"] - planted) < 0.08
        else: assert abs(p["t"]) < 3
    print("selftest ok")
def run():
    sys.path.insert(0, str(ROOT)); assert EARN.exists(), f"missing {EARN}: blackout would silently be empty"
    B = pd.read_parquet(G / "research/momside/data/trades_full.parquet", columns=["setup", "side", "symbol", "date", "r", "gross", "spy_move"])
    assert not ((B.date >= LB0) & (B.date <= LB1)).any(), "locked block in trades"
    nh = int(B.date.isin(HALF).sum()); B = B[~B.date.isin(HALF)].dropna(subset=["spy_move"]).reset_index(drop=True)
    E = pd.read_parquet(EARN); E = E[E.symbol.isin(B.symbol.unique())]
    ed = pd.to_datetime(E.date).dt.strftime("%Y-%m-%d"); E = E[(ed >= B.date.min()) & (ed <= B.date.max()) & ~((ed >= LB0) & (ed <= LB1))]
    nrep = E.groupby("symbol").size(); good = set(nrep[nrep >= 6].index)
    print(f"trades {len(B)}; half-day dropped {nh}; names traded {B.symbol.nunique()}; with >= 6 reports {len(good)} "
          f"({len(good) / B.symbol.nunique():.0%}); trades on those names {B.symbol.isin(good).mean():.0%} (others excluded)")
    B = B[B.symbol.isin(good)].reset_index(drop=True); sessions = sorted(B.date.unique())
    k, tru, amc = offsets(B, E, sessions); B["k"], B["trusted"], B["amc"] = k, tru, amc
    B["grp"] = np.where(np.abs(B.k) <= 4, "in", np.where(np.abs(B.k) >= 10, "out", "buf"))
    B["per"] = np.where(B.date <= TR_END, "TRAIN", np.where(B.date <= VA_END, "VALID", "FWD"))
    beta = {s: (np.polyfit(g.spy_move, g.gross, 1)[0] if len(g) >= 30 else float(g.side.iloc[0])) for s, g in B[B.per == "TRAIN"].groupby("setup")}
    B["exm"] = B.gross - B.setup.map(beta).fillna(B.side.astype(float)) * B.spy_move
    print("groups:", B.grp.value_counts().to_dict(), "| inside with trusted BMO/AMC time:", f"{B[B.grp == 'in'].trusted.mean():.0%}")
    print("\nPRIMARY (within setup x ISO-week; day-clustered; gross first):")
    for per in ("TRAIN", "VALID", "FWD"):
        b = B[(B.per == per) & (B.grp != "buf")]
        for col in ("gross", "exm", "r"):
            p = primary(b, col); print(f"  {per:5s} {col:5s}: inside-outside {p['diff']:+.4f}R t {p['t']:+.2f} MDE80 {p.get('MDE80', np.nan):.4f} n_in {p.get('n_in', 0)} days {p.get('days', 0)} best-week {p.get('best_week_share', np.nan):.0%}")
    print("\nSECONDARY (descriptive; cells counted):")
    v = B[(B.per == "VALID") & (B.grp != "buf")]; ps = {}
    for s, g in v.groupby("setup"):
        if (g.grp == "in").sum() >= 30: ps[s] = primary(g, "exm")["diff"]
    ps = pd.Series(ps).dropna(); print(f"  per setup (>= 30 inside, VALID, ex-market): {len(ps)} setups; inside better {int((ps > 0).sum())} / worse {int((ps <= 0).sum())}")
    for side, g in v.groupby("side"): p = primary(g, "exm"); print(f"  side {side:+d}: {p['diff']:+.4f} t {p['t']:+.2f}")
    tv = v[(v.grp == "out") | ((v.grp == "in") & v.trusted)]; cells = 0
    for lab, amc_flag in (("BMO", False), ("AMC", True)):
        for kk in range(-4, 5):
            g = tv[(tv.grp == "out") | ((tv.k == kk) & (tv.amc == amc_flag))]; p = primary(g, "exm"); cells += 1
            print(f"  {lab} k={kk:+d}: {p['diff']:+.4f} t {p['t']:+.2f} n_in {p.get('n_in', 0)}")
    print(f"  cells printed: {cells} offset x time + side 2 + per-setup 1. Net r is OPTIMISTIC inside (x3 costs only at |gap| >= 20%): "
          "no 'blackout costs R' claim before the Phase 2 spread re-charge. Educational only - not financial advice.")
if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest()
    elif "--run" in sys.argv: run()
    else: print(__doc__)
