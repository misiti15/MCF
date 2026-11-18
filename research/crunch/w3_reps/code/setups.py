"""Per assigned setup (docs/live/assignments.json, 11-18): merged live record across accounts (traded sessions = distinct
days with >= 1 closed live trade), current-account rate over its last <= 10 enabled sessions, sessions to reach 30 trades
AND 15 active days, shadow reps since 11-17. Usage: setups.py <dbdir> <snapshots.csv> <assignments.json> <out.csv>"""
import csv, json, sqlite3, sys, collections, math
dbdir, snapf, asgf, outf = sys.argv[1:5]
ACCS = ["primary", "ondeck", "tA", "tB", "tC", "tD", "tE", "tF", "gen", "gy"]
ASG = {"primary": "primary", "testing": "ondeck", "testing2": "tA", "explore1": "tB", "livelab": "tC", "testingd": "tD",
       "testinge": "tE", "testingf": "tF", "gen": "gen", "graveyard": "gy"}
HP = ["GEN-261027-08", "GEN-261027-01", "GEN-261026-03", "L3-gap-slope-rsi5hi", "L3-gap-slope-lowdist", "CWT09-gapdn-vwaploss-g10",
      "NM-RWR3", "NM-RWN5", "NM1-cwt09-g10", "NS3-failed-vwap", "MF2-open", "MF4-h40", "RW6G1", "CWT09-gapdn-bounce-g10", "NM-RWN"]
asg = json.load(open(asgf))
home = {}
for a, ss in asg["accounts"].items():
    for s in ss: home.setdefault(s, []).append(ASG.get(a, a))
snap = collections.defaultdict(set)
for r in csv.DictReader(open(snapf)):
    if r["enabled"] == "1": snap[(r["account"], r["setup"])].add(r["day"])
tr = collections.defaultdict(list); sh = collections.defaultdict(list); sig = collections.Counter()
for a in ACCS:
    c = sqlite3.connect(f"{dbdir}/{a}.db")
    live = c.execute("select id from runs where kind='paper' order by id limit 1").fetchone()[0]
    s3 = c.execute("select id from runs where kind='shadow' limit 1").fetchone(); s3 = s3[0] if s3 else -1
    for s, d, e, st, n, pa in c.execute("select strategy,date,entry,stop,shares,pnl_adj from trades where run_id=? and exit_time is not null and pnl_adj is not null", (live,)):
        den = abs(e - st) * (n or 0)
        if den > 0: tr[s].append((d, a, pa / den))
    for s, d, e, st, n, pa in c.execute("select strategy,date,entry,stop,shares,pnl_adj from trades where run_id=? and exit_time is not null and pnl_adj is not null", (s3,)):
        den = abs(e - st) * (n or 0)
        if den > 0: sh[s].append((d, a, pa / den))
    for s, d, n in c.execute("select strategy,day,count(*) from signals where run_id=? group by 1,2", (live,)):
        sig[(a, s, d)] += n
rows = []
for s, accts in home.items():
    t = tr.get(s, [])
    days = collections.defaultdict(float)
    for d, a, r in t: days[d] += r
    n = len(t); td = len(days)
    tot = sum(days.values())
    bd = max(days, key=days.get) if days else None
    rest = [r for d, a, r in t if d != bd]
    a = accts[0]
    en = sorted(snap.get((a, s), set()))
    last = en[-10:]
    tl = [x for x in t if x[1] == a and x[0] in set(last)]
    rate = len(tl) / len(last) if last else 0.0
    drate = len({x[0] for x in tl}) / len(last) if last else 0.0
    need_t = max(0, 30 - n); need_d = max(0, 15 - td)
    s_t = math.ceil(need_t / rate) if rate > 0 else (0 if need_t == 0 else None)
    s_d = math.ceil(need_d / drate) if drate > 0 else (0 if need_d == 0 else None)
    eta = None if (s_t is None or s_d is None) else max(s_t, s_d)
    shd = sh.get(s, [])
    sigs = sum(v for (aa, ss, d), v in sig.items() if ss == s and aa == a and d in set(last))
    rows.append(dict(setup=s, accounts="+".join(accts), hp=int(any(s.startswith(h) for h in HP)),
                     enabled_sessions_home=len(en), trades=n, traded_sessions=td,
                     avg_r=round(sum(r for *_, r in t) / n, 3) if n else None,
                     avg_r_wobd=round(sum(rest) / len(rest), 3) if rest else None,
                     best_day_share=round(days[bd] / tot, 2) if (days and tot > 0) else None,
                     total_r=round(tot, 1),
                     home_last_sessions=len(last), home_sig_per_sess=round(sigs / len(last), 2) if last else None,
                     home_trades_per_sess=round(rate, 2), home_traded_rate=round(drate, 2),
                     sess_to_30t=s_t, sess_to_15d=s_d, eta_sessions=eta,
                     shadow_trades=len(shd), shadow_days=len({d for d, *_ in shd}),
                     shadow_avg_r=round(sum(r for *_, r in shd) / len(shd), 3) if shd else None))
w = csv.DictWriter(open(outf, "w", newline=""), fieldnames=list(rows[0].keys()))
w.writeheader(); [w.writerow(r) for r in sorted(rows, key=lambda r: (r["accounts"], r["setup"]))]
print(len(rows))
