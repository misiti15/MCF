"""Skip reasons for the current regime (sessions >= 2026-11-17, TSZ1 sizing) per account, and per-setup resource
skips in testing accounts. Usage: recent_skips.py <dbdir>. Educational only."""
import sqlite3, sys, collections
dbdir = sys.argv[1]
def cat(r):
    r = (r or "").lower()
    for k, v in (("not shortable", "borrow/short-gate"), ("split", "borrow/short-gate"), ("spread", "spread"), ("cost filter", "cost filter"),
                 ("setup daily loss", "setup -2R latch"), ("halted", "account halt"), ("max positions for this setup", "per-setup cap"),
                 ("max concurrent", "slots full"), ('"buying_power"', "buying power (broker)"), ("base_price", "broker target reject"),
                 ("opposite side", "symbol crowding"), ("twin", "symbol crowding"), ("already in symbol", "symbol crowding"), ("lot cap", "symbol crowding")):
        if k in r: return v
    return "other"
RES = {"account halt", "per-setup cap", "slots full", "buying power (broker)", "symbol crowding", "setup -2R latch"}
for a in ["primary", "ondeck", "tA", "tB", "tC", "tD", "tE", "tF", "gen", "gy"]:
    c = sqlite3.connect(f"{dbdir}/{a}.db")
    n = c.execute("select count(*), sum(status='submitted') from signals where run_id=1 and day>='2026-11-17'").fetchone()
    cc = collections.Counter(); ps = collections.Counter()
    for s, r in c.execute("select strategy,reason from signals where run_id=1 and day>='2026-11-17' and status in ('skipped','rejected')"):
        k = cat(r); cc[k] += 1
        if k in RES: ps[s] += 1
    res = sum(v for k, v in cc.items() if k in RES)
    print(f"{a}: signals {n[0]}, submitted {n[1]}, resource skips {res} ({100*res/max(n[0],1):.1f}%) |", dict(cc.most_common(6)))
    if a not in ("gy",):
        print("    top resource-skipped setups:", [(s[:40], v) for s, v in ps.most_common(4)])
