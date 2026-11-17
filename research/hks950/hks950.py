"""HKS950 scorer (frozen PLAN.md). Educational only - not financial advice.
  python3 -I hks950.py --selftest              synthetic check: planted same-slot effect is found, null is not
  python3 -I hks950.py <m30.csv.gz> <outdir>    the ONE real look (run after 16:00 ET)"""
import sys, numpy as np, pandas as pd
HALF = ['2025-07-03', '2025-11-28', '2025-12-24']
BAR, COST_RT = 1.35, 6.0  # bps round trip per name per leg -> L-S net = gross - 2*COST_RT

def prep(d):
    d = d.copy()
    d['t'] = pd.to_datetime(d.t, utc=True)
    d['t'] = d.t.dt.tz_convert('America/New_York')
    d['day'] = d.t.dt.date.astype(str); d['hm'] = d.t.dt.strftime('%H%M')
    d = d[~d.day.isin(HALF)]
    d = d[(d.hm >= '0930') & (d.hm <= '1530')].sort_values(['symbol', 't'])
    d['r'] = d.groupby(['symbol', 'day']).c.pct_change()
    return d[d.hm >= '1000'].dropna(subset=['r'])[['symbol', 'day', 'hm', 'r']]

def signal(x, L):
    w = x.pivot_table(index='day', columns=['hm', 'symbol'], values='r').sort_index()
    m = w.shift(1).rolling(L, min_periods=int(0.8 * L)).mean()   # prior L sessions only (shift 1 = no look-ahead)
    s = m.stack(level=[0, 1], future_stack=True).rename('sig').reset_index()
    return x.merge(s.dropna(), on=['day', 'hm', 'symbol'])

def spreads(z, sigcol='sig'):
    g = z.groupby(['day', 'hm'])
    n = g.r.transform('size'); k = n // 10
    rk = g[sigcol].rank(method='first')
    top = rk > n - k; bot = rk <= k
    mu = g.r.transform('mean')
    t = z.r.where(top).groupby([z.day, z.hm]).mean(); b = z.r.where(bot).groupby([z.day, z.hm]).mean()
    m = mu.groupby([z.day, z.hm]).first(); kk = k.groupby([z.day, z.hm]).first()
    o = pd.DataFrame({'ls': t - b, 'lx': t - m, 'sx': m - b})[kk >= 3]
    o.index.names = ['day', 'hm']
    return o.dropna() * 1e4

def tstat(s):
    return s.mean() / (s.std() / np.sqrt(len(s))) if len(s) > 2 else np.nan

def report(z, label, spy=None, nperm=200, seed=7):
    sp = spreads(z); day = sp.groupby(level=0).mean(); out = []
    for nm, msk in (('TRAIN', day.index < '2026-01-01'), ('VALID', day.index >= '2026-01-01'), ('ALL', day.index == day.index)):
        dd = day[msk]
        if len(dd) < 3: continue
        best = dd.ls.idxmax(); share = dd.ls.max() / dd.ls.sum() if dd.ls.sum() > 0 else np.nan
        out.append(f"{label} {nm}: days {len(dd)}  L-S gross {dd.ls.mean():+.2f} bps (t {tstat(dd.ls):+.2f})  long-leg ex {dd.lx.mean():+.2f} (t {tstat(dd.lx):+.2f})"
                   f"  short-leg ex {dd.sx.mean():+.2f} (t {tstat(dd.sx):+.2f})  net {dd.ls.mean() - 2 * COST_RT:+.2f}  w/o best day {dd.ls.drop(best).mean():+.2f}  best-day share {share:.3f}")
    out.append(f"{label} by slot (ALL, bps): " + ' '.join(f"{h}:{v:+.2f}" for h, v in sp.ls.groupby(level=1).mean().items()))
    if spy is not None:
        up = day.index.isin(spy[spy > 0].index)
        out.append(f"{label} SPY-up days {up.sum()}: {day.ls[up].mean():+.2f} bps (t {tstat(day.ls[up]):+.2f}); down {(~up).sum()}: {day.ls[~up].mean():+.2f} (t {tstat(day.ls[~up]):+.2f})")
    rng = np.random.default_rng(seed); va = day.index >= '2026-01-01'; real = day.ls[va].mean(); null = []
    for _ in range(nperm):
        zz = z.copy(); zz['sig'] = rng.random(len(zz))  # iid random ranks within each (day, slot) = shuffle of the signal
        null.append(spreads(zz).ls.groupby(level=0).mean()[va].mean())
    null = np.array(null)
    out.append(f"{label} VALID shuffle control ({nperm}): null mean {null.mean():+.3f} sd {null.std():.3f}; real {real:+.2f}; p(null>=real) {(null >= real).mean():.3f}")
    v = day[va]; tr = day[~va]
    ok = tstat(v.ls) >= BAR and np.sign(v.ls.mean()) == np.sign(tr.ls.mean())
    verdict = ('LEAD (net > 0)' if v.ls.mean() - 2 * COST_RT > 0 else 'TILT only (gross passes, net <= 0)') if ok else 'CLOSED'
    se = v.ls.std() / np.sqrt(len(v))
    out.append(f"{label} VERDICT: {verdict}; VALID MDE at bar {(BAR + 0.84) * se:.2f} bps (nothing above that if closed; smaller unknown); break-even cost per leg {v.ls.mean() / 2:.2f} bps RT")
    return out, day

