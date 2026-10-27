"""SZ-PROOF replay (research/ops/sizing_proof.md section 0, declared before this ran).
Live paper replay of every Primary trade + two-year replay of the 8 Primary setups, tiered vs flat vs risk-matched flat.
No lookahead: a setup's tier on session D uses only trades dated before D.

    G21SCR=$SCRATCH/szp/g python research/ops/sizing_proof/replay.py <journals_dir> > research/ops/sizing_proof/replay_out.txt
<journals_dir>/<acct>/journal.db for acct in p t1 t2 gy gen (run_id 1 = live paper). Writes results.csv, tiers_live.csv.
Educational only - not financial advice."""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research" / "ops" / "late_entry1027"))
from late import load_trades, name  # noqa: E402

N_CONF = 12
BAR = round(max(1.5, math.sqrt(2 * math.log(N_CONF))), 2)
LIVE0 = pd.Timestamp("2026-10-06").date()
USD_PER_R = 15.88
ASG = json.loads((ROOT / "docs/live/assignments.json").read_text())["accounts"]
CONFIGS = {  # name: (drift window or None, allow 1.5x, use live stream, use backtest line)
    "V1 T-main+drift20": (20, True, True, True),
    "V2 T-main no drift": (None, True, True, True),
    "V3 drift last-30": (30, True, True, True),
    "V4 no 1.5x +drift": (20, False, True, True),
    "V5 live-only proof": (20, True, True, False),
    "V6 backtest-only proof": (20, True, False, True),
}
TIERS = (0.5, 1.0, 1.5)


def stats(r: np.ndarray, d: np.ndarray) -> dict:
    n = len(r)
    if n == 0:
        return {"n": 0}
    s = pd.Series(r).groupby(d).sum()
    wo = (r.sum() - s.max()) / n
    w, l = r[r > 0], r[r <= 0]
    be = (-l.mean()) / (w.mean() - l.mean()) if len(w) and len(l) else (0.0 if len(w) else 1.0)
    return {"n": n, "avg": r.mean(), "wo": wo, "win": (r > 0).mean(), "be": be}


def tier_of(st: dict, bt: float | None, allow15: bool, use_bt: bool) -> float:
    """bt = backtest avg R before the first live session (None = no two-year list for this setup)."""
    if st["n"] < 30:
        return 0.5
    ok_core = st["avg"] > 0 and st["wo"] > 0 and st["win"] > st["be"]
    if not ok_core:
        return 0.5
    bt_ok1 = (not use_bt) or bt is None or bt >= -0.02 or st["n"] >= 100
    if not bt_ok1:
        return 0.5
    bt_ok15 = (not use_bt) or (bt is not None and bt > 0)
    if allow15 and st["n"] >= 50 and st["avg"] >= 0.10 and st["wo"] >= 0.05 and bt_ok15:
        return 1.5
    return 1.0


def drift(r: np.ndarray, w: int | None) -> bool:
    if w is None or len(r) < 2 * w:
        return False
    last = r[-w:].mean(); lr = r[:-w].mean()
    return last < lr - 0.30 and last < 0


def schedule(stream: pd.DataFrame, sessions: list, bt: float | None, cfg) -> dict:
    """stream: date, r (the proof stream, sorted). Returns {session: multiplier} with down-now / up-at-weekly-review."""
    w, allow15, use_live, use_bt = cfg
    dts = stream["date"].to_numpy(); rr = stream["r"].to_numpy(float)
    eff = None; out = {}; prev = None
    for D in sessions:
        k = np.searchsorted(dts, D, side="left")         # trades strictly before D
        r, d = rr[:k], dts[:k]
        if use_live:
            st = stats(r, d)
        else:   # backtest-only: the stream is empty; proof = the backtest record (passed as a pseudo stream by caller)
            st = stats(r, d)
        cand = tier_of(st, bt, allow15, use_bt)
        if drift(r, w):
            cand = TIERS[max(0, TIERS.index(cand) - 1)]
        review = prev is None or pd.Timestamp(D).isocalendar()[1] != pd.Timestamp(prev).isocalendar()[1]
        if eff is None or cand < eff or (cand > eff and review):
            eff = cand
        out[D] = eff; prev = D
    return out


