"""Round-3 daily trend engine (swing/daily, NOT intraday; research/crypto_r3/PREREG.md section 2).

Long-only sleeves on daily UTC bars. At each decision (00:00 UTC, the close of a day) a rule says enter / exit.
Entry: maker limit buy at the decision close, resting `expiry` minutes, filled only by a traded minute whose low is
strictly below the limit (round-2 Amendment-1 fill), or a taker buy at the open of the first minute (sensitivity).
Exit: taker at the open of the first minute at/after the decision. Costs from `CostModel` (fees per tier,
half-spread, slippage). Each sleeve is marked at the daily closes; a portfolio is the mean of equal sleeves (no
rebalancing, cash earns 0). Educational only — not financial advice.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .costs import FEE_TIERS, CostModel
from .exec1m import Minutes
from .features import rsi, wilder

RULES = {"A": "regime", "B": "breakout20/10", "C": "pullback RSI3<20"}


@dataclass(frozen=True)
class TrendRule:
    rule: str                 # "A" regime | "B" breakout in regime | "C" pullback in regime
    ma: int                   # SMA length of the regime filter (days)
    draw_id: int = -1
    entry: str = "maker"      # "maker" | "taker" (sensitivity)
    expiry_min: int = 1440
    max_hold: int = 10        # rule C only (decisions)

    def label(self) -> str:
        return f"1d {RULES[self.rule]} in close>SMA{self.ma}, {self.entry} entry"


def indicators(d: pd.DataFrame) -> pd.DataFrame:
    """Daily features from daily bars (o/h/l/c). Everything at row k uses closes up to and including day k."""
    c = d["c"]
    f = pd.DataFrame(index=d.index)
    f["c"] = c
    for n in (50, 100, 200):
        f[f"sma{n}"] = c.rolling(n, min_periods=n).mean()
    f["hi20"] = c.shift(1).rolling(20, min_periods=20).max()
    f["lo10"] = c.shift(1).rolling(10, min_periods=10).min()
    f["rsi3"] = rsi(c, 3)
    pc = c.shift(1)
    tr = pd.concat([d["h"] - d["l"], (d["h"] - pc).abs(), (d["l"] - pc).abs()], axis=1).max(axis=1)
    f["atr"] = wilder(tr, 14)
    return f


def signals(rule: TrendRule, f: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """(enter, exit) boolean arrays for each decision row."""
    c = f["c"].to_numpy()
    ma = f[f"sma{rule.ma}"].to_numpy()
    up = np.nan_to_num(c > ma, nan=False).astype(bool) & ~np.isnan(ma)
    if rule.rule == "A":
        return up, ~up
    if rule.rule == "B":
        hi, lo = f["hi20"].to_numpy(), f["lo10"].to_numpy()
        return up & (c > hi), (~up) | (c < lo)
    if rule.rule == "C":
        r3 = f["rsi3"].to_numpy()
        return up & (r3 < 20), (~up) | (r3 > 70)
    raise ValueError(rule.rule)


def simulate(pair: str, dec_t: np.ndarray, close: np.ndarray, enter: np.ndarray, exitc: np.ndarray,
             mins: Minutes, costs: CostModel, mode: str = "maker", expiry: int = 1440, max_hold: int = 0,
             tier: int = 1, atr: np.ndarray | None = None) -> pd.DataFrame:
    """Trades of one sleeve. dec_t: decision times (minutes since epoch, ascending, one per day). A position open
    at the last decision is closed there (taker). Returns one row per trade with entry/exit decision indices."""
    mk_fee, tk_fee = FEE_TIERS[tier]
    t, o, lo, trd = mins.t, mins.o, mins.l, mins.traded
    n = len(t)
    rows = []
    k_in = -1
    e = t_in = 0.0
    cin = 0.0
    last = len(dec_t) - 1
    for k in range(len(dec_t)):
        if k_in >= 0:
            if exitc[k] or k == last or (max_hold and k - k_in >= max_hold):
                j = np.searchsorted(t, dec_t[k])
                if j >= n:
                    j = n - 1
                thin = t[j] > dec_t[k]
                yr = pd.Timestamp(int(t[j]) * 60, unit="s").year
                nf, _ = costs.leg(pair, yr, maker=False, entry=False)
                if thin:
                    nf += costs.slip_bps / 1e4 * (costs.thin_mult - 1)
                cout = nf + tk_fee
                x = o[j]
                net = (x / e) * (1 - cin) * (1 - cout) - 1
                rows.append((k_in, k, t_in, t[j], e, x, cin, cout, net,
                             atr[k_in] / e if atr is not None else np.nan))
                k_in = -1
            continue
        if k == last or not enter[k]:
            continue
        j = np.searchsorted(t, dec_t[k])
        if j >= n:
            break
        yr = pd.Timestamp(int(dec_t[k]) * 60, unit="s").year
        if mode == "maker":
            z = np.searchsorted(t, dec_t[k] + expiry)
            hit = np.flatnonzero(trd[j:z] & (lo[j:z] < close[k]))
            if len(hit) == 0:
                continue
            e, t_in, cin = close[k], t[j + hit[0]], mk_fee
        else:
            nf, _ = costs.leg(pair, yr, maker=False, entry=True, thin=bool(t[j] > dec_t[k]))
            e, t_in, cin = o[j], t[j], nf + tk_fee
        k_in = k
    cols = ["k_in", "k_out", "t_in", "t_out", "entry", "exit", "cost_in", "cost_out", "net", "atr_pct"]
    df = pd.DataFrame(rows, columns=cols)
    df["pair"] = pair
    return df


def sleeve_equity(trades: pd.DataFrame, dec_t: np.ndarray, close: np.ndarray) -> np.ndarray:
    """Equity at each decision (start 1.0 before the first decision). Mark-to-market at the daily closes."""
    r = np.zeros(len(dec_t))
    for tr in trades.itertuples():
        a = int(np.searchsorted(dec_t, tr.t_in, "right"))      # first close after the fill
        b = int(np.searchsorted(dec_t, tr.t_out, "right"))     # first close after the exit print
        b = min(b, len(dec_t) - 1)
        if a > b:
            a = b
        if a == b:
            r[b] = (tr.exit / tr.entry) * (1 - tr.cost_in) * (1 - tr.cost_out) - 1
            continue
        r[a] = (close[a] / tr.entry) * (1 - tr.cost_in) - 1
        if b > a + 1:
            r[a + 1:b] = close[a + 1:b] / close[a:b - 1] - 1
        r[b] = (tr.exit / close[b - 1]) * (1 - tr.cost_out) - 1
    return np.cumprod(1 + r)


def metrics(eq: np.ndarray) -> dict:
    eq = np.asarray(eq, float)
    full = np.concatenate([[1.0], eq])
    ret = full[1:] / full[:-1] - 1
    sd = ret.std(ddof=1)
    dd = 1 - full / np.maximum.accumulate(full)
    total = full[-1] - 1
    yrs = len(ret) / 365.0
    return {"total": float(total), "cagr": float((1 + total) ** (1 / yrs) - 1) if yrs > 0 and total > -1 else np.nan,
            "sharpe": float(ret.mean() / sd * np.sqrt(365)) if sd > 0 else 0.0, "maxdd": float(dd.max())}


def random_windows(rng: np.random.Generator, durations: list[int], n_dec: int) -> tuple[np.ndarray, np.ndarray]:
    """Random non-overlapping holding windows with the given durations (decisions) inside n_dec decisions.
    Returns (enter, exit) arrays for `simulate`: enter inside a window, exit at its end and outside windows."""
    enter = np.zeros(n_dec, bool)
    exitc = np.ones(n_dec, bool)
    durs = [max(1, int(d)) for d in durations]
    slack = n_dec - 1 - sum(durs) - len(durs)
    if not durs or slack < 0:
        return enter, exitc
    gaps = np.diff(np.concatenate([[0], np.sort(rng.integers(0, slack + 1, len(durs))), [slack]]))
    pos = 0
    for d, g in zip(rng.permutation(durs), gaps[:len(durs)]):
        pos += int(g)
        enter[pos:pos + d] = True
        exitc[pos:pos + d] = False
        pos += d + 1
    return enter, exitc
