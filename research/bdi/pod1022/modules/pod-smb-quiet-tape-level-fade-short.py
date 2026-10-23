"""pod-smb-quiet-tape-level-fade-short - Quiet-tape fade of an extended push into PDH without a break (SHORT side; the
LONG mirror at PDL is pod-smb-quiet-tape-level-fade-long, the same code with SIDE flipped).

Source: SMB Training blog 'Finding good setups in a quiet tape' (Palau).
URL: https://www.smbtraining.com/blog/finding-good-setups-in-a-quiet-tape

VARIANT of obos-levels (holdout_failed) and the no-break opposite of CWT14 failed-break (needs a break). Stated change:
a decision-time quiet-market gate and a 'buyer loses' trigger at the level with no break.

SPY range so far: SPY's own frame row at the same (date, tod): (HOD - LOD) from its dist_hod_atr / dist_lod_atr,
compared with SPY's daily ATR. No SPY row -> no trade.

Rules (plain English), decision bar i (SHORT; LONG = mirror at PDL):
  1. Quiet tape: |spy_fo| <= 0.30%, breadth 0.40-0.60, SPY range so far today <= 0.6 x SPY daily ATR.
  2. Extended push: fromOpen_i >= +1.0% and move high (max high of bars i-4..i) - low_{i-4} >= 0.5 x daily ATR.
     ONE pre-declared reading change (first full scoring, literal 'close_i - low_{i-4}', gave 0 trades on both sides
     over the whole open history because a 0.5 ATR close-to-low push and a close below the prior bar's low almost
     never coexist on one bar): the push is measured to the top of the move into the level, as the source describes
     it ('an extended push into the level'). Nothing was tuned on the valid period.
  3. At the level without a break: max(high_i, high_{i-1}) within 0.10 x daily ATR of the prior-day high, and no close
     above the PDH today (frame bars up to i).
  4. Buyer loses: close_i < low_{i-1} with upper_wick_i >= 0.4, or RSI(5) falls from >= 80 (bar i-1) to < 65 (bar i).
  Entry: close_i, bar close 10:30-14:30. Stop (GEOM S): the move high (max high of bars i-4..i) + 0.02 x daily ATR.
  Target: session VWAP at entry, capped at 1.5R (the nearer of VWAP and entry - 1.5 x risk); no trade when VWAP is not
  below the entry. Flat 15:55. Costs in (scorer). Reported by regime (scorer by_regime). No tweak used.
  LONG: fromOpen <= -1.0%, high_{i-4} - move low >= 0.5 ATR, min(low_i, low_{i-1}) within 0.10 ATR of PDL, no close below
  PDL today, close > high_{i-1} with lower_wick >= 0.4 or RSI(5) from <= 20 to > 35; stop move low - 0.02 ATR;
  target VWAP capped at 1.5R.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "S"
WINDOW = (1030, 1430)
CONTEXT = ["spy_fo", "breadth"]
LAYERS = ["|spy_fo| <= 0.30%, breadth 0.40-0.60, SPY range <= 0.6 SPY ATR",
          "|fromOpen| >= 1%, 4-bar push >= 0.5 ATR toward the level",
          "bar extreme within 0.10 ATR of PDH/PDL, no close beyond it today",
          "close beyond the prior bar's extreme with a 40% wick, or RSI5 80->65 (20->35)",
          "stop move extreme + 0.02 ATR, target VWAP capped at 1.5R", "10:30-14:30 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _spy_cols(df, cols):
    """SPY's own row values at the same (date, tod), aligned to df (NaN where SPY is absent)."""
    key = pd.DataFrame({"date": df["date"].to_numpy(), "tod": df["tod"].to_numpy()})
    sp = df.loc[df["symbol"].astype(str) == "SPY", ["date", "tod"] + cols].drop_duplicates(["date", "tod"])
    sp = sp.rename(columns={c: "spy_" + c for c in cols})
    j = key.merge(sp, on=["date", "tod"], how="left")
    return {c: j["spy_" + c].to_numpy(float) for c in cols}


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, vw, fo, wick, r5, lvl, quiet, atr, sg, w0, w1):
    """sg = -1 short (level PDH) / +1 long (level PDL). Prices are mirrored via sg."""
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        broke = False
        for i in range(i0, i1):
            L = lvl[i]
            if sg < 0 and c[i] > L:
                broke = True
            if sg > 0 and c[i] < L:
                broke = True
            if broke or i < i0 + 4 or tod[i] < w0 or tod[i] > w1 or not quiet[i]:
                continue
            a = atr[i]
            if not (a > 0):
                continue
            if sg < 0:
                ext = max(max(h[i - 4], h[i - 3]), max(max(h[i - 2], h[i - 1]), h[i]))
                if not (fo[i] >= 1.0 and ext - l[i - 4] >= 0.5 * a):
                    continue
                if not (abs(max(h[i], h[i - 1]) - L) <= 0.10 * a):
                    continue
                trig = (c[i] < l[i - 1] and wick[i] >= 0.4) or (r5[i - 1] >= 80 and r5[i] < 65)
                if not trig:
                    continue
                sp = ext + 0.02 * a
                risk = sp - c[i]
                if not (risk > 0 and vw[i] < c[i]):
                    continue
                tp = max(vw[i], c[i] - 1.5 * risk)
            else:
                ext = min(min(l[i - 4], l[i - 3]), min(min(l[i - 2], l[i - 1]), l[i]))
                if not (fo[i] <= -1.0 and h[i - 4] - ext >= 0.5 * a):
                    continue
                if not (abs(min(l[i], l[i - 1]) - L) <= 0.10 * a):
                    continue
                trig = (c[i] > h[i - 1] and wick[i] >= 0.4) or (r5[i - 1] <= 20 and r5[i] > 35)
                if not trig:
                    continue
                sp = ext - 0.02 * a
                risk = c[i] - sp
                if not (risk > 0 and vw[i] > c[i]):
                    continue
                tp = min(vw[i], c[i] + 1.5 * risk)
            m[i] = True
            stop[i] = sp
            tgt[i] = tp
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0 or "spy_fo" not in df or "breadth" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr = f("close"), f("atr_d")
    sg = 1 if SIDE == "long" else -1
    sp = _spy_cols(df, ["dist_hod_atr", "dist_lod_atr"])
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = c / (1 + f("vwapDistPct") / 100)
        spy_rng_atr = sp["dist_hod_atr"] + sp["dist_lod_atr"]           # (HOD - LOD) / SPY atr_d
        br = f("breadth")
        quiet = (np.abs(f("spy_fo")) <= 0.30) & (br >= 0.40) & (br <= 0.60) & (spy_rng_atr <= 0.6)
        if sg < 0:
            lvl = c + f("dist_pdh_atr") * atr
            wick = f("upper_wick")
        else:
            lvl = c - f("dist_pdl_atr") * atr
            wick = f("lower_wick")
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, f("high"), f("low"), vw, f("fromOpen"), wick, f("rsi5"),
                   lvl, quiet, atr, sg, WINDOW[0], WINDOW[1])


def mask(df) -> np.ndarray:
    m, stop, tgt = compute(df)
    _STASH.clear()
    _STASH[id(df)] = (stop, tgt)
    return m


def _get(f):
    s = _STASH.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
