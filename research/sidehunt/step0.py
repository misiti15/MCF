"""SIDEHUNT #2 step 0 (Lead lead-20261118-2100-2; Observer -1955-1; Skeptic -0150-1 / -0151-2). OUTCOME-FREE: only bars 09:30-09:49 ET.
Feature (day-reset, built fresh): F = sum(sign(c - o) x v) / sum(v) over today's 5-min bars 09:30, 09:35, 09:40, 09:45.
Competitor: C = close of the 09:45 bar / open of the 09:30 bar - 1 (today's 09:30-09:50 side).
In-play PROXY: (09:30-09:50 high - low) / prior-day ATR14 (daily bars, shifted one day), top quintile per day. This is NOT precursors.py's
vol_exp (5-min ATR / daily ATR, its rows are not in this container); stated with the result.
Prints: sign agreement, Spearman (pooled and median per day), discordant N (F and C disagree in sign) and its MDE at BAR90 2.74 under a
STATED per-trade SD of 1.0R and ICC 0.22 (ICCSET 11-18): MDE = (2.74 + 0.84) x 1.0 / sqrt(n_eff), n_eff = N / (1 + (m - 1) x 0.22).
    python3 -I step0.py <open_dir> <daily.csv.gz> <out.txt>     |  --selftest        Educational only - not financial advice."""
import sys, glob, numpy as np, pandas as pd
BAR, SD, ICC = 2.74, 1.0, 0.22
def feats(b):
    b = b.copy(); b['t'] = pd.to_datetime(b.t, utc=True).dt.tz_convert('America/New_York')
    b['day'] = b.t.dt.date.astype(str); b['hm'] = b.t.dt.strftime('%H%M'); b = b[b.hm.isin(['0930', '0935', '0940', '0945'])]
    assert b.hm.max() <= '0945', 'outcome guard: no bar after 09:45 start may be read'
    b['sv'] = np.sign(b.c - b.o) * b.v
    g = b.sort_values('hm').groupby(['symbol', 'day'])
    o = pd.DataFrame({'F': g.sv.sum() / g.v.sum(), 'C': g.c.last() / g.o.first() - 1, 'rng': g.h.max() - g.l.min(), 'n': g.size(), 'px': g.o.first()})
    return o[o.n == 4].reset_index()
def atr(d):
    d = d.sort_values(['symbol', 't']).copy(); d['day'] = pd.to_datetime(d.t, utc=True).dt.tz_convert('America/New_York').dt.date.astype(str)
    pc = d.groupby('symbol').c.shift(1); tr = np.maximum(d.h - d.l, np.maximum((d.h - pc).abs(), (d.l - pc).abs()))
    d['atr'] = tr.groupby(d.symbol).transform(lambda x: x.rolling(14, min_periods=10).mean().shift(1))   # prior days only
    return d[['symbol', 'day', 'atr']]
def report(o):
    nd = o.day.nunique(); L = [f"rows (symbol-days with 4 bars): {len(o)}, days {nd}, in-play proxy rows (top quintile of range/ATR): {len(o[o.inplay])}"]
    for lab, x in (('ALL names', o), ('IN-PLAY proxy', o[o.inplay])):
        z = x[(x.F != 0) & (x.C != 0)]; agree = (np.sign(z.F) == np.sign(z.C)).mean()
        sp = z[['F', 'C']].rank().corr().iloc[0, 1]; spd = z.groupby('day').apply(lambda g: g[['F', 'C']].rank().corr().iloc[0, 1] if len(g) > 5 else np.nan).median()
        dis = z[np.sign(z.F) != np.sign(z.C)]; m = len(dis) / nd; neff = len(dis) / (1 + (m - 1) * ICC) if m > 0 else 0
        mde = (BAR + 0.84) * SD / np.sqrt(neff) if neff > 0 else np.inf
        L.append(f"{lab}: sign agreement {agree:.1%}; Spearman pooled {sp:+.3f}, median per day {spd:+.3f}; discordant N {len(dis)} ({m:.1f}/day); "
                 f"n_eff {neff:.0f}; MDE at BAR90 {BAR} = {mde:.3f}R per trade (SD {SD}R, ICC {ICC} stated, not measured)")
    return L
def selftest():
    rng = np.random.default_rng(0); rows = []
    for d in pd.bdate_range('2026-01-05', periods=30):
        for s in range(50):
            p = 100.0
            for k, hm in enumerate(['09:30', '09:35', '09:40', '09:45']):
                o_ = p; p *= 1 + rng.normal(0, 0.004); rows.append((f"S{s}", pd.Timestamp(f"{d.date()} {hm}", tz='America/New_York').tz_convert('UTC').isoformat(), o_, max(o_, p) + .05, min(o_, p) - .05, p, rng.integers(1000, 5000)))
    b = pd.DataFrame(rows, columns=['symbol', 't', 'o', 'h', 'l', 'c', 'v']); o = feats(b); o['inplay'] = True
    L = report(o); print('\n'.join(L))
    ag = float(L[1].split('sign agreement ')[1].split('%')[0]); assert ag > 70, ag      # F is built from bar signs: high agreement expected
    late = b.copy(); late.loc[0, 't'] = pd.Timestamp('2026-01-05 09:50', tz='America/New_York').tz_convert('UTC').isoformat()
    assert len(feats(late)) == len(o) - 1                                                   # a 09:50 bar is dropped, not read
    print('selftest OK')
if __name__ == '__main__':
    if sys.argv[1] == '--selftest': selftest(); sys.exit()
    o = feats(pd.concat([pd.read_csv(f) for f in sorted(glob.glob(sys.argv[1] + '/*.csv.gz'))]))
    o = o.merge(atr(pd.read_csv(sys.argv[2])), on=['symbol', 'day'], how='left').dropna(subset=['atr'])
    o['x'] = o.rng / o.atr; o['inplay'] = o.groupby('day').x.rank(pct=True) > 0.8
    L = report(o) + ["Outcome-free: no price after 09:50 was read. Educational only - not financial advice."]
    open(sys.argv[3], 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
