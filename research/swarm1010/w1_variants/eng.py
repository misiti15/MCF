"""W1 engine: memory-mapped open two-year lab rows (base.npz + data/ext + reddit extra.npz), lazy float32 columns with a
byte-budget cache, first-qualifying-bar trades and the probation statistics (vectorised; checked against
mcf.research.gates on sample lists). Educational only - not financial advice."""
from __future__ import annotations

import sys
from collections import OrderedDict
from pathlib import Path

import numba
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "history2y"), str(HERE)]
import lib  # noqa: E402
from npzmap import npz_memmap  # noqa: E402

SDIR = ROOT / "research" / "bdi" / "stack1009" / "data"
EXT = HERE / "data" / "ext"
RDX = ROOT / "research" / "bdi" / "reddit" / "data" / "extra.npz"
BUCKETS = {"B1": (950, 1030), "B2": (1035, 1130), "B3": (1135, 1300), "B4": (1305, 1400), "B5": (1405, 1500)}
CACHE_BYTES = 1.3e9


@numba.njit(cache=True)
def _first_per_sd(idx, sd):
    keep = np.zeros(len(idx), np.bool_)
    last = -1
    for j in range(len(idx)):
        s = sd[idx[j]]
        if s != last:
            keep[j] = True
            last = s
    return keep


@numba.njit(cache=True)
def _seg_cum(x, new, ismax):
    out = np.empty_like(x)
    cur = x[0]
    for i in range(len(x)):
        if new[i]:
            cur = x[i]
        elif ismax:
            cur = max(cur, x[i])
        else:
            cur = min(cur, x[i])
        out[i] = cur
    return out


@numba.njit(cache=True)
def _seg_cumsum(x, new):
    out = np.empty_like(x)
    cur = 0.0
    for i in range(len(x)):
        if new[i]:
            cur = 0.0
        if not np.isnan(x[i]):
            cur += x[i]
        out[i] = cur
    return out


@numba.njit(cache=True)
def _seg_ffill(x, new):
    out = np.empty_like(x)
    cur = np.nan
    for i in range(len(x)):
        if new[i]:
            cur = np.nan
        if not np.isnan(x[i]):
            cur = x[i]
        out[i] = cur
    return out


@numba.njit(cache=True)
def _band_block(zsd, new, k):
    """RW6G1 guard on rows: blocked while close > VWAP and a close > VWAP + k SD happened since the last close at or
    below VWAP (same symbol-day). NaN zsd (no volume) -> treated as not beyond (rows are 09:50+ only)."""
    out = np.zeros(len(zsd), np.bool_)
    flag = False
    for i in range(len(zsd)):
        if new[i]:
            flag = False
        z = zsd[i]
        beyond = z > 0
        if not beyond:
            flag = False
        else:
            if z > k:
                flag = True
            out[i] = flag
    return out


