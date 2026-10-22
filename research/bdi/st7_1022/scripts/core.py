"""st7_1022 core: candidate table, P0 selection, exit simulator with production costs, random partners, scoring.
Educational only - not financial advice.

Simulator (PLAN.md): entry at the signal bar close; per later 5-minute bar (tod <= 15:55): stop first if stop and target
fall in the same bar; timed exit at the close of the last bar <= 15:55. Costs as mcf.research.gates.prod_r: entry side
(1c + 1 bps) x time-of-day multiplier; exit side free on a target limit fill, else 1c + 1 bps, +2c on stop fills
(trailing / break-even stops are stop fills); x3 on the extended tier (|gap| >= 20% or price < $5)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from sc import HERE, RG22, SLIP_BPS, SLIP_PS, STOP_EXTRA, W, no_locked, split_of, summ, tier, tod_cost_mult

import sys
sys.path.insert(0, str(HERE.parents[0] / "regime1022" / "scripts"))


def day_table() -> pd.DataFrame:
    import os
    os.environ.setdefault("G21SCR", str(RG22))
    from regime import day_table as dt  # regime1022/scripts/regime.py (unchanged)
    return dt()


def load():
    cand = pd.concat([pd.read_parquet(p) for p in sorted((W / "cand").glob("*.parquet"))], ignore_index=True)
    part = pd.concat([pd.read_parquet(p) for p in sorted((W / "part").glob("*.parquet"))], ignore_index=True)
    no_locked(cand["date"].unique())
    no_locked(part["date"].unique())
    pc = np.load(W / "paths_cand.npz")
    pp = np.load(W / "paths_part.npz")
    cand["split"] = split_of(cand["date"])
    dt = day_table()
    dt.index = pd.Index(dt.index).astype(str)
    cand = cand.join(dt[["regime", "o2c", "range"]], on="date")
    cand["regime2"] = np.where((cand["regime"] == "Choppy") & (cand["o2c"] > 0), "Choppy-up",
                               np.where(cand["regime"] == "Choppy", "Choppy-dn", cand["regime"]))
    cand["upday"] = cand["regime"].eq("Bull") | cand["regime2"].eq("Choppy-up")
    return cand, part, pc, pp


def first_per_symday(df: pd.DataFrame, m: np.ndarray) -> np.ndarray:
    """Positions of the first True row per symbol-day (rows sorted by symbol, date, tod inside)."""
    x = df.loc[m, ["symbol", "date", "tod"]].sort_values(["symbol", "date", "tod"], kind="mergesort")
    x = x[~x.duplicated(["symbol", "date"])]
    return np.sort(x.index.to_numpy())


def p0_cond(c: pd.DataFrame, rsi_max=30.0, fo_max=-1.0, lvl=50.0) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return ((c["prsi"] >= lvl) & (c["rsi"] < lvl) & (c["rsi"] <= rsi_max) & (c["fromOpen"] < fo_max)
                & (c["buyPressure"] > 0)).to_numpy()


def simulate(E, D, H, L, C, T, ku=1.0, kd=1.0, be=None, trail=None, scale=None, scale_be=True):
    """Long only. Returns gross R (price move / D, position-weighted), cost in $ per share (before tier and tod),
    exit tod, kind (2 target, 1 stop, 0 timed, 3 scaled)."""
    E, D = np.asarray(E, float), np.asarray(D, float)
    n, m = H.shape
    stop = E - kd * D
    tgt = E + ku * D if ku is not None else np.full(n, np.nan)
    best = E.copy()
    done = ~(np.isfinite(E) & np.isfinite(D) & (D > 0))
    pnl = np.zeros(n)
    exit_cost = np.zeros(n)
    kind = np.zeros(n, int)
    ex_t = np.full(n, np.nan)
    last_c = E.copy()
    last_t = np.full(n, np.nan)
    w = np.ones(n)                      # remaining position weight
    scaled = np.zeros(n, bool)
    leg = SLIP_PS + E * SLIP_BPS
    for j in range(m):
        h, lo, c, t = H[:, j], L[:, j], C[:, j], T[:, j]
        ok = (~done) & np.isfinite(c) & (t <= 1555)
        if not ok.any():
            continue
        hs = ok & (lo <= stop)
        ht = ok & ~hs & np.isfinite(tgt) & (h >= tgt)
        pnl = np.where(hs, pnl + w * (stop - E), pnl)
        exit_cost = np.where(hs, exit_cost + w * (leg + STOP_EXTRA), exit_cost)
        pnl = np.where(ht, pnl + w * (tgt - E), pnl)
        kind = np.where(hs, 1, np.where(ht, 2, kind))
        ex_t = np.where(hs | ht, t, ex_t)
        done = done | hs | ht
        still = ok & ~hs & ~ht
        if scale is not None:
            sp = E + scale * D
            hsc = still & ~scaled & (h >= sp)
            pnl = np.where(hsc, pnl + 0.5 * (sp - E), pnl)
            w = np.where(hsc, 0.5, w)
            scaled |= hsc
            if scale_be:
                stop = np.where(hsc, np.maximum(stop, E), stop)
        last_c = np.where(still, c, last_c)
        last_t = np.where(still, t, last_t)
        best = np.where(still, np.maximum(best, h), best)
        if be is not None:
            mv = still & (best - E >= be * D - 1e-12)
            stop = np.where(mv, np.maximum(stop, E), stop)
        if trail is not None:
            stop = np.where(still, np.maximum(stop, best - trail * D), stop)
    timed = ~done & np.isfinite(E) & np.isfinite(D) & (D > 0)
    pnl = np.where(timed, pnl + w * (last_c - E), pnl)
    exit_cost = np.where(timed, exit_cost + w * leg, exit_cost)
    ex_t = np.where(timed, np.where(np.isfinite(last_t), last_t, np.nan), ex_t)
    kind = np.where(timed & scaled, 3, kind)
    gross = pnl / np.where(D > 0, D, np.nan)
    return gross, exit_cost, ex_t, kind


def net_r(gross, exit_cost, E, D, tod, gap):
    entry = (SLIP_PS + np.asarray(E, float) * SLIP_BPS) * tod_cost_mult(tod)
    return gross - tier(E, gap) * (entry + exit_cost) / np.asarray(D, float)


EXITS = {
    "t1s1": dict(ku=1.0), "t05s1": dict(ku=0.5), "t1s05": dict(ku=1.0, kd=0.5),
    "D1_t15s1": dict(ku=1.5), "D2_t2s1": dict(ku=2.0), "D3_hold": dict(ku=None),
    "D4_trail1": dict(ku=None, trail=1.0), "D5_t2_be1": dict(ku=2.0, be=1.0),
    "D6_half1_rest_hold_be": dict(ku=None, scale=1.0, scale_be=True),
}


def exit_r(frame: pd.DataFrame, P, name: str, rows=None) -> np.ndarray:
    rows = np.arange(len(frame)) if rows is None else rows
    kw = EXITS[name]
    E = frame["close"].to_numpy(float)[rows]
    D = 0.25 * frame["atr_d"].to_numpy(float)[rows]
    g, xc, _, _ = simulate(E, D, P["H"][rows], P["L"][rows], P["C"][rows], P["T"][rows], **kw)
    return net_r(g, xc, E, D, frame["tod"].to_numpy(float)[rows], frame["gap"].to_numpy(float)[rows])


def stats(df: pd.DataFrame, r: np.ndarray, ctrl: np.ndarray | None = None) -> dict:
    out = {}
    for sp in ("train", "valid", "all"):
        m = np.ones(len(df), bool) if sp == "all" else (df["split"].to_numpy() == sp)
        rr = r[m]
        if not len(rr):
            out.update({f"n_{sp}": 0})
            continue
        s = summ(rr, df["date"].to_numpy()[m])
        day = pd.Series(rr).groupby(df["date"].to_numpy()[m]).sum()
        tot = float(rr.sum())
        out.update({f"n_{sp}": s["n"], f"avg_{sp}": s["exp_r"], f"tot_{sp}": round(tot, 2), f"t_{sp}": s["t"],
                    f"worst_day_{sp}": round(float(day.min()), 2),
                    f"top_day_share_{sp}": round(float(day.max() / tot), 3) if tot > 0 else None})
        if ctrl is not None:
            cc = ctrl[m]
            ok = np.isfinite(cc)
            out[f"rand_{sp}"] = round(float(np.nanmean(cc)), 4) if ok.any() else None
            out[f"excess_{sp}"] = round(float(rr[ok].mean() - cc[ok].mean()), 4) if ok.any() else None
    k = np.sort(pd.Series(r).groupby(df["date"].to_numpy()).sum().to_numpy())
    out["worst5pct_days"] = round(float(k[: max(1, int(round(0.05 * len(k))))].mean()), 2)
    for reg in ("Bull", "Bear", "Choppy", "Quiet", "Choppy-up"):
        col = "regime2" if reg == "Choppy-up" else "regime"
        for sp in ("train", "valid", "all"):
            m = (df[col].to_numpy() == reg) & ((df["split"].to_numpy() == sp) if sp != "all" else True)
            out[f"{reg}_{sp}_n"] = int(m.sum())
            out[f"{reg}_{sp}_avg"] = round(float(r[m].mean()), 4) if m.any() else None
            out[f"{reg}_{sp}_tot"] = round(float(r[m].sum()), 2)
    for sp in ("train", "valid", "all"):
        m = df["upday"].to_numpy() & ((df["split"].to_numpy() == sp) if sp != "all" else True)
        out[f"Up_{sp}_n"] = int(m.sum())
        out[f"Up_{sp}_avg"] = round(float(r[m].mean()), 4) if m.any() else None
        out[f"Up_{sp}_tot"] = round(float(r[m].sum()), 2)
    return out
