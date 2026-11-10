"""SC1 (guild Scout plan research/sc1/PLAN.md, frozen 2026-11-09 09:55 ET before any score): event-day gap-and-hold.
Event proxy: |gap| >= G and 09:30-09:55 volume >= 4x the name's prior-20-session norm. Hold test once at bar close T:
above open + session VWAP + still holds half the gap (long; short mirror). Entry next 5-min bar open, stop low of day so
far - 0.05 ATR_d (skip if risk > 0.6 or < 0.10 ATR_d), exit 15:55, trail to the 6-bar low once +1R is reached.
8 configs (G 4/6% x T 10:00/10:30 x side), lineage N 8, BAR90 1.84 on raw t AND C2-excess t.
Controls: C1 failed-hold event gaps same day / T / side (paired by day); C2 same-minute random no-event pool name.
Locked block 2024-11-01..2025-02-28 dropped at every read (asserted).
    python sc1.py > sc1_out.txt          (needs data/cache_hist/1Min with a volume column + research/history2y daily)
    python sc1.py --selftest             (synthetic checks; no data)
Educational only - not financial advice."""
import os, re, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path("/home/user/MCF"); HERE = Path(__file__).resolve().parent
GRID = [(g, T, side) for g in (0.04, 0.06) for T in (1000, 1030) for side in (1, -1)]
N_LINEAGE = 8
# SC1-R rework (plan Amendment 3, frozen before any rework score): longs, gap >= 4%, (T, cap, stop) -> lineage N 12
GRID_R = [(0.04, 1030, 1, 1.0, False), (0.04, 1000, 1, 1.0, False), (0.04, 1030, 1, 0.6, True), (0.04, 1000, 1, 0.6, True)]
REWORK = "--rework" in sys.argv
if REWORK: N_LINEAGE = 12
END_MIN = 570 + 5 * np.arange(1, 79)
END_TOD = END_MIN // 60 * 100 + END_MIN % 60
I = {int(t): i for i, t in enumerate(END_TOD)}
I955, I1555 = I[955], I[1555]
SPREAD_BPS = 4.4e-4; SLIP_PS, SLIP_BPS, STOP_EXTRA = 0.01, 1e-4, 0.02
TOD_COST = ((935, 3.8), (950, 2.1), (1030, 1.4))
VOL_X, MIN_ADV = 4.0, 60e6
# Amendment (2026-11-09 11:45 ET, before any score): no lab ETP list exists, so every ETF / ETN / fund is excluded by name
# (data/universe.csv), plus index ETFs by symbol. Corporate events are the target; leveraged products gap on index moves.
ETP_RE = re.compile(r"\bETF\b|\bETN\b|\bFund\b|ProShares|Direxion|iShares|SPDR|Invesco QQQ|\b[23]X\b|Leveraged|Inverse|"
                    r"\bUltra|\bBear\b|\bBull\b|Daily Target|GraniteShares|Tradr|Defiance|T-Rex|Volatility|VIX|Physical (Gold|Silver)", re.I)
IDX = {"SPY", "QQQ", "IWM", "DIA"}


def tod_mult(tod):
    for edge, m in TOD_COST:
        if tod < edge: return m
    return 1.0


def hold_ok(a, s, iT, pc):
    """hold test at bar iT. a: (78, 6) o h l c v pv. Long: close > open, > VWAP, >= pc + 0.5 (open - pc). Short mirror."""
    o0 = float(a[0, 0]); c = float(a[iT, 3]); v = float(np.nansum(a[:iT + 1, 4])); pv = float(np.nansum(a[:iT + 1, 5]))
    if v <= 0: return False
    vwap = pv / v
    return bool(s * (c - o0) > 0 and s * (c - vwap) > 0 and s * (c - (pc + 0.5 * (o0 - pc))) >= 0)


