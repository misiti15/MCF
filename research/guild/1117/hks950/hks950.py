"""HKS950 scorer (frozen PLAN.md). Educational only - not financial advice.
  python3 -I hks950.py --selftest              synthetic check: planted same-slot effect is found, null is not
  python3 -I hks950.py <m30.csv.gz> <outdir>    the ONE real look (run after 16:00 ET)"""
import sys, numpy as np, pandas as pd
HALF = ['2025-07-03', '2025-11-28', '2025-12-24']
BAR, FULLBAR, COST_RT = 2.46, 2.73, 6.0  # family N 42 (cross-sectional return family; Lead 11-17)
MAIN_SLOTS = ['1000','1030','1100','1130','1200','1230','1300','1330','1400','1430','1500']  # 15:30 reported apart (Live flat by 15:55)  # bps round trip per name per leg -> L-S net = gross - 2*COST_RT

def prep(d):
    d = d.copy()
    d['t'] = pd.to_datetime(d.t, utc=True)
    d['t'] = d.t.dt.tz_convert('America/New_York')
    d['day'] = d.t.dt.date.astype(str); d['hm'] = d.t.dt.strftime('%H%M')
    d = d[~d.day.isin(HALF)]
    pre = (d.hm < '0930').sum(); post = (d.hm > '1530').sum()
    d = d[(d.hm >= '0930') & (d.hm <= '1530')].sort_values(['symbol', 't'])
    fl = d.groupby('day').hm.agg(['min', 'max'])
    assert (fl['min'] == '0930').all() and (fl['max'] == '1530').all(), 'RTH assert failed: ' + str(fl[(fl['min'] != '0930') | (fl['max'] != '1530')].head())
    print(f'RTH check: dropped {pre} pre-09:30 and {post} post-15:30 bars; every day runs 09:30..15:30 (bar starts)')
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

def verdict_block(label, sp, day, slots, rng, nperm):
    out = []; va = day.index >= '2026-01-01'
    for nm, msk in (('TRAIN', ~va), ('VALID', va), ('ALL', va | ~va)):
        dd = day[msk]
        if len(dd) < 3: continue
        best = dd.ls.idxmax(); share = dd.ls.max() / dd.ls.sum() if dd.ls.sum() > 0 else np.nan
        out.append(f"{label} {nm}: days {len(dd)}  L-S gross {dd.ls.mean():+.2f} bps (t {tstat(dd.ls):+.2f})  LONG leg ex {dd.lx.mean():+.2f} (t {tstat(dd.lx):+.2f})"
                   f"  short leg ex {dd.sx.mean():+.2f} (t {tstat(dd.sx):+.2f})  L-S net {dd.ls.mean() - 2 * COST_RT:+.2f}  LONG net {dd.lx.mean() - COST_RT:+.2f}"
                   f"  w/o best day {dd.ls.drop(best).mean():+.2f}  best-day share {share:.3f}")
    vs = sp[sp.index.get_level_values(0) >= '2026-01-01'].groupby(level=1).ls.mean()
    out.append(f"{label} VALID by slot, L-S bps (break-even cost per leg RT = half): " + ' '.join(f"{h}:{v:+.2f}/{v / 2:.2f}" for h, v in vs.items()))
    v, tr = day[va], day[~va]; sgn = np.sign(v.ls.mean()); nslot = int((np.sign(vs) == sgn).sum())
    return out, v, tr, nslot, len(vs)

def report(z, label, spy=None, nperm=200, seed=7):
    rng = np.random.default_rng(seed)
    spall = spreads(z); out = []
    sp = spall[spall.index.get_level_values(1).isin(MAIN_SLOTS)]
    day = sp.groupby(level=0).mean()
    o, v, tr, nslot, ns = verdict_block(label, sp, day, MAIN_SLOTS, rng, nperm); out += o
    if spy is not None:
        up = day.index.isin(spy[spy > 0].index)
        out.append(f"{label} SPY-up days {up.sum()}: {day.ls[up].mean():+.2f} bps (t {tstat(day.ls[up]):+.2f}); down {(~up).sum()}: {day.ls[~up].mean():+.2f} (t {tstat(day.ls[~up]):+.2f})")
    va = day.index >= '2026-01-01'; real = v.ls.mean(); null = []
    for _ in range(nperm):
        zz = z.copy(); zz['sig'] = rng.random(len(zz))  # iid random ranks within each (day, slot) = shuffle of the signal
        sn = spreads(zz); sn = sn[sn.index.get_level_values(1).isin(MAIN_SLOTS)]
        null.append(sn.ls.groupby(level=0).mean()[va].mean())
    null = np.array(null); n95 = np.quantile(null, 0.95)
    out.append(f"{label} VALID shuffle control ({nperm}): null mean {null.mean():+.3f} sd {null.std():.3f} 95th {n95:+.3f}; real {real:+.2f}")
    t = tstat(v.ls)
    checks = {'t>=BAR90 2.46': t >= BAR, 'TRAIN same sign': np.sign(real) == np.sign(tr.ls.mean()) and real > 0,
              f'slots same sign {nslot}/{ns} >= 8': nslot >= 8, 'real > null95': real > n95}
    ok = all(checks.values())
    verdict = ('LEAD (net > 0)' if real - 2 * COST_RT > 0 else 'TILT only (gross passes, net <= 0)') if ok else 'CLOSED'
    se = v.ls.std() / np.sqrt(len(v))
    out.append(f"{label} checks: " + '; '.join(f"{k} {'yes' if c else 'NO'}" for k, c in checks.items()) + f"; VALID t {t:+.2f} (full bar {FULLBAR} {'met' if t >= FULLBAR else 'not met'})")
    out.append(f"{label} VERDICT: {verdict}; VALID MDE at BAR90 {(BAR + 0.84) * se:.2f} bps (nothing above that if closed; smaller unknown); break-even cost per leg RT {real / 2:.2f} bps (main slots)")
    s15 = spall[spall.index.get_level_values(1) == '1530']
    if len(s15):
        x15 = s15.groupby(level=0).mean(); v15 = x15[x15.index >= '2026-01-01']
        out.append(f"{label} 15:30 slot APART (ends at the 16:00 close, not tradable by Live): VALID {v15.ls.mean():+.2f} bps (t {tstat(v15.ls):+.2f}), TRAIN {x15[x15.index < '2026-01-01'].ls.mean():+.2f}")
    return out, day

