"""PDL-1a (owner exception 2026-10-30, Testing 2): the regime-day "R2A" row of research/bdi/pdl1030/regime-day, live.
Educational only - not financial advice.

OWNER EXCEPTION, NOT A CANDIDATE: R2A did NOT pass the BAR90 Testing bar (TRAIN +0.0031 / VALID +0.0071 avg R,
day-clustered t 1.14 vs bar 4.355, 76.5% months positive, 54.3 trades/session; 152 configurations tried in pdl1030,
lineage N 121,611). It runs as a forward observation only.

What regime-day/score.py scored (build.py harness), reproduced here:
  signal   CWT14-failbrk-pdl-p05 (cwt_live_lib.b3 PD level, p 0.05, any volume, long kernel): price trades 0.05+ ATR
           under yesterday's low, then closes back above it within 3 bars. FIRST such bar per symbol-day with a bar
           close in 09:50-15:00 (adv20 >= $95M = the YAML min_adv), entry at that bar's close.
  cost5    skip the symbol-day when that FIRST bar's round-trip cost estimate is > 5% of R1, R1 = 0.25 x daily ATR:
           [(1c + 1 bp) x 1.4 before 10:30 (x1.0 from 10:30) + (1c + 1 bp)] x 3 on the extended tier (|gap| >= 20% or
           price < $5) / R1 <= 0.05. A later bar of the same day never replaces a skipped first bar (as scored).
  side     pre-open regime: SPY prior-day range / SPY ATR (lab context spy_prng) > 0.7956493496894836 (the TRAIN
           median, regime-day CUT R2) -> LONG; < the cut -> SHORT at the same signal-bar close; equal / missing -> none.
  exits    S3: stop 3 x R1 = 0.75 ATR from the entry (same $ risk: the runner sizes on the stop distance, so 1/3 of the
           parent's shares); target PRICE kept = entry +/- 0.5 R1 = 0.125 ATR; half off at entry +/- 0.25 R1 =
           0.0625 ATR, rest's stop to breakeven (YAML scale_out_r 1/12 of the 0.75 ATR stop distance); flat 15:55.
           The short leg mirrors every price.
Two setups (one per side) share this mask; exactly one of them can fire on a given day.
"""
import numpy as np

import cwt_live_lib as L

REGIME_CUT = 0.7956493496894836   # regime-day score_out.txt cuts['R2'] (median SPY prng over TRAIN sessions)
R1_ATR = 0.25                      # the parent's R (0.25 x daily ATR)
STOP_R1 = 3.0                      # S3 stop: 3 x R1
TARGET_R1 = 0.5                    # parent's target price: +0.5 R1
COST_MAX_R1 = 0.05                 # cost5


def entries(df) -> np.ndarray:
    """The first p05 signal bar per symbol-day in 09:50-15:00 that passes cost5 (regime not applied)."""
    x = L.arrays(df)
    sig = np.asarray(L.b3(df, level="PD", p=0.05, lowvol=False, side="long"), bool)
    atr = df["atr_d"].to_numpy(float)
    with np.errstate(invalid="ignore"):
        sig &= (x.tod >= 950) & (x.tod <= 1500) & np.isfinite(atr) & (atr > 0)
    idx = np.flatnonzero(sig)
    first = np.zeros(x.n, bool)
    if len(idx):
        seg = x.seg[idx]
        first[idx[np.r_[True, seg[1:] != seg[:-1]]]] = True
    c = x.c
    one = 0.01 + c * 1e-4
    with np.errstate(invalid="ignore", divide="ignore"):
        tier = np.where((np.abs(df["gap"].to_numpy(float)) >= 20) | (c < 5), 3.0, 1.0)
        cost_r1 = (one * np.where(x.tod < 1030, 1.4, 1.0) + one) * tier / (R1_ATR * atr)
        return first & (cost_r1 <= COST_MAX_R1)


def regime(df) -> tuple[np.ndarray, np.ndarray]:
    """(long day, short day) per row from the lab context column spy_prng; NaN / missing / at the cut -> neither."""
    if "spy_prng" not in df.columns:
        z = np.zeros(len(df), bool)
        return z, z
    v = df["spy_prng"].to_numpy(float)
    with np.errstate(invalid="ignore"):
        return v > REGIME_CUT, v < REGIME_CUT


def mask(df, side: str) -> np.ndarray:
    up, dn = regime(df)
    return entries(df) & (up if side == "long" else dn)


def stop_price(f, i, side: str) -> float:
    s = 1 if side == "long" else -1
    return float(f["close"].iloc[i]) - s * STOP_R1 * R1_ATR * float(f["atr_d"].iloc[i])


def target_price(f, i, side: str) -> float:
    s = 1 if side == "long" else -1
    return float(f["close"].iloc[i]) + s * TARGET_R1 * R1_ATR * float(f["atr_d"].iloc[i])
