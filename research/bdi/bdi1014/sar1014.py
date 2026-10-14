"""BDI 2026-10-14 Part B: CWT14 stop-and-reverse ("failed fail-break continuation") on the open two-year history.
Pre-declaration: PLAN.md (Part B), written before scoring. Educational only - not financial advice.

    python research/bdi/bdi1014/sar1014.py      # -> sar_results.csv, sar_summary.json (trades stay in scratch)

The locked block 2024-11-01..2025-02-28 is never loaded (lib.months() lists open months only, lib.load_month refuses
locked months, MCF_HIST_ALLOW_LOCKED is never set).
"""
from __future__ import annotations

import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research" / "bdi" / "refire1014"), str(ROOT / "research" / "history2y"), str(ROOT)]
import lib  # noqa: E402
import scan  # noqa: E402
from mcf.research import gates  # noqa: E402

OUT = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
HITS = SCR / "n1014" / "bt_hits.parquet"
GEOMS = {"t05s1": (0.5, 1.0), "t1s1": (1.0, 1.0), "t2s1": (2.0, 1.0), "t1s05": (1.0, 0.5), "eods1": (None, 1.0)}
CTRL_G = {"t05s1": "t05s1", "t1s1": "t1s1", "t2s1": "t1s1", "t1s05": "t1s05", "eods1": "t1s1"}
ENTRIES = ("E1", "E2")
N_STUDY = 240
N_LINEAGE = 120_599 + 10 + N_STUDY


def side_of(name: str) -> int:
    return 1 if name.endswith("long") else -1


def cost(px, kind, tier, entry_kind, tod):
    """Production cost per share: entry (stop-entry = slip + 2c, market = slip x tod mult), exit (target free)."""
    slip = gates.SLIP_PS + px * gates.SLIP_BPS
    if entry_kind == "stop":
        c = slip + gates.STOP_EXTRA
    else:
        c = slip * float(gates.tod_cost_mult([tod])[0])
    return c * tier


def exit_cost(px, kind, tier):
    if kind == "target":
        return 0.0
    c = gates.SLIP_PS + px * gates.SLIP_BPS
    if kind == "stop":
        c += gates.STOP_EXTRA
    return c * tier


def run(H, L, C, TOD, a, b, side, px, stop, tgt):
    """Bars a..b inclusive (after entry), stop-first, flat at the last bar <= 15:55. -> (exit px, kind, bar idx)."""
    last = None
    for i in range(a, b + 1):
        if TOD[i] > 1555:
            break
        if (side == 1 and L[i] <= stop) or (side == -1 and H[i] >= stop):
            return stop, "stop", i
        if tgt is not None and ((side == 1 and H[i] >= tgt) or (side == -1 and L[i] <= tgt)):
            return tgt, "target", i
        last = i
    if last is None:
        return px, "flat", a - 1
    return C[last], "flat", last


