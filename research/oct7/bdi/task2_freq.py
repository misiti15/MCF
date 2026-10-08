"""Task 2 - trade frequency. (a) the production funnel on Jul 15 - Sep 15 2026; (b) RE-ENTRY: up to 2-3 trades per
symbol per setup per day after the previous trade has closed, with a 15/30-minute cooldown, either on any later
qualifying bar ('any') or only on a fresh threshold cross ('fresh': the bar before was not qualifying).
Every trade: mcf.backtest.engine.simulate + production costs; portfolio rows also go through the production
allocator (Backtester.allocate: 160 slots, 100 per setup, one open position per symbol, -20R daily stop).
Train <= 2026-08-25, valid 08-26..09-15. Educational only - not financial advice."""
import json
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
sys.path.insert(0, "research/oct7/bdi")
from lib import CFG, D, load, paired, run, stats  # noqa: E402
from mcf.backtest.engine import Backtester  # noqa: E402
from mcf.strategies.base import Signal, t  # noqa: E402
from mcf.strategies.setups import HeatStrategy, LabStrategy, build_strategies  # noqa: E402

STRATS = {s.name: s for s in build_strategies(CFG)}
REENTRY = ["heat_fade_short", "heat_fade_long", "exhaustion_short"]


def make_sig(setup, sym, end, side, px, atr):
    s = STRATS[setup]
    R = s.r_atr_frac * atr
    if isinstance(s, HeatStrategy):
        return Signal(sym, setup, side, int(end), stop=px - side * R,
                      target=None if s.target_r is None else px + side * s.target_r * R), R
    return Signal(sym, setup, side, int(end), stop=px - side * s.dn * R, target=px + side * s.up * R,
                  exit_by=t("15:55")), R


