"""Writes the 5 ex30/time lab modules (self-contained; one shared feature block). Educational only - not financial advice."""
from pathlib import Path

HERE = Path(__file__).resolve().parent

HEAD = '''"""{name} - ex30/time time / calendar setup (BDI 2026-11-03, research/bdi/ex30/time).
{doc}
{ctxnote}Exploratory account candidate; see research/bdi/ex30/time/NOTES.md. Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "{side}"
GEOM = "{geom}"
WINDOW = {window}
CONTEXT = {context}
LAYERS = {layers}


def _features(df):
    """Per-bar features on a lab frame (one live symbol-day indexed by bar starts, or many offline symbol-days sorted by
    symbol, date, tod). Lags use only bars with tod >= 950 (history frames start at 09:50), so live = history."""
    n = len(df)

    def col(k):
        return df[k].to_numpy(dtype=float) if k in df else np.full(n, np.nan)

    if "date" in df:
        d = pd.to_datetime(pd.Series(np.asarray(df["date"]).astype(str)))
    elif isinstance(df.index, pd.DatetimeIndex):
        d = pd.Series(df.index.tz_localize(None).normalize() if df.index.tz is not None else df.index.normalize())
    elif "ts" in df:
        d = pd.to_datetime(pd.Series(np.asarray(df["ts"]))).dt.tz_localize(None).dt.normalize()
    else:
        d = pd.Series(pd.NaT, index=range(n))
    d = d.reset_index(drop=True)
    if "symbol" in df:
        key = pd.factorize(pd.Series(np.asarray(df["symbol"]).astype(str)) + "|" + d.astype(str))[0]
    else:
        key = np.zeros(n, dtype=int)
    tod = col("tod")
    early = tod < 950
    c, atr, fo = col("close"), col("atr_d"), col("fromOpen")
    hi = col("high")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + col("dist_hod_atr") * atr
        lod = c - col("dist_lod_atr") * atr
    s = pd.DataFrame({{"k": key, "c": np.where(early, np.nan, c), "hi": np.where(early, np.nan, hi),
                       "hod": np.where(early, np.nan, hod), "lod": np.where(early, np.nan, lod)}})
    g = s.groupby("k", sort=False)
    F = dict(tod=tod, c=c, atr=atr, hod=hod, lod=lod, spy=col("spy_fo"), prng=col("spy_prng"), gap=col("gap"),
             vwd=col("vwapDistPct"), dhod=col("dist_hod_atr"), dlod=col("dist_lod_atr"),
             dom=d.dt.day.to_numpy(dtype=float), dow=d.dt.weekday.to_numpy(dtype=float))
    F["prev_c"] = g["c"].shift(1).to_numpy()
    F["prev_hi"] = g["hi"].shift(1).to_numpy()
    F["hod6"] = g["hod"].shift(6).to_numpy()
    F["lod2"] = g["lod"].shift(2).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        F["move"] = (c - c / (1 + fo / 100)) / atr
        F["rng"] = F["dhod"] + F["dlod"]
        F["pos"] = F["dlod"] / F["rng"]
        F["vwa"] = F["vwd"] / 100 * c / atr
    return F


def mask(df) -> np.ndarray:
    F = _features(df)
    tod = F["tod"]
    with np.errstate(invalid="ignore"):
        m = {expr}
        return np.asarray(m & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)
'''

