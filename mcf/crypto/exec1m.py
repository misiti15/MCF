"""Round-2 execution engine ("E5b crypto 1-min fills"): signals decided on any bar timeframe, fills and exits
simulated on the pair's REAL 1-minute prints (minutes with no trade do not exist, so nothing fills on them).

Entry modes
  taker   market buy at the open of the first real print at/after the decision time (bar close). If that print is
          not in the first minute after the decision, the entry counts as `thin` (x3 slippage).
  maker   limit buy at L = ref_close - off * ATR(tf), resting `expiry` minutes from the decision. It fills ONLY if
          a later 1-min bar trades THROUGH the limit (low < L, strictly); a touch (low == L) does not fill. Fill
          price = L. Orders that never trade through are MISSED (counted, no trade). This makes the entry pay its
          own adverse selection: a limit only fills when price comes down to it.
  naive   (sensitivity only) round-1 assumption: maker fee, filled at the first print's open with certainty.
Exits
  stop    risk = max(stop_atr * ATR(tf), min_stop_pct * entry); stop = entry - risk. Taker. Fills at the stop, or at
          the minute's open when it gaps through. On a maker fill minute the stop is checked on that same minute
          (the low that filled the order may also have hit the stop: assumed it did).
  target  entry + target_r * risk; a resting maker sell that fills only when a later minute trades THROUGH it
          (high > target). Never on the entry minute.
  time    first real print at/after entry + hold minutes, taker at its open.
  Stop is checked before target inside one minute. One open position per pair; signals while a position or a
  resting order is live are ignored.
Educational only — not financial advice.
"""
from __future__ import annotations

from dataclasses import dataclass

import numba
import numpy as np
import pandas as pd

from .costs import FEE_TIERS, CostModel

KIND = {0: "time", 1: "stop", 2: "target", 3: "end"}


@dataclass(frozen=True)
class Plan:
    mode: str = "maker"            # "maker" | "taker" | "naive"
    off_atr: float = 0.0           # maker limit offset below the decision close, ATR(tf) units
    expiry_min: int = 60           # maker order life, minutes
    stop_atr: float = 2.0
    min_stop_pct: float = 0.03
    target_r: float | None = 2.0
    hold_min: int = 1440


@dataclass
class Minutes:
    """Real 1-min prints of one pair: t = minutes since epoch (int64), o/h/l/c float64."""
    t: np.ndarray
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray

    @classmethod
    def from_bars(cls, b: pd.DataFrame) -> "Minutes":
        if "filled" in b:
            b = b[~b["filled"]]
        t = to_min(b.index)
        f = lambda k: np.ascontiguousarray(b[k].to_numpy(np.float64))  # noqa: E731
        return cls(t, f("o"), f("h"), f("l"), f("c"))

    def slice(self, a: int, z: int) -> "Minutes":
        i, j = np.searchsorted(self.t, [a, z])
        return Minutes(self.t[i:j], self.o[i:j], self.h[i:j], self.l[i:j], self.c[i:j])


