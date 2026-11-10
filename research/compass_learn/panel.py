"""COMPASS-LEARN step 1: point-in-time 5-min panel (09:35..15:55) of every compass input, history (1-min cache, locked
block filtered inside the read by mcf.hunch.data.load_1min) + the live days (fetch_live.py). Usage:
    python panel.py <scratch>          -> <scratch>/panel.parquet, <scratch>/days.parquet
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf.hunch import data as HD  # noqa: E402
from mcf.report import compass_live as CL  # noqa: E402

S = Path(sys.argv[1])
XL = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
U = CL.universe()
MARKS = np.arange(575, 956, 5)                      # 09:35 .. 15:55 (minutes since midnight ET)
NM = 390


def period(d: str) -> str:
    if d < "2025-03-01":
        return "TRAIN" if d >= "2024-10-01" else "PRE"
    if d < "2026-01-01":
        return "TRAIN"
    if d < "2026-10-06":
        return "VALID"
    if d < "2026-11-05":
        return "FWD"
    return "LIVE"


def grid(df: pd.DataFrame, cols=("open", "high", "low", "close", "volume")):
    """1-min bars (ET index) -> dict date -> arrays over minute 0..389, forward-filled close; first open."""
    df = df[["open", "high", "low", "close", "volume"]].astype(float)
    m = df.index.hour * 60 + df.index.minute
    df = df[(m >= 570) & (m < 960)]
    m = (df.index.hour * 60 + df.index.minute).values - 570
    d = df.index.strftime("%Y-%m-%d").values
    out = {}
    for day in pd.unique(d):
        k = d == day
        mm = m[k]
        C = np.full(NM, np.nan); C[mm] = df.close.values[k]
        C = pd.Series(C).ffill().values
        H = np.full(NM, np.nan); H[mm] = df.high.values[k]
        L = np.full(NM, np.nan); L[mm] = df.low.values[k]
        TP = np.zeros(NM); V = np.zeros(NM)
        TP[mm] = (df.high.values[k] + df.low.values[k] + df.close.values[k]) / 3; V[mm] = df.volume.values[k]
        out[day] = dict(o=float(df.open.values[k][0]), c=C, h=H, l=L, tpv=np.cumsum(TP * V), cv=np.cumsum(V),
                        last=int(mm.max()))
    return out


def load_hist(sym):
    return HD.load_1min(sym, Path("/home/user/MCF/data/cache_hist/1Min"))


def build(src: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """src: symbol -> grid(). Returns panel (date x mark) and day table."""
    spy = src["SPY"]
    days = sorted(d for d in spy if spy[d]["last"] >= 385)          # last bar starts >= 15:55
    ix = MARKS - 571                                                  # bar that starts at T-1 (closed by T)
    rows, drows = [], []
    for d in days:
        g = spy[d]
        o = g["o"]; c = g["c"][ix]
        fo = c / o - 1
        vw = c / (g["tpv"][ix] / np.maximum(g["cv"][ix], 1)) - 1
        hh = np.fmax.accumulate(np.nan_to_num(g["h"], nan=-np.inf)); ll = np.fmin.accumulate(np.nan_to_num(g["l"], nan=np.inf))
        or15h, or15l = hh[14], ll[14]; or30h, or30l = hh[29], ll[29]
        orb15 = np.where(MARKS >= 585, np.where(c > or15h, 1, np.where(c < or15l, -1, 0)), 0)
        orb30 = np.where(MARKS >= 600, np.where(c > or30h, 1, np.where(c < or30l, -1, 0)), 0)
        qq = src["QQQ"].get(d); iw = src["IWM"].get(d)
        qfo = qq["c"][ix] / qq["o"] - 1 if qq else np.full(len(ix), np.nan)
        ifo = iw["c"][ix] / iw["o"] - 1 if iw else np.full(len(ix), np.nan)
        up, n, up15, n15 = np.zeros(len(ix)), np.zeros(len(ix)), np.zeros(len(ix)), np.zeros(len(ix))
        for s in U:
            x = src.get(s, {}).get(d)
            if x is None:
                continue
            cc = x["c"][ix]; ok = np.isfinite(cc)
            up += (cc > x["o"]) & ok; n += ok
            prev = x["c"][np.maximum(ix - 15, 0)]; prev = np.where(ix - 15 >= 0, prev, x["o"])
            ok2 = ok & np.isfinite(prev)
            up15 += (cc > prev) & ok2; n15 += ok2
        sb = np.zeros(len(ix)); sn = np.zeros(len(ix))
        for s in XL:
            x = src.get(s, {}).get(d)
            if x is None:
                continue
            cc = x["c"][ix]; ok = np.isfinite(cc)
            sb += np.where(ok, np.sign(cc / x["o"] - 1), 0); sn += ok
        r = pd.DataFrame(dict(date=d, T=MARKS, px=c, fo=fo, vw=vw, qfo=qfo, ifo=ifo, br=up / np.maximum(n, 1), br_n=n,
                              br15=up15 / np.maximum(n15, 1), sb=sb, sb_n=sn, orb15=orb15, orb30=orb30,
                              mfe_up=np.fmax.accumulate(fo), mfe_dn=np.fmin.accumulate(fo)))
        rows.append(r)
        drows.append(dict(date=d, open=o, close=g["c"][-1], hi=np.nanmax(g["h"]), lo=np.nanmin(g["l"])))
    P = pd.concat(rows, ignore_index=True)
    D = pd.DataFrame(drows)
    return P, D


def day_feats(D: pd.DataFrame) -> pd.DataFrame:
    D = D.sort_values("date").reset_index(drop=True)
    dt = pd.to_datetime(D.date)
    D["oc"] = D.close / D.open - 1
    D["rng"] = (D.hi - D.lo) / D.open
    # previous day only if it is the previous session (no gap across the locked block)
    contiguous = (dt - dt.shift(1)).dt.days.le(5)
    D["gap"] = np.where(contiguous, D.open / D.close.shift(1) - 1, np.nan)
    D["prev_oc"] = np.where(contiguous, D.oc.shift(1), np.nan)
    D["atr20"] = D.rng.shift(1).rolling(20, min_periods=10).median()
    D["period"] = D.date.map(period)
    return D


if __name__ == "__main__":
    syms = list(dict.fromkeys(["SPY", "QQQ", "IWM"] + XL + U))
    src = {}
    lv = pd.read_parquet(S / "live" / "live_bars.parquet")
    lv["ts"] = pd.to_datetime(lv.ts)
    for i, s in enumerate(syms):
        h = load_hist(s)
        h.index = pd.to_datetime(h.index)
        if h.index.tz is None:
            h.index = h.index.tz_localize("America/New_York")
        h = h.tz_convert("America/New_York")
        x = lv[lv.symbol == s].set_index("ts")[["open", "high", "low", "close", "volume"]]
        h = pd.concat([h[["open", "high", "low", "close", "volume"]], x[x.index > h.index.max()]])
        lo, hi = pd.Timestamp("2024-11-01", tz="America/New_York"), pd.Timestamp("2025-03-01", tz="America/New_York")
        assert not ((h.index >= lo) & (h.index < hi)).any()
        src[s] = grid(h)
        if i % 40 == 0:
            print(i, s, len(src[s]), flush=True)
    P, D = build(src)
    D = day_feats(D)
    P = P.merge(D[["date", "open", "close", "oc", "gap", "prev_oc", "atr20", "period"]], on="date")
    P.to_parquet(S / "panel.parquet"); D.to_parquet(S / "days.parquet")
    print(P.shape, D.groupby("period").size().to_dict())
