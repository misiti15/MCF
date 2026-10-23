"""pod-smb-big-dog-consolidation-above-vwap-break-long - Big Dog consolidation above VWAP after an opening drive (LONG).

Source: SMB Capital YouTube / SMB Training 'big dog consolidation' trader talk ('number one setup I've focused on for
two years'); SMB PlayBook Checkup 'Opening Drive - Consolidation Above VWAP' ($K).
URL: https://www.smbtraining.com/blog/2014/page/37

VARIANT of 'Relative-volume breakout from a 5-minute consolidation' (generic, failed). Stated changes: in-play
opening-drive days only, a longer box held entirely above VWAP, and a volume dry-up gate inside the box. Not the SMB
Opening Drive first-pullback setup already tested: this enters on a breakout of a time-boxed range, not on a pullback.

Data: the 09:30-10:00 bars (open, high, low, close, volume) and raw 5m volume come from the 1-minute vendor bars (helper
_smbv5_bars; the locked block is never read). rvol at 10:00 = 09:30-10:00 volume / its mean over the 20 prior sessions
(min 10). ATR14(5m) = atrPct x close, VWAP = close / (1 + vwapDistPct%) (frame).

Rules (plain English):
  1. Opening drive: close(10:00) - open(09:30) >= 1.5 x ATR14(5m) x sqrt(6) (ATR5 at the 10:00 bar), and the 10:00
     close is in the top 30% of the 09:30-10:00 range.
  2. rvol at 10:00 >= 2.
  3. Box: >= 9 consecutive 5m bars (45+ min), all starting 10:15 or later and ending by 13:30, ending on the bar before
     i; box height (max high - min low) <= 35% of the opening-drive move; every box bar's low above its VWAP. The
     longest box that passes every rule is used.
  4. Dry-up: mean box volume <= 0.7 x the mean volume of the six 09:30-10:00 bars.
  5. Breakout bar i closes above the box high with volume >= 1.5 x the box mean volume.
  Entry: next bar open (scorer: close_i). Stop (GEOM S): the higher of box low and VWAP_i, minus 0.1 x ATR14(5m).
  Target: measured move, box high + 2 x box height; else flat 15:55. Costs in (scorer). 1 config, no tweak.
Educational only - not financial advice."""
import numba
import numpy as np

import _smbv5_bars as V

SIDE = "long"
GEOM = "S"
WINDOW = (1105, 1335)
LAYERS = ["09:30-10:00 drive >= 1.5 ATR5 x sqrt(6), close in top 30%", "rvol at 10:00 >= 2",
          ">= 9-bar box 10:15-13:30, height <= 35% of drive, lows above VWAP",
          "box mean volume <= 0.7 x drive mean volume", "close above box high on >= 1.5x box volume",
          "stop max(box low, VWAP) - 0.1 ATR5, target box high + 2 x height"]
_STASH = {}
_C = {}


def _ctx():
    if "c" in _C:
        return _C["c"]
    d = V.dayagg()
    d = d[(d["rv1000"] >= 2) & (d["c1000"] > d["o935"]) & (d["dr_h"] > d["dr_l"])]
    d = d[(d["c1000"] - d["dr_l"]) >= 0.7 * (d["dr_h"] - d["dr_l"])]
    d = d[["symbol", "date", "o935", "c1000", "dr_vavg"]]
    E = V.evbars()
    E = E.merge(d[["symbol", "date"]], on=["symbol", "date"], how="inner")[["symbol", "date", "tod", "v"]]
    _C["c"] = (d, E)
    return _C["c"]


@numba.njit(cache=False)
def _kernel(b, e, o935, c1000, dva, tod, c, h, l, vd, ap, v):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if not (o935[s] == o935[s] and dva[s] > 0):
            continue
        a10 = np.nan
        for k in range(i0, i1):
            if tod[k] == 1000:
                a10 = ap[k] / 100.0 * c[k]
                break
        move = c1000[s] - o935[s]
        if not (a10 > 0 and move >= 1.5 * a10 * np.sqrt(6.0)):
            continue
        done = False
        for i in range(i0, i1):
            if done:
                break
            if tod[i] < 1105 or tod[i] > 1335 or not (v[i] == v[i]):
                continue
            # box ends at i-1; start j: longest valid first
            js = i - 1
            while js - 1 >= i0 and tod[js - 1] >= 1020:
                js -= 1
            for j in range(js, i - 8):
                bh = -1e18
                bl = 1e18
                vs = 0.0
                ok = True
                for k in range(j, i):
                    vw = c[k] / (1.0 + vd[k] / 100.0)
                    if not (l[k] > vw) or not (v[k] == v[k]):
                        ok = False
                        break
                    bh = max(bh, h[k])
                    bl = min(bl, l[k])
                    vs += v[k]
                if not ok:
                    continue
                nb = i - j
                bav = vs / nb
                if not (bh - bl <= 0.35 * move and bav <= 0.7 * dva[s]):
                    continue
                if c[i] > bh and v[i] >= 1.5 * bav:
                    a5 = ap[i] / 100.0 * c[i]
                    vwi = c[i] / (1.0 + vd[i] / 100.0)
                    sp = max(bl, vwi) - 0.1 * a5
                    tp = bh + 2.0 * (bh - bl)
                    if sp < c[i] and tp > c[i]:
                        m[i] = True
                        stop[i] = sp
                        tgt[i] = tp
                        done = True
                break
    return m, stop, tgt


def compute(df):
    n = len(df)
    z = (np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan))
    if n == 0:
        return z
    try:
        d, E = _ctx()
    except Exception:  # noqa: BLE001 - no cache -> no trades
        return z
    sym, dat, b, e = V.keys(df)
    g = V.segmap(sym, dat, b, d, ["o935", "c1000", "dr_vavg"])
    r = V.rowmap(df, E, ["v"])
    f = lambda k: df[k].to_numpy(float)
    return _kernel(b, e, g["o935"], g["c1000"], g["dr_vavg"], df["tod"].to_numpy(np.int64), f("close"), f("high"),
                   f("low"), f("vwapDistPct"), f("atrPct"), r["v"])


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
