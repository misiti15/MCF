"""Weekly top-20 re-rank (owner request 2026-11-25), 2026-11-27.

Rank non-Graveyard setups (dashboard leaderboard merge: one row per setup, all accounts' EOD scorecards merged;
GEN-* only if graduated to a testing area; Graveyard-only and no_leaderboard setups out; assigned somewhere now)
by avg R per trade WITHOUT the best session (>= 20 trades). R = scorecard R after costs, LR8 basis (DQ-P3).
Reads origin/mcf-data*/reports/scorecard.json via git show (GET-only data; no broker calls).
Usage: python research/rerank_1127/rerank.py <git-dir>   -> research/rerank_1127/rerank.json
Educational only - not financial advice.
"""
import json, math, subprocess, sys, pathlib
GIT = sys.argv[1] if len(sys.argv) > 1 else "."
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ACC = {"primary": "mcf-data", "testing": "mcf-data-testing", "testing2": "mcf-data-testing2", "gen": "mcf-data-gen",
       "graveyard": "mcf-data-graveyard", "livelab": "mcf-data-livelab", "explore1": "mcf-data-explore1",
       "testingd": "mcf-data-testingd", "testinge": "mcf-data-testinge", "testingf": "mcf-data-testingf"}
LAB = {"primary": "Primary", "testing": "On Deck", "testing2": "Testing A", "explore1": "Testing B", "livelab": "Testing C",
       "testingd": "Testing D", "testinge": "Testing E", "testingf": "Testing F", "gen": "Gen", "graveyard": "Graveyard"}
WEEK = ("2026-11-23", "2026-11-27")
# last week's list: research/bdi/top20/CONDITIONS.md, 2026-11-21 block (shrunk-score leaderboard as of 11-20, >= 20 tr, GEN-* out)
LAST = ["ULT-05-withgap-cont-short", "L3-gap-slope-fromopen-FD", "L3-gap-slope-lowdist-FD",
        "RW3-gapdn-rsi5pop-flowsell-short-FD", "NM-RWN4-ns2-spyup05-notfri-short", "CWT09-gapdn-vwaploss-g10-short",
        "RW3-gapdn-rsi5pop-flowsell-short-FD-WB4", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
        "CWT14-failbrk-orl-p10-long-WB5", "NM-MF3-qqqdn-gapdn-FD", "NM-RWR4-ns2-up3-qqqup-slopedn-short",
        "L3-gap-slope-rsi5hi-FD", "RW7-gapdn-bounce-early-short-FD-WB3", "RW7-gapdn-bounce-early-short-FD",
        "MF4-h40-open-flowsell", "NS1-rsidip-rsi5pop-long", "RW1-gapdn-bounce-flowsell-short-FD",
        "RW6G1-ns2-up3-vwap2sd-short-FD", "CWT12-flag-s1-long", "ST3-rsi5up-short-pm-t1s1-FD"]

def card(br):
    try:
        return json.loads(subprocess.run(["git", "-C", GIT, "show", f"origin/{br}:reports/scorecard.json"],
                                         capture_output=True, text=True, check=True).stdout)
    except Exception:
        return None

asg = json.load(open(ROOT / "docs/live/assignments.json"))
S = asg["setups"]
isgen = lambda s: s.startswith("GEN-")
grad = lambda s: isgen(s) and any(a != "gen" for a in S.get(s, {}).get("accounts", []))
rows, gen_at = {}, {}
for k, br in ACC.items():
    c = card(br)
    if not c:
        continue
    gen_at[k] = c.get("generated")
    for r in c.get("leaderboard") or []:
        if isgen(r["setup"]) and not grad(r["setup"]):
            continue
        rows.setdefault(r["setup"], []).append({**r, "acct": k})

