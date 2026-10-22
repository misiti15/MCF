"""ns3var1022 Part 1: descriptive diagnosis of P0 (NS3-FD as run) on two years: splits by regime, time of day,
gap, relative strength, 20-day return, beta, ATR%, reclaim size, bars below VWAP, reclaim volume, entry #k per symbol-
day, day of week, SPY / QQQ VWAP side, breadth direction, peers. Also restricted to Bull + Choppy days (where the
losses sit). Not counted as configurations. Educational only - not financial advice."""
from __future__ import annotations

import numpy as np
import pandas as pd

from nv import HERE, NV
from variants import cl


def main():
    tr = pd.read_pickle(NV / "trades.pkl")["trades"]["P0"].copy()
    df = pd.read_pickle(NV / "cand.pkl")
    f = df.iloc[tr["row"].to_numpy()].reset_index(drop=True)
    for k in ("gap", "rs", "ret20", "beta60", "atr_pct_d", "vwapDistPct", "runs_below", "volumeRatio", "spy_vwap",
              "qqq_vwap", "d2", "peer_med", "spy_fo", "min6", "fromOpen", "close"):
        tr[k] = f[k].to_numpy()
    tr = tr.sort_values(["date", "symbol", "tod"])
    tr["k"] = tr.groupby(["date", "symbol"]).cumcount() + 1
    B = {
        "regime": tr["regime"].astype(str),
        "time of day": pd.cut(tr["tod"], [950, 1000, 1030, 1130, 1300, 1400, 1501], right=False).astype(str),
        "gap %": pd.cut(tr["gap"], [-100, -5, -2, 0, 2, 100]).astype(str),
        "RS vs SPY (fromOpen - SPY fromOpen)": pd.cut(tr["rs"], [-100, -5, -4, -3, -2, 100]).astype(str),
        "20-day return %": pd.cut(tr["ret20"], [-100, -10, 0, 10, 25, 1000]).astype(str),
        "60-day beta": pd.cut(tr["beta60"], [-10, 0.75, 1.0, 1.5, 2.0, 10]).astype(str),
        "daily ATR %": pd.cut(tr["atr_pct_d"], [0, 2, 3, 5, 8, 100]).astype(str),
        "reclaim size (% above VWAP)": pd.cut(tr["vwapDistPct"], [0, 0.1, 0.25, 0.5, 1, 100]).astype(str),
        "bars below VWAP before": pd.cut(tr["runs_below"], [-1, 0, 2, 5, 11, 1000]).astype(str),
        "reclaim bar volume ratio": pd.cut(tr["volumeRatio"], [0, 0.75, 1.0, 1.5, 2.5, 1000]).astype(str),
        "entry #k of the day (symbol)": tr["k"].clip(upper=4).map({1: "1st", 2: "2nd", 3: "3rd", 4: "4th+"}),
        "day of week": tr["dow"].map(dict(enumerate(["Mon", "Tue", "Wed", "Thu", "Fri"]))),
        "SPY vs its VWAP at entry": np.where(tr["spy_vwap"] > 0, "above", np.where(tr["spy_vwap"] <= 0, "below", "n/a")),
        "QQQ vs its VWAP at entry": np.where(tr["qqq_vwap"] > 0, "above", np.where(tr["qqq_vwap"] <= 0, "below", "n/a")),
        "SPY from open at entry": pd.cut(tr["spy_fo"], [-100, -0.5, -0.15, 0.15, 0.5, 100]).astype(str),
        "breadth 2-bar change": np.where(tr["d2"] < 0, "falling", np.where(tr["d2"] >= 0, "rising/flat", "n/a (before 10:00)")),
        "peer median from open": pd.cut(tr["peer_med"], [-100, -2, -1, 0, 1, 100]).astype(str),
        "stock from open at entry": pd.cut(tr["fromOpen"], [-100, -6, -4, -3, -2]).astype(str),
        "exit kind": tr["kind"].map({0: "held to 15:55", 1: "stop", 2: "target"}),
    }
    rows = []
    for scope, m in (("all days", np.ones(len(tr), bool)), ("Bull+Choppy days", tr["regime"].isin(["Bull", "Choppy"]).to_numpy())):
        for fam, b in B.items():
            for sp in ("train", "valid", "2y"):
                ms = m & ((tr["split"] == sp).to_numpy() if sp != "2y" else True)
                q = tr[ms]
                bb = pd.Series(np.asarray(b), index=tr.index)[ms]
                for lev, g in q.groupby(bb):
                    mu, t, n = cl(g["r"], g["date"])
                    ex, ext, _ = cl(g["r"] - g["ctrl"], g["date"])
                    rows.append({"scope": scope, "family": fam, "bucket": lev, "split": sp, "n": n,
                                 "share": round(n / max(1, len(q)), 3), "avg_r": round(mu, 4), "tot_r": round(g["r"].sum(), 1),
                                 "t": round(t, 2) if np.isfinite(t) else None, "ctrl_avg": round(float(np.nanmean(g["ctrl"])), 4),
                                 "excess": round(ex, 4), "excess_t": round(ext, 2) if np.isfinite(ext) else None})
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "diag.csv", index=False)
    # regime x time-of-day and regime x k (2y)
    x = []
    for fam in ("time of day", "entry #k of the day (symbol)", "SPY vs its VWAP at entry", "RS vs SPY (fromOpen - SPY fromOpen)"):
        b = pd.Series(np.asarray(B[fam]), index=tr.index)
        for (rg, lev), g in tr.groupby([tr["regime"].astype(str), b]):
            x.append({"family": fam, "regime": rg, "bucket": lev, "n": len(g), "avg_r": round(g["r"].mean(), 4),
                      "tot_r": round(g["r"].sum(), 1)})
    pd.DataFrame(x).to_csv(HERE / "diag_regime_cross.csv", index=False)
    # worst days
    dd = tr.groupby("date").agg(r=("r", "sum"), n=("r", "size"), regime=("regime", "first")).sort_values("r")
    dd.head(25).to_csv(HERE / "diag_worst_days.csv")
    print(out[(out["split"] == "2y") & (out["scope"] == "all days")].to_string())


if __name__ == "__main__":
    main()
