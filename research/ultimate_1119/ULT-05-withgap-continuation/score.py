"""ULT-05 scoring: fit grid / fit selection (frozen to fitsel.json) / single check score / random control / diagnostics.
    python score.py WORK fit      -> fit grid table + fitsel.json (written BEFORE any check data exists)
    python score.py WORK check    -> the frozen config scored once on check, then the plateau diagnostic
Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bt  # noqa: E402

CACHE = bt.CACHE
APRIL = ("2025-04-03", "2025-04-09")


def spy_daytype(days):
    d = pads.dataset(str(CACHE / "SPY.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    tz = "America/New_York"
    L0, L1 = pd.Timestamp("2024-11-01", tz=tz), pd.Timestamp("2025-03-01", tz=tz)
    b = d.to_table(filter=(fld < L0) | (fld >= L1)).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(tz)
    bt.no_locked(np.unique(b.index.date))
    b = b[(b.index.hour * 100 + b.index.minute >= 930) & (b.index.hour * 100 + b.index.minute <= 1559)]
    g = b.groupby(np.array([str(x) for x in b.index.date]))
    ret = (g.close.last() / g.open.first() - 1) * 100
    lab = pd.Series(np.where(ret >= 0.3, "up", np.where(ret <= -0.3, "down", "flat")), index=ret.index)
    return lab.reindex(days)


def stats(s, days, dtype=None):
    n = len(s)
    nd = len(days)
    if n == 0:
        return dict(trades=0, per_session=0.0, win=np.nan, avg=np.nan, avg_wo=np.nan, share=np.nan, total=0.0,
                    r_session=0.0, worst=np.nan, hold=np.nan)
    byd = s.groupby("date").r.sum()
    tot = float(s.r.sum())
    best = byd.idxmax()
    wo = s[s.date != best]
    out = dict(trades=n, per_session=n / nd, win=float((s.r > 0).mean()), avg=float(s.r.mean()),
               avg_wo=float(wo.r.mean()) if len(wo) else np.nan,
               share=(float(byd.max() / tot) if tot > 0 else np.nan), total=tot, r_session=tot / nd,
               worst=float(byd.min()), hold=float(s.hold.median()), traded_sessions=int(byd.size), best_day=best)
    if dtype is not None:
        lab = s.date.map(dtype)
        for k in ("up", "flat", "down"):
            out["spy_" + k] = float(s.r[lab == k].mean()) if (lab == k).any() else np.nan
    return out


def fmt(st):
    sh = st.get("share", np.nan)
    shs = "n/a" if sh != sh else f"{sh:.2f}" + (" **1 day**" if sh >= 0.5 else "")
    return (f"{st['trades']} | {st['per_session']:.2f} | {st['win']:.3f} | {st['avg']:+.3f} | {st['avg_wo']:+.3f} | "
            f"{shs} | {st['total']:+.1f} | {st['r_session']:+.3f} | {st['worst']:+.1f} | {st['hold']:.0f}")


def random_control(sel, pool, cfg, half, seed=1119):
    """Same symbol-sessions as the selected trades, random decision bar inside the config window (intake U bars),
    same side and exit; one draw per selected trade."""
    rng = np.random.default_rng(seed)
    p = pool[(pool.tod >= 1015) & (pool.tod <= cfg["w_hi"])]
    grp = {k: g for k, g in p.groupby(["symbol", "date", "side"])}
    rows = []
    for r in sel.itertuples():
        g = grp.get((r.symbol, r.date, r.side))
        if g is None or not len(g):
            continue
        rows.append(g.iloc[int(rng.integers(len(g)))])
    T = pd.DataFrame(rows).reset_index(drop=True)
    W = bt.walk(T, half)
    ex = cfg["ex"]
    W = W[W["k" + ex] >= 0]
    return bt.score_rows(W, ex)


HDR = ("| config | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | "
       "worst day | median hold |\n|---|---|---|---|---|---|---|---|---|---|---|")


def module_chain(S, cfg):
    """Diagnostic: the module's own bar-only refire rule (2nd hit >= 15 bars after the 1st, max 2) + day cap 30."""
    ex = cfg["ex"]
    s = bt.cfg_filter(S, cfg).sort_values(["symbol", "date", "tod"], kind="mergesort")
    keep = []
    for _, g in s.groupby(["symbol", "date"], sort=False):
        last, n = -10**9, 0
        for i, t in zip(g.index, bt.m2(g.tod.to_numpy())):
            if n < 2 and t - last >= 75:
                keep.append(i); last = t; n += 1
    s = S.loc[keep].sort_values(["date", "tod", "adv20"], ascending=[True, True, False], kind="mergesort")
    s = s.groupby("date", sort=False).head(30)
    return bt.score_rows(s, ex)


