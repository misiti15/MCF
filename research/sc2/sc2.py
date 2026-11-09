"""SC2 (guild Scout plan research/sc2/PLAN.md, frozen 2026-11-09 09:40 ET before any score): cross-asset driver ->
equity laggard catch-up. Drivers USO / GLD / IBIT; a fresh |z| >= Z crossing of the driver's 15-min return (driver on the
s-side of its open) buys / sells followers with beta-to-driver >= 0.5 that moved < L x beta x |driver move|.
Entry next 5-min bar open, stop 0.25 ATR_d, target +1R, time exit H minutes or 15:55. 12 configs, lineage N 12, BAR90 2.01.
Controls: C1 same-minute random non-group name (seeded 200-name pool), C2 same follower at a random event-free bar.
Locked block 2024-11-01..2025-02-28 dropped at every read (asserted).
    python sc2.py > sc2_out.txt          (needs the 2-year cache: data/cache_hist/1Min + research/history2y daily)
    python sc2.py --selftest             (synthetic checks of the event, laggard and trade logic; no data)
Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path("/home/user/MCF"); HERE = Path(__file__).resolve().parent
GROUPS = {"OIL": ("USO", "XLE XOP XOM CVX COP OXY DVN EOG APA FANG HAL SLB EQT AR RRC".split()),
          "GOLD": ("GLD", "GDX GDXJ NEM AEM GFI KGC WPM PAAS AU FNV AG CDE RGLD".split()),
          "CRYPTO": ("IBIT", "MSTR COIN MARA RIOT CLSK HUT CIFR WULF HOOD".split())}
GRID = [(z, l, h) for z in (1.5, 2.0, 2.5) for l in (0.3, 0.5) for h in (30, 60)]
N_LINEAGE = 12
END_MIN = 570 + 5 * np.arange(1, 79)                       # bar ends 09:35 .. 16:00
END_TOD = END_MIN // 60 * 100 + END_MIN % 60
I = {int(t): i for i, t in enumerate(END_TOD)}
I940, I1000, I1500, I1555 = I[940], I[1000], I[1500], I[1555]
SPREAD_BPS = 4.4e-4; SLIP_PS, SLIP_BPS, STOP_EXTRA = 0.01, 1e-4, 0.02   # = mcf.research.gates values (asserted in main)
TOD_COST = ((935, 3.8), (950, 2.1), (1030, 1.4))


def tod_mult(tod):
    for edge, m in TOD_COST:
        if tod < edge: return m
    return 1.0


def ret15(a):
    """15-min return at every bar close (NaN for the first 3 bars)."""
    c = a[:, 3].astype(float); r = np.full(len(c), np.nan); r[3:] = c[3:] / c[:-3] - 1
    return r


def events(a_drv, sigma, Z):
    """[(bar index, side)] fresh |z| >= Z crossings at bar closes 10:00..15:00 with the driver on the s-side of its open."""
    if not (sigma and np.isfinite(sigma) and sigma > 0): return []
    z = ret15(a_drv) / sigma; o = a_drv[0, 0]; out = []
    for b in range(I1000, I1500 + 1):
        if not np.isfinite(z[b]) or abs(z[b]) < Z: continue
        if np.isfinite(z[b - 1]) and abs(z[b - 1]) >= Z: continue
        s = int(np.sign(z[b]))
        if s * (a_drv[b, 3] - o) > 0: out.append((b, s))
    return out


def is_laggard(a_f, b, s, beta, rD, L):
    rF = ret15(a_f)[b]
    return bool(np.isfinite(rF) and beta >= 0.5 and s * rF < L * beta * abs(rD))


def trade(a, s, ib, atr, H):
    """signal bar ib -> (net R, gross R, kind, exit bar, entry price) entering at bar ib+1 open; None if no bar / bad R."""
    j = ib + 1
    if j > I1555 or not (atr and np.isfinite(atr) and atr > 0): return None
    e = float(a[j, 0]); R = 0.25 * atr
    if not np.isfinite(e) or e <= 0: return None
    stop, tgt = e - s * R, e + s * R; last = min(I1555, ib + H // 5)
    kind, xp, xb = "time", float(a[last, 3]), last
    for i in range(j, last + 1):
        o, h, l, c = (float(v) for v in a[i])
        if i > j and s * (o - stop) <= 0: kind, xp, xb = "stop", o, i; break      # gap through the stop
        if (s > 0 and l <= stop) or (s < 0 and h >= stop): kind, xp, xb = "stop", stop, i; break   # stop first
        if i > j and s * (o - tgt) >= 0: kind, xp, xb = "target", o, i; break      # gap through the target: fill at open
        if (s > 0 and h >= tgt) or (s < 0 and l <= tgt): kind, xp, xb = "target", tgt, i; break
    m = tod_mult(int(END_TOD[ib]))
    cost = (SLIP_PS + e * SLIP_BPS) * m + SPREAD_BPS * e * m + SLIP_PS + e * SLIP_BPS + (STOP_EXTRA if kind == "stop" else 0)
    g = s * (xp - e) / R
    return g - cost / R, g, kind, xb, e


# ---------------------------------------------------------------------------------------------------- self-test
def selftest():
    def flat(p=100.0):
        a = np.full((78, 4), p, np.float32); return a
    # driver: flat, then +1% over 3 bars ending 10:30 -> one fresh crossing at the 10:30 bar, side +1
    d = flat(); b = I[1030]
    for k, p in zip(range(b - 2, 78), [100.3, 100.6, 101.0] + [101.0] * 78): d[k] = p
    ev = events(d, 0.002, 4.0); assert ev == [(b, 1)], ev     # z 1.5, 3.0, 5.0 on bars b-2..b -> first >= 4 at b
    assert events(d, 0.002, 2.0) == [(b - 1, 1)]                               # fresh crossing only, not repeated at b
    assert events(d, 0.002, 6.0) == []                                       # 1% / 0.2% = 5 sigma < 6
    dn = flat(); dn[b - 2:] = 99.0; dn[:b - 2] = 100.0                         # down move but driver below open: side -1 ok
    assert events(dn, 0.002, 2.0)[0][1] == -1
    up_below = flat(100.0); up_below[1:b - 2] = 98.0; up_below[b - 2:] = 99.0; up_below[0, 0] = 100.0
    assert events(up_below, 0.002, 2.0) == []                                  # +1% move but still below its open -> no event
    f = flat(50.0); assert is_laggard(f, b, 1, 1.0, 0.01, 0.3)                 # follower flat -> laggard
    f2 = flat(50.0); f2[b - 2:] = 50.5; assert not is_laggard(f2, b, 1, 1.0, 0.01, 0.3)   # +1% = already followed
    assert not is_laggard(f, b, 1, 0.4, 0.01, 0.3)                              # beta < 0.5
    # trade: long, ATR 4 -> R 1.0; entry 50 at bar b+1 open; target 51 hit at bar b+3
    t = flat(50.0); t[b + 3, 1] = 51.2
    r = trade(t, 1, b, 4.0, 60); assert r[2] == "target" and abs(r[1] - 1) < 1e-6 and r[3] == b + 3, r
    t2 = flat(50.0); t2[b + 2, 2] = 48.9; t2[b + 2, 1] = 51.5                  # both touched in one bar -> stop first
    r = trade(t2, 1, b, 4.0, 60); assert r[2] == "stop" and abs(r[1] + 1) < 1e-6, r
    t3 = flat(50.0); t3[b + 3:] = 48.5                                         # gap through the stop -> fill at the open
    r = trade(t3, 1, b, 4.0, 60); assert r[2] == "stop" and abs(r[1] + 1.5) < 1e-6, r
    t4 = flat(50.0); t4[b + 1:, :] = 50.0; t4[b + 6, 3] = 50.4                 # time exit after 30 min = bar b+6 close
    r = trade(t4, 1, b, 4.0, 30); assert r[2] == "time" and r[3] == b + 6 and abs(r[1] - 0.4) < 1e-5, r
    s5 = flat(50.0); s5[b + 2, 2] = 48.9                                       # short: target 49 hit
    r = trade(s5, -1, b, 4.0, 60); assert r[2] == "target" and abs(r[1] - 1) < 1e-6, r
    assert trade(flat(), 1, I1555, 4.0, 60) is None                            # no bar after 15:55
    assert r[0] < r[1]                                                          # costs subtract
    print("selftest ok: events (crossing, side, open-side), laggard (move, beta), trade (target, stop-first, gap, time, short, costs)")


# ---------------------------------------------------------------------------------------------------- full run
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
    IDX = {"SPY", "QQQ", "IWM", "DIA"}

    Dd = lib.daily().sort_values(["symbol", "date"]).reset_index(drop=True)
    assert not ((Dd.date >= LK0) & (Dd.date <= LK1)).any()
    pc = Dd.groupby("symbol").close.shift(1)
    tr = np.maximum(Dd.high - Dd.low, np.maximum((Dd.high - pc).abs(), (Dd.low - pc).abs()))
    gap = pd.to_datetime(Dd.date).groupby(Dd.symbol).diff().dt.days > 5          # first session after the locked gap
    tr = tr.mask(gap); Dd["ret"] = (Dd.close / pc - 1).mask(gap)
    Dd["atr"] = tr.groupby(Dd.symbol).transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
    SPYD = Dd[Dd.symbol == "SPY"].set_index("date"); Dd["spy_ret"] = Dd.date.map(SPYD.ret)
    def _beta(g):
        x, y = g.spy_ret.shift(1), g.ret.shift(1)
        cov = (x * y).rolling(60, min_periods=40).mean() - x.rolling(60, min_periods=40).mean() * y.rolling(60, min_periods=40).mean()
        return cov / x.rolling(60, min_periods=40).var(ddof=0)
    Dd["beta_spy"] = Dd.groupby("symbol", group_keys=False).apply(_beta)
    Dd["bl"] = GD._blackout(Dd.symbol.to_numpy(), Dd.date.to_numpy())
    INFO = {(s, d): (a, b, bl, adv) for s, d, a, b, bl, adv in Dd[["symbol", "date", "atr", "beta_spy", "bl", "adv20"]].itertuples(index=False)}
    dtype = pd.Series(np.where(SPYD.close / SPYD.open - 1 > .0025, "up", np.where(SPYD.close / SPYD.open - 1 < -.0025, "down", "quiet")), index=SPYD.index)

    CACHE = ROOT / "data/cache_hist/1Min"
    def bars(sym):                                        # = research/gate2/gate2.py bars(), all open dates
        p = CACHE / f"{sym}.parquet"
        if not p.exists(): return {}
        ix = "__index_level_0__"
        df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
        if ix in df.columns: df = df.set_index(ix)
        assert not ((df.index >= TL0) & (df.index < TL1)).any()
        df = df[~df.index.duplicated(keep="last")].sort_index()
        mm = df.index.hour * 60 + df.index.minute
        df = df[(mm >= 570) & (mm < 960)]; mm = df.index.hour * 60 + df.index.minute
        df = df.assign(_d=df.index.date, _b=(mm - 570) // 5)
        out = {}
        g = df.groupby(["_d", "_b"]).agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"))
        for d, gd in g.groupby(level=0):
            a = np.full((78, 4), np.nan, np.float32); a[gd.index.get_level_values(1)] = gd[["o", "h", "l", "c"]].to_numpy()
            if np.isnan(a[0, 0]): continue
            c = pd.Series(a[:, 3]).ffill().to_numpy(); miss = np.isnan(a[:, 0])
            a[miss, 0] = a[miss, 1] = a[miss, 2] = c[miss]; a[:, 3] = c
            out[d] = a
        return out

    members = {s for _, (drv, fol) in GROUPS.items() for s in [drv] + fol}
    P = {s: bars(s) for s in sorted(members | {"SPY"})}
    DATES = sorted(P["SPY"]); assert not any(LK0 <= d <= LK1 for d in DATES)
    # control pool: seeded 200 lab names (median adv20 >= $60M, not in any group, not an index ETF)
    med = Dd.groupby("symbol").adv20.median()
    pool_all = sorted(s for s in med[med >= 60e6].index if s not in members and s not in IDX)
    POOL = sorted(RNG.choice(pool_all, size=min(200, len(pool_all)), replace=False).tolist())
    for k, s in enumerate(POOL):
        P[s] = bars(s)
        if k % 50 == 0: print(f"control bars {k}/{len(POOL)}", flush=True)
    print(f"SPY sessions {len(DATES)} ({DATES[0]}..{DATES[-1]}, locked absent); members {len(members)}; control pool {len(POOL)}", flush=True)

    def prior_sessions(d, sym, n=20):
        """the n open sessions before d with bars for sym; restart after a > 5-day gap (locked block)."""
        k = DATES.index(d); out = []
        for j in range(k - 1, -1, -1):
            if (DATES[j + 1] - DATES[j]).days > 5: break
            if DATES[j] in P[sym]: out.append(DATES[j])
            if len(out) == n: break
        return out

    SIG, BETA = {}, {}
    for gname, (drv, fol) in GROUPS.items():
        for d in DATES:
            if d not in P[drv]: continue
            ps = prior_sessions(d, drv)
            if len(ps) >= 15:
                SIG[(drv, d)] = float(np.nanstd(np.concatenate([ret15(P[drv][x])[I1000:I1500 + 1] for x in ps]), ddof=1))
            for f in fol:
                if d not in P.get(f, {}): continue
                both = [x for x in ps if x in P[f]]
                if len(both) < 15: continue
                rd = np.concatenate([P[drv][x][I940:, 3] / P[drv][x][I940 - 1:-1, 3] - 1 for x in both])
                rf = np.concatenate([P[f][x][I940:, 3] / P[f][x][I940 - 1:-1, 3] - 1 for x in both])
                ok = np.isfinite(rd) & np.isfinite(rf)
                if ok.sum() > 100 and rd[ok].var() > 0:
                    BETA[(f, d)] = float(np.cov(rf[ok], rd[ok])[0, 1] / rd[ok].var(ddof=1))
    print(f"driver sigma days {len(SIG)}; follower beta rows {len(BETA)}", flush=True)

    def spy_hedge(d, s, ib, xb, e, R, beta_spy):
        a = P["SPY"].get(d)
        if a is None or not np.isfinite(beta_spy): return np.nan
        mv = float(a[xb, 3]) / float(a[ib + 1, 0]) - 1
        return beta_spy * s * mv * e / R + (2 * (SLIP_PS / float(a[ib + 1, 0]) + SLIP_BPS)) * abs(beta_spy) * e / R

    rows, ALLT = [], []
    NS = len(DATES)
    print(f"lineage N {N_LINEAGE}: full bar {T_FULL}, BAR90 {T90}")
    for Z, L, H in GRID:
        nm = f"SC2-Z{Z}-L{L}-H{H}"; T = []
        for gname, (drv, fol) in GROUPS.items():
            for d in DATES:
                a_d = P[drv].get(d); sig = SIG.get((drv, d))
                if a_d is None or sig is None: continue
                busy = {}
                for ib, s in events(a_d, sig, Z):
                    rD = ret15(a_d)[ib]
                    for f in fol:
                        a = P.get(f, {}).get(d); inf = INFO.get((f, d)); beta = BETA.get((f, d))
                        if a is None or inf is None or beta is None: continue
                        atr, bspy, bl, adv = inf
                        if bl or not (adv >= 60e6) or busy.get(f, -1) >= ib: continue
                        if not is_laggard(a, ib, s, beta, rD, L): continue
                        res = trade(a, s, ib, atr, H)
                        if res is None: continue
                        busy[f] = res[3]
                        # C1: same-minute random pool name (eligible that day), same side and rules
                        c1 = None; cands = [c for c in POOL if d in P[c] and (c, d) in INFO and not INFO[(c, d)][2]
                                            and INFO[(c, d)][3] >= 60e6 and np.isfinite(INFO[(c, d)][0])]
                        if cands:
                            c = cands[int(RNG.integers(len(cands)))]; c1 = trade(P[c][d], s, ib, INFO[(c, d)][0], H)
                        # C2: same follower, random event-free bar (|z| < 1) the same day, same side
                        z = ret15(a_d) / sig; free = [b for b in range(I1000, I1500 + 1) if np.isfinite(z[b]) and abs(z[b]) < 1]
                        c2 = trade(a, s, int(RNG.choice(free)), atr, H) if free else None
                        hedge = spy_hedge(d, s, ib, res[3], res[4], 0.25 * atr, bspy)
                        T.append(dict(date=d, group=gname, symbol=f, side=s, tod=int(END_TOD[ib]), r=res[0], gross=res[1],
                                      kind=res[2], c1=c1[0] if c1 else np.nan, c2=c2[0] if c2 else np.nan,
                                      r_hedged=res[0] - hedge if np.isfinite(hedge) else np.nan,
                                      eia=bool(gname == "OIL" and pd.Timestamp(d).dayofweek == 2 and 1035 <= END_TOD[ib] <= 1100)))
        t = pd.DataFrame(T)
        if not len(t): rows.append(dict(config=nm, n=0)); continue
        t["config"] = nm; ALLT.append(t)
        S = G.summary(t); tr_, va_ = G.summary(t[t.date <= SPLIT]), G.summary(t[t.date > SPLIT]); lv = G.summary(t[t.date >= LIVE0])
        x1 = G.summary(t.dropna(subset=["c1"]).assign(r=lambda x: x.r - x.c1))
        x2 = G.summary(t.dropna(subset=["c2"]).assign(r=lambda x: x.r - x.c2))
        hd = G.summary(t.dropna(subset=["r_hedged"]).assign(r=lambda x: x.r_hedged))
        ty = t.groupby(t.date.map(dtype)).r.agg(["mean", "size"])
        mo = t.groupby(pd.to_datetime(t.date).dt.to_period("M")).r.mean()
        gd = t.groupby("date").r.sum(); share = round(gd.max() / gd.sum(), 2) if gd.sum() > 0 else None
        grp = {f"{g}_r": round(v, 3) for g, v in t.groupby("group").r.mean().items()}
        grp.update({f"{g}_n": int(v) for g, v in t.groupby("group").size().items()})
        row = dict(config=nm, n=S["n"], days=S["days"], per_sess=round(S["n"] / NS, 2), avg_r=S["exp_r"], t=S.get("t"),
                   gross=round(t.gross.mean(), 3), wo_best=S.get("ex_best_day"), best_share=share, train=tr_.get("exp_r"),
                   valid=va_.get("exp_r"), valid_t=va_.get("t"), live_n=lv.get("n", 0), live=lv.get("exp_r"),
                   up=round(ty["mean"].get("up", np.nan), 3), down=round(ty["mean"].get("down", np.nan), 3),
                   quiet=round(ty["mean"].get("quiet", np.nan), 3), wf_pos=round(float((mo > 0).mean()), 2),
                   c1_ex=x1.get("exp_r"), c1_t=x1.get("t"), c2_ex=x2.get("exp_r"), c2_t=x2.get("t"),
                   hedged=hd.get("exp_r"), hedged_t=hd.get("t"), long_r=round(t[t.side > 0].r.mean(), 3),
                   short_r=round(t[t.side < 0].r.mean(), 3), long_share=round(float((t.side > 0).mean()), 2),
                   eia_n=int(t.eia.sum()), eia_r=round(t[t.eia].r.mean(), 3) if t.eia.any() else None,
                   targets=round(float((t.kind == "target").mean()), 2), stops=round(float((t.kind == "stop").mean()), 2), **grp)
        row["bar90"] = bool((row["t"] or 0) >= T90 and (row["c1_t"] or 0) >= T90 and (row["train"] or -1) > 0
                            and (row["valid"] or -1) > 0 and (row["up"] or -1) > 0 and (row["down"] or -1) > 0
                            and row["wf_pos"] >= .54 and (row["wo_best"] or -1) > 0)
        rows.append(row); print(nm, "done", flush=True)

    R = pd.DataFrame(rows); pd.set_option("display.width", 420); pd.set_option("display.max_columns", 80)
    print(R.to_string(index=False))
    print("\nentry next 5-min bar open (1-min SIP cache); stop 0.25 ATR_d, target +1R, time exit H min / 15:55; stop-first, gaps fill"
          "\nat the open; costs production + 4.4bp spread (tod multiplier on entry). c1 = excess over a same-minute random pool name,"
          "\nc2 = over the same follower at a random event-free bar; hedged = minus beta_SPY x SPY move (report only); day type SPY o-c +-0.25%.")
    print(f"configs {len(GRID)} (lineage N {N_LINEAGE}), BAR90 {T90}: pass {int(R.bar90.fillna(False).sum())}")
    R.to_csv(HERE / "sc2_results.csv", index=False)
    if ALLT: pd.concat(ALLT).to_csv(HERE / "sc2_trades.csv", index=False)
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
