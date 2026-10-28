"""htf1028: two-year scan (open history 2024-10..2026-10-07; the rule-19 locked block 2024-11-01..2025-02-28 is never
loaded: lib.months() lists open months only, lib.load_month refuses locked months, the daily file and the head/tail
file are read with a date filter that excludes the block, MCF_HIST_ALLOW_LOCKED is asserted unset). No holdout scored.

1. htf1028-mss-pullback (long and short): HTF-aligned 30-minute market-structure shift, limit entry on a pullback
   into the shift leg. 16 configurations = side {long, short} x swing k {2, 3} x target {1.5R, 2R} x entry {38.2%, 50%}.
2. htf1028-coil-k4-trendfilter: per-trade HTF / market features for the CWT12-coil-k4-long parent trades from
   research/bdi/hf1027/scan_hf.py (var P; same kernel, sim and cost model as top5_1021) -> scored in eval_htf.py.

Definitions (fixed before the run):
- 5-minute RTH path = lab frames (09:50-15:00) + head/tail rows (09:35-09:45, 15:05-15:55); bar `tod` = bar close.
- 30-minute bars anchored 09:30 (closes 10:00 .. 15:30, last bar 15:30-15:55); 60-minute bars anchored 09:30
  (10:30 .. 15:30, last 15:30-15:55). Bar series run across consecutive sessions of a symbol (break if > 5 calendar
  days apart, so nothing spans the locked block).
- Stock HTF up: prior-day close > SMA20 of daily closes through the prior day (20 rows spanning <= 40 calendar days)
  AND the last two confirmed 60-minute pivot lows (k = 1, pivot confirmed by the next completed hour) are rising.
  Down = mirror (close < SMA20, last two 60-minute pivot highs falling). Uses only bars completed by the signal time.
- Swing high (k bars): high strictly above the k bars on each side; confirmed k bars later.
- Long shift at a 30-minute close t (close tod 10:30..15:00, i.e. signals 10:10-15:00): j = the last confirmed swing
  high (j + k <= t - 1, within today + prior session), i = the last swing low before j; closes j+1..t-1 <= high[j];
  low(j+1..t) < low[i] (lower low); close[t] > high[j]. Shift low LL = low(j+1..t).
  Entry limit L = close[t] - p x (close[t] - LL); location: L <= midpoint of today's range so far, or <= the prior
  day's midpoint. Stop = LL - $0.01. Target = L + tgt x R. Short = mirror.
- Fill: first 5-minute bar after the shift bar with tod <= 15:00 whose low < L (trade-through, strict) fills at L.
  The fill bar is checked for the stop only (worst case); then stop-first per bar, target, flat at the 15:55 close.
  First signal per symbol-day-side only (an unfilled order is not replaced). ADV20 >= $95M, daily ATR > 0.
- Costs (as the lab harness, scan_1019.sim): entry 1c + 1 bp x the time-of-day multiplier, stop exits 1c + 1 bp + 2c,
  clock exits 1c + 1 bp, target exits free.

Usage: python scan_htf.py -> <scratch>/htf1028/{mss,coilfeat}.parquet     Educational only - not financial advice.
"""
from __future__ import annotations

import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/htf1028")
HT = ROOT / "research" / "bdi" / "cwt" / "test_b" / "data" / "headtail.parquet"
COIL = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/hf/coil2y.parquet")
LK0, LK1 = pd.Timestamp(lib.LOCKED[0]), pd.Timestamp(lib.LOCKED[1])
ADV = 95e6
VARIANTS = [(side, k, tgt, p) for side in (1, -1) for k in (2, 3) for tgt in (1.5, 2.0) for p in (0.382, 0.5)]


def daily_feats() -> pd.DataFrame:
    d = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "high", "low", "close"],
                        filters=[[("date", "<", LK0.date())], [("date", ">", LK1.date())]])
    d["date"] = pd.to_datetime(d["date"])
    assert not ((d.date >= LK0) & (d.date <= LK1)).any()
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    g = d.groupby("symbol", sort=False)
    sma = g["close"].transform(lambda x: x.rolling(20).mean())
    span = (d["date"] - g["date"].shift(19)).dt.days
    d["sma20"] = np.where(span <= 40, sma, np.nan)
    out = pd.DataFrame({"symbol": d.symbol, "date": d.date})
    for c in ("close", "sma20", "high", "low"):
        out["p_" + c] = g[c if c != "sma20" else "close"].shift(1) if c != "sma20" else d.groupby("symbol")["sma20"].shift(1)
    gap = (d["date"] - g["date"].shift(1)).dt.days
    out.loc[~(gap <= 5), ["p_close", "p_sma20", "p_high", "p_low"]] = np.nan
    out["date"] = out["date"].dt.date
    return out


