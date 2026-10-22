"""ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD - "RSI Collapse Dip Buy, Nasdaq-below-VWAP only (all day)".
research/bdi/st7_1022 (owner 2026-10-22 review of ST7-rsi50dn-long-pm-t1s1-FD). A NEW, independent variant of the
full-day ST7 parent (research/bdi/fullday/ST7-rsi50dn-long-pm-t1s1-FD.py, copied; logic identical) with ONE added layer:
QQQ's own close is at or below its session VWAP at the same 5-minute bar (`qqq_vwap` <= 0, QQQ vwapDistPct).
Plain English: buy a liquid stock whose RSI(14) collapses from 50+ to 30 or less in one 5-minute bar while it is > 1%
below its open and buyers still lead the last 19 bars - but only while the Nasdaq itself is below its VWAP (the stock's
drop is part of a market dip). Skips the "stock falls alone while the market is strong" entries (the 10-21 losses).
Side long, exit t1s1 (R = 0.25 x daily ATR, flat by 15:55). Run with min_adv 95000000 and window [950, 1500].
2-year open history (locked block never read; production + time-of-day costs, x3 extended tier; first signal per
symbol-day): train n 183 +0.092R / valid n 351 +0.141R, day-clustered t 2.27 (lineage bar 4.97: NOT met), beats
same-minute random longs by +0.062 / +0.189R, largest day 14.6% of total R. By regime (2y avg R): Bull +0.654,
Bear +0.059, Choppy +0.188, Quiet +0.091 (parent: +0.226 / -0.177 / +0.126 / +0.021).
CAVEAT: the QQQ-VWAP layer was chosen AFTER the diagnosis looked at both periods (post-hoc; counted) - VALID is not
out-of-sample for this choice. Meets the owner's near-miss merit rule only.
NEEDS LIVE CODE: the live lab context has spy_fo / qqq_fo / breadth / breadth_open but no `qqq_vwap`; until a
`qqq_vwap` context column exists the mask fires nothing (missing column -> NaN -> False: fail safe).
Educational only - not financial advice."""
import numpy as np

SIDE = "long"
GEOM = "t1s1"
TRIGGER = ['rsi50', 'dn', None]
FILTERS = [['rsi_ext', 70], ['fo_against', 1.0], ['bp_with', None], ['qqq_vwap_below', 0.0]]
WINDOW = None  # full day (source: WINDOW = (1335, 1500)); window = YAML [950, 1500]
LAYERS = [
    "RSI(14) crosses below 50",
    "RSI(14) <= 30",
    "stock down > 1.0% from the open",
    "19-bar buy pressure > 0",
    "QQQ at or below its own session VWAP at the same bar",
    "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])",
]
GENERIC = {"vwap_with", "vwap_against", "ema_with", "ema_against", "sma50_with", "sma50_against", "slope20_with",
           "slope20_against", "macd_with", "macd_against", "bp_with", "bp_against", "flow3_with", "flow3_against",
           "rsi50_with", "gap_with", "gap_against"}


