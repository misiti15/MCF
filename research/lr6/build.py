# LR6 2026-11-11 (research only): one row per live entry with signal/quote/fill/exit, segment features and the 1-min
# bar window it needs. Writes <S>/lr6/trades.pkl and <S>/lr6/bars.pkl. Reads journal copies from <S>/j (as live_ready).
import sqlite3, json, subprocess, io, os, sys
import pandas as pd, numpy as np
import pyarrow.parquet as pq, pyarrow.compute as pc

S = '/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad'
OUT = f'{S}/lr6'; os.makedirs(OUT, exist_ok=True)
REPO = '/home/user/MCF'
ACC = {'mcf-data': 'primary', 'mcf-data-testing': 'testing', 'mcf-data-testing2': 'testing2', 'mcf-data-gen': 'gen',
       'mcf-data-graveyard': 'graveyard', 'mcf-data-livelab': 'livelab', 'mcf-data-explore1': 'explore1'}
DAYF = {d: f'{S}/mh{d[5:7]}{d[8:]}/cov/days/{d}/bars.parquet' for d in ['2026-11-05', '2026-11-06', '2026-11-09', '2026-11-10']}
LO = pd.Timestamp('2026-10-01', tz='America/New_York')   # never examine anything before this (locked block 2024-11..2025-02)


def js(x):
    try: return json.loads(x)
    except Exception: return {}


def trades():
    out = []
    for b, a in ACC.items():
        db = sqlite3.connect(f'{S}/j/{b}.db')
        t = pd.read_sql("select t.* from trades t join runs r on r.id=t.run_id where r.kind='paper' and t.exit_time is not null and t.exit_time!='None'", db)
        o = pd.read_sql("select broker_order_id, entry_ref from orders", db)
        t = t.merge(o, on='broker_order_id', how='left'); t['acct'] = a; out.append(t)
    t = pd.concat(out, ignore_index=True)
    m = t.meta.fillna('').str.split(';').str[0].map(js)
    for k in ['bid', 'ask', 'spread_bps', 'quote_age_s', 'quote_dev_pct', 'bar_age_min']:
        t[k] = pd.to_numeric(m.map(lambda d: d.get(k)), errors='coerce')
    t['ts'] = pd.to_datetime(t.signal_time, utc=True, format='mixed').dt.tz_convert('America/New_York')
    t['tf'] = pd.to_datetime(t.entry_time, utc=True, format='mixed').dt.tz_convert('America/New_York')
    t['te'] = pd.to_datetime(t.exit_time, utc=True, format='mixed').dt.tz_convert('America/New_York')
    t['ref'] = t.entry_ref.astype(float)
    t['risk_plan'] = (t.ref - t.stop).abs()
    t = t[(t.ref > 0) & (t.risk_plan > 0)].copy()
    t['lat_s'] = (t.tf - t.ts).dt.total_seconds()
    u = pd.read_csv(io.StringIO(subprocess.run(['git', '-C', REPO, 'show', 'origin/mcf-data:universe.csv'], capture_output=True, text=True).stdout))
    t = t.merge(u[['symbol', 'name', 'adv', 'atr_pct']], on='symbol', how='left')
    nm = t.name.fillna('')
    etf = nm.str.contains(r'\bETF\b|Fund|Trust|iShares|SPDR|ProShares|Direxion|Invesco|VanEck|Vanguard|Shares\b|ETN', case=False)
    lev = nm.str.contains(r'2X|3X|1\.5X|1\.25X|-1X|Ultra|Leveraged|Daily .*(Bull|Bear)|Inverse|Short ', case=False)
    t['asset'] = np.where(lev & etf | lev & nm.str.contains('Daily', case=False), 'lev_etf', np.where(etf, 'etf', 'stock'))
    t['family'] = t.strategy.str.split('-').str[0]
    return t


