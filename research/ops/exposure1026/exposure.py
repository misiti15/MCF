"""Exposure / trade-count notes 2026-10-26 (read only). Educational only — not financial advice.

Reads each account's journal.db, setups/<day>.json and status.json from its state branch (git show) and prints per-account
per-day counts, cap losses, peak open positions, peak gross exposure, and per-setup pace to 30 live trades.
Usage: python research/ops/exposure1026/exposure.py  (writes research/ops/exposure1026/results.json)
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from mcf.report.playing_time import classify  # noqa: E402

ACCOUNTS = {"Primary": ("mcf-data", "config/default.yaml"), "Testing 1": ("mcf-data-testing", "config/account_testing.yaml"),
            "Testing 2": ("mcf-data-testing2", "config/account_testing2.yaml"),
            "Graveyard": ("mcf-data-graveyard", "config/account_graveyard.yaml"), "Gen": ("mcf-data-gen", "config/account_gen.yaml")}
DAYS = ["2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-26"]
CAP_BUCKETS = ("slots_full", "setup_cap", "trades_cap", "daily_loss")
LOT = ("lot cap",)


def show(branch: str, path: str) -> bytes | None:
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{branch}:{path}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def sweep(tr: pd.DataFrame) -> tuple[int, float, str]:
    ev = []
    for a, b, n in zip(pd.to_datetime(tr.entry_time, utc=True, errors="coerce"),
                       pd.to_datetime(tr.exit_time, utc=True, errors="coerce"), tr.notional):
        if pd.notna(a):
            ev += [(a, 1, n), (b if pd.notna(b) else a, -1, -n)]
    cur = peak = 0
    g = gpk = 0.0
    tpk = ""
    for t, d, n in sorted(ev, key=lambda x: (x[0], x[1])):
        cur += d
        g += n
        peak = max(peak, cur)
        if g > gpk:
            gpk, tpk = g, t.tz_convert("America/New_York").strftime("%H:%M")
    return peak, gpk, tpk


def main() -> None:
    import yaml
    out = {}
    for acct, (br, cfgp) in ACCOUNTS.items():
        import os
        from mcf.config import load_config
        os.environ["MCF_ACCOUNT"] = {"Primary": "primary", "Testing 1": "testing", "Testing 2": "testing2",
                                     "Graveyard": "graveyard", "Gen": "gen"}[acct]
        cfg = load_config()
        risk = cfg["account"]
        caps = {k: risk.get(k) for k in ("slots", "max_concurrent_positions", "max_positions_per_strategy",
                                         "buying_power_multiple", "max_trades_per_day", "max_setup_daily_loss_r",
                                         "max_daily_loss_r")}
        caps["max_lots_per_symbol"] = cfg["live"].get("max_lots_per_symbol")
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            f.write(show(br, "journal.db"))
            f.flush()
            c = sqlite3.connect(f.name)
            pid = c.execute("select id from runs where kind='paper' order by id limit 1").fetchone()[0]
            sig = pd.read_sql("select day, ts, strategy, status, reason from signals where run_id=?", c, params=(pid,))
            tr = pd.read_sql("select date, strategy, entry_time, exit_time, entry, shares, r_multiple, pnl_adj from trades "
                             "where run_id=?", c, params=(pid,))
        status = json.loads(show(br, "status.json") or b"{}")
        tr["notional"] = (tr.entry.fillna(0) * tr.shares.fillna(0)).abs()
        sig["bucket"] = [classify(s, r) for s, r in zip(sig.status, sig.reason)]
        sig["lot"] = sig.reason.fillna("").str.lower().str.startswith(LOT)
        days = {}
        for d in DAYS:
            s, t = sig[sig.day == d], tr[tr.date == d]
            b = Counter(s.bucket)
            peak, gpk, tpk = sweep(t)
            first = pd.to_datetime(s.ts, utc=True, errors="coerce").min() if len(s) else None
            enabled = []
            snap = show(br, f"setups/{d}.json")
            if snap:
                st = json.loads(snap).get("strategies", {})
                enabled = [k for k, v in st.items() if isinstance(v, dict) and v.get("enabled")]
            days[d] = {"signals": len(s), "trades": len(t), "submitted": int(b.get("taken", 0)),
                       "lost_caps": {k: int(b.get(k, 0)) for k in CAP_BUCKETS if b.get(k)},
                       "lot_cap": int(s.lot.sum()),
                       "setup_daily_loss": int(s.reason.fillna("").str.startswith("setup daily loss").sum()),
                       "split_gate": int(b.get("split_gate", 0)), "held_by_other": int(b.get("held_by_other", 0)),
                       "borrow": int(b.get("borrow", 0)), "realism": int(b.get("realism", 0)),
                       "shadow": int(b.get("window", 0)), "rejected": int(b.get("rejected", 0)),
                       "other": int(b.get("other", 0)) + int(b.get("price", 0)) + int(b.get("missed_trigger", 0)),
                       "peak_open": peak, "peak_gross": round(gpk), "peak_gross_at": tpk,
                       "first_signal_et": first.tz_convert("America/New_York").strftime("%H:%M") if first is not None and pd.notna(first) else None,
                       "setups_enabled": len(enabled), "enabled": enabled}
        # per setup, live trades so far (all sessions in this account), setups enabled today
        en = days["2026-10-26"]["enabled"]
        alltr = tr.groupby("strategy").size()
        sess = tr.groupby("strategy").date.nunique()
        last5 = tr[tr.date.isin(DAYS)]
        setups = {}
        for k in en:
            n = int(alltr.get(k, 0))
            ns = int(sess.get(k, 0))
            # sessions the setup was enabled in this account in the last 5 days
            en5 = sum(1 for d in DAYS if k in days[d]["enabled"])
            n5 = int((last5.strategy == k).sum())
            pace = n5 / en5 if en5 else 0.0
            setups[k] = {"trades": n, "trade_days": ns, "enabled_last5": en5, "trades_last5": n5,
                         "per_session": round(pace, 2),
                         "sessions_to_30": (0 if n >= 30 else (round((30 - n) / pace, 1) if pace > 0 else None))}
        for d in days.values():
            d.pop("enabled")
        out[acct] = {"branch": br, "caps": caps, "equity": (status.get("account") or {}).get("equity"),
                     "days": days, "setups": setups}
    p = Path(__file__).with_name("results.json")
    p.write_text(json.dumps(out, indent=1))
    for a, v in out.items():
        print("==", a, v["caps"], "equity", v["equity"])
        for d, x in v["days"].items():
            print(" ", d, {k: x[k] for k in x})
        s = v["setups"]
        lo = sorted(s.items(), key=lambda kv: (kv[1]["sessions_to_30"] is None, kv[1]["sessions_to_30"] or 0), reverse=True)
        print("  setups", len(s), "0-2 trades:", sum(1 for x in s.values() if x["trades"] <= 2))


if __name__ == "__main__":
    main()
