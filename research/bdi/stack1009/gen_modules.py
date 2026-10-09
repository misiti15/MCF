"""Write one self-contained lab module per candidate (modules/<ID>.py) for LabStrategy, from candidates.json.
Only live-frame columns are used (heat_frame + setup_lab.extra_features); prev-bar logic respects symbol-day boundaries
on offline frames. Educational only - not financial advice."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

TEMPLATE = '''"""{id} - BDI basic-stack study 2026-10-09 (research/bdi/stack1009). {desc}
Side {side}, exit {geom} (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars, values known at the bar close.
Run with min_adv 95000000 and window [{lo}, {hi}] (bar close ET).
2-year open history (426 sessions, locked block excluded, production costs): {stats}
LIVE-PROBATION candidate only: t is below the try-count bar t_required = {treq} (N = {ntries} configurations).
NOT scored on the rule-19 locked block. Educational only - not financial advice."""
import numpy as np

SIDE = "{side}"
GEOM = "{geom}"
TRIGGER = {trigger!r}
FILTERS = {filters!r}
WINDOW = ({lo}, {hi})
LAYERS = {layers!r}
GENERIC = {{"vwap_with", "vwap_against", "ema_with", "ema_against", "sma50_with", "sma50_against", "slope20_with",
           "slope20_against", "macd_with", "macd_against", "bp_with", "bp_against", "flow3_with", "flow3_against",
           "rsi50_with", "gap_with", "gap_against"}}


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
            k = {{"ema": "emaDiff", "sma50": "sma50_dist_pct", "slope20": "sma20_slope_pct", "macd": "macdPct",
                 "bp": "buyPressure", "flow3": "flow3"}}[base]
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
        return np.asarray(m & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), dtype=bool)
'''


TRIG_TXT = {
    ("vwap", "up"): "close crosses above VWAP", ("vwap", "dn"): "close crosses below VWAP",
    ("ema", "up"): "EMA9 crosses above EMA21", ("ema", "dn"): "EMA9 crosses below EMA21",
    ("macd", "up"): "MACD line crosses above 0", ("macd", "dn"): "MACD line crosses below 0",
    ("rsi14", "up"): "RSI(14) crosses back above {p}", ("rsi14", "dn"): "RSI(14) crosses back below {q}",
    ("rsi5", "up"): "RSI(5) crosses back above {p}", ("rsi5", "dn"): "RSI(5) crosses back below {q}",
    ("or", "up"): "close crosses above the 09:30-10:00 opening-range high", ("or", "dn"): "close crosses below the 09:30-10:00 opening-range low",
    ("sma50", "up"): "close crosses above the 5-min SMA50", ("sma50", "dn"): "close crosses below the 5-min SMA50",
    ("sma20", "up"): "close crosses above the 5-min SMA20", ("sma20", "dn"): "close crosses below the 5-min SMA20",
    ("pdbrk", "up"): "close crosses above the prior-day high", ("pdbrk", "dn"): "close crosses below the prior-day low",
    ("pdfail", "up"): "close crosses back above the prior-day low", ("pdfail", "dn"): "close crosses back below the prior-day high",
    ("hodlod", "up"): "new high of day", ("hodlod", "dn"): "new low of day",
    ("rsi50", "up"): "RSI(14) crosses above 50", ("rsi50", "dn"): "RSI(14) crosses below 50",
    ("volspike", "up"): "volume ratio crosses above 2.0 on a bar closing above VWAP",
    ("volspike", "dn"): "volume ratio crosses above 2.0 on a bar closing below VWAP",
    ("fo3", "up"): "move from the open crosses above +3%", ("fo3", "dn"): "move from the open crosses below -3%",
    ("slope20", "up"): "5-min SMA20 slope turns positive", ("slope20", "dn"): "5-min SMA20 slope turns negative",
    ("flow3", "up"): "3-bar signed-volume share crosses above +0.5", ("flow3", "dn"): "3-bar signed-volume share crosses below -0.5",
}


def filt_txt(n, p, side):
    L = side == "long"
    up_or_dn = lambda w: ("above" if (w == "with") == L else "below")  # noqa: E731
    base = {"vwap": "VWAP", "ema": "EMA21 (EMA9 vs EMA21)", "sma50": "the 5-min SMA50", "macd": "0 (MACD line)"}
    if n in ("vwap_with", "vwap_against"):
        return f"close {up_or_dn(n.split('_')[1])} VWAP"
    if n in ("ema_with", "ema_against"):
        return f"EMA9 {up_or_dn(n.split('_')[1])} EMA21"
    if n in ("sma50_with", "sma50_against"):
        return f"close {up_or_dn(n.split('_')[1])} the 5-min SMA50"
    if n in ("macd_with", "macd_against"):
        return f"MACD line {up_or_dn(n.split('_')[1])} 0"
    if n in ("slope20_with", "slope20_against"):
        return "5-min SMA20 rising" if up_or_dn(n.split('_')[1]) == "above" else "5-min SMA20 falling"
    if n in ("bp_with", "bp_against"):
        return "19-bar buy pressure > 0" if up_or_dn(n.split('_')[1]) == "above" else "19-bar buy pressure < 0"
    if n in ("flow3_with", "flow3_against"):
        return "3-bar signed-volume share > 0" if up_or_dn(n.split('_')[1]) == "above" else "3-bar signed-volume share < 0"
    if n == "rsi50_with":
        return "RSI(14) > 50" if L else "RSI(14) < 50"
    if n in ("gap_with", "gap_against"):
        pp = 1.0 if p is None else p
        return f"gap up > {pp}%" if up_or_dn(n.split('_')[1]) == "above" else f"gap down > {pp}%"
    if n == "vol":
        return f"volume ratio >= {p}"
    if n == "fo_with":
        return f"stock up > {p}% from the open" if L else f"stock down > {p}% from the open"
    if n == "fo_against":
        return f"stock down > {p}% from the open" if L else f"stock up > {p}% from the open"
    if n == "rsi_ext":
        return f"RSI(14) <= {100 - p}" if L else f"RSI(14) >= {p}"
    if n == "rsi5_ext":
        return f"RSI(5) <= {100 - p}" if L else f"RSI(5) >= {p}"
    if n == "stretch_small":
        return f"close within {p} daily ATR of VWAP"
    if n == "near_ext":
        return f"within {p} ATR of the high of day" if L else f"within {p} ATR of the low of day"
    if n == "pd_out_with":
        return "close above the prior-day high" if L else "close below the prior-day low"
    if n == "pd_inside":
        return "close inside the prior-day range"
    raise KeyError(n)


def main():
    cands = json.load(open(HERE / "candidates.json"))
    for c in cands:
        fam, d, p = c["trigger"]
        tx = TRIG_TXT[(fam, d)].format(p=p, q=None if p is None else 100 - p)
        lo, hi = c["lo"], c["hi"]
        c["layers"] = [tx] + [filt_txt(n, pp, c["side"]) for n, pp in c["filters"]] + \
            [f"{lo // 100:02d}:{lo % 100:02d}-{hi // 100:02d}:{hi % 100:02d} ET (bar close)"]
        c["desc"] = "Basic stack: " + "; ".join(c["layers"]) + "."
        src = TEMPLATE.format(**c)
        json.dump(cands, open(HERE / "candidates.json", "w"), indent=1)
        (HERE / "modules" / f"{c['id']}.py").write_text(src)
        print("wrote", c["id"])


if __name__ == "__main__":
    main()
