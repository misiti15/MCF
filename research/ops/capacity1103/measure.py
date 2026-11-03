"""capacity1103: measure GitHub Actions load and poll coverage (re-run after each rollout step).
Educational only — not financial advice.

  python research/ops/capacity1103/measure.py --since 2026-10-27 [--runs runs.json] [--polls-root DIR] --out results.json

GitHub side (repo-scoped REST via `gh api`, the same data the GitHub MCP actions tools return): every workflow run created
since --since and its jobs. A job holds a runner only when runner_name is set: a standby trade job waiting in its
concurrency group shows started_at = created_at but status pending and no runner, so it is NOT counted. Per session day
(09:00-16:30 ET) it reports the exact peak of concurrently running jobs (event sweep, second resolution) and its mix,
the per-minute histogram, queue delay (job started - created; for trade jobs this includes the concurrency wait),
minutes per job and the trade handover gaps (previous trade job of an account completed -> next one started).
Poll side (optional, --polls-root holding <branch>/polls/<day>/*.jsonl.gz): polls per account, distinct poll minutes vs
the expected 09:30..last minute, gaps > 90 s, fetch ms.
"""
import argparse
import collections
import concurrent.futures as cf
import datetime as dt
import json
import statistics as st
import subprocess
import sys
from pathlib import Path

REPO = "misiti15/MCF"
UTC = dt.timezone.utc


def api(path):
    return json.loads(subprocess.check_output(["gh", "api", path]))


def fetch(since):
    runs, page = [], 1
    while True:
        d = api(f"repos/{REPO}/actions/runs?per_page=100&page={page}&created=>={since}")
        runs += d["workflow_runs"]
        if len(d["workflow_runs"]) < 100:
            break
        page += 1

    def jobs(r):
        out, pg = [], 1
        while True:
            d = api(f"repos/{REPO}/actions/runs/{r['id']}/jobs?filter=all&per_page=100&page={pg}")
            out += d["jobs"]
            if len(d["jobs"]) < 100:
                return out
            pg += 1

    with cf.ThreadPoolExecutor(8) as ex:
        js = list(ex.map(jobs, runs))
    return [dict(id=r["id"], name=r["name"], event=r["event"], created=r["created_at"], conclusion=r["conclusion"],
                 jobs=[dict(name=x["name"], created=x.get("created_at"), started=x["started_at"],
                            completed=x["completed_at"], status=x["status"], conclusion=x["conclusion"],
                            runner=x.get("runner_name")) for x in j]) for r, j in zip(runs, js)]


