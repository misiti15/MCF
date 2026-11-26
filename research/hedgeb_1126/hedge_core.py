"""HEDGE-B overlay (PREREG.md): target h* = -sign(E) max(|E| - B, 0) R per +1% SPY, next-bar fill, 2R band, flatten when
the book is empty and at the 15:55 bar close, SPY/IWM split f = |E_IWM| / (|E| + |E_IWM|), 1 bp per side + SEC/TAF/CAT.
Educational only - not financial advice."""
import numpy as np

BAND, FLAT_K = 2.0, 385
SIDE_BP, SEC, CAT, TAF = 1e-4, 20.60e-6, 0.00005, 0.000195


def hedge(E, EI, ES, GR, OPN, S, I, biw, B):
    """overlay for one day. S, I = 390 closes. Returns gross, cost, rebalances, traded notional (R$), peak |V|,
    peak gross (lots + hedge), per-setup net allocation."""
    qs = qi = h = 0.0; gross = cost = tr = 0.0; nreb = 0; pkv = 0.0; pkg = 0.0
    N = ES.shape[0]; w = np.zeros(N); alloc = np.zeros(N)
    for k in range(1, 390):
        p = qs * (S[k] - S[k - 1]) + qi * (I[k] - I[k - 1])
        gross += p; alloc += w * p
        if k > FLAT_K:
            continue
        e = E[k - 1]
        if k == FLAT_K or not OPN[k - 1]:
            ht = 0.0; go = h != 0.0
        else:
            ht = -np.sign(e) * max(abs(e) - B, 0.0); go = abs(ht - h) >= BAND
        if go:
            if ht != 0.0:
                ei = abs(EI[k - 1]); f = ei / (abs(e) + ei) if abs(e) + ei > 0 else 0.0
                nqs = 100.0 * (1 - f) * ht / S[k]; nqi = 100.0 * f * ht / biw / I[k]
                w = ES[:, k - 1] / e
            else:
                nqs = nqi = 0.0
            c = 0.0
            for dq, px in ((nqs - qs, S[k]), (nqi - qi, I[k])):
                if dq == 0.0:
                    continue
                v = abs(dq) * px; tr += v
                c += v * SIDE_BP + CAT * abs(dq) + ((v * SEC + TAF * abs(dq)) if dq < 0 else 0.0)
            cost += c; alloc -= w * c; nreb += 1
            qs, qi, h = nqs, nqi, ht
        hv = abs(qs * S[k]) + abs(qi * I[k])
        pkv = max(pkv, hv); pkg = max(pkg, GR[k] + hv)
    return gross, cost, nreb, tr, pkv, pkg, alloc
