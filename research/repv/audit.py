"""REPV step 1: live rep-velocity audit per setup and account (research only, no config change).

Reads each account's live journal (origin/<branch>:journal.db, run_id=1 signals + trades, run_id=2 what-if) and the
frozen per-session setup snapshots (origin/<branch>:setups/<day>.json) for the sessions each setup was live.

    python research/repv/audit.py            # writes research/repv/audit_by_account.csv, audit_by_setup.csv,
                                             #        audit_reasons_by_account.csv
Educational only - not financial advice."""
from __future__ import annotations

import io
import json
import sqlite3
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
LAST_DAY = "2026-11-10"          # complete sessions only (the audit was run during the 11-11 session)
ACCOUNTS = {"primary": ("mcf-data", "Primary"), "testing": ("mcf-data-testing", "On Deck"),
            "testing2": ("mcf-data-testing2", "Testing A"), "explore1": ("mcf-data-explore1", "Testing B"),
            "livelab": ("mcf-data-livelab", "Testing C"), "gen": ("mcf-data-gen", "Setup Generator"),
            "graveyard": ("mcf-data-graveyard", "Graveyard")}
REASONS = ["taken", "pool_universe", "cost_filter", "borrow", "split_gate", "twin", "setup_cap", "slots",
           "buying_power", "spread_crosscheck", "time_window", "one_per_symbol", "earnings", "latch", "account_halt",
           "other"]


def bucket(status: str, reason: str | None) -> str:
    s, r = str(status or ""), str(reason or "").lower()
    if s in ("submitted", "dry_run"):
        return "taken"
    if s == "shadow" or r.startswith("before "):
        return "time_window"
    if s == "rejected":
        return "buying_power" if "insufficient buying power" in r else "other"
    if r.startswith("cost filter"):
        return "cost_filter"
    if "shortable" in r or "shorts disabled" in r:
        return "borrow"
    if r.startswith("split-tape"):
        return "split_gate"
    if r.startswith("twin held"):
        return "twin"
    if r.startswith("max positions for this setup"):
        return "setup_cap"
    if r.startswith("max concurrent positions") or r.startswith("max trades/day"):
        return "slots"
    if r.startswith(("spread", "crosscheck", "no quote", "no two-sided", "size <")):
        return "spread_crosscheck"
    if r.startswith(("already in symbol", "opposite side held", "lot cap")):
        return "one_per_symbol"
    if r.startswith("setup daily loss limit"):
        return "latch"
    if r == "halted" or r.startswith("daily loss limit"):
        return "account_halt"
    return "other"


def git(*a, text=True):
    r = subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=text)
    return r.stdout if r.returncode == 0 else None


def live_sessions(branch: str) -> dict[str, set[str]]:
    """setup -> set of session dates it was enabled (frozen snapshot)."""
    out = defaultdict(set)
    names = (git("ls-tree", "--name-only", f"origin/{branch}", "setups/") or "").split()
    for p in names:
        d = Path(p).stem
        if len(d) != 10:
            continue
        try:
            snap = json.loads(git("show", f"origin/{branch}:{p}") or "{}")
        except ValueError:
            continue
        for k, v in (snap.get("strategies") or {}).items():
            if isinstance(v, dict) and v.get("enabled", True) is not False:
                out[k].add(d)
    return out


def load(branch: str):
    raw = git("show", f"origin/{branch}:journal.db", text=False)
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        f.write(raw)
    c = sqlite3.connect(f.name)
    sig = pd.read_sql("select run_id, day, symbol, strategy, side, status, reason from signals", c)
    tr = pd.read_sql("select run_id, date, symbol, strategy, side, entry, stop, shares, pnl, pnl_adj, r_multiple, meta from trades", c)
    c.close()
    Path(f.name).unlink()
    sig, tr = sig[sig.day <= LAST_DAY], tr[tr.date <= LAST_DAY].copy()
    risk = (tr.entry - tr.stop).abs() * tr.shares.abs()
    tr["r"] = tr.pnl_adj.fillna(tr.pnl) / risk.where(risk > 0)
    wi = tr.run_id == 2                       # what-if rows: shares 0, simulated R with backtest costs in r_multiple
    tr.loc[wi, "r"] = tr.loc[wi, "r_multiple"]
    st = tr.meta.fillna("").str.extract(r"status=([^;]*)")[0]
    why = tr.meta.fillna("").str.extract(r"why=(.*)$")[0]
    tr["bucket"] = [bucket(a, b) if w else None for a, b, w in zip(st, why, wi)]
    return sig, tr


