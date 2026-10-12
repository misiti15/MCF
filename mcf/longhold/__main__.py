"""CLI: python -m mcf.longhold run|init|mark|report|status|plan [--state-dir state] [--dry-run] [--stage plan|submit|all]

Live (paper orders) only when LONGHOLD_LIVE=true AND ALPACA_TRADE_API_KEY/SECRET are set (the workflow maps the
ALPACA_LONGHOLD_* secrets onto them) AND --dry-run is not given. Otherwise dry run: plans and marks, no orders, and
only the data keys (ALPACA_API_KEY/SECRET, SIP) are used. Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime

from .runner import ET, Runner


def is_live(args, env=None, state_dir=None) -> bool:
    """Paper orders only with the long-hold keys present, no --dry-run, and either LONGHOLD_LIVE=true or the book
    already went live (longhold/LIVE marker on the state branch, written at the first paper submission, so a
    scheduled mark never treats a live book as a dry one)."""
    env = os.environ if env is None else env
    from pathlib import Path

    marker = state_dir is not None and (Path(state_dir) / "longhold" / "LIVE").exists()
    return (not args.dry_run and bool(env.get("ALPACA_TRADE_API_KEY"))
            and (env.get("LONGHOLD_LIVE", "false").strip().lower() == "true" or marker))


def make_runner(args) -> Runner:
    from .broker import AlpacaLongholdBroker, CalendarOnly, check_key_separation
    from .data import SipDaily

    live = is_live(args, state_dir=args.state_dir)
    if os.environ.get("ALPACA_TRADE_API_KEY"):
        check_key_separation()                     # refuse to start on a shared account, dry or live
    broker = AlpacaLongholdBroker() if live else None
    now = datetime.fromisoformat(args.now).replace(tzinfo=ET) if args.now else None
    return Runner(args.state_dir, SipDaily(), broker=broker, calendar=broker or CalendarOnly(), now=now, live=live)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m mcf.longhold", description="Long-hold (S6) paper runner. "
                                 "Educational only - not financial advice.")
    ap.add_argument("command", choices=["init", "mark", "run", "status", "plan", "report"])
    ap.add_argument("--state-dir", default="state")
    ap.add_argument("--dry-run", action="store_true", help="never place orders")
    ap.add_argument("--stage", choices=["plan", "submit", "all"], default="all")
    ap.add_argument("--phase", choices=["morning", "recon", "evening"], help="override the clock-derived phase")
    ap.add_argument("--now", help="ET wall clock override, e.g. 2026-10-12T15:00 (testing)")
    args = ap.parse_args(argv)
    if args.command == "status":
        from pathlib import Path

        p = Path(args.state_dir) / "longhold" / "status.json"
        print(p.read_text() if p.exists() else "no status yet")
        return 0
    r = make_runner(args)
    print(f"long-hold runner: mode={r.mode} today={r.today} (Educational only - not financial advice)")
    if args.command == "init":
        plan = r.init(args.stage)
        print(json.dumps({k: plan.get(k) for k in ("signal_day", "exec_day", "status", "skip_reason")}, default=str))
        for o in plan["orders"]:
            print(f"  {o['side']:4} {o['qty']:>6} {o['symbol']:6} ~${o['notional']:>10,.2f}  {o['client_order_id']}")
        return 0 if plan["status"] in ("planned", "submitted") else 2
    if args.command == "plan":
        sd = r.last_signal_day(r.today if r.now.hour < 18 else date.fromordinal(r.today.toordinal() + 1))
        sig, bad, _ = r.signal(sd)
        print(f"signal day {sd}: " + (f"SKIP ({bad})" if bad else f"{len(sig['eligible'])} eligible"))
        if sig:
            for s, w in sorted(sig["targets"].items()):
                print(f"  {s:6} {w:.3f}")
        return 0
    if args.command == "mark":
        r.mark()
        return 0
    if args.command == "report":
        print("weekly report:", r.report())
        return 0
    if args.command == "run":
        print(json.dumps(r.run(args.stage, args.phase), default=str))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
