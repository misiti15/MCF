"""BURST1 remedy rules (PLAN.md). Every rule takes one ordered group (entry order) and returns keep flags.
Inputs per trade: m (entry minute of day), xm (exit minute), r (R), side, and callables mk(j, t) / mfe(j, t) giving
mark-to-market R and MFE-to-date R of trade j at minute t (NaN-safe -> 0). Educational only - not financial advice."""
import numpy as np


def pace(m, N, W=15):
    keep = np.ones(len(m), bool)
    for i in range(len(m)):
        prev = keep[:i] & (m[:i] > m[i] - W) & (m[:i] <= m[i])
        if prev.sum() >= N:
            keep[i] = False
    return keep


def latch(m, xm, r, L, mk=None):
    """mk=None: realised-only live latch. mk given: realised + open mark-to-market. Latched for the rest of the day."""
    keep = np.ones(len(m), bool); hit = False
    for i in range(len(m)):
        if not hit and i:
            k = keep[:i]
            done = k & (xm[:i] <= m[i])
            tot = r[:i][done].sum()
            if mk is not None:
                op = np.flatnonzero(k & (xm[:i] > m[i]))
                tot += sum(mk(j, m[i]) for j in op)
            hit = tot <= L + 1e-9
        if hit:
            keep[i] = False
    return keep


def fof(m, xm, K, x, mfe):
    keep = np.ones(len(m), bool)
    for i in range(len(m)):
        op = np.flatnonzero(keep[:i] & (xm[:i] > m[i]))
        if len(op) >= K and sum(mfe(j, m[i]) < x for j in op) >= K:
            keep[i] = False
    return keep


def burst_compass(m, side, B, against, W=15):
    """against(t) -> True if the market state at the last checkpoint <= t is against `side`."""
    keep = np.ones(len(m), bool)
    for i in range(len(m)):
        prev = keep[:i] & (m[:i] > m[i] - W) & (m[:i] <= m[i])
        if prev.sum() >= B and against(m[i], side):
            keep[i] = False
    return keep
