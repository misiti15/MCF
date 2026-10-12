"""CWT package A engine: 1-minute grids per symbol-day, daily context, 5-min decision bars, exit simulation and costs.

Pre-declared in research/bdi/cwt/TESTPLAN.md (package A + the 2026-10-12 CWT-A amendment) and test_a/NOTES.md.
The rule-19 locked block (2024-11-01..2025-02-28) is dropped right after each symbol's 1-minute load, before any
rolling computation; rolling features are computed per contiguous segment (before / after the block), so nothing
from the block leaks into March 2025 lookbacks. Educational only - not financial advice.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from mcf.research.gates import tod_cost_mult  # noqa: E402

CACHE = ROOT / "data" / "cache_hist" / "1Min"
LOCKED = ("2024-11-01", "2025-02-28")
FIRST = "2024-10-01"
NM = 390                      # minutes 09:30..15:59
NB = 78                       # 5-min bars
LAST = 384                    # 15:54 minute; its close is the 15:55 flat
SLIP_PS, SLIP_BPS, STOP_EXTRA = 0.01, 1e-4, 0.02
ADV_MIN, ADV_CORE, PX_MIN = 1e6, 5e6, 1.0
HOLIDAYS = ["2024-09-02", "2024-11-28", "2024-12-25", "2025-01-01", "2025-01-09", "2025-01-20", "2025-02-17",
            "2025-04-18", "2025-05-26", "2025-06-19", "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25",
            "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19", "2026-07-03",
            "2026-09-07", "2026-11-26", "2026-12-25"]


def hhmm(minute_of_day: int) -> int:
    return (minute_of_day // 60) * 100 + minute_of_day % 60


def bar_tod(k):
    """Bar-close HHMM of 5-min bar k (k = 0 is 09:30-09:35 -> 935)."""
    m = 570 + 5 * (np.asarray(k) + 1)
    return (m // 60) * 100 + m % 60


def kidx(tod: int) -> int:
    """5-min bar index whose close is HHMM tod."""
    return ((tod // 100) * 60 + tod % 100 - 570) // 5 - 1


def minute_tod(m) -> np.ndarray:
    """HHMM of the start of minute index m (0 = 09:30)."""
    t = 570 + np.asarray(m)
    return (t // 60) * 100 + t % 60


def _seg_shift(a: np.ndarray, seg: np.ndarray, k: int = 1) -> np.ndarray:
    out = np.full(a.shape, np.nan)
    if len(a) > k:
        out[k:] = a[:-k]
        same = np.zeros(len(a), bool)
        same[k:] = seg[k:] == seg[:-k]
        out[~same] = np.nan
    return out


def _seg_roll_mean(a: np.ndarray, seg: np.ndarray, w: int, minp: int) -> np.ndarray:
    s = pd.Series(a)
    return s.groupby(seg).transform(lambda x: x.rolling(w, min_periods=minp).mean()).to_numpy()


def _ffill_rows(a: np.ndarray) -> np.ndarray:
    ok = ~np.isnan(a)
    ix = np.where(ok, np.arange(a.shape[1])[None, :], 0)
    np.maximum.accumulate(ix, axis=1, out=ix)
    out = a[np.arange(a.shape[0])[:, None], ix]
    out[~np.logical_or.accumulate(ok, axis=1)] = np.nan
    return out


def _seg_roll_mean2d(a: np.ndarray, seg: np.ndarray, w: int, minp: int) -> np.ndarray:
    """Rolling mean over rows (days) within each segment, window w, min_periods minp."""
    out = np.full(a.shape, np.nan)
    for sg in np.unique(seg):
        ix = np.flatnonzero(seg == sg)
        x = a[ix]
        cs = np.vstack([np.zeros((1, x.shape[1])), np.cumsum(x, 0)])
        n = np.arange(1, len(x) + 1)
        lo = np.maximum(0, n - w)
        cnt = n - lo
        m = (cs[n] - cs[lo]) / cnt[:, None]
        m[cnt < minp] = np.nan
        out[ix] = m
    return out


class Sym:
    """All arrays for one symbol. Days exclude the locked block and anything before 2024-09-16."""

    def __init__(self, sym: str):
        self.sym = sym
        df = pd.read_parquet(CACHE / f"{sym}.parquet")
        idx = df.index
        if idx.tz is None:
            idx = idx.tz_localize("UTC").tz_convert("America/New_York")
        else:
            idx = idx.tz_convert("America/New_York")
        loc = idx.tz_localize(None).values
        ds = np.datetime_as_string(loc.astype("datetime64[D]"), unit="D")
        keep = (ds < LOCKED[0]) | (ds > LOCKED[1])          # locked rows dropped right after the load
        mins = idx.hour * 60 + idx.minute - 570
        keep &= (mins >= 0) & (mins < NM)
        df, ds, mins = df[keep], ds[keep], np.asarray(mins)[keep]
        self.dates, di = np.unique(ds, return_inverse=True)
        D = len(self.dates)
        self.D = D
        g = {}
        for c in ("open", "high", "low", "close", "volume"):
            a = np.full((D, NM), np.nan)
            a[di, mins] = df[c].to_numpy(float)
            g[c] = a
        V = np.nan_to_num(g["volume"])
        C = _ffill_rows(g["close"])                                  # ffill within the day
        miss = np.isnan(g["close"])
        O, H, L = g["open"].copy(), g["high"].copy(), g["low"].copy()
        O[miss], H[miss], L[miss] = C[miss], C[miss], C[miss]
        self.O, self.H, self.L, self.C, self.V = O, H, L, C, V
        # ---- daily table
        first = np.argmax(~np.isnan(O), axis=1)
        self.open_d = O[np.arange(D), first]
        self.hi = np.nanmax(H, 1)
        self.lo = np.nanmin(L, 1)
        self.cl = C[:, -1]
        self.vol = V.sum(1)
        dv = np.nansum(np.nan_to_num(C) * V, 1)
        self.seg = (self.dates > LOCKED[1]).astype(int)
        seg = self.seg
        sh = lambda a, k=1: _seg_shift(a, seg, k)
        self.pc = sh(self.cl)
        self.pdh, self.pdl = sh(self.hi), sh(self.lo)
        tr = np.nanmax(np.vstack([self.hi - self.lo, np.abs(self.hi - self.pc), np.abs(self.lo - self.pc)]), 0)
        tr[np.isnan(self.pc)] = (self.hi - self.lo)[np.isnan(self.pc)]
        self.atr = sh(_seg_roll_mean(tr, seg, 14, 10))
        self.adv20 = sh(_seg_roll_mean(dv, seg, 20, 5))
        self.gap = (self.open_d / self.pc - 1) * 100
        c1, c2, c3, c4, c6 = sh(self.cl, 1), sh(self.cl, 2), sh(self.cl, 3), sh(self.cl, 4), sh(self.cl, 6)
        self.run3 = (c1 / c4 - 1) * 100
        self.run5 = (c1 / c6 - 1) * 100
        up = (self.cl > self.pc).astype(float)
        up[np.isnan(self.pc)] = 0
        streak = np.zeros(D)
        for i in range(D):
            streak[i] = (streak[i - 1] + 1) if (i and up[i] and seg[i] == seg[i - 1]) else (1.0 if up[i] else 0.0)
        self.upstreak = sh(streak)                                  # consecutive up closes ending yesterday
        vm20 = _seg_roll_mean(self.vol, seg, 20, 5)
        rvol_d = self.vol / sh(vm20)                                 # day volume / prior 20-day mean
        self.d1_gap = sh(self.gap)
        self.d1_rvol = sh(rvol_d)
        self.d1_ret = (c1 / c2 - 1) * 100
        self.d2_ret = (c2 / c3 - 1) * 100                           # return of day t-2 (day-3 play's day 1)
        self.d2_rvol = sh(rvol_d, 2)
        self.h2, self.l2 = sh(self.hi, 2), sh(self.lo, 2)
        hi5 = pd.Series(self.hi).groupby(seg).transform(lambda x: x.rolling(5, min_periods=5).max()).to_numpy()
        lo5 = pd.Series(self.lo).groupby(seg).transform(lambda x: x.rolling(5, min_periods=5).min()).to_numpy()
        self.hi5, self.lo5 = sh(hi5), sh(lo5)
        # ---- cumulative-volume rvol by minute (prior 20 sessions, min 5, per segment)
        CV = np.cumsum(V, 1)
        base = _seg_roll_mean2d(CV, seg, 20, 5)
        base = np.vstack([np.full((1, NM), np.nan), base[:-1]])
        base[1:][seg[1:] != seg[:-1]] = np.nan
        with np.errstate(divide="ignore", invalid="ignore"):
            self.rvol_m = CV / base                                   # rvol_tod at the end of minute m
        # ---- 5-min bars
        H5 = H.reshape(D, NB, 5)
        L5 = L.reshape(D, NB, 5)
        self.h5 = np.nanmax(H5, 2) if True else None
        self.l5 = np.nanmin(L5, 2)
        self.c5 = C[:, 4::5]
        self.o5 = O[:, 0::5]
        self.v5 = V.reshape(D, NB, 5).sum(2)
        typ = (self.h5 + self.l5 + self.c5) / 3
        cv5 = np.cumsum(self.v5, 1)
        with np.errstate(divide="ignore", invalid="ignore"):
            self.vw5 = np.cumsum(np.nan_to_num(typ) * self.v5, 1) / np.where(cv5 > 0, cv5, np.nan)
        self.hod5 = np.fmax.accumulate(self.h5, 1)
        self.lod5 = np.fmin.accumulate(self.l5, 1)
        kk = np.broadcast_to(np.arange(NB), (D, NB))
        self.hodk = np.maximum.accumulate(np.where(self.h5 >= self.hod5, kk, -1), 1)
        self.lodk = np.maximum.accumulate(np.where(self.l5 <= self.lod5, kk, -1), 1)
        self.rv5 = self.rvol_m[:, 4::5]
        # ---- universe and cost tier
        self.ok = (np.isfinite(self.pc) & np.isfinite(self.atr) & (self.atr > 0) & (self.adv20 >= ADV_MIN)
                   & (self.open_d >= PX_MIN) & (self.dates >= FIRST))
        self.ext = np.where((np.abs(self.gap) >= 20) | (self.open_d < 5) | (self.adv20 < ADV_CORE), 3.0, 1.0)
        dd = pd.to_datetime(self.dates)
        self.dnum = dd.values.astype("datetime64[D]")

    # ------------------------------------------------------------------ helpers
    def next_day(self, d: int, k: int = 1, max_cal: int = 7 * 1):
        j = d + k
        if j >= self.D or self.seg[j] != self.seg[d]:
            return None
        n_bd = np.busday_count(self.dnum[d], self.dnum[j], holidays=HOLIDAYS)
        return j if n_bd == k else None


# ---------------------------------------------------------------------------------------------- simulation
def sim(s: Sym, d: int, m0: int, side: int, stop: float, tgt: float, last: int = LAST):
    """From minute m0 (entry at its open) through minute `last`: stop-first inside a minute, a gap through the stop
    fills at the minute's open (not on the entry minute), the target is a limit filled at its price. Returns
    (exit price, kind 1 stop / 2 target / 3 time, exit minute)."""
    if m0 > last:
        return np.nan, 0, m0
    Hs, Ls, Os = s.H[d, m0:last + 1], s.L[d, m0:last + 1], s.O[d, m0:last + 1]
    n = len(Hs)
    if np.isfinite(stop):
        hs = (Ls <= stop) if side > 0 else (Hs >= stop)
        i_s = int(np.argmax(hs)) if hs.any() else n
    else:
        i_s = n
    if np.isfinite(tgt):
        ht = (Hs >= tgt) if side > 0 else (Ls <= tgt)
        i_t = int(np.argmax(ht)) if ht.any() else n
    else:
        i_t = n
    if i_s < n and i_s <= i_t:
        px = stop
        if i_s > 0 and ((side > 0 and Os[i_s] < stop) or (side < 0 and Os[i_s] > stop)):
            px = Os[i_s]
        return px, 1, m0 + i_s
    if i_t < n:
        return tgt, 2, m0 + i_t
    return s.C[d, last], 3, last


def cost_r(s: Sym, d: int, e: float, legs, m_entry: int, R: float, entry_mult: float | None = None) -> float:
    """Production cost in R: entry (1c + 1 bps) x TOD multiplier x tier; each non-target exit leg (weight w) pays
    (1c + 1 bps) x TOD multiplier (exits before 10:30) x tier, +2c x tier on stops. legs: [(w, px, kind, minute)]."""
    ext = s.ext[d]
    em = float(tod_cost_mult(minute_tod(m_entry))) if entry_mult is None else entry_mult
    c = (SLIP_PS + e * SLIP_BPS) * em * ext
    for w, px, kind, m in legs:
        if kind == 2:
            continue
        xm = float(tod_cost_mult(minute_tod(min(m + 1, NM - 1)))) if m < NM else 1.0
        c += w * ((SLIP_PS + px * SLIP_BPS) * xm * ext + (STOP_EXTRA * ext if kind == 1 else 0.0))
    return c / R


def r_of(s: Sym, d: int, side: int, e: float, legs, m_entry: int, entry_mult=None) -> float:
    R = 0.25 * s.atr[d]
    gross = sum(w * side * (px - e) for w, px, _, _ in legs) / R
    return gross - cost_r(s, d, e, legs, m_entry, R, entry_mult)


GEOMK = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5)}


def exit_geom(s, d, m0, side, e, geom):
    up, dn = GEOMK[geom]
    R = 0.25 * s.atr[d]
    px, kind, m = sim(s, d, m0, side, e - side * dn * R, e + side * up * R)
    return r_of(s, d, side, e, [(1.0, px, kind, m)], m0)


def stop_ok(side: int, e: float, stop: float) -> bool:
    """A structural stop must sit beyond the entry: side * (entry - stop) > 0, and finite. Same guard as the live
    LabStrategy structural branch (mcf/strategies/setups.py). Fix 2026-10-12 (RECHECK_1012.md): before it, a short
    entered at or above its stop was 'stopped' on the entry minute at the stop price - below the entry - and booked
    as a gain (mirror for longs). Such entries are now skipped (NaN -> not emitted)."""
    return bool(np.isfinite(stop) and side * (e - stop) > 0)


def exit_struct(s, d, m0, side, e, stop, tgt=np.nan, last=LAST):
    if not stop_ok(side, e, stop):
        return np.nan
    px, kind, m = sim(s, d, m0, side, stop, tgt, last)
    return r_of(s, d, side, e, [(1.0, px, kind, m)], m0)


def exit_overnight(s, d, m0, side, e, stop):
    """Hold through the close (stop active to 16:00) to the next session's 09:35 (stop active, gap fills at open)."""
    if not stop_ok(side, e, stop):
        return np.nan
    px, kind, m = sim(s, d, m0, side, stop, np.nan, NM - 1)
    if kind == 1:
        return r_of(s, d, side, e, [(1.0, px, kind, m)], m0)
    j = s.next_day(d)
    if j is None:
        return np.nan
    o = s.O[j, 0]
    if np.isfinite(stop) and ((side > 0 and o <= stop) or (side < 0 and o >= stop)):
        legs = [(1.0, o, 1, 0)]
    else:
        px2, k2, m2 = sim(s, j, 0, side, stop, np.nan, 4)
        legs = [(1.0, px2, k2, m2)]
    R = 0.25 * s.atr[d]
    gross = side * (legs[0][1] - e) / R
    w, px2, k2, m2 = legs[0]
    em = float(tod_cost_mult(minute_tod(m0)))
    xm = float(tod_cost_mult(minute_tod(min(m2 + 1, NM - 1))))
    c = (SLIP_PS + e * SLIP_BPS) * em * s.ext[d] + (SLIP_PS + px2 * SLIP_BPS) * xm * s.ext[d] + (STOP_EXTRA * s.ext[d] if k2 == 1 else 0)
    return gross - c / R


