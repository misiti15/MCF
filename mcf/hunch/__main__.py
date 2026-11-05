"""Hunch CLI (research only; never places orders).

  python -m mcf.hunch replay --metric M1 [--metric M3] [--cache DIR] [--panel FILE] [--out research/hunch]
  python -m mcf.hunch live --dry      shows the guesses Hunch would make on the latest cached session (offline)
  python -m mcf.hunch live --dry --loop --state-dir state --seed research/hunch/u200/state/M1_model.npz [--push]
                                      the live shadow (mcf/hunch/live.py; .github/workflows/hunch.yml): real guesses on
                                      live 3-min bars, scored and learned from; no orders, ever

GitHub load: the shadow is one job a trading day (~09:40-16:01 ET, a hand-over run after ~5h40m), one Alpaca bars
request per 100 symbols every 3 minutes. Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

from . import data as D
from . import metrics as M
from . import replay as R


def _panel(args) -> pd.DataFrame:
    if args.panel and Path(args.panel).exists():
        return pd.read_parquet(args.panel)
    p = D.build_panel(_universe(args), cache=args.cache, verbose=True)
    if args.panel:
        p.to_parquet(args.panel)
    return p


def _universe(args) -> list:
    if getattr(args, "universe", None):
        return [ln.split()[0] for ln in Path(args.universe).read_text().splitlines() if ln.strip() and ln[0] != "#"]
    return list(D.UNIVERSE)


def _universe_note(panel: pd.DataFrame, args=None) -> str:
    if args is not None and getattr(args, "universe", None):
        syms = list(dict.fromkeys(panel["symbol"]))
        first = panel.groupby("symbol")["date"].min()
        late = sum(str(first[s]) > "2024-10-01" for s in syms)
        return (f"- Data: SIP 1-min bars from the 2-year cache (data/cache_hist/1Min), RTH only, built into 3-min bars. "
                f"Universe ({len(syms)}, list in {args.universe}): SPY, QQQ, IWM + the most liquid names in the cache "
                f"by 20-day dollar ADV (to 2026-11-04), live-traded names first. {late} of them list after the start "
                f"and join when they list. Context: SPY, QQQ, SMH, IBIT. Survivorship: today's liquid names applied "
                f"to the past.")
    first = panel.groupby("symbol")["date"].min()
    late = [f"{s} (from {first[s]})" for s in D.UNIVERSE if str(first.get(s, "")) > "2024-10-01"]
    return (f"- Data: SIP 1-min bars from the 2-year cache (data/cache_hist/1Min), RTH only, built into 3-min bars. "
            f"Universe ({len(D.UNIVERSE)}): {', '.join(D.INDEX)} + the most-traded live symbols in the journals "
            f"(Primary + Testing 1 + Testing 2 on 2026-11-04) with history in the cache: {', '.join(D.LIVE)}. "
            f"Later listings join when they list: {', '.join(late) or 'none'}. Context: SPY, QQQ, sector ETFs "
            f"SMH (semis) and IBIT (crypto names). Survivorship: today's most-traded names applied to the past.")


def cmd_replay(args):
    t0 = time.time()
    panel = _panel(args)
    metrics = args.metric or [M.ACTIVE]
    n_metrics = max(args.n_metrics, len(metrics))
    out = Path(args.out)
    for met in metrics:
        t1 = time.time()
        print(f"[{met}] grid", flush=True)
        g = R.make_grid(panel, met)
        print(f"[{met}] replay {g.X.shape}", flush=True)
        res = R.run(g, verbose=True)
        sc = R.score(g, res, n_metrics=n_metrics)
        md = R.report(sc, g, res, met, out, _universe_note(panel, args), time.time() - t1)
        import json
        import resource
        sj = out / f"{met}_summary.json"
        js = json.loads(sj.read_text())
        js.update(runtime_s=round(time.time() - t1, 1), n_tickers=len(g.symbols),
                  max_rss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024),
                  valid_by_ticker={s: d["VALID"]["rate"]["pooled:logreg"] for s, d in sc["by_symbol"].items()},
                  valid_by_ticker_own={s: d["VALID"]["rate"]["ticker:logreg"] for s, d in sc["by_symbol"].items()},
                  valid_by_ticker_base={s: d["VALID"]["rate"][d["VALID"]["best_baseline"]]
                                        for s, d in sc["by_symbol"].items()})
        sj.write_text(json.dumps(js, indent=1, default=float))
        if args.save_state:
            R.save_state(res, out / "state" / f"{met}_model.npz", met, g.steps["date"].iloc[-1])
        V = sc["periods"]["VALID"]
        best = max(R.MAIN, key=lambda n: V["rate"][n]["hit"])
        print(f"[{met}] best {best} {V['rate'][best]['hit']:.4f} vs {V['best_baseline']} "
              f"{V['rate'][V['best_baseline']]['hit']:.4f} z={V['vs_best'][best]['z_day']:.2f} -> {md}", flush=True)
    print(f"done in {time.time() - t0:.0f}s")


def cmd_live(args):
    if not args.dry:
        raise SystemExit("Hunch has no live mode that acts on anything; use --dry (shadow guesses only).")
    if args.loop:
        from .live import run_live

        why = run_live(Path(args.state_dir), Path(args.seed) if args.seed else None, do_push=args.push,
                       max_minutes=args.max_minutes)
        print(f"Hunch shadow stopped: {why}. No orders were placed. Educational only - not financial advice.")
        return
    panel = D.build_panel(D.UNIVERSE[:3], cache=args.cache)  # light: the three index ETFs
    last = panel["date"].max()
    met = args.metric[0] if args.metric else M.ACTIVE
    g = R.make_grid(panel[panel["date"] >= sorted(panel["date"].unique())[-(R.WARMUP_SESS + 5)]], met)
    res = R._walk(g, list(range(len(D.FEATURES))), full=False)
    st = g.steps
    k = st.index[st["date"] == last].max()
    print(f"Hunch shadow (dry) — {met}: {M.DESCRIBE[met]} — latest cached session {last}, bar b={st.loc[k, 'b']}")
    for i, s in enumerate(g.symbols):
        if g.mask[k, i]:
            print(f"  {s}: Hunch (pooled logreg, warmed on the last {R.WARMUP_SESS + 5} sessions) says "
                  f"{'YES' if res['P'][k, i, 0] else 'no'}")
    print("Shadow stub only: no orders, no state written. Educational only - not financial advice.")


def cmd_scale(args):
    from .scale import build

    print(build(Path(args.out)))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m mcf.hunch")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("replay")
    r.add_argument("--metric", action="append", choices=M.LADDER)
    r.add_argument("--n-metrics", type=int, default=2, help="metrics run in the study (multiple-testing N)")
    r.add_argument("--cache", default=None, help="1-min parquet cache dir (default data/cache_hist/1Min)")
    r.add_argument("--universe", default=None, help="file with one ticker per line (default: data.UNIVERSE)")
    r.add_argument("--save-state", action="store_true", help="save the end-of-replay model for the live shadow")
    r.add_argument("--panel", default=None, help="optional parquet to cache the feature panel")
    r.add_argument("--out", default=str(D.ROOT / "research" / "hunch"))
    r.set_defaults(fn=cmd_replay)
    lv = sub.add_parser("live")
    lv.add_argument("--dry", action="store_true")
    lv.add_argument("--metric", action="append", choices=M.LADDER)
    lv.add_argument("--cache", default=None)
    lv.add_argument("--loop", action="store_true", help="run the live shadow loop for today (Alpaca market data)")
    lv.add_argument("--state-dir", default="state", help="checkout of the mcf-data-hunch branch")
    lv.add_argument("--seed", default=None, help="start model when state/model.npz is missing (replay output)")
    lv.add_argument("--push", action="store_true", help="commit + push the state dir to mcf-data-hunch as it goes")
    lv.add_argument("--max-minutes", type=float, default=340, help="hand over to the next queued run after this")
    lv.set_defaults(fn=cmd_live)
    sc = sub.add_parser("scale", help="write research/hunch/SCALE.md from the 20 / 100 / 200 replays")
    sc.add_argument("--out", default=str(D.ROOT / "research" / "hunch"))
    sc.set_defaults(fn=cmd_scale)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