def prep_spy(src):
    d = pd.read_csv(src); d = d[d.symbol == 'SPY'].copy()
    if d.empty: print('SPY not in file: no up/down split'); return None
    d['t'] = pd.to_datetime(d.t, utc=True).dt.tz_convert('America/New_York')
    d['day'] = d.t.dt.date.astype(str); d['hm'] = d.t.dt.strftime('%H%M')
    w = d.pivot_table(index='day', columns='hm', values='c')
    return (w['1530'] / w['0930'] - 1).dropna()   # SPY from the 10:00 anchor (09:30-bar close) to the close

def synth(effect, ndays=120, nsym=60, seed=0):
    rng = np.random.default_rng(seed); days = pd.bdate_range('2025-09-01', periods=ndays // 2).append(pd.bdate_range('2026-01-05', periods=ndays // 2))
    rows = []; slots = pd.date_range('09:30', '15:30', freq='30min').time; alpha = rng.normal(0, 1, (nsym, len(slots)))
    for d in days:
        for s in range(nsym):
            p = 100.0
            for k, tt in enumerate(slots):
                p *= 1 + effect * 1e-4 * alpha[s, k] + rng.normal(0, 30e-4)
                rows.append((f"S{s}", pd.Timestamp.combine(d, tt).tz_localize('America/New_York').tz_convert('UTC'), p))
    return pd.DataFrame(rows, columns=['symbol', 't', 'c'])

if __name__ == '__main__':
    if sys.argv[1] == '--selftest':
        for eff, want in ((8.0, True), (0.0, False)):
            z = signal(prep(synth(eff)), 20); o, day = report(z, f'synth{eff:g}', nperm=20)
            v = day[day.index >= '2026-01-01'].ls; t = tstat(v); print(o[1]); print(o[-1])
            assert (t >= BAR) == want, (eff, t)
        x = prep(synth(0.0, ndays=40)); s = signal(x, 5)
        assert s.groupby('symbol').day.min().min() > x.day.min(), 'look-ahead: first day must have no signal'
        print('selftest OK'); sys.exit()
    src, outdir = sys.argv[1], sys.argv[2]
    x = prep(pd.read_csv(src)); lines = [f"HKS950 one look; {x.symbol.nunique()} names, {x.day.nunique()} days {x.day.min()}..{x.day.max()}; configs 2; family N 3; BAR90 {BAR}"]
    d0 = prep_spy(src)
    for L in (20, 40):
        o, day = report(signal(x, L), f'L{L}', spy=d0); lines += o
        day.to_csv(f"{outdir}/hks950_L{L}_days.csv")
    lines.append('Educational only - not financial advice.')
    open(f"{outdir}/hks950_out.txt", 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
