"""RD2-idx-cont-closeentry-2R-long - BDI reddit1021 (Reddit "untouched levels + 5m fib retrace"), NEAR-MISS (train avg R <= 0), NOT A CANDIDATE.
Continuation: a large-body 5m candle (body >= 60% of range, range >= 1.5x 5m ATR, volume > previous bar) closes through an untouched level; enter at the candle close instead of waiting for the retrace.
Entry at the close of the trigger candle itself (no retrace wait) - the LabStrategy-native form. Stop = the trigger candle's far end + max($0.01, 2% of its range); target = 2.0x the
entry-to-stop risk (structural GEOM "S" with target_price); flat 15:55. First signal of the day only (refire: false).
Levels: OR (09:30-09:45 H/L, from the frame's own 09:35-09:45 rows), PD (prior regular session H/L, from dist_pdh_atr /
dist_pdl_atr x atr_d), SW (today's 5-minute pivots, 2 bars each side). PM (04:00-09:30) and AH (prior 16:00-20:00)
levels are used only when the frame carries pm_high / pm_low / ah_high / ah_low columns - no such live context
exists yet (it would need a new lab_context field fed from extended-hours bars).
Open history, production costs, 1-minute simulator:
- scan form (entry at the candle close, one position at a time), this side: train n 67 -0.0964R t -0.51; valid n 50 0.0315R t 0.14
- this module as runnable now (OR/PD/SW levels): train n 60 -0.0791R t -0.39; valid n 48 0.0155R t 0.07
- this module with PM/AH context columns: train n 67 -0.0964R t -0.51; valid n 49 0.0542R t 0.24
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "long"          # LabStrategy needs one side per module; the other side is a separate module
GEOM = "S"
WINDOW = (950, 1140)
SYMBOLS = ['SPY', 'QQQ']
LAYERS = ['continuation 5m candle through an untouched level (OR/PD/SW)', 'candle range >= 1.5 x 5m ATR', 'volume > previous 5m bar', "entry at the trigger candle's close", 'trigger candle closes 3..23 (bar index, 3 = 09:50, 23 = 11:30)', 'stop beyond the candle, target 2.0R, flat 15:55', 'first signal of the day']
CFG = {'type': 0, 'k': 1.5, 'vol': 1, 'fresh': 1, 'trend': 0, 'fib': 0.5, 'mult': 2.0, 'fammask': 31, 'side_only': 1, 'klo': 3, 'khi': 23, 'entry': 'close'}   # type 0 continuation / 1 reversal, k, vol 0 off / 1 > prev / 2 > 1.5x prev, fresh, trend 0 / 1 vwap, ...

_PRIO = {0: 3, 1: 1, 2: 2, 3: 0, 4: 4}      # family -> priority (PD, PM, AH, OR, SW)
_CACHE = {}


def _kidx(tod):
    t = np.asarray(tod, int)
    return ((t // 100) * 60 + t % 100 - 570) // 5 - 1          # bar close 09:35 -> 0, 09:50 -> 3, 11:30 -> 23


def _day_plan(g):
    """One symbol-day of frame rows (sorted by tod). Returns {row position: (side, stop)} for the signal row."""
    c = CFG
    n = 78
    K = _kidx(g["tod"].to_numpy())
    H = np.full(n, np.nan); L = np.full(n, np.nan); C = np.full(n, np.nan); V = np.full(n, np.nan)
    A = np.full(n, np.nan); VW = np.full(n, np.nan); pos = np.full(n, -1)
    ok = (K >= 0) & (K < n)
    H[K[ok]] = g["high"].to_numpy(float)[ok]; L[K[ok]] = g["low"].to_numpy(float)[ok]
    C[K[ok]] = g["close"].to_numpy(float)[ok]
    V[K[ok]] = g["volume"].to_numpy(float)[ok] if "volume" in g else np.nan
    A[K[ok]] = (g["atrPct"].to_numpy(float) * g["close"].to_numpy(float) / 100)[ok]
    VW[K[ok]] = np.sign(g["vwapDistPct"].to_numpy(float))[ok] if "vwapDistPct" in g else 0
    pos[K[ok]] = np.flatnonzero(ok)
    lv, fam, avail, used = [], [], [], []

    def add(x, f, a):
        if np.isfinite(x) and (c["fammask"] >> f) & 1:
            lv.append(float(x)); fam.append(f); avail.append(a); used.append(False)
    orh, orl = np.nanmax(H[0:3]) if np.isfinite(H[0:3]).all() else np.nan, np.nanmin(L[0:3]) if np.isfinite(L[0:3]).all() else np.nan
    first = lambda col: (g[col].to_numpy(float)[np.isfinite(g[col].to_numpy(float))][:1] if col in g else np.array([]))
    pdh = pdl = np.nan
    if "dist_pdh_atr" in g and "atr_d" in g:
        x = (g["close"] + g["dist_pdh_atr"] * g["atr_d"]).to_numpy(float); x = x[np.isfinite(x)]
        pdh = x[0] if len(x) else np.nan
        x = (g["close"] - g["dist_pdl_atr"] * g["atr_d"]).to_numpy(float); x = x[np.isfinite(x)]
        pdl = x[0] if len(x) else np.nan
    pm = [first("pm_high"), first("pm_low"), first("ah_high"), first("ah_low")]
    add(orh, 0, 3); add(orl, 0, 3)
    for x, f in ((pm[0], 1), (pm[1], 1), (pm[2], 2), (pm[3], 2)):
        add(x[0] if len(x) else np.nan, f, 0)
    add(pdh, 3, 0); add(pdl, 3, 0)
    out = {}
    for k in range(3, 24):
        j = k - 3
        if j >= 2 and (c["fammask"] >> 4) & 1 and len(lv) < 30:
            hj, lj = H[j], L[j]
            if np.isfinite(hj) and hj > H[j - 1] and hj > H[j - 2] and hj > H[j + 1] and hj > H[j + 2]:
                lv.append(hj); fam.append(4); avail.append(j + 3); used.append(False)
            if np.isfinite(lj) and lj < L[j - 1] and lj < L[j - 2] and lj < L[j + 1] and lj < L[j + 2]:
                lv.append(lj); fam.append(4); avail.append(j + 3); used.append(False)
        if k < c["klo"] or k > c["khi"]:
            continue
        h, l, cl, pc, v, a = H[k], L[k], C[k], C[k - 1], V[k], A[k - 1]
        if not (np.isfinite(h) and np.isfinite(pc) and np.isfinite(a)) or a <= 0:
            continue
        rng = h - l
        if rng <= 0 or rng < c["k"] * a:
            continue
        if c["vol"] == 1 and not (v > V[k - 1]):
            continue
        if c["vol"] == 2 and not (v > 1.5 * V[k - 1]):
            continue
        side, bestp = 0, 99
        for q in range(len(lv)):
            if used[q] or avail[q] > k:
                continue
            L0 = lv[q]
            hh, ll = H[avail[q]:k], L[avail[q]:k]
            above = not (np.nan_to_num(hh, nan=-np.inf) >= L0).any()
            below = not (np.nan_to_num(ll, nan=np.inf) <= L0).any()
            if not c["fresh"]:
                above, below = pc < L0, pc > L0
            s = 0
            if c["type"] == 0:
                if abs(cl - pc) >= 0.6 * rng:
                    if above and cl > L0 and cl > pc:
                        s = 1
                    elif below and cl < L0 and cl < pc:
                        s = -1
            else:
                if above and h > L0 and cl < L0 and cl <= l + 0.35 * rng:
                    s = -1
                elif below and l < L0 and cl > L0 and cl >= h - 0.35 * rng:
                    s = 1
            if s and (side == 0 or (_PRIO[fam[q]] < bestp and s == side)):
                side, bestp = s, _PRIO[fam[q]]
        if side == 0:
            continue
        for q in range(len(lv)):
            if avail[q] <= k and l <= lv[q] <= h:
                used[q] = True
        if c["trend"] == 1 and VW[k] != side:
            continue
        if c["side_only"] and side != c["side_only"]:
            continue
        buf = max(0.01, 0.02 * rng)
        stop = l - buf if side > 0 else h + buf
        if c["entry"] == "close":       # market entry at the trigger candle's close (no retrace)
            if pos[k] >= 0 and side * (cl - stop) > 1e-6 * cl:
                out[int(pos[k])] = (side, stop)
                return out
            continue
        e = h - c["fib"] * rng if side > 0 else l + c["fib"] * rng
        for kk in (k + 1, k + 2):
            if kk < n and np.isfinite(L[kk]) and ((side > 0 and L[kk] < e) or (side < 0 and H[kk] > e)):
                if side * (C[kk] - stop) > 1e-6 * C[kk] and pos[kk] >= 0:
                    out[int(pos[kk])] = (side, stop)
                    return out          # first filled signal of the day
                break
    return out


def _plans(df):
    key = (id(df), len(df))
    if key in _CACHE:
        return _CACHE[key]
    if len(_CACHE) > 64:
        _CACHE.clear()
    sig = np.zeros(len(df), bool)
    stop = np.full(len(df), np.nan)
    if "date" in df and "symbol" in df:
        keys = df["symbol"].astype(str) + "|" + df["date"].astype(str)
    elif "date" in df:
        keys = df["date"].astype(str)
    else:
        keys = pd.Series(np.zeros(len(df)), index=df.index)
    for _, idx in pd.Series(np.arange(len(df))).groupby(keys.to_numpy()).groups.items():
        rows = np.asarray(sorted(idx, key=lambda r: df["tod"].iat[r]))
        g = df.iloc[rows]
        for p, (s, st) in _day_plan(g).items():
            sig[rows[p]] = True
            stop[rows[p]] = st
    _CACHE[key] = (sig, stop)
    return sig, stop


def mask(df) -> np.ndarray:
    need = {"high", "low", "close", "tod", "atrPct", "volume"}
    if not need.issubset(df.columns):
        return np.zeros(len(df), dtype=bool)
    sig, _ = _plans(df)
    tod = df["tod"].to_numpy(float)
    return sig & (tod >= WINDOW[0]) & (tod <= WINDOW[1])


def stop_price(f, i):
    _, stop = _plans(f)
    return float(stop[i])


def target_price(f, i, stop):
    px = float(f["close"].iloc[i])
    return px + CFG["mult"] * (px - stop)
