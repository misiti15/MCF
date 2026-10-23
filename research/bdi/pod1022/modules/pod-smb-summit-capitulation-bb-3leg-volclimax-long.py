"""pod-smb-summit-capitulation-bb-3leg-volclimax-long - SMB Summit capitulation fade: 3+ extended down legs below the
lower Bollinger band on a volume climax (not a day-1 news move) (LONG).

Source: SMB Capital Trading Summit 2026 - 'Capitulation Fade' talk (summarized on LinkedIn) + 'How to Stop Making Bad
Fade Trades' (SMB blog).
URL: https://www.smbtraining.com/blog/how-to-stop-making-bad-fade-trades

VARIANT of pod-cwt-breitstein-stock-multiday-flush and pod-three-push-deceleration-low-long. What changes: the stretch
is a 2-SD Bollinger close plus a volume-climax bar, day-1 news moves are skipped, and deceleration is not required.

Data: continuous 5m bars (frame 09:50-15:00 + the 09:35-09:45 / 15:05-15:55 head-tail table, previous open month as
warm-up; helper _cwt3_bars.full_bars, locked block never read) for Bollinger(20, 2), ATR14(5m) and the swing lows.
Bar volume vs its 20-bar average = the frame's volumeRatio (so a climax bar is a 09:50+ bar).

Rules (plain English):
  1. Daily (completed days): >= 2 consecutive red daily closes (D-1 close < D-2 close < D-3 close) and today's
     |gap| < 3% (proxy for 'not day 1 of fresh news'); price >= $10; ADV >= 1M shares (adv20 $ / price).
  2. Intraday: >= 3 successive lower 5m swing lows since the open (a swing low = a bar whose low is under the previous
     bar's low and not above the next bar's low, confirmed one bar later), each leg (highest high since the previous
     swing low, or since the open, down to the swing low) >= 0.5 x ATR14(5m).
  3. Climax bar: a 5m bar closes below the lower BB(20, 2) with volume >= 3x its 20-bar average, with rule 2 true.
  4. Entry: within the next 3 bars, the first 5m close back inside the band (above the lower band) and above the
     prior bar's high, bar close 10:00-15:00.
  Stop: session low - 0.05 daily ATR. Target 1: the BB middle (SMA20) at entry. Time stop 60 minutes (12 bars,
  GEOM S+x MAX_BARS). The source's 'Target 2 / trail to VWAP' leg is not modelled (one unit, pre-declared: the
  whole position exits at target 1). Flat 15:55.
Tweak: none. 1 configuration. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

import _cwt3_bars as C3
import _r33_util as U

SIDE = "long"
GEOM = "S+x"
MAX_BARS = 12
WINDOW = (1000, 1500)
LAYERS = [">= 2 red daily closes, |gap| < 3%, price >= 10, ADV >= 1M sh", ">= 3 successive lower swing lows, legs >= 0.5 ATR5",
          "close < lower BB(20,2) on >= 3x volume", "within 3 bars: close back inside the band and above prior high",
          "stop LOD - 0.05 ATR, target BB middle, 60-min time stop"]
_ST = {}


@numba.njit(cache=False)
def _kern(newd, tod, h, l, c, atr5, bbl, bbm, vr, atrd, ok):
    n = len(c)
    sig = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    i = 0
    while i < n:
        j0 = i
        j1 = i + 1
        while j1 < n and not newd[j1]:
            j1 += 1
        if ok[j0]:
            lod = np.inf
            last_sw = np.inf
            run = 0
            hi_since = -np.inf
            climax = -100
            done = False
            for t in range(j0, j1):
                lod = min(lod, l[t])
                # confirm a swing low at t-1 (needs t-2 in session)
                if t - 2 >= j0:
                    p = t - 1
                    if l[p] < l[p - 1] and l[p] <= l[t]:
                        leg = hi_since - l[p]
                        if atr5[p] > 0 and leg >= 0.5 * atr5[p]:
                            if l[p] < last_sw and run > 0:
                                run += 1
                            else:
                                run = 1
                        else:
                            run = 0
                        last_sw = l[p]
                        hi_since = -np.inf
                        for q in range(p + 1, t + 1):
                            hi_since = max(hi_since, h[q])
                    else:
                        hi_since = max(hi_since, h[t])
                else:
                    hi_since = max(hi_since, h[t])
                if done:
                    continue
                if t - climax >= 1 and t - climax <= 3 and tod[t] >= 1000 and tod[t] <= 1500:
                    if c[t] > bbl[t] and c[t] > h[t - 1]:
                        sp = lod - 0.05 * atrd[t]
                        if bbm[t] > c[t] and c[t] > sp:
                            sig[t] = True
                            stop[t] = sp
                            tgt[t] = bbm[t]
                        done = True
                        continue
                if run >= 3 and c[t] < bbl[t] and vr[t] >= 3.0:
                    climax = t
        i = j1
    return sig, stop, tgt


def mask(df):
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    if not n:
        return z
    k = U.key(df)
    d = U.map_day(df, U.daily_tab(), ["c1", "c2", "c3"])
    c = U.f(df, "close")
    with np.errstate(invalid="ignore", divide="ignore"):
        ok = ((d["c1"] < d["c2"]) & (d["c2"] < d["c3"]) & (np.abs(U.f(df, "gap")) < 3) & (c >= 10)
              & (U.f(df, "adv20") / c >= 1e6))
    if not ok.any():
        _ST[id(df)] = (np.full(n, np.nan), np.full(n, np.nan))
        return z
    # a symbol-day qualifies on its first frame row's values (daily facts; price at 09:50)
    st = np.r_[True, k[1:] != k[:-1]]
    okd = ok[st][np.cumsum(st) - 1]
    syms = sorted(set(df["symbol"].astype(str).to_numpy()[okd]))
    P = C3.full_bars(df, symbols=syms)
    if P is None:
        _ST[id(df)] = (np.full(n, np.nan), np.full(n, np.nan))
        return z
    P = P.copy()
    g = pd.factorize(P["symbol"].to_numpy())[0]
    cs = pd.Series(P["c"].to_numpy(float))
    P["bbm"] = cs.groupby(g).transform(lambda x: x.rolling(20, min_periods=20).mean()).to_numpy()
    sd = cs.groupby(g).transform(lambda x: x.rolling(20, min_periods=20).std(ddof=0)).to_numpy()
    P["bbl"] = P["bbm"].to_numpy() - 2 * sd
    pc = cs.groupby(g).shift(1).to_numpy()
    hh, ll = P["h"].to_numpy(float), P["l"].to_numpy(float)
    tr = np.nanmax(np.c_[hh - ll, np.abs(hh - pc), np.abs(ll - pc)], axis=1)
    P["atr5"] = pd.Series(tr).groupby(g).transform(lambda x: x.rolling(14, min_periods=14).mean()).to_numpy()
    # frame values onto P rows (NaN on head / tail rows and on symbol-days outside the frame)
    F = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(object), "date": df["date"].to_numpy(),
                      "tod": df["tod"].to_numpy(np.int64), "vr": U.f(df, "volumeRatio"), "atrd": U.f(df, "atr_d"),
                      "ok": okd.astype(float)})
    Q = P.merge(F, on=["symbol", "date", "tod"], how="left")
    assert len(Q) == len(P)
    sym = Q["symbol"].to_numpy()
    dat = pd.Series(Q["date"].to_numpy()).astype(str).to_numpy()
    newd = np.r_[True, (sym[1:] != sym[:-1]) | (dat[1:] != dat[:-1])]
    seg = np.cumsum(newd) - 1
    okq = Q["ok"].to_numpy(float)
    okseg = pd.Series(okq).groupby(seg).transform("max").to_numpy() == 1
    atrd = pd.Series(Q["atrd"].to_numpy(float)).groupby(seg).transform("first").to_numpy()
    sig, stop, tgt = _kern(newd, Q["tod"].to_numpy(np.int64), Q["h"].to_numpy(float), Q["l"].to_numpy(float),
                           Q["c"].to_numpy(float), Q["atr5"].to_numpy(float), Q["bbl"].to_numpy(float),
                           Q["bbm"].to_numpy(float), Q["vr"].to_numpy(float), atrd, okseg)
    T = pd.DataFrame({"symbol": Q["symbol"].to_numpy(object), "date": Q["date"].to_numpy(),
                      "tod": Q["tod"].to_numpy(np.int64), "sig": sig.astype(float), "sp": stop, "tp": tgt})
    T = T[T["sig"] == 1]
    M = C3.map_rows(df, T, ["sig", "sp", "tp"])
    m = M["sig"] == 1
    _ST[id(df)] = (M["sp"], M["tp"])
    return np.asarray(m & okd, bool)


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
