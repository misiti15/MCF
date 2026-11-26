"""TAPE-1126 H2 trapped-short gap reclaim long + same-minute random universe control (PREREG.md config 7).
Usage (cwd repo): python h2.py W  (needs W/idx.npz). Locked block never read (filters + asserts).
Educational only - not financial advice."""
import datetime as dt
import json
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.dataset as pads

sys.path.insert(0, "research/primshorts_1126")
import calib_live as CL  # noqa: E402

W = Path(sys.argv[1])
TZ = "America/New_York"; LOCK = ("2024-11-01", "2025-02-28")
HIST, FRESH = Path("/home/user/MCF/data/cache_hist/1Min"), Path("/home/user/MCF/data/cache_fresh/1Min")
FLAT = 384


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


def universe():
    f = pads.field("date")
    flt = (f < dt.date(2024, 11, 1)) | (f >= dt.date(2025, 3, 1))
    cols = ["symbol", "date", "open", "high", "low", "close", "adv20"]
    a = pads.dataset("/home/user/MCF/research/history2y/data/daily.parquet").to_table(filter=flt, columns=cols).to_pandas()
    b = pd.read_parquet("/home/user/MCF/data/cache_fresh/daily.parquet", columns=cols)
    a["date"] = a.date.astype(str); b["date"] = b.date.astype(str)
    x = pd.concat([b[b.date < "2024-09-16"], a]).drop_duplicates(["symbol", "date"]).sort_values(["symbol", "date"])
    x = x[~((x.date >= LOCK[0]) & (x.date <= LOCK[1]))]
    no_locked(x.date.unique())
    x["dt"] = pd.to_datetime(x.date)
    g = x.groupby("symbol")
    brk = g.dt.diff().dt.days > 5
    x["pc"] = g.close.shift(1); x.loc[brk, "pc"] = np.nan
    tr = np.maximum(x.high - x.low, np.maximum((x.high - x.pc).abs(), (x.low - x.pc).abs()))
    x["tr"] = tr
    x["atr"] = x.groupby("symbol").tr.transform(lambda s: s.rolling(14, min_periods=10).mean().shift(1))
    x["adv"] = g.adv20.shift(1)
    x["gap"] = x.open / x.pc - 1
    x["per"] = x.date.map(period)
    u = x[(x.per != "none") & (x.gap <= -0.02657) & (x.adv >= 95e6) & (x.open >= 5) & x.atr.gt(0)].copy()
    return u[["symbol", "date", "per", "pc", "atr", "gap"]]


def job(args):
    sym, ds = args
    out = []
    for src, sub in ((HIST, [d for d in ds if d >= "2024-09-16"]), (FRESH, [d for d in ds if d < "2024-09-16"])):
        p = src / f"{sym}.parquet"
        if not sub or not p.exists():
            continue
        f = pads.field("__index_level_0__")
        flt = (f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))
        b = pads.dataset(str(p), format="parquet").to_table(filter=flt).to_pandas()
        if "__index_level_0__" in b.columns:
            b = b.set_index("__index_level_0__")
        b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
        dd = b.index.date.astype(str)
        no_locked(np.unique(dd))
        mm = (b.index.hour * 60 + b.index.minute).to_numpy() - 570
        for d in sub:
            ix = np.flatnonzero((dd == d) & (mm >= 0) & (mm < 390))
            if len(ix) < 30:
                continue
            A = np.full((4, 390), np.nan)
            for j, c in enumerate(("open", "high", "low", "close")):
                A[j, mm[ix]] = b[c].to_numpy(float)[ix]
            Cf = pd.Series(A[3]).ffill().bfill().to_numpy()
            A[0] = np.where(np.isfinite(A[0]), A[0], Cf); A[1] = np.where(np.isfinite(A[1]), A[1], Cf)
            A[2] = np.where(np.isfinite(A[2]), A[2], Cf); A[3] = Cf
            out.append((sym, d, A.astype(np.float32)))
    return out


