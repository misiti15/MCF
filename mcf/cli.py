"""Command line entry point.

  mcf demo                         synthetic-data smoke run -> journal -> dashboard
  mcf download --symbols SPY,QQQ --start 2024-01-01 --end 2025-01-01
  mcf universe                     list tradable symbols (Alpaca assets)
  mcf backtest --start 2024-01-01 [--symbols ...] [--label name]
  mcf dashboard [--out reports/dashboard.html]
  mcf discover                     weekly setup discovery -> reports/discovery (candidates only)
  mcf prep                         pre-market: universe + priors into the state dir
  mcf live [--dry-run]             one CI job of the live paper session (runs to close or job limit)
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime

import pandas as pd

from .analytics.metrics import breakdowns, gate_check, summarize
from .backtest.engine import Backtester
from .config import load_config, load_dotenv
from .data.store import BarStore
from .journal import Journal
from .strategies.setups import build_strategies


def _symbols(arg: str | None, store: BarStore) -> list[str]:
    if arg:
        return [s.strip().upper() for s in arg.split(",") if s.strip()]
    return store.symbols()


def _print_report(trades: pd.DataFrame, cfg: dict | None = None) -> None:
    s = summarize(trades)
    print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()}, indent=2))
    if cfg and not trades.empty:
        print("\n== promotion gates (per setup) ==")
        for name, g in trades.groupby("strategy"):
            ok, fails = gate_check(summarize(g), cfg.get("gates", {}))
            print(f"  {name:<22} {'PASS' if ok else 'FAIL: ' + '; '.join(fails)}")
    b = breakdowns(trades)
    for name in ("strategy", "time_of_day", "weekday", "exit_reason"):
        if name in b:
            print(f"\n== by {name} ==")
            print(b[name].round(3).to_string())


def cmd_backtest(args, cfg):
    store = BarStore(cfg["data"]["cache_dir"])
    data = store.load_many(_symbols(args.symbols, store), args.start, args.end)
    if not data:
        raise SystemExit("no cached data: run `mcf download` (or import CSVs) first")
    strategies = build_strategies(cfg)
    if args.only:
        keep = set(args.only.split(","))
        strategies = [s for s in strategies if s.name in keep]
    print(f"backtesting {len(data)} symbols with {[s.name for s in strategies]}")
    trades = Backtester(strategies, cfg).run(data, progress=True)
    _print_report(trades, cfg)
    j = Journal(cfg["data"]["journal_path"])
    run = j.new_run("backtest", args.label or f"bt {args.start}..{args.end or 'now'}", cfg)
    j.add_trades(run, trades)
    j.set_summary(run, summarize(trades))
    print(f"\nsaved as run {run}")


def cmd_demo(args, cfg):
    from .data.synthetic import make_universe

    syms = ["SPY", "QQQ", "IWM", "DIA"] + [f"SYN{i:02d}" for i in range(36)]
    data = make_universe(syms, days=args.days)
    cfg["universe"]["min_avg_dollar_volume"] = 0
    cfg["account"]["max_daily_loss_r"] = 1e9  # random data trips the daily stop; lift it so every setup shows
    trades = Backtester(build_strategies(cfg), cfg).run(data)
    _print_report(trades, cfg)
    j = Journal(cfg["data"]["journal_path"])
    run = j.new_run("backtest", "DEMO synthetic data (not real results)", cfg)
    j.add_trades(run, trades)
    from .dashboard.build import build

    print("dashboard:", build(cfg["data"]["journal_path"], args.out))


def cmd_download(args, cfg):
    load_dotenv()
    from .data.alpaca_data import download_to_store

    store = BarStore(cfg["data"]["cache_dir"])
    syms = _symbols(args.symbols, store)
    n = download_to_store(syms, datetime.fromisoformat(args.start), datetime.fromisoformat(args.end), store,
                          feed=args.feed or cfg["data"]["feed"])
    print(f"saved {n} symbols to {store.dir}")


def cmd_universe(args, cfg):
    load_dotenv()
    from .data.universe import build_universe

    df = build_universe(cfg, args.out or "data/universe.csv")
    print(f"{len(df)} symbols ({df.tier.value_counts().to_dict()}); ADV ${df.adv.min() / 1e6:.0f}M..${df.adv.max() / 1e9:.1f}B; "
          f"shortable+ETB {int((df.shortable & df.easy_to_borrow).sum())}")


def cmd_dashboard(args, cfg):
    from .dashboard.build import build

    print("dashboard:", build(cfg["data"]["journal_path"], args.out))


def cmd_brief(args, cfg):
    load_dotenv()
    from .report.brief import build_brief, send_email

    subject, text, html_body = build_brief(Journal(cfg["data"]["journal_path"]), args.day, args.kind,
                                           cfg.get("report", {}).get("dashboard_url"))
    print(text)
    if args.send:
        send_email(subject, text, html_body, os.environ.get("MCF_EMAIL_TO") or cfg["report"]["email_to"])
        print("sent")


def _state_cfg(cfg, state_dir):
    cfg["data"]["journal_path"] = os.path.join(state_dir, "journal.db")
    return cfg


def cmd_prep(args, cfg):
    load_dotenv()
    from .execution.session import NY, prep

    day = pd.Timestamp(args.day) if args.day else pd.Timestamp.now(tz=NY)
    prep(cfg, args.state_dir, day.date())


def cmd_live(args, cfg):
    """One CI slot of the live paper session (see mcf/execution/session.py)."""
    load_dotenv()
    from .execution.runner import PaperRunner
    from .execution.session import NY, Publisher, job_deadline, prep

    now = pd.Timestamp.now(tz=NY)
    until = job_deadline(now, cfg.get("live", {}))
    if until is None and not args.force:
        print(f"{now:%a %H:%M} ET is outside the trading-job window: nothing to do")
        return
    slot = f"job {now:%H:%M}"
    _state_cfg(cfg, args.state_dir)
    pub = Publisher(args.state_dir, enabled=not args.no_push)
    priors = prep(cfg, args.state_dir, now.date())
    status = os.path.join(args.state_dir, "status.json")
    last = {"journal": None}

    def on_status(st):
        paths = ["status.json"]
        ts = pd.Timestamp.now(tz=NY)
        if last["journal"] is None or ts - last["journal"] >= pd.Timedelta(minutes=30) or st["phase"] in ("closed", "handover"):
            paths.append("journal.db")
            last["journal"] = ts
        pub.push(paths, f"status {st['asof_et']} ({st['phase']})")

    print(f"{slot}: {len(priors)} symbols, until {until or 'close'}, dry_run={args.dry_run}")
    PaperRunner(cfg, build_strategies(cfg), priors, dry_run=args.dry_run, status_path=status,
                on_status=on_status).run(until=until)
    pub.push(["status.json", "journal.db", "universe.csv"], f"slot {slot} done {now.date()}")


def cmd_discover(args, cfg):
    load_dotenv()
    from .data.universe import load_universe
    from .discovery import run_discovery

    if args.max_symbols:
        cfg.setdefault("discovery", {})["max_symbols"] = args.max_symbols
    uni = load_universe(args.universe)
    p = run_discovery(cfg, uni, args.out)
    print(f"tried {p['rules_tried']:,} rules; {p['passed_train']} passed training; {p['replicated']} replicated -> {args.out}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="mcf")
    p.add_argument("--config", help="extra YAML merged over config/default.yaml")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("backtest")
    b.add_argument("--start", required=True)
    b.add_argument("--end")
    b.add_argument("--symbols")
    b.add_argument("--only", help="comma-separated strategy names")
    b.add_argument("--label")
    b.set_defaults(fn=cmd_backtest)

    d = sub.add_parser("demo")
    d.add_argument("--days", type=int, default=80)
    d.add_argument("--out", default="reports/dashboard.html")
    d.set_defaults(fn=cmd_demo)

    dl = sub.add_parser("download")
    dl.add_argument("--symbols", required=True)
    dl.add_argument("--start", required=True)
    dl.add_argument("--end", required=True)
    dl.add_argument("--feed", choices=["iex", "sip", "delayed_sip"])
    dl.set_defaults(fn=cmd_download)

    u = sub.add_parser("universe")
    u.add_argument("--out")
    u.set_defaults(fn=cmd_universe)

    db = sub.add_parser("dashboard")
    db.add_argument("--out", default="reports/dashboard.html")
    db.set_defaults(fn=cmd_dashboard)

    br = sub.add_parser("brief", help="daily brief (prints; --send emails it)")
    br.add_argument("--day")
    br.add_argument("--kind", default="paper", choices=["paper", "backtest", "live", "reference"])
    br.add_argument("--send", action="store_true")
    br.set_defaults(fn=cmd_brief)

    pr = sub.add_parser("prep", help="pre-market: build universe + priors into the state dir")
    pr.add_argument("--state-dir", default="state")
    pr.add_argument("--day")
    pr.set_defaults(fn=cmd_prep)

    dc = sub.add_parser("discover", help="weekly layered-rule mining (candidates only, never auto-traded)")
    dc.add_argument("--universe", default="data/universe.csv")
    dc.add_argument("--out", default="reports/discovery")
    dc.add_argument("--max-symbols", type=int)
    dc.set_defaults(fn=cmd_discover)

    lv = sub.add_parser("live", help="run one slot of the live paper session")
    lv.add_argument("--state-dir", default="state")
    lv.add_argument("--force", action="store_true", help="run even outside the job window")
    lv.add_argument("--dry-run", action="store_true", help="scan and journal signals, place no orders")
    lv.add_argument("--no-push", action="store_true")
    lv.set_defaults(fn=cmd_live)

    args = p.parse_args(argv)
    args.fn(args, load_config(args.config))


if __name__ == "__main__":
    main()
