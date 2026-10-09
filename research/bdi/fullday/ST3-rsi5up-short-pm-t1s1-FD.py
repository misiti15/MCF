"""ST3-rsi5up-short-pm-t1s1-FD - FULL-DAY version of ST3-rsi5up-short-pm-t1s1 (owner decision 2026-10-09: full-day versions
first, then identify time frames that may be better; Testing account).
Source module: research/bdi/stack1009/modules/ST3-rsi5up-short-pm-t1s1.py (copied; logic identical except the removed clause).
Removed: `m & (tod >= WINDOW[0]) & (tod <= WINDOW[1])` with WINDOW = (1335, 1500) - the clause that limited WHEN the rule may fire (source module window 1335-1500
ET bar close; source YAML window [1335, 1500]).
Kept: every other condition; the 09:30-10:00 opening range read at the 10:00 bar (`tod == 1000`) and the OR trigger's `tod > 1000` guard are structural, not a window, and stay.
Run with min_adv 95000000 and window [950, 1500] (bar close ET).
Check: research/bdi/fullday/verify.json (this mask AND the source window == the source mask, open history).
Source docstring (provenance only - its results describe the WINDOWED rule, not this one):
    ST3-rsi5up-short-pm-t1s1 - BDI basic-stack study 2026-10-09 (research/bdi/stack1009). Basic stack: RSI(5) crosses back above 20; stock down > 3.0% from the open; close above VWAP; gap up > 1.0%; 13:35-15:00 ET (bar close).
    Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars, values known at the bar close.
    Source ran with min_adv 95000000 and window [1335, 1500] (bar close ET).
    2-year open history (426 sessions, locked block excluded, production costs): n 358 (0.84/day), win 0.5866, exp +0.106R, day-clustered t 2.35; up +0.056 (n 93.0) / flat +0.152 (n 148.0) / down +0.087 (n 117.0); walk-forward + share 0.769; plateau mean 0.0939; ex-best-day +0.086.
    LIVE-PROBATION candidate only: t is below the try-count bar t_required = 4.837 (N = 120500 configurations).
    NOT scored on the rule-19 locked block. Educational only - not financial advice.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
TRIGGER = ['rsi5', 'up', 20]
FILTERS = [['fo_with', 3.0], ['vwap_against', None], ['gap_against', 1.0]]
WINDOW = None  # full day (source: WINDOW = (1335, 1500)); window = YAML [950, 1500]
LAYERS = [
    "RSI(5) crosses back above 20",
    "stock down > 3.0% from the open",
    "close above VWAP",
    "gap up > 1.0%",
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
        if name == "pd_inside":
            return (c >= pdl) & (c <= pdh)
        raise KeyError(name)

    with np.errstate(invalid="ignore"):
        m = trig(*TRIGGER)
        for name, p in FILTERS:
            m = m & filt(name, p)
        return np.asarray(m, dtype=bool)
