"""pod-iwm-spy-spread-z-choppy-revert-long - Choppy-day IWM vs SPY intraday spread z-score reversion, long the laggard
leg IWM (LONG).

Source: QuantStart, 'Backtesting an Intraday Mean Reversion Pairs Strategy Between SPY and IWM' (hedge ratio from a
rolling OLS, spread z-score, enter at |z| >= 2, exit at |z| <= 0.5 region).
URL: https://www.quantstart.com/articles/Backtesting-An-Intraday-Mean-Reversion-Pairs-Strategy-Between-SPY-And-IWM

VARIANT of sw-w2-rv-pairs. Stated change: the universe is index ETFs (IWM vs SPY) instead of stocks within a sector;
long-only on the laggard leg (no short leg); a choppy-day gate is added. The hedged version and the QQQ/SPY mirror
are separate pre-declared variants and are NOT scored in this module.

Rules (plain English, LONG IWM):
  Spread s = log(IWM) - b x log(SPY) on continuous 5m closes (09:35..15:55 bars). b = OLS slope of IWM 5m log returns
  on SPY 5m log returns (intraday bars only, overnight excluded) over the 20 prior completed sessions. z = (s - mean
  of s over the last 48 5m bars) / its standard deviation, with today's b applied to the whole 48-bar window.
  1. Chop gate: by the entry bar, SPY's 5m close has switched sides of its session VWAP >= 3 times (VWAP from 09:35,
     typical price x 5m volume), and |SPY return from the open| < 0.4% (context spy_fo).
  2. z <= -2.0 (IWM lagging SPY), bar close 10:30-15:00 ET.
  3. IWM's bar did not make a new session low (its low is not below the running low before the bar).
  Entry: buy IWM at that bar's close, one entry per day. Stop (GEOM S+x): entry - 1 x 5m ATR(14) (atrPct x close).
  Module exit: the close of the first later bar with z >= -0.25 (reversion) or z <= -3.5 (spread stop); else 15:55.
Point-in-time: b uses completed prior sessions only; the z window and VWAP use bars up to the decision bar. Warm-up
reads the previous open month only (never the locked block), so the first ~20 sessions after a gap have no b.
No tweak made. Costs per config/default.yaml (applied by the scorer; unhedged, so one leg).
Educational only - not financial advice."""
import numpy as np
import pandas as pd

import _r212_util as U
import _cwt3_bars as CB
import _r24_bars as R24

SIDE = "long"
GEOM = "S+x"
WINDOW = (1030, 1500)
SYMBOLS = ["IWM"]
CONTEXT = ["spy_fo"]
LAYERS = ["SPY VWAP side switches >= 3 and |spy_fo| < 0.4", "IWM-SPY spread z(48) <= -2.0, 20d OLS hedge ratio",
          "IWM bar not a new session low", "stop 1 x ATR5m, exit z >= -0.25 or z <= -3.5, flat 15:55", "10:30-15:00"]
_ST = {}


