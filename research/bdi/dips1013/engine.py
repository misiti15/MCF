"""dips1013 shared engine: data load, exit simulation with production costs, same-minute control, fast statistics.

Bar index k: 5-minute bar closing at 09:35 + 5k (k=2 09:45, k=3 09:50, k=4 09:55, k=8 10:15, k=65 15:00, k=76 15:55).
Open two-year history only (prep.py); the locked block is never loaded. Educational only - not financial advice.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(ROOT))
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

DATA = HERE / "data"
NB = 78
K_LAST = 76                     # 15:55 bar
KS = np.arange(2, 66)           # entry bars 09:45 .. 15:00
SP, BP, SX = gates.SLIP_PS, gates.SLIP_BPS, gates.STOP_EXTRA
EXITS = ("t1s1", "t05s1", "t1s05", "HTC", "SL-VWAP", "SL-OPEN", "SL-HTC", "SW-VWAP")


def tod_of(k):
    m = 575 + 5 * np.asarray(k)
    return (m // 60) * 100 + m % 60


class Data:
    def __init__(self):
        self.days = pd.read_parquet(DATA / "days.parquet")
        z = np.load(DATA / "bars.npz")
        self.b = {k: z[k] for k in z.files}
        m = np.load(DATA / "mkt.npz")
        self.m = {k: m[k] for k in m.files}
        d = self.days
        self.N = len(d)
        self.sess = d["sess"].to_numpy(int)
        self.atr = d["atr_d"].to_numpy(float)
        self.R = 0.25 * self.atr
        self.gap = d["gap"].to_numpy(float)
        self.open0 = d["open"].to_numpy(float)
        self.pc = d["open"].to_numpy(float) / (1 + self.gap / 100)
        reg = lib.regimes()
        dates = sorted(reg.index)
        self.dates = np.array([pd.Timestamp(x) for x in dates])
        self.nsess = len(dates)
        code = {"up": 0, "flat": 1, "down": 2}
        self.reg = np.array([code[reg.loc[x, "regime"]] for x in dates])
        self.valid_sess = np.array([str(x) > "2025-12-31" for x in dates])
        O, H, L, C = (self.b[k].astype(np.float64) for k in "OHLC")
        self.O, self.H, self.L, self.C = O, H, L, C
        self.VW = self.b["VW"].astype(np.float64)
        self.LOD = np.fmin.accumulate(L, 1)
        self.HOD = np.fmax.accumulate(H, 1)


def simulate(D: Data, k: int, stop, tgt, entry=None, from_k=None):
    """Long trades entered at bar k (price `entry`, default the close of bar k) for every day row. Stop first inside a
    bar, a bar opening through the stop fills at its open, target at the target, timed exit at the 15:55 close.
    Returns (net R, gross R, kind) with kind 0 timed / 1 target / 2 stop. Costs: gates production costs with the
    tod entry multiplier of bar k, x3 on the extended tier."""
    px = D.C[:, k] if entry is None else entry
    k0 = k + 1 if from_k is None else from_k
    Lw, Hw, Ow = D.L[:, k0:K_LAST + 1], D.H[:, k0:K_LAST + 1], D.O[:, k0:K_LAST + 1]
    big = Lw.shape[1] + 1
    with np.errstate(invalid="ignore"):
        hs = Lw <= stop[:, None]
        ht = Hw >= tgt[:, None]
    fs = np.where(hs.any(1), np.argmax(hs, 1), big)
    ft = np.where(ht.any(1), np.argmax(ht, 1), big)
    stopped = (fs <= ft) & (fs < big)
    won = (ft < fs)
    rows = np.arange(D.N)
    o_s = Ow[rows, np.minimum(fs, big - 2)]
    xp = np.where(stopped, np.fmin(o_s, stop), np.where(won, tgt, D.C[:, K_LAST]))
    R = D.R
    gross = (xp - px) / R
    mult = float(gates.tod_cost_mult(tod_of(k)))
    cost = (SP + px * BP) * mult + np.where(won, 0.0, SP + xp * BP) + np.where(stopped, SX, 0.0)
    ext = (np.abs(D.gap) >= 20) | (px < 5)
    net = gross - np.where(ext, 3.0, 1.0) * cost / R
    kind = np.where(stopped, 2, np.where(won, 1, 0))
    bad = ~np.isfinite(px) | ~np.isfinite(R) | (R <= 0) | ~np.isfinite(D.C[:, K_LAST])
    net[bad] = np.nan
    gross[bad] = np.nan
    return net, gross, kind


def levels(D: Data, k: int, ex: str, px=None):
    """Stop and target for exit `ex` at entry bar k (entry price px, default the close of bar k)."""
    px = D.C[:, k] if px is None else px
    R = D.R
    nan = np.full(D.N, np.nan)
    if ex in gates.GEOMK:
        up, dn = gates.GEOMK[ex]
        return px - dn * R, px + up * R
    if ex == "HTC":
        return nan, nan
    if ex.startswith("SL-"):
        stop = D.LOD[:, k] - 0.05 * R
    elif ex == "SW-VWAP":
        stop = np.nanmin(D.L[:, max(0, k - 3):k + 1], 1) - 0.05 * R
    vw = D.VW[:, k]
    if ex in ("SL-VWAP", "SW-VWAP"):
        tgt = np.where(vw > px, vw, np.nan)
    elif ex == "SL-OPEN":
        tgt = np.where(D.open0 > px, D.open0, np.nan)
    else:
        tgt = nan
    return stop, tgt


def all_exits(D: Data, exits=EXITS, log=print):
    """NET[ex] [N, 78] (NaN outside 09:45..15:00) and the same-minute control CT[ex] [sess, 78]."""
    NET, CT = {}, {}
    for ex in exits:
        a = np.full((D.N, NB), np.nan, np.float32)
        for k in KS:
            stop, tgt = levels(D, k, ex)
            net, _, _ = simulate(D, k, stop, tgt)
            a[:, k] = net
        NET[ex] = a
        ct = np.full((D.nsess, NB), np.nan)
        for k in KS:
            v = a[:, k].astype(float)
            ok = np.isfinite(v)
            s = np.bincount(D.sess[ok], v[ok], D.nsess)
            n = np.bincount(D.sess[ok], minlength=D.nsess)
            ct[:, k] = np.where(n > 0, s / np.maximum(n, 1), np.nan)
        CT[ex] = ct
        log(ex, "done", flush=True)
    return NET, CT


def tstat(r, sess, nsess):
    n = len(r)
    if n < 2:
        return np.nan, np.nan
    mu = r.mean()
    s = np.bincount(sess, r, nsess)
    c = np.bincount(sess, minlength=nsess)
    se = np.sqrt(((s - c * mu) ** 2).sum()) / n
    return mu, (mu / se if se > 0 else np.nan)


def fast_stats(D: Data, NET, CT, ex, d, k) -> dict:
    """Statistics of the trade set (day rows d, entry bars k) under exit ex."""
    r = NET[ex][d, k].astype(float)
    ok = np.isfinite(r)
    d, k, r = d[ok], k[ok], r[ok]
    out = {"n": int(len(r))}
    if len(r) < 2:
        return out
    s = D.sess[d]
    x = r - CT[ex][s, k]
    va = D.valid_sess[s]
    for nm, m in (("train", ~va), ("valid", va), ("open", np.ones(len(r), bool))):
        mu, t = tstat(r[m], s[m], D.nsess)
        out[f"{nm}_n"], out[f"{nm}_exp"], out[f"{nm}_t"] = int(m.sum()), mu, t
        mu, t = tstat(x[m], s[m], D.nsess)
        out[f"{nm}_exc"], out[f"{nm}_exc_t"] = mu, t
    rg = D.reg[s]
    for code, nm in ((0, "up"), (1, "flat"), (2, "down")):
        m = rg == code
        out[f"{nm}_n"] = int(m.sum())
        out[f"{nm}_exp"] = float(r[m].mean()) if m.any() else np.nan
        out[f"{nm}_exc"] = float(x[m].mean()) if m.any() else np.nan
    ds = np.bincount(s, r, D.nsess)
    dc = np.bincount(s, minlength=D.nsess)
    b = int(np.argmax(ds))
    out["ex_best"] = float((ds.sum() - ds[b]) / max(1, len(r) - dc[b]))
    out["busiest"] = float(dc.max() / len(r))
    out["per_day"] = float(len(r) / D.nsess)
    return out


def trades_frame(D: Data, NET, CT, ex, d, k) -> pd.DataFrame:
    r = NET[ex][d, k].astype(float)
    ok = np.isfinite(r)
    d, k, r = d[ok], k[ok], r[ok]
    s = D.sess[d]
    return pd.DataFrame({"date": D.dates[s], "symbol": D.days["symbol"].to_numpy()[d], "tod": tod_of(k), "k": k,
                         "row": d, "r": r, "ctrl": CT[ex][s, k]})