def month_job(month: str) -> pd.DataFrame:
    cols = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20", "gap"]
    rc = [f"{k}_{s}_{g}" for k in ("r", "win") for s in ("long", "short") for g in ("t05s1", "t1s1", "t1s05")]
    f = lib.load_month(month, columns=cols + rc)
    f["symbol"] = f["symbol"].astype(str)
    # same-time controls: mean production R of every universe bar (adv20 >= $95M) at date x tod, per side x geom
    u = f[f["adv20"] >= 95e6]
    ctrl = u[["date", "tod"]].copy()
    for s in ("long", "short"):
        for g in ("t05s1", "t1s1", "t1s05"):
            ctrl[f"c_{s}_{g}"] = gates.prod_r(u[f"r_{s}_{g}"].to_numpy(float), u[f"win_{s}_{g}"].to_numpy(float),
                                              u["close"].to_numpy(float), u["atr_d"].to_numpy(float), g,
                                              tod=u["tod"].to_numpy(float))
    ctrl = ctrl.groupby(["date", "tod"]).mean()
    tail = scan.tail_rows(month)
    P = pd.concat([f[["symbol", "date", "tod", "high", "low", "close"]], tail], ignore_index=True)
    P = P.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    P["pos"] = np.arange(len(P))
    H, L, C, TOD = (P[k].to_numpy(float) for k in ("high", "low", "close", "tod"))
    gend = P.groupby(["symbol", "date"], sort=False)["pos"].max()
    day = f.groupby(["symbol", "date"], sort=False)[["atr_d", "gap"]].first()
    a = pd.Timestamp(month + "-01").date()
    z = pd.Timestamp(month + "-01") + pd.offsets.MonthBegin(1)
    h = pd.read_parquet(HITS, filters=[("date", ">=", a), ("date", "<", z.date())])
    h = h[h["name"].str.startswith("CWT14-") & h["r"].notna()]
    h["symbol"] = h["symbol"].astype(str)
    h["date"] = pd.to_datetime(h["date"]).dt.date
    h = h.sort_values(["name", "symbol", "date", "tod"]).groupby(["name", "symbol", "date"], sort=False).head(1)
    h = h.merge(P[["symbol", "date", "tod", "pos", "close"]], on=["symbol", "date", "tod"], how="inner")
    out = []
    for x in h.itertuples(index=False):
        k0 = x.pos
        e = int(gend[(x.symbol, x.date)])
        atr, gap = day.loc[(x.symbol, x.date)]
        px = float(x.close)
        R = 0.25 * float(atr)
        if not (R > 0 and np.isfinite(px)):
            continue
        tier = 3.0 if (abs(gap) >= 20 or px < 5) else 1.0
        s = side_of(x.name)
        stop, tgt = px - s * R, px + s * 0.5 * R
        ex, kind, k = run(H, L, C, TOD, k0 + 1, e, s, px, stop, tgt)
        base = (s * (ex - px) - cost(px, kind, tier, "mkt", x.tod) - exit_cost(ex, kind, tier)) / R
        row = {"name": x.name, "symbol": x.symbol, "date": x.date, "tod": int(x.tod), "side": s, "r_hits": x.r,
               "base": base, "stopped": kind == "stop", "stop_tod": int(TOD[k]) if kind == "stop" else -1}
        if kind == "stop":
            ls = -s
            for ent in ENTRIES:
                if ent == "E1":
                    lp, et = stop, "stop"
                else:
                    lp, et = C[k], "mkt"
                    if TOD[k] > 1550:
                        continue
                ct = TOD[k]
                for g, (tm, sm) in GEOMS.items():
                    lst = lp - ls * sm * R
                    ltg = None if tm is None else lp + ls * tm * R
                    if ent == "E1" and ((ls == -1 and H[k] >= lst) or (ls == 1 and L[k] <= lst)):
                        lx, lk = lst, "stop"
                    elif ent == "E2" and ls * (C[k] - lst) <= 0:
                        continue
                    else:
                        lx, lk, _ = run(H, L, C, TOD, k + 1, e, ls, lp, lst, ltg)
                    row[f"{ent}_{g}"] = (ls * (lx - lp) - cost(lp, lk, tier, et, ct) - exit_cost(lx, lk, tier)) / R
                    cg = CTRL_G[g]
                    key = (x.date, int(TOD[k]))
                    row[f"{ent}_{g}_ctrl"] = float(ctrl.loc[key, f"c_{'long' if ls == 1 else 'short'}_{cg}"]) if key in ctrl.index else np.nan
        out.append(row)
    print(month, len(out), flush=True)
    return pd.DataFrame(out)


def score_book(d: pd.DataFrame, reg, book: str) -> list[dict]:
    rows = []
    base = d[["date", "base"]].rename(columns={"base": "r"})
    sb = gates.summary(base)
    late = pd.to_datetime(d["date"]) >= "2026-01-01"
    for ent in ENTRIES:
        for g in GEOMS:
            c = f"{ent}_{g}"
            if c not in d:
                continue
            leg = d[d[c].notna()][["date", c, c + "_ctrl"]].rename(columns={c: "r"})
            s = gates.summary(leg)
            rs = gates.regime_split(leg, reg)
            wf = gates.walk_forward(leg, exclude_months=lib.LOCKED_MONTHS)
            lt = pd.to_datetime(leg["date"]) >= "2026-01-01"
            ex = leg.assign(r=leg["r"] - leg[c + "_ctrl"]).dropna(subset=["r"])
            se = gates.summary(ex)
            comb = d[["date"]].assign(r=d["base"] + d[c].fillna(0.0))
            sc = gates.summary(comb)
            rc = gates.regime_split(comb, reg)
            rb = gates.regime_split(base, reg)
            v, fails = gates.verdict(s, rs, wf, N_LINEAGE)
            rows.append({
                "book": book, "entry": ent, "geom": g, "n_base": sb["n"], "base_exp": sb["exp_r"], "base_t": sb["t"],
                "stop_share": round(float(d["stopped"].mean()), 3),
                "n": s.get("n", 0), "days": s.get("days"), "exp": s.get("exp_r"), "t": s.get("t"), "win": s.get("win_rate"),
                "ex_best_day": s.get("ex_best_day"),
                "h1_exp": round(float(leg.r[~lt].mean()), 4) if (~lt).any() else None,
                "h2_exp": round(float(leg.r[lt].mean()), 4) if lt.any() else None,
                "up": rs["up"].get("exp_r"), "down": rs["down"].get("exp_r"), "flat": rs["flat"].get("exp_r"),
                "wf": wf.get("share_positive"), "excess": se.get("exp_r"), "excess_t": se.get("t"),
                "comb_exp": sc.get("exp_r"), "comb_t": sc.get("t"),
                "comb_minus_base_up": None if rc["up"].get("exp_r") is None else round(rc["up"]["exp_r"] - rb["up"]["exp_r"], 4),
                "comb_minus_base_down": None if rc["down"].get("exp_r") is None else round(rc["down"]["exp_r"] - rb["down"]["exp_r"], 4),
                "verdict_lineage": v, "fails": "; ".join(fails)})
    return rows


