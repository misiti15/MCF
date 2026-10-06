"""Initial setup library. Parameters live in config/default.yaml.

Each setup cites the idea it is based on; see docs/RESEARCH.md for evidence and caveats.
These are starting points to be validated on real data — not proven edges.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

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
        return (ctx.rank_rvol is not None and ctx.rank_rvol <= self.params.get("top_n", 20)
                and ctx.atr >= self.params.get("min_atr", 0.0))

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


class RuleStrategy(Strategy):
    """A layered rule promoted from setup discovery (mcf/discovery.py), e.g.
    short when "RSI14 > 65" + "below 20 SMA". Enters at the close of the FIRST complete 5-minute bar
    where every layer holds (same definition the miner measured); stop 1R, target `target_r` R,
    with R = r_atr_frac x daily ATR. Configure under `strategies:` with `type: rule`."""

    name = "rule"

    def __init__(self, name: str, layers: list[str], side: str, r_atr_frac: float = 0.25,
                 target_r: float | None = 1.0, **params):
        super().__init__(layers=layers, side=side, r_atr_frac=r_atr_frac, target_r=target_r, **params)
        self.name = name
        from ..layers import LABELS

        unknown = [x for x in layers if x not in LABELS]
        if unknown:
            raise ValueError(f"{name}: unknown layers {unknown}")

    def generate(self, ctx: DayContext):
        from ..data.bars import resample
        from ..layers import layer_frame, rule_mask

        bars = ctx.bars
        d5 = resample(bars, "5min")
        last_end = bars.index[-1] + pd.Timedelta(minutes=1)
        d5 = d5[d5.index + pd.Timedelta(minutes=5) <= last_end]          # complete 5-min bars only
        if d5.empty:
            return []
        rv = ctx.rvol()
        ends = [bars.index.searchsorted(ts + pd.Timedelta(minutes=4)) for ts in d5.index]
        ends = [min(e, len(bars) - 1) for e in ends]
        f = layer_frame(d5, ctx.prior5, ctx.prev_close, rv.to_numpy()[ends])
        hits = np.flatnonzero(rule_mask(f, self.layers))
        if not len(hits):
            return []
        i = hits[0]
        side = 1 if self.side == "long" else -1
        px = float(f["close"].iloc[i])
        r = self.r_atr_frac * ctx.atr
        if r <= 0:
            return []
        tgt = None if self.target_r is None else px + side * self.target_r * r
        return [Signal(ctx.symbol, self.name, side, int(ends[i]), stop=px - side * r, target=tgt,
                       meta={"layers": " + ".join(self.layers)})]


class HeatStrategy(Strategy):
    """A re-weighted MarcoFlow heat score (mcf/research/heat.py) from the heat-score study.
    `formula` names a module file exposing score(df), LONG_AT and SHORT_AT (research/heat/candidates/*.py).
    Enters at the close of the first complete 5-minute bar where the score crosses its threshold
    (long >= LONG_AT, short <= SHORT_AT); stop 1R, target `target_r` R, R = r_atr_frac x daily ATR —
    the same outcome model the study measured. Configure under `strategies:` with `type: heat`."""

    name = "heat"

    def __init__(self, name: str, formula: str, r_atr_frac: float = 0.25, target_r: float | None = 1.0,
                 sides: str = "both", **params):
        super().__init__(formula=formula, r_atr_frac=r_atr_frac, target_r=target_r, sides=sides, **params)
        self.name = name
        import importlib.util
        from pathlib import Path

        path = Path(formula)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path
        spec = importlib.util.spec_from_file_location(f"heat_{name}", path)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def generate(self, ctx: DayContext):
        from ..data.bars import resample
        from ..research.heat import heat_frame

        bars = ctx.bars
        d5 = resample(bars, "5min")
        last_end = bars.index[-1] + pd.Timedelta(minutes=1)
        d5 = d5[d5.index + pd.Timedelta(minutes=5) <= last_end]
        if d5.empty:
            return []
        hist = d5 if ctx.prior5 is None or ctx.prior5.empty else pd.concat([ctx.prior5, d5])
        f = heat_frame(hist).iloc[-len(d5):].copy()
        f["atr_d"] = ctx.atr
        f["gap"] = (float(d5["open"].iloc[0]) / ctx.prev_close - 1) * 100
        s = np.asarray(self.mod.score(f), dtype=float)
        ok = (f["tod"].to_numpy() >= 950) & (f["tod"].to_numpy() <= 1500)
        cands = []
        if self.sides in ("both", "long") and getattr(self.mod, "LONG_AT", None) is not None:
            hit = np.flatnonzero(ok & (s >= self.mod.LONG_AT))
            if len(hit):
                cands.append((hit[0], 1))
        if self.sides in ("both", "short") and getattr(self.mod, "SHORT_AT", None) is not None:
            hit = np.flatnonzero(ok & (s <= self.mod.SHORT_AT))
            if len(hit):
                cands.append((hit[0], -1))
        out = []
        for i, side in sorted(cands):
            end = min(bars.index.searchsorted(d5.index[i] + pd.Timedelta(minutes=4)), len(bars) - 1)
            px, r = float(d5["close"].iloc[i]), self.r_atr_frac * ctx.atr
            if r <= 0:
                continue
            tgt = None if self.target_r is None else px + side * self.target_r * r
            out.append(Signal(ctx.symbol, self.name, side, int(end), stop=px - side * r, target=tgt,
                              meta={"heat_score": float(s[i])}))
        return out[:1]


REGISTRY: dict[str, type[Strategy]] = {
    c.name: c
    for c in (OpeningRangeBreakout, NoiseBandMomentum, IntradayMomentum, VWAPReclaim, GapAndGo, GapFade,
              VWAPReversion)
}
from .research_setups import RESEARCH_REGISTRY  # noqa: E402

REGISTRY.update(RESEARCH_REGISTRY)


def build_strategies(cfg: dict) -> list[Strategy]:
    out = []
    top_n = cfg.get("universe", {}).get("stocks_in_play_top_n", 20)
    exits = cfg.get("exits", {})
    for name, params in cfg.get("strategies", {}).items():
        params = {**exits, **params}
        if not params.pop("enabled", True):
            continue
        kind = params.pop("type", None)
        if kind == "rule":
            out.append(RuleStrategy(name=name, **params))
            continue
        if kind == "heat":
            out.append(HeatStrategy(name=name, **params))
            continue
        cls_name = params.pop("class", name)   # several configs of one setup: orb20_a / orb20_b -> class orb20
        if cls_name not in REGISTRY:
            continue
        if cls_name != name:
            st = REGISTRY[cls_name](**params)
            st.name = name
            out.append(st)
            continue
        if name == "orb":
            params.setdefault("top_n", top_n)
        out.append(REGISTRY[name](**params))
    return out