def trade(A, t, pc, atr):
    """H2 exit rules from entry at the open of minute t. -> (gross R, exit kind, entry, risk) or None (skip)."""
    O, H, L, C = A
    e = float(O[t]); lo = float(np.min(L[:t]))
    if e - lo < 0.15 * atr or e >= pc:
        return None
    st = max(lo, e - 0.5 * atr); risk = e - st
    for j in range(t, FLAT + 1):
        if L[j] <= st:
            return (min(st, O[j]) - e) / risk, "stop", e, risk
        if H[j] >= pc:
            return (max(pc, O[j]) - e) / risk, "target", e, risk
    return (C[FLAT] - e) / risk, "market", e, risk


if __name__ == "__main__":
    U = universe()
    Z = np.load(W / "idx.npz"); days = Z["days"].astype(str); pos = {d: i for i, d in enumerate(days)}
    U = U[U.date.isin(pos)]
    print("universe symbol-days", len(U), U.groupby("per").size().to_dict(), flush=True)
    bars = {}
    with Pool(2) as p:
        for res in p.imap_unordered(job, [(s, sorted(g.date)) for s, g in U.groupby("symbol")], chunksize=4):
            for s, d, A in res:
                bars[(s, d)] = A
    U = U[[(s, d) in bars for s, d in zip(U.symbol, U.date)]].reset_index(drop=True)
    SC, SV = Z["SPY"][3], Z["SPY"][4]
    cells = json.load(open("research/primshorts_1126/cells_live.json"))
    sig = []
    for r in U.itertuples():
        A = bars[(r.symbol, r.date)]; O, H, L, C = A; o = float(O[0]); i = pos[r.date]
        for t in range(60, 301, 5):
            if C[t - 1] > o and np.min(L[:t]) <= o - 0.5 * r.atr and SC[i, t - 1] >= SV[i, t - 1]:
                sig.append((r.date, r.per, r.symbol, t, r.pc, r.atr)); break
    S = pd.DataFrame(sig, columns=["date", "per", "symbol", "t", "pc", "atr"]).sort_values(["date", "t", "symbol"])
    S = S.groupby("date").head(10).reset_index(drop=True)
    res = [trade(bars[(r.symbol, r.date)], r.t, r.pc, r.atr) for r in S.itertuples()]
    S["ok"] = [x is not None for x in res]
    S = S[S.ok].copy(); res = [x for x in res if x is not None]
    S["rg"] = [x[0] for x in res]; S["kind"] = [x[1] for x in res]; S["entry"] = [x[2] for x in res]; S["risk"] = [x[3] for x in res]
    S["r"] = S.rg - CL.predict_R(cells, S.entry.to_numpy(), S.risk.to_numpy(), S.kind.to_numpy())
    no_locked(S.date.unique())
    S.drop(columns=["ok"]).to_parquet(W / "h2_trades.parquet", index=False)
    # same-minute random universe control, 20 draws
    byday = U.groupby("date")
    rng = np.random.default_rng(1126)
    ctl = []
    for k in range(20):
        for r in S.itertuples():
            g = byday.get_group(r.date); g = g[g.symbol != r.symbol]
            if not len(g):
                continue
            for _ in range(20):
                q = g.iloc[int(rng.integers(len(g)))]
                x = trade(bars[(q.symbol, r.date)], r.t, q.pc, q.atr)
                if x is not None:
                    ctl.append((k, r.date, r.per, q.symbol, r.t, x[0], x[1], x[2], x[3])); break
    Q = pd.DataFrame(ctl, columns=["draw", "date", "per", "symbol", "t", "rg", "kind", "entry", "risk"])
    Q["r"] = Q.rg - CL.predict_R(cells, Q.entry.to_numpy(), Q.risk.to_numpy(), Q.kind.to_numpy())
    Q.to_parquet(W / "h2_control.parquet", index=False)
    print(S.groupby("per").r.agg(["count", "mean"]), Q.groupby("per").r.agg(["count", "mean"]))
