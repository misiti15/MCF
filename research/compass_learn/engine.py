"""COMPASS-LEARN engine: compass readings from the 5-min panel (panel.py), all as [days x marks] matrices.
A reading is computed at the config's update marks from bars that START before the mark (closed by it) and is held
until the next update. Side codes: +1 confirmed up, -1 confirmed down, 0 not confirmed. Educational only."""
from __future__ import annotations

import numpy as np
import pandas as pd

MARKS = np.arange(575, 956, 5)
G = np.arange(600, 931, 15)                       # common scoring grid 10:00..15:30
CPS = [585] + list(range(600, 931, 30))
mi = lambda T: (np.asarray(T) - 575) // 5


def lab(T):
    return f"{T // 60:02d}:{T % 60:02d}"


class Panel:
    def __init__(self, P: pd.DataFrame, hunch: pd.DataFrame | None = None):
        P = P.sort_values(["date", "T"])
        self.dates = np.array(sorted(P.date.unique()))
        nd, nm = len(self.dates), len(MARKS)
        full = pd.MultiIndex.from_product([self.dates, MARKS], names=["date", "T"])
        P = P.set_index(["date", "T"]).reindex(full)
        self.m = {c: P[c].values.reshape(nd, nm).astype(float) for c in
                  ["px", "fo", "vw", "qfo", "ifo", "br", "br15", "sb", "orb15", "orb30", "mfe_up", "mfe_dn"]}
        d = P.groupby(level=0).first()
        self.oc = d.oc.values; self.close = d.close.values; self.gap = d.gap.values
        self.prev_oc = d.prev_oc.values; self.atr = d.atr20.values; self.period = d.period.values
        self.eod = np.sign(self.oc)
        if hunch is not None:
            H = np.full((nd, nm), np.nan)
            pos = {d: i for i, d in enumerate(self.dates)}
            for d, g in hunch.groupby("date"):
                if d not in pos:
                    continue
                t = g["T"].values; s = g.share_up.values
                j = np.searchsorted(t, MARKS, side="right") - 1          # last Hunch bar closed by the mark
                H[pos[d]] = np.where(j >= 0, s[np.maximum(j, 0)], np.nan)
            self.m["hunch"] = H
        else:
            self.m["hunch"] = np.full((nd, nm), np.nan)

    def sub(self, mask):
        q = object.__new__(Panel)
        q.dates = self.dates[mask]
        q.m = {k: v[mask] for k, v in self.m.items()}
        for k in ("oc", "close", "gap", "prev_oc", "atr", "period", "eod"):
            setattr(q, k, getattr(self, k)[mask])
        return q


def upd_marks(I):
    if I == 5:
        return list(range(585, 956, 5))
    if I == 10:
        return list(range(590, 956, 10))
    if I == 15:
        return list(range(585, 956, 15))
    if I == 30:
        return list(CPS)
    raise ValueError(I)


def hold(R: np.ndarray, marks: list[int]) -> np.ndarray:
    """R: [days x len(marks)] readings at update marks -> [days x MARKS] held (0 before the first update)."""
    out = np.zeros((R.shape[0], len(MARKS)))
    idx = np.searchsorted(np.array(marks), MARKS, side="right") - 1
    ok = idx >= 0
    out[:, ok] = R[:, idx[ok]]
    return out


def sgn(x):
    return np.sign(np.nan_to_num(x))


def base_votes(p: Panel, cols, b09=True):
    fo = p.m["fo"][:, cols]; vw = p.m["vw"][:, cols]; br = p.m["br"][:, cols].copy()
    if b09:
        br[:, np.array(MARKS[cols]) == 585] = 0.5          # live convention: no breadth vote at 09:45
    s = sgn(fo)
    agree = np.where((sgn(p.m["qfo"][:, cols]) == s) & (sgn(p.m["ifo"][:, cols]) == s), s, 0)
    bside = np.where(br > 0.5, 1, np.where(br < 0.5, -1, 0))
    return s, sgn(vw), bside, agree


def persistence(s: np.ndarray, marks: list[int], W: int):
    """same nonzero fo sign at every update mark t with T - W < t <= T; also returns number of marks in the window."""
    nd, k = s.shape
    pw = np.zeros_like(s); nmk = np.zeros(k, int)
    for j, T in enumerate(marks):
        js = [i for i, t in enumerate(marks) if T - W < t <= T]
        nmk[j] = len(js)
        w = s[:, js]
        same = np.all(w == w[:, [-1]], axis=1) & (w[:, -1] != 0)
        pw[:, j] = np.where(same, w[:, -1], 0)
    return pw, nmk