def load_path(month: str) -> pd.DataFrame:
    assert month not in lib.LOCKED_MONTHS
    f = lib.load_month(month, columns=["symbol", "date", "tod", "high", "low", "close", "atr_d", "adv20"])
    f["symbol"] = f["symbol"].astype(str)
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(HT, filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
    ht = ht[(ht.tod < 950) | (ht.tod > 1500)]
    ht["symbol"] = ht["symbol"].astype(str)
    ht["date"] = pd.to_datetime(ht["date"]).dt.date
    day = f.groupby(["symbol", "date"], sort=False).agg(atr_d=("atr_d", "first"), adv20=("adv20", "first")).reset_index()
    ht = ht.rename(columns={"h": "high", "l": "low", "c": "close"}).merge(day, on=["symbol", "date"], how="inner")
    P = pd.concat([f, ht[["symbol", "date", "tod", "high", "low", "close", "atr_d", "adv20"]]], ignore_index=True)
    P["tod"] = P["tod"].astype(np.int32)
    return P.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)


def bars(P: pd.DataFrame, mins: int) -> pd.DataFrame:
    t = P["tod"].to_numpy()
    m = (t // 100) * 60 + t % 100 - 570
    b = (m - 5) // mins
    B = P.assign(b=b).groupby(["symbol", "date", "b"], sort=True).agg(
        high=("high", "max"), low=("low", "min"), close=("close", "last"), etod=("tod", "last"), n=("tod", "size")).reset_index()
    full_end = 570 + (B["b"].to_numpy() + 1) * mins
    B["end"] = np.minimum((full_end // 60) * 100 + full_end % 60, 1555)
    return B


def series_index(B: pd.DataFrame):
    """seg (contiguous sessions of one symbol), session start row, prior-session start row (same seg)."""
    sym = B["symbol"].to_numpy()
    dt = pd.to_datetime(B["date"]).to_numpy()
    n = len(B)
    newsess = np.r_[True, (sym[1:] != sym[:-1]) | (dt[1:] != dt[:-1])]
    gapd = np.r_[np.inf, (dt[1:] - dt[:-1]) / np.timedelta64(1, "D")]
    newseg = np.r_[True, sym[1:] != sym[:-1]] | (newsess & (gapd > 5))
    seg = np.cumsum(newseg)
    ss_idx = np.flatnonzero(newsess)
    sess_no = np.cumsum(newsess) - 1
    sstart = ss_idx[sess_no]
    prev = np.r_[ss_idx[0], ss_idx[:-1]][sess_no]
    prev_start = np.where(seg[prev] == seg, prev, sstart)
    prev_start[sess_no == 0] = sstart[sess_no == 0]
    return seg, sstart, prev_start


@numba.njit(cache=True)
def hourly_state(h, l, seg):
    """For each completed hourly bar e: +1 if the last two confirmed pivot lows rise (HL), and separately -1 state
    if the last two confirmed pivot highs fall (LH). k = 1, pivot i confirmed when bar i+1 completes."""
    n = len(h)
    hl = np.zeros(n, np.bool_)
    lh = np.zeros(n, np.bool_)
    pl1 = np.nan; pl2 = np.nan; ph1 = np.nan; ph2 = np.nan
    for e in range(n):
        if e == 0 or seg[e] != seg[e - 1]:
            pl1 = np.nan; pl2 = np.nan; ph1 = np.nan; ph2 = np.nan
        i = e - 1
        if i - 1 >= 0 and seg[i - 1] == seg[e]:
            if l[i] < l[i - 1] and l[i] < l[e]:
                pl2 = pl1; pl1 = l[i]
            if h[i] > h[i - 1] and h[i] > h[e]:
                ph2 = ph1; ph1 = h[i]
        hl[e] = pl1 > pl2
        lh[e] = ph1 < ph2
    return hl, lh


@numba.njit(cache=True)
def mss(h, l, c, sstart, pstart, k, side):
    """Long (side 1): shift flag and shift low per 30-minute bar t. Short: mirror (flag, shift high)."""
    n = len(h)
    flag = np.zeros(n, np.bool_)
    ext = np.full(n, np.nan)
    for t in range(n):
        lo = pstart[t]
        # last confirmed swing high (long) / low (short) j with j + k <= t - 1
        j = -1
        for jj in range(t - 1 - k, lo + k - 1, -1):
            ok = True
            for m in range(1, k + 1):
                if side == 1:
                    if not (h[jj] > h[jj - m] and h[jj] > h[jj + m]):
                        ok = False; break
                else:
                    if not (l[jj] < l[jj - m] and l[jj] < l[jj + m]):
                        ok = False; break
            if ok:
                j = jj
                break
        if j < 0:
            continue
        lvl = h[j] if side == 1 else l[j]
        if not (side * (c[t] - lvl) > 0):
            continue
        bad = False
        for q in range(j + 1, t):
            if side * (c[q] - lvl) > 0:
                bad = True; break
        if bad:
            continue
        # swing low (long) / high (short) i < j
        i = -1
        for ii in range(j - 1, lo + k - 1, -1):
            if ii + k > t - 1:
                continue
            ok = True
            for m in range(1, k + 1):
                if side == 1:
                    if not (l[ii] < l[ii - m] and l[ii] < l[ii + m]):
                        ok = False; break
                else:
                    if not (h[ii] > h[ii - m] and h[ii] > h[ii + m]):
                        ok = False; break
            if ok:
                i = ii
                break
        if i < 0:
            continue
        x = l[j + 1] if side == 1 else h[j + 1]
        for q in range(j + 1, t + 1):
            x = min(x, l[q]) if side == 1 else max(x, h[q])
        if side * (x - (l[i] if side == 1 else h[i])) < 0:
            flag[t] = True
            ext[t] = x
    return flag, ext


@numba.njit(cache=True)
def _mult(t):
    if t < 935:
        return 3.8
    if t < 950:
        return 2.1
    if t < 1030:
        return 1.4
    return 1.0


@numba.njit(cache=True)
def sim_limit(h, l, c, tod, start, dend, L, S, side, up):
    """Limit entry at L from row start (rows with tod <= 1500); stop S; target L + side*up*R; flat at the 15:55 close.
    Returns r after costs, code (0 unfilled, 1 target, 2 stop, 6 flat), fill tod, exit row."""
    n = len(start)
    r = np.full(n, np.nan); code = np.zeros(n, np.int8); ftod = np.zeros(n, np.int32); xr = np.full(n, -1, np.int64)
    for q in range(n):
        s0 = start[q]
        if s0 < 0:
            continue
        end = dend[s0]
        R = side * (L[q] - S[q])
        if not (R > 0):
            continue
        j = -1
        for k in range(s0, end + 1):
            if tod[k] > 1500:
                break
            if (side == 1 and l[k] < L[q]) or (side == -1 and h[k] > L[q]):
                j = k
                break
        if j < 0:
            continue
        e = L[q]
        ec = (0.01 + e * 1e-4) * _mult(tod[j])
        tgt = e + side * up * R
        x = 0.0; cd = 0; xk = -1
        if (side == 1 and l[j] <= S[q]) or (side == -1 and h[j] >= S[q]):
            x, cd, xk = S[q], 2, j
        else:
            for k in range(j + 1, end + 1):
                if tod[k] > 1555:
                    break
                if (side == 1 and l[k] <= S[q]) or (side == -1 and h[k] >= S[q]):
                    x, cd, xk = S[q], 2, k
                    break
                if (side == 1 and h[k] >= tgt) or (side == -1 and l[k] <= tgt):
                    x, cd, xk = tgt, 1, k
                    break
            if cd == 0:
                kk = end
                while kk > j and tod[kk] > 1555:
                    kk -= 1
                x, cd, xk = c[kk], 6, kk
        xc = 0.0 if cd == 1 else (0.01 + x * 1e-4 + (0.02 if cd == 2 else 0.0))
        r[q] = side * (x - e) / R - (ec + xc) / R
        code[q] = cd; ftod[q] = tod[j]; xr[q] = xk
    return r, code, ftod, xr


def prev_month(month):
    p = (pd.Timestamp(month + "-01") - pd.offsets.MonthBegin(1)).strftime("%Y-%m")
    return p if p in lib.months() and p not in lib.LOCKED_MONTHS else None


def month_job(month):
    t0 = time.time()
    DF = daily_feats()
    P = load_path(month)
    pm = prev_month(month)
    if pm:
        Pp = load_path(pm)
        last = sorted(Pp.date.unique())[-3:]
        Pp = Pp[Pp.date.isin(last)]
        P = pd.concat([Pp, P], ignore_index=True).sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    cur = pd.to_datetime(P["date"]).dt.strftime("%Y-%m").to_numpy() == month
    # 5-minute path arrays
    key = P["symbol"].to_numpy() + "|" + P["date"].astype(str).to_numpy()
    new = np.r_[True, key[1:] != key[:-1]]
    segp = np.cumsum(new) - 1
    dend = np.r_[np.flatnonzero(new)[1:] - 1, len(P) - 1][segp]
    ph, pl, pc = (P[k].to_numpy(float) for k in ("high", "low", "close"))
    ptod = P["tod"].to_numpy(np.int32)
    pkey = pd.MultiIndex.from_arrays([P.symbol, P.date, P.tod])
    prow = pd.Series(np.arange(len(P)), index=pkey)
    # hourly state
    H = bars(P, 60)
    hseg, _, _ = series_index(H)
    hl, lh = hourly_state(H.high.to_numpy(float), H.low.to_numpy(float), hseg)
    H["hl"], H["lh"] = hl, lh
    Hc = H[["symbol", "date", "end", "hl", "lh"]].copy()
    Hc["ord"] = np.arange(len(Hc))

    def htf_at(sym, dat, tod):
        """hourly HL / LH state as of the last hourly bar completed by `tod` (that session or earlier)."""
        q = pd.DataFrame({"symbol": sym, "date": dat, "tod": np.asarray(tod, np.int64)})
        q["ord_q"] = np.arange(len(q))
        # completed bars today: end <= tod; else the prior session's last bar
        Hs = Hc.sort_values(["symbol", "date", "end"])
        Hs["dkey"] = Hs.symbol + "|" + Hs.date.astype(str)
        q["dkey"] = q.symbol + "|" + q.date.astype(str)
        first_ord = Hs.groupby("dkey")["ord"].min()
        q = q.sort_values("tod")
        Hs2 = Hs.sort_values("end")
        m = pd.merge_asof(q, Hs2[["dkey", "end", "ord"]].rename(columns={"end": "tod"}).astype({"tod": np.int64}), on="tod", by="dkey", direction="backward")
        o = m["ord"].to_numpy(float).copy()
        miss = np.isnan(o)
        o[miss] = m.loc[miss, "dkey"].map(first_ord).to_numpy(float) - 1
        hlv = np.zeros(len(m), bool); lhv = np.zeros(len(m), bool)
        okk = o >= 0
        oi = o[okk].astype(int)
        same = (Hc.symbol.to_numpy()[oi] == m.symbol.to_numpy()[okk])
        hlv[np.flatnonzero(okk)[same]] = Hc.hl.to_numpy()[oi][same]
        lhv[np.flatnonzero(okk)[same]] = Hc.lh.to_numpy()[oi][same]
        m["hl"], m["lh"] = hlv, lhv
        return m.sort_values("ord_q")[["hl", "lh"]].to_numpy()

    out = []
    # ---- 1. MSS
    B = bars(P, 30)
    seg, sst, pst = series_index(B)
    bh, bl, bc = (B[k].to_numpy(float) for k in ("high", "low", "close"))
    # today's range so far
    dkey = B.symbol + "|" + B.date.astype(str)
    B["dhi"] = B.groupby(dkey.to_numpy()).high.cummax()
    B["dlo"] = B.groupby(dkey.to_numpy()).low.cummin()
    B = B.merge(DF, on=["symbol", "date"], how="left")
    bcur = pd.to_datetime(B["date"]).dt.strftime("%Y-%m").to_numpy() == month
    elig = bcur & (B.end.to_numpy() >= 1030) & (B.end.to_numpy() <= 1500) & (B.n.to_numpy() == 6)
    sig_rows = np.flatnonzero(elig)
    st = htf_at(B.symbol.to_numpy()[sig_rows], B.date.to_numpy()[sig_rows], B.end.to_numpy()[sig_rows])
    HL = np.zeros(len(B), bool); LH = np.zeros(len(B), bool)
    HL[sig_rows], LH[sig_rows] = st[:, 0], st[:, 1]
    # start row in the 5-minute path: the first row after the shift bar's close
    sr = prow.reindex(pd.MultiIndex.from_arrays([B.symbol, B.date, B.etod])).to_numpy(float)
    adv_ok = (B.merge(P.groupby(["symbol", "date"]).agg(adv=("adv20", "first"), atr=("atr_d", "first")).reset_index(),
                      on=["symbol", "date"], how="left").eval("adv >= @ADV and atr > 0")).to_numpy()
    with np.errstate(invalid="ignore"):
        up_d = (B.p_close > B.p_sma20).to_numpy()
        dn_d = (B.p_close < B.p_sma20).to_numpy()
        pmid = ((B.p_high + B.p_low) / 2).to_numpy(float)
        tmid = ((B.dhi + B.dlo) / 2).to_numpy(float)
    for vi, (side, k, tgt, p) in enumerate(VARIANTS):
        fl, ext = mss(bh, bl, bc, sst, pst, k, side)
        L = bc - p * (bc - ext)
        with np.errstate(invalid="ignore"):
            loc = (side * (tmid - L) >= 0) | (side * (pmid - L) >= 0)
            htf = (up_d & HL) if side == 1 else (dn_d & LH)
        sig = elig & fl & loc & htf & adv_ok & np.isfinite(sr)
        rows = np.flatnonzero(sig)
        d = pd.DataFrame({"row": rows, "dk": dkey.to_numpy()[rows]}).drop_duplicates("dk")
        rows = d.row.to_numpy()
        S = ext[rows] - side * 0.01
        start = sr[rows].astype(np.int64) + 1
        start = np.where(start <= dend[np.maximum(start - 1, 0)], start, -1)
        r, cd, ft, xr = sim_limit(ph, pl, pc, ptod, start, dend, L[rows], S, side, tgt)
        t = pd.DataFrame({"date": B.date.to_numpy()[rows], "symbol": B.symbol.to_numpy()[rows], "sig_tod": B.end.to_numpy()[rows],
                          "fill_tod": ft, "r": r, "code": cd, "L": L[rows], "R": side * (L[rows] - S)})
        t["side"], t["k"], t["tgt"], t["p"], t["vid"] = side, k, tgt, p, vi
        out.append(t)
    mt = pd.concat(out, ignore_index=True)
    # ---- 2. coil features
    C = pd.read_parquet(COIL, filters=[("var", "==", "P")])
    C["date"] = pd.to_datetime(C["date"]).dt.date
    C = C[pd.to_datetime(C.date).dt.strftime("%Y-%m") == month].copy()
    C["symbol"] = C.symbol.astype(str)
    if len(C):
        st = htf_at(C.symbol.to_numpy(), C.date.to_numpy(), C.sig_tod.to_numpy())
        C["h60_hl"] = st[:, 0]
        C = C.merge(DF, on=["symbol", "date"], how="left")
        ctx = lib.load_context(month)[["date", "tod", "breadth_open", "qqq_fo"]]
        q = lib.load_month(month, columns=["symbol", "date", "tod", "vwapDistPct"])
        q = q[q.symbol == "QQQ"][["date", "tod", "vwapDistPct"]].rename(columns={"vwapDistPct": "qqq_vwap"})
        C = C.merge(ctx.rename(columns={"tod": "sig_tod"}), on=["date", "sig_tod"], how="left") \
             .merge(q.rename(columns={"tod": "sig_tod"}), on=["date", "sig_tod"], how="left")
    print(month, len(mt), int(mt.r.notna().sum()), len(C), round(time.time() - t0), flush=True)
    return mt, C


def main():
    SCR.mkdir(parents=True, exist_ok=True)
    months = lib.months()
    assert not set(months) & set(lib.LOCKED_MONTHS)
    with Pool(int(os.environ.get("HTF_PROCS", 3))) as pool:
        res = pool.map(month_job, months)
    M = pd.concat([a for a, _ in res], ignore_index=True)
    C = pd.concat([b for _, b in res if len(b)], ignore_index=True)
    M.to_parquet(SCR / "mss.parquet", index=False)
    C.to_parquet(SCR / "coilfeat.parquet", index=False)
    print(M.groupby("vid").agg(n=("r", "size"), filled=("r", lambda x: x.notna().mean()), exp=("r", "mean")).to_string())


if __name__ == "__main__":
    if sys.argv[1:2] == ["one"]:
        a, b = month_job(sys.argv[2])
        print(a.groupby("vid").agg(n=("r", "size"), filled=("r", lambda x: x.notna().mean()), exp=("r", "mean"), R=("R", "median")))
        print(b[["h60_hl", "p_close", "p_sma20", "breadth_open", "qqq_vwap"]].describe(include="all"))
    else:
        main()