def to_min(idx: pd.DatetimeIndex) -> np.ndarray:
    return np.asarray((idx - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta("1min"), dtype=np.int64)


@numba.njit(cache=True)
def _sim(t, o, h, l, c, st, sref, satr, mode, off, expiry, stop_atr, min_pct, tgt_r, hold):
    n_sig = len(st)
    n = len(t)
    out = np.empty((n_sig, 9))     # sig, t_in, t_out, entry, exit, risk, kind, maker_in, thin
    k = 0
    missed = 0
    busy = -1
    for s in range(n_sig):
        ts = st[s]
        if ts < busy or not (satr[s] > 0):
            continue
        j = np.searchsorted(t, ts)
        if j >= n:
            break
        thin = 0.0
        maker_in = 0.0
        if mode == 1:                                   # realistic maker: must trade through the limit
            lim = sref[s] - off * satr[s]
            f = -1
            q = j
            while q < n and t[q] < ts + expiry:
                if l[q] < lim:
                    f = q
                    break
                q += 1
            if f < 0:
                missed += 1
                busy = ts + expiry
                continue
            e = lim
            j = f
            maker_in = 1.0
        else:
            e = o[j]
            if t[j] > ts:
                thin = 1.0
            if mode == 2:
                maker_in = 1.0
        risk = max(stop_atr * satr[s], min_pct * e)
        stop = e - risk
        tgt = e + tgt_r * risk if tgt_r > 0 else np.inf
        t_end = t[j] + hold
        x = -1
        px = 0.0
        kind = 3
        for m in range(j, n):
            if m > j and t[m] >= t_end:
                x, px, kind = m, o[m], 0
                break
            if l[m] <= stop:
                if m == j and mode == 1:
                    px = stop
                elif m == j:
                    px = stop
                else:
                    px = min(o[m], stop)
                x, kind = m, 1
                break
            if m > j and h[m] > tgt:
                x, px, kind = m, tgt, 2
                break
        if x < 0:
            x = n - 1
            px = c[n - 1]
            kind = 3
        out[k, 0] = s
        out[k, 1] = t[j]
        out[k, 2] = t[x]
        out[k, 3] = e
        out[k, 4] = px
        out[k, 5] = risk
        out[k, 6] = kind
        out[k, 7] = maker_in
        out[k, 8] = thin
        k += 1
        busy = t[x] + 1
    return out[:k], missed


COLS = ["pair", "entry_time", "exit_time", "day", "entry", "exit", "risk", "kind", "maker_in", "maker_out", "thin",
        "gross_r", "nonfee_r", "fee_r", "cost_r", "r", "fee_in", "fee_out", "rpu"]


def run(pair: str, mins: Minutes, sig_t: np.ndarray, sig_ref: np.ndarray, sig_atr: np.ndarray, plan: Plan,
        costs: CostModel | None = None, tier: int = 1) -> tuple[pd.DataFrame, int, int]:
    """Trades for one pair from decision times (minutes since epoch, sorted), the decision-bar close and ATR(tf).
    Returns (trades, signals offered, maker orders missed). Long only (Alpaca crypto spot)."""
    costs = costs or CostModel()
    mode = {"taker": 0, "maker": 1, "naive": 2}[plan.mode]
    if len(sig_t) == 0 or len(mins.t) == 0:
        return pd.DataFrame(columns=COLS), 0, 0
    out, missed = _sim(mins.t, mins.o, mins.h, mins.l, mins.c, np.ascontiguousarray(sig_t, np.int64),
                       np.ascontiguousarray(sig_ref, np.float64), np.ascontiguousarray(sig_atr, np.float64), mode,
                       float(plan.off_atr), int(plan.expiry_min), float(plan.stop_atr), float(plan.min_stop_pct),
                       float(plan.target_r or 0.0), int(plan.hold_min))
    if len(out) == 0:
        return pd.DataFrame(columns=COLS), len(sig_t), int(missed)
    t_in = pd.to_datetime(out[:, 1].astype(np.int64), unit="m", utc=True)
    t_out = pd.to_datetime(out[:, 2].astype(np.int64), unit="m", utc=True)
    en, xp, risk, kind = out[:, 3], out[:, 4], out[:, 5], out[:, 6].astype(int)
    maker_in = out[:, 7] > 0
    maker_out = kind == 2
    thin = out[:, 8] > 0
    years = t_in.year.to_numpy()
    nonfee = np.empty(len(out))
    for q in range(len(out)):
        a, _ = costs.leg(pair, int(years[q]), maker=bool(maker_in[q]), entry=True, thin=bool(thin[q]))
        b, _ = costs.leg(pair, int(years[q]), maker=bool(maker_out[q]), entry=False, stop_exit=bool(kind[q] == 1))
        nonfee[q] = a + b
    rpu = en / risk                                      # cost fraction -> R
    df = pd.DataFrame({"pair": pair, "entry_time": t_in, "exit_time": t_out, "day": t_in.floor("D"), "entry": en,
                       "exit": xp, "risk": risk, "kind": kind, "maker_in": maker_in, "maker_out": maker_out,
                       "thin": thin, "gross_r": (xp - en) / risk, "nonfee_r": nonfee * rpu, "rpu": rpu})
    reprice(df, tier)
    return df, len(sig_t), int(missed)


def reprice(df: pd.DataFrame, tier: int = 1) -> pd.DataFrame:
    """(Re)charge fees at an Alpaca volume tier (1 = 15/25 bps maker/taker, 2 = 12/22, 3 = 10/20) in place."""
    mk, tk = FEE_TIERS[tier]
    df["fee_in"] = np.where(df["maker_in"], mk, tk)
    df["fee_out"] = np.where(df["maker_out"], mk, tk)
    df["fee_r"] = (df["fee_in"] + df["fee_out"]) * df["rpu"]
    df["cost_r"] = df["nonfee_r"] + df["fee_r"]
    df["r"] = df["gross_r"] - df["cost_r"]
    return df
