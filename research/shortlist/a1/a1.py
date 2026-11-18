"""A1 descriptive (frozen PLAN.md). Educational only - not financial advice.
  python3 -I a1.py --selftest
  python3 -I a1.py <moves.csv> <a1_m5.csv.gz> <universe.csv> <out.txt>"""
import sys, numpy as np, pandas as pd
ETF = r"\bETF\b|Trust|Fund|ProShares|iShares|SPDR|Direxion|Invesco|Vanguard|\bShares\b|Leveraged|Bull|Bear"

def bucket(s):
    s = str(s)
    return 'skipped' if s.startswith('skipped') else s

def measure(mv, bars):
    """mv: one catalogue row; bars: that symbol-day's 5-min bars with 'end' (ET HH:MM bar end) sorted"""
    b = bars.set_index('end'); dec = mv['decision']; t0 = max(dec, '09:50')
    if t0 not in b.index or '15:55' not in b.index: return None
    p0 = b.at[t0, 'c']; atr = mv['atr_pct_d'] / 100 * p0; sg = 1 if mv['side'] == 'long' else -1
    w = b[(b.index > t0) & (b.index <= '15:55')]
    if w.empty: return None
    fav = (w.h - p0) if sg == 1 else (p0 - w.l)
    adv = (p0 - w.l) if sg == 1 else (w.h - p0)
    k = int(np.argmax(fav.values)); left_mfe = max(fav.iloc[k], 0) / atr
    mae_first = max(adv.iloc[:k + 1].max(), 0) / atr
    ex = mv['extreme']
    left_ext = max(sg * (b.at[ex, 'c'] - p0), 0) / atr if (ex > t0 and ex in b.index) else 0.0
    return dict(t0=t0, left_to_extreme=left_ext, share_left=left_ext / mv['move_atr'] if mv['move_atr'] > 0 else np.nan,
                left_mfe=left_mfe, mae_first=mae_first, close_left=sg * (b.at['15:55', 'c'] - p0) / atr, after950=ex > t0)

def run(m, bars, etfset):
    bars = bars.copy(); t = pd.to_datetime(bars.t, utc=True).dt.tz_convert('America/New_York')
    bars['end'] = (t + pd.Timedelta(minutes=5)).dt.strftime('%H:%M'); bars = bars.sort_values(['date', 'symbol', 'end'])
    g = {k: v for k, v in bars.groupby(['date', 'symbol'])}; out = []
    for _, mv in m.iterrows():
        bb = g.get((mv['date'], mv['symbol']))
        r = measure(mv, bb) if bb is not None else None
        if r: out.append(dict(date=mv['date'], side=mv['side'], bucket=bucket(mv['miss_reason']), etf=mv['symbol'] in etfset, **r))
    return pd.DataFrame(out)

def table(o):
    nd = o.date.nunique(); L = [f"A1: {len(o)} moves measured on {nd} sessions (ceiling: hindsight-picked movers). End = 15:55. ATR = daily ATR."]
    def row(lab, x):
        return (f"{lab:<44} n {len(x):>3} ({len(x) / nd:4.1f}/day)  extreme after 09:50 {x.after950.mean():5.0%}  left_to_extreme mean {x.left_to_extreme.mean():.2f} "
                f"med {x.left_to_extreme.median():.2f}  share_left {x.share_left.mean():4.0%}  left_mfe {x.left_mfe.mean():.2f}  mae_first {x.mae_first.mean():.2f}"
                f"  close_left {x.close_left.mean():+.2f}  >=0.5ATR {(x.left_mfe >= .5).sum() / nd:.1f}/day  >=1ATR {(x.left_mfe >= 1).sum() / nd:.1f}/day")
    L.append(row('ALL', o))
    for (s, e), x in o.groupby(['side', 'etf']): L.append(row(f"{s} {'ETF' if e else 'non-ETF'}", x))
    for (s, b), x in o[~o.etf].groupby(['side', 'bucket']): L.append(row(f"  non-ETF {s} | {b}", x))
    return L

def synth():
    rows = []; ends = pd.date_range('2026-11-02 09:35', '2026-11-02 16:00', freq='5min', tz='America/New_York')
    for sym, path in (('UPLATE', lambda i: 100 + (0 if i < 8 else (i - 8) * 0.2)), ('UPEARLY', lambda i: 100 + min(i, 3) * 2.0)):
        for i, e in enumerate(ends):
            p = path(i); rows.append(('2026-11-02', sym, (e - pd.Timedelta(minutes=5)).tz_convert('UTC').isoformat(), p, p + 0.05, p - 0.05, p, 1000))
    bars = pd.DataFrame(rows, columns=['date', 'symbol', 't', 'o', 'h', 'l', 'c', 'v'])
    m = pd.DataFrame([dict(date='2026-11-02', side='long', symbol='UPLATE', decision='09:35', extreme='15:00', move_atr=5.0, atr_pct_d=2.0, miss_reason='no setup signalled'),
                      dict(date='2026-11-02', side='long', symbol='UPEARLY', decision='09:35', extreme='09:50', move_atr=3.0, atr_pct_d=2.0, miss_reason='caught')])
    return m, bars

if __name__ == '__main__':
    if sys.argv[1] == '--selftest':
        m, bars = synth(); o = run(m, bars, set())
        late, early = o.iloc[0], o.iloc[1]
        assert late.after950 and late.left_to_extreme > 3 and late.left_mfe >= late.left_to_extreme, late
        assert (not early.after950) and early.left_to_extreme == 0 and early.left_mfe < 0.1, early
        print('\n'.join(table(o))); print('selftest OK'); sys.exit()
    m = pd.read_csv(sys.argv[1]); m = m[(m.set == 'all') & (~m.blackout)]
    u = pd.read_csv(sys.argv[3]); etfset = set(u[u.name.str.contains(ETF, case=False, regex=True)].symbol)
    o = run(m, pd.read_csv(sys.argv[2]), etfset)
    L = table(o) + [f"unmeasured (no bar at T0 or 15:55): {len(m) - len(o)}", "Educational only - not financial advice."]
    open(sys.argv[4], 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
