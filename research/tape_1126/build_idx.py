"""TAPE-1126: index / sector 1-min grids (SPY, IWM, 11 sector SPDRs), prior closes, IWM->SPY beta, breadth_vwap on the
5-min grid. Locked block 2024-11-01..2025-02-28 never read (pyarrow filters + asserts). Usage (cwd repo): python build_idx.py W BR
(BR = output dir of research/breadth_1125/build_breadth.py). Educational only - not financial advice."""
import datetime as dt
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.dataset as pads

W, BR = Path(sys.argv[1]), Path(sys.argv[2])
TZ = "America/New_York"; LOCK = ("2024-11-01", "2025-02-28")
HIST, FRESH = Path("/home/user/MCF/data/cache_hist/1Min"), Path("/home/user/MCF/data/cache_fresh/1Min")
SYMS = ["SPY", "IWM", "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if "2025-10-01" <= d <= "2026-11-04":
        return "CHECK"
    if "2023-01-03" <= d <= "2024-09-13":
        return "T2"
    return "none"


def load(sym, src):
    f = pads.field("__index_level_0__")
    flt = (f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))
    b = pads.dataset(str(src / f"{sym}.parquet"), format="parquet").to_table(filter=flt).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    no_locked(np.unique(b.index.date.astype(str)))
    return b


def grids(sym, days):
    out = {}
    for src, ds in ((HIST, [d for d in days if d >= "2024-09-16"]), (FRESH, [d for d in days if d < "2024-09-16"])):
        b = load(sym, src)
        dd = b.index.date.astype(str)
        mm = (b.index.hour * 60 + b.index.minute).to_numpy() - 570
        for d in ds:
            ix = np.flatnonzero((dd == d) & (mm >= 0) & (mm < 390))
            if not len(ix):
                continue
            k = mm[ix]; sub = b.iloc[ix]
            A = np.full((5, 390), np.nan)
            for j, c in enumerate(("open", "high", "low", "close", "volume")):
                A[j, k] = sub[c].to_numpy(float)
            out[d] = A
    return out


def ffill(a):
    return pd.Series(a).ffill().bfill().to_numpy()


if __name__ == "__main__":
    br = pd.read_parquet(BR / "breadth.parquet")
    br["date"] = br.date.astype(str)
    no_locked(br.date.unique())
    br["per"] = br.date.map(period)
    days = sorted(d for d in br.date.unique() if period(d) != "none")
    G = {s: grids(s, days) for s in SYMS}
    days = [d for d in days if d in G["SPY"] and d in G["IWM"]]
    no_locked(days)
    D = len(days)
    # daily closes for prior close and IWM beta
    f = pads.field("date")
    flt = ((f < dt.date(2024, 11, 1)) | (f >= dt.date(2025, 3, 1))) & pads.field("symbol").isin(SYMS)
    a = pads.dataset("/home/user/MCF/research/history2y/data/daily.parquet").to_table(
        filter=flt, columns=["symbol", "date", "close"]).to_pandas()
    b = pd.read_parquet("/home/user/MCF/data/cache_fresh/daily.parquet", columns=["symbol", "date", "close"])
    b = b[b.symbol.isin(SYMS)]
    a["date"] = a.date.astype(str); b["date"] = b.date.astype(str)
    x = pd.concat([b[b.date < "2024-09-16"], a]).drop_duplicates(["symbol", "date"]).sort_values(["symbol", "date"])
    x = x[~((x.date >= LOCK[0]) & (x.date <= LOCK[1]))]
    no_locked(x.date.unique())
    x["dt"] = pd.to_datetime(x.date)
    x["pc"] = x.groupby("symbol").close.shift(1)
    x.loc[x.groupby("symbol").dt.diff().dt.days > 5, "pc"] = np.nan     # never bridge the locked gap
    x["ret"] = x.close / x.pc - 1
    PC = {s: g.set_index("date").pc for s, g in x.groupby("symbol")}
    sp = x[x.symbol == "SPY"].set_index("date").ret; iw = x[x.symbol == "IWM"].set_index("date").ret
    j = pd.concat([iw.rename("r"), sp.rename("m")], axis=1).dropna().sort_index()
    mu = lambda q: q.rolling(60, min_periods=20).mean()  # noqa: E731
    bet = ((mu(j.r * j.m) - mu(j.r) * mu(j.m)) / (mu(j.m * j.m) - mu(j.m) ** 2)).shift(1)
    biw = np.array([bet.get(d, np.nan) for d in days]); biw = np.where(np.isfinite(biw), biw, 1.2)
    out = {"days": np.array(days), "biw": biw}
    for s in SYMS:
        A = np.full((D, 5, 390), np.nan)
        for i, d in enumerate(days):
            if d in G[s]:
                A[i] = G[s][d]
        O, H, L, C, V = A[:, 0], A[:, 1], A[:, 2], A[:, 3], A[:, 4]
        has = np.isfinite(C)
        first = np.where(has.any(1), O[np.arange(D), np.argmax(has, 1)], np.nan)
        Cf = np.stack([ffill(c) if np.isfinite(c).any() else c for c in C])
        Of = np.where(np.isfinite(O), O, Cf)
        Hf = np.where(np.isfinite(H), H, Cf); Lf = np.where(np.isfinite(L), L, Cf)
        v = np.where(has, V, 0.0); tp = np.where(has, (H + L + C) / 3, 0.0)
        cv = np.cumsum(v, 1); vw = np.where(cv > 0, np.cumsum(tp * v, 1) / np.maximum(cv, 1e-9), Cf)
        pc = np.array([PC.get(s, pd.Series(dtype=float)).get(d, np.nan) for d in days])
        out[s] = np.stack([Of, Hf, Lf, Cf, vw]).astype(np.float64)   # 5 x D x 390
        out[s + "_open"] = first; out[s + "_pc"] = pc
    # breadth pct_vwap on the 5-min grid T = 09:50..15:00 (bars < T)
    T = sorted(br["T"].unique())
    pv = br.pivot_table(index="date", columns="T", values="pct_vwap").reindex(days)
    out["brT"] = np.array(T); out["brv"] = pv.to_numpy(float)
    np.savez(W / "idx.npz", **out)
    print("days", D, {p: sum(period(d) == p for d in days) for p in ("FIT", "CHECK", "T2")},
          "breadth NaN share %.3f" % np.isnan(out["brv"]).mean(), "IWM beta median %.2f" % np.median(biw))
