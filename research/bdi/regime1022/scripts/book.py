"""regime1022 Part B: protection rules on whole books (PLAN.md). Event simulation per day in time order: a lot is open
from its entry bar until its exit bar (5-minute path), account-wide max 3 lots per symbol (same side only), the
account's per-setup and concurrent caps and its existing realized stops (P0 = as-run), then each pre-declared variant
on top. Books: Primary, Testing 1, Testing 2, Graveyard (covered setups, 2-year history) + a replay of the live Primary
paper journal. Writes part_b.csv, part_b_days.csv, part_b_out.md. Educational only - not financial advice."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from live import journals
from rc import HERE, SCR, g21c, lib, split_of

ACCT = {"primary": "p", "testing": "t1", "testing2": "t2", "graveyard": "gy"}
VARIANTS = {
    "P0 as-run": {},
    "B1a per-setup 1 open lot per symbol": {"setup_sym_cap": 1},
    "B1b per-setup 2 open lots per symbol": {"setup_sym_cap": 2},
    "B1c per-setup max 5 open lots": {"setup_open_cap": 5},
    "B1d per-setup max 10 open lots": {"setup_open_cap": 10},
    "B2a per-setup realized+open stop -3R": {"setup_or_stop": 3.0},
    "B2b per-setup realized+open stop -4R": {"setup_or_stop": 4.0},
    "B3a account realized+open stop -10R": {"acct_or_stop": 10.0},
    "B3b account realized+open stop -15R": {"acct_or_stop": 15.0},
    "B3c account realized+open stop -20R": {"acct_or_stop": 20.0},
    "B4a cluster cap 3 (20d corr > 0.7)": {"cluster_cap": 3},
    "B4b cluster cap 5 (20d corr > 0.7)": {"cluster_cap": 5},
}


def corr_lookup():
    d = lib.daily()[["symbol", "date", "close"]].copy()
    d["date"] = pd.to_datetime(d["date"]).dt.date
    w = d.pivot_table(index="date", columns="symbol", values="close").sort_index()
    r = w.pct_change()
    gap = pd.Series(pd.to_datetime(r.index)).diff().dt.days.to_numpy() > 5
    r.iloc[gap] = np.nan
    dates = list(r.index)
    pos = {x: i for i, x in enumerate(dates)}
    cache = {}

    def get(date, syms):
        key = date
        if key not in cache:
            cache.clear()
            i = pos.get(date)
            cache[key] = (None if i is None or i < 20 else r.iloc[i - 20:i])
        win = cache[key]
        if win is None:
            return None
        cols = [s for s in syms if s in win.columns]
        sub = win[cols]
        return sub.corr(min_periods=15)
    return get


def simulate(df: pd.DataFrame, caps: dict, var: dict, corr=None) -> np.ndarray:
    """df sorted by date, tod, order, symbol. Columns: date, tod, exit_tod, r, setup, symbol, side."""
    keep = np.zeros(len(df), bool)
    D, Tm, X, R = df["date"].to_numpy(), df["tod"].to_numpy(), df["exit_tod"].to_numpy(), df["r"].to_numpy(float)
    S, Y, SD = df["setup"].to_numpy(), df["symbol"].to_numpy(), df["side"].to_numpy()
    starts = np.flatnonzero(np.r_[True, D[1:] != D[:-1]])
    ends = np.r_[starts[1:], len(D)]
    for a, b in zip(starts, ends):
        lots = []                  # [setup, symbol, side, exit, r]
        real_s, real_a = {}, 0.0
        cm = None
        if var.get("cluster_cap") and corr is not None:
            cm = corr(D[a], list(pd.unique(Y[a:b])))
        for i in range(a, b):
            t = Tm[i]
            still = []
            for L in lots:
                if L[3] <= t:
                    real_s[L[0]] = real_s.get(L[0], 0.0) + L[4]
                    real_a += L[4]
                else:
                    still.append(L)
            lots = still
            s, y, sd = S[i], Y[i], SD[i]
            # P0 as-run account rules
            if caps.get("max_daily_loss_r") and real_a <= -caps["max_daily_loss_r"]:
                continue
            if caps.get("max_setup_daily_loss_r") and real_s.get(s, 0.0) <= -caps["max_setup_daily_loss_r"]:
                continue
            on_sym = [L for L in lots if L[1] == y]
            if any(L[2] != sd for L in on_sym) or len(on_sym) >= caps.get("lots", 3):
                continue
            if caps.get("twin") and any(L[0] != s and L[0].replace("-FD", "") == s.replace("-FD", "") for L in on_sym):
                continue
            mine = [L for L in lots if L[0] == s]
            if len(mine) >= caps.get("per_strategy", 1e9) or len(lots) >= caps.get("concurrent", 1e9):
                continue
            # variants
            if var.get("setup_sym_cap") and sum(L[1] == y for L in mine) >= var["setup_sym_cap"]:
                continue
            if var.get("setup_open_cap") and len(mine) >= var["setup_open_cap"]:
                continue
            if var.get("setup_or_stop") and real_s.get(s, 0.0) - len(mine) <= -var["setup_or_stop"]:
                continue
            if var.get("acct_or_stop") and real_a - len(lots) <= -var["acct_or_stop"]:
                continue
            if cm is not None and y in cm.columns:
                peers = [L for L in lots if L[2] == sd and L[1] != y and L[1] in cm.columns]
                if peers:
                    c = cm.loc[y, [L[1] for L in peers]].to_numpy(float)
                    if np.nansum(c > 0.7) >= var["cluster_cap"]:
                        continue
            keep[i] = True
            lots.append([s, y, sd, X[i], R[i]])
    return keep


def metrics(x: pd.DataFrame, par: pd.DataFrame, all_days) -> dict:
    out = {}
    for sp in ("train", "valid", "all"):
        xs = x if sp == "all" else x[x["split"] == sp]
        ps = par if sp == "all" else par[par["split"] == sp]
        days = [d for d in all_days if sp == "all" or split_of([d])[0] == sp]
        dr = xs.groupby("date")["r"].sum().reindex(days, fill_value=0.0)
        pr = ps.groupby("date")["r"].sum().reindex(days, fill_value=0.0)
        k = max(1, int(round(0.05 * len(days))))
        worst_p = pr.sort_values().index[:k]       # the parent's worst 5% of days
        kept = len(xs) / max(1, len(ps))
        out.update({f"{sp}_n": len(xs), f"{sp}_kept_pct": round(100 * kept, 1),
                    f"{sp}_total_R": round(float(xs["r"].sum()), 1), f"{sp}_avg_R": round(float(xs["r"].mean()), 4) if len(xs) else None,
                    f"{sp}_vs_random_thin_R": round(float(xs["r"].sum() - kept * ps["r"].sum()), 1),
                    f"{sp}_worst_day": round(float(dr.min()), 1),
                    f"{sp}_worst5pct_mean": round(float(dr.sort_values().iloc[:k].mean()), 2),
                    f"{sp}_parent_worst5pct_days_mean": round(float(dr.loc[worst_p].mean()), 2),
                    f"{sp}_days_le_m10": int((dr <= -10).sum()), f"{sp}_days": len(days)})
    return out


def book_frame(acct: str, asr: pd.DataFrame, setups: pd.DataFrame) -> pd.DataFrame:
    names = setups[(setups["account"] == acct) & setups["covered"]]["setup"].tolist()
    order = {n: i for i, n in enumerate(names)}
    x = asr.assign(setup=asr["names"].str.split(",")).explode("setup")
    x = x[x["setup"].isin(names)].copy()
    x["side"] = np.where(x["side"] == "long", 1, -1)
    x["ord"] = x["setup"].map(order)
    return x.sort_values(["date", "tod", "ord", "symbol"]).reset_index(drop=True)


def main():
    asr = pd.read_parquet(SCR / "asrun.parquet")    # every refire-chain signal (lot rules applied here)
    setups = pd.read_csv(HERE / "setups_used.csv")
    corr = corr_lookup()
    rows, md, day_rows = [], ["# Part B - protection rules (2-year backtest books; costs in)\n"], []
    for acct in ACCT:
        cfg = g21c.account_cfg(acct)
        A, L = cfg["account"], cfg.get("live") or {}
        caps = {"max_daily_loss_r": A.get("max_daily_loss_r"), "max_setup_daily_loss_r": A.get("max_setup_daily_loss_r"),
                "lots": L.get("max_lots_per_symbol", 3), "per_strategy": A.get("max_positions_per_strategy"),
                "concurrent": A.get("max_concurrent_positions"), "twin": bool(L.get("block_twin_same_symbol"))}
        x = book_frame(acct, asr, setups)
        all_days = sorted(asr["date"].unique())
        keeps = {}
        for vname, var in VARIANTS.items():
            keeps[vname] = simulate(x, caps, var, corr)
        par = x[keeps["P0 as-run"]]
        for vname, k in keeps.items():
            m = metrics(x[k], par, all_days)
            rows.append({"book": acct, "variant": vname, "setups": x["setup"].nunique(), **m})
            dr = x[k].groupby("date")["r"].sum()
            day_rows.append(pd.DataFrame({"book": acct, "variant": vname, "date": dr.index, "R": dr.values}))
        print(acct, "done", flush=True)
    res = pd.DataFrame(rows)
    res.to_csv(HERE / "part_b.csv", index=False)
    pd.concat(day_rows).to_csv(HERE / "part_b_days.csv", index=False)
    cols = ["variant", "train_total_R", "valid_total_R", "train_kept_pct", "valid_kept_pct", "train_vs_random_thin_R",
            "valid_vs_random_thin_R", "all_worst_day", "all_worst5pct_mean", "all_parent_worst5pct_days_mean",
            "all_days_le_m10"]
    for acct in ACCT:
        md.append(f"\n## {acct}\n\n" + res[res["book"] == acct][cols].to_markdown(index=False) + "\n")
    (HERE / "part_b_out.md").write_text("".join(md))
    print("".join(md))


def live_replay():
    """The same rules on the live Primary paper journal (entries/exits from the journal, R after costs)."""
    T = journals()
    p = T[(T["acct"] == "p") & T["radj"].notna()].copy()
    ent = pd.to_datetime(p["entry_time"], utc=True, format="mixed").dt.tz_convert("America/New_York")
    ex = pd.to_datetime(p["exit_time"], utc=True, format="mixed").dt.tz_convert("America/New_York")
    p["tod"] = ent.dt.hour * 100 + ent.dt.minute
    p["exit_tod"] = (ex.dt.hour * 100 + ex.dt.minute).fillna(1600)
    p = p.rename(columns={"strategy": "setup", "radj": "r"}).sort_values(["date", "tod", "symbol"]).reset_index(drop=True)
    p["side"] = p["side"].astype(int)
    p["split"] = "valid"
    caps = {"max_daily_loss_r": None, "lots": 99}     # the journal already reflects every live rule
    corr = corr_lookup()
    out = []
    for vname, var in VARIANTS.items():
        k = simulate(p, caps, var, corr)
        x = p[k]
        dr = x.groupby("date")["r"].sum()
        out.append({"variant": vname, "trades": int(k.sum()), "kept_pct": round(100 * k.mean(), 1),
                    "total_R": round(float(x["r"].sum()), 1), "pnl_adj": round(float(x["pnl_adj"].sum()), 0),
                    "worst_day_R": round(float(dr.min()), 1),
                    "R_1021": round(float(x[x["date"].astype(str) == "2026-10-21"]["r"].sum()), 1),
                    "R_1015": round(float(x[x["date"].astype(str) == "2026-10-15"]["r"].sum()), 1)})
    df = pd.DataFrame(out)
    df.to_csv(HERE / "part_b_live_primary.csv", index=False)
    print(df.to_string())


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "live":
        live_replay()
    else:
        main()