def P(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def et_offset(d):   # hours behind UTC (EDT until 2026-11-01, EST after)
    return 5 if d >= dt.date(2026, 11, 1) else 4


def github_load(runs, now):
    J = [dict(wf=r["name"], job=j["name"], cr=P(j["created"]), s=P(j["started"]), c=P(j["completed"]))
         for r in runs for j in r["jobs"] if j["runner"]]
    out = {"jobs_with_runner": len(J),
           "jobs_without_runner": sum(1 for r in runs for j in r["jobs"] if not j["runner"]), "days": {}, "per_workflow": {}}
    for d in sorted({j["cr"].date() for j in J}):
        o = et_offset(d)
        t0 = dt.datetime(d.year, d.month, d.day, 9 + o, 0, tzinfo=UTC)
        t1 = t0 + dt.timedelta(hours=7.5)
        run = [j for j in J if (j["c"] or now) > t0 and j["s"] < t1]
        ev = sorted([(j["s"], 1, j["wf"]) for j in run] + [((j["c"] or now), -1, j["wf"]) for j in run],
                    key=lambda x: (x[0], x[1]))
        cur, peak, at, mix = collections.Counter(), 0, None, {}
        for t, dl, w in ev:
            cur[w] += dl
            n = sum(cur.values())
            if n > peak and t0 <= t < t1:
                peak, at, mix = n, t, {k: v for k, v in cur.items() if v}
        mins, t = [], t0
        while t < min(t1, now):
            mins.append(sum(1 for j in run if j["s"] < t + dt.timedelta(minutes=1) and (j["c"] or now) > t))
            t += dt.timedelta(minutes=1)
        if not mins or peak == 0:
            continue
        out["days"][str(d)] = {"peak_exact": peak, "peak_at_et": (at - dt.timedelta(hours=o)).strftime("%H:%M:%S"),
                               "peak_mix": mix, "per_minute_max": max(mins), "per_minute_median": st.median(mins),
                               "per_minute_hist": dict(sorted(collections.Counter(mins).items()))}
    for w in sorted({j["wf"] for j in J}):
        L = [j for j in J if j["wf"] == w]
        q = sorted((j["s"] - j["cr"]).total_seconds() for j in L)
        m = sorted((j["c"] - j["s"]).total_seconds() / 60 for j in L if j["c"])
        out["per_workflow"][w] = {"jobs": len(L), "queue_s_median": st.median(q), "queue_s_p90": q[int(0.9 * (len(q) - 1))],
                                  "queue_s_max": q[-1], "minutes_median": round(st.median(m), 2) if m else None,
                                  "minutes_p90": round(m[int(0.9 * (len(m) - 1))], 1) if m else None,
                                  "minutes_total": round(sum(m))}
    by = collections.defaultdict(list)
    for j in J:
        if j["wf"] == "trade" and j["c"] and (j["c"] - j["s"]).total_seconds() > 1800:
            by[(j["s"].date(), j["job"])].append((j["s"], j["c"]))
    gaps = [(b[0] - a[1]).total_seconds() for v in by.values() for a, b in zip(sorted(v), sorted(v)[1:])]
    out["trade_handover_gap_s"] = {"n": len(gaps), "max": max(gaps) if gaps else None,
                                   "median": st.median(gaps) if gaps else None}
    return out


def polls(root, days, accounts):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from mcf.execution.runner import read_poll_log

    def sec(t):
        h, m, s = map(int, t.split(":"))
        return h * 3600 + m * 60 + s

    out = {}
    for day in days:
        for acc, br in accounts.items():
            r = read_poll_log(str(Path(root) / br / "polls"), day)
            if not r:
                continue
            lh, lm = map(int, r[-1]["lm"].split(":"))
            exp = lh * 60 + lm - (9 * 60 + 30) + 1
            ts = [sec(x["t"]) for x in r]
            gaps = [ts[i] - ts[i - 1] for i in range(1, len(r)) if ts[i] - ts[i - 1] > 90]
            ms = sorted(x["ms"] for x in r)
            out[f"{day} {acc}"] = {"polls": len(r), "distinct_minutes": len({x["lm"] for x in r}), "expected": exp,
                                   "coverage": round(len({x["lm"] for x in r}) / exp, 3), "gaps_gt90s": len(gaps),
                                   "longest_gap_s": max(gaps) if gaps else 0, "fetch_ms_median": st.median(ms),
                                   "fetch_ms_p90": ms[int(0.9 * (len(ms) - 1))], "stale_polls": sum(x["stale"] for x in r)}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=str(dt.date.today() - dt.timedelta(days=7)))
    ap.add_argument("--runs", help="cached runs json (written when missing)")
    ap.add_argument("--polls-root")
    ap.add_argument("--poll-days", default="")
    ap.add_argument("--out", default="results.json")
    a = ap.parse_args()
    if a.runs and Path(a.runs).exists():
        runs = json.load(open(a.runs))
    else:
        runs = fetch(a.since)
        if a.runs:
            json.dump(runs, open(a.runs, "w"))
    res = {"since": a.since, "measured_at_utc": dt.datetime.now(UTC).isoformat(timespec="seconds"),
           "runs": len(runs), "github": github_load(runs, dt.datetime.now(UTC))}
    if a.polls_root:
        accts = {"primary": "br_mcf-data", "testing": "br_mcf-data-testing", "testing2": "br_mcf-data-testing2",
                 "gen": "br_mcf-data-gen", "graveyard": "br_mcf-data-graveyard"}
        res["polls"] = polls(a.polls_root, [d for d in a.poll_days.split(",") if d], accts)
    json.dump(res, open(a.out, "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in res["github"].items() if k != "per_workflow"}, indent=1, default=str)[:3000])