def _table(df):
    fb = CB.full_bars(df, symbols=["IWM", "SPY"], warm=True)
    if fb is None or not len(fb):
        return None
    W = fb.pivot_table(index=["date", "tod"], columns="symbol", values="c", aggfunc="last").sort_index()
    if "IWM" not in W or "SPY" not in W:
        return None
    W = W.dropna(subset=["IWM", "SPY"]).reset_index()
    li, ls = np.log(W["IWM"].to_numpy(float)), np.log(W["SPY"].to_numpy(float))
    dstr = W["date"].astype(str).to_numpy()
    newday = np.r_[True, dstr[1:] != dstr[:-1]]
    ri = np.r_[np.nan, np.diff(li)]
    rs = np.r_[np.nan, np.diff(ls)]
    ri[newday], rs[newday] = np.nan, np.nan
    ok = np.isfinite(ri) & np.isfinite(rs)
    D = pd.DataFrame({"d": dstr, "x": np.where(ok, rs, 0), "y": np.where(ok, ri, 0), "n": ok.astype(float)})
    D["xx"], D["xy"] = D["x"] ** 2, D["x"] * D["y"]
    S = D.groupby("d", sort=True)[["x", "y", "xx", "xy", "n"]].sum()
    dt = pd.to_datetime(pd.Series(S.index))
    seg = ((dt - dt.shift()).dt.days > 7).cumsum().to_numpy()
    R = S.groupby(seg).transform(lambda s: s.rolling(20, min_periods=20).sum().shift(1))
    bb = (R["n"] * R["xy"] - R["x"] * R["y"]) / (R["n"] * R["xx"] - R["x"] ** 2)
    bmap = dict(zip(S.index, bb.to_numpy(float)))
    bd = np.array([bmap.get(d, np.nan) for d in dstr])
    w = 48
    s_li, s_ls = pd.Series(li), pd.Series(ls)
    mi, ms = s_li.rolling(w).mean().to_numpy(), s_ls.rolling(w).mean().to_numpy()
    vi, vs = s_li.rolling(w).var(ddof=0).to_numpy(), s_ls.rolling(w).var(ddof=0).to_numpy()
    cv = s_li.rolling(w).cov(s_ls, ddof=0).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        sd = np.sqrt(np.maximum(vi + bd * bd * vs - 2 * bd * cv, 0))
        z = ((li - bd * ls) - (mi - bd * ms)) / np.where(sd > 0, sd, np.nan)
    W["z"] = z
    # SPY session VWAP side switches (bars 09:35..15:00)
    sp = fb[(fb["symbol"] == "SPY") & (fb["tod"] <= 1500)].copy()
    sp["dn"] = pd.to_datetime(pd.Series(sp["date"]).astype(str)).to_numpy("datetime64[D]").astype(np.int64)
    parts = []
    for m in R24._months_of(df):
        V = U._vol_month(m)
        if V is not None:
            parts.append(V[V["symbol"] == "SPY"].copy())
    sw = pd.DataFrame(columns=["date", "tod", "sw"])
    if parts:
        V = pd.concat(parts, ignore_index=True)
        V["dn"], V["tod"] = V["dn"].astype(np.int64), V["tod"].astype(np.int64)
        x = sp.merge(V[["dn", "tod", "v"]], on=["dn", "tod"], how="inner").sort_values(["dn", "tod"])
        tp = (x["h"] + x["l"] + x["c"]).to_numpy(float) / 3
        v = np.nan_to_num(x["v"].to_numpy(float))
        g = x["dn"].to_numpy()
        cvv = pd.Series(v).groupby(g).cumsum().to_numpy()
        cpv = pd.Series(v * tp).groupby(g).cumsum().to_numpy()
        with np.errstate(invalid="ignore", divide="ignore"):
            vw = np.where(cvv > 0, cpv / cvv, np.nan)
        sg = np.sign(x["c"].to_numpy(float) - vw)
        sgs = pd.Series(np.where(sg == 0, np.nan, sg)).groupby(g).ffill().to_numpy()
        prev = pd.Series(sgs).groupby(g).shift(1).to_numpy()
        chg = (np.isfinite(prev) & np.isfinite(sgs) & (prev != sgs)).astype(float)
        x["sw"] = pd.Series(chg).groupby(g).cumsum().to_numpy()
        sw = x[["date", "tod", "sw"]]
    W = W.merge(sw, on=["date", "tod"], how="left")
    W.insert(0, "symbol", "IWM")
    return W[["symbol", "date", "tod", "z", "sw"]]


def _compute(df):
    n = len(df)
    z0 = np.full(n, np.nan)
    if not n:
        return np.zeros(0, bool), z0, z0, z0
    t = _table(df)
    if t is None:
        return np.zeros(n, bool), z0, z0, z0
    r = CB.map_rows(df, t, ["z", "sw"])
    z, sw = r["z"], r["sw"]
    b = U.base(df)
    k = U.key(df)
    tod, c = b["tod"], b["c"]
    sym = df["symbol"].astype(str).to_numpy()
    sfo = U.f(df, "spy_fo")
    with np.errstate(invalid="ignore"):
        m = (sym == "IWM") & (sw >= 3) & (np.abs(sfo) < 0.4)                 # (1)
        m &= (z <= -2.0) & (tod >= 1030) & (tod <= 1500)                    # (2)
        lodp = U.lag(b["lod"], k, 1)
        m &= np.isfinite(lodp) & (b["l"] >= lodp)                           # (3)
        sp = c - b["atr5"]
        m &= sp < c
    return np.asarray(m, bool), sp, z, k


def mask(df) -> np.ndarray:
    try:
        m, sp, z, k = _compute(df)
    except (KeyError, FileNotFoundError):
        n = len(df)
        m, sp, z, k = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan), np.zeros(n, np.int64)
    _ST.clear()
    _ST[id(df)] = (sp, z, k)
    return m


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def exit_index(f, i, stop, target):
    _, z, k = _get(f)
    j = i + 1
    while j < len(f) and k[j] == k[i]:
        if z[j] >= -0.25 or z[j] <= -3.5:
            return j
        j += 1
    return -1
