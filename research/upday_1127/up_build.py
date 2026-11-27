"""UPDAY_1127 build (PREREG.md): per symbol-day candidate long trades for SQZ / RSL / GUP (filters that need a cross-section
or SPY gate are applied in up_score.py), exits HOLD (15:55) and TRAIL, stress (+1 bar entry), plus the eligible
symbol-day list for the random control. Locked block 2024-11-01..2025-02-28 never read (pyarrow filter + assert).
Usage: python up_build.py OUTDIR. Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads
from numba import njit

TZ = "America/New_York"
LOCK = ("2024-11-01", "2025-02-28")
SRC = {"t1": Path("/home/user/MCF/data/cache_hist/1Min"), "t2": Path("/home/user/MCF/data/cache_fresh/1Min")}
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def load(p):
    f = pads.field("__index_level_0__")
    flt = (f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))
    b = pads.dataset(str(p), format="parquet").to_table(filter=flt).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    mm = (b.index.hour * 60 + b.index.minute).to_numpy() - 570
    b = b[(mm >= 0) & (mm < 390)]
    no_locked(np.unique(b.index.date.astype(str)))
    return b


@njit(cache=True)
def walk(o, h, l, c, i0, ie, stop, trail):
    """long from o[i0] to c[ie]; stop-first; gap through stop fills at open. trail: once +1R, stop = best high - 1R
    (updated after each bar, used from the next bar). returns (px, kind 1=stop 0=time)."""
    e = o[i0]; risk = e - stop; best = -1e18
    for i in range(i0, ie + 1):
        if o[i] <= stop:
            return o[i], 1
        if l[i] <= stop:
            return stop, 1
        if trail:
            if h[i] > best:
                best = h[i]
            if best - e >= risk:
                ns = best - risk
                if ns > stop:
                    stop = ns
    return c[ie], 0


def daily(b):
    dates = b.index.date.astype(str)
    mm = (b.index.hour * 60 + b.index.minute).to_numpy() - 570
    g = pd.DataFrame({"d": dates, "o": b.open.to_numpy(), "h": b.high.to_numpy(), "l": b.low.to_numpy(),
                      "c": b.close.to_numpy(), "dv": (b.close * b.volume).to_numpy(),
                      "v20": np.where(mm < 20, b.volume.to_numpy(), 0.0), "n20": (mm < 20).astype(int)})
    D = g.groupby("d").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"), dv=("dv", "sum"),
                           v20=("v20", "sum"), n20=("n20", "sum"))
    dt = pd.to_datetime(D.index)
    seg = np.r_[0, np.cumsum(np.diff(dt.values).astype("timedelta64[D]").astype(int) > 7)]
    D["seg"] = seg
    pc = D.groupby("seg").c.shift(1)
    tr = np.maximum(D.h, pc) - np.minimum(D.l, pc)
    D["pc"] = pc
    gs = D.assign(tr=tr).groupby("seg")
    D["atr"] = gs.tr.transform(lambda s: s.shift(1).rolling(14, min_periods=14).mean())
    D["adv20"] = gs.dv.transform(lambda s: s.shift(1).rolling(20, min_periods=20).mean())
    D["ret20"] = gs.c.transform(lambda s: s.shift(1) / s.shift(21) - 1)
    D["v20med"] = gs.v20.transform(lambda s: s.shift(1).rolling(20, min_periods=20).median())
    return D


def work(args):
    tag, sym, spy = args
    try:
        b = load(SRC[tag] / f"{sym}.parquet")
    except Exception as ex:  # noqa: BLE001
        return None
    if len(b) < 1000:
        return None
    D = daily(b)
    mmall = (b.index.hour * 60 + b.index.minute).to_numpy() - 570
    dates = b.index.date.astype(str)
    O, H, L, C, V = (b[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
    starts = np.flatnonzero(np.r_[True, dates[1:] != dates[:-1]])
    ends = np.r_[starts[1:], len(dates)]
    trades, elig = [], []
    for s, e in zip(starts, ends):
        d = dates[s]
        r = D.loc[d]
        if not (r.adv20 >= 20e6) or not (r.atr == r.atr) or r.n20 < 15 or not (r.pc == r.pc):
            continue
        o, h, l, c, v, mm = O[s:e], H[s:e], L[s:e], C[s:e], V[s:e], mmall[s:e]
        if mm[0] != 0 or not (mm >= 20).any():
            continue
        ie_c = np.flatnonzero(mm <= 385)
        if not len(ie_c):
            continue
        ie = ie_c[-1]
        op = o[0]; gap = op / r.pc - 1; atr = r.atr
        tp = (h + l + c) / 3
        cv = np.cumsum(v); vw = np.where(cv > 0, np.cumsum(tp * v) / np.maximum(cv, 1e-9), c)
        w20 = mm < 20
        i49 = np.flatnonzero(w20)[-1]
        c49 = c[i49]; r50 = c49 / op - 1
        rvol = r.v20 / r.v20med if r.v20med and r.v20med > 0 else np.nan
        elig.append((sym, d, tag, op, atr, r.adv20, r.ret20))
        lowcum = np.minimum.accumulate(l)
        base = dict(symbol=sym, date=d, tag=tag, gap=gap, atr=atr, adv20=r.adv20, ret20=r.ret20, rvol=rvol,
                    r50=r50, spy_r50=spy.get(d, np.nan))
        cands = []
        # SQZ
        if gap <= -0.01:
            m1 = (mm >= 20) & (mm < 60)
            if m1.sum() >= 20 and (c[m1] < vw[m1]).all():
                sig = np.flatnonzero((mm >= 60) & (mm <= 240) & (c > vw))
                if len(sig):
                    k = sig[0]
                    vmed = np.median(v[:k + 1])
                    cands.append(("SQZ", k, lowcum[k] - 0.01, dict(sig_mm=int(mm[k]),
                                                                    vratio=v[k] / vmed if vmed > 0 else np.nan)))
        # RSL
        spr = spy.get(d, np.nan)
        if spr == spr and r50 - spr >= 0.005 and l[w20].min() < op:
            if c49 > op:
                k = i49
            else:
                sig = np.flatnonzero((mm >= 20) & (mm <= 120) & (c > op))
                k = sig[0] if len(sig) else -1
            if k >= 0:
                cands.append(("RSL", k, lowcum[k] - 0.01, dict(sig_mm=int(mm[k]), rs=r50 - spr)))
        # GUP
        if gap >= 0.02 and c49 > vw[i49]:
            idx = np.flatnonzero(mm >= 20)
            for k in idx:
                if mm[k] > 150:
                    break
                if c[k] <= vw[k]:
                    break
                if mm[k] >= 30 and l[k] <= vw[k] * 1.001:
                    cands.append(("GUP", k, min(l[k], vw[k]) - 0.10 * atr, dict(sig_mm=int(mm[k]))))
                    break
        for fam, k, stop, extra in cands:
            i0 = k + 1
            if i0 > ie:
                continue
            ent = o[i0]; risk = ent - stop
            if ent < 5 or risk < 0.001 * ent or risk > atr:
                continue
            px_h, k_h = walk(o, h, l, c, i0, ie, stop, False)
            px_t, k_t = walk(o, h, l, c, i0, ie, stop, True)
            rec = dict(base, fam=fam, em=int(mm[i0]), entry=ent, stop=stop, risk=risk,
                       px_h=px_h, k_h=k_h, px_t=px_t, k_t=k_t, **extra)
            if i0 + 1 <= ie and o[i0 + 1] - stop > 0:
                e2 = o[i0 + 1]
                rec["e_s"] = e2
                rec["px_hs"], rec["k_hs"] = walk(o, h, l, c, i0 + 1, ie, stop, False)
                rec["px_ts"], rec["k_ts"] = walk(o, h, l, c, i0 + 1, ie, stop, True)
            trades.append(rec)
    return pd.DataFrame(trades), pd.DataFrame(elig, columns=["symbol", "date", "tag", "open", "atr", "adv20", "ret20"])


def spy_info():
    rows = []
    for tag in ("t2", "t1"):
        b = load(SRC[tag] / "SPY.parquet")
        mm = (b.index.hour * 60 + b.index.minute).to_numpy() - 570
        d = b.index.date.astype(str)
        g = pd.DataFrame({"d": d, "mm": mm, "o": b.open.to_numpy(), "c": b.close.to_numpy()})
        for dd, x in g.groupby("d"):
            if x.mm.iloc[0] != 0 or not (x.mm < 20).any():
                continue
            c49 = x.c[x.mm < 20].iloc[-1]
            rows.append((dd, tag, x.o.iloc[0], c49, x.c.iloc[-1]))
    s = pd.DataFrame(rows, columns=["date", "tag", "o", "c49", "cl"]).drop_duplicates("date", keep="last")
    s["r50"] = s.c49 / s.o - 1
    s["oc"] = s.cl / s.o - 1
    return s


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    S = spy_info(); no_locked(S.date)
    S.to_csv(OUT / "spy_days.csv", index=False)
    spy = dict(zip(S.date, S.r50))
    jobs = [(tag, p.stem, spy) for tag in ("t1", "t2") for p in sorted(SRC[tag].glob("*.parquet"))]
    T, E = [], []
    with Pool(4) as pool:
        for n, res in enumerate(pool.imap_unordered(work, jobs, chunksize=4)):
            if res is not None:
                T.append(res[0]); E.append(res[1])
            if n % 200 == 0:
                print(n, len(jobs), flush=True)
    T = pd.concat([t for t in T if len(t)], ignore_index=True); E = pd.concat(E, ignore_index=True)
    no_locked(T.date.unique()); no_locked(E.date.unique())
    T.to_parquet(OUT / "cands.parquet"); E.to_parquet(OUT / "elig.parquet")
    print("cands", len(T), T.fam.value_counts().to_dict(), "elig", len(E))