def stop_level(a, s, iT, atr, vwap_stop=False):
    """LOD/HOD so far -/+ 0.05 ATR (plan), or session VWAP at the signal bar -/+ 0.10 ATR (rework SC1-R)."""
    if vwap_stop:
        v = float(np.nansum(a[:iT + 1, 4])); pv = float(np.nansum(a[:iT + 1, 5]))
        return (pv / v - s * 0.10 * atr) if v > 0 else np.nan
    ext = float(np.nanmin(a[:iT + 1, 2])) if s > 0 else float(np.nanmax(a[:iT + 1, 1]))
    return ext - s * 0.05 * atr


def trade(a, s, iT, atr, spread_mult=1.0, cap=0.6, vwap_stop=False):
    """signal bar iT -> (net R, gross R, kind, entry, cost R, exit bar, stop at exit, R) entering at bar iT+1 open; None if skipped."""
    j = iT + 1
    if j > I1555 or not (atr and np.isfinite(atr) and atr > 0): return None
    e = float(a[j, 0])
    if not np.isfinite(e) or e <= 0: return None
    stop = stop_level(a, s, iT, atr, vwap_stop); R = s * (e - stop)
    if not np.isfinite(R) or R > cap * atr or R < 0.10 * atr: return None
    kind, xp, xb = "time", float(a[I1555, 3]), I1555; hit1 = False
    for i in range(j, I1555 + 1):
        o, h, l, c = (float(x) for x in a[i, :4])
        if i > j and s * (o - stop) <= 0: kind, xp, xb = "stop", o, i; break
        if (s > 0 and l <= stop) or (s < 0 and h >= stop): kind, xp, xb = "stop", stop, i; break
        if s * (c - e) >= R: hit1 = True                                   # +1R on a bar close
        if hit1:                                                           # trail from the next bar, never loosened
            w = a[max(j, i - 5):i + 1]
            tr = float(np.min(w[:, 2])) if s > 0 else float(np.max(w[:, 1]))
            if s * (tr - stop) > 0: stop = tr
    m = tod_mult(int(END_TOD[iT]))
    cost = (SLIP_PS + e * SLIP_BPS) * m + spread_mult * SPREAD_BPS * e * m + SLIP_PS + e * SLIP_BPS + (STOP_EXTRA if kind == "stop" else 0)
    g = s * (xp - e) / R
    return g - cost / R, g, kind, e, cost / R, xb, stop, R


def skip_reason(a, s, iT, atr, cap=0.6, vwap_stop=False):
    """why trade() returned None (Lead lead-20261109-1658-2: log skips by reason)."""
    j = iT + 1
    if j > I1555 or not (atr and np.isfinite(atr) and atr > 0): return "no_bar_or_atr"
    e = float(a[j, 0])
    if not np.isfinite(e) or e <= 0: return "no_bar_or_atr"
    R = s * (e - stop_level(a, s, iT, atr, vwap_stop))
    if not np.isfinite(R): return "no_vwap"
    return f"risk_gt_{cap}atr" if R > cap * atr else ("risk_lt_0.1atr" if R < 0.10 * atr else "other")


def reprice_stop(res, m1, s):
    """Amendment 2 (Skeptic): re-price a 5-min stop fill on 1-min bars. m1: (390, 4) o h l c minutes 09:30..15:59.
    The fill is the stop, or the first touching minute's open when that minute opens through it. Returns (net, gross)."""
    net, g, kind, e, cr, xb, stop, R = res
    if kind != "stop" or m1 is None: return net, g
    for k in range(xb * 5, xb * 5 + 5):
        o, h, l = (float(x) for x in m1[k, :3])
        if not np.isfinite(o): continue
        if (s > 0 and l <= stop) or (s < 0 and h >= stop):
            fill = o if s * (o - stop) <= 0 else stop
            g2 = s * (fill - e) / R
            return net - g + g2, g2
    return net, g