def main():
    months = lib.months()
    assert not set(months) & set(lib.LOCKED_MONTHS)
    tp = SCR / "bdi1014_sar_trades.parquet"
    if tp.exists():
        T = pd.read_parquet(tp)
    else:
        with Pool(3) as p:
            T = pd.concat(p.map(month_job, months), ignore_index=True)
        T.to_parquet(tp)
    T["date"] = pd.to_datetime(T["date"]).dt.date
    reg = lib.regimes()
    reg.index = pd.to_datetime(reg.index).date
    rows = []
    for nm, d in T.groupby("name"):
        rows += score_book(d, reg, nm)
    pool = T.sort_values(["symbol", "date", "side", "stop_tod", "tod"])
    pool = pool[pool["stopped"]].groupby(["symbol", "date", "side", "stop_tod"]).head(1)
    # pooled book: one managed trade per symbol-day-side-stop-bar; base-only (unstopped) signals de-duplicated per symbol-day-side
    unst = T[~T["stopped"]].groupby(["symbol", "date", "side"]).head(1)
    rows += score_book(pd.concat([pool, unst], ignore_index=True), reg, "POOLED")
    R = pd.DataFrame(rows)
    t_l, t_s = gates.t_required(N_LINEAGE), gates.t_required(N_STUDY)
    R["t_bar_lineage"], R["t_bar_study"] = t_l, t_s

    def plateau(r):
        nb = {"t05s1": ["t1s1"], "t1s1": ["t05s1", "t2s1", "t1s05"], "t2s1": ["t1s1"], "t1s05": ["t1s1"], "eods1": ["t2s1"]}[r.geom]
        same = R[(R.book == r.book) & (R.entry == r.entry) & R.geom.isin(nb)]
        other = R[(R.book == r.book) & (R.entry != r.entry) & (R.geom == r.geom)]
        return bool(len(same) and (same.exp > 0).all() and len(other) and (other.exp > 0).all())

    R["plateau"] = R.apply(plateau, axis=1)
    common = (R.exp > 0) & (R.h1_exp > 0) & (R.h2_exp > 0) & (R.up > 0) & (R.down > 0) & (R.wf >= 0.6) & (R.ex_best_day > 0) & R.plateau
    R["testing_pass"] = common & (R.t >= 2.0)
    R["research_pass"] = common & (R.t >= t_l) & (R.excess > 0) & (R.verdict_lineage == "keep")
    R.to_csv(OUT / "sar_results.csv", index=False)
    chk = T[["r_hits", "base"]].corr().iloc[0, 1]
    summ = {"configs_scored": int(len(R)) * 2, "N_study": N_STUDY, "N_lineage": N_LINEAGE, "t_bar_lineage": t_l, "t_bar_study": t_s,
            "signals": int(len(T)), "stopped_share": round(float(T["stopped"].mean()), 3),
            "base_sim_vs_scan_corr": round(float(chk), 4), "base_sim_mean": round(float(T.base.mean()), 4),
            "scan_r_mean": round(float(T.r_hits.mean()), 4),
            "testing_pass": int(R.testing_pass.sum()), "research_pass": int(R.research_pass.sum()),
            "positive_exp": int((R.exp > 0).sum()), "locked_block_loaded": False}
    (OUT / "sar_summary.json").write_text(json.dumps(summ, indent=1))
    pd.set_option("display.width", 300)
    pd.set_option("display.max_rows", 200)
    print(json.dumps(summ, indent=1))
    print(R[["book", "entry", "geom", "n", "exp", "t", "h1_exp", "h2_exp", "up", "down", "wf", "excess", "excess_t",
             "base_exp", "comb_exp", "comb_minus_base_up", "comb_minus_base_down", "plateau", "testing_pass"]].to_string())


if __name__ == "__main__":
    main()