def prep_spy(src):
    d = pd.read_csv(src); d = d[d.symbol == 'SPY'].copy()
    if d.empty: print('SPY not in file: no up/down split'); return None
    d['t'] = pd.to_datetime(d.t, utc=True).dt.tz_convert('America/New_York')
    d['day'] = d.t.dt.date.astype(str); d['hm'] = d.t.dt.strftime('%H%M')
    w = d.pivot_table(index='day', columns='hm', values='c')
    return (w['1530'] / w['0930'] - 1).dropna()   # SPY from the 10:00 anchor (09:30-bar close) to the close

def synth(effect, ndays=120, nsym=60, seed=0, one_slot=False):
    rng = np.random.default_rng(seed); days = pd.bdate_range('2025-09-01', periods=ndays // 2).append(pd.bdate_range('2026-01-05', periods=ndays // 2))
    rows = []; slots = pd.date_range('09:30', '15:30', freq='30min').time; alpha = rng.normal(0, 1, (nsym, len(slots)))
    if one_slot: alpha[:, [k for k in range(len(slots)) if k != 4]] = 0   # effect only in the 11:30 slot
    for d in days:
        for s in range(nsym):
            p = 100.0
            for k, tt in enumerate(slots):
                p *= 1 + effect * 1e-4 * alpha[s, k] + rng.normal(0, 30e-4)
                rows.append((f"S{s}", pd.Timestamp.combine(d, tt).tz_localize('America/New_York').tz_convert('UTC'), p))
    return pd.DataFrame(rows, columns=['symbol', 't', 'c'])

if __name__ == '__main__':
    if sys.argv[1] == '--selftest':
        for eff, want, one in ((8.0, 'LEAD', False), (3.0, 'TILT', False), (0.0, 'CLOSED', False), (8.0, 'CLOSED', True)):
            z = signal(prep(synth(eff, one_slot=one)), 20); o, day = report(z, f'synth{eff:g}{"-oneslot" if one else ""}', nperm=20)
            for l in o:
                if 'VALID:' in l or 'checks' in l or 'VERDICT' in l: print(l)
            vd = [l for l in o if 'VERDICT' in l][0]
            assert want in vd, (eff, one, vd)
        bad = synth(0.0, ndays=10); bad = bad[~((bad.t.dt.tz_convert('America/New_York').dt.strftime('%H%M') == '1530') & (bad.index < 2000))]
        try: prep(bad); raise SystemExit('RTH assert did not fire')
        except AssertionError: print('RTH assert fires on a day missing its 15:30 bar: ok')
        x = prep(synth(0.0, ndays=40)); s = signal(x, 5)
        assert s.groupby('symbol').day.min().min() > x.day.min(), 'look-ahead: first day must have no signal'
        print('selftest OK'); sys.exit()
    src, outdir = sys.argv[1], sys.argv[2]
    x = prep(pd.read_csv(src)); lines = [f"HKS950 one look; {x.symbol.nunique()} names, {x.day.nunique()} days {x.day.min()}..{x.day.max()}; configs 2; family N 42 (cross-sectional return family); BAR90 {BAR}, full bar {FULLBAR}; universe = fixed top-500 ADV list of the 2026-10-05 snapshot applied back to 2024 (checklist 32: costs breadth)"]
    d0 = prep_spy(src)
    for L in (20, 40):
        o, day = report(signal(x, L), f'L{L}', spy=d0); lines += o
        day.to_csv(f"{outdir}/hks950_L{L}_days.csv")
    lines.append('Educational only - not financial advice.')
    open(f"{outdir}/hks950_out.txt", 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
