"""Blocked-signal audit (owner 2026-10-22: "We don't want setups sitting unused because of hiccups"), first run 2026-10-26,
covering the sessions 2026-10-22, 2026-10-23 and 2026-10-26 in all five intraday accounts.

    python research/ops/blocked1026_audit.py <scratch>
      <scratch>/j/<branch>/journal.db            git show origin/<branch>:journal.db
      <scratch>/polls/<branch>/<day>/*.jsonl.gz  git show origin/<branch>:polls/<day>/...

Reads only. Writes research/ops/blocked1026_results.json and prints the tables of research/ops/blocked_audit.md.
1) poll coverage: per poll log; a lab decision bar (count c, c % 5 == 0, c in 20..330) is evaluated only when a poll sees
   the symbol at exactly c bars (pollspeed1022_missed.missed counts the gaps between polls); the decision bars before the
   account's first poll (late start) are counted on top. Coverage = 1 - missed / (63 x symbols with bars).
2) never fired: setups enabled in the account's frozen setups/<day>.json with zero journaled signals (run 1, any status).
3)-5) skips by reason, priced with the journal's what-if run (run 2) gross and after the production cost model
   (config/default.yaml costs: $0.01/sh + 1 bps per side, target exits without slippage, +$0.02/sh on stops).
Educational only - not financial advice."""
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/ops"))
from mcf.execution.runner import read_poll_log            # noqa: E402
from pollspeed1022_missed import missed, LO, HI           # noqa: E402

S = Path(sys.argv[1])
DAYS = ["2026-10-22", "2026-10-23", "2026-10-26"]
ACCTS = {"Primary": "mcf-data", "Testing 1": "mcf-data-testing", "Testing 2": "mcf-data-testing2",
         "Graveyard": "mcf-data-graveyard", "Generated": "mcf-data-gen"}
INTENDED = ("setup daily loss limit", "spread", "twin held", "lot cap", "max positions for this setup",
            "not shortable/ETB", "split-tape short gate", "account daily stop", "daily loss", "price below minimum",
            "size < 1 share after liquidity cap", "opposite side held", "already in symbol", "same setup, same moment",
            "shorts disabled")
QUEUE = ("twin held", "lot cap", "opposite side held", "already in symbol", "max positions for this setup")
DEC = [c for c in range(LO, HI + 1) if c % 5 == 0]


def kind(reason: str, status: str) -> str:
    if status == "rejected":
        return "broker reject"
    r = reason or ""
    if r.startswith("crosscheck"):
        return "crosscheck"
    if r.startswith("missed: triggered"):
        return "missed: triggered (late start)"
    if r.startswith("no quote") or r.startswith("no two-sided"):
        return "no quote"
    if r.startswith("spread"):
        return "spread filter" if "bps" in r else "spread vs stop"
    return r


def unintended(k: str) -> bool:
    return k in ("broker reject", "crosscheck", "missed: triggered (late start)", "no quote")


def net(w: pd.DataFrame) -> pd.Series:
    R = (w.entry - w.stop).abs()
    cps = (0.01 + w.entry * 1e-4) + np.where(w.exit_reason == "target", 0.0, 0.01 + w.exit * 1e-4) \
        + np.where(w.exit_reason == "stop", 0.02, 0.0)
    return w.r_multiple - np.where(R > 0, cps / R, 0.0)


