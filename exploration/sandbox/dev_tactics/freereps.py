"""Low-rep setups: how many reach 30 / 100 outcomes if the journals' what-if rows (run 2, signals not taken, scored with
the same bars) are counted beside live trades (10-23..11-27, all accounts, identical keys once). Counting only; what-if
fills are not calibrated against live (the shadow run is: see SHADOW in findings). Read-only. Educational only."""
import sqlite3, sys
from pathlib import Path
import pandas as pd
from mcf.research.shadow_calib import BRANCHES
p = []
for a, br in BRANCHES.items():
    con = sqlite3.connect(Path(sys.argv[1]) / f'{br}.db')
    x = pd.read_sql("SELECT run_id, strategy, symbol, date, entry_time FROM trades WHERE run_id IN (1,2) AND exit_time IS NOT NULL", con)
    con.close(); p.append(x)
t = pd.concat(p); t['date'] = t.date.astype(str).str[:10]; t = t[t.date >= '2026-10-23']
t['k'] = t.strategy + '|' + t.symbol + '|' + t.date + '|' + t.entry_time.astype(str).str[:16]
t = t.drop_duplicates(['run_id', 'k'])
live = t[t.run_id == 1].groupby('strategy').size(); wi = t[t.run_id == 2].groupby('strategy').size()
df = pd.concat([live.rename('live'), wi.rename('whatif')], axis=1).fillna(0)
df['both'] = df.live + df.whatif
for th in (30, 100):
    lo = df[df.live < th]
    print(f'setups with < {th} live trades: {len(lo)}; reach {th} with what-if counted: {(lo.both >= th).sum()}')
print('total live', int(df.live.sum()), 'what-if', int(df.whatif.sum()))
