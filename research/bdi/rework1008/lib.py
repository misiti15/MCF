"""Shared helpers for the 2026-10-08 BDI rework round (train/valid lab frame only).
Educational only - not financial advice."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mcf.research.setup_lab import load

GEOMS = ["t1s1", "t05s1", "t1s05"]
SIDES = ["long", "short"]
OUTS = [(s, g) for s in SIDES for g in GEOMS]
BASE = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "rsi", "rsi5", "sma20_dist_pct", "sma50_dist_pct",
        "vwapDistPct", "volumeRatio", "fromOpen", "gap", "heat", "buyPressure", "dist_hod_atr", "dist_lod_atr",
        "bear_div", "bull_div", "upper_wick", "lower_wick"]
RCOLS = [f"r_{s}_{g}" for s, g in OUTS]


class Split:
    """One split, sorted by symbol-day-tod, with per-row helpers. Nothing after 2026-09-15 is ever loaded."""

    def __init__(self, name: str, extra: list[str] | None = None):
        df = load(name, columns=list(dict.fromkeys(BASE + (extra or []) + RCOLS)))
        assert str(df["date"].max()) < "2026-09-16"
        df = df.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
        self.name, self.df, self.n = name, df, len(df)
        key = df.symbol.astype(str).to_numpy() + "|" + df.date.astype(str).to_numpy()
        self.sid = pd.factorize(key)[0]
        self.first = np.r_[True, self.sid[1:] != self.sid[:-1]]
        self.dcode, self.dates = pd.factorize(df.date.astype(str).to_numpy(), sort=True)
        self.ndays = len(self.dates)
        self.half = self.dcode >= (self.ndays // 2)          # train halves by calendar
        self.tod = df.tod.to_numpy()
        self.close = df.close.to_numpy(dtype=float)
        self.atr = df.atr_d.to_numpy(dtype=float)
        R = 0.25 * self.atr
        self.hair = (2 * self.close * 1e-4 + 0.02) / R
        self.r = {(s, g): df[f"r_{s}_{g}"].to_numpy(dtype=float) - self.hair for s, g in OUTS}
        self.sym = df.symbol.astype(str).to_numpy()

    def col(self, k):
        return self.df[k].to_numpy(dtype=float)

    def prev(self, x):
        p = np.r_[np.nan, x[:-1]]
        p[self.first] = np.nan
        return p

    def first_per_day(self, idx):
        """idx sorted ascending -> keep the first index of each symbol-day."""
        if len(idx) == 0:
            return idx
        s = self.sid[idx]
        return idx[np.r_[True, s[1:] != s[:-1]]]

    def win(self, lo, hi):
        return (self.tod >= lo) & (self.tod <= hi)


def stats(sp: Split, idx: np.ndarray, side: str, geom: str) -> dict | None:
    """idx: entry rows (already first-per-day). Returns metrics after the production haircut."""
    r = sp.r[(side, geom)][idx]
    ok = np.isfinite(r)
    idx, r = idx[ok], r[ok]
    n = len(r)
    if n < 2:
        return None
    d = sp.dcode[idx]
    S = np.bincount(d, weights=r, minlength=sp.ndays)
    C = np.bincount(d, minlength=sp.ndays)
    mu = r.mean()
    se = np.sqrt(((S - C * mu) ** 2).sum()) / n
    act = C > 0
    best = np.argmax(np.where(act, S, -np.inf))
    exb = (r.sum() - S[best]) / max(1, n - C[best])
    h = sp.half[idx]
    return {"n": n, "exp": mu, "t": mu / se if se > 0 else 0.0, "green": float((S[act] > 0).mean()),
            "h1": r[~h].mean() if (~h).any() else np.nan, "h2": r[h].mean() if h.any() else np.nan,
            "exbest": exb, "tpd": n / sp.ndays, "win": float((r > 0).mean())}


def baseline(sp: Split, side, geom, lo, hi) -> float:
    r = sp.r[(side, geom)][sp.win(lo, hi)]
    return float(np.nanmean(r))


def same_time_ctrl(sp: Split, idx, side, geom) -> float:
    r = sp.r[(side, geom)]
    ok = np.isfinite(r)
    t = pd.Series(r[ok]).groupby(sp.tod[ok]).mean()
    rr = r[idx]
    m = np.isfinite(rr)
    return float(np.mean(rr[m] - t.reindex(sp.tod[idx][m]).to_numpy()))


def exit_bar(sp: Split, idx: np.ndarray, side: str, geom: str) -> np.ndarray:
    """For entries idx (first per symbol-day), the row where the trade exits inside the frame (stop checked first,
    target/stop touched by a LATER bar's high/low, as the lab), or -1 if it is still open at the last frame bar
    (15:00) - then no re-entry/reverse is possible. Also returns whether the exit was a stop."""
    up, dn = {"t1s1": (1, 1), "t05s1": (0.5, 1), "t1s05": (1, 0.5)}[geom]
    sgn = 1 if side == "long" else -1
    hi, lo = sp.col("high"), sp.col("low")
    out = np.full(len(idx), -1)
    stop = np.zeros(len(idx), bool)
    # walk forward bar by bar (vectorised over trades); at most 63 bars in a frame day
    px = sp.close[idx]
    R = 0.25 * sp.atr[idx]
    tgt, stp = px + sgn * up * R, px - sgn * dn * R
    cur = idx.copy()
    alive = np.ones(len(idx), bool)
    for _ in range(80):
        cur = cur + 1
        valid = alive & (cur < sp.n)
        valid[valid] &= sp.sid[cur[valid]] == sp.sid[idx[valid]]
        alive &= valid
        if not alive.any():
            break
        c = np.where(alive, cur, 0)
        if sgn == 1:
            hs, ht = lo[c] <= stp, hi[c] >= tgt
        else:
            hs, ht = hi[c] >= stp, lo[c] <= tgt
        hs &= alive
        ht &= alive & ~hs
        done = hs | ht
        out[done] = c[done]
        stop[hs] = True
        alive &= ~done
    return out, stop