def merge(name, rs):
    tr = [r for r in rs if r.get("trades")]
    n = sum(r["trades"] for r in tr); tot = sum(r.get("total_r") or 0 for r in tr)
    if not n:
        return None
    avg = tot / n
    ex = all(r.get("r_sq_sum") is not None for r in tr)
    t = None
    if len(tr) == 1:
        t = tr[0].get("t_stat")
    elif ex and n > 1:
        v = (sum(r["r_sq_sum"] for r in tr) - n * avg * avg) / (n - 1)
        t = round(avg / math.sqrt(v / n), 2) if v > 0 else None
    by = {}
    for r in tr:
        for d, cnt, R, *_ in r.get("daily") or []:
            a = by.setdefault(d, [0, 0.0]); a[0] += cnt; a[1] += R or 0
    ds = {d: v for d, v in by.items() if v[0] > 0}
    exbest = share = bd = None; nleft = None
    if len(ds) >= 2:
        bd, (bn, br) = max(ds.items(), key=lambda x: x[1][1])
        exbest = (tot - br) / (n - bn) if n - bn > 0 else None; nleft = n - bn
        share = min(9.99, br / tot) if tot > 0 and br > 0 else None
    tday = None
    if len(ds) > 2:
        mu = [v[1] / v[0] for v in ds.values()]; mm = sum(mu) / len(mu)
        sd = math.sqrt(sum((x - mm) ** 2 for x in mu) / (len(mu) - 1))
        tday = round(mm / (sd / math.sqrt(len(mu))), 2) if sd > 0 else None
    wk = [v for d, v in ds.items() if WEEK[0] <= d <= WEEK[1]]
    wn = sum(v[0] for v in wk); wr = sum(v[1] for v in wk)
    pre = {d: v for d, v in ds.items() if d <= "2026-11-20"}
    pn = sum(v[0] for v in pre.values()); pr = sum(v[1] for v in pre.values())
    cur = [a for a in S.get(name, {}).get("accounts", [])]
    return {"setup": name, "accounts": cur, "account": " + ".join(LAB.get(a, a) for a in cur) or "(off)",
            "record_from": " + ".join(f"{LAB[r['acct']]} {r['trades']}" for r in tr),
            "trades": n, "sessions": len(ds), "total_r": round(tot, 2), "avg_r": round(avg, 3),
            "exbest_r": None if exbest is None else round(exbest, 3), "best_day": bd,
            "best_share": None if share is None else round(share, 3), "n_left": nleft, "t": t, "t_day": tday,
            "score": round(avg * n / (n + 20), 4),
            "week_trades": wn, "week_r": round(wr, 2), "week_avg": round(wr / wn, 3) if wn else None,
            "week_days": len(wk),
            "pre_trades": pn, "pre_avg": round(pr / pn, 3) if pn else None,
            "no_leaderboard": bool(S.get(name, {}).get("no_leaderboard"))}

M = {s: merge(s, rs) for s, rs in rows.items()}
M = {s: m for s, m in M.items() if m}
gyonly = lambda s: (lambda a: bool(a) and all(x == "graveyard" for x in a) and not S.get(s, {}).get("guest"))(S.get(s, {}).get("accounts", []))
elig = [m for s, m in M.items() if m["accounts"] and not gyonly(s) and not m["no_leaderboard"]
        and not all(a == "graveyard" for a in m["accounts"])]
q20 = [m for m in elig if m["trades"] >= 20 and m["exbest_r"] is not None]
new = sorted(q20, key=lambda m: -m["exbest_r"])
for i, m in enumerate(new):
    m["rank_wobest"] = i + 1
shr = sorted([m for m in elig if m["trades"] >= 20], key=lambda m: -m["score"])
for i, m in enumerate(shr):
    m["rank_score"] = i + 1
last = []
for i, s in enumerate(LAST):
    m = M.get(s)
    last.append({"last_rank": i + 1, "setup": s, **({k: m[k] for k in ("account", "accounts", "trades", "avg_r", "exbest_r",
                 "best_share", "week_trades", "week_r", "week_avg", "week_days", "pre_trades", "pre_avg", "rank_wobest", "rank_score")
                 if k in m} if m else {}),
                 "eligible_now": bool(m) and m in elig})
out = {"generated_from": gen_at, "week": WEEK, "n_eligible": len(elig), "n_ranked": len(new),
       "top20": new[:20], "ranked_all": new, "shrunk_top20": shr[:20], "last_week": last}
json.dump(out, open(HERE / "rerank.json", "w"), indent=1)
print(len(elig), len(new))

# per-day detail for the week (both lists) -> rerank_week.json
def days_of(name):
    by = {}
    for r in rows.get(name, []):
        for d, cnt, R, *_ in r.get("daily") or []:
            a = by.setdefault(d, [0, 0.0]); a[0] += cnt; a[1] += R or 0
    return {d: [v[0], round(v[1], 2)] for d, v in sorted(by.items()) if WEEK[0] <= d <= WEEK[1] and v[0]}
wk = {s: days_of(s) for s in set(LAST) | {m["setup"] for m in new[:20]}}
json.dump(wk, open(HERE / "rerank_week.json", "w"), indent=1)
