"""W3-reps inventory: per setup x account live signals / fills / skips by reason / traded sessions / R (after costs),
resource use per account, zero-fill triage. Inputs: journal copies (live run = runs.kind 'paper' id 1), snapshots.csv.
Usage: python inventory.py <dbdir> <snapshots.csv> <assignments.json> <outdir>. Educational only - not financial advice."""
import csv, json, re, sqlite3, sys, collections, math
dbdir, snapf, asgf, outd = sys.argv[1:5]
ACCS = ["primary", "ondeck", "tA", "tB", "tC", "tD", "tE", "tF", "gen", "gy"]
ASG = {"primary": "primary", "testing": "ondeck", "testing2": "tA", "explore1": "tB", "livelab": "tC", "testingd": "tD",
       "testinge": "tE", "testingf": "tF", "gen": "gen", "graveyard": "gy"}
SLOTS = {"primary": 77, "ondeck": 400, "tA": 800, "tB": 400, "tC": 400, "tD": 400, "tE": 400, "tF": 400, "gen": 300, "gy": 300}

def cat(reason):
    r = (reason or "").lower()
    if "not shortable" in r or "etb" in r or "split-tape" in r or "split tape" in r: return "borrow/short-gate"
    if r.startswith("spread") : return "spread"
    if "cost filter" in r: return "cost filter"
    if "setup daily loss" in r: return "setup -2R latch"
    if "halted" in r or r.startswith("daily loss limit"): return "account halt"
    if "max positions for this setup" in r: return "per-setup cap"
    if "max concurrent" in r: return "slots full"
    if '"buying_power"' in r: return "buying power (broker)"
    if "base_price" in r: return "broker target reject"
    if "opposite side" in r or "twin" in r or "already in symbol" in r or "lot cap" in r or "same setup" in r: return "symbol crowding"
    if "size <" in r or "price below" in r: return "size/price"
    if "through target" in r or "through stop" in r or "crosscheck" in r or "missed" in r or "no quote" in r: return "quote/timing"
    if "mismatch" in r: return "account halt"
    return "other"

RESOURCE = {"account halt", "per-setup cap", "slots full", "buying power (broker)", "symbol crowding", "setup -2R latch"}

asg = json.load(open(asgf))
home = {}
for a, ss in asg["accounts"].items():
    for s in ss: home.setdefault(s, []).append(ASG.get(a, a))

snap = collections.defaultdict(set)  # (acct, setup) -> enabled days
for r in csv.DictReader(open(snapf)):
    if r["enabled"] == "1": snap[(r["account"], r["setup"])].add(r["day"])

rows = {}
def R(a, s):
    k = (a, s)
    if k not in rows:
        rows[k] = dict(sig=0, sub=0, skip=collections.Counter(), trades=[], sdays=set(), shadow=[], shadow_sig=0)
    return rows[k]

acct_day = collections.defaultdict(dict)
for a in ACCS:
    c = sqlite3.connect(f"{dbdir}/{a}.db")
    live = c.execute("select id from runs where kind='paper' order by id limit 1").fetchone()[0]
    sh = c.execute("select id from runs where kind='shadow' order by id limit 1").fetchone()
    sh = sh[0] if sh else -1
    for day, s, st, reason in c.execute("select day,strategy,status,reason from signals where run_id=?", (live,)):
        x = R(a, s); x["sig"] += 1; x["sdays"].add(day)
        if st == "submitted": x["sub"] += 1
        elif st in ("skipped", "rejected"): x["skip"][cat(reason)] += 1
    for s, st, n in c.execute("select strategy,status,count(*) from signals where run_id=? group by 1,2", (sh,)):
        if st in ("shadow_entered", "shadow_skipped"): R(a, s)["shadow_sig"] += n
    for s, d, e, stp, sh_, pa, et, xt in c.execute(
            "select strategy,date,entry,stop,shares,pnl_adj,entry_time,exit_time from trades where run_id=? and exit_time is not null and pnl_adj is not null", (live,)):
        den = abs(e - stp) * (sh_ or 0)
        if den > 0: R(a, s)["trades"].append((d, pa / den))
    for s, d, e, stp, sh_, pa in c.execute(
            "select strategy,date,entry,stop,shares,pnl_adj from trades where run_id=? and exit_time is not null and pnl_adj is not null", (sh,)):
        den = abs(e - stp) * (sh_ or 0)
        if den > 0: R(a, s)["shadow"].append((d, pa / den))
    # peak concurrent live lots per day (entry/exit timestamps)
    ev = collections.defaultdict(list)
    for d, et, xt in c.execute("select date,entry_time,exit_time from trades where run_id=? and entry_time is not null", (live,)):
        ev[d].append((et, 1)); ev[d].append((xt or "99", -1))
    for d, L in ev.items():
        cur = pk = 0
        for t, k in sorted(L, key=lambda z: (z[0], z[1])):
            cur += k; pk = max(pk, cur)
        acct_day[a][d] = pk
    c.close()

