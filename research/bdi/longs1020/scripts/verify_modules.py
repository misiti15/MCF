"""Parity: every longs1020 near-miss module (LD1-LD8) vs the research scan's signals, open history only.
Educational only - not financial advice.

Two frame shapes per module:
- "offline": the lab frames as stored (they start at the 09:50 bar).
- "live_shape": the same frames plus the 09:35 / 09:40 / 09:45 rows a live frame has, carrying only the SPY / QQQ
  context (spy_fo / qqq_fo from the scan's own 5-minute SPY / QQQ bars, idx5.parquet); every stock feature and breadth
  is NaN there (the scan had no breadth before 09:50 either). This is the shape the scan's index running low used
  ("since 09:35"), so it is the exact-reproduction check.
Stock modules (LD1, LD3, LD4, LD5, LD7): first bar per symbol-day where mask & finite r_long_t1s1, adv20 >= $95M, vs
b_trades.parquet. ETF modules (LD2 TQQQ, LD6 / LD8 SPXL): module signals on the ETF's rows vs trades_A.csv.gz.
LD6 also runs with the scan's exact SPY ATR% (SPY atr_d / SPY 09:50 close) in place of the SPXL-based estimate, to
separate the estimate's effect from the logic."""
import importlib.util
import json

import numpy as np
import pandas as pd

from common import HERE, SCR, lib
from mcf.research import gates

MODS = {
    "LD1": ("LD1-ns1-breadthup-t05s1-long", "B5-NS1-BRDUP"),
    "LD3": ("LD3-st2-idxturn-t05s1-long", "B5-ST2-IDXTURN"),
    "LD4": ("LD4-st4-breadthup-t1s05-long", "B5-ST4-BRDUP"),
    "LD5": ("LD5-st2-breadthup-t05s1-long", "B5-ST2-BRDUP"),
    "LD7": ("LD7-ns1-idxturn-holdtr-long", "B5-NS1-IDXTURN"),
}
ETF = {
    "LD2": ("LD2-qqq-dip015-breadthturn-tqqq-t05s1-long", "A-QQQ-abs015-brd-t05s1", "TQQQ"),
    "LD6": ("LD6-spy-dip020atr-breadthturn-spxl-holdtr-long", "A-SPY-rel020-brd-holdtr", "SPXL"),
    "LD8": ("LD8-spy-dip030-breadthturn-spxl-holdtr-long", "A-SPY-abs030-brd-holdtr", "SPXL"),
}
COLS = ["symbol", "date", "tod", "close", "rsi", "rsi5", "fromOpen", "vwapDistPct", "atr_d", "sma20_slope_pct",
        "buyPressure", "emaDiff", "adv20", "r_long_t1s1"]


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / "modules" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def early_rows(df, idx5):
    """09:35-09:45 rows per symbol-day of df with spy_fo / qqq_fo from the scan's 5-minute index bars."""
    sd = df[["symbol", "date"]].drop_duplicates()
    e = idx5[idx5.tod.isin([935, 940, 945])].pivot_table(index=["date", "tod"], columns="sym", values="fo").reset_index()
    e = e.rename(columns={"SPY": "spy_fo", "QQQ": "qqq_fo"})[["date", "tod", "spy_fo", "qqq_fo"]]
    x = sd.merge(e, on="date", how="inner")
    out = pd.concat([df, x], ignore_index=True)
    return out.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)


