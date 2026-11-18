"""Zero-/low-fill triage for setups enabled on the last snapshot day (11-18), from inventory_by_account.csv + snapshots.csv.
DORMANT = <= 0.1 live signals per enabled session over >= 5 sessions; BLOCKED = >= 60% of signals skipped (top reason);
NEW = < 3 enabled sessions in this account; SLOW = < 0.5 fills per session; OK otherwise. Educational only."""
import csv, sys, collections
inv, snapf, outf = sys.argv[1:4]
en = set(); last = "2026-11-18"
for r in csv.DictReader(open(snapf)):
    if r["day"] == last and r["enabled"] == "1": en.add((r["account"], r["setup"]))
rows = [r for r in csv.DictReader(open(inv)) if (r["account"], r["setup"]) in en]
out = []
for r in rows:
    ns = int(r["live_sessions"]); sig = int(r["sig"]); sk = int(r["skipped"]); tr = int(r["trades"])
    sps = sig / ns if ns else 0
    if ns < 3: cls = "NEW"
    elif sps <= 0.1: cls = "DORMANT"
    elif sig and sk / sig >= 0.6: cls = "BLOCKED"
    elif tr / ns < 0.5: cls = "SLOW"
    else: cls = "OK"
    out.append(dict(account=r["account"], setup=r["setup"], cls=cls, sessions=ns, sig_per_sess=round(sps, 2),
                    skip_share=round(sk / sig, 2) if sig else None, fills_per_sess=round(tr / ns, 2) if ns else 0,
                    trades=tr, traded_sessions=r["traded_sessions"], top_skip=r["top_skip"]))
w = csv.DictWriter(open(outf, "w", newline=""), fieldnames=list(out[0].keys())); w.writeheader()
for r in sorted(out, key=lambda r: (r["cls"], r["account"], r["setup"])): w.writerow(r)
c = collections.Counter((r["account"], r["cls"]) for r in out)
for a in ["primary", "ondeck", "tA", "tB", "tC", "tD", "tE", "tF", "gen", "gy"]:
    print(a, {k: c[(a, k)] for k in ["OK", "SLOW", "BLOCKED", "DORMANT", "NEW"]})
print("total enabled", len(out), collections.Counter(r["cls"] for r in out))
for r in out:
    if r["cls"] in ("DORMANT", "BLOCKED", "SLOW"): print(" ", r["cls"], r["account"], r["setup"][:62], r["sessions"], r["sig_per_sess"], r["skip_share"], r["fills_per_sess"], r["top_skip"])