def _nn(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else x


def sig_from_row(r):
    return Signal(r["symbol"], r["setup"], int(r["side"]), int(r["end"]), stop=r["stop"], target=_nn(r["target"]),
                  entry_type=r["entry_type"], entry_price=_nn(r["entry_price"]), entry_valid_bars=int(r["entry_valid_bars"]),
                  exit_by=None if _nn(r["exit_by"]) is None else t(r["exit_by"]))


def sequence(G, b, ext, max_n, cool, mode):
    """G: one symbol-day's qualifying bars for one setup (sorted by end). Returns [(n_th, Trade)]."""
    ends = G["end"].to_numpy()
    qual = set(ends.tolist())
    out, k_free = [], -1
    for r in G.itertuples():
        if len(out) >= max_n:
            break
        if r.end < k_free:
            continue
        if out and mode == "fresh" and (r.end - 5) in qual:
            continue
        sig, R = make_sig(r.setup, r.symbol, r.end, r.side, r.px, r.atr)
        tr, k = run(sig, b, ext)
        if tr is None:
            continue
        out.append((len(out) + 1, tr))
        k_free = k + cool
    return out


def main():
    H, bars, F = load()
    sessions = {"train": sorted(F.date[F.date <= "2026-08-25"]), "valid": sorted(F.date[F.date > "2026-08-25"])}
    ndays = {k: len(v) for k, v in sessions.items()}
    report = {}

    # ---------------- (a) funnel ----------------
    allq = H[H.kind == "all"]
    simple = H[H.kind == "sig"]
    fun = []
    base_trades = []
    for setup in STRATS:
        Q = allq[allq.setup == setup]
        if len(Q):
            first = Q.sort_values("end").groupby(["symbol", "date"]).head(1)
            for r in first.itertuples():
                sig, R = make_sig(setup, r.symbol, r.end, r.side, r.px, r.atr)
                tr, _ = run(sig, bars[(r.symbol, r.date)], r.ext)
                if tr:
                    base_trades.append(tr)
            fun.append(dict(setup=setup, qualifying_bars=len(Q), symbol_days=len(first)))
        else:
            S = simple[simple.setup == setup]
            n_ok = 0
            for r in S.to_dict("records"):
                tr, _ = run(sig_from_row(r), bars[(r["symbol"], r["date"])], r["ext"])
                if tr:
                    base_trades.append(tr)
                    n_ok += 1
            fun.append(dict(setup=setup, qualifying_bars=len(S), symbol_days=len(S)))
    bt = Backtester(list(STRATS.values()), CFG)
    cand = pd.DataFrame([dict(strategy=x.strategy, date=str(x.date)) for x in base_trades])
    acc = bt.allocate(list(base_trades))
    acc["date"] = acc["date"].astype(str)
    Ffun = pd.DataFrame(fun).set_index("setup")
    Ffun["eligible_symbol_days"] = [F.get(f"elig_{s}", pd.Series(dtype=float)).sum() for s in Ffun.index]
    Ffun["filled_candidates"] = cand.groupby("strategy").size().reindex(Ffun.index, fill_value=0)
    Ffun["after_allocator"] = acc.groupby("strategy").size().reindex(Ffun.index, fill_value=0)
    nd = len(F)
    for c in ("eligible_symbol_days", "qualifying_bars", "symbol_days", "filled_candidates", "after_allocator"):
        Ffun[c + "_per_day"] = (Ffun[c] / nd).round(1)
    Ffun["exp_r_after_alloc"] = acc.groupby("strategy").r_multiple.mean().reindex(Ffun.index).round(4)
    for sp in ("train", "valid"):
        a = acc[acc.date.isin(sessions[sp])]
        Ffun[f"exp_r_{sp}"] = a.groupby("strategy").r_multiple.mean().reindex(Ffun.index).round(4)
        Ffun[f"n_{sp}"] = a.groupby("strategy").size().reindex(Ffun.index, fill_value=0)
        Ffun[f"t_day_{sp}"] = [round(float(np.nan_to_num(_t(a[a.strategy == s]))), 2) for s in Ffun.index]
    pd.set_option("display.width", 250)
    print("=== (a) funnel, %d sessions; universe/day %.0f, in-play/day %.0f ===" % (nd, F.universe.mean(), F.in_play.mean()))
    print(Ffun.to_string())
    print("portfolio after allocator: %.1f trades/day; total R %.1f" % (len(acc) / nd, acc.r_multiple.sum()))
    Ffun.to_csv("research/oct7/bdi/task2_funnel.csv")
    report["funnel_trades_per_day"] = round(len(acc) / nd, 2)

    # ---------------- (b) re-entry ----------------
    rows, legs_all = [], {}
    for setup in REENTRY:
        Q = allq[allq.setup == setup].sort_values("end")
        groups = list(Q.groupby(["symbol", "date"]))
        for max_n in (1, 2, 3):
            for cool in ((0,) if max_n == 1 else (15, 30)):
                for mode in (("any",) if max_n == 1 else ("any", "fresh")):
                    L = []
                    for (sym, d), G in groups:
                        for nth, tr in sequence(G, bars[(sym, d)], bool(G.ext.iloc[0]), max_n, cool, mode):
                            L.append(dict(date=d, symbol=sym, nth=nth, r=tr.r_multiple, tr=tr))
                    key = f"{setup}|n{max_n}|cd{cool}|{mode}"
                    legs_all[key] = pd.DataFrame(L)
    for key, L in legs_all.items():
        setup = key.split("|")[0]
        base = legs_all[f"{setup}|n1|cd0|any"]
        for sp in ("train", "valid"):
            Ls = L[L.date.isin(sessions[sp])]
            Bs = base[base.date.isin(sessions[sp])]
            st = stats(Ls)
            add = Ls[Ls.nth > 1]
            sa = stats(add) if len(add) else dict(n=0)
            pr = paired(Ls, Bs, sessions[sp]) if not key.endswith("n1|cd0|any") else {}
            rows.append(dict(config=key, split=sp, **st, trades_per_day=round(st.get("n", 0) / ndays[sp], 2),
                             reentry_n=sa.get("n", 0), reentry_exp=sa.get("exp"), reentry_t=sa.get("t_day"),
                             reentry_ex_best=sa.get("ex_best"), **pr))
    R = pd.DataFrame(rows)
    R.to_csv("research/oct7/bdi/task2_reentry.csv", index=False)
    print("=== (b) re-entry (R = own 1R = 0.25 ATR; costs in) ===")
    print(R[["config", "split", "n", "trades_per_day", "win", "exp", "tot", "t_day", "ex_best", "reentry_n", "reentry_exp",
             "reentry_t", "diff_tot", "diff_t", "diff_ex_best"]].to_string())
    print("configs tried (task 2b):", len(legs_all) - len(REENTRY), "re-entry configs +", len(REENTRY), "baselines")

    # portfolio through the allocator: production first-signals vs each re-entry config of all three setups at once
    others = [x for x in base_trades if x.strategy not in REENTRY]
    port = []
    for cfgk in ("n1|cd0|any", "n2|cd15|any", "n2|cd30|any", "n3|cd15|any", "n3|cd30|any",
                 "n2|cd15|fresh", "n2|cd30|fresh", "n3|cd15|fresh", "n3|cd30|fresh"):
        trs = list(others)
        for setup in REENTRY:
            trs += [Trade_copy(x) for x in legs_all[f"{setup}|{cfgk}"].tr]
        A = bt.allocate(trs)
        A["date"] = A["date"].astype(str)
        for sp in ("train", "valid"):
            a = A[A.date.isin(sessions[sp])]
            d = a.groupby("date").r_multiple.sum()
            port.append(dict(config=cfgk, split=sp, n=len(a), per_day=round(len(a) / ndays[sp], 1),
                             exp=round(a.r_multiple.mean(), 4), tot=round(a.r_multiple.sum(), 1), t_day=round(_t(a), 2),
                             ex_best=round(d.sum() - d.max(), 1), pnl=round(a.pnl.sum(), 0)))
    P = pd.DataFrame(port)
    P.to_csv("research/oct7/bdi/task2_portfolio.csv", index=False)
    print("=== portfolio (all live setups, production allocator) ===")
    print(P.to_string())


def Trade_copy(x):
    from copy import copy
    return copy(x)


def _t(a):
    if len(a) == 0:
        return float("nan")
    d = a.groupby("date").r_multiple.sum()
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 2 and d.std(ddof=1) > 0 else float("nan")


if __name__ == "__main__":
    main()