def main():
    idx5 = pd.read_parquet(SCR / "idx5.parquet")
    idx5["date"] = pd.to_datetime(idx5["date"]).dt.date
    T = pd.read_parquet(SCR / "b_trades.parquet")
    T["date"] = pd.to_datetime(T["date"]).dt.date
    A = pd.read_csv(HERE / "trades_A.csv.gz")
    etf = pd.read_parquet(SCR / "etf_rows.parquet")
    etf["date"] = pd.to_datetime(etf["date"]).dt.date
    e0 = etf.sort_values(["symbol", "date", "tod"]).groupby(["symbol", "date"]).agg(atr=("atr_d", "first"), c0=("close", "first"))
    spy_atrp = (e0.loc["SPY", "atr"] / e0.loc["SPY", "c0"] * 100)
    spxl_c0 = e0.loc["SPXL", "c0"]
    ratio = (e0.loc["SPXL", "atr"] / e0.loc["SPXL", "c0"] * 100 / spy_atrp).dropna()
    mods = {k: load(v[0]) for k, v in {**MODS, **ETF}.items()}
    got = {k: {"offline": set(), "live_shape": set()} for k in mods}
    got["LD6"]["live_shape_exact_spy_atr"] = set()
    months = [m for m in lib.months() if m not in lib.LOCKED_MONTHS]
    for mo in months:
        df = lib.load_month(mo, columns=COLS, context=True)
        etfdf = {s: df[df.symbol == s].reset_index(drop=True) for s in ("SPXL", "TQQQ")}
        df = df[df.adv20 >= 95e6].reset_index(drop=True)
        for shape in ("offline", "live_shape"):
            d = df if shape == "offline" else early_rows(df, idx5)
            ok = np.isfinite(d.r_long_t1s1.to_numpy())
            for k in MODS:
                i = gates.first_per_symbol_day(d.symbol.to_numpy(), d.date.to_numpy(), mods[k].mask(d) & ok)
                got[k][shape] |= set(zip(d.symbol.to_numpy()[i], d.date.to_numpy()[i], d.tod.to_numpy()[i].astype(int)))
            for k, (_, _, sym) in ETF.items():
                x = etfdf[sym] if shape == "offline" else early_rows(etfdf[sym], idx5)
                mk = mods[k].mask(x)
                got[k][shape] |= set(zip(x.date.astype(str)[mk], x.tod[mk].astype(int)))
                if k == "LD6" and shape == "live_shape":
                    y = x.copy()       # exact SPY ATR%: atr_d such that atr_d / close950 * 100 / ratio == SPY ATR%
                    y["atr_d"] = y["date"].map(spy_atrp).to_numpy() * y["date"].map(spxl_c0).to_numpy() / 100 * mods[k].SPXL_SPY_ATR
                    mk = mods[k].mask(y)
                    got[k]["live_shape_exact_spy_atr"] |= set(zip(y.date.astype(str)[mk], y.tod[mk].astype(int)))
        print(mo, flush=True)
    out = {"_note": __doc__.split("\n\n", 1)[1], "months": months,
           "spxl_spy_atr_ratio": {"median": round(float(ratio.median()), 4),
                                  "p05": round(float(ratio.quantile(0.05)), 4), "p95": round(float(ratio.quantile(0.95)), 4),
                                  "train_median": round(float(ratio[[d <= pd.Timestamp("2025-12-31").date() for d in ratio.index]].median()), 4)}}
    for k, (mod, base) in MODS.items():
        b = set(zip(T[T.base == base].symbol, T[T.base == base].date, T[T.base == base].tod.astype(int)))
        out[k] = {"module": mod, "scan_cfg": base, "scan": len(b)}
        for shape, a in got[k].items():
            out[k][shape] = {"module": len(a), "both": len(a & b), "module_only": sorted(map(str, a - b))[:10],
                             "scan_only": sorted(map(str, b - a))[:10]}
    for k, (mod, cfg, sym) in ETF.items():
        t = A[A.cfg == cfg]
        b = set(zip(t.date.astype(str), t.tod.astype(int)))
        out[k] = {"module": mod, "scan_cfg": cfg, "instrument": sym, "scan": len(b)}
        for shape, a in got[k].items():
            out[k][shape] = {"module": len(a), "both": len(a & b), "module_only": sorted(map(str, a - b))[:10],
                             "scan_only": sorted(map(str, b - a))[:10]}
    json.dump(out, open(HERE / "verify_modules.json", "w"), indent=1, default=str)
    for k in sorted(out):
        if k.startswith("LD"):
            print(k, out[k]["scan"], {s: (v["module"], v["both"]) for s, v in out[k].items() if isinstance(v, dict)})
    print(out["spxl_spy_atr_ratio"])


if __name__ == "__main__":
    main()
