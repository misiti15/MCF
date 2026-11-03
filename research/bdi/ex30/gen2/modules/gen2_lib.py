"""ex30/gen2 shared primitives for the grammar-generated lab modules (research/bdi/ex30/gen2).
A gen2 rule = one TRIGGER (event at this bar) + 0..2 CONTEXTS (state), all known at the bar close, on the lab frame
columns plus the opt-in context columns spy_fo / breadth (mcf/strategies/lab_context.py). Look-backs are one bar,
inside one symbol-day; module windows start at 10:00, so every lag read is a >= 09:50 bar (live frames hold 09:35+,
offline frames 09:50+; both agree inside the window). NaN comparisons are False (fail safe).
numpy re-implementation; the harness in ../gen.py uses an independent pandas version (parity checked on 2026-09).
Educational only - not financial advice."""
import numpy as np


def col(df, k):
    return df[k].to_numpy(dtype=float) if k in df else np.full(len(df), np.nan)


def segments(df):
    if "symbol" in df and "date" in df:
        key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
        return np.cumsum(np.r_[True, key[1:] != key[:-1]])
    return np.ones(len(df), int)


def lag(x, seg):
    x = np.asarray(x, float)
    p = np.r_[np.nan, x[:-1]]
    ps = np.r_[-1, seg[:-1]]
    p[ps != seg] = np.nan
    return p


def primitive(df, name, seg=None):
    """Boolean array for one grammar primitive (names as in PLAN.md)."""
    seg = segments(df) if seg is None else seg
    c, h, l, atr = col(df, "close"), col(df, "high"), col(df, "low"), col(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        rng = (h - l) / atr
        vd = col(df, "vwapDistPct")
        o = c / (1 + col(df, "fromOpen") / 100)
        fo_atr = (c - o) / atr
        vw_atr = (c - c / (1 + vd / 100)) / atr
        f = {
            # triggers
            "vwup": lambda: (vd > 0) & (lag(vd, seg) <= 0),
            "vwdn": lambda: (vd < 0) & (lag(vd, seg) >= 0),
            "hod": lambda: col(df, "dist_hod_atr") <= 0.01,
            "lod": lambda: col(df, "dist_lod_atr") <= 0.01,
            "volsurge": lambda: col(df, "volumeSurge") >= 2.0,
            "bulldiv": lambda: col(df, "bull_div") == 1,
            "beardiv": lambda: col(df, "bear_div") == 1,
            "uwick": lambda: (col(df, "upper_wick") >= 0.6) & (rng >= 0.10),
            "lwick": lambda: (col(df, "lower_wick") >= 0.6) & (rng >= 0.10),
            "rsi5up": lambda: (col(df, "rsi5") >= 30) & (lag(col(df, "rsi5"), seg) < 30),
            "rsi5dn": lambda: (col(df, "rsi5") <= 70) & (lag(col(df, "rsi5"), seg) > 70),
            "macdup": lambda: (col(df, "macdPct") > 0) & (lag(col(df, "macdPct"), seg) <= 0),
            "macddn": lambda: (col(df, "macdPct") < 0) & (lag(col(df, "macdPct"), seg) >= 0),
            "flowup": lambda: (col(df, "flow3") >= 0.3) & (col(df, "flow9prev") <= -0.1),
            "flowdn": lambda: (col(df, "flow3") <= -0.3) & (col(df, "flow9prev") >= 0.1),
            "wide": lambda: rng >= 0.18,
            "inside": lambda: (h <= lag(h, seg)) & (l >= lag(l, seg)),
            "round": lambda: col(df, "dist_round_atr") <= 0.02,
            "dry": lambda: col(df, "volumeRatio") <= 0.3,
            # contexts
            "fo_up": lambda: fo_atr >= 0.5, "fo_dn": lambda: fo_atr <= -0.5, "fo_flat": lambda: np.abs(fo_atr) <= 0.2,
            "gap_up": lambda: col(df, "gap") >= 1.0, "gap_dn": lambda: col(df, "gap") <= -1.0,
            "gap_flat": lambda: np.abs(col(df, "gap")) <= 0.3,
            "pp_hi": lambda: col(df, "pricePosition") >= 0.85, "pp_lo": lambda: col(df, "pricePosition") <= 0.15,
            "d20_hi": lambda: col(df, "sma20_dist_pct") >= 0.8, "d20_lo": lambda: col(df, "sma20_dist_pct") <= -0.8,
            "slope_up": lambda: col(df, "sma20_slope_pct") >= 0.3, "slope_dn": lambda: col(df, "sma20_slope_pct") <= -0.3,
            "abv_pdh": lambda: col(df, "dist_pdh_atr") < 0, "blw_pdl": lambda: col(df, "dist_pdl_atr") < 0,
            "inside_pd": lambda: (col(df, "dist_pdh_atr") > 0) & (col(df, "dist_pdl_atr") > 0),
            "rsi_hi": lambda: col(df, "rsi") >= 70, "rsi_lo": lambda: col(df, "rsi") <= 30,
            "vr_lo": lambda: col(df, "volumeRatio") <= 0.6, "vs_hi": lambda: col(df, "volumeSurge") >= 1.5,
            "heat_hi": lambda: col(df, "heat") >= 25, "heat_lo": lambda: col(df, "heat") <= -25,
            "bp_hi": lambda: col(df, "buyPressure") >= 0.3, "bp_lo": lambda: col(df, "buyPressure") <= -0.3,
            "vol_hi": lambda: atr / c >= 0.045, "vol_lo": lambda: atr / c <= 0.017,
            "vw_up": lambda: vw_atr >= 0.5, "vw_dn": lambda: vw_atr <= -0.5,
            "spy_up": lambda: col(df, "spy_fo") >= 0.3, "spy_dn": lambda: col(df, "spy_fo") <= -0.3,
            "spy_flat": lambda: np.abs(col(df, "spy_fo")) <= 0.15,
            "br_hi": lambda: col(df, "breadth") >= 0.70, "br_lo": lambda: col(df, "breadth") <= 0.30,
            "br_mid": lambda: (col(df, "breadth") >= 0.42) & (col(df, "breadth") <= 0.58),
            "rs_up": lambda: col(df, "fromOpen") - col(df, "spy_fo") >= 1.5,
            "rs_dn": lambda: col(df, "fromOpen") - col(df, "spy_fo") <= -1.5,
        }[name]()
    return np.asarray(f, bool)


def mask_rule(df, rule, window):
    seg = segments(df)
    tod = col(df, "tod")
    m = (tod >= window[0]) & (tod <= window[1])
    for p in rule:
        m &= primitive(df, p, seg)
    return np.asarray(m, bool)
