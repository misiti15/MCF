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
           (its own eligible(): 5-minute bar count, window, ADV, ...) or its mask has no hit on the latest decision bar
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
        self.other = [s for s in runner.strategies if not isinstance(s, S.LabStrategy)]
        self.frames: dict[str, pd.DataFrame | None] = {}
        self.ends: dict[str, np.ndarray] = {}
        self.ctx_full: dict[str, DayContext] = {}
        self.masks: dict[tuple[str, str], np.ndarray | None] = {}
        self._pref: dict[tuple[str, int], pd.DataFrame] = {}
        self.mask_hits = self.mask_misses = 0
        self.dropped = self.kept = 0
        self.rv: dict = {}
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
                        st.generate(ctx)
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
        if n < 5 or n % 5:
            return False                                         # every lab setup's eligible() needs n % 5 == 0
        f = self.frame(sym)
        if f is None:
            return any(st.eligible(ctx) for st in self.lab)      # unknown here: let the real code decide
        j = int(np.searchsorted(self.ends[sym], ctx.bars.index[-1].value + 60_000_000_000, side="right"))
        if j == 0:
            return False                                         # no completed 5-minute bar: generate() returns []
        tod = self.tod[sym][j - 1]
        for st in self.lab:
            if getattr(st, "ticker_split", None) and not st.trades_symbol(sym):
                continue
            lo, hi = st.window or (950, 1500)
            if not max(950, lo) <= tod <= min(1500, hi):
                continue
            m = self.full_mask(st.name, sym)
            if m is None or len(m) < j:
                if st.eligible(ctx):
                    return True
                continue
            if m[j - 1] and st.eligible(ctx):                    # a hit on the latest decision bar, and eligible
                return True
        return False

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

        self._saved = (S._LAB_FRAMES, engine.pinned_symbols)
        S._LAB_FRAMES = FrameProvider(self)
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

    def uninstall(self):
        from ..backtest import engine

        S._LAB_FRAMES, engine.pinned_symbols = self._saved
        DayContext.rvol = _ORIG_RVOL
        _RVOL.clear()
        for st in self.lab:
            st.mod = getattr(st.mod, "_mod", st.mod)

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
                j = int(rng.integers(1, len(f) + 1))
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
                    st.generate(ctx)
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
                    real = np.asarray(getattr(st2.mod, "_mod", st2.mod).mask(gg), dtype=bool)
                    full = self.full_mask(st2.name, sym)
                    if full is None or not np.array_equal(real, full[: len(real)]):
                        out["mask_diff"] += 1
                        if len(out["examples"]) < 5:
                            out["examples"].append({"symbol": sym, "rows": len(g), "setup": st2.name})
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