def wobd(tr):
    if not tr: return (None, None, None)
    byd = collections.defaultdict(float)
    for d, r in tr: byd[d] += r
    tot = sum(byd.values()); bd = max(byd, key=byd.get)
    rest = [r for d, r in tr if d != bd]
    share = (byd[bd] / tot) if tot > 0 else None
    return (sum(r for _, r in tr) / len(tr), (sum(rest) / len(rest)) if rest else None, share)

out = []
cats = ["borrow/short-gate", "spread", "cost filter", "setup -2R latch", "account halt", "per-setup cap", "slots full",
        "buying power (broker)", "broker target reject", "symbol crowding", "size/price", "quote/timing", "other"]
for (a, s), x in rows.items():
    days = snap.get((a, s), set())
    nd = len(days)
    tr = x["trades"]; td = len({d for d, _ in tr})
    last10 = sorted(days)[-10:]
    tr10 = [t for t in tr if t[0] in set(last10)]
    av, aw, sh = wobd(tr)
    skipped = sum(x["skip"].values())
    res = sum(v for k, v in x["skip"].items() if k in RESOURCE)
    top = x["skip"].most_common(1)[0] if x["skip"] else ("", 0)
    out.append(dict(setup=s, account=a, home=int(a in home.get(s, [])), live_sessions=nd,
                    sig=x["sig"], sig_per_sess=round(x["sig"] / nd, 2) if nd else None, submitted=x["sub"],
                    skipped=skipped, resource_skip=res, top_skip=f"{top[0]}:{top[1]}" if top[1] else "",
                    trades=len(tr), traded_sessions=td, trades_per_sess=round(len(tr) / nd, 2) if nd else None,
                    traded_rate=round(td / nd, 2) if nd else None,
                    last10_sessions=len(last10), last10_trades=len(tr10), last10_traded=len({d for d, _ in tr10}),
                    avg_r=None if av is None else round(av, 3), avg_r_wobd=None if aw is None else round(aw, 3),
                    best_day_share=None if sh is None else round(sh, 2),
                    shadow_sig=x["shadow_sig"], shadow_trades=len(x["shadow"]),
                    shadow_days=len({d for d, _ in x["shadow"]}),
                    **{"skip_" + k: x["skip"].get(k, 0) for k in cats}))
# include enabled setups that never signalled
seen = {(r["account"], r["setup"]) for r in out}
for (a, s), days in snap.items():
    if (a, s) not in seen:
        out.append(dict(setup=s, account=a, home=int(a in home.get(s, [])), live_sessions=len(days), sig=0, sig_per_sess=0,
                        submitted=0, skipped=0, resource_skip=0, top_skip="", trades=0, traded_sessions=0, trades_per_sess=0,
                        traded_rate=0, last10_sessions=min(10, len(days)), last10_trades=0, last10_traded=0, avg_r=None,
                        avg_r_wobd=None, best_day_share=None, shadow_sig=0, shadow_trades=0, shadow_days=0,
                        **{"skip_" + k: 0 for k in cats}))
w = csv.DictWriter(open(f"{outd}/inventory_by_account.csv", "w", newline=""), fieldnames=list(out[0].keys()))
w.writeheader(); [w.writerow(r) for r in sorted(out, key=lambda r: (r["account"], r["setup"]))]

# resources per account
with open(f"{outd}/account_resources.csv", "w", newline="") as f:
    ww = csv.writer(f); ww.writerow(["account", "slots", "sessions", "median_peak_open", "max_peak_open", "max_peak_share",
                                     "signals", "submitted", "resource_skips", "resource_share", "top_resource_reasons"])
    for a in ACCS:
        pk = sorted(acct_day[a].values()) or [0]
        rr = [r for r in out if r["account"] == a]
        sig = sum(r["sig"] for r in rr); sub = sum(r["submitted"] for r in rr); res = sum(r["resource_skip"] for r in rr)
        rc = collections.Counter()
        for r in rr:
            for k in RESOURCE: rc[k] += r["skip_" + k]
        ww.writerow([a, SLOTS[a], len(acct_day[a]), pk[len(pk) // 2], pk[-1], round(pk[-1] / SLOTS[a], 2), sig, sub, res,
                     round(res / sig, 3) if sig else None, "; ".join(f"{k}:{v}" for k, v in rc.most_common(4) if v)])
print("ok", len(out))