def vote(p: Panel, I=15, W=60, theta=0.0, filt=None):
    """VOTE family (today's W60 structure). filt: optional [days x marks] agreement side matrix (+1/-1/0, NaN = pass)."""
    marks = upd_marks(I); cols = mi(marks)
    s, v1, v2, v3 = base_votes(p, cols)
    pw, nmk = persistence(s, marks, W)
    v = s + v1 + v2 + v3 + pw
    fo = p.m["fo"][:, cols]
    ok = (nmk >= 2)[None, :] & (np.abs(np.nan_to_num(fo)) >= theta)
    R = np.where((v >= 4) & (pw == 1) & ok, 1, np.where((v <= -4) & (pw == -1) & ok, -1, 0))
    if filt is not None:
        f = filt[:, cols]
        R = np.where(np.isnan(f) | (f == R), R, 0)
    return hold(R, marks), R, marks


def c30(p: Panel):
    """30-min GATE1 compass exactly as compass_live.c30_at (checkpoints 10:00..15:30, held); confirmed only."""
    L = c30_level(p)
    R = np.where(L == 2, 1, np.where(L == -2, -1, 0))
    return hold(R, CPS), R, list(CPS)


def c30_level(p: Panel):
    """5-level 30-min compass (for the live-consistency check)."""
    cols = mi(CPS)
    s, v1, v2, v3 = base_votes(p, cols)
    L = np.zeros((s.shape[0], len(CPS)))
    for j in range(1, len(CPS)):
        p2 = np.where(s[:, j] == s[:, j - 1], s[:, j], 0)
        p3 = np.where((s[:, j] == s[:, j - 1]) & (s[:, j] == s[:, max(j - 2, 0)]), s[:, j], 0) if j >= 2 else 0 * s[:, j]
        v = s[:, j] + v1[:, j] + v2[:, j] + v3[:, j] + p2
        L[:, j] = np.where((v >= 4) & (p3 == 1), 2, np.where(v >= 2, 1, np.where((v <= -4) & (p3 == -1), -2, np.where(v <= -2, -1, 0))))
    return L


def chk(p: Panel, I=30, theta=0.003, W=None, start=585, filt=None):
    marks = [t for t in upd_marks(I) if t >= start]; cols = mi(marks)
    fo = np.nan_to_num(p.m["fo"][:, cols])
    R = np.where(fo >= theta, 1, np.where(fo <= -theta, -1, 0))
    if W:
        pw, nmk = persistence(sgn(fo), marks, W)
        R = np.where((pw == R) & (nmk >= 2)[None, :], R, 0)
    if filt is not None:
        f = filt[:, cols]
        R = np.where(np.isnan(f) | (f == R), R, 0)
    return hold(R, marks), R, marks


def b_chk(p: Panel):
    """today's checkpoint state: |fo| >= 0.30% at the latest 30-min checkpoint from 10:30."""
    return chk(p, 30, 0.003, None, start=630)


# -------------------------------------------------------------------------------------------------------- filters
def filters(p: Panel):
    """input agreement side per [day x mark]: +1 up-side, -1 down-side, 0 neither; NaN = no data (pass)."""
    fo = p.m["fo"]; nd = fo.shape[0]
    F = {}
    F["orb15"] = p.m["orb15"]
    F["orb30"] = p.m["orb30"]
    F["sector"] = np.where(p.m["sb"] >= 1, 1, np.where(p.m["sb"] <= -1, -1, 0)).astype(float)
    F["br15"] = np.where(p.m["br15"] > 0.5, 1, np.where(p.m["br15"] < 0.5, -1, 0)).astype(float)
    a = p.atr[:, None]
    big = np.abs(np.nan_to_num(fo)) >= 0.25 * np.nan_to_num(a, nan=0.0)
    F["atr"] = np.where(big, sgn(fo), 0).astype(float)
    g = np.repeat(p.gap[:, None], fo.shape[1], 1)
    # gap veto: no UP confirmation after a gap <= -0.5%, no DOWN after >= +0.5%: express as "allowed side"
    F["gap"] = np.where(g <= -0.005, -1.0, np.where(g >= 0.005, 1.0, np.nan))   # NaN = both sides allowed
    pr = np.repeat(sgn(p.prev_oc)[:, None], fo.shape[1], 1).astype(float)
    pr[np.isnan(np.repeat(p.prev_oc[:, None], fo.shape[1], 1))] = np.nan
    F["prevday"] = pr
    h = p.m["hunch"]
    F["hunch"] = np.where(np.isnan(h), np.nan, np.where(h > 0.5, 1, np.where(h < 0.5, -1, 0)))
    return F


