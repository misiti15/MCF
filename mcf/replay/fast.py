"""Replay fast path: per-session caches that give the live code the same answers it would compute itself, faster.

The live runner rebuilds each lab setup's 5-minute feature frame and mask from the session's bars so far on every poll
(heat_frame + extra_features over PRIOR5_BARS warm-up + today's 5-minute bars). Every feature is causal (rolling /
ewm / shift over past rows), so the frame of the first j completed 5-minute bars is the first j rows of the frame
built once from the whole session, and a row-wise mask over it is the first j values of the whole-session mask. The
fast path therefore builds, once per session and symbol, the frame exactly as LabStrategy.generate does (by calling
it), and serves prefixes of it:

  frames   mcf.strategies.setups._LAB_FRAMES is replaced by a provider that returns the whole-session frame cut to the
           poll's completed 5-minute bars (anything it does not know is built by the real code, as live).
  masks    each lab setup's module is wrapped; mask(frame prefix) returns the whole-session mask's prefix.
  gate     after the runner's own _contexts() (universe, in-play filter, ranking - unchanged), a symbol is dropped from
           the poll's loop only when no setup can act on it this poll: every lab setup either is not eligible
           (its own eligible(): a completed 5-minute clock bucket, window, ADV, ...) or its mask has no hit on the
           buckets the latest bar decides
           (the runner acts only on signals of the latest bar), and no other setup type is eligible.
  pinned   engine.pinned_symbols(cfg) memoised per config object (it walks every setup on every call).

`check()` re-computes a sample of (symbol, poll) frames and every setup's mask from the truncated bars with the real
code and counts any difference; the harness reports it per session, and `exact=True` (CLI --exact) turns the fast
path off entirely. Educational only - not financial advice."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..strategies import setups as S
from ..strategies.base import DayContext


_SHARED: dict = {}     # (session, symbol) -> (frame, bucket ends, priors object): reused by the next account


class FrameProvider(dict):
    """Stands in for setups._LAB_FRAMES: (symbol, date, n bars, last bar) -> frame of the completed 5-minute bars."""

    def __init__(self, session: "FastSession"):
        super().__init__()
        self.s = session
        self.hits = self.misses = 0

    def get(self, key, default=None):
        sym, day, n, last = key
        f = self.s.prefix_frame(sym, last)
        if f is not None:
            self.hits += 1
            return f
        self.misses += 1
        return dict.get(self, key, default)

    def __len__(self):                       # generate() clears the cache above 4,000 entries; never needed here
        return min(dict.__len__(self), 10)


class MaskModule:
    """A lab module whose mask(frame) is served from the whole-session mask when the frame is a known prefix."""

    def __init__(self, mod, name: str, session: "FastSession"):
        self.__dict__["_mod"], self.__dict__["_name"], self.__dict__["_s"] = mod, name, session

    def __getattr__(self, k):
        return getattr(self._mod, k)

    def mask(self, f):
        key = f.attrs.get("replay_prefix") if hasattr(f, "attrs") else None
        if key is not None:
            m = self._s.full_mask(self._name, key[0])
            if m is not None and len(m) >= key[1]:
                self._s.mask_hits += 1
                return m[: key[1]]
        self._s.mask_misses += 1
        return self._mod.mask(f)


class FastSession:
    def __init__(self, runner, day_bars: dict[str, pd.DataFrame], today):
        self.r, self.bars, self.today = runner, day_bars, today
        self.lab = [s for s in runner.strategies if isinstance(s, S.LabStrategy)]
        self.heat = [s for s in runner.strategies if isinstance(s, S.HeatStrategy)]
        self.other = [s for s in runner.strategies if not isinstance(s, (S.LabStrategy, S.HeatStrategy))]
        self.hscore: dict[tuple[str, str], tuple | None] = {}
        self.frames: dict[str, pd.DataFrame | None] = {}
        self.ends: dict[str, np.ndarray] = {}
        self.ctx_full: dict[str, DayContext] = {}
        self.masks: dict[tuple[str, str], np.ndarray | None] = {}
        self._pref: dict[tuple[str, int], pd.DataFrame] = {}
        self.mask_hits = self.mask_misses = 0
        self.dropped = self.kept = 0
        self.rv: dict = {}
        self.gen_skipped = 0
        self.tod: dict[str, np.ndarray] = {}

    # ---------------------------------------------------------------- whole-session frames (built by the real code)
    def _ctx(self, sym) -> DayContext | None:
        if sym not in self.ctx_full:
            p, b = self.r.priors.get(sym), self.bars.get(sym)
            self.ctx_full[sym] = None if p is None or b is None or b.empty else DayContext(
                symbol=sym, date=self.today, bars=b, prev_close=p.prev_close, prev_high=p.prev_high,
                prev_low=p.prev_low, atr=p.atr, avg_dollar_volume=p.adv, avg_cum_volume=p.avg_cum,
                avg_move=p.avg_move, prior5=getattr(p, "tail5", None), sma20=getattr(p, "sma20", float("nan")),
                peers=self.bars)
        return self.ctx_full[sym]

    def frame(self, sym) -> pd.DataFrame | None:
        g = _SHARED.get((str(self.today), sym))
        if sym not in self.frames and g is not None and self.r.priors.get(sym) is g[2]:
            self.frames[sym], self.ends[sym] = g[0], g[1]       # built for another account of this session
            self.tod[sym] = g[0]["tod"].to_numpy()
        if sym not in self.frames:
            self.frames[sym] = None
            ctx = self._ctx(sym)
            if ctx is not None and self.lab:
                from ..data.bars import resample

                d5 = resample(ctx.bars, "5min")
                end = ctx.bars.index[-1] + pd.Timedelta(minutes=1)
                d5 = d5[d5.index + pd.Timedelta(minutes=5) <= end]
                key = (sym, str(ctx.date), len(ctx.bars), ctx.bars.index[-1])
                saved = S._LAB_FRAMES
                S._LAB_FRAMES = {}
                try:
                    st = self.lab[0]
                    mod = st.mod
                    st.mod = getattr(mod, "_mod", mod)          # the real module: generate builds and caches the frame
                    try:
                        type(st).generate(st, ctx)
                    except Exception:
                        pass
                    finally:
                        st.mod = mod
                    f = S._LAB_FRAMES.get(key)
                finally:
                    S._LAB_FRAMES = saved
                if f is not None and len(f) == len(d5):
                    self.frames[sym] = f
                    self.ends[sym] = (d5.index + pd.Timedelta(minutes=5)).as_unit("ns").asi8
                    self.tod[sym] = f["tod"].to_numpy()
                    if len(_SHARED) > 6000:
                        _SHARED.clear()
                    _SHARED[(str(self.today), sym)] = (f, self.ends[sym], self.r.priors.get(sym))
        return self.frames[sym]

    def prefix_frame(self, sym, last_bar) -> pd.DataFrame | None:
        f = self.frame(sym)
        if f is None:
            return None
        j = int(np.searchsorted(self.ends[sym], (pd.Timestamp(last_bar) + pd.Timedelta(minutes=1)).value,
                                side="right"))
        if j == 0:
            return None
        k = (sym, j)
        if k not in self._pref:
            if len(self._pref) > 5000:
                self._pref.clear()
            g = f.iloc[:j].copy()
            g.attrs["replay_prefix"] = (sym, j)
            self._pref[k] = g
        return self._pref[k]

    def full_mask(self, name, sym) -> np.ndarray | None:
        k = (name, sym)
        if k not in self.masks:
            self.masks[k] = None
            st = next((s for s in self.lab if s.name == name), None)
            f = self.frame(sym)
            if st is not None and f is not None:
                g = f
                if st.context:
                    from ..strategies.lab_context import add_context

                    g = add_context(f, self.bars, st.context)
                mod = getattr(st.mod, "_mod", st.mod)
                self.masks[k] = np.asarray(mod.mask(g), dtype=bool)
        return self.masks[k]

    # ---------------------------------------------------------------- poll gate
    def can_act(self, ctx) -> bool:
        """False only when no setup can produce a signal on this symbol's latest bar this poll."""
        for st in self.other:
            if getattr(st, "ticker_split", None) and not st.trades_symbol(ctx.symbol):
                continue
            if st.eligible(ctx):
                return True
        sym = ctx.symbol
        n = len(ctx.bars)
        if n >= 5 and n % 5 == 0:                                # heat eligible() needs n % 5 == 0
            for st in self.heat:
                if getattr(st, "ticker_split", None) and not st.trades_symbol(sym):
                    continue
                if self.heat_hit(st, ctx) and st.eligible(ctx):
                    return True
        # lab eligible(): the latest bar must decide a completed 5-minute clock bucket (GX1 clock gate, the same
        # function as live); one bucket, or two when the previous bar's bucket had no 4th-minute bar
        k = len(S.lab_decision_buckets(ctx.bars.index)) if n != 390 else 1
        if not k or not self.lab:
            return False
        f = self.frame(sym)
        if f is None:
            return any(st.eligible(ctx) for st in self.lab)      # unknown here: let the real code decide
        j = int(np.searchsorted(self.ends[sym], ctx.bars.index[-1].value + 60_000_000_000, side="right"))
        if j == 0:
            return False                                         # no completed 5-minute bar: generate() returns []
        rows = range(max(0, j - k), j)                           # the decided buckets are the latest completed ones
        tods = [self.tod[sym][r] for r in rows]
        for st in self.lab:
            if getattr(st, "ticker_split", None) and not st.trades_symbol(sym):
                continue
            lo, hi = st.window or (950, 1500)
            ok = [r for r, tod in zip(rows, tods) if max(950, lo) <= tod <= min(1500, hi)]
            if not ok:
                continue
            m = self.full_mask(st.name, sym)
            if m is None or len(m) < j:
                if st.eligible(ctx):
                    return True
                continue
            if any(m[r] for r in ok) and st.eligible(ctx):       # a hit on a bucket the latest bar decides, and eligible
                return True
        return False

    # ---------------------------------------------------------------- heat setups (score per 5-minute bar: causal)
    def heat_full(self, st, sym):
        """(score array, tod array, bucket ends) of a heat setup over the whole session, from its real generate()."""
        k = (st.name, sym)
        if k not in self.hscore:
            self.hscore[k] = None
            ctx = self._ctx(sym)
            if ctx is not None:
                got = {}
                mod = st.mod
                real = getattr(mod, "_mod", mod)

                class _Cap:
                    def __getattr__(self, a):
                        return getattr(real, a)

                    def score(self, f):
                        got["f"], got["s"] = f, np.asarray(real.score(f), dtype=float)
                        return got["s"]

                st.mod = _Cap()
                try:
                    type(st).generate(st, ctx)
                except Exception:
                    pass
                finally:
                    st.mod = mod
                if "s" in got:
                    from ..data.bars import resample

                    d5 = resample(ctx.bars, "5min")
                    end = ctx.bars.index[-1] + pd.Timedelta(minutes=1)
                    d5 = d5[d5.index + pd.Timedelta(minutes=5) <= end]
                    if len(d5) == len(got["s"]):
                        self.hscore[k] = (got["s"], got["f"]["tod"].to_numpy(),
                                          (d5.index + pd.Timedelta(minutes=5)).as_unit("ns").asi8)
        return self.hscore[k]

    def heat_hit(self, st, ctx) -> bool:
        """True when the heat setup's score crosses a threshold on the latest completed 5-minute bar (or unknown)."""
        h = self.heat_full(st, ctx.symbol)
        if h is None:
            return True                                          # unknown: let the real code decide
        sc, tod, ends = h
        j = int(np.searchsorted(ends, ctx.bars.index[-1].value + 60_000_000_000, side="right"))
        if j == 0:
            return False
        lo, hi = st.window or (950, 1500)
        if not max(950, lo) <= tod[j - 1] <= min(1500, hi):
            return False
        v = sc[j - 1]
        la, sa = getattr(st.mod, "LONG_AT", None), getattr(st.mod, "SHORT_AT", None)
        return bool((st.sides in ("both", "long") and la is not None and v >= la) or
                    (st.sides in ("both", "short") and sa is not None and v <= sa))

    # ---------------------------------------------------------------- rvol (cumulative volume / profile: causal)
    def on_slice(self, sym: str, k: int, df, old=None):
        """The feed hands out bars[:k] of `sym`: register it so DayContext.rvol() serves the session rvol's prefix."""
        if old is not None:
            _RVOL.pop(id(old), None)
        full = self._rvol_full(sym)
        if full is not None:
            _RVOL[id(df)] = (df, full, k)

    def _rvol_full(self, sym):
        if sym not in self.rv:
            ctx = self._ctx(sym)
            self.rv[sym] = None if ctx is None else _ORIG_RVOL(ctx)
        return self.rv[sym]

    def install(self):
        """Patch the module-level hooks and wrap this runner's lab modules and _contexts (one process, one session)."""
        from ..backtest import engine

        from ..research import heat as H

        self._saved = (S._LAB_FRAMES, engine.pinned_symbols)
        self._heat_saved = H.heat_frame
        S._LAB_FRAMES = FrameProvider(self)
        H.heat_frame = _memo_heat_frame
        orig_pinned = self._saved[1]
        memo: dict = {}

        def pinned(cfg):
            k = id(cfg)
            if k not in memo:
                memo[k] = (cfg, orig_pinned(cfg))
            return memo[k][1]

        engine.pinned_symbols = pinned
        for st in self.lab:
            st.mod = MaskModule(st.mod, st.name, self)
            st.generate = self._gen_wrap(st, st.generate)       # instance attribute; uninstall() removes it
        for st in self.heat:
            st.generate = self._heat_wrap(st, st.generate)
        orig_ctx = self.r._contexts

        def contexts(today_bars, today):
            out = orig_ctx(today_bars, today)
            keep = [c for c in out if self.can_act(c)]
            self.kept += len(keep)
            self.dropped += len(out) - len(keep)
            return keep

        self.r._contexts = contexts
        _RVOL.clear()
        _RVOL_FULL_OK[0] = not self.other
        DayContext.rvol = _fast_rvol
        return self

    def _gen_wrap(self, st, real):
        """generate() of a lab setup that skips the build when its whole-session mask has no hit on a bucket the latest
        bar decides: the runner only acts on signals of the latest bar, so the result would be ignored anyway."""
        def gen(ctx):
            f = self.frame(ctx.symbol)
            m = self.full_mask(st.name, ctx.symbol) if f is not None else None
            if f is not None and m is not None and len(ctx.bars):
                j = int(np.searchsorted(self.ends[ctx.symbol], ctx.bars.index[-1].value + 60_000_000_000,
                                        side="right"))
                k = max(1, len(S.lab_decision_buckets(ctx.bars.index)))   # buckets the latest bar decides (GX1)
                if j == 0 or (len(m) >= j and not m[max(0, j - k):j].any()):
                    self.gen_skipped += 1
                    return []
            return real(ctx)
        return gen

    def _heat_wrap(self, st, real):
        """generate() of a heat setup: skipped when its whole-session score does not cross a threshold on the latest
        completed 5-minute bar (the runner ignores signals of earlier bars)."""
        def gen(ctx):
            if len(ctx.bars) and not self.heat_hit(st, ctx):
                self.gen_skipped += 1
                return []
            return real(ctx)
        return gen

    def uninstall(self):
        from ..backtest import engine

        from ..research import heat as H

        S._LAB_FRAMES, engine.pinned_symbols = self._saved
        H.heat_frame = self._heat_saved
        _HEAT_MEMO.clear()
        DayContext.rvol = _ORIG_RVOL
        _RVOL.clear()
        for st in self.lab:
            st.mod = getattr(st.mod, "_mod", st.mod)
            st.__dict__.pop("generate", None)
        for st in self.heat:
            st.__dict__.pop("generate", None)

    # ---------------------------------------------------------------- fidelity check
    def check(self, samples: int = 24, seed: int = 0) -> dict:
        """Re-build `samples` random (symbol, poll) frames from the truncated bars with the real code (no cache) and
        compare them, and every lab setup's mask on them, with the served prefixes."""
        rng = np.random.default_rng(seed)
        syms = [s for s in self.frames if self.frames[s] is not None]
        out = {"samples": 0, "frame_diff": 0, "mask_diff": 0, "rvol_diff": 0, "examples": []}
        if not syms or not self.lab:
            return out
        saved = S._LAB_FRAMES
        try:
            for _ in range(samples):
                sym = syms[int(rng.integers(len(syms)))]
                f = self.frames[sym]
                j = int(rng.integers(min(4, len(f)), len(f) + 1))   # decision bars start at 09:50 (row 4)
                b = self.bars[sym]
                last = pd.Timestamp(self.ends[sym][j - 1], tz="UTC").tz_convert(b.index.tz) - pd.Timedelta(minutes=1)
                tb = b[b.index <= last]
                c = self._ctx(sym)
                ctx = DayContext(symbol=sym, date=c.date, bars=tb, prev_close=c.prev_close, prev_high=c.prev_high,
                                 prev_low=c.prev_low, atr=c.atr, avg_dollar_volume=c.avg_dollar_volume,
                                 avg_cum_volume=c.avg_cum_volume, avg_move=c.avg_move, prior5=c.prior5, sma20=c.sma20,
                                 peers={s: x[x.index <= last] for s, x in self.bars.items()})
                full_rv = self._rvol_full(sym)
                if full_rv is not None and len(tb):
                    a_rv = _ORIG_RVOL(ctx).to_numpy(float)
                    if not np.allclose(a_rv, full_rv.iloc[: len(tb)].to_numpy(float), rtol=1e-12, equal_nan=True):
                        out["rvol_diff"] += 1
                    ctx._cache.pop("rvol", None)
                S._LAB_FRAMES = {}
                st = self.lab[0]
                mod = st.mod
                st.mod = getattr(mod, "_mod", mod)
                try:
                    type(st).generate(st, ctx)
                except Exception:
                    pass
                finally:
                    st.mod = mod
                key = (sym, str(ctx.date), len(tb), tb.index[-1]) if len(tb) else None
                g = S._LAB_FRAMES.get(key) if key else None
                if g is None:
                    continue
                out["samples"] += 1
                pf = f.iloc[: len(g)]
                num = [k for k in g.columns if pd.api.types.is_numeric_dtype(g[k])]
                a, bb = g[num].to_numpy(float), pf[num].to_numpy(float)
                same = a.shape == bb.shape and np.allclose(a, bb, rtol=1e-9, atol=1e-12, equal_nan=True)
                if not same:
                    out["frame_diff"] += 1
                    if len(out["examples"]) < 5:
                        bad = [k for k in num if not np.allclose(g[k].to_numpy(float), pf[k].to_numpy(float),
                                                                 rtol=1e-9, atol=1e-12, equal_nan=True)]
                        out["examples"].append({"symbol": sym, "rows": len(g), "columns": bad[:8]})
                for st2 in self.lab:
                    gg = g
                    if st2.context:
                        from ..strategies.lab_context import add_context

                        gg = add_context(g, ctx.peers, st2.context)
                    try:
                        real = np.asarray(getattr(st2.mod, "_mod", st2.mod).mask(gg), dtype=bool)
                    except Exception:            # the module itself fails on this short frame (live would too)
                        out["mask_errors"] = out.get("mask_errors", 0) + 1
                        continue
                    full = self.full_mask(st2.name, sym)
                    if full is None or not np.array_equal(real, full[: len(real)]):
                        out["mask_diff"] += 1
                        if len(out["examples"]) < 5:
                            out["examples"].append({"symbol": sym, "rows": len(g), "setup": st2.name})
            out["heat_samples"] = out["heat_diff"] = 0
            for st in self.heat:
                for _ in range(max(1, samples // 4)):
                    keys = [k for k, v in self.hscore.items() if k[0] == st.name and v is not None]
                    if not keys:
                        break
                    sym = keys[int(rng.integers(len(keys)))][1]
                    sc, tod, ends = self.hscore[(st.name, sym)]
                    j = int(rng.integers(1, len(sc) + 1))
                    b = self.bars[sym]
                    last = pd.Timestamp(ends[j - 1], tz="UTC").tz_convert(b.index.tz) - pd.Timedelta(minutes=1)
                    c = self._ctx(sym)
                    tb = b[b.index <= last]
                    ctx = DayContext(symbol=sym, date=c.date, bars=tb, prev_close=c.prev_close, prev_high=c.prev_high,
                                     prev_low=c.prev_low, atr=c.atr, avg_dollar_volume=c.avg_dollar_volume,
                                     avg_cum_volume=c.avg_cum_volume, prior5=c.prior5)
                    got = {}
                    real = st.mod

                    class _Cap:
                        def __getattr__(self, a):
                            return getattr(real, a)

                        def score(self, f):
                            got["s"] = np.asarray(real.score(f), dtype=float)
                            return got["s"]

                    st.mod = _Cap()
                    try:
                        type(st).generate(st, ctx)
                    except Exception:
                        pass
                    finally:
                        st.mod = real
                    if "s" in got:
                        out["heat_samples"] += 1
                        if not np.allclose(got["s"], sc[: len(got["s"])], equal_nan=True):
                            out["heat_diff"] += 1
        finally:
            S._LAB_FRAMES = saved
        return out


_ORIG_RVOL = DayContext.rvol
_RVOL: dict = {}      # id(bars prefix) -> (prefix, session rvol, k)
_RVOL_FULL_OK = [False]


def _fast_rvol(self):
    """DayContext.rvol during a fast replay: the session series' first k values when the bars are a registered prefix
    (cumulative volume / average cumulative volume at the same minute is causal), else the real method."""
    if "rvol" not in self._cache:
        e = _RVOL.get(id(self.bars))
        if e is not None and e[0] is self.bars:
            # only lab setups (they never read rvol) and the runner's ranking (rvol at bars 4 and 19, len > 19)
            # read it, so past bar 19 the session series answers identically without a slice
            self._cache["rvol"] = e[1] if (e[2] > 19 and _RVOL_FULL_OK[0]) else e[1].iloc[: e[2]]
        else:
            return _ORIG_RVOL(self)
    return self._cache["rvol"]


_HEAT_MEMO: dict = {}


def _memo_heat_frame(d5):
    """mcf.research.heat.heat_frame memoised on the input bars' content (the lab frame and every heat setup of a
    symbol-session build it from the same warm-up + session bars). Returns a copy: callers add columns."""
    from ..research import heat as H

    try:
        key = (len(d5), d5.index[0].value, d5.index[-1].value, float(d5["close"].to_numpy().sum()),
               float(d5["volume"].to_numpy().sum()), float(d5["high"].to_numpy().sum()))
    except Exception:
        return _REAL_HEAT(d5)
    f = _HEAT_MEMO.get(key)
    if f is None:
        if len(_HEAT_MEMO) > 3000:
            _HEAT_MEMO.clear()
        f = _HEAT_MEMO[key] = _REAL_HEAT(d5)
    return f.copy()


from ..research.heat import heat_frame as _REAL_HEAT  # noqa: E402
