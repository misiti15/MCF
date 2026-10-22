"""Replay recorded sessions through the real live runner (see mcf/replay/harness.py).

    python -m mcf.replay prep  --dates 2026-08-10..2026-10-21 [--fetch]       store + priors for those sessions
    python -m mcf.replay run   --account testing2 --dates 2026-09-01..2026-10-07 [--setup NAME --module PATH [--alone]]
                               [--as-live] [--fills costs|paper] [--limit-fill through|touch] [--jobs N] [--exact]
                               [--label NAME]
    python -m mcf.replay export [--runs data/replay/runs]                    docs/live/replay.json + pipeline.json

Outputs per session: data/replay/runs/<label>/<account>/<date>/{signals,trades,whatif,summary}.csv.gz + stats.json;
per run: summary.csv (per setup) and run.json. Educational only - not financial advice."""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import timedelta
from pathlib import Path

import pandas as pd

from . import store

RUNS = store.STORE / "runs"


def parse_dates(spec: str) -> list:
    out = []
    for part in spec.split(","):
        if ".." in part:
            a, b = part.split("..")
            out += store.sessions(a, b)
        else:
            out.append(pd.Timestamp(part).date())
    have = set(store.available_days())
    return [d for d in out if d in have]


def _day(job: dict) -> list[dict]:
    """One session for one or more accounts in one worker (the accounts share the session's feature frames)."""
    return [_one({**job, "account": a}) for a in job["account"].split(",")]


def _one(job: dict) -> dict:
    """One session and account: config -> inputs -> replay -> files."""
    from . import harness

    d = pd.Timestamp(job["day"]).date()
    out = Path(job["out"]) / job["account"] / str(d)
    if (out / "stats.json").exists() and not job.get("force"):
        return json.loads((out / "stats.json").read_text())
    try:
        cfg = harness.account_config(job["account"], d, as_live=job["as_live"])
        if job.get("setup"):
            block = json.loads(job["block"]) if job.get("block") else None
            cfg = harness.add_setup(cfg, job["setup"], job.get("module"), alone=job.get("alone", False), block=block)
        branch = harness.data_branch(job["account"])
        bars, priors, notes = harness.session_inputs(cfg, d, universe=job["universe"], branch=branch)
        res = harness.run_session(cfg, d, bars, priors, fills=job["fills"], limit_fill=job["limit_fill"],
                                  exact=job["exact"], check=job["check"], log=lambda m: None)
        res["stats"]["inputs"] = notes
        res["stats"]["missing_modules"] = cfg.get("_replay_missing_modules", [])
        harness.write(res, out)
        return res["stats"]
    except Exception as e:  # one bad session must not stop the run
        import traceback

        return {"day": str(d), "account": job["account"], "error": f"{type(e).__name__}: {e}",
                "trace": traceback.format_exc()[-1500:]}


def cmd_prep(a):
    days = store.sessions(*a.dates.split("..")) if ".." in a.dates else [pd.Timestamp(a.dates).date()]
    store.check_dates(days)
    have = set(store.available_days())
    if a.fetch:
        store.fetch_1min([d for d in days if d not in have and d <= pd.Timestamp.now().date()])
    if not (store.STORE / "daily.parquet").exists():
        store.fetch_daily(min(days) - timedelta(days=store.LOOKBACK_DAYS + 30), max(days))
    daily = pd.read_parquet(store.STORE / "daily.parquet")
    cache: dict = {}
    for d in [d for d in days if d in set(store.available_days())]:
        t = time.time()
        p = store.build_priors_for(d, store.symbols(), cache=cache, daily=daily)
        print(f"priors {d}: {len(p)} symbols ({time.time() - t:.0f}s)", flush=True)


