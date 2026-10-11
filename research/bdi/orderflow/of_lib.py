"""OF-A shared library: load 1-second records, build the order-flow feature panel (NOTES 1.2), prior-session
normalisers and thresholds, bar-level signatures (C3b / C6), session regimes. Educational only - not financial advice."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from fetch_agg import DATA, MIN, NSEC, SEC, SYMBOLS, sessions

DAYS = sessions()                      # 21: 09-11 warmup + 20 scored
SCORED = DAYS[1:]
H1, H2 = SCORED[:10], SCORED[10:]
W0, W1 = 1200, 21600                   # 09:50:00 .. 15:30:00 (entry window, seconds after 09:30)
FLOW = ["dlt10", "dlt30", "dlt60", "dlt300", "imb60", "cvd_div300", "ofi10", "ofi60", "qimb10", "big60", "sweep30",
        "iso30", "burst10", "absorb60", "lit60", "fp_stack", "fp_low_d", "fp_high_d", "spread_z", "flicker10"]
SIGNED = FLOW[:18]
PRICE = ["r10", "r60", "r300"]


def roll(x: np.ndarray, k: int) -> np.ndarray:
    c = np.concatenate([[0.0], np.cumsum(x, dtype=float)])
    out = c[k:] - c[:-k]
    return np.concatenate([c[1:k], out])  # first k-1 seconds: partial sums


def load_day(sym: str, day: str) -> pd.DataFrame | None:
    f = SEC / sym / f"{day}.parquet"
    if not f.exists():
        return None
    d = pd.read_parquet(f).set_index("sec").reindex(np.arange(NSEC))
    flows = ["ofi", "n_q", "n_midchg", "n_tr", "vol", "bvol", "svol", "bvol_q", "svol_q", "lit_b", "lit_s", "iso_b",
             "iso_s", "big_b", "big_s", "odd_vol", "dollar", "max_sz", "sweep_b", "sweep_s"]
    d[flows] = d[flows].fillna(0.0)
    q = ["bid", "ask", "bsz", "asz"]
    d[q] = d[q].ffill().bfill()
    sp = (d.ask - d.bid)
    qi = (d.bsz - d.asz) / (d.bsz + d.asz).replace(0, np.nan)
    d["spread_tw"] = d.spread_tw.fillna(sp.shift(1)).fillna(sp)
    d["qimb_tw"] = d.qimb_tw.fillna(qi.shift(1)).fillna(qi).fillna(0.0)
    d["mid"] = (d.bid + d.ask) / 2
    m = MIN / sym / f"{day}.parquet"
    d.attrs["fp"] = pd.read_parquet(m) if m.exists() else None
    return d


def day_stats(d: pd.DataFrame) -> dict:
    lm = np.log(d.mid.to_numpy())
    st = {"vps": float(d.vol.sum() / NSEC), "depth": float(((d.bsz + d.asz) / 2).mean()),
          "tps": float(d.n_tr.sum() / NSEC), "qps": float(d.n_q.sum() / NSEC),
          "spread_med": float(np.nanmedian(d.spread_tw.to_numpy()))}
    for k in (10, 60, 300):
        st[f"sig{k}"] = float(np.nanstd(np.diff(lm[::k])))
    st["sd_dlt300_raw_over_v"] = float(np.nanstd(roll((d.bvol - d.svol).to_numpy(), 300)[300:]) / max(st["vps"] * 300, 1e-9))
    return st


def ref_stats(stats: list[dict]) -> dict:
    return {k: float(np.mean([s[k] for s in stats])) for k in stats[0]}


def features(d: pd.DataFrame, ref: dict) -> pd.DataFrame:
    """Feature panel, one row per second (NOTES 1.2). ref: prior sessions' mean day_stats."""
    b, s, v = d.bvol.to_numpy(), d.svol.to_numpy(), d.vol.to_numpy()
    mid = d.mid.to_numpy()
    lm = np.log(mid)
    V = lambda k: max(ref["vps"] * k, 1e-9)
    x = {}
    for k in (10, 30, 60, 300):
        x[f"dlt{k}"] = roll(b - s, k) / V(k)
    bs60 = roll(b + s, 60)
    x["imb60"] = roll(b - s, 60) / np.maximum(bs60, 1.0)
    r = {}
    for k in (10, 60, 300):
        r[k] = np.concatenate([np.full(k, np.nan), lm[k:] - lm[:-k]])
        x[f"r{k}"] = r[k]
    x["cvd_div300"] = x["dlt300"] / max(ref["sd_dlt300_raw_over_v"], 1e-9) - r[300] / max(ref["sig300"], 1e-9)
    D = max(ref["depth"], 1e-9)
    ofi = d.ofi.to_numpy()
    x["ofi10"], x["ofi60"] = roll(ofi, 10) / D, roll(ofi, 60) / D
    x["qimb10"] = roll(d.qimb_tw.to_numpy(), 10) / 10
    x["big60"] = roll((d.big_b - d.big_s).to_numpy(), 60) / V(60)
    x["sweep30"] = roll((d.sweep_b - d.sweep_s).to_numpy(), 30) / V(30)
    x["iso30"] = roll((d.iso_b - d.iso_s).to_numpy(), 30) / V(30)
    x["burst10"] = roll(d.n_tr.to_numpy(), 10) / max(ref["tps"] * 10, 1e-9) * np.sign(np.nan_to_num(r[10]))
    quiet = np.abs(np.nan_to_num(r[60], nan=1.0)) < 0.5 * ref["sig60"]
    x["absorb60"] = np.where(quiet & (np.abs(x["imb60"]) >= 0.2), -np.sign(x["dlt60"]) * roll(v, 60) / V(60), 0.0)
    x["lit60"] = roll((d.lit_b - d.lit_s).to_numpy(), 60) / V(60)
    fp = d.attrs.get("fp")
    for c_out, c_in in (("fp_stack", None), ("fp_low_d", "fp_low_d"), ("fp_high_d", "fp_high_d")):
        arr = np.zeros(NSEC)
        if fp is not None and len(fp):
            per_min = np.full(NSEC // 60 + 1, 0.0)
            vals = (fp.fp_stack_b - fp.fp_stack_s) if c_in is None else fp[c_in]
            per_min[fp.m.to_numpy(int).clip(0, NSEC // 60)] = vals.to_numpy(float)
            mm = np.arange(NSEC) // 60 - 1                 # last completed minute
            arr = np.where(mm >= 0, per_min[mm.clip(0)], 0.0)
        x[c_out] = arr
    x["spread_z"] = d.spread_tw.to_numpy() / max(ref["spread_med"], 1e-9)
    x["flicker10"] = roll(d.n_q.to_numpy(), 10) / max(ref["qps"] * 10, 1e-9)
    out = pd.DataFrame(x)
    return out.astype(np.float32)


# ------------------------------------------------------------------------------------------------ bars / signatures
def bars1m() -> pd.DataFrame:
    b = pd.read_parquet(DATA / "bars1m.parquet")
    b["date"] = b.t.dt.date.astype(str)
    return b


def daily_atr(b1: pd.DataFrame) -> pd.Series:
    """14-session mean true range of the regular session as of the prior close, index (symbol, date)."""
    d = b1.groupby(["symbol", "date"]).agg(high=("high", "max"), low=("low", "min"), close=("close", "last"),
                                           open=("open", "first")).reset_index()
    out = []
    for sym, g in d.groupby("symbol"):
        g = g.sort_values("date")
        pc = g.close.shift(1)
        tr = pd.concat([g.high - g.low, (g.high - pc).abs(), (g.low - pc).abs()], axis=1).max(axis=1)
        g = g.assign(atr_d=tr.rolling(14, min_periods=10).mean().shift(1))
        out.append(g)
    return pd.concat(out).set_index(["symbol", "date"])


def regimes(b1: pd.DataFrame) -> pd.Series:
    """Session class up/flat/down by the 40 names' median open-to-close, terciles over the 20 scored sessions."""
    d = b1[b1.date.isin(SCORED)].groupby(["symbol", "date"]).agg(o=("open", "first"), c=("close", "last")).reset_index()
    med = ((d.c / d.o - 1) * 100).groupby(d.date).median()
    lo, hi = np.quantile(med, [1 / 3, 2 / 3])
    return pd.Series(np.where(med <= lo, "down", np.where(med >= hi, "up", "flat")), index=med.index)


def _rsi(c: pd.Series, n: int) -> pd.Series:
    dd = c.diff()
    g = dd.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    l = (-dd.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + g / l.replace(0, np.nan))


def _cross(a: pd.Series, k: int = 3) -> pd.Series:
    s = np.sign(a)
    up = ((s > 0) & (s.shift(1) <= 0)).astype(int).rolling(k).max()
    dn = ((s < 0) & (s.shift(1) >= 0)).astype(int).rolling(k).max()
    return pd.Series(np.where((up > 0) & (s > 0), 1, np.where((dn > 0) & (s < 0), -1, 0)), index=a.index)


def signatures_1m(b: pd.DataFrame, atr: pd.Series) -> pd.DataFrame:
    """C3b / C6 per 1-minute bar for one symbol (as turns1009/signatures.py, panel.py definitions). b: that symbol's
    continuous RTH 1-minute bars. Returns date, m (minute index after 09:30 of the bar start), c3b_long/short,
    c6_long/short; the signal is known at the bar close (second (m+1)*60)."""
    b = b.sort_values("t").set_index("t")
    o, h, l, c, v = b.open, b.high, b.low, b.close, b.volume
    day = b.date
    atr_d = pd.Series(list(zip(b.symbol, day)), index=b.index).map(atr).astype(float)
    ema = lambda s, n: s.ewm(span=n, adjust=False).mean()
    macd = ema(c, 12) - ema(c, 26)
    hist = macd - ema(macd, 9)
    mc = _cross(hist)
    rng = (h - l).replace(0, np.nan)
    body = (c - o).abs()
    upw, low = (h - np.maximum(o, c)) / rng, (np.minimum(o, c) - l) / rng
    be = (c > o) & (o.shift(1) > c.shift(1)) & (c >= o.shift(1)) & (o <= c.shift(1))
    se = (c < o) & (c.shift(1) > o.shift(1)) & (o >= c.shift(1)) & (c <= o.shift(1))
    ham = (low >= 0.6) & (body / rng <= 0.35)
    star = (upw >= 0.6) & (body / rng <= 0.35)
    trig_l = (mc == 1) | be | ham
    trig_s = (mc == -1) | se | star
    roc10 = (c - c.shift(10)) / atr_d
    # 5-minute bars, known at their end
    parts = []
    for dd, g in b.groupby("date"):
        parts.append(g.resample("5min", origin="start_day", offset="30min").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna(subset=["open"]).assign(date=dd))
    b5 = pd.concat(parts)
    tp = (b5.high + b5.low + b5.close) / 3
    cv = b5.volume.groupby(b5.date).cumsum().replace(0, np.nan)
    vw = (tp * b5.volume).groupby(b5.date).cumsum() / cv
    var = (tp * tp * b5.volume).groupby(b5.date).cumsum() / cv - vw ** 2
    p5 = pd.DataFrame({"vwap_z_5m": (b5.close - vw) / np.sqrt(var.clip(lower=0)).replace(0, np.nan),
                       "rsi14_5m": _rsi(b5.close, 14)}, index=b5.index + pd.Timedelta(minutes=5))
    x = pd.DataFrame({"date": day, "roc10": roc10, "trig_l": trig_l, "trig_s": trig_s}, index=b.index)
    x["known"] = x.index + pd.Timedelta(minutes=1)
    x = pd.merge_asof(x.reset_index().sort_values("known"), p5.reset_index().rename(columns={"index": "k5", "t": "k5"}).sort_values("k5"),
                      left_on="known", right_on="k5", direction="backward").set_index("t").sort_index()
    out = []
    dates = sorted(x.date.unique())
    for i, dd in enumerate(dates):
        if dd not in DAYS or i < 20:
            continue
        ref = x[x.date.isin(dates[i - 20:i])]
        g = x[x.date == dd]
        qv = {k: ref[k].quantile([0.1, 0.9]).to_numpy() for k in ("vwap_z_5m", "rsi14_5m", "roc10")}
        lo = lambda k: g[k] <= qv[k][0]
        hi = lambda k: g[k] >= qv[k][1]
        m = (g.index.hour * 60 + g.index.minute - 570).to_numpy()
        out.append(pd.DataFrame({"date": dd, "m": m,
                                 "c3b_long": (lo("vwap_z_5m") & lo("rsi14_5m") & g.trig_l).to_numpy(),
                                 "c3b_short": (hi("vwap_z_5m") & hi("rsi14_5m") & g.trig_s).to_numpy(),
                                 "c6_long": (lo("roc10") & g.trig_l).to_numpy(),
                                 "c6_short": (hi("roc10") & g.trig_s).to_numpy()}))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def meta() -> pd.DataFrame:
    p = DATA / "meta.jsonl"
    return pd.DataFrame([json.loads(l) for l in p.read_text().splitlines()]) if p.exists() else pd.DataFrame()