def selftest():
    def day(o=100.0):
        a = np.zeros((78, 6), np.float32); a[:, :4] = o; a[:, 4] = 1000; a[:, 5] = o * 1000; return a
    iT = I[1000]
    # long gap +6% from pc 100: open 106, drifts to 107 by 10:00 -> holds (above open, above VWAP ~106.5, >= 103)
    a = day(106.0); a[3:, :4] = 107.0; a[3:, 5] = 107.0 * 1000; a[1, 2] = 105.5     # entry bar iT+1 opens at 107
    assert hold_ok(a, 1, iT, 100.0)
    b = a.copy(); b[iT, 3] = 105.9; assert not hold_ok(b, 1, iT, 100.0)         # below open
    c = day(106.0); c[1:iT + 1, :4] = 110.0; c[1:iT + 1, 5] = 110.0e3; c[iT, 3] = 106.2
    assert not hold_ok(c, 1, iT, 100.0)                                         # above open but below VWAP (~109.6)
    d = day(94.0); d[3:iT + 1, :4] = 93.0; d[3:iT + 1, 5] = 93.0e3; assert hold_ok(d, -1, iT, 100.0)   # short mirror
    # trade: long, ATR 4; LOD so far 105.5 -> stop 105.3; entry 107 -> R 1.7 (< 0.6*4 = 2.4)
    t = a.copy(); r = trade(t, 1, iT, 4.0)
    assert r is not None and r[2] == "time" and abs(r[1]) < 1e-5, r
    t2 = a.copy(); t2[iT + 3, 2] = 105.0; r = trade(t2, 1, iT, 4.0); assert r[2] == "stop" and abs(r[1] + 1) < 1e-4, r
    t3 = a.copy(); t3[iT + 2:, :4] = 109.0; t3[iT + 10:, :4] = 108.6   # +1R (108.7) on the iT+2 close, then a pullback
    r = trade(t3, 1, iT, 4.0)          # trail climbs to the 6-bar low 109 once bar j leaves the window -> stopped at 109
    assert r[2] == "stop" and abs(r[1] - (109 - 107) / 1.7) < 1e-3, r
    t4 = a.copy(); t4[iT + 2:iT + 4, :4] = 109.0; t4[iT + 4, 2] = 106.0       # pullback before the window clears bar j:
    r = trade(t4, 1, iT, 4.0)          # trail = min(lows incl. bar j 107) = 107 -> stopped at breakeven, not at -1R
    assert r[2] == "stop" and abs(r[1]) < 1e-4, r
    wide = a.copy(); wide[1, 2] = 103.0; assert trade(wide, 1, iT, 4.0) is None  # risk 4.2 > 2.4 -> skip
    assert ETP_RE.search("ProShares UltraPro QQQ") and ETP_RE.search("Direxion Daily Semiconductor Bull 3X Shares")
    assert not ETP_RE.search("Micron Technology, Inc. Common Stock") and not ETP_RE.search("Glaukos Corporation")
    m1 = np.full((390, 4), 107.0, np.float32); r = trade(t2, 1, iT, 4.0)
    k0 = r[5] * 5; m1[k0 + 2] = [104.8, 104.9, 104.6, 104.7]                    # 1-min bar opens below the 105.3 stop
    n2, g2 = reprice_stop(r, m1, 1); assert abs(g2 - (104.8 - 107) / 1.7) < 1e-4 and n2 < r[0], (g2, r)
    m1b = np.full((390, 4), 107.0, np.float32); m1b[k0 + 1, 2] = 105.0         # touches intrabar -> stop price kept
    assert abs(reprice_stop(r, m1b, 1)[1] - r[1]) < 1e-6
    vs = stop_level(a, 1, iT, 4.0, True); assert abs(vs - (float(a[:iT + 1, 5].sum()) / float(a[:iT + 1, 4].sum()) - 0.4)) < 1e-4
    rv = trade(a, 1, iT, 4.0, vwap_stop=True); assert rv is not None and abs(rv[7] - (107.0 - vs)) < 1e-4, rv   # R = entry - VWAP stop
    assert trade(wide, 1, iT, 4.0) is None and trade(wide, 1, iT, 4.0, cap=1.1) is not None                  # cap 1.0+ admits it
    print("selftest ok: VWAP stop level, VWAP-stop trade, wider cap")
    print("selftest ok: 1-min stop re-pricing (gap-through minute, intrabar touch)")
    print("selftest ok: hold test (open, VWAP, half gap, short), trade (time, stop, +1R trail, trailed stop, risk skip), ETP names")