def mask(df) -> np.ndarray:
    def col(k):
        return df[k].to_numpy(dtype=float)

    n = len(df)
    if "symbol" in df and "date" in df:     # offline frames hold many symbol-days: no carry-over
        key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
        new = np.r_[True, key[1:] != key[:-1]]
    else:
        new = np.r_[True, np.zeros(max(0, n - 1), bool)]
    grp = np.cumsum(new)

    def prev(x):
        p = np.r_[np.nan, x[:-1]]
        p[new] = np.nan
        return p

    def ffill(x):  # forward fill within the symbol-day
        idx = np.where(np.isfinite(x), np.arange(n), -1)
        idx = np.maximum.accumulate(idx)
        out = np.where(idx >= 0, x[np.maximum(idx, 0)], np.nan)
        start = np.maximum.accumulate(np.where(new, np.arange(n), 0))
        out[idx < start] = np.nan
        return out

    c, atr, tod = col("close"), col("atr_d"), col("tod")
    vw = c / (1 + col("vwapDistPct") / 100)
    z = (c - vw) / atr                                   # VWAP stretch in daily ATR
    hod = c + col("dist_hod_atr") * atr
    lod = c - col("dist_lod_atr") * atr
    pdh = c + col("dist_pdh_atr") * atr
    pdl = c - col("dist_pdl_atr") * atr
    orh = ffill(np.where(tod == 1000, hod, np.nan))      # opening range 09:30-10:00
    orl = ffill(np.where(tod == 1000, lod, np.nan))
    s = 1.0 if SIDE == "long" else -1.0

    def up(x, lvl=0.0):
        return (x > lvl) & (prev(x) <= lvl)

    def dn(x, lvl=0.0):
        return (x < lvl) & (prev(x) >= lvl)

    def trig(fam, d, p):
        if fam == "vwap":
            return up(z) if d == "up" else dn(z)
        if fam == "ema":
            return up(col("emaDiff")) if d == "up" else dn(col("emaDiff"))
        if fam == "macd":
            return up(col("macdPct")) if d == "up" else dn(col("macdPct"))
        if fam == "rsi14":
            return up(col("rsi"), p) if d == "up" else dn(col("rsi"), 100 - p)
        if fam == "rsi5":
            return up(col("rsi5"), p) if d == "up" else dn(col("rsi5"), 100 - p)
        if fam == "or":
            return (up(c - orh) if d == "up" else dn(c - orl)) & (tod > 1000)
        if fam == "sma50":
            return up(col("sma50_dist_pct")) if d == "up" else dn(col("sma50_dist_pct"))
        if fam == "sma20":
            return up(col("sma20_dist_pct")) if d == "up" else dn(col("sma20_dist_pct"))
        if fam == "pdbrk":
            return up(c - pdh) if d == "up" else dn(c - pdl)
        if fam == "pdfail":
            return up(c - pdl) if d == "up" else dn(c - pdh)
        if fam in ("band05", "band10"):
            return up(z, -p) if d == "up" else dn(z, p)
        if fam == "hodlod":
            x = col("dist_hod_atr") if d == "up" else col("dist_lod_atr")
            return (x <= 0) & (prev(x) > 0)
        if fam == "rsi50":
            return up(col("rsi"), 50) if d == "up" else dn(col("rsi"), 50)
        if fam == "volspike":
            return up(col("volumeRatio"), 2.0) & ((z > 0) if d == "up" else (z < 0))
        if fam == "fo3":
            return up(col("fromOpen"), 3.0) if d == "up" else dn(col("fromOpen"), -3.0)
        if fam == "slope20":
            return up(col("sma20_slope_pct")) if d == "up" else dn(col("sma20_slope_pct"))
        if fam == "flow3":
            return up(col("flow3"), 0.5) if d == "up" else dn(col("flow3"), -0.5)
        raise KeyError(fam)

    def filt(name, p):
        if name in GENERIC:
            base, how = name.rsplit("_", 1)
            sg = s if how == "with" else -s
            if base == "rsi50":
                return sg * (col("rsi") - 50) > 0
            if base == "gap":
                return sg * col("gap") > (1.0 if p is None else p)
            if base == "vwap":
                return sg * z > 0
            k = {"ema": "emaDiff", "sma50": "sma50_dist_pct", "slope20": "sma20_slope_pct", "macd": "macdPct",
                 "bp": "buyPressure", "flow3": "flow3"}[base]
            return sg * col(k) > 0
        if name == "vol":
            return col("volumeRatio") >= p
        if name == "fo_with":
            return s * col("fromOpen") > p
        if name == "fo_against":
            return s * col("fromOpen") < -p
        if name == "rsi_ext":
            return (col("rsi") >= p) if s < 0 else (col("rsi") <= 100 - p)
        if name == "rsi5_ext":
            return (col("rsi5") >= p) if s < 0 else (col("rsi5") <= 100 - p)
        if name == "stretch_small":
            return np.abs(z) < p
        if name == "near_ext":
            return (col("dist_hod_atr") < p) if s > 0 else (col("dist_lod_atr") < p)
        if name == "pd_out_with":
            return (c > pdh) if s > 0 else (c < pdl)
        if name == "qqq_vwap_below":      # context column; absent -> NaN -> False (fail safe)
            if "qqq_vwap" not in df:
                return np.zeros(n, bool)
            return col("qqq_vwap") <= p
        if name == "pd_inside":
            return (c >= pdl) & (c <= pdh)
        raise KeyError(name)

    with np.errstate(invalid="ignore"):
        m = trig(*TRIGGER)
        for name, p in FILTERS:
            m = m & filt(name, p)
        return np.asarray(m, dtype=bool)
