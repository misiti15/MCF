"""Blocked-signal audit, second run (2026-10-29), sessions 2026-10-27, 2026-10-28, 2026-10-29 in all five intraday accounts:
the first sessions with the GX1 5-minute clock gate (mcf.strategies.setups.lab_decision_buckets).

    python research/ops/blocked1029_audit.py <scratch>
      <scratch>/j/<branch>/journal.db            git show origin/<branch>:journal.db
      <scratch>/polls/<branch>/<day>/*.jsonl.gz  git show origin/<branch>:polls/<day>/...

Reads only. Writes research/ops/blocked1029_results.json and prints the tables of research/ops/blocked_audit.md.
1) coverage under GX1: a lab decision is taken only by a poll whose latest completed minute is a bucket's 4th minute
   (poll record exp % 5 == 0; no catch-up of older buckets), so coverage = decision minutes polled of 77 (exp 0..380),
   longest gap, handover gap (longest gap starting 14:20-14:45 ET), and the share of symbols whose bar for that minute had
   arrived at the decision poll ("fresh" / "got"; a symbol without a trade in that minute is decided by its next bar, so
   this share is a lower bound on symbol-level coverage).
2) never fired: setups enabled in the account's frozen setups/<day>.json with zero journaled signals (run 1, any status);
   lifetime signals in the same journal; build_strategies on the 10-29 freeze file (LOAD_FAILURES).
3)-5) skips by reason, priced with the journal's what-if run (run 2) gross and after the production cost model
   (config/default.yaml costs: $0.01/sh + 1 bps per side, target exits without slippage, +$0.02/sh on stops).
Educational only - not financial advice."""
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf.execution.runner import read_poll_log            # noqa: E402
from mcf.strategies import setups as SU                   # noqa: E402

S = Path(sys.argv[1])
DAYS = ["2026-10-27", "2026-10-28", "2026-10-29"]
ACCTS = {"Primary": "mcf-data", "Testing 1": "mcf-data-testing", "Testing 2": "mcf-data-testing2",
         "Graveyard": "mcf-data-graveyard", "Generated": "mcf-data-gen"}
QUEUE = ("twin held", "lot cap", "opposite side held", "already in symbol", "max positions for this setup")
DEC = set(range(0, 381, 5))
PH = ",".join("?" * len(DAYS))


def kind(reason: str, status: str) -> str:
    r = reason or ""
    if status == "rejected":
        if "insufficient" in r:
            return "broker reject: buying power"
        return "broker reject: bracket leg past base price"
    if r.startswith("crosscheck"):
        return "crosscheck"
    if r.startswith("missed: triggered"):
        return "missed: triggered"
    if r.startswith("no quote") or r.startswith("no two-sided"):
        return "no quote"
    if r.startswith("spread"):
        return "spread filter" if "bps" in r else "spread vs stop"
    if r.startswith("size <"):
        return "size < 1 share after liquidity cap"
    return r


def unintended(k: str) -> bool:
    return k.startswith("broker reject") or k in ("crosscheck", "missed: triggered", "no quote")


def net(w: pd.DataFrame) -> pd.Series:
    R = (w.entry - w.stop).abs()
    cps = (0.01 + w.entry * 1e-4) + np.where(w.exit_reason == "target", 0.0, 0.01 + w.exit * 1e-4) \
        + np.where(w.exit_reason == "stop", 0.02, 0.0)
    return w.r_multiple - np.where(R > 0, cps / R, 0.0)


EXPECTED = json.loads((ROOT / "research/generator/expected_live.json").read_text()).get("setups", {})


def p_zero(name: str, s: dict, k: int) -> float | None:
    """Chance of 0 signals in k sessions from the setup's own screen: the share of zero-signal days in its last 60 screen
    sessions (research/generator/expected_live.json counts60) when there is one, else 1 - days-with-a-signal / screen
    sessions (screen.all: n / per_day sessions). Generated setups only; None when the setup has no screen record.
    Ignores the earnings blackout and the live-universe difference, so it is a rough guide, not a test."""
    c = EXPECTED.get(name, {}).get("counts60")
    if c:
        z = sum(1 for x in c if x == 0) / len(c)
    else:
        sc = ((s or {}).get("gen") or {}).get("screen") or {}
        a, pdy = sc.get("all") or {}, sc.get("per_day")
        if not a.get("n") or not pdy:
            return None
        z = 1 - a["days"] / (a["n"] / pdy)
    return round(z ** k, 3)


def hhmm(exp: int) -> str:
    m = 30 + exp - 1          # exp = minutes 09:30..lm, so the decided minute lm = 09:30 + exp - 1
    return f"{9 + m // 60:02d}:{m % 60:02d}"


