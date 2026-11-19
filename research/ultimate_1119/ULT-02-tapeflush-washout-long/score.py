"""ULT-02 scoring (fit grid + selection, check once, plateau, controls). See bt.py. Educational only - not financial advice.
    python score.py WORK fit            -> fit_grid.csv + fitsel.json (frozen BEFORE any check data is loaded)
    python score.py WORK check          -> check_once.json (fit-selected config only)
    python score.py WORK plateau        -> check_grid.csv (diagnostic, after check_once)"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bt  # noqa: E402


def controls(c, sel, ex):
    """Random controls for the selected trades: (a) same symbol-session, random window bar; (b) same moment (date, tod),
    random intake-U name. Each selected trade is replaced by the mean of its (up to 3) control draws."""
    r = f"r_{ex}"
    a = c[(c.kind == "ctlA") & c[r].notna()].groupby(["symbol", "date"])[r].mean()
    b = c[(c.kind == "ctlB") & c[r].notna()].groupby(["date", "tod"])[r].mean()
    ka = pd.MultiIndex.from_arrays([sel.symbol, sel.date])
    kb = pd.MultiIndex.from_arrays([sel.date, sel.tod])
    va, vb = a.reindex(ka).to_numpy(), b.reindex(kb).to_numpy()
    sa = sel.R.to_numpy()[np.isfinite(va)].mean() - np.nanmean(va)
    sb = sel.R.to_numpy()[np.isfinite(vb)].mean() - np.nanmean(vb)
    return dict(ctlA_avg=float(np.nanmean(va)), ctlA_n=int(np.isfinite(va).sum()), sig_minus_ctlA=float(sa),
                ctlB_avg=float(np.nanmean(vb)), ctlB_n=int(np.isfinite(vb).sum()), sig_minus_ctlB=float(sb))


def halves(sel):
    ds = sorted(sel.date.astype(str).unique())
    if not ds:
        return {}
    mid = ds[len(ds) // 2]
    d = sel.date.astype(str)
    return dict(first_half_avg=float(sel.R[d < mid].mean()), second_half_avg=float(sel.R[d >= mid].mean()), split_date=mid)


def run(W, half, cfgs):
    c = pd.read_parquet(Path(W) / f"trades_{half}.parquet")
    bt.no_locked(c["date"].unique())
    ns, ds = bt.n_sessions(half)
    dt = bt.spy_daytype(ds[0], ds[-1])
    rows, sels = [], {}
    for g in cfgs:
        s = bt.select_trades(c, g)
        sels[g["name"]] = s
        rows.append({**g, **bt.stats(s, ns, dt)})
    return c, ns, dt, pd.DataFrame(rows), sels


if __name__ == "__main__":
    W, mode = Path(sys.argv[1]), sys.argv[2]
    G = bt.grid()
    if mode == "fit":
        c, ns, dt, df, sels = run(W, "fit", G)
        df.to_csv(HERE / "fit_grid.csv", index=False, float_format="%.4f")
        ok = df[df.per_session >= 2.0]
        pool = ok if len(ok) else df
        best = pool.sort_values("total", ascending=False, kind="mergesort").iloc[0]
        g = next(x for x in G if x["name"] == best["name"])
        s = sels[g["name"]]
        unc = bt.stats(bt.select_trades(c, g, cap=0), ns, dt)
        ctl = controls(c, s, g["exit"])
        fs = dict(config=g, selected_by="highest fit total R among configs with >= 2.0 trades/session (PLAN sec. 5)",
                  reached_2_per_session=bool(len(ok)), fit_sessions=ns, fit=bt.stats(s, ns, dt), fit_uncapped_diag=unc,
                  fit_controls=ctl, fit_halves=halves(s),
                  frozen_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        pd.set_option("display.width", 250)
        print(df[["name", "spy_t", "depth", "exit", "trades", "per_session", "win", "avg", "avg_wo_best", "best_share",
                  "total", "worst_day", "avg_ex_apr3_9", "median_hold"]].round(3).to_string(index=False))
        print(json.dumps(fs, indent=1, default=float))
    elif mode == "check":
        fs = json.loads((HERE / "fitsel.json").read_text())
        g = fs["config"]
        c, ns, dt, df, sels = run(W, "check", [g])
        s = sels[g["name"]]
        out = dict(config=g, check_sessions=ns, check=bt.stats(s, ns, dt),
                   check_uncapped_diag=bt.stats(bt.select_trades(c, g, cap=0), ns, dt),
                   check_controls=controls(c, s, g["exit"]), check_halves=halves(s),
                   by_month=s.groupby(s.date.astype(str).str[:7]).R.agg(["size", "mean", "sum"]).round(3).to_dict("index"),
                   scored_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        (HERE / "check_once.json").write_text(json.dumps(out, indent=1, default=float))
        s[["symbol", "date", "tod", "close", "atr_d", "fo_atr", "dist_hod_atr", "r30", "R", "hold"]].to_csv(
            HERE / "check_trades.csv", index=False, float_format="%.4f")
        print(json.dumps(out, indent=1, default=float))
    elif mode == "plateau":
        c, ns, dt, df, sels = run(W, "check", G)
        df.to_csv(HERE / "check_grid.csv", index=False, float_format="%.4f")
        pd.set_option("display.width", 250)
        print(df[["name", "spy_t", "depth", "exit", "trades", "per_session", "win", "avg", "avg_wo_best", "best_share",
                  "total", "worst_day", "median_hold"]].round(3).to_string(index=False))