def exit_hold_days(s, d, m0, side, e, stop, ndays=2):
    """S2: stop active intraday on day 0 and the next `ndays` sessions (gap through it fills at the open); else the
    close of day +ndays."""
    if not stop_ok(side, e, stop):
        return np.nan
    px, kind, m = sim(s, d, m0, side, stop, np.nan, NM - 1)
    R = 0.25 * s.atr[d]
    if kind == 1:
        return r_of(s, d, side, e, [(1.0, px, kind, m)], m0)
    for k in range(1, ndays + 1):
        j = s.next_day(d, k)
        if j is None:
            return np.nan
        o = s.O[j, 0]
        if (side > 0 and o <= stop) or (side < 0 and o >= stop):
            px, kind, mm = o, 1, 0
        else:
            px, kind, mm = sim(s, j, 0, side, stop, np.nan, NM - 1)
        if kind == 1 or k == ndays:
            em = float(tod_cost_mult(minute_tod(m0)))
            xm = float(tod_cost_mult(minute_tod(min(mm + 1, NM - 1)))) if kind == 1 else 1.0
            c = (SLIP_PS + e * SLIP_BPS) * em * s.ext[d] + (SLIP_PS + px * SLIP_BPS) * xm * s.ext[d] + (STOP_EXTRA * s.ext[d] if kind == 1 else 0)
            return side * (px - e) / R - c / R
    return np.nan


