"""pod-oa-narrow-first-hour-pm-break-long - Narrow first hour, then an afternoon break of the first-hour high on
expanding volume (LONG).

Source: Option Alpha, 'Opening Range Breakout' study (SPY opening ranges split into four size groups to test trend vs
reversion after the first hour).
URL: https://optionalpha.com/blog/opening-range-breakout

VARIANT of pod-oa-wide-first-hour-continuation. Stated change: the opposite size quartile (narrow), a later window
(11:30-14:30) and a volume-expansion requirement on the break. Not nr7-orb: the gate is the intraday first-hour
width, not a daily NR7 bar.

Rules (plain English, LONG), SYMBOLS SPY, QQQ. Conditions 1-2 on SPY, 3-4 on the traded symbol:
  1. SPY's first-hour range (HOD - LOD on the 10:30 bar, 09:30-10:30, as % of price) is <= the 25th percentile of its
     own first-hour ranges over the trailing 20 completed sessions (prior sessions only, at least 15 required).
  2. At the 10:30 bar close SPY is above the prior close and above session VWAP.
  3. Bar close 11:30-14:30 ET: a 5m close > first-hour high x 1.0003, on 5m volume >= 1.3 x the symbol's average
     volume for that same bar time over the 20 prior sessions (min 10; 1-min vendor bars aggregated in _r24_bars).
  4. No earlier failed break this session: no bar after 10:30 and before this one closed above the first-hour high
     and then closed back below it within the next 3 bars.
  Entry: that close. Stop (GEOM S): first-hour midpoint. Target: first-hour high + 1 x first-hour range; else 15:55.
Point-in-time: first-hour high / low are known from the 10:30 bar; the trailing quartile and volume baselines use prior
sessions only; condition 4 uses only bars before the entry bar. Optional high-beta stock extension not scored.
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
import numpy as np
import pandas as pd

import _r212_util as U
import _cwt3_bars as CB
import _r24_bars as R24

SIDE = "long"
GEOM = "S"
WINDOW = (1130, 1430)
SYMBOLS = ["SPY", "QQQ"]
LAYERS = ["SPY first-hour range <= trailing-20 P25", "SPY 10:30 above prior close and VWAP",
          "close > FH high + 0.03% on vol >= 1.3x time-of-day avg, 11:30-14:30", "no earlier failed FH-high break",
          "stop FH mid, target FH high + FH range, flat 15:55"]
_ST = {}
_DC = {}


def _fh_table():
    if "t" in _DC:
        return _DC["t"]
    L = CB.lib()
    rows = []
    for mo in L.months():
        x = L.load_month(mo, columns=["symbol", "date", "tod", "close", "dist_hod_atr", "dist_lod_atr", "atr_d"])
        rows.append(x[(x["symbol"].astype(str) == "SPY") & (x["tod"] == 1030)])
    x = pd.concat(rows, ignore_index=True)
    x["rng"] = (x["dist_hod_atr"] + x["dist_lod_atr"]) * x["atr_d"] / x["close"] * 100
    x = x.sort_values("date").reset_index(drop=True)
    x["p25"] = x["rng"].shift(1).rolling(20, min_periods=15).quantile(0.25)
    x["date"] = x["date"].astype(str)
    _DC["t"] = x[["date", "rng", "p25"]]
    return _DC["t"]


def _vol(df):
    months = R24._months_of(df)
    allm = set(CB.lib().months()) - CB._LOCKED_MONTHS
    load = sorted(set([CB.prev_month(months[0])] if CB.prev_month(months[0]) in allm else []) | set(months))
    parts = []
    for m in load:
        p = R24._OUT / "bars" / f"month={m}.parquet"
        if p.exists():
            v = pd.read_parquet(p, columns=["symbol", "dn", "tod", "v"])
            parts.append(v[v["symbol"].isin(SYMBOLS)])
    V = pd.concat(parts, ignore_index=True)
    V["symbol"] = V["symbol"].astype(str)
    V["dn"], V["tod"] = V["dn"].astype(np.int64), V["tod"].astype(np.int64)
    V = V.sort_values(["symbol", "tod", "dn"]).reset_index(drop=True)
    V["avg"] = V.groupby(["symbol", "tod"])["v"].transform(lambda s: s.shift(1).rolling(20, min_periods=10).mean())
    dn = pd.to_datetime(pd.Series(df["date"].to_numpy()).astype(str)).to_numpy("datetime64[D]").astype(np.int64)
    kk = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "dn": dn, "tod": df["tod"].to_numpy(np.int64)})
    mm = kk.merge(V[["symbol", "dn", "tod", "v", "avg"]], on=["symbol", "dn", "tod"], how="left")
    return mm["v"].to_numpy(float), mm["avg"].to_numpy(float)


def _compute(df):
    n = len(df)
    b = U.base(df)
    k = U.key(df)
    tod, c = b["tod"], b["c"]
    ds = U.dstr(df)
    sym = df["symbol"].astype(str).to_numpy()
    t = _fh_table()
    tm = dict(zip(t["date"], (t["rng"] <= t["p25"]).to_numpy()))
    narrow = np.array([bool(tm.get(d, False)) for d in ds]) if n else np.zeros(0, bool)
    s30 = (sym == "SPY") & (tod == 1030)
    spy_ok = {d: bool(x) for d, x in zip(ds[s30], ((c > b["pc"]) & (c > b["vwap"]))[s30])}
    sok = np.array([spy_ok.get(d, False) for d in ds]) if n else np.zeros(0, bool)
    H = U.at_tod(b["hod"], k, tod, 1030)
    L = U.at_tod(b["lod"], k, tod, 1030)
    v, avg = _vol(df)
    # (4) earlier failed break: close > H at bar j (tod > 1030) followed by a close < H within 3 bars
    failed_before = np.zeros(n, bool)
    st = np.flatnonzero(CB.start(k))
    en = np.r_[st[1:], n]
    for a, e in zip(st, en):
        flag = False
        fb_at = []
        for i in range(a, e):
            # a failure becomes known at the bar that closes back below; it blocks bars after that
            failed_before[i] = flag
            if tod[i] > 1030 and np.isfinite(H[i]):
                if c[i] < H[i] and any(i - j <= 3 for j in fb_at):
                    flag = True
                if c[i] > H[i]:
                    fb_at.append(i)
    with np.errstate(invalid="ignore"):
        m = narrow & sok                                                   # (1) (2)
        m &= (tod >= 1130) & (tod <= 1430) & (c > H * 1.0003)              # (3)
        m &= v >= 1.3 * avg
        m &= ~failed_before                                                # (4)
        sp = (H + L) / 2
        tg = H + (H - L)
        m &= (sp < c) & (tg > c)
    return np.asarray(m, bool), sp, tg


def mask(df) -> np.ndarray:
    try:
        m, sp, tg = _compute(df)
    except (KeyError, FileNotFoundError):
        m, sp, tg = np.zeros(len(df), bool), np.full(len(df), np.nan), np.full(len(df), np.nan)
    _ST.clear()
    _ST[id(df)] = (sp, tg)
    return m


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
