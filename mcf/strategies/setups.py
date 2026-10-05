"""Initial setup library. Parameters live in config/default.yaml.

Each setup cites the idea it is based on; see docs/RESEARCH.md for evidence and caveats.
These are starting points to be validated on real data — not proven edges.
"""

from __future__ import annotations

import numpy as np

from .. import features as F
from .base import DayContext, Signal, Strategy, t


class OpeningRangeBreakout(Strategy):
    """Opening Range Breakout on 'stocks in play' (Zarattini, Barbon & Aziz 2024).

    Trade only the top-N names by opening relative volume. Direction from the first
    `range_minutes` candle; stop-entry at the range extreme; stop = stop_atr_frac * daily ATR;
    exit at end of day (or target_r if set).
    """

    name = "orb"

    def eligible(self, ctx):
        return ctx.rank_rvol is not None and ctx.rank_rvol <= self.params.get("top_n", 20)

    def generate(self, ctx: DayContext):
        hi, lo, last = F.opening_range(ctx.bars, self.range_minutes)
        if last < 0 or last + 1 >= len(ctx.bars):
            return []
        rv = ctx.rvol().iloc[last]
        if not (rv >= self.min_rvol):
            return []
        o = ctx.bars["open"].iloc[0]
        c = ctx.bars["close"].iloc[last]
        if c == o:
            return []
        side = 1 if c > o else -1
        entry = hi if side == 1 else lo
        stop = entry - side * self.stop_atr_frac * ctx.atr
        tr = self.params.get("target_r")
        target = entry + side * tr * abs(entry - stop) if tr else None
        return [
            Signal(ctx.symbol, self.name, side, last, stop, target, "stop", entry,
                   entry_valid_bars=390, meta={"rvol": float(rv), "or_hi": hi, "or_lo": lo})
        ]


class VWAPReclaim(Strategy):
    """Long when a stock in play that traded below VWAP closes back above it on rising volume."""

    name = "vwap_reclaim"

    def eligible(self, ctx):
        return ctx.rank_rvol is not None and ctx.rank_rvol <= 50

    def generate(self, ctx):
        bars, vw, rv, times = ctx.bars, ctx.vwap(), ctx.rvol(), ctx.times()
        close = bars["close"].to_numpy()
        lo = bars["low"].to_numpy()
        vwv = vw.to_numpy()
        e, l = t(self.earliest), t(self.latest)
        n = self.lookback_bars
        for i in range(max(n, 1), len(bars) - 1):
            if times[i] < e:
                continue
            if times[i] > l:
                break
            below_recently = (close[i - n : i] < vwv[i - n : i]).sum() >= n * 0.6
            if below_recently and close[i - 1] < vwv[i - 1] and close[i] > vwv[i] and rv.iloc[i] >= self.min_rvol:
                stop = lo[i - n : i + 1].min()
                risk = close[i] - stop
                if risk <= 0 or risk > 0.5 * ctx.atr:
                    continue
                return [Signal(ctx.symbol, self.name, 1, i, stop, close[i] + self.target_r * risk,
                               meta={"rvol": float(rv.iloc[i])})]
        return []


class GapAndGo(Strategy):
    """Gap >= min_gap_pct with heavy volume: buy the break of the opening range high."""

    name = "gap_and_go"

    def eligible(self, ctx):
        return ctx.gap_pct >= self.min_gap_pct

    def generate(self, ctx):
        hi, lo, last = F.opening_range(ctx.bars, self.range_minutes)
        if last < 0 or last + 1 >= len(ctx.bars):
            return []
        rv = ctx.rvol().iloc[last]
        if not (rv >= self.min_rvol) or ctx.bars["close"].iloc[last] < ctx.vwap().iloc[last]:
            return []
        risk = hi - lo
        if risk <= 0:
            return []
        return [Signal(ctx.symbol, self.name, 1, last, lo, hi + self.target_r * risk, "stop", hi,
                       entry_valid_bars=60, exit_by=t(self.exit_by),
                       meta={"gap_pct": ctx.gap_pct, "rvol": float(rv)})]


class GapFade(Strategy):
    """Fade modest gaps on ordinary volume back toward the prior close (gap-fill)."""

    name = "gap_fade"

    def eligible(self, ctx):
        return self.min_gap_pct <= abs(ctx.gap_pct) <= self.max_gap_pct

    def generate(self, ctx):
        hi, lo, last = F.opening_range(ctx.bars, self.range_minutes)
        if last < 0 or last + 1 >= len(ctx.bars):
            return []
        rv = ctx.rvol().iloc[last]
        if not (rv <= self.max_rvol):
            return []
        side = -1 if ctx.gap_pct > 0 else 1
        c = ctx.bars["close"].iloc[last]
        vw = ctx.vwap().iloc[last]
        # require the open to be failing: price back on the prior-close side of VWAP
        if (side == -1 and c >= vw) or (side == 1 and c <= vw):
            return []
        stop = hi if side == -1 else lo
        target = ctx.prev_close
        if side * (target - c) <= 0 or side * (c - stop) >= 0:
            return []
        return [Signal(ctx.symbol, self.name, side, last, stop, target, exit_by=t(self.exit_by),
                       meta={"gap_pct": ctx.gap_pct, "rvol": float(rv)})]