def cmd_run(a):
    from multiprocessing import get_context

    days = parse_dates(a.dates)
    store.check_dates(days)
    label = a.label or (f"{a.account.replace(',', '+')}-{a.setup}" if a.setup else a.account.replace(",", "+")) + \
        ("-live" if a.as_live else "")
    out = Path(a.out or RUNS / label)
    jobs = [dict(day=str(d), account=a.account, as_live=a.as_live, setup=a.setup, module=a.module, alone=a.alone,
                 block=a.block, universe=a.universe, fills=a.fills, limit_fill=a.limit_fill, exact=a.exact,
                 check=a.check, out=str(out), force=a.force) for d in days]
    t0 = time.time()
    stats = []
    if a.jobs > 1:
        with get_context("fork").Pool(a.jobs, maxtasksperchild=4) as pool:
            for sts in pool.imap_unordered(_day, jobs):
                for st in sts:
                    stats.append(st)
                    print(_line(st), flush=True)
    else:
        for j in jobs:
            for st in _day(j):
                stats.append(st)
                print(_line(st), flush=True)
    for acct in a.account.split(","):
        mine = [s for s in stats if s.get("account") == acct]
        summ = aggregate(out / acct)
        summ.to_csv(out / f"{acct}-summary.csv", index=False)
        run = {"label": label, "account": acct, "dates": [str(d) for d in days], "fills": a.fills,
               "limit_fill": a.limit_fill, "as_live": a.as_live, "setup": a.setup, "module": a.module,
               "wall_s": round(time.time() - t0, 1), "jobs": a.jobs,
               "errors": [s for s in mine if "error" in s],
               "sec_per_session": round(sum(s.get("seconds", 0) for s in mine) / max(1, len(mine)), 1),
               "fast_check": {k: sum((s.get("fast_check") or {}).get(k, 0) for s in mine)
                              for k in ("samples", "frame_diff", "mask_diff", "rvol_diff")},
               "note": "Educational only - not financial advice."}
        (out / f"{acct}-run.json").write_text(json.dumps(run, indent=1, default=str))
        print(f"== {acct}")
        print(summ.to_string(index=False))
        print(f"{len(mine)} sessions, {run['sec_per_session']}s per session, wall {run['wall_s']}s; errors: "
              f"{len(run['errors'])}; fast-path check {run['fast_check']}")
    print("Educational only - not financial advice.")


def _line(st: dict) -> str:
    if "error" in st:
        return f"{st['day']} {st['account']}: ERROR {st['error']}"
    fc = st.get("fast_check") or {}
    return (f"{st['day']} {st['account']}: {st.get('seconds')}s, check frames {fc.get('frame_diff', '-')} / masks "
            f"{fc.get('mask_diff', '-')} diffs of {fc.get('samples', '-')}")


def load_run(acct_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All sessions of one account in a run: (trades, signals)."""
    tr, sg = [], []
    for d in sorted(Path(acct_dir).glob("*/trades.csv.gz")):
        x = pd.read_csv(d)
        if len(x):
            tr.append(x.assign(session=d.parent.name))
        s = pd.read_csv(d.parent / "signals.csv.gz")
        if len(s):
            sg.append(s.assign(session=d.parent.name))
    return (pd.concat(tr, ignore_index=True) if tr else pd.DataFrame(),
            pd.concat(sg, ignore_index=True) if sg else pd.DataFrame())


def aggregate(acct_dir: Path) -> pd.DataFrame:
    from .export import setup_stats

    tr, sg = load_run(acct_dir)
    rows = []
    names = sorted(set(tr.strategy) if len(tr) else set())
    for n in names:
        st = setup_stats(tr[tr.strategy == n])
        s = sg[sg.strategy == n] if len(sg) else sg
        st.update(setup=n, signals=len(s), submitted=int((s.status == "submitted").sum()) if len(s) else 0)
        rows.append(st)
    return pd.DataFrame(rows)


def cmd_export(a):
    from .export import export

    p = export(Path(a.runs), Path(a.out_dir))
    print("wrote", *p)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m mcf.replay", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep")
    p.add_argument("--dates", required=True)
    p.add_argument("--fetch", action="store_true")
    p = sub.add_parser("run")
    p.add_argument("--account", default=os.environ.get("MCF_ACCOUNT", "primary"))
    p.add_argument("--dates", required=True, help="YYYY-MM-DD..YYYY-MM-DD[,YYYY-MM-DD...]")
    p.add_argument("--setup")
    p.add_argument("--module")
    p.add_argument("--block", help="JSON strategies: block for --setup (e.g. '{\"refire\": true}')")
    p.add_argument("--alone", action="store_true", help="only the --setup (the account's setups off)")
    p.add_argument("--as-live", action="store_true", help="the setups frozen for each session on the data branch")
    p.add_argument("--universe", default="lab", choices=["lab", "live"])
    p.add_argument("--fills", default="costs", choices=["costs", "paper"])
    p.add_argument("--limit-fill", default="through", choices=["through", "touch"])
    p.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    p.add_argument("--exact", action="store_true", help="no fast path (slow; for spot checks)")
    p.add_argument("--check", type=int, default=24, help="fast-path fidelity samples per session (0 = off)")
    p.add_argument("--label")
    p.add_argument("--out")
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("export")
    p.add_argument("--runs", default=str(RUNS))
    p.add_argument("--out-dir", default=str(store.ROOT / "docs" / "live"))
    a = ap.parse_args(argv)
    {"prep": cmd_prep, "run": cmd_run, "export": cmd_export}[a.cmd](a)


if __name__ == "__main__":
    main()