def book(df: pd.DataFrame, mult: np.ndarray, usd: np.ndarray, days_all) -> dict:
    """df: date, r; flat vs tiered vs risk-matched flat (c = mean multiplier)."""
    r = df["r"].to_numpy(float); d = df["date"].to_numpy()
    c = mult.mean()
    res = {"n": len(r), "mean_mult": round(c, 3), "share_0.5": round((mult == 0.5).mean(), 3),
           "share_1.5": round((mult == 1.5).mean(), 3)}
    for lab, m in (("flat", np.ones_like(r)), ("tiered", mult), ("matched", np.full_like(r, c))):
        x = pd.Series(m * r).groupby(d).sum().reindex(days_all, fill_value=0.0)
        u = pd.Series(m * usd).groupby(d).sum().reindex(days_all, fill_value=0.0)
        cum = x.cumsum(); dd = (cum - cum.cummax()).min()
        cu = u.cumsum(); ddu = (cu - cu.cummax()).min()
        res[f"{lab}_R"] = x.sum(); res[f"{lab}_usd"] = u.sum(); res[f"{lab}_R_per_risk"] = (m * r).sum() / m.sum()
        res[f"{lab}_maxDD_R"] = dd; res[f"{lab}_maxDD_usd"] = ddu; res[f"{lab}_worst_day_R"] = x.min()
        res[f"{lab}_worst_day_usd"] = u.min(); res[f"{lab}_R_wo_best_day"] = x.sum() - x.max()
        res[f"_{lab}"] = x
    for lab, other in (("vs_flat", "flat"), ("vs_matched", "matched")):
        D = res["_tiered"] - res[f"_{other}"]
        se = D.std(ddof=1) / math.sqrt(len(D)) if len(D) > 1 else np.nan
        res[f"delta_{lab}_R"] = D.sum(); res[f"t_{lab}"] = D.mean() / se if se and se > 0 else np.nan
        res[f"delta_{lab}_wo_best_day"] = D.sum() - D.max()
        res[f"delta_{lab}_best_day"] = str(D.idxmax())
    for k in ("_flat", "_tiered", "_matched"):
        res.pop(k)
    return res