def load_bars(t):
    need = t.groupby('symbol').date.agg(set)
    frames = []
    d0 = t.date.min()
    for sym, dates in need.items():
        f = f'{REPO}/data/cache_hist/1Min/{sym}.parquet'
        if not os.path.exists(f) or min(dates) > '2026-11-04': continue
        tb = pq.read_table(f)
        ix = tb.column('__index_level_0__')
        tb = tb.filter(pc.greater_equal(ix, pa_ts(LO)))
        b = tb.to_pandas()
        b = b[b.index.strftime('%Y-%m-%d').isin(dates)]
        b['symbol'] = sym; frames.append(b)
    for d, f in DAYF.items():
        b = pd.read_parquet(f)
        syms = set(t.symbol[t.date == d])
        b = b[b.symbol.isin(syms)]
        b.index = pd.to_datetime(b.index).tz_convert('America/New_York')
        frames.append(b[['open', 'high', 'low', 'close', 'volume', 'symbol']])
    # SPY for market condition (all live days + 7 prior sessions for the vol regime)
    tb = pq.read_table(f'{REPO}/data/cache_hist/1Min/SPY.parquet')
    tb = tb.filter(pc.greater_equal(tb.column('__index_level_0__'), pa_ts(pd.Timestamp('2026-09-20', tz='America/New_York'))))
    spy = tb.to_pandas()
    for d, f in DAYF.items():
        b = pd.read_parquet(f); b = b[b.symbol == 'SPY']; b.index = pd.to_datetime(b.index).tz_convert('America/New_York')
        spy = pd.concat([spy, b[['open', 'high', 'low', 'close', 'volume']]])
    bars = pd.concat(frames)
    bars.index.name = 'ts'
    bars = bars.reset_index().drop_duplicates(['symbol', 'ts']).set_index(['symbol', 'ts']).sort_index()
    return bars, spy[~spy.index.duplicated()].sort_index()


def pa_ts(x):
    import pyarrow as pa
    return pa.scalar(x.to_pydatetime(), type=pa.timestamp('us', tz='America/New_York'))


def features(t, bars, spy):
    # momentum into the signal: side x return from the close 3 minutes before the signal minute's last complete bar to ref
    mom = np.full(len(t), np.nan); has = np.zeros(len(t), bool)
    for i, (sym, ts, ref, s) in enumerate(zip(t.symbol, t.ts, t.ref, t.side)):
        try: b = bars.loc[sym]
        except KeyError: continue
        m0 = ts.floor('min')
        j = b.index.searchsorted(m0)            # bars strictly before the signal minute are complete
        if j >= 4 and j < len(b) and b.index[j] == m0:
            has[i] = True
            mom[i] = s * (ref / b.close.iloc[j - 4] - 1) * 1e4
    t['mom3_bps'] = mom; t['has_bars'] = has
    # SPY from open at signal, day range, prior-5-day range regime
    sd = spy.groupby(spy.index.date).agg(o=('open', 'first'), h=('high', 'max'), l=('low', 'min'), c=('close', 'last'))
    sd['rng'] = (sd.h - sd.l) / sd.o; sd['reg5'] = sd.rng.shift(1).rolling(5).mean()
    sd.index = [str(x) for x in sd.index]
    live = sd.reindex(sorted(t.date.unique())).dropna(subset=['reg5'])
    q = live.reg5.quantile([1 / 3, 2 / 3]).values
    t['vol_regime'] = t.date.map(lambda d: 'low' if sd.reg5.get(d, np.nan) <= q[0] else ('high' if sd.reg5.get(d, np.nan) > q[1] else 'mid'))
    spy_c = spy.close
    fo = []
    for d, ts in zip(t.date, t.ts):
        o = sd.o.get(d, np.nan)
        k = spy_c.index.searchsorted(ts.floor('min')) - 1
        fo.append(spy_c.iloc[k] / o - 1 if k >= 0 and str(spy_c.index[k].date()) == d else np.nan)
    t['spy_fo'] = fo
    t['spy_cond'] = np.where(t.spy_fo > 0.003, 'up', np.where(t.spy_fo < -0.003, 'down', 'quiet'))
    t.loc[t.spy_fo.isna(), 'spy_cond'] = 'na'
    t['spy_day'] = t.date.map((sd.c / sd.o - 1))
    # compass c30 as-of the signal (15-min log)
    c = pd.read_parquet(f'{S}/live_compass.parquet')[['date', 'T', 'c30']]
    c['k'] = c.date + ' ' + c['T']
    cm = dict(zip(c.k, c.c30))
    def comp(ts):
        q = ts.floor('15min') - pd.Timedelta(minutes=15)
        for _ in range(4):
            v = cm.get(f'{ts.date()} {q:%H:%M}')
            if v is not None: return v
            q -= pd.Timedelta(minutes=15)
        return 'na'
    t['compass'] = [comp(x) for x in t.ts]
    return t


if __name__ == '__main__':
    t = trades()
    if os.path.exists(f'{OUT}/bars.pkl'):
        bars, spy = pd.read_pickle(f'{OUT}/bars.pkl'), pd.read_pickle(f'{OUT}/spy.pkl')
    else:
        bars, spy = load_bars(t); bars.to_pickle(f'{OUT}/bars.pkl'); spy.to_pickle(f'{OUT}/spy.pkl')
    t = features(t, bars, spy)
    t.to_pickle(f'{OUT}/trades.pkl')
    print(len(t), t.has_bars.mean(), len(bars))
