"""pod-cwt2-tagr-peers-green-leader-long - Peers flip green after a weak open: buy the group leader (LONG).

Source: Chat With Traders ep 157 and ep 223 clip, Alex 'Tagger' (@TAGRtrades); records 'Hot-sector leader long when
peers turn green'.
URL: https://chatwithtraders.com

VARIANT of t4-rel-strength / rw-t4 / sector-rs (RS vs SPY or the sector, failed) and ix-leadlag (failed). Stated
change: the trigger is a PEER BREADTH FLIP inside the stock's own group (>= 2 peers cross from red to green on the
day after a weak group open), not a relative-strength level against an index.

Rules (plain English), bars up to the decision bar only; daily values from completed days only:
  1. Group: the sector-ETF map used by rw-t4 (research/rework/web_families/sector_map.json; members = the universe
     names in the frame that day mapped to the same sector ETF). Fallback for names not mapped to a sector (absent,
     or mapped to 'SPY'): the name plus its 5 most correlated universe names on 60-day daily close-to-close returns,
     computed from the 60 completed days before the first day of the scored month (point in time, no lookahead).
     The group needs >= 4 members in the frame that day.
  2. Weak open: at the 09:50 bar, >= 75% of the group members (with a 09:50 bar) are below their prior close
     (prior close = open / (1 + gap), open = close / (1 + fromOpen)).
  3. Flip: by bar t, >= 2 group members other than the candidate were below their prior close at 09:50 and have
     closed a 5-minute bar above it since.
  4. Candidate = the group member with the highest 5-day return (completed days: close D-1 / close D-6 - 1);
     trigger = its own 5-minute close crossing above its prior close (previous bar at or below), volumeRatio >= 1.3.
  5. spy_fo > -0.5.
  Entry: that close, bar close 09:55-11:30. Stop (GEOM S): today's LOD - 0.05 x atr_d. Target: none, hold to 15:55
  (the source holds while the theme is hot; the stated alternative 2R is NOT used). Costs in (scorer).
  No tweak used.
Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (955, 1130)
CONTEXT = ["spy_fo"]
LAYERS = ["group: sector-ETF map (fallback top-5 60d correlation), >= 4 members",
          "09:50: >= 75% of the group below prior close", ">= 2 other members crossed red -> green since 09:50",
          "candidate = highest 5-day return in the group; its close crosses above prior close, volumeRatio >= 1.3",
          "spy_fo > -0.5", "09:55-11:30 ET", "stop LOD - 0.05 ATR, hold to 15:55"]

_ROOT = Path(__file__).resolve().parents[4]
_STASH = {}
_CACHE = {}


def _lib():
    p = str(_ROOT / "research" / "history2y")
    if p not in sys.path:
        sys.path.insert(0, p)
    import lib  # noqa: E402
    return lib


def _smap():
    if "smap" not in _CACHE:
        _CACHE["smap"] = json.loads((_ROOT / "research" / "rework" / "web_families" / "sector_map.json").read_text())
    return _CACHE["smap"]


def _daily():
    if "d" in _CACHE:
        return _CACHE["d"]
    d = _lib().daily()[["symbol", "date", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    _CACHE["d"] = d
    return d


def _ret5():
    if "r5" in _CACHE:
        return _CACHE["r5"]
    d = _daily().copy()
    g = d.groupby("symbol", sort=False)
    dt = pd.to_datetime(d["date"])
    d["r5"] = d["close"] / g["close"].shift(5) - 1
    sp = (dt - dt.groupby(d["symbol"]).shift(5)).dt.days
    d.loc[~(sp <= 10), "r5"] = np.nan
    nd = g["date"].shift(-1)
    ok = (pd.to_datetime(nd) - dt).dt.days <= 5
    o = pd.DataFrame({"symbol": d["symbol"], "date": nd, "r5": d["r5"]})[ok]
    _CACHE["r5"] = o
    return o


def _corr_peers(first_date, syms):
    """Top-5 correlated names per symbol on 60 completed days before first_date (only among syms)."""
    key = ("cp", first_date)
    if key in _CACHE:
        return _CACHE[key]
    d = _daily()
    d = d[(d["date"] < first_date) & d["symbol"].isin(syms)]
    p = d.pivot(index="date", columns="symbol", values="close").sort_index()
    p = p.iloc[-61:]
    r = p.pct_change().iloc[1:]
    r = r.loc[:, r.notna().sum() >= 50]
    out = {}
    if r.shape[1] >= 6 and len(r) >= 50:
        cm = r.corr(min_periods=50).to_numpy().copy()
        np.fill_diagonal(cm, -np.inf)
        cm = np.where(np.isfinite(cm), cm, -np.inf)
        cols = np.array(r.columns)
        top = np.argsort(-cm, axis=1)[:, :5]
        for a, s in enumerate(cols):
            out[s] = list(cols[top[a]])
    _CACHE[key] = out
    return out


def compute(df):
    n = len(df)
    m = np.zeros(n, bool)
    stop = np.full(n, np.nan)
    if n == 0 or "spy_fo" not in df:
        return m, stop, np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr = f("close"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        op = c / (1 + f("fromOpen") / 100)
        pc = op / (1 + f("gap") / 100)
        lod = c - f("dist_lod_atr") * atr
    sym = df["symbol"].astype(str).to_numpy()
    dates = df["date"].to_numpy()
    tod = df["tod"].to_numpy(np.int64)
    vr, spy = f("volumeRatio"), f("spy_fo")
    smap = _smap()
    r5 = _ret5()
    first = min(dates)
    cpeers = _corr_peers(first, set(sym))
    slot = ((tod // 100) * 60 + tod % 100 - (9 * 60 + 50)) // 5          # 0 = 09:50
    T = int(slot.max()) + 1
    above = c > pc
    udates = pd.unique(dates)
    # positions of each date block (frame sorted by symbol, date, tod -> gather by date)
    order = np.argsort(pd.factorize(dates)[0], kind="stable")
    dcode = pd.factorize(dates)[0]
    bounds = np.searchsorted(dcode[order], np.arange(len(udates) + 1))
    r5map = r5.set_index(["symbol", "date"])["r5"]
    for di, dd in enumerate(udates):
        rows = order[bounds[di]:bounds[di + 1]]
        ss = sym[rows]
        us, sidx = np.unique(ss, return_inverse=True)
        S = len(us)
        ab = np.zeros((S, T), bool)
        has = np.zeros((S, T), bool)
        ab[sidx, slot[rows]] = above[rows]
        has[sidx, slot[rows]] = True
        b950 = has[:, 0] & ~ab[:, 0]
        h950 = has[:, 0]
        crossed = b950[:, None] & np.maximum.accumulate(ab & has, axis=1)
        crossed[:, 0] = False
        rv = np.array([r5map.get((s, dd), np.nan) for s in us], float)
        pos = {s: k for k, s in enumerate(us)}
        # groups
        groups = []
        sec = {}
        for k, s in enumerate(us):
            e = smap.get(s)
            if e is not None and e != "SPY":
                sec.setdefault(e, []).append(k)
            else:
                pe = cpeers.get(s)
                if pe:
                    mem = [k] + [pos[p] for p in pe if p in pos]
                    groups.append((k, np.array(mem)))
        for e, mem in sec.items():
            mem = np.array(mem)
            groups.append((None, mem))
        for own, mem in groups:
            if len(mem) < 4:
                continue
            hm = mem[h950[mem]]
            if len(hm) == 0 or b950[hm].mean() < 0.75:
                continue
            rr = rv[mem]
            if not np.isfinite(rr).any():
                continue
            cand = mem[int(np.nanargmax(rr))]
            if own is not None and cand != own:
                continue          # a correlation group only fires for its own anchor name
            others = mem[mem != cand]
            flips = crossed[others].sum(0)
            crow = rows[ss == us[cand]]
            crow = crow[np.argsort(tod[crow])]
            for q in range(1, len(crow)):
                i, p = crow[q], crow[q - 1]
                if tod[i] < WINDOW[0] or tod[i] > WINDOW[1]:
                    continue
                if c[i] > pc[i] and c[p] <= pc[p] and vr[i] >= 1.3 and spy[i] > -0.5 and flips[slot[i]] >= 2:
                    sp = lod[i] - 0.05 * atr[i]
                    if sp < c[i]:
                        m[i] = True
                        stop[i] = sp
                        break
    return m, stop, np.full(n, np.nan)


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

