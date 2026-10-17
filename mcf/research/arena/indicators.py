"""Arena indicator library (swarm 2026-10-17): point-in-time indicators on the 5-minute lab frames.

Every indicator is computed per symbol-day on the 5-minute decision bars with bar close 09:50..15:00 ET (the rows the
history frames hold, research/history2y/build_frames.py). Rows outside that range (the live frame also carries the
09:35-09:45 bars and post-15:00 bars) get NaN, so the history and the live LabStrategy frame see the same inputs.
A value on row i uses only rows <= i of the same symbol-day plus columns that are themselves causal at row i
(the existing lab columns: heat_frame + setup_lab.extra_features + atr_d/gap/prior-day levels). Day-level values
read at the 09:50 bar (opening-range high/low) are known at 09:50.

Families: mom, mr, trend, vol, flow, struct, ctx (cross-asset/breadth: research only, not live), time.
The frames carry no raw volume, so volume indicators are built from the existing volume ratios (volumeRatio,
volumeSurge, vol_climax, buyPressure, flow3, flow9prev); true rvol-by-time-of-day is not available.

    from mcf.research.arena.indicators import compute, INDICATORS
    x = compute(frame)                     # DataFrame aligned with frame.index, one column per indicator
    x = compute(frame, names=["rsi2", "or_high_dist_atr"])
Educational only - not financial advice.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

FIRST_TOD, LAST_TOD, STEP = 950, 1500, 5
N_SLOTS = 63                        # 09:50 .. 15:00 bar closes
CTX_SYMBOLS = ("SPY", "QQQ", "IWM")


@dataclass(frozen=True)
class Ind:
    name: str
    family: str
    desc: str
    live: bool = True               # computable by the live LabStrategy frame (one symbol, no cross-section)
    kind: str = "cont"              # cont | binary | cat


def _reg():
    I = []
    a = lambda *x, **k: I.append(Ind(*x, **k))
    # momentum
    a("ret1", "mom", "1-bar (5 min) return %")
    a("ret3", "mom", "3-bar (15 min) return %")
    a("ret6", "mom", "6-bar (30 min) return %")
    a("ret12", "mom", "12-bar (60 min) return %")
    a("ret3_atr", "mom", "15-min change in daily ATRs")
    a("ret_since950_atr", "mom", "change since the 09:50 close in daily ATRs")
    a("fromOpen", "mom", "close vs today's open % (frame column)")
    a("fromOpen_atr", "mom", "close - open in daily ATRs")
    a("from_pc", "mom", "close vs prior close %")
    a("from_pc_atr", "mom", "close - prior close in daily ATRs")
    a("gap", "mom", "open vs prior close % (frame column)")
    a("gap_atr", "mom", "open - prior close in daily ATRs")
    a("momentum", "mom", "MarcoFlow momentum (frame column)")
    # mean reversion
    a("rsi2", "mr", "RSI(2) on in-day 5-min closes")
    a("rsi5", "mr", "RSI(5) (frame column)")
    a("rsi7", "mr", "RSI(7) on in-day 5-min closes")
    a("rsi", "mr", "RSI(14) (frame column)")
    a("rsiSlope", "mr", "RSI(14) change over 3 bars (frame column)")
    a("vwap_atr", "mr", "close - session VWAP in daily ATRs")
    a("vwapDistPct", "mr", "close vs session VWAP % (frame column)")
    a("sma20_dist_pct", "mr", "close vs 5-min SMA20 % (frame column)")
    a("sma50_dist_pct", "mr", "close vs 5-min SMA50 % (frame column)")
    a("z12", "mr", "z-score of close vs its in-day 12-bar mean/std")
    a("bb_pctb12", "mr", "Bollinger %B (12 bars, 2 sd, in-day)")
    a("dist_hod_atr", "mr", "high of day - close in ATRs (frame column)")
    a("dist_lod_atr", "mr", "close - low of day in ATRs (frame column)")
    a("day_pos", "mr", "position in today's range so far (0 = low, 1 = high)")
    a("pricePosition", "mr", "position in 20-bar range (frame column)")
    # trend
    a("emaDiff", "trend", "EMA9 vs EMA21 % (frame column)")
    a("macdPct", "trend", "MACD line % of price (frame column)")
    a("sma20_slope_pct", "trend", "SMA20 slope over 5 bars % (frame column)")
    a("emaDiff_chg3", "trend", "emaDiff change over 3 bars")
    a("macd_hist", "trend", "macdPct minus its in-day EMA9 (histogram)")
    a("ema9_slope_atr", "trend", "in-day EMA9 change over 3 bars in daily ATRs")
    a("adx7", "trend", "ADX(7), in-day")
    a("di_diff7", "trend", "+DI(7) - -DI(7), in-day")
    a("hh_count6", "trend", "higher highs among the last 6 bars")
    a("ll_count6", "trend", "lower lows among the last 6 bars")
    a("slope6_atr", "trend", "least-squares slope of the last 6 closes per bar, in daily ATRs")
    a("eff6", "trend", "efficiency ratio over 6 bars (net move / path)")
    # volatility
    a("atrPct", "vol", "5-min ATR(14) % of price (frame column)")
    a("atr_d_pct", "vol", "daily ATR % of price")
    a("bar_range_atr", "vol", "bar high-low in daily ATRs")
    a("range_exp", "vol", "bar range / mean range of the prior 6 bars")
    a("day_range_atr", "vol", "today's range so far in daily ATRs")
    a("prev_range_atr", "vol", "prior day's range in daily ATRs (NR-style compression)")
    a("day_vs_prev_range", "vol", "today's range so far / prior day's range")
    a("compress6_atr", "vol", "6-bar high-low range in daily ATRs")
    a("rv12", "vol", "std of 5-min returns over 12 bars (%)")
    # volume / flow
    a("volumeRatio", "flow", "bar volume / 20-bar mean (frame column)")
    a("volumeSurge", "flow", "5-bar mean volume / prior 15 (frame column)")
    a("buyPressure", "flow", "signed volume share, 19 bars (frame column)")
    a("flow3", "flow", "signed volume share, 3 bars (frame column)")
    a("flow9prev", "flow", "signed volume share, the 9 bars before the last 3 (frame column)")
    a("flow_shift", "flow", "flow3 - flow9prev")
    a("rvol_day", "flow", "mean volumeRatio since 09:50 (rvol proxy)")
    a("obv6", "flow", "sum over 6 bars of sign(return) x volumeRatio (OBV-slope proxy)")
    a("vol_trend", "flow", "mean volumeRatio last 3 bars / prior 6")
    a("vwap_cross_n", "flow", "VWAP side changes since 09:50")
    a("vwap_side_bars", "flow", "bars on the current VWAP side (signed: + above)")
    a("vwapReclaim", "flow", "VWAP reclaim/loss over 3 bars (frame column)", kind="cat")
    a("heat", "flow", "MarcoFlow heat (frame column)")
    a("volumeHeat", "flow", "MarcoFlow volume heat (frame column)")
    # structure
    a("or_high_dist_atr", "struct", "close - opening-range high (09:30-09:50) in daily ATRs")
    a("or_low_dist_atr", "struct", "close - opening-range low in daily ATRs")
    a("orb_fail_up", "struct", "closed above the OR high earlier today, now back below", kind="binary")
    a("orb_fail_dn", "struct", "closed below the OR low earlier today, now back above", kind="binary")
    a("dist_pdh_atr", "struct", "prior-day high - close in ATRs (frame column)")
    a("dist_pdl_atr", "struct", "close - prior-day low in ATRs (frame column)")
    a("dist_round_atr", "struct", "distance to the nearest round number in ATRs (frame column)")
    a("new_hod", "struct", "bar made a new high of day", kind="binary")
    a("new_lod", "struct", "bar made a new low of day", kind="binary")
    a("bars_since_hod", "struct", "bars since the last new high of day (from 09:50)")
    a("bars_since_lod", "struct", "bars since the last new low of day (from 09:50)")
    a("upper_wick", "struct", "upper wick share of the bar (frame column)")
    a("lower_wick", "struct", "lower wick share of the bar (frame column)")
    a("bear_div", "struct", "20-bar high with RSI below its high (frame column)", kind="binary")
    a("bull_div", "struct", "20-bar low with RSI above its low (frame column)", kind="binary")
    # cross-asset / context (research only)
    for s in CTX_SYMBOLS:
        a(f"{s.lower()}_fromOpen", "ctx", f"{s} close vs its open % at this minute", live=False)
    a("spy_ret3", "ctx", "SPY 15-min return %", live=False)
    a("rs_spy", "ctx", "fromOpen - SPY fromOpen", live=False)
    a("rs_spy3", "ctx", "ret3 - SPY ret3", live=False)
    a("breadth_vwap", "ctx", "share of the lab universe above VWAP at this minute", live=False)
    a("breadth_med_fromOpen", "ctx", "median fromOpen of the lab universe at this minute", live=False)
    a("rs_univ", "ctx", "fromOpen - universe median fromOpen", live=False)
    # time
    a("tod_min", "time", "minutes since 09:30 at the bar close")
    a("dow", "time", "day of week (0 = Monday)", kind="cat")
    return {i.name: i for i in I}


INDICATORS: dict[str, Ind] = _reg()
FRAME_COLS = ["close", "high", "low", "tod", "atr_d", "gap", "fromOpen", "momentum", "rsi", "rsi5", "rsiSlope",
              "vwapDistPct", "sma20_dist_pct", "sma50_dist_pct", "dist_hod_atr", "dist_lod_atr", "pricePosition",
              "emaDiff", "macdPct", "sma20_slope_pct", "atrPct", "volumeRatio", "volumeSurge", "vol_climax",
              "buyPressure", "flow3", "flow9prev", "vwapReclaim", "heat", "volumeHeat", "dist_pdh_atr", "dist_pdl_atr",
              "dist_round_atr", "upper_wick", "lower_wick", "bear_div", "bull_div"]


# ------------------------------------------------------------------------------------------------ panel helpers
def tod_slot(tod) -> np.ndarray:
    """Slot 0..62 for bar closes 09:50..15:00 (HHMM), -1 otherwise."""
    t = np.asarray(tod, float)
    mins = np.floor(t / 100) * 60 + np.mod(t, 100)
    s = (mins - (9 * 60 + 50)) / STEP
    ok = np.isfinite(s) & (s >= 0) & (s < N_SLOTS) & (np.mod(s, 1) == 0)
    return np.where(ok, s, -1).astype(int)


def _day_keys(df: pd.DataFrame) -> np.ndarray:
    if "symbol" in df.columns and "date" in df.columns:
        return pd.MultiIndex.from_arrays([df["symbol"].astype(str).to_numpy(), pd.Index(df["date"]).astype(str)]).factorize()[0]
    if isinstance(df.index, pd.DatetimeIndex):
        return pd.Index(df.index.date).factorize()[0]
    if "ts" in df.columns:
        return pd.Index(pd.to_datetime(df["ts"]).dt.date).factorize()[0]
    return np.zeros(len(df), int)          # one symbol-day


class Panel:
    """Rows of a frame laid out as a [symbol-day, slot] matrix (NaN where a bar is missing)."""

    def __init__(self, df: pd.DataFrame):
        self.n = len(df)
        self.sd = _day_keys(df)
        self.slot = tod_slot(df["tod"].to_numpy())
        self.ok = self.slot >= 0
        self.nsd = int(self.sd.max()) + 1 if self.n else 0
        self.r, self.k = self.sd[self.ok], self.slot[self.ok]
        self.flat = self.r * N_SLOTS + self.k
        self.okidx = np.flatnonzero(self.ok)

    def mat(self, x) -> np.ndarray:
        M = np.full(self.nsd * N_SLOTS, np.nan)
        M[self.flat] = np.asarray(x, float)[self.okidx]
        return M.reshape(self.nsd, N_SLOTS)

    def rows(self, M) -> np.ndarray:
        out = np.full(self.n, np.nan, dtype=np.float32)
        out[self.okidx] = M.reshape(-1)[self.flat]
        return out


def _shift(M, k):
    out = np.full_like(M, np.nan)
    if k < M.shape[1]:
        out[:, k:] = M[:, :M.shape[1] - k]
    return out


def _roll(M, k, fn):
    """Rolling reduce over the last k slots (current included); NaN until k slots exist."""
    st = np.stack([_shift(M, j) for j in range(k)], axis=0)
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        return fn(st, axis=0)


def _cum(M, fn):
    out = np.full_like(M, np.nan)
    acc = None
    for j in range(M.shape[1]):
        acc = M[:, j].copy() if acc is None else fn(acc, M[:, j])
        out[:, j] = acc
    return out


def _ewm(M, span):
    a = 2.0 / (span + 1)
    out = np.full_like(M, np.nan)
    prev = np.full(M.shape[0], np.nan)
    for j in range(M.shape[1]):
        x = M[:, j]
        prev = np.where(np.isnan(prev), x, np.where(np.isnan(x), prev, a * x + (1 - a) * prev))
        out[:, j] = np.where(np.isnan(x), np.nan, prev)
    return out


def _rsi(C, n):
    d = C - _shift(C, 1)
    g = _roll(np.clip(d, 0, None), n, np.sum) / n
    l = _roll(np.clip(-d, 0, None), n, np.sum) / n
    with np.errstate(invalid="ignore", divide="ignore"):
        r = 100 - 100 / (1 + g / l)
    return np.where(l == 0, np.where(g > 0, 100.0, 50.0), r)


def _count_since(flag):
    """Bars since the last True (0 on a True bar); NaN before the first True."""
    out = np.full(flag.shape, np.nan)
    last = np.full(flag.shape[0], np.nan)
    for j in range(flag.shape[1]):
        f = flag[:, j]
        last = np.where(f, j, last)
        out[:, j] = j - last
    return out


# ------------------------------------------------------------------------------------------------ compute
def compute(df: pd.DataFrame, names=None, context: bool = True) -> pd.DataFrame:
    """Indicators for every row of a lab frame (history frame, or the live LabStrategy frame of one symbol).
    names: subset to return (default all). context: compute the cross-asset/breadth family (needs symbol and date
    columns with many symbols per minute; otherwise those columns are NaN)."""
    names = list(INDICATORS) if names is None else list(names)
    bad = [n for n in names if n not in INDICATORS]
    if bad:
        raise KeyError(f"unknown indicators: {bad}")
    p = Panel(df)
    col = lambda c: p.mat(df[c].to_numpy(float)) if c in df.columns else np.full((p.nsd, N_SLOTS), np.nan)
    need = set(names)
    if any(INDICATORS[n].family == "ctx" for n in names):
        need.add("ret3")

    class _Rows(dict):              # store each needed indicator as float32 rows at once; drop the rest (memory)
        def __setitem__(self, k, M):
            if k in need:
                super().__setitem__(k, p.rows(M))

    out = _Rows()
    cache: dict[str, np.ndarray] = {}

    def M(c):
        if c not in cache:
            cache[c] = col(c)
        return cache[c]

    C, H, L, A = M("close"), M("high"), M("low"), M("atr_d")
    A = np.where(A > 0, A, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        o_open = C / (1 + M("fromOpen") / 100)
        pc = o_open / (1 + M("gap") / 100)
        R1 = (C / _shift(C, 1) - 1) * 100
        # --- momentum
        for k, nm in ((1, "ret1"), (3, "ret3"), (6, "ret6"), (12, "ret12")):
            out[nm] = (C / _shift(C, k) - 1) * 100
        out["ret3_atr"] = (C - _shift(C, 3)) / A
        out["ret_since950_atr"] = (C - C[:, [0]]) / A
        out["fromOpen"] = M("fromOpen")
        out["fromOpen_atr"] = (C - o_open) / A
        out["from_pc"] = (C / pc - 1) * 100
        out["from_pc_atr"] = (C - pc) / A
        out["gap"] = M("gap")
        out["gap_atr"] = (o_open - pc) / A
        out["momentum"] = M("momentum")
        # --- mean reversion
        if "rsi2" in need:
            out["rsi2"] = _rsi(C, 2)
        if "rsi7" in need:
            out["rsi7"] = _rsi(C, 7)
        for c in ("rsi5", "rsi", "rsiSlope", "vwapDistPct", "sma20_dist_pct", "sma50_dist_pct", "dist_hod_atr",
                  "dist_lod_atr", "pricePosition", "emaDiff", "macdPct", "sma20_slope_pct", "atrPct", "volumeRatio",
                  "volumeSurge", "buyPressure", "flow3", "flow9prev", "vwapReclaim", "heat",
                  "volumeHeat", "dist_pdh_atr", "dist_pdl_atr", "dist_round_atr", "upper_wick", "lower_wick",
                  "bear_div", "bull_div"):
            if c in need:
                out[c] = M(c)
        vwap = C / (1 + M("vwapDistPct") / 100)
        out["vwap_atr"] = (C - vwap) / A
        if need & {"z12", "bb_pctb12"}:
            mu, sd = _roll(C, 12, np.mean), _roll(C, 12, np.std)
            sd = np.where(sd > 0, sd, np.nan)
            out["z12"] = (C - mu) / sd
            out["bb_pctb12"] = (C - (mu - 2 * sd)) / (4 * sd)
        dh, dl = M("dist_hod_atr"), M("dist_lod_atr")
        rng = dh + dl
        out["day_pos"] = np.where(rng > 0, dl / rng, np.nan)
        # --- trend
        out["emaDiff_chg3"] = M("emaDiff") - _shift(M("emaDiff"), 3)
        out["macd_hist"] = M("macdPct") - _ewm(M("macdPct"), 9)
        e9 = _ewm(C, 9)
        out["ema9_slope_atr"] = (e9 - _shift(e9, 3)) / A
        if need & {"adx7", "di_diff7"}:
            up, dn = H - _shift(H, 1), _shift(L, 1) - L
            pdm = np.where((up > dn) & (up > 0), up, 0.0)
            ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
            pdm[np.isnan(up) | np.isnan(dn)] = np.nan
            ndm[np.isnan(up) | np.isnan(dn)] = np.nan
            tr = np.fmax(H - L, np.fmax(np.abs(H - _shift(C, 1)), np.abs(L - _shift(C, 1))))
            tr[np.isnan(_shift(C, 1))] = np.nan
            atr7 = _roll(tr, 7, np.mean)
            pdi, ndi = 100 * _roll(pdm, 7, np.mean) / atr7, 100 * _roll(ndm, 7, np.mean) / atr7
            dx = 100 * np.abs(pdi - ndi) / (pdi + ndi)
            out["adx7"] = _roll(dx, 7, np.mean)
            out["di_diff7"] = pdi - ndi
        hh = (H > _shift(H, 1)).astype(float)
        hh[np.isnan(_shift(H, 1)) | np.isnan(H)] = np.nan
        ll = (L < _shift(L, 1)).astype(float)
        ll[np.isnan(_shift(L, 1)) | np.isnan(L)] = np.nan
        out["hh_count6"] = _roll(hh, 6, np.sum)
        out["ll_count6"] = _roll(ll, 6, np.sum)
        if "slope6_atr" in need:
            st = np.stack([_shift(C, j) for j in range(6)], axis=0)   # st[j] = C shifted j (x = -j)
            xs = -np.arange(6, dtype=float)
            xs = xs - xs.mean()
            out["slope6_atr"] = np.einsum("j,jab->ab", xs, st) / (xs ** 2).sum() / A
        path = _roll(np.abs(C - _shift(C, 1)), 6, np.sum)
        out["eff6"] = np.where(path > 0, np.abs(C - _shift(C, 6)) / path, np.nan)
        # --- volatility
        out["atr_d_pct"] = A / C * 100
        br = H - L
        out["bar_range_atr"] = br / A
        prior = _roll(_shift(br, 1), 6, np.mean)
        out["range_exp"] = np.where(prior > 0, br / prior, np.nan)
        out["day_range_atr"] = rng
        prev = M("dist_pdh_atr") + M("dist_pdl_atr")
        out["prev_range_atr"] = prev
        out["day_vs_prev_range"] = np.where(prev > 0, rng / prev, np.nan)
        out["compress6_atr"] = (_roll(H, 6, np.max) - _roll(L, 6, np.min)) / A
        out["rv12"] = _roll(R1, 12, np.std)
        # --- flow
        out["flow_shift"] = M("flow3") - M("flow9prev")
        vr = M("volumeRatio")
        cnt = _cum(np.isfinite(vr).astype(float), np.add)
        out["rvol_day"] = _cum(np.nan_to_num(vr), np.add) / np.where(cnt > 0, cnt, np.nan)
        out["obv6"] = _roll(np.sign(R1) * vr, 6, np.sum)
        out["vol_trend"] = _roll(vr, 3, np.mean) / _roll(_shift(vr, 3), 6, np.mean)
        side = np.sign(M("vwapDistPct"))
        chg = (side != _shift(side, 1)) & np.isfinite(_shift(side, 1)) & np.isfinite(side)
        cc = _cum(chg.astype(float), np.add)
        cc[np.isnan(side)] = np.nan
        out["vwap_cross_n"] = cc
        same = _count_since(chg | (np.arange(N_SLOTS)[None, :] == 0))
        out["vwap_side_bars"] = np.where(np.isnan(side), np.nan, side * (same + 1))
        # --- structure (opening range = 09:30-09:50 high/low, read at the 09:50 bar)
        orh = (C[:, 0] + dh[:, 0] * A[:, 0])[:, None]
        orl = (C[:, 0] - dl[:, 0] * A[:, 0])[:, None]
        out["or_high_dist_atr"] = (C - orh) / A
        out["or_low_dist_atr"] = (C - orl) / A
        above = _cum((C > orh).astype(float), np.fmax)
        below = _cum((C < orl).astype(float), np.fmax)
        out["orb_fail_up"] = np.where(np.isnan(C), np.nan, ((above > 0) & (C < orh)).astype(float))
        out["orb_fail_dn"] = np.where(np.isnan(C), np.nan, ((below > 0) & (C > orl)).astype(float))
        nh = np.where(np.isnan(dh), np.nan, (dh <= 1e-9).astype(float))
        nl = np.where(np.isnan(dl), np.nan, (dl <= 1e-9).astype(float))
        out["new_hod"], out["new_lod"] = nh, nl
        out["bars_since_hod"] = np.where(np.isnan(C), np.nan, _count_since(nh == 1))
        out["bars_since_lod"] = np.where(np.isnan(C), np.nan, _count_since(nl == 1))
        # --- time
        tmin = np.broadcast_to(20.0 + STEP * np.arange(N_SLOTS)[None, :], C.shape)
        out["tod_min"] = np.where(np.isnan(C), np.nan, tmin)

    res = {n: out[n] for n in names if n in out}
    if "dow" in need:
        if "date" in df.columns:
            d = pd.to_datetime(pd.Series(df["date"]).astype(str)).dt.dayofweek.to_numpy(float)
        elif isinstance(df.index, pd.DatetimeIndex):
            d = np.asarray(df.index.dayofweek, float)
        else:
            d = np.full(len(df), np.nan)
        res["dow"] = np.where(p.ok, d, np.nan)
    ctx_names = [n for n in names if INDICATORS[n].family == "ctx"]
    if ctx_names:
        cx = _context(df, p, out) if context and {"symbol", "date"} <= set(df.columns) else {}
        for n in ctx_names:
            res[n] = cx.get(n, np.full(len(df), np.nan))
    return pd.DataFrame({n: res[n].astype("float32") for n in names}, index=df.index)


def _context(df: pd.DataFrame, p: Panel, out: dict) -> dict:
    """Cross-asset/breadth indicators: same-minute values of SPY/QQQ/IWM and of the whole frame's universe.
    Point-in-time: every value is at the same (date, bar close) as the row."""
    key = pd.MultiIndex.from_arrays([pd.Index(df["date"]).astype(str), df["tod"].to_numpy()])
    sym = df["symbol"].astype(str).to_numpy()
    fo = df["fromOpen"].to_numpy(float)
    r3 = np.asarray(out["ret3"], float)
    res = {}
    ok = p.ok
    for s in CTX_SYMBOLS:
        m = (sym == s) & ok
        ser = pd.Series(fo[m], index=key[m])
        ser = ser[~ser.index.duplicated()]
        res[f"{s.lower()}_fromOpen"] = ser.reindex(key).to_numpy(float)
        if s == "SPY":
            s3 = pd.Series(r3[m], index=key[m])
            s3 = s3[~s3.index.duplicated()]
            res["spy_ret3"] = s3.reindex(key).to_numpy(float)
    res["rs_spy"] = fo - res["spy_fromOpen"]
    res["rs_spy3"] = r3 - res["spy_ret3"]
    vd = df["vwapDistPct"].to_numpy(float)
    g = pd.DataFrame({"a": np.where(np.isfinite(vd), (vd > 0).astype(float), np.nan), "f": fo}, index=key)[ok]
    agg = g.groupby(level=[0, 1]).agg(a=("a", "mean"), f=("f", "median"))
    res["breadth_vwap"] = agg["a"].reindex(key).to_numpy(float)
    res["breadth_med_fromOpen"] = agg["f"].reindex(key).to_numpy(float)
    res["rs_univ"] = fo - res["breadth_med_fromOpen"]
    for k in res:
        res[k] = np.where(ok, res[k], np.nan)
    return res
