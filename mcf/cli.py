"""Command line entry point.

  mcf demo                         synthetic-data smoke run -> journal -> dashboard
  mcf download --symbols SPY,QQQ --start 2024-01-01 --end 2025-01-01
  mcf universe                     list tradable symbols (Alpaca assets)
  mcf backtest --start 2024-01-01 [--symbols ...] [--label name]
  mcf dashboard [--out reports/dashboard.html]
  mcf paper --watchlist SPY,QQQ,...  run one paper-trading session on Alpaca
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime

import pandas as pd

from .analytics.metrics import breakdowns, summarize
from .backtest.engine import Backtester
from .config import load_config, load_dotenv
from .data.store import BarStore
from .journal import Journal
from .strategies.setups import build_strategies


def _symbols(arg: str | None, store: BarStore) -> list[str]:
    if arg:
        return [s.strip().upper() for s in arg.split(",") if s.strip()]
    return store.symbols()


def _print_report(trades: pd.DataFrame) -> None:
    s = summarize(trades)
    print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()}, indent=2))
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
    _print_report(trades)
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
    _print_report(trades)
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
    from .data.alpaca_data import tradable_universe

    syms = tradable_universe()
    print(f"{len(syms)} tradable symbols")
    if args.out:
        open(args.out, "w").write("\n".join(syms))


def cmd_dashboard(args, cfg):
    from .dashboard.build import build

    print("dashboard:", build(cfg["data"]["journal_path"], args.out))


def cmd_paper(args, cfg):
    load_dotenv()
    from .execution.runner import PaperRunner

    store = BarStore(cfg["data"]["cache_dir"])
    watch = _symbols(args.watchlist, store)
    hist = store.load_many(watch, start=(pd.Timestamp.now() - pd.Timedelta(days=40)).date())
    PaperRunner(cfg, build_strategies(cfg), watch, hist).run_day()
    from .dashboard.build import build

    build(cfg["data"]["journal_path"], "reports/dashboard.html")


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

    pp = sub.add_parser("paper")
    pp.add_argument("--watchlist", help="comma-separated; default = all cached symbols")
    pp.set_defaults(fn=cmd_paper)

    args = p.parse_args(argv)
    args.fn(args, load_config(args.config))


if __name__ == "__main__":
    main()