res: dict = {"days": DAYS, "coverage": {}, "never_fired": {}, "skips": {}, "queue": {}, "errors": {}, "unbooked": {}}
for acct, br in ACCTS.items():
    # ---- 1) coverage under GX1
    cov = {}
    for d in DAYS:
        recs = read_poll_log(str(S / "polls" / br), d)
        if not recs:
            cov[d] = None
            continue
        t = pd.to_datetime([f"{d} {r['t']}" for r in recs])
        g = np.diff(t.values).astype("timedelta64[s]").astype(float) / 60
        exps = {r["exp"] for r in recs}
        miss = sorted(DEC - exps)
        dp = [r for r in recs if r["exp"] % 5 == 0 and 20 <= r["exp"] <= 330]     # lab windows 09:50-15:00
        fresh = sum(r["fresh"] for r in dp) / max(1, sum(r["got"] for r in dp))
        i = int(g.argmax()) if len(g) else 0
        hw = [(recs[j]["t"], recs[j + 1]["t"], g[j]) for j in range(len(g)) if "14:20" <= recs[j]["t"][:5] <= "14:45"]
        h = max(hw, key=lambda z: z[2]) if hw else None
        cov[d] = dict(polls=len(recs), first=recs[0]["t"], last=recs[-1]["t"],
                      max_gap_min=round(float(g.max()), 1) if len(g) else None, max_gap_at=recs[i]["t"],
                      gaps_over_3=int((g > 3).sum()), stale_polls=sum(1 for r in recs if r.get("stale")),
                      decision_polled=len(DEC) - len(miss), decision_total=len(DEC),
                      decision_missed=[hhmm(m) for m in miss],
                      handover=f"{h[0]} -> {h[1]} ({h[2]:.1f} min)" if h else None,
                      fresh_at_decision_pct=round(100 * fresh, 1),
                      coverage_pct=round(100 * (len(DEC) - len(miss)) / len(DEC), 1))
    res["coverage"][acct] = cov

    # ---- 2) never fired
    c = sqlite3.connect(S / "j" / br / "journal.db")
    sig = pd.read_sql(f"select day, ts, symbol, strategy, side, status, reason, info from signals where run_id=1 and day in ({PH})",
                      c, params=DAYS)
    life = pd.read_sql("select strategy, count(*) n, max(day) last from signals where run_id=1 group by strategy", c) \
        .set_index("strategy")
    fired = sig.groupby("strategy").size().to_dict()
    enabled: dict[str, dict] = {}
    last_fz = None
    for d in DAYS:
        try:
            fz = json.loads(subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:setups/{d}.json"],
                                           capture_output=True, text=True, check=True).stdout)
        except Exception:
            continue
        last_fz = fz
        for name, s in fz.get("strategies", {}).items():
            if isinstance(s, dict) and s.get("enabled", True) is not False:
                e = enabled.setdefault(name, {"days": [], "type": s.get("type", "rule"), "min_adv": s.get("min_adv"),
                                              "window": s.get("window"), "context": s.get("context"),
                                              "module": s.get("module")})
                e["days"].append(d)
    nf = {n: e for n, e in enabled.items() if fired.get(n, 0) == 0}
    # every freeze file of the live record (sessions 10-12 .. the last audit day) for the lifetime session count
    ls = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "--name-only", f"origin/{br}", "setups/"],
                        capture_output=True, text=True).stdout.split()
    hist = {}
    for f in ls:
        d = Path(f).stem
        if "2026-10-12" <= d <= DAYS[-1] and nf:
            hist[d] = json.loads(subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:{f}"], capture_output=True,
                                                text=True).stdout or "{}").get("strategies", {})
    for n, e in nf.items():
        e["module_exists"] = (ROOT / e["module"]).exists() if e.get("module") else None
        e["lifetime_signals"] = int(life.n.get(n, 0))
        e["last_signal_day"] = life["last"].get(n)
        e["p_zero"] = p_zero(n, (last_fz or {}).get("strategies", {}).get(n, {}), len(e["days"]))
        e["sessions_enabled"] = sum(1 for fz in hist.values() if (fz.get(n) or {}).get("enabled", False) is not False and n in fz)
        e["p_zero_life"] = p_zero(n, (last_fz or {}).get("strategies", {}).get(n, {}), e["sessions_enabled"])
    load_fail = []
    if last_fz:
        try:
            SU.build_strategies({"strategies": last_fz.get("strategies", {}), "exits": last_fz.get("exits", {}),
                                 "universe": last_fz.get("universe", {})})
            load_fail = list(SU.LOAD_FAILURES)
        except Exception as ex:                       # report, do not hide
            load_fail = [("<build>", f"{type(ex).__name__}: {ex}")]
    res["never_fired"][acct] = {"enabled": len(enabled), "fired": len(enabled) - len(nf), "never": nf,
                                "load_failures": load_fail}

    # ---- 3)-5) skips priced with the what-if run
    w = pd.read_sql("select symbol, strategy, side, date, signal_time, entry, stop, exit, exit_reason, r_multiple, pnl, meta "
                    f"from trades where run_id=2 and date in ({PH})", c, params=DAYS)
    w["why"] = w.meta.fillna("").str.extract(r"why=(.*)$")[0].fillna("")
    w["st"] = w.meta.fillna("").str.extract(r"status=(\w+)")[0].fillna("")
    w["k"] = [kind(a, b) for a, b in zip(w.why, w.st)]
    w["net"] = net(w)
    live = pd.read_sql("select strategy, date, r_multiple, entry, stop, exit, exit_reason from trades where run_id=1 and "
                       f"date in ({PH})", c, params=DAYS)
    live["net"] = net(live) if len(live) else []
    sig["k"] = [kind(a, b) for a, b in zip(sig.reason, sig.status)]
    sk = sig[sig.status.isin(["skipped", "rejected"])]
    tab = {}
    for k, s in sk.groupby("k"):
        x = w[w.k == k]
        tab[k] = dict(n=len(s), unintended=unintended(k), priced=len(x), gross=round(float(x.r_multiple.sum()), 2),
                      net=round(float(x.net.sum()), 2), avg_net=round(float(x.net.mean()), 3) if len(x) else None,
                      by_day=s.day.value_counts().sort_index().to_dict(),
                      top=s.strategy.value_counts().head(3).to_dict())
    res["skips"][acct] = dict(sorted(tab.items(), key=lambda kv: -kv[1]["n"]))
    q = sk[sk.reason.isin(QUEUE)].copy()
    q["held_by"] = q["info"].map(lambda v: json.loads(v or "{}").get("held_by") or [])
    # lost to ANOTHER setup only (a setup blocked by its own earlier lot is a stacking cap, not a place in line)
    q["other"] = [bool(h) and s not in (h if isinstance(h, list) else [h]) for h, s in zip(q.held_by, q.strategy)]
    qo = q[q.other]
    rows = []
    for st, s in qo.groupby("strategy"):
        x = w[(w.strategy == st) & w.why.isin(QUEUE)].merge(s[["symbol", "day"]].drop_duplicates(), left_on=["symbol", "date"],
                                                             right_on=["symbol", "day"])
        lv = live[live.strategy == st]
        rows.append(dict(setup=st, lost=len(s), priced=len(x), net=round(float(x.net.sum()), 2),
                         avg_net=round(float(x.net.mean()), 3) if len(x) else None,
                         live_n=len(lv), live_avg_net=round(float(lv.net.mean()), 3) if len(lv) else None,
                         to=pd.Series([y for h in s.held_by for y in (h if isinstance(h, list) else [h])]).value_counts().head(2).to_dict()))
    res["queue"][acct] = sorted(rows, key=lambda r: -r["lost"])
    res["errors"][acct] = sk[sk.k.map(unintended)][["day", "ts", "symbol", "strategy", "k", "reason"]].to_dict("records")
    res.setdefault("live", {})[acct] = dict(n=len(live), avg_net=round(float(live.net.mean()), 3) if len(live) else None)
    # submitted entries with no trade row yet (HK-RECON): orders still 'submitted'
    o = pd.read_sql("select created_at, symbol, strategy, side from orders where status='submitted'", c)
    res["unbooked"][acct] = o.to_dict("records")

