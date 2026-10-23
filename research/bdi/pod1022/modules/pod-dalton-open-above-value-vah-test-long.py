"""pod-dalton-open-above-value-vah-test-long - Open above the prior-day value area: the FIRST test of VAH from above
holds (look below and fail), long the resumption (LONG). Structural stop, target the session high or 1R.

Source: Trader Dante value-area material + Axia Futures Volume Profile course (open outside value: the acceptance
test at the value edge); Team LBR 'MP value area rule (80% rule)'. Not re-fetched this round.
URL: http://teamlbr.blogspot.com/2008/09/mp-value-area-rule-80-rule.html

VARIANT of 'Prior-day volume profile (POC / value area) touches' (failed) and the opposite case of the 80% rule
(which trades opens INSIDE value). Stated changes: only opens OUTSIDE value (above D-1 VAH), only the FIRST test of
VAH from above, and the 5-min close must hold.

Rules (plain English, LONG):
  1. D-1 70% value area from D-1's 5-min bars, volume at the bar's typical price (h + l + c) / 3, price bins of
     0.02 x atr_d, value area grown from the POC bin by the heavier neighbour until >= 70% of volume; VAH = upper
     edge of the top bin. The open is > VAH and <= PDH + 0.5 x atr_d.
  2. The first bar (09:50-11:30) whose low is <= VAH + 0.1 x ATR5m is the test; its low must be >= VAH - 0.25 x ATR5m
     (else the first test failed - no trade that day). If the 09:30-09:45 bars already reached that zone (running low
     of day at 09:50 below the 09:50 bar's low and within VAH + 0.1 x ATR5m) the first test is not visible - no trade.
     The test bar or the next closes above VAH, and no 5-min close below VAH (inside value) from 09:50 to the entry.
  3. Test-bar volumeRatio <= 1.2 (not a heavy sell-off).
  4. SPY is above its own open at the entry bar (spy_fo > 0).
  Entry: the first later 5-min close above the test bar's high (entry by 12:00). Stop (GEOM S): min(test low,
  VAH - 0.25 x ATR5m). Target: the session high so far, or 1R if that is further than the high (max of the two).
  Flat 15:55.
Harness approximations (declared): the scoring frames have no raw volume, so the profile is built from the volume-
bearing 5-min frames (research/history2y/data/frames_tf/5min, 160 liquid symbols; SYMBOLS = that list, adv20 >= $20M)
over D-1's 09:50-15:00 bars (the first 20 minutes and the last hour are not in the frames). The previous open month
is read for the first day of a month (never the locked block). Entry deadline 12:00 is a harness bound, not a tweak.
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
from pathlib import Path as _P

SIDE = "long"
GEOM = "S"
WINDOW = (955, 1200)
MIN_ADV = 20e6
CONTEXT = ["spy_fo"]
try:
    SYMBOLS = [s.strip() for s in (_P(__file__).resolve().parents[3] / "history2y" / "data" / "frames_tf" /
                                   "symbols.txt").read_text().split() if s.strip()]
except OSError:
    SYMBOLS = ["SPY"]
LAYERS = ["open above D-1 VAH (5m volume profile), <= PDH + 0.5 ATR", "first VAH test 09:50-11:30 within +0.1/-0.25 ATR5m, holds",
          "test volumeRatio <= 1.2", "spy_fo > 0", "entry: close above the test high by 12:00",
          "stop min(test low, VAH - 0.25 ATR5m), target max(HOD, 1R)"]

import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

_ST = {}
_DC = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _segs(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _lib():
    try:
        import lib
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
        import lib
    return lib


def _base(df):
    """Point-in-time levels per row (all from the bar itself or earlier / completed prior days)."""
    c, atr = _f(df, "close"), _f(df, "atr_d")
    b = dict(c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr, tod=df["tod"].to_numpy(np.int64))
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr          # running low of day (includes 09:30-09:45)
    b["pdh"] = c + _f(df, "dist_pdh_atr") * atr
    b["pdl"] = c - _f(df, "dist_pdl_atr") * atr
    b["opn"] = c / (1 + _f(df, "fromOpen") / 100)        # today's open
    b["pc"] = b["opn"] / (1 + _f(df, "gap") / 100)        # prior close
    b["vwap"] = c / (1 + _f(df, "vwapDistPct") / 100)
    b["atr5"] = _f(df, "atrPct") / 100 * c               # 5m ATR(14), $
    return b


def _prev_month(m):
    y, mo = int(m[:4]), int(m[5:7])
    y, mo = (y - 1, 12) if mo == 1 else (y, mo - 1)
    return f"{y:04d}-{mo:02d}"


def _open_month(m):
    """True only for an OPEN month (never the rule-19 locked block)."""
    L = _lib()
    return m not in L.LOCKED_MONTHS and m in set(L.months())


def mask(df) -> np.ndarray:
    n = len(df)
    try:
        m, stop, tgt = _compute(df)
    except KeyError:
        m, stop, tgt = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    _ST.clear()
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])


@numba.njit(cache=False)
def _profile(bs, be, h, l, c, v, atr):
    """Per symbol-day segment: VAH, VAL, POC from volume at typical price (bins of 0.02 x atr_d)."""
    ns = len(bs)
    vah = np.full(ns, np.nan)
    val = np.full(ns, np.nan)
    poc = np.full(ns, np.nan)
    for s in range(ns):
        i0, i1 = bs[s], be[s]
        a = atr[i0]
        if not (a > 0) or i1 - i0 < 10:
            continue
        w = 0.02 * a
        lo = 1e18
        hi = -1e18
        for i in range(i0, i1):
            tp = (h[i] + l[i] + c[i]) / 3.0
            lo = min(lo, tp)
            hi = max(hi, tp)
        b0 = np.floor(lo / w)
        nb = int(np.floor(hi / w) - b0) + 1
        if nb <= 0 or nb > 100000:
            continue
        vol = np.zeros(nb)
        tot = 0.0
        for i in range(i0, i1):
            if np.isfinite(v[i]) and v[i] > 0:
                q = int(np.floor((h[i] + l[i] + c[i]) / 3.0 / w) - b0)
                vol[q] += v[i]
                tot += v[i]
        if tot <= 0:
            continue
        p = int(np.argmax(vol))
        up = p
        dn = p
        acc = vol[p]
        while acc < 0.7 * tot:
            va = vol[up + 1] if up + 1 < nb else -1.0
            vb = vol[dn - 1] if dn - 1 >= 0 else -1.0
            if va < 0 and vb < 0:
                break
            if va >= vb:
                up += 1
                acc += va
            else:
                dn -= 1
                acc += vb
        vah[s] = (b0 + up + 1) * w
        val[s] = (b0 + dn) * w
        poc[s] = (b0 + p + 0.5) * w
    return vah, val, poc


def _va_table(months):
    """(symbol, date D) -> D-1's VAH from the volume-bearing 5-min frames, previous open month included."""
    key = tuple(sorted(months))
    if _DC.get("va_key") == key:
        return _DC["va"]
    need = set(months)
    for mo in months:
        pm = _prev_month(mo)
        if _open_month(pm):
            need.add(pm)
    L = _lib()
    import pyarrow.dataset as pds
    parts = []
    for mo in sorted(need):
        if mo in L.LOCKED_MONTHS:
            continue
        p = L.DATA / "frames_tf" / "5min" / f"month={mo}"
        if not p.exists():
            continue
        t = pds.dataset(str(p), format="parquet").to_table(
            columns=["symbol", "date", "tod", "high", "low", "close", "volume", "atr_d"]).to_pandas()
        parts.append(t)
    if not parts:
        _DC["va_key"], _DC["va"] = key, None
        return None
    t = pd.concat(parts, ignore_index=True)
    t["symbol"] = t["symbol"].astype(str)
    t["date"] = pd.to_datetime(t["date"]).dt.date.astype(str)
    lk = _lib().LOCKED
    t = t[(t["date"] < lk[0]) | (t["date"] > lk[1])]
    t = t.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    k = pd.factorize(t["symbol"] + "|" + t["date"])[0]
    bs, be = _segs(k)
    f = lambda c: t[c].to_numpy(float)
    vah, val, poc = _profile(bs, be, f("high"), f("low"), f("close"), f("volume"), f("atr_d"))
    d = pd.DataFrame({"symbol": t["symbol"].to_numpy()[bs], "pdate": t["date"].to_numpy()[bs], "vah": vah})
    d = d.sort_values(["symbol", "pdate"]).reset_index(drop=True)
    d["date"] = d.groupby("symbol")["pdate"].shift(-1)          # the profile of D-1 is used on D
    gap = (pd.to_datetime(d["date"]) - pd.to_datetime(d["pdate"])).dt.days
    d = d[d["date"].notna() & (gap <= 4)][["symbol", "date", "vah"]]
    _DC["va_key"], _DC["va"] = key, d
    return d


