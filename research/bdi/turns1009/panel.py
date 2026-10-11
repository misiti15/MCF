"""Indicator panel for the 2026-10-09 turn case studies (owner chart reads). Causal: every value at bar label t uses
only bars up to and including t, i.e. it is known at t+1 (the close of bar t). 5-minute values are mapped onto the
1-minute grid as of the last 5-minute bar that had closed by the close of the 1-minute bar.

build(sym) -> one row per regular-session minute, 2026-09-02..10-09 (history before 09-02 from data/cache/1Min is used
only for the daily ATR warm-up). Columns: <feature>_1m, <feature>_5m, level / context / market / breadth features.
Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from mcf.research.heat import heat_frame  # noqa: E402
from mcf.research.setup_lab import extra_features  # noqa: E402

DATA = HERE / "data"
SECTOR = {"AAPL": "XLK", "CAT": "XLI", "TSLA": "XLY", "SPCX": "IWM"}

_FOCUS = None


def focus() -> pd.DataFrame:
    global _FOCUS
    if _FOCUS is None:
        _FOCUS = pd.read_parquet(DATA / "focus_1m.parquet")
    return _FOCUS


def bars_all(sym: str) -> pd.DataFrame:
    """Extended-hours 1-min bars 09-02..10-09 (SIP fetch)."""
    f = focus()
    return f[f.symbol == sym].set_index("timestamp")[["open", "high", "low", "close", "volume"]].sort_index()


def rth(df: pd.DataFrame) -> pd.DataFrame:
    return df.between_time("09:30", "15:59")


def daily_atr(sym: str) -> pd.Series:
    """14-session mean true range of the regular session, as of the prior close (indexed by date)."""
    c = pd.read_parquet(ROOT / "data" / "cache" / "1Min" / f"{sym}.parquet")
    r = pd.concat([c, rth(bars_all(sym))])
    r = r[~r.index.duplicated(keep="last")].sort_index()
    d = r.groupby(r.index.date).agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    pc = d.close.shift(1)
    tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(14, min_periods=10).mean().shift(1)


# ------------------------------------------------------------------------------------------------ indicators
def wilder(x: pd.Series, n: int) -> pd.Series:
    return x.ewm(alpha=1 / n, adjust=False).mean()


def rsi(c: pd.Series, n: int) -> pd.Series:
    d = c.diff()
    g, l = wilder(d.clip(lower=0), n), wilder(-d.clip(upper=0), n)
    return 100 - 100 / (1 + g / l.replace(0, np.nan))


def cross(a: pd.Series, k: int = 3) -> pd.Series:
    """+1 if a turned positive within the last k bars (and is still positive), -1 if turned negative, else 0."""
    s = np.sign(a)
    up = ((s > 0) & (s.shift(1) <= 0)).astype(int).rolling(k).max()
    dn = ((s < 0) & (s.shift(1) >= 0)).astype(int).rolling(k).max()
    return pd.Series(np.where((up > 0) & (s > 0), 1, np.where((dn > 0) & (s < 0), -1, 0)), index=a.index)


def indicators(b: pd.DataFrame, atr_d: pd.Series, tod_key: pd.Series) -> pd.DataFrame:
    """Bar-level panel for one timeframe. b: continuous regular-session bars (many sessions)."""
    o, h, l, c, v = b.open, b.high, b.low, b.close, b.volume
    day = pd.Series(b.index.date, index=b.index)
    rng = (h - l).replace(0, np.nan)
    x = pd.DataFrame(index=b.index)
    for n in (2, 5, 14):
        x[f"rsi{n}"] = rsi(c, n)
    ll14, hh14 = l.rolling(14).min(), h.rolling(14).max()
    fk = 100 * (c - ll14) / (hh14 - ll14).replace(0, np.nan)
    x["stoch_k"] = fk.rolling(3).mean()
    x["stoch_d"] = x.stoch_k.rolling(3).mean()
    x["willr"] = -100 * (hh14 - c) / (hh14 - ll14).replace(0, np.nan)
    tp = (h + l + c) / 3
    sma_tp = tp.rolling(20).mean()
    md = tp.rolling(20).apply(lambda a: np.mean(np.abs(a - a.mean())), raw=True)
    x["cci20"] = (tp - sma_tp) / (0.015 * md.replace(0, np.nan))
    mf = tp * v
    pos = mf.where(tp > tp.shift(1), 0).rolling(14).sum()
    neg = mf.where(tp < tp.shift(1), 0).rolling(14).sum()
    x["mfi14"] = 100 - 100 / (1 + pos / neg.replace(0, np.nan))
    ema = lambda s, n: s.ewm(span=n, adjust=False).mean()
    macd = ema(c, 12) - ema(c, 26)
    hist = macd - ema(macd, 9)
    x["macd_hist_atr"] = hist / atr_d
    x["macd_cross"] = cross(hist)
    lo20, hi20 = l.rolling(20).min(), h.rolling(20).max()
    at_lo, at_hi = l <= lo20, h >= hi20
    r14 = x.rsi14
    x["bull_div_rsi"] = (at_lo & (r14 > r14.rolling(20).min() + 3)).astype(int)
    x["bear_div_rsi"] = (at_hi & (r14 < r14.rolling(20).max() - 3)).astype(int)
    x["bull_div_macd"] = (at_lo & (hist > hist.rolling(20).min())).astype(int)
    x["bear_div_macd"] = (at_hi & (hist < hist.rolling(20).max())).astype(int)
    sma20, sd20 = c.rolling(20).mean(), c.rolling(20).std()
    x["bb_pctb"] = (c - (sma20 - 2 * sd20)) / (4 * sd20).replace(0, np.nan)
    x["bb_bw"] = 4 * sd20 / sma20
    pc = c.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    atr10, atr14 = wilder(tr, 10), wilder(tr, 14)
    x["kelt_pos"] = (c - ema(c, 20)) / (2 * atr10).replace(0, np.nan)
    cv = v.groupby(day).cumsum().replace(0, np.nan)
    vwap = (tp * v).groupby(day).cumsum() / cv
    var = (tp * tp * v).groupby(day).cumsum() / cv - vwap ** 2
    x["vwap_z"] = (c - vwap) / np.sqrt(var.clip(lower=0)).replace(0, np.nan)
    e9, e21 = ema(c, 9), ema(c, 21)
    x["ema9_21_atr"] = (e9 - e21) / atr_d
    x["ema_cross"] = cross(e9 - e21)
    x["c_ema9_atr"] = (c - e9) / atr_d
    x["sma50_dist_atr"] = (c - c.rolling(50).mean()) / atr_d
    x["sma200_dist_atr"] = (c - c.rolling(200).mean()) / atr_d
    up, dn = h.diff(), -l.diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=b.index)
    ndm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=b.index)
    pdi, ndi = 100 * wilder(pdm, 14) / atr14, 100 * wilder(ndm, 14) / atr14
    x["adx"] = wilder(100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, np.nan), 14)
    x["di_diff"] = pdi - ndi
    x["atr_exp"] = tr.rolling(5).mean() / tr.rolling(60).mean().replace(0, np.nan)
    x["vol_z"] = (v - v.rolling(20).mean()) / v.rolling(20).std().replace(0, np.nan)
    # relative volume vs the same minute-of-day over the prior 20 sessions
    piv = v.groupby([day, tod_key]).sum().unstack()
    avg = piv.shift(1).rolling(20, min_periods=10).mean()
    rv = v / pd.Series(avg.stack().reindex(list(zip(day, tod_key))).to_numpy(), index=b.index)
    x["rvol_tod"] = rv
    x["climax"] = ((x.vol_z > 3) & (rng > 2 * (h - l).rolling(20).mean())).astype(int)
    sgn = np.sign(c.diff()).fillna(0)
    obv = (sgn * v).cumsum()
    x["obv_slope"] = (obv - obv.shift(10)) / v.rolling(10).sum().replace(0, np.nan)
    x["bull_div_obv"] = (at_lo & (obv > obv.rolling(20).min())).astype(int)
    x["bear_div_obv"] = (at_hi & (obv < obv.rolling(20).max())).astype(int)
    clv = ((c - l) - (h - c)) / rng
    adv = (clv.fillna(0) * v)
    x["cmf20"] = adv.rolling(20).sum() / v.rolling(20).sum().replace(0, np.nan)
    adl = adv.cumsum()
    x["adl_slope"] = (adl - adl.shift(10)) / v.rolling(10).sum().replace(0, np.nan)
    body = (c - o).abs()
    x["upper_wick"] = (h - np.maximum(o, c)) / rng
    x["lower_wick"] = (np.minimum(o, c) - l) / rng
    x["bull_engulf"] = ((c > o) & (o.shift(1) > c.shift(1)) & (c >= o.shift(1)) & (o <= c.shift(1))).astype(int)
    x["bear_engulf"] = ((c < o) & (c.shift(1) > o.shift(1)) & (o >= c.shift(1)) & (c <= o.shift(1))).astype(int)
    x["hammer"] = ((x.lower_wick >= 0.6) & (body / rng <= 0.35)).astype(int)
    x["shooting_star"] = ((x.upper_wick >= 0.6) & (body / rng <= 0.35)).astype(int)
    x["inside"] = ((h <= h.shift(1)) & (l >= l.shift(1))).astype(int)
    x["outside"] = ((h > h.shift(1)) & (l < l.shift(1))).astype(int)
    col = np.sign(c - o)
    grp = (col != col.shift(1)).cumsum()
    x["run_len"] = col * col.groupby(grp).cumcount().add(1)        # +n green run, -n red run
    for k in (5, 10, 30):
        x[f"roc{k}_atr"] = (c - c.shift(k)) / atr_d
    return x


def resample5(b1: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for d, g in b1.groupby(b1.index.date):
        parts.append(g.resample("5min", origin="start_day", offset="30min").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna(subset=["open"]))
    return pd.concat(parts)


def build(sym: str) -> pd.DataFrame:
    ext = bars_all(sym)
    b1 = rth(ext)
    days = pd.Series(b1.index.date, index=b1.index)
    atr = daily_atr(sym)
    atr_d = days.map(atr)
    tod1 = pd.Series(b1.index.hour * 60 + b1.index.minute, index=b1.index)
    p1 = indicators(b1, atr_d, tod1).add_suffix("_1m")
    b5 = resample5(b1)
    d5 = pd.Series(b5.index.date, index=b5.index)
    tod5 = pd.Series(b5.index.hour * 60 + b5.index.minute, index=b5.index)
    p5 = indicators(b5, d5.map(atr), tod5)
    hf = heat_frame(b5)
    ef = extra_features(b5, hf)
    p5["heat"] = hf["heat"]
    p5["mf_buyPressure"] = hf["buyPressure"]
    p5["lab_flow3"] = ef["flow3"]
    p5 = p5.add_suffix("_5m")
    p5.index = p5.index + pd.Timedelta(minutes=5)        # known at 5-min bar end
    x = b1.copy()
    x["atr_d"] = atr_d
    x["known"] = x.index + pd.Timedelta(minutes=1)
    x = pd.merge_asof(x.reset_index(), p5.reset_index().rename(columns={"timestamp": "known5"}).sort_values("known5"),
                      left_on="known", right_on="known5", direction="backward").set_index("timestamp")
    x = x.join(p1)
    # levels, in daily ATRs (signed: close - level)
    c, a = x.close, x.atr_d
    dd = pd.Series(x.index.date, index=x.index)
    dly = b1.groupby(b1.index.date).agg(high=("high", "max"), low=("low", "min"), close=("close", "last"),
                                         open=("open", "first"))
    x["day_open"] = dd.map(dly.open)
    x["prev_close"] = dd.map(dly.close.shift(1))
    x["pdh"], x["pdl"] = dd.map(dly.high.shift(1)), dd.map(dly.low.shift(1))
    pm = ext[(ext.index.hour >= 4) & ((ext.index.hour < 9) | ((ext.index.hour == 9) & (ext.index.minute < 30)))]
    pmd = pm.groupby(pm.index.date).agg(high=("high", "max"), low=("low", "min"))
    x["pmh"], x["pml"] = dd.map(pmd.high), dd.map(pmd.low)
    x["hod"] = x.high.groupby(dd).cummax()
    x["lod"] = x.low.groupby(dd).cummin()
    for k in ("day_open", "prev_close", "pdh", "pdl", "pmh", "pml"):
        x[f"d_{k}_atr"] = (c - x[k]) / a
    x["dist_hod_atr"] = (x.hod - c) / a
    x["dist_lod_atr"] = (c - x.lod) / a
    x["from_open_atr"] = x.d_day_open_atr
    x["gap_atr"] = (x.day_open - x.prev_close) / a
    x["round1_atr"] = (c - c.round()).abs() / a
    x["round5_atr"] = (c - (c / 5).round() * 5).abs() / a
    x["round10_atr"] = (c - (c / 10).round() * 10).abs() / a
    return x


def market_cols(x: pd.DataFrame, sym: str) -> pd.DataFrame:
    """SPY / QQQ / sector context at the same minute, residual (beta-adjusted) move, breadth."""
    out = x.copy()
    r_stock = out.close.pct_change()
    for m, tag in (("SPY", "spy"), ("QQQ", "qqq"), (SECTOR[sym], "sec")):
        mb = rth(bars_all(m))
        md = pd.Series(mb.index.date, index=mb.index)
        mo = md.map(mb.groupby(mb.index.date).open.first())
        mx = pd.DataFrame(index=mb.index)
        mx[f"{tag}_from_open_pct"] = (mb.close / mo - 1) * 100
        mx[f"{tag}_rsi14_1m"] = rsi(mb.close, 14)
        tp = (mb.high + mb.low + mb.close) / 3
        cv = mb.volume.groupby(md).cumsum()
        vw = (tp * mb.volume).groupby(md).cumsum() / cv
        var = (tp * tp * mb.volume).groupby(md).cumsum() / cv - vw ** 2
        mx[f"{tag}_vwap_z"] = (mb.close - vw) / np.sqrt(var.clip(lower=0)).replace(0, np.nan)
        mx[f"{tag}_ret30_pct"] = (mb.close / mb.close.shift(30) - 1) * 100
        mx[f"{tag}_close"] = mb.close
        out = out.join(mx)
    # rolling beta to SPY on 5-min returns over the prior 20 sessions (one value per session, as of the prior close)
    s5 = out.close.resample("5min").last().dropna()
    m5 = out.spy_close.resample("5min").last().dropna()
    j = pd.concat([s5.pct_change(), m5.pct_change()], axis=1, keys=["s", "m"]).dropna()
    j["d"] = j.index.date
    betas = {}
    ds = sorted(j.d.unique())
    for i, d in enumerate(ds):
        w = j[j.d.isin(ds[max(0, i - 20):i])]
        betas[d] = (w.s.cov(w.m) / w.m.var()) if len(w) > 200 else np.nan
    out["beta_spy"] = pd.Series(out.index.date, index=out.index).map(betas)
    r30s = out.close / out.close.shift(30) - 1
    out["resid30_atr"] = (r30s - out.beta_spy * out.spy_ret30_pct / 100) * out.close / out.atr_d
    br = pd.read_parquet(DATA / "breadth.parquet")
    out = out.join(br[["br_above_vwap", "br_above_open", "br_new30h", "br_new30l"]])
    out["br_hl_net"] = out.br_new30h - out.br_new30l
    _ = r_stock
    return out


if __name__ == "__main__":
    for s in ("AAPL", "SPCX", "CAT", "TSLA"):
        p = market_cols(build(s), s)
        p.to_parquet(DATA / f"panel_{s}.parquet")
        print(s, p.shape, p.index.min(), p.index.max())