class D:
    """Data adapter (also serves the Reddit builders: c, atr, tod, h, l, hod, lod, open_d, pdc, chg, vwap, sma20,
    spy_z, spy_fo_atr, fo_atr, F, prev, grp_*, ffill, new, B)."""

    def __init__(self):
        self.B = npz_memmap(SDIR / "base.npz")
        self.E = {p.stem: np.load(p, mmap_mode="r") for p in EXT.glob("*.npy")}
        self.N = len(self.B["close"])
        self.dates = pd.read_csv(SDIR / "dates.csv").iloc[:, 0].astype(str).tolist()
        self.symbols = pd.read_csv(SDIR / "symbols.csv").iloc[:, 0].astype(str).tolist()
        self.nd = len(self.dates)
        self.reg = lib.regimes()
        reg = self.reg.reindex(pd.to_datetime(self.dates).date)["regime"].to_numpy()
        self.regc = np.select([reg == "up", reg == "down"], [1, -1], 0).astype(np.int8)
        per = pd.PeriodIndex(pd.to_datetime(self.dates), freq="M")
        self.months = sorted(set(per))
        self.mon = np.array([self.months.index(p) for p in per], np.int32)
        sd = self.B["sd"]
        self.sd = sd
        self.new = np.r_[True, np.asarray(sd[1:]) != np.asarray(sd[:-1])]
        self.day = np.asarray(self.B["day"])
        self.tod = np.asarray(self.B["tod"])
        self._c: OrderedDict[str, np.ndarray] = OrderedDict()
        self._rdx = None
        self.adv_ok = {}

    # ------------------------------------------------------------------ columns
    def _put(self, k, v):
        self._c[k] = v
        self._c.move_to_end(k)
        while sum(a.nbytes for a in self._c.values()) > CACHE_BYTES and len(self._c) > 1:
            self._c.popitem(last=False)
        return v

    def F(self, k):
        if k in self._c:
            self._c.move_to_end(k)
            return self._c[k]
        if k in self.B:
            v = np.asarray(self.B[k], dtype=np.float32)
        elif k in self.E:
            v = np.asarray(self.E[k], dtype=np.float32)
        elif k in ("bull_div", "bear_div", "hi_atr", "lo_atr", "upper_wick", "lower_wick"):
            if self._rdx is None:
                self._rdx = np.load(RDX)
            v = np.asarray(self._rdx[k], dtype=np.float32)
        elif k in DERIVED:
            v = DERIVED[k](self).astype(np.float32)
        else:
            raise KeyError(k)
        return self._put(k, v)

    def clear(self):
        self._c.clear()

    def __getattr__(self, k):
        if k.startswith("_") or k not in DERIVED_ATTR:
            raise AttributeError(k)
        return self.F(DERIVED_ATTR[k])

    # ------------------------------------------------------------------ helpers
    def prev(self, x, k=1):
        x = np.asarray(x)
        if k == 0:
            return x.astype(np.float32, copy=True)
        p = np.empty(len(x), np.float32)
        p[:k] = np.nan
        p[k:] = x[:-k]
        if k == 1:
            p[self.new] = np.nan
        else:
            sd = self.sd
            bad = np.r_[np.ones(k, bool), np.asarray(sd[k:]) != np.asarray(sd[:-k])]
            p[bad] = np.nan
        return p

    def grp_cummax(self, x):
        return _seg_cum(np.nan_to_num(np.asarray(x, np.float32), nan=-np.inf), self.new, True)

    def grp_cummin(self, x):
        return _seg_cum(np.nan_to_num(np.asarray(x, np.float32), nan=np.inf), self.new, False)

    def grp_cumsum(self, x):
        return _seg_cumsum(np.asarray(x, np.float32), self.new)

    def ffill(self, x):
        return _seg_ffill(np.asarray(x, np.float32), self.new)

    def adv(self, min_adv):
        if min_adv not in self.adv_ok:
            self.adv_ok[min_adv] = np.asarray(self.B["adv20"]) >= min_adv
        return self.adv_ok[min_adv]

    def outcome(self, side, geom):
        k = f"p_{side}_{geom}"
        return self.B[k] if k in self.B else self.E[k]

    # ------------------------------------------------------------------ trades and stats
    def trades(self, mask, side, geom, min_adv=95e6):
        m = np.asarray(mask, bool)
        if min_adv > 95e6:
            m = m & self.adv(min_adv)
        idx = np.flatnonzero(m)
        if not len(idx):
            return idx, np.zeros(0)
        idx = idx[_first_per_sd(idx, self.sd)]
        r = np.asarray(self.outcome(side, geom)[idx], np.float64)
        ok = np.isfinite(r)
        return idx[ok], r[ok]

    def stats(self, idx, r):
        return stats(r, self.day[idx], self.nd, self.regc, self.mon, self.months)


def _t(S, C, n, mu):
    se = np.sqrt(((S - C * mu) ** 2).sum()) / n
    return float(mu / se) if se > 0 else 0.0


