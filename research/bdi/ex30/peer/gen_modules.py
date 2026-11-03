"""Writes the 5 ex30/peer lab modules (one shared feature block inlined in each, so every module is standalone).
    python gen_modules.py
Educational only - not financial advice."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMON = '''

def _features(df):
    """Per-bar peer features on a lab frame (one live symbol-day, or many offline symbol-days sorted by symbol, date, tod).
    Intraday sympathy stats use only returns of bars with tod >= 955 whose previous bar is >= 950 (history frames start
    at 09:50), so live (frame from 09:35) and history compute the same numbers."""
    def col(k):
        return df[k].to_numpy(dtype=float) if k in df else np.full(len(df), np.nan)

    if "symbol" in df and "date" in df:
        key = pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0]
    else:
        key = np.zeros(len(df), dtype=int)
    s = pd.DataFrame({"k": key, "c": col("close"), "spy": col("spy_fo"), "qqq": col("qqq_fo"), "tod": col("tod")})
    g = s.groupby("k", sort=False)
    pc, pt = g["c"].shift(1), g["tod"].shift(1)
    ok = (s["tod"] >= 955) & (pt >= 950)
    rs = (s["c"] / pc - 1) * 100
    out = {}
    for ix in ("spy", "qqq"):
        pi = g[ix].shift(1)
        ri = ((1 + s[ix] / 100) / (1 + pi / 100) - 1) * 100
        v = ok & np.isfinite(rs) & np.isfinite(ri)
        x, y = ri.where(v, 0.0), rs.where(v, 0.0)
        t = pd.DataFrame({"k": key, "n": v.astype(float), "x": x, "y": y, "xx": x * x, "yy": y * y, "xy": x * y})
        cs = t.groupby("k", sort=False)[["n", "x", "y", "xx", "yy", "xy"]].cumsum()
        n = cs["n"].to_numpy()
        with np.errstate(invalid="ignore", divide="ignore"):
            mx, my = cs["x"].to_numpy() / n, cs["y"].to_numpy() / n
            cov = cs["xy"].to_numpy() / n - mx * my
            vx = cs["xx"].to_numpy() / n - mx * mx
            vy = cs["yy"].to_numpy() / n - my * my
            out["n_" + ix] = n
            out["corr_" + ix] = cov / np.sqrt(vx * vy)
            out["beta_" + ix] = cov / vx
    c, atr, fo = col("close"), col("atr_d"), col("fromOpen")
    with np.errstate(invalid="ignore", divide="ignore"):
        atrp = atr / c * 100
        out["move"] = (c - c / (1 + fo / 100)) / atr
        out["res_spy"] = (fo - out["beta_spy"] * col("spy_fo")) / atrp
        out["res_qqq"] = (fo - out["beta_qqq"] * col("qqq_fo")) / atrp
        out["prev_res_qqq"] = pd.Series(out["res_qqq"]).groupby(key).shift(1).to_numpy()
        out["prev_c"] = pc.to_numpy()
        out["s2"] = (s["c"] / g["c"].shift(2) - 1).to_numpy() * 100
        out["q2"] = ((1 + s["qqq"] / 100) / (1 + g["qqq"].shift(2) / 100) - 1).to_numpy() * 100
        c950 = s["c"].where(s["tod"] >= 950)
        out["low_before"] = c950.groupby(key).cummin().groupby(key).shift(1).to_numpy()
    out.update(c=c, vwd=col("vwapDistPct"), spy=col("spy_fo"), qqq=col("qqq_fo"), bo=col("breadth_open"), tod=col("tod"))
    return out
'''

MODS = {
    "PR1-sympathy-laggard-long": dict(
        side="long", geom="t1s1", window=(1030, 1330), ctx=["spy_fo"],
        doc="Buys a name that has been moving WITH SPY today (intraday 5-minute return correlation >= 0.5, beta >= 0.5 since\n"
            "09:50) but has lagged the up-move its own beta implies by >= 0.5 daily ATR, while SPY is >= 0.30% above its open,\n"
            "on the first up-tick bar. MH4 (BDI 11-02) laggard catch-up, with the index as the moving peer group.",
        layers=["SPY >= +0.30% from its open", "intraday corr(stock, SPY) >= 0.50 and beta >= 0.50 over >= 8 bars from 09:55",
                "residual move (fromOpen - beta x spy_fo) <= -0.50 daily ATR", "close > previous 5-min close",
                "bar close 10:30-13:30 ET"],
        expr='(F["n_spy"] >= 8) & (F["spy"] >= 0.30) & (F["corr_spy"] >= 0.50) & (F["beta_spy"] >= 0.50) & '
             '(F["res_spy"] <= -0.50) & (F["c"] > F["prev_c"])'),
    "PR2-decoupled-quiet-breakdown-short": dict(
        side="short", geom="t1s1", window=(1030, 1430), ctx=["spy_fo"],
        doc="Shorts a name that has DECOUPLED from the tape on a quiet index (SPY within +-0.25% of its open, intraday\n"
            "correlation with SPY within +-0.15) and is breaking down on its own: >= 1 daily ATR below its open, under VWAP,\n"
            "closing at a new low of the day (09:50 onward). Quiet-day design.",
        layers=["abs(SPY from open) <= 0.25%", "abs(intraday corr(stock, SPY)) <= 0.15 over >= 8 bars from 09:55",
                "move from open <= -1.0 daily ATR", "close < VWAP", "close <= lowest earlier close since 09:50",
                "bar close 10:30-14:30 ET"],
        expr='(F["n_spy"] >= 8) & (np.abs(F["spy"]) <= 0.25) & (np.abs(F["corr_spy"]) <= 0.15) & (F["move"] <= -1.0) & '
             '(F["vwd"] < 0) & (F["c"] <= F["low_before"])'),
    "PR3-narrow-rally-laggard-short": dict(
        side="short", geom="t1s1", window=(1030, 1430), ctx=["spy_fo", "qqq_fo", "breadth_open"],
        doc="Index-vs-component divergence: SPY is >= 0.30% above its open but <= 45% of the universe is above its own open\n"
            "and QQQ leads SPY (a narrow, mega-cap rally). Shorts a component that is not being carried: >= 0.5 daily ATR\n"
            "below its open and under VWAP.",
        layers=["SPY >= +0.30% from its open", "breadth_open <= 0.45", "qqq_fo >= spy_fo",
                "move from open <= -0.50 daily ATR", "close < VWAP", "bar close 10:30-14:30 ET"],
        expr='(F["spy"] >= 0.30) & (F["bo"] <= 0.45) & (F["qqq"] >= F["spy"]) & (F["move"] <= -0.50) & (F["vwd"] < 0)'),
    "PR4-qqq-residual-stretch-revert-short": dict(
        side="short", geom="t05s1", window=(1100, 1500), ctx=["qqq_fo"],
        doc="Intraday pair spread vs QQQ: a name co-moving with QQQ (corr >= 0.40 over >= 12 bars) whose move left after its\n"
            "own QQQ beta is stretched >= 1.25 daily ATR to the upside and has started to shrink (residual and close both\n"
            "lower than one bar earlier). Shorts the spread reverting.",
        layers=["intraday corr(stock, QQQ) >= 0.40 over >= 12 bars from 09:55",
                "residual move (fromOpen - beta x qqq_fo) >= +1.25 daily ATR", "residual < its value one bar earlier",
                "close < previous 5-min close", "bar close 11:00-15:00 ET"],
        expr='(F["n_qqq"] >= 12) & (F["corr_qqq"] >= 0.40) & (F["res_qqq"] >= 1.25) & '
             '(F["res_qqq"] < F["prev_res_qqq"]) & (F["c"] < F["prev_c"])'),
    "PR5-qqq-impulse-leadlag-long": dict(
        side="long", geom="t05s1", window=(1020, 1500), ctx=["qqq_fo"],
        doc="Index lead-lag: QQQ rose >= 0.20% over the last two 5-minute bars, and a high-sympathy name (intraday corr with\n"
            "QQQ >= 0.50, beta >= 0.80) has moved less than a quarter of what its beta implies over the same 10 minutes.\n"
            "Buys the lagging follower.",
        layers=["QQQ +0.20% or more over the last 2 bars", "intraday corr(stock, QQQ) >= 0.50, beta >= 0.80 over >= 6 bars",
                "stock's 2-bar return <= 0.25 x beta x QQQ 2-bar return", "bar close 10:20-15:00 ET"],
        expr='(F["n_qqq"] >= 6) & (F["corr_qqq"] >= 0.50) & (F["beta_qqq"] >= 0.80) & (F["q2"] >= 0.20) & '
             '(F["s2"] <= 0.25 * F["beta_qqq"] * F["q2"])'),
}

for name, m in MODS.items():
    src = f'''"""{name} - ex30/peer peer / sympathy / dispersion setup (BDI 2026-11-03, research/bdi/ex30/peer).
{m["doc"]}
Needs lab context columns (YAML `context: {m["ctx"]}`); a missing column gives NaN -> no signal (fail safe).
Exploratory account candidate; see research/bdi/ex30/peer/NOTES.md. Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "{m["side"]}"
GEOM = "{m["geom"]}"
WINDOW = {m["window"]}
CONTEXT = {m["ctx"]}
LAYERS = {m["layers"]!r}
{COMMON}

def mask(df) -> np.ndarray:
    F = _features(df)
    tod = F["tod"]
    with np.errstate(invalid="ignore"):
        m = {m["expr"]}
        return np.asarray(m & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)
'''
    (HERE / "modules" / f"{name}.py").write_text(src)
print("wrote", len(MODS))