def main():
    J = Path(sys.argv[1])
    L = []
    for a in ("p", "t1", "t2", "gy", "gen"):
        x = pd.read_sql("select * from trades where run_id=1", sqlite3.connect(J / a / "journal.db"))
        x["acct"] = a; L.append(x)
    L = pd.concat(L, ignore_index=True)
    L["risk"] = L.shares * (L.entry - L.stop).abs()
    L = L[L.risk > 0].copy()
    L["r"] = L.pnl_adj / L.risk
    L["date"] = pd.to_datetime(L["date"]).dt.date
    L = L.sort_values(["date", "entry_time"]).reset_index(drop=True)
    H = load_trades()
    H = H.sort_values(["date", "tod"]).reset_index(drop=True)
    bt_live = {s: g[g.date < LIVE0].r.mean() for s, g in H.groupby("setup")}
    P = L[L.acct == "p"].reset_index(drop=True)
    sessions = sorted(P.date.unique())
    print(f"live: {len(L)} paper trades all accounts; Primary {len(P)} trades, {len(sessions)} sessions "
          f"{sessions[0]}..{sessions[-1]}, {P.strategy.nunique()} setups; N configs {N_CONF}, bar {BAR}")
    rows = []; tier_rows = []
    for cname, cfg in CONFIGS.items():
        w, allow15, use_live, use_bt = cfg
        mult = np.full(len(P), np.nan)
        for s, idx in P.groupby("strategy").groups.items():
            bt = bt_live.get(s)
            if use_live:
                stream = L[L.strategy == s][["date", "r"]]
            else:
                hb = H[(H.setup == s) & (H.date < LIVE0)][["date", "r"]]
                stream = hb
            sch = schedule(stream, sessions, bt, cfg)
            mult[np.asarray(idx)] = [sch[d] for d in P.loc[idx, "date"]]
            if cname.startswith("V1"):
                for d in sessions:
                    if (P.loc[idx, "date"] == d).any():
                        tier_rows.append({"setup": s, "date": d, "mult": sch[d], "trades": int((P.loc[idx, "date"] == d).sum())})
        res = book(P[["date", "r"]], mult, P.pnl_adj.to_numpy(float), sessions)
        rows.append({"replay": "live Primary", "config": cname, **res})
    pd.DataFrame(tier_rows).to_csv(HERE / "tiers_live.csv", index=False)
    # two-year replay: 8 Primary setups (from 2026-10-28)
    prim = [s for s in ASG["primary"] if s in set(H.setup)]
    B = H[H.setup.isin(prim)].reset_index(drop=True)
    hs = sorted(H.date.unique())
    print(f"two-year: {len(B)} backtest trades, {len(prim)} setups, {len(hs)} sessions {hs[0]}..{hs[-1]}")
    for cname, cfg in CONFIGS.items():
        w, allow15, use_live, use_bt = cfg
        cfg2 = (w, allow15, True, False)        # the stream IS the backtest record (walk-forward)
        mult = np.full(len(B), np.nan)
        for s, idx in B.groupby("setup").groups.items():
            sch = schedule(B.loc[idx, ["date", "r"]], hs, None, cfg2)
            mult[np.asarray(idx)] = [sch[d] for d in B.loc[idx, "date"]]
        res = book(B[["date", "r"]], mult, B.r.to_numpy(float) * USD_PER_R, hs)
        rows.append({"replay": "two-year 8 Primary", "config": cname, **res})
        if cname.startswith("V1"):
            yr = B.assign(m=mult, y=pd.to_datetime(B.date).dt.year)
            print("\nV1 two-year by setup (flat R / tiered R / mean multiplier):")
            g = yr.groupby("setup").apply(lambda x: pd.Series({"n": len(x), "flat_R": x.r.sum(), "tiered_R": (x.m * x.r).sum(),
                                                                "mean_mult": x.m.mean(), "share_1.5": (x.m == 1.5).mean()}))
            g.insert(0, "name", [name(s)[:40] for s in g.index]); print(g.round(2).to_string())
            print("\nV1 two-year by half-year: flat R / tiered R / matched R")
            hy = pd.to_datetime(B.date).dt.year.astype(str) + np.where(pd.to_datetime(B.date).dt.month <= 6, "H1", "H2")
            yy = pd.DataFrame({"hy": hy, "flat": B.r, "tiered": mult * B.r, "m": mult})
            agg = yy.groupby("hy").agg(n=("flat", "size"), flat=("flat", "sum"), tiered=("tiered", "sum"), mult=("m", "mean"))
            agg["matched"] = [yy[yy.hy == h].flat.sum() * mult.mean() for h in agg.index]
            print(agg.round(2).to_string())
    R = pd.DataFrame(rows)
    R.round(4).to_csv(HERE / "results.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
    cols = ["replay", "config", "n", "mean_mult", "share_0.5", "share_1.5", "flat_R", "tiered_R", "matched_R",
            "flat_usd", "tiered_usd", "flat_R_per_risk", "tiered_R_per_risk", "flat_maxDD_R", "tiered_maxDD_R",
            "flat_worst_day_R", "tiered_worst_day_R", "flat_maxDD_usd", "tiered_maxDD_usd", "flat_worst_day_usd",
            "tiered_worst_day_usd", "flat_R_wo_best_day", "tiered_R_wo_best_day",
            "delta_vs_flat_R", "t_vs_flat", "delta_vs_flat_wo_best_day", "delta_vs_matched_R", "t_vs_matched",
            "delta_vs_matched_wo_best_day"]
    print("\n== results (R = sum of multiplier x R after costs; usd = live pnl_adj x multiplier, two-year R x $15.88)")
    print(R[cols].round(3).T.to_string())
    print("\nEducational only - not financial advice.")


if __name__ == "__main__":
    main()
