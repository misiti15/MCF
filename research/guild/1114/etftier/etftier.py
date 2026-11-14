"""ETFTIER scorer (PLAN.md frozen 2026-11-14 03:20 ET). One look.
    python -I etftier.py --selftest | <m5.csv.gz>        Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
SPLIT = "2025-09-30"; BAR = 3.57
def trade(bars, e, stop, tiered):
    """bars: list of (h, l, c) after entry (10:30..15:50 bars, entry at the 10:30 open). Returns gross R, net R, events."""
    R = max(e - stop, 0.005 * e); stop = e - R
    tr = [(1/3, e + 0.5 * R), (1/3, e + 1.0 * R)] if tiered else []
    open_w, exits, ev = 1.0, [], set()
    ce = 0.01 + e * (1.4e-4 + 4.4e-4)
    for h, l, c in bars:
        if l <= stop:
            exits.append((open_w, stop, 0.01 + stop * 1e-4 + 0.02)); open_w = 0; ev.add("stop"); break
        for w, px in list(tr):
            if h >= px:
                exits.append((w, px, 0.01 + px * 1e-4)); open_w -= w; tr.remove((w, px)); ev.add(f"t{px > e + 0.75 * R and 2 or 1}")
    if open_w > 1e-9:
        c = bars[-1][2]; exits.append((open_w, c, 0.01 + c * 1e-4))
    g = sum(w * (px - e) for w, px, _ in exits) / R
    n = sum(w * (px - e - ce - k) for w, px, k in exits) / R
    return g, n, ev
def selftest():
    b = [(101, 99.6, 100.5), (102, 100, 101.5)]                 # e 100, stop 99 -> R 1; t1 100.5 bar1, t2 101 bar2
    g, n, ev = trade(b, 100.0, 99.0, True); assert abs(g - (0.5/3 + 1/3 + 1.5/3)) < 1e-9, g
    g, n, ev = trade([(100.2, 98.5, 99)], 100.0, 99.0, True); assert abs(g + 1) < 1e-9 and "stop" in ev
    g, n, ev = trade([(100.1, 99.9, 100.05)], 100.0, 100.2, False); assert abs(g - 0.05 / 0.5) < 1e-9   # floored R 0.5
    print("selftest ok")
def main(f):
    m = pd.read_csv(f); m["t"] = pd.to_datetime(m.t, utc=True).dt.tz_convert("America/New_York")
    m["date"] = m.t.dt.strftime("%Y-%m-%d"); m["hm"] = m.t.dt.hour * 100 + m.t.dt.minute
    assert not ((m.date >= "2024-11-01") & (m.date <= "2025-02-28")).any()
    m = m[(m.hm >= 930) & (m.hm <= 1550)]
    G = {k: g.sort_values("hm") for k, g in m.groupby(["symbol", "date"])}
    rows = []
    for d in sorted(set(m.date)):
        spy = G.get(("SPY", d))
        if spy is None: continue
        s = spy.set_index("hm")
        if not {930, 1025}.issubset(s.index) or not (s.loc[1025, "c"] > s.loc[930, "o"]): continue
        for inst in ("SPXL", "TQQQ"):
            g = G.get((inst, d))
            if g is None: continue
            mor, aft = g[g.hm <= 1025], g[g.hm >= 1030]
            if len(mor) < 6 or len(aft) < 60 or aft.hm.iloc[0] != 1030 or aft.hm.iloc[-1] != 1550: continue
            e, stop = aft.o.iloc[0], mor.l.min()
            bars = list(zip(aft.h, aft.l, aft.c))
            for tier in (False, True):
                gR, nR, ev = trade(bars, e, stop, tier)
                rows.append(dict(date=d, inst=inst, tier=tier, g=gR, n=nR, stop="stop" in ev, t1="t1" in ev, t2="t2" in ev))
    D = pd.DataFrame(rows)
    tt = lambda x: x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan
    print(f"up-reading days traded: SPXL {D[(D.inst=='SPXL')&~D.tier].shape[0]}, TQQQ {D[(D.inst=='TQQQ')&~D.tier].shape[0]}")
    for inst in ("SPXL", "TQQQ"):
        x = D[D.inst == inst]; P, T = x[~x.tier].set_index("date"), x[x.tier].set_index("date")
        print(f"\n{inst}: stop hit {P.stop.mean():.0%}, +0.5R reached {T.t1.mean():.0%}, +1R {T.t2.mean():.0%}")
        for nm, y in (("PLAIN", P), ("TIERED", T)):
            bd = y.n.idxmax()
            print(f"  {nm:6s} gross {y.g.mean():+.3f}R  net {y.n.mean():+.3f}R (t {tt(y.n):+.2f})  median {y.n.median():+.3f}  "
                  f"w/o best day {y.drop(bd).n.mean():+.3f} | TRAIN {y[y.index <= SPLIT].n.mean():+.3f}  VALID {y[y.index > SPLIT].n.mean():+.3f}")
        dlt = (T.n - P.n); print(f"  TIERED - PLAIN (paired): {dlt.mean():+.3f}R (t {tt(dlt):+.2f}); share of days tiered better {(dlt > 0).mean():.0%}")
    T = D[(D.inst == "SPXL") & D.tier].set_index("date")
    ok = (T.n.mean() > 0 and tt(T.n) >= BAR and T[T.index <= SPLIT].n.mean() > 0 and T[T.index > SPLIT].n.mean() > 0
          and T.drop(T.n.idxmax()).n.mean() > 0)
    print(f"\nPASS {ok}{'' if ok else ' -> ETFTIER closed'} (bar 3.57, family 2,608). Educational only - not financial advice.")
if __name__ == "__main__":
    selftest() if sys.argv[1] == "--selftest" else main(sys.argv[1])
