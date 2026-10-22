"""Why live != backtest: a waterfall per account on replayed sessions, every step on the same symbols, priors and bars.

  A  backtest      every signal the setups produce on the full session (the backtester's view: n = 390 bars, so the
                   5-bar gate never applies), simulated with production costs (mcf.backtest.engine.simulate), no caps.
  A' gate          the A signals the live runner can see: lab setups evaluate only when the symbol's 1-minute bar count
                   is a multiple of 5 at the poll after the decision bar ((decision index + 1) % 5 == 0).
  B  live signals  the signals the replayed runner journaled (taken, skipped or shadow), simulated like A.
  C  taken (costs) the replayed trades with production costs and trade-through limit fills (crowding, caps, twin,
                   risk blocks, spread / quote checks, re-entry rules applied by the real runner).
  C' touch         C with the touch-fill counterfactual for target limits (r_touch).
  D  paper fills   the replay with raw paper fills and touch limits (what Alpaca paper does).
  E  live          the paper journals.

    python research/replay/gap.py --costs data/replay/runs/val-costs --paper data/replay/runs/val-paper
        [--accounts primary,testing,testing2] [--jobs 4] [--out research/replay/gap.json]

Educational only - not financial advice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def backtest_day(job: dict) -> pd.DataFrame:
    """A for one account and session: every signal on the full session + simulate with costs, gate flag per signal."""
    from mcf.backtest.engine import Costs, in_play_filter, is_extended, rank_contexts, simulate, universe_ok
    from mcf.replay import harness
    from mcf.strategies.base import DayContext, t
    from mcf.strategies.setups import LabStrategy, build_strategies

    d = pd.Timestamp(job["day"]).date()
    try:
        cfg = harness.account_config(job["account"], d, as_live=job.get("as_live", True))
    except FileNotFoundError:
        return pd.DataFrame()
    bars, priors, _ = harness.session_inputs(cfg, d, universe=job.get("universe", "live"),
                                             branch=harness.data_branch(job["account"]))
    strategies = build_strategies(cfg)
    costs = Costs.from_cfg(cfg["costs"])
    costs_ext = Costs.from_cfg({**cfg["costs"], "slippage_per_share": cfg["costs"].get("extended_slippage_per_share",
                                                                                      0.03)})
    flat = t(cfg["session"]["flatten_by"])
    ctxs = []
    for sym, b in bars.items():
        p = priors.get(sym)
        if p is None or b.empty:
            continue
        c = DayContext(symbol=sym, date=d, bars=b, prev_close=p.prev_close, prev_high=p.prev_high, prev_low=p.prev_low,
                       atr=p.atr, avg_dollar_volume=p.adv, avg_cum_volume=p.avg_cum, avg_move=p.avg_move,
                       prior5=getattr(p, "tail5", None), sma20=getattr(p, "sma20", float("nan")), peers=bars)
        if universe_ok(c, cfg):
            ctxs.append(c)
    orv = [c.rvol().iloc[min(4, len(c.bars) - 1)] for c in ctxs]
    ctxs, _ = in_play_filter(ctxs, orv, cfg)
    rank_contexts(ctxs)
    rows = []
    for c in ctxs:
        for st in strategies:
            if getattr(st, "ticker_split", None) and not st.trades_symbol(c.symbol):
                continue
            if isinstance(st, LabStrategy):
                # research view: the mask over the whole session (ADV floor and allow-list only). eligible() is the
                # live gate; on a full session it also drops every symbol-day with fewer than 390 bars (n % 5 or the
                # window check on the 16:00 bar end) - the engine Backtester inherits that, the research scans do not.
                if c.avg_dollar_volume < st.min_adv or (st.symbols is not None and c.symbol not in st.symbols):
                    continue
                full = len(c.bars) == 390 or st.eligible(c)
            elif not st.eligible(c):
                continue
            else:
                full = True
            try:
                sigs = st.signals(c)
            except Exception:
                continue
            for sig in sigs:
                tr = simulate(sig, c.bars, flat, costs_ext if is_extended(c, cfg) else costs)
                if tr is None:
                    continue
                bt = c.bars.index[sig.bar_index]
                rows.append({"day": str(d), "strategy": st.name, "symbol": c.symbol, "side": sig.side,
                             "min": bt.hour * 60 + bt.minute, "r": tr.r_multiple, "exit_reason": tr.exit_reason,
                             "lab": isinstance(st, LabStrategy), "bt_engine_sees": full,
                             "gate_ok": (not isinstance(st, LabStrategy)) or (sig.bar_index + 1) % 5 == 0})
    return pd.DataFrame(rows)


def _replay_signals_r(run: Path, account: str, days: list[str]) -> pd.DataFrame:
    """B: the replay's journaled signals, simulated with costs on the session bars (as the runner's what-if does)."""
    from mcf.backtest.engine import Costs, simulate
    from mcf.replay import store
    from mcf.strategies.base import Signal, t

    rows = []
    costs = Costs()
    for d in days:
        p = run / account / d / "signals.csv.gz"
        if not p.exists():
            continue
        s = pd.read_csv(p)
        if not len(s):
            continue
        bars = store.load_day(d, sorted(set(s.symbol)))
        for r in s.itertuples():
            b = bars.get(r.symbol)
            if b is None:
                continue
            sig = Signal(r.symbol, r.strategy, int(r.side), int(r.bar_index), float(r.stop),
                         None if pd.isna(r.target) else float(r.target), r.entry_type,
                         None if pd.isna(r.entry_price) else float(r.entry_price))
            try:
                info = json.loads(r.info or "{}")
            except (TypeError, ValueError):
                info = {}
            tr = simulate(sig, b, t("15:55"), costs)
            bt = info.get("bar_time")
            rows.append({"day": d, "strategy": r.strategy, "symbol": r.symbol, "status": r.status, "reason": r.reason,
                         "min": int(bt[:2]) * 60 + int(bt[2:]) if bt else None,
                         "r": None if tr is None else tr.r_multiple})
    return pd.DataFrame(rows)


def _trades(run: Path, account: str, days: list[str]) -> pd.DataFrame:
    parts = []
    for d in days:
        p = run / account / d / "trades.csv.gz"
        if p.exists():
            x = pd.read_csv(p)
            if len(x):
                parts.append(x.assign(day=d))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["r_multiple", "strategy"])


def _sum(x, col="r"):
    x = x[col].dropna().astype(float) if len(x) else pd.Series(dtype=float)
    return {"n": int(len(x)), "total_r": round(float(x.sum()), 2), "avg_r": round(float(x.mean()), 3) if len(x) else None}


def waterfall(costs_run: Path, paper_run: Path | None, account: str, A: pd.DataFrame, live: pd.DataFrame) -> dict:
    days = sorted(A.day.unique()) if len(A) else []
    B = _replay_signals_r(costs_run, account, days)
    C = _trades(costs_run, account, days)
    D = _trades(paper_run, account, days) if paper_run else pd.DataFrame(columns=["r_multiple"])
    E = live[live.date.isin(days)] if len(live) else live
    gated = A[~A.gate_ok]
    out = {"sessions": days,
           "A_backtest": _sum(A), "A_gated_out": _sum(gated), "A_after_gate": _sum(A[A.gate_ok]),
           "A_gated_out_lab_share": round(float(len(gated) / max(1, A.lab.sum())), 3),
           "B_live_signals": _sum(B), "B_taken": _sum(B[B.status == "submitted"]) if len(B) else _sum(B),
           "B_blocked": _sum(B[B.status != "submitted"]) if len(B) else _sum(B),
           "C_taken_costs": _sum(C, "r_multiple"),
           "C_touch": _sum(C, "r_touch") if "r_touch" in C else None,
           "D_paper": _sum(D, "r_multiple"), "E_live": _sum(E, "r_multiple")}
    if len(B):
        blk = B[B.status != "submitted"].copy()
        blk["why"] = blk.reason.astype(str).str.replace(r"\d+(\.\d+)?", "#", regex=True).str[:40]
        out["blocks_by_reason"] = {k: {"n": int(len(g)), "total_r": round(float(g.r.dropna().sum()), 2),
                                       "avg_r": round(float(g.r.dropna().mean()), 3) if g.r.notna().any() else None}
                                   for k, g in blk.groupby("why")}
    # per setup
    rows = []
    for n in sorted(set(A.strategy) | set(C.strategy if len(C) else [])):
        rows.append({"setup": n, "A": _sum(A[A.strategy == n]), "A_gate": _sum(A[(A.strategy == n) & A.gate_ok]),
                     "B": _sum(B[B.strategy == n]) if len(B) else None,
                     "C": _sum(C[C.strategy == n], "r_multiple"),
                     "D": _sum(D[D.strategy == n], "r_multiple") if len(D) else None,
                     "E": _sum(E[E.strategy == n], "r_multiple") if len(E) else None})
    out["per_setup"] = rows
    return out


def regime(days: list[str]) -> pd.DataFrame:
    """Universe median open-to-close (%) per session (the regime classification of rule 19, on the lab universe)."""
    from mcf.replay import store

    rows = []
    for d in days:
        b = store.load_day(d)
        oc = [(x["close"].iloc[-1] / x["open"].iloc[0] - 1) * 100 for x in b.values() if len(x) > 300]
        rows.append({"day": d, "median_oc": float(np.median(oc)) if oc else np.nan,
                     "breadth_up": float(np.mean(np.array(oc) > 0)) if oc else np.nan})
    return pd.DataFrame(rows)


def main():
    from multiprocessing import Pool

    sys.path.insert(0, str(ROOT / "research" / "replay"))
    from validate import live_journal

    ap = argparse.ArgumentParser()
    ap.add_argument("--costs", required=True)
    ap.add_argument("--paper")
    ap.add_argument("--accounts", default="primary,testing,testing2")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--universe", default="live")
    ap.add_argument("--as-live", action="store_true", default=True)
    ap.add_argument("--current", action="store_true", help="today's configs instead of the frozen ones")
    ap.add_argument("--out")
    a = ap.parse_args()
    run = Path(a.costs)
    res = {}
    for acct in a.accounts.split(","):
        days = sorted(p.parent.name for p in (run / acct).glob("*/stats.json"))
        cached = run / f"{acct}-backtest.csv.gz"
        A = pd.read_csv(cached) if cached.exists() else None      # resume: A is the slow part
        if A is not None:
            A["day"] = A["day"].astype(str)
        if A is None or set(days) - set(A.day):
            jobs = [{"day": d, "account": acct, "as_live": not a.current, "universe": a.universe} for d in days
                    if A is None or d not in set(A.day)]
            with Pool(a.jobs) as pool:
                parts = [x for x in pool.map(backtest_day, jobs) if len(x)]
            A = pd.concat(([A] if A is not None else []) + parts, ignore_index=True) if parts or A is not None \
                else pd.DataFrame(columns=["day", "strategy", "r", "gate_ok", "lab"])
            A.to_csv(cached, index=False)
        try:
            _, live = live_journal(acct)
        except Exception:
            live = pd.DataFrame(columns=["date", "r_multiple", "strategy"])
        res[acct] = waterfall(run, Path(a.paper) if a.paper else None, acct, A, live)
        reg = regime(days)
        if len(A):
            per = A.groupby("day").r.agg(["sum", "count"]).reset_index().merge(reg, on="day")
            res[acct]["by_session"] = per.round(3).to_dict(orient="records")
        print(acct, {k: v for k, v in res[acct].items() if k.startswith(("A_", "B_", "C_", "D_", "E_"))})
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1, default=str))
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    main()