def main():
    rows, acct_rows, daily, wif = [], [], [], []
    for acct, (branch, tag) in ACCOUNTS.items():
        sig, tr = load(branch)
        live = live_sessions(branch)
        s1 = sig[sig.run_id == 1].copy()
        s1["bucket"] = [bucket(a, b) for a, b in zip(s1.status, s1.reason)]
        t1, t2 = tr[tr.run_id == 1], tr[tr.run_id == 2]
        sess_all = sorted(set(s1.day) | set(t1.date))
        # account-level reason shares
        cnt = s1.bucket.value_counts()
        acct_rows.append({"account": acct, "tag": tag, "sessions": len(sess_all), "first": sess_all[0] if sess_all else None,
                          "last": sess_all[-1] if sess_all else None, "signals": len(s1),
                          **{b: int(cnt.get(b, 0)) for b in REASONS}})
        for b, g in t2.groupby("bucket"):
            wif.append({"account": acct, "tag": tag, "bucket": b, "whatif_trades": len(g),
                        "whatif_avg_r": round(float(g.r.mean()), 3), "whatif_total_r": round(float(g.r.sum()), 1)})
        # what-if R of lost signals, per (setup, symbol, day) - approximate join by setup+bucket share
        wi = t2.groupby("strategy").r.agg(["count", "mean"]).rename(columns={"count": "whatif_n", "mean": "whatif_avg_r"})
        sc = s1.groupby(["strategy", "day"]).size()
        tc = t1.groupby(["strategy", "date"]).size()
        for st, days in live.items():
            for d in sorted(days & set(sess_all)):
                daily.append({"account": acct, "setup": st, "day": d, "signals": int(sc.get((st, d), 0)),
                              "trades": int(tc.get((st, d), 0))})
        setups = sorted(set(s1.strategy) | set(t1.strategy) | {k for k, v in live.items() if v & set(sess_all)})
        for st in setups:
            g, t = s1[s1.strategy == st], t1[t1.strategy == st]
            lv = live.get(st, set()) & set(sess_all)
            n_live = len(lv) if lv else len(set(g.day) | set(t.date))
            if n_live == 0:
                continue
            b = g.bucket.value_counts()
            rr = t.r.dropna()
            by_day = t.groupby("date").r.sum()
            best = float(by_day.max()) if len(by_day) else 0.0
            rows.append({"account": acct, "tag": tag, "setup": st, "live_sessions": n_live,
                         "first": min(lv) if lv else None, "last": max(lv) if lv else None,
                         "signals": len(g), "entries": int(b.get("taken", 0)), "trades": len(t),
                         "traded_sessions": int(t.date.nunique()),
                         "signals_per_session": round(len(g) / n_live, 2),
                         "trades_per_session": round(len(t) / n_live, 2),
                         "traded_sessions_per_week": round(t.date.nunique() / n_live * 5, 2),
                         "total_r": round(float(rr.sum()), 2), "avg_r": round(float(rr.mean()), 3) if len(rr) else None,
                         "avg_r_wo_best_day": round((float(rr.sum()) - best) / max(1, len(t) - int((t.date == by_day.idxmax()).sum())), 3)
                         if len(by_day) > 1 else None,
                         "best_day_share": round(best / float(rr.sum()), 2) if len(rr) and rr.sum() > 0 else None,
                         "whatif_n": int(wi.whatif_n.get(st, 0)) if st in wi.index else 0,
                         "whatif_avg_r": round(float(wi.whatif_avg_r.get(st)), 3) if st in wi.index and pd.notna(wi.whatif_avg_r.get(st)) else None,
                         **{f"lost_{k}": int(b.get(k, 0)) for k in REASONS if k != "taken"}})
    A = pd.DataFrame(acct_rows)
    S = pd.DataFrame(rows)
    A.to_csv(OUT / "audit_reasons_by_account.csv", index=False)
    pd.DataFrame(wif).to_csv(OUT / "audit_whatif_by_reason.csv", index=False)
    pd.DataFrame(daily).to_csv(OUT / "live_daily.csv", index=False)
    S.to_csv(OUT / "audit_by_account.csv", index=False)
    # merged across accounts per setup
    num = [c for c in S.columns if c.startswith("lost_")] + ["signals", "entries", "trades", "whatif_n"]
    M = S.groupby("setup")[num + ["live_sessions"]].sum()
    M["accounts"] = S.groupby("setup").account.apply(lambda x: "+".join(sorted(set(x))))
    print(A.to_string())
    return A, S


if __name__ == "__main__":
    main()
