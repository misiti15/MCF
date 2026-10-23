"""pod-wt-bull-flag-breakout-or-bailout-long-live - LIVE copy of
research/bdi/pod1022/modules/pod-wt-bull-flag-breakout-or-bailout-long.py (owner 2026-10-23). The research file stays
unchanged.

Live adaptation of the ENTRY (no rule change): the pole / flag search and the EMA9 seed use only bars closing at or
after 09:50, as the scored history frames did (they start at the 09:50 bar; the live frame also carries 09:35-09:45).
On the history frames this is a no-op.

Live adaptation of the EXIT (stated difference, re-scored): the live LabStrategy has no 'S+ts2' geometry, so the config
entry runs `geom: S` (stop flag low - 0.02 ATR, target flag high + pole, flat 15:55) with the runner's existing trade
management: `be_at_r: 0.5` (stop to entry once +0.5R, as scored) and `time_stop_min: 10` + `time_stop_min_r: 0.01`
(the bailout: exit after 10 minutes = 2 bars when the trade has not gone +0.01R). The runner's time stop is measured
from the entry price, not from the entry bar's high, so BAILOUT_REF_R = 0.01 below makes the scorer use the same
reference (score_batch.py). Re-score on the open history, costs in (2026-10-23): train 756 trades +0.141R (t 5.88),
valid 40 trades +0.076R (t 0.40), best day 2025-04-09 = 81% of R; the research exit (entry bar's high) scored
+0.108R / +0.113R with the same 796 entries. Same entries, different bailout reference.

ORIGINAL DOCSTRING:
pod-wt-bull-flag-breakout-or-bailout-long - Bull flag with Ross Cameron's 'breakout or bailout' exit (exit if no
new high within 2 bars) (LONG).

Source: Warrior Trading / Ross Cameron, 'breakout or bailout' trade-management rule applied to bull-flag entries
(Warrior Trading YouTube small-account lessons). Not re-fetched this round.
URL: https://www.youtube.com/@DaytradeWarrior

VARIANT of bdi-reddit-bull-flag-pole (the reddit R08 bull flag failed). The trigger stays the same; the stated change
is the EXIT LOGIC.

Rules (plain English):
  1. Pole: bars P-L+1..P (L = 1, 2 or 3; the shortest that passes) rise >= 1.0 x atr_d (high of P - lowest low of
     those bars) with mean volumeRatio >= 1.5, and bar P's high is the running HOD.
  2. Flag: the F = 2-6 bars after P (P+1 .. prior bar): lowest low retraces <= 50% of the pole, mean volumeRatio
     <= 0.7 x the pole mean, every close >= EMA9 - 0.05 x atr_d and above session VWAP.
  3. This bar closes above the flag high (highest high of the flag bars).
  Entry: that close, bar close 10:00-14:30. Stop: flag low - 0.02 x atr_d. Target: flag high + pole height.
  Exits (GEOM 'S+ts2', added to the scorer for this idea): BAILOUT - if neither of the next 2 bars makes a high above
  this bar's high, exit at the close of the 2nd bar; once the trade has been +0.5R the stop moves to break-even;
  flat 15:55. The '-S' file is the same trigger with the plain structural exit (no bailout, no break-even), so the
  effect of the exit change is visible.
Frame note: EMA9 is on the day's 5-minute closes seeded at the 09:50 close; the pole must be on frame bars.
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S+ts2"
BAILOUT_BARS = 2
BE_AT_R = 0.5
BAILOUT_REF_R = 0.01   # live: bailout reference = entry + 0.01R (runner time_stop_min_r), see above
WINDOW = (1000, 1430)
LAYERS = ["pole >= 1.0 ATR in <= 3 bars, vr >= 1.5, ends at HOD", "2-6 bar flag, retrace <= 50%, vr <= 0.7 x pole",
          "flag closes >= EMA9 - 0.05 ATR and above VWAP", "close > flag high",
          "stop flag low - 0.02 ATR, target flag high + pole", "bailout after 2 bars without a new high, BE at +0.5R",
          "10:00-14:30"]

import numba
import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _segments(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _base(df):
    k = _key(df)
    c = _f(df, "close")
    atr = _f(df, "atr_d")
    b = dict(k=k, tod=df["tod"].to_numpy(np.int64), c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr)
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr          # running low of day (includes 09:30-09:45)
    b["opn"] = c / (1 + _f(df, "fromOpen") / 100)        # today's open
    b["pc"] = b["opn"] / (1 + _f(df, "gap") / 100)        # prior close
    b["vwap"] = c / (1 + _f(df, "vwapDistPct") / 100)
    return b


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None:
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, hod, vw, atr, vr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    ema = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        ev = c[i0]
        for i in range(i0, i1):
            ev = ev + (2.0 / 10.0) * (c[i] - ev)
            ema[i] = ev
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (a > 0):
                continue
            for F in range(2, 7):
                P = i - 1 - F
                if P < i0:
                    break
                if not (h[P] >= hod[P] - 1e-6 * c[P]):
                    continue
                ph = 0.0
                pm = 0.0
                found = False
                for L in range(1, 4):
                    if P - L + 1 < i0:
                        break
                    lo = 1e18
                    vs = 0.0
                    for t in range(P - L + 1, P + 1):
                        lo = min(lo, l[t])
                        vs += vr[t]
                    if h[P] - lo >= 1.0 * a and vs / L >= 1.5:
                        ph = h[P] - lo
                        pm = vs / L
                        found = True
                        break
                if not found:
                    continue
                fh = -1e18
                fl = 1e18
                fv = 0.0
                ok = True
                for t in range(P + 1, i):
                    fh = max(fh, h[t])
                    fl = min(fl, l[t])
                    fv += vr[t]
                    if not (c[t] >= ema[t] - 0.05 * a and c[t] > vw[t]):
                        ok = False
                if not ok or h[P] - fl > 0.5 * ph or fv / F > 0.7 * pm or not (c[i] > fh):
                    continue
                m[i] = True
                stop[i] = fl - 0.02 * a
                tgt[i] = fh + ph
                break
    return m, stop, tgt


def _ident(df):
    """LIVE: the LabStrategy frame is one symbol-day indexed by bar start, without symbol / date columns; add them
    (one group) so the research code's symbol-day keys work unchanged. History frames already carry them."""
    if "symbol" in df and "date" in df:
        return df
    g = df.copy()
    if "symbol" not in g:
        g["symbol"] = "_"
    if "date" not in g:
        g["date"] = [str(x) for x in pd.DatetimeIndex(df.index).date]
    return g


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    keep = df["tod"].to_numpy(np.int64) >= 950     # LIVE: as the history frames (start at the 09:50 bar)
    if not keep.all() or "symbol" not in df or "date" not in df:
        pos = np.flatnonzero(keep)
        sub = _ident(df.iloc[pos])
        m_sub = mask(sub)
        st_sub, tg_sub = _ST.pop(id(sub), (np.full(len(sub), np.nan), np.full(len(sub), np.nan)))
        stop, tgt = np.full(len(df), np.nan), np.full(len(df), np.nan)
        stop[pos], tgt[pos] = st_sub, tg_sub
        z[pos] = m_sub
        _ST.clear()
        _ST[id(df)] = (stop, tgt)
        return z
    b = _base(df)
    bb, ee = _segments(b["k"])
    m, stop, tgt = _kern(bb, ee, b["tod"], b["c"], b["h"], b["l"], b["hod"], b["vwap"], b["atr"],
                         _f(df, "volumeRatio"), WINDOW[0], WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
