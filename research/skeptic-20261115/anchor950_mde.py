"""ANCHOR950 - the index null re-anchored per the owner's 2026-11-14 rule (descriptive, 0 configs). Reference = the 09:50 state and
the 09:30-09:50 range, never the 09:30 open alone; score readings by the return AFTER the decision time.
Patterns from the first 20 min (bars 09:30-09:45, i.e. 09:30-09:50), per instrument (SPY, QQQ, SPXL, TQQQ; LEAD20 cache):
  pos = (P09:50 - L20) / (H20 - L20) where P09:50 = open of the 09:50 bar (position in the early range at the decision);
  dip_turn = 09:30-09:50 low <= open - 0.25 x range AND pos >= 0.6 (dipped, then recovered into the top of the range);
  pop_fade = mirror (high >= open + 0.25 x range AND pos <= 0.4).
Outcomes after the decision: 09:50 open -> 15:55 (close of 15:50 bar); and 09:50 -> 10:50; also break of the early range:
first close above H20 / below L20 after 09:50 and the return from that break to 15:55. Day-clustered t (one row per day).
    python -I anchor950.py <lead20 m5.csv.gz>        Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
m = pd.read_csv(sys.argv[1]); m["t"] = pd.to_datetime(m.t, utc=True).dt.tz_convert("America/New_York")
m["date"] = m.t.dt.strftime("%Y-%m-%d"); m["hm"] = m.t.dt.hour * 100 + m.t.dt.minute
m = m[(m.hm >= 930) & (m.hm <= 1550)]
assert not ((m.date >= "2024-11-01") & (m.date <= "2025-02-28")).any()
tt = lambda x: x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan
for inst in ("SPY", "QQQ", "SPXL", "TQQQ"):
    rows = []
    for d, g in m[m.symbol == inst].groupby("date"):
        g = g.set_index("hm").sort_index()
        if not {930, 945, 950, 1050, 1550}.issubset(g.index): continue
        e20 = g.loc[930:945]; o = g.loc[930, "o"]; H, L = e20.h.max(), e20.l.min()
        if H <= L: continue
        p = g.loc[950, "o"]; pos = (p - L) / (H - L); rng = H - L
        aft = g.loc[950:1550]
        brk_up = aft[aft.c > H]; brk_dn = aft[aft.c < L]
        rows.append(dict(date=d, pos=pos, rng_bps=rng / o * 1e4,
                         dip_turn=(L <= o - 0.25 * rng) and pos >= 0.6, pop_fade=(H >= o + 0.25 * rng) and pos <= 0.4,
                         r_close=(g.loc[1550, "c"] / p - 1) * 1e4, r_1h=(g.loc[1050, "o"] / p - 1) * 1e4,
                         up_brk=(g.loc[1550, "c"] / brk_up.c.iloc[0] - 1) * 1e4 if len(brk_up) else np.nan,
                         dn_brk=(g.loc[1550, "c"] / brk_dn.c.iloc[0] - 1) * 1e4 if len(brk_dn) else np.nan))
    R = pd.DataFrame(rows)
    se = lambda x: x.std(ddof=1) / np.sqrt(len(x))
    cells = [("all days", R)] + [(nm, R[sel]) for nm, sel in (("dip-then-turn", R.dip_turn), ("pop-then-fade", R.pop_fade), ("pos>=0.8", R.pos >= 0.8), ("pos<=0.2", R.pos <= 0.2))]
    print(f"{inst}: " + " | ".join(f"{nm} n{len(x)} se {se(x.r_close):.1f} MDE80 {2.8 * se(x.r_close):.0f}bps" for nm, x in cells))
    u = R.up_brk.dropna(); print(f"   break-up n{len(u)} MDE80 {2.8 * se(u):.0f}bps; sd 09:50->close {R.r_close.std():.0f}bps")
