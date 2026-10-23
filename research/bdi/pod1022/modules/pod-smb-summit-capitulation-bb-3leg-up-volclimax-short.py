"""pod-smb-summit-capitulation-bb-3leg-up-volclimax-short - SMB Summit capitulation fade (short): multi-day run, 3+
extended up legs above the upper Bollinger band on a volume climax (SHORT).

Source: SMB Capital Trading Summit 2026 - 'Capitulation Fade' talk (summarized on LinkedIn) + 'Would You Make This
Fade Trade? $APOL' (SMB blog).
URL: https://www.smbtraining.com/blog/would-you-make-this-fade-trade-apol

VARIANT of pod-bbt-parabolic-ema9-snapback-short; the mirror of pod-smb-summit-capitulation-bb-3leg-volclimax-long.
What changes: the stretch is a 2-SD Bollinger close plus a volume climax instead of EMA9 distance; it needs a
multi-day run (>= 3 green daily closes; SMB: the biggest capitulations come after 3+ legs and multi-day runs) and skips
day-1 news moves (|gap| < 3%).

Data: continuous 5m bars (frame 09:50-15:00 + the 09:35-09:45 / 15:05-15:55 head-tail table, previous open month as
warm-up; _cwt3_bars.full_bars, locked block never read) for Bollinger(20, 2), ATR14(5m) and swing highs. Bar volume
vs its 20-bar average = the frame's volumeRatio (so a climax bar is a 09:50+ bar). Daily closes D-1..D-4 from
_r34_util (completed days).

Rules (plain English):
  1. Daily: >= 3 consecutive green daily closes (D-1 > D-2 > D-3 > D-4 close to close); |gap| < 3%; price >= $10;
     ADV >= 1M shares (adv20 $ / price).
  2. Intraday: >= 3 successive higher 5m swing highs since the open (a swing high = a bar whose high is above the
     previous bar's high and not below the next bar's high, confirmed one bar later), each leg (lowest low since the
     previous swing high, or since the open, up to the swing high) >= 0.5 x ATR14(5m).
  3. Climax bar: a 5m close above the upper BB(20, 2) with volume >= 3x its 20-bar average, with rule 2 true.
  4. Entry: within the next 3 bars, the first 5m close back inside the band (below the upper band) and below the
     prior bar's low, bar close 10:00-15:00.
  Stop: HOD + 0.05 daily ATR. Target: the BB middle (SMA20) at entry; the 'then VWAP' second leg is not modelled (one
  unit, as in the long mirror). Time stop 60 minutes (12 bars, GEOM S+x MAX_BARS). Flat 15:55.
Reading (pre-declared): 'green daily close' = close above the prior close. Tweak: none. 1 configuration.
Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

import _cwt3_bars as C3
import _r33_util as U
import _r34_util as D34

SIDE = "short"
GEOM = "S+x"
MAX_BARS = 12
WINDOW = (1000, 1500)
LAYERS = [">= 3 green daily closes, |gap| < 3%, price >= 10, ADV >= 1M sh", ">= 3 successive higher swing highs, legs >= 0.5 ATR5",
          "close > upper BB(20,2) on >= 3x volume", "within 3 bars: close back inside the band and below prior low",
          "stop HOD + 0.05 ATR, target BB middle, 60-min time stop"]
_ST = {}


@numba.njit(cache=False)
def _kern(newd, tod, h, l, c, atr5, bbu, bbm, vr, atrd, ok):
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
            hod = -np.inf
            last_sw = -np.inf
            run = 0
            lo_since = np.inf
            climax = -100
            done = False
            for t in range(j0, j1):
                hod = max(hod, h[t])
                if t - 2 >= j0:
                    p = t - 1
                    if h[p] > h[p - 1] and h[p] >= h[t]:
                        leg = h[p] - lo_since
                        if atr5[p] > 0 and leg >= 0.5 * atr5[p]:
                            if h[p] > last_sw and run > 0:
                                run += 1
                            else:
                                run = 1
                        else:
                            run = 0
                        last_sw = h[p]
                        lo_since = np.inf
                        for q in range(p + 1, t + 1):
                            lo_since = min(lo_since, l[q])
                    else:
                        lo_since = min(lo_since, l[t])
                else:
                    lo_since = min(lo_since, l[t])
                if done:
                    continue
                if t - climax >= 1 and t - climax <= 3 and tod[t] >= 1000 and tod[t] <= 1500:
                    if c[t] < bbu[t] and c[t] < l[t - 1]:
                        sp = hod + 0.05 * atrd[t]
                        if bbm[t] < c[t] and c[t] < sp:
                            sig[t] = True
                            stop[t] = sp
                            tgt[t] = bbm[t]
                        done = True
                        continue
                if run >= 3 and c[t] > bbu[t] and vr[t] >= 3.0:
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
    d = D34.map_daily(df, ["c1", "c2", "c3", "c4"])
    c = U.f(df, "close")
    with np.errstate(invalid="ignore", divide="ignore"):
        ok = ((d["c1"] > d["c2"]) & (d["c2"] > d["c3"]) & (d["c3"] > d["c4"]) & (np.abs(U.f(df, "gap")) < 3)
              & (c >= 10) & (U.f(df, "adv20") / c >= 1e6))
    st = np.r_[True, k[1:] != k[:-1]]
    okd = ok[st][np.cumsum(st) - 1]
    if not okd.any():
        _ST[id(df)] = (np.full(n, np.nan), np.full(n, np.nan))
        return z
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
    P["bbu"] = P["bbm"].to_numpy() + 2 * sd
    pc = cs.groupby(g).shift(1).to_numpy()
    hh, ll = P["h"].to_numpy(float), P["l"].to_numpy(float)
    tr = np.nanmax(np.c_[hh - ll, np.abs(hh - pc), np.abs(ll - pc)], axis=1)
    P["atr5"] = pd.Series(tr).groupby(g).transform(lambda x: x.rolling(14, min_periods=14).mean()).to_numpy()
    F = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(object), "date": df["date"].to_numpy(),
                      "tod": df["tod"].to_numpy(np.int64), "vr": U.f(df, "volumeRatio"), "atrd": U.f(df, "atr_d"),
                      "ok": okd.astype(float)})
    Q = P.merge(F, on=["symbol", "date", "tod"], how="left")
    assert len(Q) == len(P)
    sym = Q["symbol"].to_numpy()
    dat = pd.Series(Q["date"].to_numpy()).astype(str).to_numpy()
    newd = np.r_[True, (sym[1:] != sym[:-1]) | (dat[1:] != dat[:-1])]
    seg = np.cumsum(newd) - 1
    okseg = pd.Series(Q["ok"].to_numpy(float)).groupby(seg).transform("max").to_numpy() == 1
    atrd = pd.Series(Q["atrd"].to_numpy(float)).groupby(seg).transform("first").to_numpy()
    sig, stop, tgt = _kern(newd, Q["tod"].to_numpy(np.int64), Q["h"].to_numpy(float), Q["l"].to_numpy(float),
                           Q["c"].to_numpy(float), Q["atr5"].to_numpy(float), Q["bbu"].to_numpy(float),
                           Q["bbm"].to_numpy(float), Q["vr"].to_numpy(float), atrd, okseg)
    T = pd.DataFrame({"symbol": Q["symbol"].to_numpy(object), "date": Q["date"].to_numpy(),
                      "tod": Q["tod"].to_numpy(np.int64), "sig": sig.astype(float), "sp": stop, "tp": tgt})
    T = T[T["sig"] == 1]
    M = C3.map_rows(df, T, ["sig", "sp", "tp"])
    _ST[id(df)] = (M["sp"], M["tp"])
    return np.asarray((M["sig"] == 1) & okd, bool)


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
