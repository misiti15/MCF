"""Volume II pass: features2 columns + 9-EMA trail exits, for the same rows as build.py (train+valid dates only).
Reads data/cache/1Min with timestamp < 2026-09-16. Writes research/bdi/videos/data/parts2/<SYM>.parquet (git-ignored).
New exits (R = 0.25 x atr_d, entry at the next 1-minute open, 1c+1bps per side, +2c stops, flat at 15:55):
  c9      exit at the next open after a 5-minute close beyond EMA9; 2R hard stop
  trail9  stop starts 1c beyond the signal candle's extreme and trails candle by candle to each later completed
          5-minute bar's low (long) / high (short); plus the c9 close exit (BKTraders: "until a full candle closes beyond")
Anchors (chosen from sessions before the day): pwh/pwl = highest-high / lowest-low 1-minute bar of the previous calendar
week; gap = open bar of the latest prior session with abs(gap) >= 2%; qop = open bar of the first session of the day's
calendar quarter if it is before the day, else the cache start (2026-06-15). No earnings anchor (no earnings calendar).
Usage: python research/bdi/videos/build2.py [--test-causal N]      Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, str(Path(__file__).parent))
from build import CACHE, FIRST, SLIP_BPS, SLIP_C, STOP_C, load_symbol, sim  # noqa: E402
from features2 import day_features2  # noqa: E402

OUT = Path("research/bdi/videos/data/parts2")


@njit(cache=True)
def sim_trail(o, h, l, c, entries, sigbar, side, init, m_end, l5, h5, flags, tend, R):
    out = np.full(len(entries), np.nan)
    nm = len(o)
    for k in range(len(entries)):
        e = entries[k]
        if e < 0 or e >= tend or not (R > 0):
            continue
        fill = o[e] + side * (o[e] * SLIP_BPS + SLIP_C)
        st = init[k]
        kb = sigbar[k] + 1
        ex = np.nan
        is_stop = False
        for t in range(e, tend):
            while kb < len(m_end) and m_end[kb] < t:
                st = max(st, l5[kb] - 0.01) if side == 1 else min(st, h5[kb] + 0.01)
                kb += 1
            if (side == 1 and l[t] <= st) or (side == -1 and h[t] >= st):
                ex = min(o[t], st) if side == 1 else max(o[t], st)
                is_stop = True
                break
            if flags[t]:
                ex = o[t + 1] if t + 1 < nm else c[t]
                break
        if ex != ex:
            ex = o[tend] if tend < nm else c[nm - 1]
        net = ex - side * (ex * SLIP_BPS + SLIP_C + (STOP_C if is_stop else 0.0))
        out[k] = side * (net - fill) / R
    return out


def one(path, check_causal=False):
    try:
        m = load_symbol(path)
    except Exception:
        return None
    if len(m) < 2000:
        return None
    dates = np.array(m.index.date)
    days = sorted(set(dates))
    daily = m.groupby(dates).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"))
    pc = daily["close"].shift(1)
    tr = pd.concat([daily.high - daily.low, (daily.high - pc).abs(), (daily.low - pc).abs()], axis=1).max(axis=1)
    atr_lab = tr.rolling(14, min_periods=10).mean().shift(1)
    gapp = (daily.open / pc - 1) * 100
    first_pos = {d: int(np.searchsorted(dates, d)) for d in days}
    d5all = m.resample("5min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna(subset=["open"])
    d5d = np.array(d5all.index.date)
    hiv, lov = m["high"].to_numpy(), m["low"].to_numpy()
    out = []
    for i, d in enumerate(days):
        if d < FIRST or i == 0:
            continue
        a0 = first_pos[d]
        b1 = m.iloc[a0: a0 + int((dates[a0:a0 + 400] == d).sum())]
        if len(b1) < 60:
            continue
        hist = m.iloc[:a0]
        p1 = m.iloc[first_pos[days[i - 1]]:a0]
        atr = float(atr_lab.get(d, np.nan))
        # anchors (positions in hist)
        anc = {}
        wk = pd.Timestamp(d).isocalendar()
        pw = [x for x in days[:i] if pd.Timestamp(x).isocalendar()[:2] == (pd.Timestamp(d) - pd.Timedelta(days=7)).isocalendar()[:2]]
        if pw:
            s0, s1 = first_pos[pw[0]], first_pos[days[days.index(pw[-1]) + 1]]
            anc["pwh"] = s0 + int(np.argmax(hiv[s0:s1]))
            anc["pwl"] = s0 + int(np.argmin(lov[s0:s1]))
        gd = [x for x in days[1:i] if abs(gapp.get(x, 0)) >= 2]
        if gd:
            anc["gap"] = first_pos[gd[-1]]
        q0 = pd.Timestamp(year=d.year, month=3 * ((d.month - 1) // 3) + 1, day=1).date()
        qd = [x for x in days[:i] if x >= q0]
        anc["qop"] = first_pos[qd[0]] if qd else 0
        del wk
        F = day_features2(b1, hist, p1, atr, anc, float(pc.get(d, np.nan)))
        if F.empty:
            continue
        if check_causal:
            for cut in (25, 70, 150, 260):
                Ft = day_features2(b1.iloc[:cut], hist, p1, atr, anc, float(pc.get(d, np.nan)))
                if len(Ft):
                    for col in F.columns:
                        x, y = F[col].to_numpy(float)[:len(Ft)], Ft[col].to_numpy(float)
                        bad = ~(np.isclose(x, y, rtol=1e-5, atol=1e-6) | (np.isnan(x) & np.isnan(y)))
                        if bad.any():
                            raise AssertionError(f"look-ahead {col} {path.stem} {d} cut {cut}")
        # 9-EMA exits
        jd5 = np.searchsorted(d5d, d)
        prior5 = d5all.iloc[max(0, jd5 - 40): jd5]
        d5 = d5all.iloc[jd5: jd5 + len(F)]
        e9 = pd.concat([prior5, d5])["close"].ewm(span=9, adjust=False).mean().to_numpy()[-len(F):]
        o, h, l, c = (b1[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        mos = (b1.index.hour * 60 + b1.index.minute - 570).to_numpy()
        m_end = np.searchsorted(mos, (d5.index.hour * 60 + d5.index.minute - 570).to_numpy() + 4, side="right") - 1
        nm = len(o)
        tend = int(np.searchsorted(mos, 385))
        R = 0.25 * atr
        ent = (m_end + 1).astype(np.int64)
        ent[ent >= nm] = -1
        c5, l5, h5 = d5.close.to_numpy(float), d5.low.to_numpy(float), d5.high.to_numpy(float)
        entry_px = np.where(ent >= 0, o[np.clip(ent, 0, nm - 1)], np.nan)
        for side, nmx in ((1, "long"), (-1, "short")):
            fl = np.zeros(nm, np.bool_)
            fl[m_end[(c5 < e9) if side == 1 else (c5 > e9)]] = True
            F[f"x_{nmx}_c9"] = sim(o, h, l, c, ent, side, entry_px - side * 2 * R, np.full(len(F), np.nan), np.zeros(1), False,
                                   fl, tend, R).astype(np.float32)
            init = (l5 - 0.01) if side == 1 else (h5 + 0.01)
            F[f"x_{nmx}_trail9"] = sim_trail(o, h, l, c, ent, np.arange(len(F)), side, init, m_end, l5, h5, fl, tend,
                                             R).astype(np.float32)
        end = F.index + pd.Timedelta(minutes=5)
        F["tod"] = (end.hour * 100 + end.minute).astype("int16")
        F = F[(F.tod >= 950) & (F.tod <= 1500)]
        F["date"] = d
        out.append(F.reset_index(drop=True))
    if not out:
        return None
    x = pd.concat(out, ignore_index=True)
    x["symbol"] = path.stem
    OUT.mkdir(parents=True, exist_ok=True)
    x.to_parquet(OUT / f"{path.stem}.parquet", index=False)
    return len(x)


if __name__ == "__main__":
    args = sys.argv[1:]
    files = sorted(CACHE.glob("*.parquet"))
    if "--symbols" in args:
        want = set(args[args.index("--symbols") + 1].split(","))
        files = [f for f in files if f.stem in want]
    if "--test-causal" in args:
        for f in files[:int(args[args.index("--test-causal") + 1])]:
            print(f.stem, one(f, check_causal=True), "rows - causal check passed", flush=True)
        sys.exit(0)
    done = {p.stem for p in OUT.glob("*.parquet")} if OUT.exists() else set()
    files = [f for f in files if f.stem not in done]
    tot = 0
    with Pool(4) as p:
        for k, r in enumerate(p.imap_unordered(one, files, chunksize=2)):
            tot += r or 0
            if k % 50 == 0:
                print(k, len(files), tot, flush=True)
    print("done rows", tot)
