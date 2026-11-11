# Worst intraday drawdown (5-min marked R path) for live Primary, live subsets and the Team books. Research only.
# python research/preval_1110/live_dd.py <repo root> <dir with mcf-data.db, mcf-data-livelab.db> <team 1Min cache dir>
# (journals: git show origin/<branch>:journal.db > <branch>.db). R = pnl_adj / (|entry - stop| x shares).
import sys, json, sqlite3, os
sys.path.insert(0, sys.argv[1])
DB, BARS = sys.argv[2], sys.argv[3]
import pandas as pd
from mcf.report.exposure_lab import r_path, book_stats, grid
WT = sys.argv[1]
T6 = ['RW3-gapdn-rsi5pop-flowsell-short-FD','RW5-heat30-flowsell-rsi5pop-gapdn-short-FD','L3-gap-slope-fromopen-FD',
      'ST7-rsi50dn-long-pm-t1s1-FD','NS5-sma50-flush-oversold-long','NM-ETF-late-dip-di-long']
PV1_OUT = {'MF2-open-rsimidhi-flowsell-FD','MF4-h40-open-flowsell-FD','MF4-h40-open-flowsell'}
def live(db, day, strat=None):
    c = sqlite3.connect(os.path.join(DB, db)); out = []
    for s, sym, side, en, st, sh, et, xt, p in c.execute(
        "select strategy,symbol,side,entry,stop,shares,entry_time,exit_time,pnl_adj from trades where run_id=1 and date=? "
        "and exit_time is not null and pnl_adj is not null", (day,)):
        if strat and s not in strat: continue
        risk = abs(en-st)*sh
        if risk > 0:
            out.append(dict(strategy=s, symbol=sym, side=side, entry=en, stop=st, shares=sh, entry_time=et, exit_time=xt, r=p/risk))
    return out
res = {}
for day in ['2026-11-09', '2026-11-10']:
    x = pd.read_parquet(f'{BARS}/{day}.parquet')
    x = x.set_index(pd.DatetimeIndex(x.ts).tz_convert('America/New_York'))
    closes = {s: g['close'] for s, g in x.groupby('symbol')}
    g = grid(day)
    P = live('mcf-data.db', day)
    strats = sorted({t['strategy'] for t in P})
    books = {
        'PV0_live': P,
        'PV1_live_subset': [t for t in P if t['strategy'] not in PV1_OUT],
        'TEAM6_live_subset': [t for t in P if t['strategy'] in T6] + live('mcf-data-livelab.db', day, {'NM-ETF-late-dip-di-long'}),
    }
    tj = json.load(open(f'{WT}/research/shadow_primary/team/{day}.json'))
    tt = [t for t in tj['trades'] if t.get('r') == t.get('r') and t.get('r') is not None]
    books['TEAM_full_sim'] = tt
    books['TEAM6_sim'] = [t for t in tt if t['strategy'] in T6]
    res[day] = {}
    for k, b in books.items():
        s = book_stats(b, r_path(b, closes, g)); res[day][k] = s
        print(day, k, s['trades'], s['r'], s['worst_intraday_dd_r'], s['low_r'])
    res[day]['primary_strategies'] = strats
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dd_out.json'), 'w'), indent=1)