res: dict = {"days": DAYS, "coverage": {}, "never_fired": {}, "skips": {}, "queue": {}, "errors": {}}
for acct, br in ACCTS.items():
    # ---- 1) poll coverage
    cov = {}
    for d in DAYS:
        recs = read_poll_log(str(S / "polls" / br), d)
        if not recs:
            cov[d] = None
            continue
        t = pd.to_datetime([f"{d} {r['t']}" for r in recs])
        g = np.diff(t.values).astype("timedelta64[s]").astype(float) / 60
        m = missed(recs)
        first_exp, got = recs[0]["exp"], m["symbols_with_bars"]
        late = [c for c in DEC if c < first_exp]           # decision bars before the first poll (no job running)
        tot = len(DEC) * got
        own = m["symbol_decisions_missed"]
        stale = sum(1 for r in recs if r.get("stale"))
        i = int(g.argmax()) if len(g) else 0
        cov[d] = dict(polls=len(recs), first=recs[0]["t"], last=recs[-1]["t"], max_gap_min=round(float(g.max()), 1) if len(g) else None,
                      max_gap_at=recs[i]["t"], gaps_over_3=int((g > 3).sum()), gaps_over_70s=int((g > 70 / 60).sum()),
                      stale_polls=stale, late_start_bars=len(late), late_start_missed=len(late) * got,
                      gap_missed=own, total=tot,
                      own_window_pct=round(100 * (1 - own / max(1, tot - len(late) * got)), 1),
                      coverage_pct=round(100 * (1 - (own + len(late) * got) / max(1, tot)), 1))
    res["coverage"][acct] = cov

    # ---- 2) never fired
    c = sqlite3.connect(S / "j" / br / "journal.db")
    sig = pd.read_sql("select day, ts, symbol, strategy, side, status, reason, info from signals where run_id=1 and day in (?,?,?)",
                      c, params=DAYS)
    fired = sig.groupby("strategy").size().to_dict()
    enabled: dict[str, dict] = {}
    for d in DAYS:
        try:
            fz = json.loads(subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:setups/{d}.json"],
                                           capture_output=True, text=True, check=True).stdout)
        except Exception:
            continue
        for name, s in fz.get("strategies", {}).items():
            if isinstance(s, dict) and s.get("enabled", True) and s.get("enabled") is not False:
                e = enabled.setdefault(name, {"days": [], "type": s.get("type", "rule"), "min_adv": s.get("min_adv"),
                                              "window": s.get("window"), "context": s.get("context"),
                                              "module": s.get("module"), "prefilter": s.get("prefilter")})
                e["days"].append(d)
    nf = {n: e for n, e in enabled.items() if fired.get(n, 0) == 0}
    for n, e in nf.items():
        e["module_exists"] = (ROOT / e["module"]).exists() if e.get("module") else None
    res["never_fired"][acct] = {"enabled": len(enabled), "fired": len(enabled) - len(nf), "never": nf}

    # ---- 3)-5) skips priced with the what-if run
    w = pd.read_sql("select symbol, strategy, side, date, signal_time, entry, stop, exit, exit_reason, r_multiple, pnl, meta "
                    "from trades where run_id=2 and date in (?,?,?)", c, params=DAYS)
    w["why"] = w.meta.fillna("").str.extract(r"why=(.*)$")[0].fillna("")
    w["st"] = w.meta.fillna("").str.extract(r"status=(\w+)")[0].fillna("")
    w["k"] = [kind(a, b) for a, b in zip(w.why, w.st)]
    w["net"] = net(w)
    live = pd.read_sql("select strategy, date, r_multiple, entry, stop, exit, exit_reason from trades where run_id=1 and date in (?,?,?)",
                       c, params=DAYS)
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
    # place in line: a setup lost the symbol to another setup of this account (held_by not itself)
    q = sk[sk.reason.isin(QUEUE)].copy()
    q["held_by"] = q["info"].map(lambda v: json.loads(v or "{}").get("held_by") or [])
    # lost to ANOTHER setup only: the symbol was held by other setups and not by this one (a setup blocked by its own
    # earlier lot is a stacking cap, not a place in line)
    q["other"] = [bool(h) and s not in (h if isinstance(h, list) else [h]) for h, s in zip(q.held_by, q.strategy)]
    qo = q[q.other]
    wq = w[w.why.isin(QUEUE)]
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

out = ROOT / "research/ops/blocked1026_results.json"
out.write_text(json.dumps(res, indent=1, default=str) + "\n")
for acct in ACCTS:
    print(f"\n=== {acct}  live trades {res['live'][acct]}")
    for d, v in res["coverage"][acct].items():
        print("  cov", d, v and {k: v[k] for k in ("polls", "first", "max_gap_min", "max_gap_at", "gaps_over_3", "stale_polls",
                                                    "own_window_pct", "coverage_pct", "late_start_bars")})
    nf = res["never_fired"][acct]
    print(f"  enabled {nf['enabled']}, never fired {len(nf['never'])}")
    for n, e in nf["never"].items():
        print("    NF", n, e["type"], e["min_adv"], e["window"], e["context"], len(e["days"]), "d", "mod" if e.get("module_exists") else e.get("module"))
    for k, v in res["skips"][acct].items():
        print(f"  {'UNINT ' if v['unintended'] else '      '}{k:34s} n {v['n']:4d} priced {v['priced']:4d} gross {v['gross']:+7.2f} net {v['net']:+7.2f} avg {v['avg_net']} {v['by_day']}")
    for r in res["queue"][acct][:8]:
        print("  Q", r)
print("\nEducational only - not financial advice.")
