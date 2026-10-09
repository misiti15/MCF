"""Regime study step 1 (NOTES.md 1.2): market-context signals per (session, bar) from the open 2-year lab rows
(stack1009/data/base.npz, adv20 >= 95M, 09:50-15:00; the rule-19 locked block is not in it) + the rest-of-day target.
Output (git-ignored): data/ctx.parquet, one row per (day, tod). Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402

SDIR = ROOT / "research" / "bdi" / "stack1009" / "data"


def main():
    z = np.load(SDIR / "base.npz")
    keys = ["fromOpen", "vwapDistPct", "gap", "volumeRatio", "day", "tod", "sym", "close", "atr_d", "dist_hod_atr",
            "dist_lod_atr"]
    B = {k: z[k] for k in keys}
    dates = pd.read_csv(SDIR / "dates.csv").iloc[:, 0].tolist()
    syms = pd.read_csv(SDIR / "symbols.csv").iloc[:, 0].astype(str).tolist()
    d = lib.daily()
    d["key"] = d["symbol"].astype(str) + "|" + d["date"].astype(str)
    close_d = pd.Series(d["close"].to_numpy(float), index=d["key"])
    sym_s = np.array(syms, dtype=object)[B["sym"]]
    date_s = np.array(dates, dtype=object)[B["day"]]
    rk = pd.Series(sym_s).astype(str) + "|" + pd.Series(date_s).astype(str)
    cd = close_d.reindex(rk.to_numpy()).to_numpy()
    c = B["close"].astype(float)
    rod = (cd / c - 1) * 100
    key = B["day"].astype(np.int64) * 10000 + B["tod"].astype(np.int64)
    fo = B["fromOpen"].astype(float)
    df = pd.DataFrame({"key": key, "up": (fo > 0).astype(float), "vw": (B["vwapDistPct"] > 0).astype(float), "fo": fo,
                       "gap": B["gap"].astype(float), "rvol": B["volumeRatio"].astype(float), "rod": rod})
    g = df.groupby("key")
    ctx = pd.DataFrame({"S1_brd_fo": g["up"].mean(), "S2_brd_vwap": g["vw"].mean(), "S3_med_fo": g["fo"].median(),
                        "S10_med_gap": g["gap"].median(), "S12_gap_disp": g["gap"].std(), "S15_med_rvol": g["rvol"].median(),
                        "S16_sect_disp": g["fo"].std(), "ROD": g["rod"].median(), "n_names": g["up"].size()})
    del df
    ctx["day"] = (ctx.index // 10000).astype(int)
    ctx["tod"] = (ctx.index % 10000).astype(int)
    for nm in ("SPY", "QQQ", "IWM"):
        m = B["sym"] == syms.index(nm)
        s = pd.DataFrame({"key": key[m], "fo": fo[m], "gap": B["gap"][m].astype(float), "c": c[m],
                          "vd": B["vwapDistPct"][m].astype(float), "atr": B["atr_d"][m].astype(float),
                          "rng": (B["dist_hod_atr"][m] + B["dist_lod_atr"][m]).astype(float), "day": B["day"][m],
                          "tod": B["tod"][m]}).set_index("key").sort_index()
        lo = nm.lower()
        ctx[f"{lo}_fo"] = s["fo"].reindex(ctx.index)
        if nm == "SPY":
            vwap = s["c"] / (1 + s["vd"] / 100)
            ctx["S7_spy_z"] = ((s["c"] - vwap) / s["atr"]).reindex(ctx.index)
            prev = vwap.groupby(s["day"]).shift(6)
            ctx["S8_spy_vwslope"] = ((vwap - prev) / s["atr"]).reindex(ctx.index)
            ctx["S9_spy_gap"] = s["gap"].reindex(ctx.index)
            ctx["S13_spy_atrpct"] = (s["atr"] / s["c"] * 100).reindex(ctx.index)
            ctx["S14_spy_orw"] = s["rng"].reindex(ctx.index)
    ctx = ctx.rename(columns={"spy_fo": "S4_spy_fo", "qqq_fo": "S5_qqq_fo", "iwm_fo": "S6_iwm_fo"})
    reg = lib.regimes()
    dts = pd.to_datetime(pd.Series(dates)).dt.date
    med = reg["med_o2c"].reindex(dts.to_numpy()).to_numpy()
    prev = np.r_[np.nan, med[:-1]]
    gapdays = np.r_[99, np.diff(pd.to_datetime(pd.Series(dates)).to_numpy()).astype("timedelta64[D]").astype(int)]
    prev[gapdays > 5] = np.nan
    ctx["S11_prior_o2c"] = prev[ctx["day"].to_numpy()]
    ctx["med_o2c"] = med[ctx["day"].to_numpy()]
    ctx["regime"] = reg["regime"].reindex(dts.to_numpy()).to_numpy()[ctx["day"].to_numpy()]
    ctx["date"] = np.array(dates)[ctx["day"].to_numpy()]
    ctx.reset_index(drop=True).to_parquet(HERE / "data" / "ctx.parquet")
    print(ctx.shape, ctx["n_names"].describe().round(0).to_dict())
    print(ctx[ctx.tod == 1000].drop(columns=["regime", "date"]).describe().T.round(3).to_string())


if __name__ == "__main__":
    main()
