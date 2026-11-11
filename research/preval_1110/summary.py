# PREVAL 1110 summary: PV books (Exposure Lab), live Primary (truth for PV0), Team books, crowding. Research only.
# Run from the repo root: python research/preval_1110/summary.py  (needs live_dd.py output dd_out.json next to it)
import json
from pathlib import Path
H = Path(__file__).resolve().parent
R = H.parents[1]
DAYS = ['2026-11-09', '2026-11-10']
lab = {d: json.load(open(R / f'research/exposure_lab/{d}.json')) for d in DAYS}
dd = json.load(open(H / 'dd_out.json'))
rows = {}
for name, get in [
    ('PV0 live (truth)', lambda d: dd[d]['PV0_live']),
    ('PV0 lab', lambda d: lab[d]['books']['PV0']),
    ('PV1 lab', lambda d: lab[d]['books']['PV1']),
    ('PV1 live subset', lambda d: dd[d]['PV1_live_subset']),
    ('PV2 lab (= TEAM-6 lineup)', lambda d: lab[d]['books']['PV2']),
    ('TEAM-6 Team sim', lambda d: dd[d]['TEAM6_sim']),
    ('TEAM-6 live subset', lambda d: dd[d]['TEAM6_live_subset']),
    ('TEAM-8 Team sim (11-09 = Team-7)', lambda d: dd[d]['TEAM_full_sim']),
    ('All 26 together (lab)', lambda d: lab[d]['together']),
]:
    v = [get(d) for d in DAYS]
    rows[name] = v
    print(f"| {name} | " + " | ".join(f"{x['r']:+.2f} ({x['trades']})" for x in v)
          + f" | {sum(x['r'] for x in v):+.2f} | {sum(x['r'] > 0 for x in v)}/2 | {min(x['worst_intraday_dd_r'] for x in v):+.2f} |")
print()
T6 = lab['2026-11-10']['books']['PV2']['setups']
for bk in ['PV0', 'PV1', 'PV2']:
    print(bk, {d: lab[d]['books'][bk]['per_setup'] for d in DAYS})
print()
print('| setup | ' + ' | '.join(f'{d[5:]} alone | {d[5:]} PV2 book | {d[5:]} all-26 together' for d in DAYS) + ' |')
for s in lab['2026-11-10']['books']['PV0']['setups'] + ['NM-ETF-late-dip-di-long', 'CWT09-gapdn-vwaploss-g10-short']:
    cells = []
    for d in DAYS:
        a = lab[d]['alone'].get(s, {})
        b = lab[d]['books']['PV2']['per_setup'].get(s)
        c = next((c for c in lab[d]['crowding'] if c['id'] == s), {})
        cells += [f"{a.get('r', 0):+.2f}/{a.get('trades', 0)}",
                  (f"{b['r']:+.2f}/{b['trades']}" if b else '-'),
                  f"{c.get('together_r', 0):+.2f}/{c.get('together_trades', 0)}"]
    print(f"| {s} | " + ' | '.join(cells) + ' |')
print()
for d in DAYS:
    print(d, 'pairs', [(p['a'][:14], p['b'][:14], p['same_symbol_overlaps'], p['opposite_side'], p['corr_5min'])
                       for p in lab[d]['pairwise'] if p['a'] in T6 and p['b'] in T6])
    print(d, 'PV2 skips', lab[d]['books']['PV2']['skips'])
    print(d, 'method', lab[d]['method'])
