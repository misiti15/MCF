"""Quality-rep measures. (1) per assigned setup: live trades, distinct symbol-days, active days, trades per active day,
max one-day share of trades (live run 1, all accounts merged). (2) Pseudo-replication: parent vs Workbench copy (-WBn)
live trades on the same symbol-day since 11-17. Usage: quality.py <dbdir> <assignments.json> <out.csv>. Educational only."""
import sqlite3, sys, json, collections, re, csv
dbdir, asgf, outf = sys.argv[1:4]
ACCS = ["primary", "ondeck", "tA", "tB", "tC", "tD", "tE", "tF", "gen", "gy"]
asg = json.load(open(asgf)); names = {s for ss in asg["accounts"].values() for s in ss}
T = collections.defaultdict(list)
for a in ACCS:
    c = sqlite3.connect(f"{dbdir}/{a}.db")
    for s, sym, d in c.execute("select strategy,symbol,date from trades where run_id=1 and exit_time is not null"):
        T[s].append((sym, d, a))
rows = []
for s in sorted(names):
    t = T.get(s, [])
    if not t: rows.append(dict(setup=s, trades=0, symbol_days=0, active_days=0, trades_per_active_day=None, max_day_share=None)); continue
    days = collections.Counter(d for _, d, _ in t)
    rows.append(dict(setup=s, trades=len(t), symbol_days=len({(x, d) for x, d, _ in t}), active_days=len(days),
                     trades_per_active_day=round(len(t) / len(days), 1), max_day_share=round(max(days.values()) / len(t), 2)))
w = csv.DictWriter(open(outf, "w", newline=""), fieldnames=list(rows[0].keys())); w.writeheader(); [w.writerow(r) for r in rows]
print("copy vs parent overlap since 11-17 (live symbol-days):")
for s in sorted(names):
    m = re.match(r"(.+)-WB\d+$", s)
    if not m: continue
    p = m.group(1)
    cs = {(x, d) for x, d, a in T.get(s, []) if d >= "2026-11-17"}
    ps = {(x, d) for x, d, a in T.get(p, []) if d >= "2026-11-17"}
    if cs or ps:
        print(f"  {s[:48]:48} copy {len(cs):4} parent {len(ps):4} shared {len(cs & ps):4} ({(100*len(cs & ps)/len(cs)) if cs else 0:.0f}% of copy)")