def main():
    import pyarrow.dataset as pds
    assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
    sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
    import lib
    from mcf.research import gates as G
    from mcf.research.generator import data as GD
    assert (G.SLIP_PS, G.SLIP_BPS, G.STOP_EXTRA) == (SLIP_PS, SLIP_BPS, STOP_EXTRA) and tuple(G.TOD_COST) == TOD_COST
    TZ = "America/New_York"; TL0, TL1 = pd.Timestamp("2024-11-01", tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
    LK0, LK1 = pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date()
    SPLIT = pd.Timestamp("2025-09-30").date(); LIVE0 = pd.Timestamp("2026-10-06").date()
    T_FULL = G.t_required(N_LINEAGE); T90 = round(max(1.35, 0.9 * T_FULL), 2)
    RNG = np.random.default_rng(20261109)

    Dd = lib.daily().sort_values(["symbol", "date"]).reset_index(drop=True)
    assert not ((Dd.date >= LK0) & (Dd.date <= LK1)).any()
    pc = Dd.groupby("symbol").close.shift(1)
    gapd = pd.to_datetime(Dd.date).groupby(Dd.symbol).diff().dt.days > 5
    tr = np.maximum(Dd.high - Dd.low, np.maximum((Dd.high - pc).abs(), (Dd.low - pc).abs())).mask(gapd)
    Dd["pc"] = pc.mask(gapd)
    Dd["atr"] = tr.groupby(Dd.symbol).transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
    Dd["bl"] = GD._blackout(Dd.symbol.to_numpy(), Dd.date.to_numpy())
    trig = (Dd.low / Dd.pc <= 0.90)                                        # Rule 201 trigger that day (prior close known)
    Dd["ssr_prev"] = trig.groupby(Dd.symbol).shift(1).fillna(False).astype(bool) & ~gapd   # SSR carries into the next session
    SSRP = {(s, d): bool(v) for s, d, v in Dd[["symbol", "date", "ssr_prev"]].itertuples(index=False)}
    INFO = {(s, d): (p, a, adv, bl) for s, d, p, a, adv, bl in Dd[["symbol", "date", "pc", "atr", "adv20", "bl"]].itertuples(index=False)}
    SPYD = Dd[Dd.symbol == "SPY"].set_index("date")
    dtype = pd.Series(np.where(SPYD.close / SPYD.open - 1 > .0025, "up", np.where(SPYD.close / SPYD.open - 1 < -.0025, "down", "quiet")), index=SPYD.index)
    uni = pd.read_csv(ROOT / "data/universe.csv", usecols=["symbol", "name"])
    etp = set(uni[uni.name.fillna("").str.contains(ETP_RE)].symbol) | IDX
    syms = [s.strip() for s in open(ROOT / "research/lab_symbols.txt") if s.strip()]
    named = set(uni.symbol)
    print(f"lab symbols {len(syms)}; ETP/fund excluded by name {len(etp & set(syms))}; lab names without a universe.csv name "
          f"{len(set(syms) - named)} (kept)", flush=True)

    CACHE = ROOT / "data/cache_hist/1Min"
    def bars(sym, dates=None):
        """5-min RTH bars (o h l c v pv) per date; the locked block filtered at read and asserted absent."""
        p = CACHE / f"{sym}.parquet"
        if not p.exists(): return {}
        ix = "__index_level_0__"
        df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
        if ix in df.columns: df = df.set_index(ix)
        assert not ((df.index >= TL0) & (df.index < TL1)).any() and "volume" in df.columns
        df = df[~df.index.duplicated(keep="last")].sort_index()
        mm = df.index.hour * 60 + df.index.minute
        df = df[(mm >= 570) & (mm < 960)]; mm = df.index.hour * 60 + df.index.minute
        df = df.assign(_d=df.index.date, _b=(mm - 570) // 5, pv=(df.high + df.low + df.close) / 3 * df.volume)
        if dates is not None: df = df[df._d.isin(dates)]
        out = {}
        g = df.groupby(["_d", "_b"]).agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"),
                                         v=("volume", "sum"), pv=("pv", "sum"))
        for d, gd in g.groupby(level=0):
            a = np.full((78, 6), np.nan, np.float32); a[gd.index.get_level_values(1)] = gd.to_numpy()
            if np.isnan(a[0, 0]): continue
            c = pd.Series(a[:, 3]).ffill().to_numpy(); miss = np.isnan(a[:, 0])
            a[miss, 0] = a[miss, 1] = a[miss, 2] = c[miss]; a[:, 3] = c; a[miss, 4] = 0; a[miss, 5] = 0
            out[d] = a
        return out

    def bars1m(sym, dates):
        """Amendment 2: raw 1-min RTH o h l c (390 rows) for the given dates (gap > 10% events only)."""
        p = CACHE / f"{sym}.parquet"; ix = "__index_level_0__"
        df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
        if ix in df.columns: df = df.set_index(ix)
        assert not ((df.index >= TL0) & (df.index < TL1)).any()
        df = df[~df.index.duplicated(keep="last")].sort_index(); mm = df.index.hour * 60 + df.index.minute
        df = df[(mm >= 570) & (mm < 960)]; mm = df.index.hour * 60 + df.index.minute
        out = {}
        for d in dates:
            k = df.index.date == d
            if not k.any(): continue
            a = np.full((390, 4), np.nan, np.float32); a[mm[k] - 570] = df.loc[k, ["open", "high", "low", "close"]].to_numpy()
            out[d] = a
        return out

    # pass 1: every lab name -> opening volume norm and event days (only event-day arrays are kept)
    EVT, OPENV, M1 = {}, {}, {}
    trad = [s for s in syms if s not in etp]
    for k, s in enumerate(trad):
        B = bars(s); ds = sorted(B)
        if not ds: continue
        ov = pd.Series({d: float(np.nansum(B[d][:I955 + 1, 4])) for d in ds})
        brk = pd.Series(pd.to_datetime(pd.Index(ds))).diff().dt.days.gt(5).cumsum().to_numpy()   # restart after the locked gap
        norm = ov.groupby(brk).transform(lambda x: x.shift(1).rolling(20, min_periods=15).mean())
        for d in ds:
            inf = INFO.get((s, d))
            if inf is None: continue
            p, atr, adv, bl = inf; OPENV[(s, d)] = True
            if not (adv >= MIN_ADV and np.isfinite(p) and p > 0 and np.isfinite(norm[d]) and norm[d] > 0): continue
            gap = float(B[d][0, 0]) / p - 1
            if abs(gap) >= 0.04 and ov[d] >= VOL_X * norm[d]:
                EVT[(s, d)] = (B[d], gap, p, atr, bool(bl))
        big = [d for d in ds if (s, d) in EVT and abs(EVT[(s, d)][1]) > 0.10]
        if big:
            for d, m in bars1m(s, big).items(): M1[(s, d)] = m
        if k % 100 == 0: print(f"pass 1 {k}/{len(trad)}: events so far {len(EVT)}", flush=True)
    ev_days = sorted({d for (_, d) in EVT}); ev_by_day = {}
    for (s, d) in EVT: ev_by_day.setdefault(d, set()).add(s)
    print(f"event symbol-days {len(EVT)} on {len(ev_days)} days", flush=True)

    # pass 2: control pool (seeded 200 non-ETP lab names), bars on event days only
    pool_all = sorted(s for s in trad if s not in etp)
    POOL = sorted(RNG.choice(pool_all, size=min(200, len(pool_all)), replace=False).tolist())
    PB = {}
    for k, s in enumerate(POOL):
        PB[s] = bars(s, set(ev_days))
        if k % 50 == 0: print(f"control bars {k}/{len(POOL)}", flush=True)

    def c2_for(d, s, iT, cap=0.6, vw=False):
        cands = [c for c in POOL if d in PB[c] and c not in ev_by_day.get(d, set()) and (c, d) in INFO
                 and INFO[(c, d)][2] >= MIN_ADV and np.isfinite(INFO[(c, d)][1])]
        for _ in range(5):
            if not cands: return None
            c = cands[int(RNG.integers(len(cands)))]; res = trade(PB[c][d], s, iT, INFO[(c, d)][1], cap=cap, vwap_stop=vw)
            if res is not None: return res
        return None

    rows, ALLT = [], []
    DATES = sorted(SPYD.index); NS = len(DATES)
    print(f"sessions {NS}; lineage N {N_LINEAGE}: full bar {T_FULL}, BAR90 {T90}")
    for G_, T_, side, cap, vw in (GRID_R if REWORK else [g + (0.6, False) for g in GRID]):
        nm = f"SC1-{'L' if side > 0 else 'S'}-G{int(G_ * 100)}-T{T_}" + (f"-cap{cap}-{'vwap' if vw else 'lod'}" if REWORK else "")
        iT = I[T_]; T = []; C1 = {}; SK = {}
        for (s, d), (a, gap, p, atr, bl) in EVT.items():
            if side * gap < G_: continue
            ok = hold_ok(a, side, iT, p); res = trade(a, side, iT, atr, cap=cap, vwap_stop=vw)
            if res is None:
                k_ = ("hold_ok+" if ok else "hold_fail+") + skip_reason(a, side, iT, atr, cap, vw); SK[k_] = SK.get(k_, 0) + 1
                continue
            if not ok: SK["hold_fail+traded_as_C1"] = SK.get("hold_fail+traded_as_C1", 0) + 1
            r5 = res[0]
            if abs(gap) > 0.10:                                              # Amendment 2: 1-min stop re-pricing
                nr, ng = reprice_stop(res, M1.get((s, d)), side); res = (nr, ng) + tuple(res[2:])
            ssr = bool(side < 0 and (SSRP.get((s, d), False) or float(np.nanmin(a[:iT + 1, 2])) <= 0.90 * p))
            if not ok: C1.setdefault(d, []).append(res[0]); continue
            c2 = c2_for(d, side, iT, cap, vw); r2x = trade(a, side, iT, atr, spread_mult=2.0, cap=cap, vwap_stop=vw)[0]
            ab = abs(gap); bucket = "4-6" if ab < .06 else ("6-10" if ab < .10 else ">10")
            T.append(dict(date=d, symbol=s, side=side, gap=round(gap, 4), bucket=bucket, blackout=bl, r=res[0], gross=res[1],
                          kind=res[2], cost_r=res[4], r_2x=r2x - (r5 - res[0]), r_5min=r5, ssr=ssr, c2=c2[0] if c2 else np.nan))
        SK["entered"] = len(T)
        print(f"{nm} event funnel: " + ", ".join(f"{k} {v}" for k, v in sorted(SK.items())), flush=True)
        t = pd.DataFrame(T)
        if not len(t): rows.append(dict(config=nm, n=0)); continue
        t["c1"] = t.date.map(lambda d: float(np.mean(C1[d])) if d in C1 else np.nan)
        t["config"] = nm; ALLT.append(t)
        ssr_n, ssr_r = int(t.ssr.sum()), (round(t[t.ssr].r.mean(), 3) if t.ssr.any() else None)
        t = t[~t.ssr]                                       # Amendment 2: SSR shorts are not tradable as modelled -> scored without them
        if not len(t): rows.append(dict(config=nm, n=0, ssr_n=ssr_n, ssr_r=ssr_r)); continue
        S = G.summary(t); tr_, va_ = G.summary(t[t.date <= SPLIT]), G.summary(t[t.date > SPLIT]); lv = G.summary(t[t.date >= LIVE0])
        x1 = G.summary(t.dropna(subset=["c1"]).assign(r=lambda x: x.r - x.c1))
        x2 = G.summary(t.dropna(subset=["c2"]).assign(r=lambda x: x.r - x.c2))
        ty = t.groupby(t.date.map(dtype)).r.agg(["mean", "size"])
        mo = t.groupby(pd.to_datetime(t.date).dt.to_period("M")).r.mean()
        gd = t.groupby("date").r.sum(); share = round(gd.max() / gd.sum(), 2) if gd.sum() > 0 else None
        row = dict(config=nm, n=S["n"], days=S["days"], per_sess=round(S["n"] / NS, 2), avg_r=S["exp_r"], t=S.get("t"),
                   gross=round(t.gross.mean(), 3), wo_best=S.get("ex_best_day"), best_share=share, train=tr_.get("exp_r"),
                   valid=va_.get("exp_r"), valid_t=va_.get("t"), live_n=lv.get("n", 0), live=lv.get("exp_r"),
                   up=round(ty["mean"].get("up", np.nan), 3), down=round(ty["mean"].get("down", np.nan), 3),
                   quiet=round(ty["mean"].get("quiet", np.nan), 3), n_quiet=int(ty["size"].get("quiet", 0)),
                   wf_pos=round(float((mo > 0).mean()), 2), c1_ex=x1.get("exp_r"), c1_t=x1.get("t"), c1_n=x1.get("n", 0),
                   c2_ex=x2.get("exp_r"), c2_t=x2.get("t"), fail_hold_n=sum(len(v) for v in C1.values()),
                   blackout_r=round(t[t.blackout].r.mean(), 3) if t.blackout.any() else None, blackout_n=int(t.blackout.sum()),
                   other_r=round(t[~t.blackout].r.mean(), 3) if (~t.blackout).any() else None,
                   cost_r_med=round(float(t.cost_r.median()), 3), r_2x=round(float(t.r_2x.mean()), 3),
                   stops=round(float((t.kind == "stop").mean()), 2), ssr_n=ssr_n, ssr_r=ssr_r,
                   big_n=int((t.bucket == ">10").sum()), big_r_5min=round(float(t[t.bucket == ">10"].r_5min.mean()), 3) if (t.bucket == ">10").any() else None,
                   **{f"gap{b}_r": round(v, 3) for b, v in t.groupby("bucket").r.mean().items()})
        row["bar90"] = bool((row["t"] or 0) >= T90 and (row["c2_t"] or 0) >= T90 and (row["train"] or -1) > 0
                            and (row["valid"] or -1) > 0 and (row["up"] or -1) > 0 and (row["down"] or -1) > 0
                            and row["wf_pos"] >= .54 and (row["wo_best"] or -1) > 0)
        rows.append(row); print(nm, "done", flush=True)

    R = pd.DataFrame(rows); pd.set_option("display.width", 420); pd.set_option("display.max_columns", 80)
    print(R.to_string(index=False))
    print("\nentry next 5-min bar open (1-min SIP cache); stop LOD/HOD so far -/+ 0.05 ATR_d (skip > 0.6 / < 0.10 ATR_d), 15:55 exit,"
          "\n6-bar trail once +1R on a close; stop-first, gaps fill at the open; costs production + 4.4bp spread (tod multiplier on entry)."
          "\nc1 = excess over the same day's failed-hold event gaps (same side / T), c2 = over a same-minute random no-event pool name;"
          "\nblackout = earnings calendar window (+-4 days) where the calendar covers it; day type SPY o-c +-0.25%. All universe names"
          "\nhave adv20 >= $60M, so none is extended-tier (3x slippage rule not triggered)."
          "\nAmendment 2: shorts on SSR names (touched -10% vs prior close before entry, or SSR carried from the prior session) are"
          "\nreported (ssr_n / ssr_r) and EXCLUDED from scoring; stops on > 10% gaps re-priced on 1-min bars (big_r_5min = before).")
    print(f"configs {len(GRID_R) if REWORK else len(GRID)} (lineage N {N_LINEAGE}), BAR90 {T90}: pass {int(R.bar90.fillna(False).sum())}")
    sfx = "_rework" if REWORK else ""
    R.to_csv(HERE / f"sc1_results{sfx}.csv", index=False)
    if ALLT: pd.concat(ALLT).to_csv(HERE / f"sc1_trades{sfx}.csv", index=False)
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
