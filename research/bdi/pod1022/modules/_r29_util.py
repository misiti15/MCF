"""_r29_util - shared helpers for the pod r2_9 modules (Davey trend pullback, Williams smash day, slow-day stochastic,
Dalton rotation factor, Barros failed auction). Not a setup (no SIDE / mask).

All series are causal: a value on row t uses rows <= t of the same group only.
  * Day key = symbol + date (resets every session); symbol key = a continuous 5m chart over the bars the frame carries.
  * Daily values come from lib.daily() via _r25_util / _cwt3_bars (completed days only, the rule-19 locked block is
    not in it, series restart after a > 7-day gap). Here we add the close 10 sessions back (D-10).
  * 30-minute brackets for the Dalton rotation factor: bracket 0 = 09:30-10:00, whose high / low is the running
    HOD / LOD on the 10:00 bar (the frame starts at 09:50, the running HOD / LOD include 09:30-09:50); bracket j >= 1
    = the bars closing in (10:00 + 30(j-1), 10:00 + 30j]. A bracket counts only once its last bar has closed.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _cwt3_bars as CB  # noqa: E402
import _r25_util as R25  # noqa: E402

f, key, start, lag, base, at_tod = CB.f, CB.key, CB.start, CB.lag, CB.base, CB.at_tod
_CACHE = {}


def symkey(df):
    return pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()))[0]


def minutes(tod):
    tod = np.asarray(tod, np.int64)
    return (tod // 100) * 60 + tod % 100 - 570          # minutes since 09:30 at the bar close


def daily_c10():
    if "c10" in _CACHE:
        return _CACHE["c10"]
    d = CB.lib().daily()[["symbol", "date", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"], "c10": d["close"].groupby(g).shift(10)})
    _CACHE["c10"] = out
    return out


def map_c10(df, k):
    t = daily_c10()
    st = start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": df["date"].astype(str).to_numpy()[st]})
    m = u.merge(t, on=["symbol", "date"], how="left")
    return m["c10"].to_numpy(float)[np.cumsum(st) - 1]


def rf_contrib(df, k, b):
    """Per row: (nb, contrib) where nb = number of completed brackets at this bar's close and contrib is an array
    (rows x 13) of each bracket j's RF contribution (+/-1 for the high, +/-1 for the low vs bracket j-1), NaN when
    bracket j is not complete yet. Bracket 0 has no contribution (NaN)."""
    tod = b["tod"]
    mn = minutes(tod)
    nb = mn // 30                                        # completed brackets at this close
    bidx = (mn - 1) // 30                                # bracket the bar belongs to
    hod0 = at_tod(b["hod"], k, tod, 1000)
    lod0 = at_tod(b["lod"], k, tod, 1000)
    nbr = 13
    ng = int(k.max()) + 1 if len(k) else 1
    BH = np.full((ng, nbr), np.nan)
    BL = np.full((ng, nbr), np.nan)
    st = start(k)
    BH[k[st], 0] = hod0[st]
    BL[k[st], 0] = lod0[st]
    sel = (bidx >= 1) & (bidx < nbr)
    t = pd.DataFrame({"k": k[sel], "j": bidx[sel], "h": b["h"][sel], "l": b["l"][sel]})
    if len(t):
        a = t.groupby(["k", "j"]).agg(h=("h", "max"), l=("l", "min")).reset_index()
        BH[a["k"].to_numpy(), a["j"].to_numpy()] = a["h"].to_numpy()
        BL[a["k"].to_numpy(), a["j"].to_numpy()] = a["l"].to_numpy()
    with np.errstate(invalid="ignore"):
        C = np.full((ng, nbr), np.nan)
        C[:, 1:] = np.sign(BH[:, 1:] - BH[:, :-1]) + np.sign(BL[:, 1:] - BL[:, :-1])
    R = C[k]                                             # rows x nbr
    jj = np.arange(nbr)[None, :]
    R = np.where(jj < nb[:, None], R, np.nan)            # only completed brackets
    return nb, R


def rf_total(nb, R):
    """RF over all completed brackets (NaN if fewer than 2 complete, or a bracket is missing)."""
    out = np.nansum(R, axis=1)
    cnt = np.sum(np.isfinite(R), axis=1)
    return np.where((nb >= 2) & (cnt == nb - 1), out, np.nan)


def rf_last(nb, R, n):
    """RF contributions of the last n completed brackets (needs n contributions, i.e. nb >= n + 1)."""
    jj = np.arange(R.shape[1])[None, :]
    w = (jj >= (nb - n)[:, None]) & (jj < nb[:, None])
    v = np.where(w, R, np.nan)
    cnt = np.sum(np.isfinite(v), axis=1)
    return np.where((nb >= n + 1) & (cnt == n), np.nansum(v, axis=1), np.nan)