def side_split(s):
    return " / ".join(f"{'long' if k > 0 else 'short'} {len(g)} tr {g.r.mean():+.3f} (sum {g.r.sum():+.1f})"
                      for k, g in s.groupby("side"))


if __name__ == "__main__":
    W = Path(sys.argv[1]); half = sys.argv[2]
    S = pd.read_parquet(W / f"walked_{half}.parquet")
    days = list(pd.read_parquet(W / f"days_{half}.parquet").date)
    bt.no_locked(S.date.unique()); bt.no_locked(days)
    dtype = spy_daytype(days)
    C = bt.configs()
    res = {}
    if half == "fit":
        print(HDR)
        for k, cfg in C.items():
            s = bt.select(S, cfg)
            st = stats(s, days, dtype)
            nA = s[(s.date < APRIL[0]) | (s.date > APRIL[1])]
            st["avg_ex_april"] = float(nA.r.mean())
            st["sides"] = side_split(s)
            res[k] = st
            print(f"| {k} {cfg['label']} | {fmt(st)} |")
        print()
        for k, st in res.items():
            print(k, "SPY up/flat/down", f"{st['spy_up']:+.3f} / {st['spy_flat']:+.3f} / {st['spy_down']:+.3f}",
                  "avg ex-April", f"{st['avg_ex_april']:+.3f}", "traded sessions", st["traded_sessions"], "best day", st["best_day"], "|", st["sides"])
        elig = [k for k in C if res[k]["per_session"] >= 2.0]
        pool = elig or list(C)
        pick = max(pool, key=lambda k: (round(res[k]["total"], 6), -list(C).index(k)))
        fs = dict(id="ULT-05-withgap-continuation", config=pick, **C[pick], reached_2_per_session=bool(elig),
                  rule="PLAN sec.5: highest fit total R among configs >= 2 trades/session; none -> highest fit total R (TIER B at best)",
                  fit=res[pick], frozen_utc=datetime.now(timezone.utc).isoformat())
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=str))
        json.dump({k: v for k, v in res.items()}, open(HERE / "fit_grid.json", "w"), indent=1, default=str)
        print("\nFIT-SELECTED:", pick, C[pick], "eligible(>=2/session):", elig)
        # uncapped diagnostic (counted, never used)
        su = bt.select(S, C[pick], cap=None)
        print("uncapped diag", fmt(stats(su, days)))
        sm = module_chain(S, C[pick])
        print("module-chain diag", fmt(stats(sm, days)))
        P = pd.read_parquet(W / f"pool_{half}.parquet")
        rc = random_control(bt.select(S, C[pick]), P, C[pick], half)
        print("random control", fmt(stats(rc, days)))
    else:
        fs = json.loads((HERE / "fitsel.json").read_text())
        pick = fs["config"]
        s = bt.select(S, C[pick])
        st = stats(s, days, dtype)
        mid = days[len(days) // 2]
        st["h1"] = float(s[s.date < mid].r.mean()); st["h2"] = float(s[s.date >= mid].r.mean())
        st["sides"] = side_split(s)
        print("CHECK (scored once)", pick, C[pick]["label"], "|", st["sides"])
        print(HDR); print(f"| {pick} {C[pick]['label']} | {fmt(st)} |")
        print("SPY up/flat/down", f"{st['spy_up']:+.3f} / {st['spy_flat']:+.3f} / {st['spy_down']:+.3f}",
              "H1/H2", f"{st['h1']:+.3f} / {st['h2']:+.3f}", "traded sessions", st["traded_sessions"], "best day", st["best_day"])
        json.dump(st, open(HERE / "check_selected.json", "w"), indent=1, default=str)
        P = pd.read_parquet(W / f"pool_{half}.parquet")
        rc = random_control(s, P, C[pick], half)
        print("random control", fmt(stats(rc, days)))
        print("uncapped diag", fmt(stats(bt.select(S, C[pick], cap=None), days)))
        print("module-chain diag", fmt(stats(module_chain(S, C[pick]), days)))
        print("\nPLATEAU (diagnostic only, never used to re-select)"); print(HDR)
        for k, cfg in C.items():
            print(f"| {k} {cfg['label']} | {fmt(stats(bt.select(S, cfg), days))} |")
        # monthly
        print("\nmonthly (selected):")
        print(s.assign(m=s.date.str[:7]).groupby("m").r.agg(["count", "mean", "sum"]).round(3).to_string())