SETUPS = {
    "TM1-lunch-stalled-high-fade-quiet-short": dict(
        side="short", geom="t05s1", window=(1130, 1330), context=["spy_fo"],
        doc="QUIET-day lunch reversal: on a flat tape (SPY within +-0.25% of its open) shorts a morning leader (>= 0.75\n"
            "daily ATR above its open) that has not made a new high for 30 minutes, sits >= 0.40 ATR under its high of day\n"
            "and closes below the previous 5-minute close, 11:30-13:30.",
        layers=["abs(SPY from open) <= 0.25%", "move from open >= +0.75 daily ATR", "dist below HOD >= 0.40 ATR",
                "no new HOD in the last 6 bars (hod - hod 6 bars ago <= 0.01 ATR)", "close < prev close",
                "bar close 11:30-13:30 ET"],
        expr='(np.abs(F["spy"]) <= 0.25) & (F["move"] >= 0.75) & (F["dhod"] >= 0.40) & '
             '(F["hod"] - F["hod6"] <= 0.01 * F["atr"]) & (F["c"] < F["prev_c"])'),
    "TM2-quiet-tape-range-floor-fade-long": dict(
        side="long", geom="t05s1", window=(1200, 1500), context=["spy_fo", "spy_prng"],
        doc="QUIET-day range fade: SPY within +-0.20% of its open after a narrow SPY prior day (prior range <= 1.0 SPY\n"
            "ATR); buys a name in the bottom 15% of its own day range (range >= 0.75 ATR) on the first up-close, 12:00-15:00.",
        layers=["abs(SPY from open) <= 0.20%", "SPY prior-day range <= 1.0 SPY ATR (spy_prng)", "day range >= 0.75 ATR",
                "position in day range <= 0.15", "close > prev close", "bar close 12:00-15:00 ET"],
        expr='(np.abs(F["spy"]) <= 0.20) & (F["prng"] <= 1.0) & (F["rng"] >= 0.75) & (F["pos"] <= 0.15) & '
             '(F["c"] > F["prev_c"])'),
    "TM3-gapup-drift-powerhour-short": dict(
        side="short", geom="t05s1", window=(1430, 1500), context=[],
        doc="Overnight gap vs intraday drift, power hour: a name that gapped up >= 1% but has drifted >= 0.75 daily ATR\n"
            "below its open, is under VWAP and within 0.15 ATR of its low of day at 14:30-15:00 - short into the close.",
        layers=["gap >= +1.0%", "move from open <= -0.75 daily ATR", "dist above LOD <= 0.15 ATR", "close < VWAP",
                "bar close 14:30-15:00 ET"],
        expr='(F["gap"] >= 1.0) & (F["move"] <= -0.75) & (F["dlod"] <= 0.15) & (F["vwd"] < 0)'),
    "TM4-ten-oclock-reversal-long": dict(
        side="long", geom="t1s1", window=(1000, 1015), context=[],
        doc="The 10:00 reversal: a name >= 0.75 daily ATR below its open that made a new low of day in the last 2 bars\n"
            "and now closes above the previous bar's high (still under VWAP), bar closes 10:00-10:15 only.",
        layers=["move from open <= -0.75 daily ATR", "new LOD within the last 2 bars (lod < lod 2 bars ago)",
                "close > previous bar high", "close < VWAP", "bar close 10:00-10:15 ET"],
        expr='(F["move"] <= -0.75) & (F["lod"] < F["lod2"]) & (F["c"] > F["prev_hi"]) & (F["vwd"] < 0)'),
    "TM5-turn-of-month-vwap-pullback-long": dict(
        side="long", geom="t05s1", window=(1030, 1400), context=[],
        doc="Turn-of-the-month inflow: only on calendar days 28-31 and 1-3, buys a name >= 0.50 daily ATR above its\n"
            "open that has pulled back to within 0.15 ATR above VWAP and closes up on the bar, 10:30-14:00.",
        layers=["calendar day of month >= 28 or <= 3", "move from open >= +0.50 daily ATR",
                "0 < VWAP distance <= 0.15 ATR", "close > prev close", "bar close 10:30-14:00 ET"],
        expr='((F["dom"] >= 28) | (F["dom"] <= 3)) & (F["move"] >= 0.50) & (F["vwa"] > 0) & (F["vwa"] <= 0.15) & '
             '(F["c"] > F["prev_c"])'),
}

if __name__ == "__main__":
    for name, s in SETUPS.items():
        ctxnote = (f"Needs lab context columns (YAML `context: {s['context']}`); a missing column gives NaN -> no signal "
                   "(fail safe).\n" if s["context"] else "")
        (HERE / "modules" / f"{name}.py").write_text(HEAD.format(name=name, ctxnote=ctxnote, **s))
        print("wrote", name)