def exit_half_2r(s, d, m0, side, e, stop):
    """A3 S: half at +2 x structural risk (limit), rest with the stop moved to entry, else 15:55."""
    if not stop_ok(side, e, stop):
        return np.nan
    rs = abs(e - stop)
    tgt = e + side * 2 * rs
    px, kind, m = sim(s, d, m0, side, stop, tgt)
    if kind != 2:
        return r_of(s, d, side, e, [(1.0, px, kind, m)], m0)
    px2, k2, m2 = sim(s, d, m + 1, side, e, np.nan) if m + 1 <= LAST else (s.C[d, LAST], 3, LAST)
    return r_of(s, d, side, e, [(0.5, tgt, 2, m), (0.5, px2, k2, m2)], m0)


# ---------------------------------------------------------------------------------------------- controls
CTL_K = np.arange(0, 66)            # entry minutes 5k+5: 09:35 .. 15:00
CTL_EXITS = ("t1s1", "t05s1", "t1s05", "time")


def control_outcomes(s: Sym, d: int) -> np.ndarray:
    """(66 entry bars, 2 sides [long, short], 4 exits) production-cost R for entries at the open of minute 5k+5."""
    out = np.full((len(CTL_K), 2, 4), np.nan)
    R = 0.25 * s.atr[d]
    m0s = 5 * CTL_K + 5
    e = s.O[d, m0s]
    Hm, Lm = s.H[d, :LAST + 1], s.L[d, :LAST + 1]
    mi = np.arange(LAST + 1)
    after = mi[None, :] >= m0s[:, None]
    ext = s.ext[d]
    em = tod_cost_mult(minute_tod(m0s))
    cin = (SLIP_PS + e * SLIP_BPS) * em * ext
    big = LAST + 10
    for si, side in enumerate((1, -1)):
        for xi, ex in enumerate(CTL_EXITS):
            if ex == "time":
                px = np.full(len(m0s), s.C[d, LAST])
                kind = np.full(len(m0s), 3)
                mx = np.full(len(m0s), LAST)
            else:
                up, dn = GEOMK[ex]
                st, tg = e - side * dn * R, e + side * up * R
                hs = ((Lm[None, :] <= st[:, None]) if side > 0 else (Hm[None, :] >= st[:, None])) & after
                ht = ((Hm[None, :] >= tg[:, None]) if side > 0 else (Lm[None, :] <= tg[:, None])) & after
                fs = np.where(hs.any(1), np.argmax(hs, 1), big)
                ft = np.where(ht.any(1), np.argmax(ht, 1), big)
                stop_first = (fs <= ft) & (fs < big)
                tgt_first = (~stop_first) & (ft < big)
                fsc = np.minimum(fs, LAST)
                gap_px = s.O[d, fsc]
                gapped = (fs > m0s) & (((side > 0) & (gap_px < st)) | ((side < 0) & (gap_px > st)))
                px = np.where(stop_first, np.where(gapped, gap_px, st), np.where(tgt_first, tg, s.C[d, LAST]))
                kind = np.where(stop_first, 1, np.where(tgt_first, 2, 3))
                mx = np.where(stop_first, fs, np.where(tgt_first, ft, LAST))
            xm = tod_cost_mult(minute_tod(np.minimum(mx + 1, NM - 1)))
            cout = np.where(kind == 2, 0.0, (SLIP_PS + px * SLIP_BPS) * xm * ext) + np.where(kind == 1, STOP_EXTRA * ext, 0.0)
            out[:, si, xi] = side * (px - e) / R - (cin + cout) / R
    return out
