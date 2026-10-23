"""_r210_util - shared helpers for the pod r2_10 'of3' modules (Barros failed-auction high magnet, TPO value area,
3-day balance). Not a setup (no SIDE / mask).

Per completed session S of each symbol (from _cwt3_bars.full_bars: the frame month + the previous OPEN month as
warm-up, 09:35..15:55 bars; the rule-19 locked block is never read) we build:
  * sh   = session high; ibh = IB high (bars closing 09:35..10:30)
  * z    = Barros failed-auction high: the session high was made by an excursion above the IB high after 10:30
           (contiguous run of bars with high > IBH that contains the session-high bar, starting after 10:30), the
           session high is >= IBH + 0.05 x atr_d, and a close back below the IB high came within 6 bars of the
           excursion's first bar (that bar counted as bar 1). NaN otherwise.
  * poc / val / vah = TPO profile: each 5m bar adds one count to every 0.05 x atr_d price bin it touches; POC = the
           bin with the most counts (tie: nearest the session mid-range); the value area grows from the POC one bin
           at a time towards the side with more counts (tie: up) until it holds >= 70% of all counts.
atr_d for session S = daily ATR(14) as of S-1's close (lib.daily()), the same convention as the frame's atr_d.
Prior-session values are shifted per symbol over sessions; a > 7-calendar-day gap restarts the series (never bridges
the locked block). Rows of the decision day D only ever see sessions < D. Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _cwt3_bars as CB  # noqa: E402

f, key, start, lag, base, at_tod = CB.f, CB.key, CB.start, CB.lag, CB.base, CB.at_tod
_MEM = {}


def _atr_tab():
    if "atr" in _MEM:
        return _MEM["atr"]
    t = CB.daily_feats()[["symbol", "date", "atr14_1"]].copy()
    _MEM["atr"] = t
    return t


@numba.njit(cache=False)
def _sessions(ss, se, tod, h, l, c, atr, out):
    """out[s] = (sh, ibh, z, poc, val, vah) for session s = rows ss[s]..se[s]-1."""
    for s in range(len(ss)):
        a, b = ss[s], se[s]
        sh = -1e18
        jh = -1
        ibh = -1e18
        lo = 1e18
        for i in range(a, b):
            if h[i] > sh:
                sh = h[i]
                jh = i
            if l[i] < lo:
                lo = l[i]
            if tod[i] <= 1030 and h[i] > ibh:
                ibh = h[i]
        out[s, 0] = sh
        out[s, 1] = ibh if ibh > -1e17 else np.nan
        out[s, 2] = np.nan
        A = atr[s]
        # failed-auction high
        if ibh > -1e17 and np.isfinite(A) and A > 0 and tod[jh] > 1030 and sh >= ibh + 0.05 * A:
            st = jh
            while st - 1 >= a and h[st - 1] > ibh and tod[st - 1] > 1030:
                st -= 1
            if tod[st] > 1030 and not (st - 1 >= a and h[st - 1] > ibh):
                ok = False
                for i in range(st, min(b, st + 6)):
                    if c[i] < ibh and i >= jh:
                        ok = True
                        break
                if ok:
                    out[s, 2] = sh
        # TPO profile
        out[s, 3] = np.nan
        out[s, 4] = np.nan
        out[s, 5] = np.nan
        if not (np.isfinite(A) and A > 0) or b - a < 20:
            continue
        bs = 0.05 * A
        b0 = int(np.floor(lo / bs))
        nb = int(np.floor(sh / bs)) - b0 + 1
        if nb < 1 or nb > 2000:
            continue
        cnt = np.zeros(nb, np.int64)
        for i in range(a, b):
            i0 = int(np.floor(l[i] / bs)) - b0
            i1 = int(np.floor(h[i] / bs)) - b0
            if i0 < 0:
                i0 = 0
            if i1 > nb - 1:
                i1 = nb - 1
            for q in range(i0, i1 + 1):
                cnt[q] += 1
        mid = (nb - 1) / 2.0
        p = 0
        for q in range(nb):
            if cnt[q] > cnt[p] or (cnt[q] == cnt[p] and abs(q - mid) < abs(p - mid)):
                p = q
        tot = cnt.sum()
        lo_i, hi_i = p, p
        acc = cnt[p]
        while acc < 0.7 * tot:
            up = cnt[hi_i + 1] if hi_i + 1 < nb else -1
            dn = cnt[lo_i - 1] if lo_i - 1 >= 0 else -1
            if up < 0 and dn < 0:
                break
            if up >= dn:
                hi_i += 1
                acc += up
            else:
                lo_i -= 1
                acc += dn
        out[s, 3] = (b0 + p + 0.5) * bs
        out[s, 4] = (b0 + lo_i) * bs
        out[s, 5] = (b0 + hi_i + 1) * bs


def session_table(df):
    """Per (symbol, date str) of the frame's symbols: this session's sh, ibh, z, poc, val, vah, plus a run id."""
    fb = CB.full_bars(df)
    ck = ("sess", id(fb))
    if ck in _MEM:
        return _MEM[ck]
    for kk in [k for k in _MEM if isinstance(k, tuple) and k[0] == "sess"]:
        del _MEM[kk]
    sk = pd.factorize(fb["symbol"].astype(str) + "|" + pd.Series(fb["date"]).astype(str))[0]
    st = np.r_[True, sk[1:] != sk[:-1]]
    ss = np.flatnonzero(st)
    se = np.r_[ss[1:], len(sk)]
    sess = pd.DataFrame({"symbol": fb["symbol"].to_numpy()[ss].astype(str),
                         "date": pd.Series(fb["date"].to_numpy()[ss]).astype(str).to_numpy()})
    sess = sess.merge(_atr_tab(), on=["symbol", "date"], how="left")
    out = np.full((len(ss), 6), np.nan)
    _sessions(ss.astype(np.int64), se.astype(np.int64), fb["tod"].to_numpy(np.int64), fb["h"].to_numpy(float),
              fb["l"].to_numpy(float), fb["c"].to_numpy(float), sess["atr14_1"].to_numpy(float), out)
    for j, nm in enumerate(("sh", "ibh", "z", "poc", "val", "vah")):
        sess[nm] = out[:, j]
    dt = pd.to_datetime(sess["date"])
    sess["run"] = ((sess["symbol"] != sess["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    _MEM[ck] = sess
    return sess


def prior(sess, cols, n):
    """Per session row D: value of col at session D-n of the same run (NaN when absent)."""
    g = sess.groupby("run", sort=False)
    return {f"{c}_{n}": g[c].shift(n) for c in cols}


def map_sess(df, k, tab, cols):
    st = start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": df["date"].astype(str).to_numpy()[st]})
    m = u.merge(tab[["symbol", "date"] + list(cols)], on=["symbol", "date"], how="left")
    assert len(m) == int(st.sum())
    return {c: m[c].to_numpy(float)[np.cumsum(st) - 1] for c in cols}


def daily_hl():
    """Per (symbol, date str D): high / low of D-1, D-2, D-3, D-4 (completed days; restart after a > 7-day gap)."""
    if "dhl" in _MEM:
        return _MEM["dhl"]
    d = CB.lib().daily()[["symbol", "date", "high", "low"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"].astype(str)})
    for n in (1, 2, 3, 4):
        out[f"h{n}"] = d["high"].groupby(g).shift(n)
        out[f"l{n}"] = d["low"].groupby(g).shift(n)
    _MEM["dhl"] = out
    return out