@numba.njit(cache=False)
def _kernel(bs, be, tod, c, h, l, lod, hod, atr5, atr, opn, pdh, vah, vr, spy):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(bs)):
        i0, i1 = bs[s], be[s]
        V = vah[i0]
        a = atr[i0]
        if not (np.isfinite(V) and a > 0) or tod[i0] != 950:
            continue
        if not (opn[i0] > V and opn[i0] <= pdh[i0] + 0.5 * a):                          # (1)
            continue
        if lod[i0] < l[i0] - 1e-6 * c[i0] and lod[i0] <= V + 0.1 * atr5[i0]:
            continue                                                                     # first test before 09:50
        t = -1
        for i in range(i0, i1):
            if tod[i] > 1130:
                break
            if c[i] < V:
                break                                                                    # a close inside value
            if l[i] <= V + 0.1 * atr5[i]:
                t = i
                break
        if t < 0 or l[t] < V - 0.25 * atr5[t]:                                          # (2)
            continue
        if not (vr[t] <= 1.2):                                                           # (3)
            continue
        if c[t] < V:
            continue
        for j in range(t + 1, i1):
            if tod[j] > 1200 or c[j] < V:
                break
            if j == t + 1 and not (c[t] > V or c[j] > V):
                break
            if c[j] > h[t]:
                if np.isfinite(spy[j]) and spy[j] > 0:                                   # (4)
                    sp = min(l[t], V - 0.25 * atr5[t])
                    R = c[j] - sp
                    if R > 0:
                        m[j] = True
                        stop[j] = sp
                        tgt[j] = max(hod[j], c[j] + R)
                break
    return m, stop, tgt


def _compute(df):
    n = len(df)
    z = (np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan))
    if not n or "spy_fo" not in df:
        return z
    ds = df["date"].astype(str).to_numpy()
    va = _va_table(sorted(set(x[:7] for x in np.unique(ds))))
    if va is None:
        return z
    k = _key(df)
    st = np.r_[True, k[1:] != k[:-1]]
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": ds[st]})
    vah = u.merge(va, on=["symbol", "date"], how="left")["vah"].to_numpy(float)[np.cumsum(st) - 1]
    b = _base(df)
    bs, be = _segs(k)
    return _kernel(bs, be, b["tod"], b["c"], b["h"], b["l"], b["lod"], b["hod"], b["atr5"], b["atr"], b["opn"],
                   b["pdh"], vah, _f(df, "volumeRatio"), _f(df, "spy_fo"))