class IntradayMomentum(Strategy):
    """Market intraday momentum (Gao, Han, Li & Zhou 2018): the first-half-hour return
    (prev close -> 10:00) predicts the direction of the last half hour for index ETFs."""

    name = "intraday_momentum"

    def eligible(self, ctx):
        return ctx.symbol in set(self.symbols)

    def generate(self, ctx):
        times = ctx.times()
        st, et = t(self.signal_time), t(self.entry_time)
        sig_idx = np.flatnonzero(times < st)
        ent_idx = np.flatnonzero(times < et)
        if len(sig_idx) == 0 or len(ent_idx) == 0 or ent_idx[-1] + 1 >= len(times):
            return []
        r = (ctx.bars["close"].iloc[sig_idx[-1]] / ctx.prev_close - 1) * 100
        if abs(r) < self.min_abs_return_pct:
            return []
        side = 1 if r > 0 else -1
        i = ent_idx[-1]
        c = ctx.bars["close"].iloc[i]
        return [Signal(ctx.symbol, self.name, side, i, c - side * self.stop_atr_frac * ctx.atr,
                       meta={"first_30m_ret": float(r)})]


class VWAPReversion(Strategy):
    """Mean reversion to VWAP after a > band_std deviation in liquid, non-trending names."""

    name = "vwap_reversion"

    def eligible(self, ctx):
        return ctx.avg_dollar_volume >= 50e6

    def generate(self, ctx):
        bars, vw, sd, rv, times = ctx.bars, ctx.vwap(), ctx.vwap_std(), ctx.rvol(), ctx.times()
        close = bars["close"].to_numpy()
        e, l = t(self.earliest), t(self.latest)
        for i in range(1, len(bars) - 1):
            if times[i] < e:
                continue
            if times[i] > l:
                break
            s = sd.iloc[i]
            if not s or np.isnan(s) or rv.iloc[i] > self.max_rvol:
                continue
            z = (close[i] - vw.iloc[i]) / s
            zp = (close[i - 1] - vw.iloc[i - 1]) / sd.iloc[i - 1] if sd.iloc[i - 1] else 0
            # enter on the first bar that turns back inside the band
            if zp <= -self.band_std < z:
                side = 1
            elif zp >= self.band_std > z:
                side = -1
            else:
                continue
            stop = close[i] - side * self.stop_std * s
            return [Signal(ctx.symbol, self.name, side, i, stop, float(vw.iloc[i]), meta={"z": float(z)})]
        return []


class NoiseBandMomentum(Strategy):
    """Noise-area intraday momentum on index ETFs (Zarattini, Aziz & Barbon 2024, "Beat the Market").

    Band_t = max(open, prev_close) * (1 + sigma_t) / min(open, prev_close) * (1 - sigma_t), sigma_t =
    14-day average |close_t/open - 1| at the same minute. Checked on the half hour from 10:00;
    first close outside the band enters. Simplification vs paper: a single entry per day with a fixed
    stop at the farther-in of band and VWAP (paper trails it and can re-enter), exit at close.
    """

    name = "noise_band_momentum"

    def eligible(self, ctx):
        return ctx.symbol in set(self.symbols) and ctx.avg_move is not None

    def generate(self, ctx):
        bars, times = ctx.bars, ctx.times()
        o = bars["open"].iloc[0]
        up_ref, dn_ref = max(o, ctx.prev_close), min(o, ctx.prev_close)
        mos = F.minute_of_session(bars.index)
        vw = ctx.vwap().to_numpy()
        close = bars["close"].to_numpy()
        fc, lc = t(self.first_check), t(self.last_check)
        for i in range(len(bars) - 1):
            tm = times[i]
            if tm < fc or (tm.minute + 1) % 30 != 0:  # bar ending on :00 / :30
                continue
            if tm > lc:
                break
            m = min(mos[i], len(ctx.avg_move) - 1)
            sigma = ctx.avg_move[m] * self.band_mult
            if np.isnan(sigma):
                continue
            upper, lower = up_ref * (1 + sigma), dn_ref * (1 - sigma)
            # stop = the farther-in (closer to price) of band and VWAP, as in the paper's trailing stop
            if close[i] > upper:
                stop = max(upper, vw[i]) if vw[i] < close[i] else upper
                return [Signal(ctx.symbol, self.name, 1, i, stop, meta={"sigma": float(sigma)})]
            if close[i] < lower:
                stop = min(lower, vw[i]) if vw[i] > close[i] else lower
                return [Signal(ctx.symbol, self.name, -1, i, stop, meta={"sigma": float(sigma)})]
        return []


REGISTRY: dict[str, type[Strategy]] = {
    c.name: c
    for c in (OpeningRangeBreakout, NoiseBandMomentum, IntradayMomentum, VWAPReclaim, GapAndGo, GapFade,
              VWAPReversion)
}


def build_strategies(cfg: dict) -> list[Strategy]:
    out = []
    top_n = cfg.get("universe", {}).get("stocks_in_play_top_n", 20)
    exits = cfg.get("exits", {})
    for name, params in cfg.get("strategies", {}).items():
        params = {**exits, **params}
        if not params.pop("enabled", True) or name not in REGISTRY:
            continue
        if name == "orb":
            params.setdefault("top_n", top_n)
        out.append(REGISTRY[name](**params))
    return out
