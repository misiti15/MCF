"""Shadow (run kind 'shadow', of_live) vs live (run 1) on 11-17..: paired on account, setup, symbol, date, signal_time.
Match = share of live closed trades with a shadow lot on the same key; extra = shadow lots with no live lot whose live
signal was not a resource skip; paired R diff (shadow - live) with t. Per account + per setup family. Educational only."""
import sqlite3, sys, collections, math, json, re
dbdir = sys.argv[1]
ACCS = ["primary", "ondeck", "tA", "tB", "tC", "tD", "tE", "tF", "gen", "gy"]
RES = ("halted", "daily loss limit", "max trades/day", "max concurrent positions", "max positions for this setup", "twin held",
       "already in symbol", "opposite side held", "lot cap", "position mismatch", "same setup, same moment", "buying_power", "setup daily loss")
def fam(s): return re.split(r"-", s)[0]
def stats(d):
    n = len(d)
    if n < 2: return (n, None, None)
    m = sum(d) / n; sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1))
    return (n, round(m, 3), round(m / (sd / math.sqrt(n)), 2) if sd > 0 else None)
tot = collections.Counter(); diffs_all = []; byday = collections.defaultdict(lambda: [0.0, 0.0]); perfam = collections.defaultdict(list)
print("account live matched match% shadow extra extra% resource_only  paired_n meanDiff t")
for a in ACCS:
    c = sqlite3.connect(f"{dbdir}/{a}.db")
    sh = c.execute("select id from runs where kind='shadow' limit 1").fetchone()
    if not sh: continue
    sh = sh[0]
    def load(rid):
        out = {}
        for s, sym, d, st, e, stp, n, pa, meta in c.execute("select strategy,symbol,date,signal_time,entry,stop,shares,pnl_adj,meta from trades where run_id=? and date>='2026-11-17' and exit_time is not null and pnl_adj is not null", (rid,)):
            den = abs(e - stp) * (n or 0)
            if den <= 0: continue
            mt = re.search(r"bar_time=(\d{4})", meta or "") or re.search(r'-(\d{4})"', meta or "")
            k = (s, sym, d, mt.group(1) if mt else (st or "")[:16])
            out.setdefault(k, []).append(pa / den)
        return out
    L = load(1); Sh = load(sh)
    liveskip = {}
    for s, sym, d, ts, st, rs in c.execute("select strategy,symbol,day,ts,status,reason from signals where run_id=1 and day>='2026-11-17'"):
        liveskip[(s, sym, d)] = (st, rs or "")
    live_setups = {k[0] for k in L} | {s for (s, sym, d) in liveskip}
    m = 0; diffs = []
    for k, v in L.items():
        if k in Sh:
            m += len(v); 
            for x, y in zip(v, Sh[k]): diffs.append(y - x); perfam[fam(k[0])].append(y - x)
    nl = sum(len(v) for v in L.values())
    ex = 0; res = 0; nsh = 0
    for k, v in Sh.items():
        if k[0] not in live_setups: continue  # shadow-only setups are not part of the trust check
        nsh += len(v)
        if k in L: continue
        st, rs = liveskip.get((k[0], k[1], k[2]), ("", ""))
        if any(r in rs for r in RES): res += len(v)
        else: ex += len(v)
    n, md, t = stats(diffs); diffs_all += diffs
    print(a, nl, m, round(100 * m / nl, 1) if nl else None, nsh, ex, round(100 * ex / nsh, 1) if nsh else None, res, n, md, t)
    tot.update(live=nl, matched=m, shadow=nsh, extra=ex, res=res)
print("ALL", dict(tot), "match%", round(100 * tot["matched"] / tot["live"], 1), "extra%", round(100 * tot["extra"] / tot["shadow"], 1), stats(diffs_all))
print("per family paired diff (n, mean, t):")
for f, d in sorted(perfam.items(), key=lambda z: -len(z[1]))[:15]: print(" ", f, stats(d))

# setup-day and account-day R correlation (all trades, not only pairs)
def corr(x, y):
    n = len(x); mx = sum(x) / n; my = sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y)); sx = math.sqrt(sum((a - mx) ** 2 for a in x)); sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return round(sxy / (sx * sy), 3)
sd = collections.defaultdict(lambda: [0.0, 0.0, 0, 0]); ad = collections.defaultdict(lambda: [0.0, 0.0])
for a in ACCS:
    c = sqlite3.connect(f"{dbdir}/{a}.db")
    live_set = {r[0] for r in c.execute("select distinct strategy from signals where run_id=1 and day>='2026-11-17'")}
    for rid, j in ((1, 0), (3, 1)):
        for s, d, e, stp, n, pa in c.execute("select strategy,date,entry,stop,shares,pnl_adj from trades where run_id=? and date>='2026-11-17' and exit_time is not null and pnl_adj is not null", (rid,)):
            den = abs(e - stp) * (n or 0)
            if den <= 0 or s not in live_set: continue
            sd[(a, s, d)][j] += pa / den; sd[(a, s, d)][2 + j] += 1; ad[(a, d)][j] += pa / den
x = [v[0] for v in sd.values()]; y = [v[1] for v in sd.values()]
print("setup-days", len(x), "corr", corr(x, y), "| account-days", len(ad), "corr", corr([v[0] for v in ad.values()], [v[1] for v in ad.values()]))
print("rep count: live trades", sum(v[2] for v in sd.values()), "shadow trades", sum(v[3] for v in sd.values()),
      "| setup-days with live trade", sum(1 for v in sd.values() if v[2]), "with shadow trade", sum(1 for v in sd.values() if v[3]))
