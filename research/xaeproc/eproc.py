"""XA-EPROC (guild Builder, Lead lead-20261110-0500-3): anytime-valid forward monitor for journal-only shadows.

A forward shadow is looked at every session; re-running a t-test each day inflates false positives (optional stopping).
An e-process stays valid at EVERY look: under H0 its expected value is <= 1, so by Ville's inequality
P(it ever reaches 1/alpha) <= alpha - peek daily, stop whenever it crosses.

Test: H0 "mean daily delta <= 0" (the rule does not help), on the per-session delta x_t = R(rule) - R(baseline) for the
shadow (or any paired daily series). Values are clipped to [-c, c] and scaled to [-1, 1] (c = a fixed cap declared in
the shadow's spec BEFORE it starts, e.g. 10R per day; clipping makes the test conservative, never invalid).
Betting martingale (Waudby-Smith & Ramdas 2023, predictable plug-in): K_t = prod_i (1 + lam_i y_i), lam_i chosen from
data BEFORE day i only: lam_i = clip(m / (v + m^2), 0, 0.5) with m, v the running mean / variance of y_1..y_{i-1}
(prior m 0, v 1/4). EDGE alarm when K_t >= 1/alpha. The mirror process on -y gives a HARM alarm ("rule hurts").
Report K_t daily next to the plain day-clustered t; a shadow 'holds' only when it clears its rule-18 / BAR90 bar AND
(if pre-declared) the e-process alarm.
    python eproc.py --selftest
    python eproc.py <csv> <date col> <delta col> <cap> [alpha]       (one row per session, in date order)
Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd


def eprocess(x, cap, alpha=0.05):
    y = np.clip(np.asarray(x, float), -cap, cap) / cap
    out = []
    for sign in (1, -1):
        z = sign * y; K, m, s2, n, path = 1.0, 0.0, 0.25, 0, []
        for zi in z:
            lam = min(max(m / (s2 + m * m), 0.0), 0.5) if s2 + m * m > 0 else 0.0
            K *= 1 + lam * zi; path.append(K)
            n += 1; d = zi - m; m += d / n; s2 = s2 + (d * (zi - m) - s2) / (n + 1)   # running mean / shrunk variance
        out.append(np.array(path))
    up, dn = out
    hit = lambda p: int(np.argmax(p >= 1 / alpha)) + 1 if (p >= 1 / alpha).any() else None
    return dict(n=len(y), K_edge=round(float(up[-1]), 3), K_harm=round(float(dn[-1]), 3), edge_alarm_day=hit(up),
                harm_alarm_day=hit(dn), threshold=1 / alpha, path_edge=up, path_harm=dn)


def selftest():
    rng = np.random.default_rng(7)
    fp = np.mean([eprocess(rng.normal(0, 3, 120), 10)["edge_alarm_day"] is not None for _ in range(2000)])
    tp = np.mean([eprocess(rng.normal(0.8, 3, 120), 10)["edge_alarm_day"] is not None for _ in range(500)])
    # compare: daily-peeked t-test at 1.96 on the same nulls
    def peek_t(x):
        for k in range(10, len(x) + 1):
            s = x[:k]; t = s.mean() / (s.std(ddof=1) / np.sqrt(k))
            if t >= 1.645: return True
        return False
    fpt = np.mean([peek_t(rng.normal(0, 3, 120)) for _ in range(2000)])
    assert fp <= 0.05, fp
    assert tp >= 0.5, tp
    print(f"selftest ok: null false-alarm rate {fp:.3f} over 2,000 x 120-session runs, peeking daily (<= 0.05); "
          f"daily-peeked one-sided t-test on the same nulls {fpt:.3f}; power at +0.8R/day (sd 3) {tp:.2f}")


if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest(); sys.exit()
    f, dc, vc, cap = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]); a = float(sys.argv[5]) if len(sys.argv) > 5 else .05
    d = pd.read_csv(f).sort_values(dc)
    r = eprocess(d[vc].to_numpy(), cap, a)
    print({k: v for k, v in r.items() if not k.startswith("path")})
    print("Educational only - not financial advice.")