out = ROOT / "research/ops/blocked1029_results.json"
out.write_text(json.dumps(res, indent=1, default=str) + "\n")
for acct in ACCTS:
    print(f"\n=== {acct}  live trades {res['live'][acct]}  unbooked {len(res['unbooked'][acct])}")
    for d, v in res["coverage"][acct].items():
        print("  cov", d, v and {k: v[k] for k in ("polls", "first", "max_gap_min", "max_gap_at", "decision_polled",
                                                    "decision_missed", "handover", "fresh_at_decision_pct", "stale_polls")})
    nf = res["never_fired"][acct]
    print(f"  enabled {nf['enabled']}, never fired {len(nf['never'])}, load failures {nf['load_failures']}")
    for n, e in nf["never"].items():
        print("    NF", n, e["type"], e["min_adv"], e["window"], e["context"], len(e["days"]), "d", "life", e["lifetime_signals"],
              e["last_signal_day"], "p0", e["p_zero"], "life_sess", e["sessions_enabled"], "p0life", e["p_zero_life"], "" if e.get("module_exists") in (True, None) else f"MISSING {e.get('module')}")
    for k, v in res["skips"][acct].items():
        print(f"  {'UNINT ' if v['unintended'] else '      '}{k:40s} n {v['n']:4d} priced {v['priced']:4d} gross {v['gross']:+7.2f} "
              f"net {v['net']:+7.2f} avg {v['avg_net']} {v['by_day']} {v['top']}")
    for r in res["queue"][acct][:8]:
        print("  Q", r)
print("\nEducational only - not financial advice.")
