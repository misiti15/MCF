"""TAPE-1126 tape signals from idx.npz (PREREG.md): SPY fo on the last closed 5-min bar (S1/S2), S3 / H1 market triggers on
the 5-min grid 11:30..13:30, and the H1 trade outcome for every (day, T, instrument) (used by H1, S3+H1 and the placebos).
Usage: python signals.py W. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

W = Path(sys.argv[1]); LOCK = ("2024-11-01", "2025-02-28")
_Z = np.load(W / "idx.npz"); Z = {k: _Z[k] for k in _Z.files}
days = Z["days"].astype(str)
assert not ((days >= LOCK[0]) & (days <= LOCK[1])).any()
D = len(days)
TG = np.arange(120, 241, 5)                 # T offsets from 09:30: 11:30 .. 13:30
SECT = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
FLAT = 384                                  # 15:54 bar close = 15:55
SIDE_BP, SEC = 1e-4, 20.60e-6


def h1_trade(A, o, pc, t):
    """A = 5 x 390 (O,H,L,C,VW) one day; entry at the open of minute t. Returns (r1, retp) or (nan, nan)."""
    O, H, L, C = A[0], A[1], A[2], A[3]
    e = O[t]
    if not np.isfinite(e):
        return np.nan, np.nan
    st = np.nanmin(L[60:t]) * (1 - 0.0005)
    st = max(st, e * (1 - 0.006))
    if st >= e:
        return np.nan, np.nan
    risk = e - st
    tgt = pc if (np.isfinite(pc) and o < pc and pc > e) else None
    hh = e; x = None
    for j in range(t, FLAT + 1):
        if L[j] <= st:
            x = min(st, O[j]); break
        if tgt is not None and H[j] >= tgt:
            x = max(tgt, O[j]) if O[j] >= tgt else tgt; break
        hh = max(hh, H[j])
        if hh >= e + 1.5 * risk:
            st = max(st, hh - risk)
    if x is None:
        x = C[FLAT]
    c = e * SIDE_BP + x * (SIDE_BP + SEC)
    return (x - e - c) / risk, (x - e - c) / e


if __name__ == "__main__":
    S = Z["SPY"]; so = Z["SPY_open"]
    # fo on the last fully closed 5-min bar before entry minute offset k (k = 0..390): bar end b = 5*floor(k/5), close C[b-1]
    k = np.arange(391); b = (k // 5) * 5
    fo5 = np.full((D, 391), np.nan)
    ok = b >= 5
    fo5[:, ok] = S[3][:, b[ok] - 1] / so[:, None] - 1
    brT = Z["brT"]; brv = Z["brv"]
    tcol = {int(T): i for i, T in enumerate(brT)}
    hhmm = lambda t: ((570 + t) // 60) * 100 + (570 + t) % 60  # noqa: E731
    mkt = np.zeros((D, len(TG)), bool); sec = np.zeros((D, len(TG)), int); bv = np.full((D, len(TG)), np.nan)
    for i in range(D):
        if not np.isfinite(so[i]):
            continue
        for q, t in enumerate(TG):
            dip = np.nanmin(S[2][i, 60:t]) <= so[i] * (1 - 0.004)
            rec = S[3][i, t - 1] >= S[4][i, t - 1] * 1.001
            br = brv[i, tcol[hhmm(t)]] if hhmm(t) in tcol else np.nan
            bv[i, q] = br
            mkt[i, q] = dip and rec and (br >= 0.70)
            sec[i, q] = sum(int(np.isfinite(Z[s + "_open"][i]) and Z[s][3][i, t - 1] > Z[s + "_open"][i]) for s in SECT)
    out = {"days": days, "TG": TG, "fo5": fo5, "mkt": mkt, "sec": sec, "brv": bv}
    for inst in ("SPY", "IWM"):
        A = Z[inst]; o = Z[inst + "_open"]; pc = Z[inst + "_pc"]
        r1 = np.full((D, len(TG)), np.nan); rp = np.full((D, len(TG)), np.nan)
        for i in range(D):
            for q, t in enumerate(TG):
                r1[i, q], rp[i, q] = h1_trade(A[:, i], o[i], pc[i], t)
        out[inst + "_r1"] = r1; out[inst + "_rp"] = rp
    out["biw"] = Z["biw"]
    np.savez(W / "sig.npz", **out)
    h1 = mkt.any(1); s3m = (mkt & (sec >= 8)).any(1)
    per = pd.Series(days).map(lambda d: "FIT" if (("2024-10" <= d[:7] <= "2024-10") or ("2025-03" <= d[:7] <= "2025-09"))
                              else "CHECK" if d >= "2025-10-01" else "T2")
    print(pd.DataFrame({"per": per, "h1": h1, "s3mkt": s3m}).groupby("per").agg(["sum", "count"]))