def stats(r, day, nd, regc, mon, months):
    n = len(r)
    out = {"n": n, "per_day": round(n / nd, 3)}
    if n < 2:
        return out | {"exp": np.nan, "t": 0.0, "robust": -99.0}
    S = np.bincount(day, weights=r, minlength=nd)
    C = np.bincount(day, minlength=nd)
    mu = float(r.mean())
    out.update(exp=mu, win=float((r > 0).mean()), t=_t(S, C, n, mu))
    for nm, v in (("up", 1), ("flat", 0), ("down", -1)):
        mm = regc == v
        nn = int(C[mm].sum())
        out[f"n_{nm}"] = nn
        if nn >= 2:
            m2 = float(S[mm].sum() / nn)
            out[f"exp_{nm}"] = m2
            out[f"t_{nm}"] = _t(S[mm], C[mm], nn, m2)
        else:
            out[f"exp_{nm}"], out[f"t_{nm}"] = np.nan, 0.0
    ok = out["n_up"] >= 30 and out["n_down"] >= 30
    out["robust"] = min(out["t_up"], out["t_down"]) if ok else -99.0
    out["both_pos"] = bool(ok and out["exp_up"] > 0 and out["exp_down"] > 0)
    out["spread"] = out["exp_up"] - out["exp_down"] if ok else np.nan
    b = int(np.argmax(S))
    out["ex_best_day"] = float((S.sum() - S[b]) / max(1, n - C[b]))
    out["maxday"] = float(C.max() / n)
    # walk-forward (gates.walk_forward: 3 consecutive train months + next month test, locked months excluded)
    MS = np.bincount(mon, weights=S, minlength=len(months))
    MC = np.bincount(mon, weights=C, minlength=len(months))
    pos, tot = 0, 0
    for i in range(len(months) - 3):
        w = months[i:i + 4]
        if any((b2 - a2).n != 1 for a2, b2 in zip(w, w[1:])):
            continue
        if MC[i + 3] >= 10:
            tot += 1
            pos += MS[i + 3] / MC[i + 3] > 0
    out["wf"] = round(pos / tot, 3) if tot else np.nan
    out["wf_folds"] = tot
    return out


def probation(s, plateau=None):
    """The RULES.md live-probation bar (plateau checked separately when None)."""
    ok = (s.get("n", 0) >= 150 and s.get("both_pos", False) and s.get("t", 0) >= 2.0 and (s.get("wf") or 0) >= 0.6
          and s.get("ex_best_day", -1) > 0 and s.get("maxday", 1) <= 0.10)
    if plateau is not None:
        ok = ok and plateau > 0
    return bool(ok)


# ---------------------------------------------------------------------- derived columns (float32, cached)
def _c(D):
    return D.F("close")


DERIVED = {
    "_atr": lambda D: D.F("atr_d"),
    "_h": lambda D: D.F("close") + D.F("hi_atr") * D.F("atr_d"),
    "_l": lambda D: D.F("close") - D.F("lo_atr") * D.F("atr_d"),
    "_hod": lambda D: D.F("close") + D.F("dist_hod_atr") * D.F("atr_d"),
    "_lod": lambda D: D.F("close") - D.F("dist_lod_atr") * D.F("atr_d"),
    "_open_d": lambda D: D.F("close") / (1 + D.F("fromOpen") / 100),
    "_pdc": lambda D: D.F("_open_d") / (1 + D.F("gap") / 100),
    "_chg": lambda D: (D.F("close") / D.F("_pdc") - 1) * 100,
    "_vwap": lambda D: D.F("close") / (1 + D.F("vwapDistPct") / 100),
    "_sma20": lambda D: D.F("close") / (1 + D.F("sma20_dist_pct") / 100),
    "_fo_atr": lambda D: (D.F("close") - D.F("_open_d")) / D.F("atr_d"),
    "_spy_z": lambda D: _spy(D, "z"),
    "_spy_fo_atr": lambda D: _spy(D, "_fo_atr"),
}
DERIVED_ATTR = {"c": "close", "atr": "atr_d", "h": "_h", "l": "_l", "hod": "_hod", "lod": "_lod", "open_d": "_open_d",
                "pdc": "_pdc", "chg": "_chg", "vwap": "_vwap", "sma20": "_sma20", "fo_atr": "_fo_atr",
                "spy_z": "_spy_z", "spy_fo_atr": "_spy_fo_atr"}


def _spy(D, k):
    spy = D.symbols.index("SPY")
    m = np.asarray(D.B["sym"]) == spy
    key = D.day.astype(np.int64) * 10000 + D.tod.astype(np.int64)
    s = pd.Series(D.F(k)[m].astype(np.float64), index=key[m])
    return s.reindex(key).to_numpy()