# -------------------------------------------------------------------------------------------------------- logit
def logit_X(p: Panel, model: str):
    fo = p.m["fo"]; a = np.nan_to_num(p.atr, nan=np.nanmedian(p.atr))[:, None]
    tau = ((MARKS - 570) / 390.0)[None, :] * np.ones_like(fo)
    z = np.nan_to_num(fo) / a
    s = sgn(fo)
    agree = np.where((sgn(p.m["qfo"]) == s) & (sgn(p.m["ifo"]) == s), s, 0)
    cols = [z, z * tau, np.nan_to_num(p.m["vw"]) / a, np.nan_to_num(p.m["br"], nan=0.5) - 0.5, agree]
    extra = {
        "sector": [np.nan_to_num(p.m["sb"]) / 11.0],
        "br15": [np.nan_to_num(p.m["br15"], nan=0.5) - 0.5],
        "orb30": [np.nan_to_num(p.m["orb30"])],
        "gap": [np.repeat(np.nan_to_num(p.gap)[:, None], fo.shape[1], 1) / a],
        "prevday": [np.repeat(sgn(p.prev_oc)[:, None], fo.shape[1], 1)],
        "hunch": [np.nan_to_num(p.m["hunch"], nan=0.5) - 0.5],
        "qqq_iwm": [np.nan_to_num(p.m["qfo"]) / a, np.nan_to_num(p.m["ifo"]) / a],
    }
    if model == "all":
        for v in extra.values():
            cols += v
    elif model != "base":
        cols += extra[model]
    return np.stack(cols, -1)                                         # [days x marks x F]


def fit_logit(X, y, l2=1e-2, it=50):
    X = np.column_stack([np.ones(len(X)), X])
    w = np.zeros(X.shape[1])
    for _ in range(it):
        z = np.clip(X @ w, -30, 30); pr = 1 / (1 + np.exp(-z))
        g = X.T @ (pr - y) + l2 * np.r_[0, w[1:]]
        H = (X * (pr * (1 - pr))[:, None]).T @ X + l2 * np.diag(np.r_[0, np.ones(len(w) - 1)])
        step = np.linalg.solve(H, g); w -= step
        if np.abs(step).max() < 1e-8:
            break
    return w


def logit_P(p: Panel, model: str, w):
    X = logit_X(p, model)
    z = w[0] + X @ w[1:]
    return 1 / (1 + np.exp(-np.clip(z, -30, 30)))


def logit_read(P: np.ndarray, I=5, pstar=0.85, hyst=0.10):
    marks = upd_marks(I); cols = mi(marks)
    Q = P[:, cols]
    R = np.zeros_like(Q); cur = np.zeros(Q.shape[0])
    for j in range(Q.shape[1]):
        q = Q[:, j]
        new = np.where(q >= pstar, 1, np.where(q <= 1 - pstar, -1, 0))
        keep = np.where((cur == 1) & (q >= pstar - hyst), 1, np.where((cur == -1) & (q <= 1 - pstar + hyst), -1, 0))
        cur = np.where(new != 0, new, keep)
        cur = np.where(np.isnan(q), 0, cur)
        R[:, j] = cur
    return hold(R, marks), R, marks


# -------------------------------------------------------------------------------------------------------- scoring
def score(p: Panel, held: np.ndarray, R: np.ndarray, marks: list[int], wrong=3.0) -> dict:
    """All four targets for one config on one period. Returns per-day primary score array too."""
    eod = p.eod[:, None]
    g = held[:, mi(G)]
    right = (g != 0) & (g == eod); wr = (g != 0) & (g == -eod)
    day_s = right.mean(1) - wrong * wr.mean(1)
    conf = g != 0
    out = dict(days=len(p.dates), S=day_s.mean(), cover=conf.mean(),
               stay=right.sum() / max(conf.sum(), 1), n_conf=int(conf.sum()))
    px = p.m["px"]
    for h in (30, 60, 120):
        hit = tot = 0
        for j, T in enumerate(G):
            if T + h > 960:
                continue
            fut = p.close if T + h == 960 else px[:, mi(T + h)]
            c = g[:, j]; ok = (c != 0) & np.isfinite(fut)
            mv = np.sign(fut / px[:, mi(T)] - 1)
            hit += ((mv == c) & ok).sum(); tot += ok.sum()
        out[f"head{h}"] = hit / max(tot, 1); out[f"head{h}_n"] = int(tot)
    # first confirmation over the update marks (any time)
    first_t = np.full(len(p.dates), np.nan); first_ok = np.full(len(p.dates), np.nan)
    flips = np.zeros(len(p.dates)); false_flips = np.zeros(len(p.dates))
    for i in range(len(p.dates)):
        r = R[i]; nz = np.flatnonzero(r)
        if len(nz):
            first_t[i] = marks[nz[0]]; first_ok[i] = float(r[nz[0]] == p.eod[i])
            seq = r[nz]
            ch = np.flatnonzero(seq[1:] != seq[:-1]) + 1
            flips[i] = len(ch); false_flips[i] = int((seq[ch] != p.eod[i]).sum())
    has = np.isfinite(first_t)
    out.update(first_med=lab(int(np.nanmedian(first_t))) if has.any() else "", by1000=float(np.mean(first_t <= 600)),
               by1030=float(np.mean(first_t <= 630)), first_prec=float(np.nanmean(first_ok)) if has.any() else np.nan,
               conf_days=float(has.mean()), flips=flips.mean(), false_flips=false_flips.mean())
    return out, day_s


def paired_t(a, b):
    d = a - b
    if len(d) < 3 or d.std(ddof=1) == 0:
        return np.nan
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
