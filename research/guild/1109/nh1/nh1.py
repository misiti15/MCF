"""NH1 (guild Scout plan research/nh1/PLAN.md, frozen 2026-11-09 13:45 ET before any score): quiet-top continuation long.
Bar closes 09:50..14:00, first signal per symbol-day: day range so far <= K x ATR_d, HOD - close <= 0.25 ATR_d and close in
the top 30% of the range, 0 <= fromOpen <= 0.5 ATR_d, RSI14 (5-min, seeded by the prior session) in [45, 65]; M1: SPY >= open.
Entry next bar open, stop LOD so far - 0.05 ATR_d (skip risk < 0.15 or > 1.0 ATR_d); E1 15:55 | E2 BE at +1R, trail 1R from +2R.
8 configs (K 0.5/0.8 x E1/E2 x M0/M1). Family N 1,671 -> BAR90 3.47 (own N 8 -> 1.84 = lead only).
C1 (pass control): same-minute random non-signal universe long in the same fromOpen bucket, same stop rule and exit.
C2 (descriptive): same-minute random universe name with a compressed day (range <= K ATR) sitting in the BOTTOM 30% of it.
Two passes keep memory small: pass A streams symbols for signals + their trades; pass B re-reads them and trades controls only
at the (date, bar) keys the signals need (a control's stop must fit the same skip bounds; one random fitting control per signal). Locked block 2024-11-01..2025-02-28 dropped at every read (asserted).
    python nh1.py > nh1_out.txt          python nh1.py --selftest
Educational only - not financial advice."""
import os, re, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path("/home/user/MCF"); HERE = Path(__file__).resolve().parent
GRID = [(k, ex, m) for k in (0.5, 0.8) for ex in ("E1", "E2") for m in ("M0", "M1")]
N_FAMILY, N_OWN = 1671, 8
END_MIN = 570 + 5 * np.arange(1, 79)
END_TOD = END_MIN // 60 * 100 + END_MIN % 60
I = {int(t): i for i, t in enumerate(END_TOD)}
I950, I1400, I1555 = I[950], I[1400], I[1555]
SPREAD_BPS = 4.4e-4; SLIP_PS, SLIP_BPS, STOP_EXTRA = 0.01, 1e-4, 0.02
TOD_COST = ((935, 3.8), (950, 2.1), (1030, 1.4))
ETP_RE = re.compile(r"\bETF\b|\bETN\b|\bFund\b|ProShares|Direxion|iShares|SPDR|Invesco QQQ|\b[23]X\b|Leveraged|Inverse|"
                    r"\bUltra|\bBear\b|\bBull\b|Daily Target|GraniteShares|Tradr|Defiance|T-Rex|Volatility|VIX|Physical (Gold|Silver)", re.I)
IDX = {"SPY", "QQQ", "IWM", "DIA"}


def tod_mult(tod):
    for edge, m in TOD_COST:
        if tod < edge: return m
    return 1.0


def rsi14(closes):
    """Wilder RSI(14) over a 1-D close series (prior session + today); NaN until 14 changes exist."""
    c = np.asarray(closes, float); d = np.diff(c); out = np.full(len(c), np.nan)
    if len(d) < 14: return out
    up, dn = np.clip(d, 0, None), np.clip(-d, 0, None)
    au, ad = up[:14].mean(), dn[:14].mean()
    for i in range(14, len(d) + 1):
        if i > 14: au = (au * 13 + up[i - 1]) / 14; ad = (ad * 13 + dn[i - 1]) / 14
        out[i] = 100.0 if ad == 0 else 100 - 100 / (1 + au / ad)
    return out


def state(a, atr, rsi_today):
    """per-bar arrays for bars 0..77: range/ATR, position in range, HOD gap/ATR, fromOpen/ATR, RSI."""
    o = a[0, 0]; hod = np.maximum.accumulate(a[:, 1]); lod = np.minimum.accumulate(a[:, 2]); c = a[:, 3]
    rng = hod - lod
    pos = np.where(rng > 0, (c - lod) / np.where(rng > 0, rng, 1), np.nan)
    return dict(rng=rng / atr, pos=pos, hgap=(hod - c) / atr, fo=(c - o) / atr, rsi=rsi_today, lod=lod)


def signal_bar(st, K):
    """first bar 09:50..14:00 meeting the NH1 rule, or -1."""
    ok = ((st["rng"] <= K) & (st["pos"] >= 0.7) & (st["hgap"] <= 0.25) & (st["fo"] >= 0) & (st["fo"] <= 0.5)
          & (st["rsi"] >= 45) & (st["rsi"] <= 65))
    ok[:I950] = False; ok[I1400 + 1:] = False
    h = np.flatnonzero(np.nan_to_num(ok, nan=0).astype(bool))
    return int(h[0]) if len(h) else -1


def trade(a, ib, atr, lod_at, ex):
    """long from bar ib+1 open; stop = LOD so far at ib - 0.05 ATR -> (net R, gross R, kind, cost R) or None if skipped."""
    j = ib + 1
    if j > I1555 or not (atr and np.isfinite(atr) and atr > 0): return None
    e = float(a[j, 0]); stop = float(lod_at) - 0.05 * atr; R = e - stop
    if not np.isfinite(e) or R < 0.15 * atr or R > 1.0 * atr: return None
    best = e; kind, xp = "time", float(a[I1555, 3])
    for i in range(j, I1555 + 1):
        o, h, l, c = (float(x) for x in a[i, :4])
        if i > j and o <= stop: kind, xp = "stop", o; break
        if l <= stop: kind, xp = "stop", stop; break
        if ex == "E2":                                   # gate2 E2: update on the close, active from the next bar
            best = max(best, c); run = (best - e) / R
            if run >= 2: stop = max(stop, best - R)
            elif run >= 1: stop = max(stop, e)
    m = tod_mult(int(END_TOD[ib]))
    cost = (SLIP_PS + e * SLIP_BPS) * m + SPREAD_BPS * e * m + SLIP_PS + e * SLIP_BPS + (STOP_EXTRA if kind == "stop" else 0)
    g = (xp - e) / R
    return g - cost / R, g, kind, cost / R


def bucket(fo):
    return 0 if 0 <= fo < 0.25 else (1 if 0.25 <= fo <= 0.5 else -1)


def selftest():
    r = rsi14(np.r_[np.arange(100, 115), np.arange(115, 100, -1)]); assert r[14] == 100 and 30 < r[-1] < 40      # Wilder decay after 14 ups then 14 downs ~35
    r2 = rsi14(np.r_[100.0, np.tile([101.0, 100.0], 20)]); assert 45 < r2[-1] < 55
    # compressed day: open 100, range 99.6..100.5 (0.9 on ATR 2 = 0.45), closes 100.4 from 10:00 -> signal at 09:50 bar? fo 0.2 ATR
    a = np.zeros((78, 4), np.float32); a[:] = 100.4; a[0] = [100.0, 100.5, 99.6, 100.2]; a[1:, 1] = 100.5; a[1:, 2] = 100.3
    rs = np.full(78, 55.0); st = state(a, 2.0, rs)
    assert signal_bar(st, 0.5) == I950 and signal_bar(st, 0.4) == -1        # range 0.45 ATR: K 0.5 yes, 0.4 no
    st2 = state(a, 2.0, np.full(78, 70.0)); assert signal_bar(st2, 0.5) == -1   # RSI too high
    b = a.copy(); b[1:, 3] = 99.9; b[1:, 2] = 99.8; assert signal_bar(state(b, 2.0, rs), 0.5) == -1   # below open / low in range
    # trade: entry 100.4 at bar ib+1, LOD 99.6 -> stop 99.5, R 0.9 (0.45 ATR) ok
    ib = I950; t = a.copy(); r = trade(t, ib, 2.0, 99.6, "E1"); assert r[2] == "time" and abs(r[1]) < 1e-5, r
    t2 = a.copy(); t2[ib + 3, 2] = 99.4; r = trade(t2, ib, 2.0, 99.6, "E1"); assert r[2] == "stop" and abs(r[1] + 1) < 1e-4
    t3 = a.copy(); t3[ib + 2:, :] = 102.4; t3[ib + 8:, :] = 100.0; t3[ib + 8, 0] = 101.0   # +2.2R then drop through BE
    r = trade(t3, ib, 2.0, 99.6, "E2"); assert r[2] == "stop" and abs(r[1] - (101.0 - 100.4) / 0.9) < 1e-3, r   # trail 101.5; bar opens 101.0 through it
    r = trade(t3, ib, 2.0, 99.6, "E1"); assert r[2] == "time" and abs(r[1] - (100.0 - 100.4) / 0.9) < 1e-3
    assert trade(a, ib, 2.0, 98.0, "E1") is None                              # risk 2.5 > 1.0 ATR -> skip
    assert bucket(0.1) == 0 and bucket(0.3) == 1 and bucket(0.6) == -1 and bucket(-0.1) == -1
    print("selftest ok: RSI14, compressed-top signal (K, RSI, open side), trade (time, stop, E2 trail), risk skip, buckets")


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
    T_FAM = round(max(1.35, 0.9 * G.t_required(N_FAMILY)), 2); T_OWN = round(max(1.35, 0.9 * G.t_required(N_OWN)), 2)
    RNG = np.random.default_rng(20261109)

    Dd = lib.daily().sort_values(["symbol", "date"]).reset_index(drop=True)
    assert not ((Dd.date >= LK0) & (Dd.date <= LK1)).any()
    pc = Dd.groupby("symbol").close.shift(1)
    gapd = pd.to_datetime(Dd.date).groupby(Dd.symbol).diff().dt.days > 5
    tr = np.maximum(Dd.high - Dd.low, np.maximum((Dd.high - pc).abs(), (Dd.low - pc).abs())).mask(gapd)
    Dd["atr"] = tr.groupby(Dd.symbol).transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
    uni = pd.read_csv(ROOT / "data/universe.csv", usecols=["symbol", "name"])
    etp = set(uni[uni.name.fillna("").str.contains(ETP_RE)].symbol) | IDX
    Dd["score"] = Dd.adv20 * Dd.atr / pc
    cand = Dd[(Dd.adv20 >= 95e6) & (Dd.atr > 0) & ~Dd.symbol.isin(etp)].copy()
    cand["rk"] = cand.groupby("date").score.rank(ascending=False, method="first")
    U = cand[cand.rk <= 500].copy()
    U["bl"] = GD._blackout(U.symbol.to_numpy(), U.date.to_numpy())
    U = U[~U.bl]
    ATR = {(s, d): a for s, d, a in U[["symbol", "date", "atr"]].itertuples(index=False)}
    UD = U.groupby("symbol").date.apply(set).to_dict()
    SPYD = Dd[Dd.symbol == "SPY"].set_index("date")
    dtype = pd.Series(np.where(SPYD.close / SPYD.open - 1 > .0025, "up", np.where(SPYD.close / SPYD.open - 1 < -.0025, "down", "quiet")), index=SPYD.index)
    print(f"universe symbol-days {len(U)} ({U.symbol.nunique()} names; ETP/index excluded {len(etp)}); blackout out", flush=True)

    CACHE = ROOT / "data/cache_hist/1Min"
    def bars(sym):                                        # = gate2 bars(), all open dates
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

    SPYB = bars("SPY"); DATES = sorted(SPYB); assert not any(LK0 <= d <= LK1 for d in DATES)
    SPY_UP = {d: (a[:, 3] >= a[0, 0]) for d, a in SPYB.items()}
    # per (date, bar): lists of candidates for C1 (bucket -> [(sym, lod)]) and C2 (per K: [(sym, lod)])
    SIG, SIGBARS = [], set()

    def day_states(sym, B, only=None):
        ds = sorted(B)
        for k, d in enumerate(ds):
            if only is not None and d not in only: continue
            atr = ATR.get((sym, d))
            if atr is None or not np.isfinite(atr) or atr <= 0: continue
            prev = B.get(ds[k - 1]) if k > 0 and (d - ds[k - 1]).days <= 5 else None
            closes = np.r_[prev[:, 3], B[d][:, 3]] if prev is not None else B[d][:, 3]
            rs = rsi14(closes)[-78:] if prev is not None else np.full(78, np.nan)
            yield d, atr, state(B[d], atr, rs)

    # pass A: signals and their trades
    syms = sorted(UD)
    for n_, sym in enumerate(syms):
        B = bars(sym)
        for d, atr, st in day_states(sym, B):
            for K in (0.5, 0.8):
                ib = signal_bar(st, K)
                if ib < 0: continue
                SIGBARS.add((sym, d, ib))
                for ex in ("E1", "E2"):
                    res = trade(B[d], ib, atr, st["lod"][ib], ex)
                    if res is None: continue
                    SIG.append(dict(date=d, symbol=sym, K=K, ex=ex, ib=ib, tod=int(END_TOD[ib]),
                                    spy_up=bool(SPY_UP[d][ib]) if d in SPY_UP else False,
                                    bk=bucket(st["fo"][ib]), r=res[0], gross=res[1], kind=res[2], cost_r=res[3]))
        if n_ % 100 == 0: print(f"pass A {n_}/{len(syms)}: signals {len(SIG)}", flush=True)
    S0 = pd.DataFrame(SIG)
    print(f"pass A done: signal rows {len(S0)}", flush=True)

    # pass B: control trades only at the needed (date, bar) keys
    K1 = set(zip(S0.date, S0.ib, S0.bk)); K2 = set(zip(S0.date, S0.ib, S0.K))
    byday = {}
    for d, ib, bk in K1: byday.setdefault(d, [[], []])[0].append((ib, bk))
    for d, ib, K in K2: byday.setdefault(d, [[], []])[1].append((ib, K))
    C1R, C2R = {}, {}
    for n_, sym in enumerate(syms):
        days = UD[sym] & set(byday)
        if not days: continue
        B = bars(sym)
        for d, atr, st in day_states(sym, B, only=days):
            k1, k2 = byday[d]
            for ib, bk in k1:                                 # C1: same bucket, not a signal at that bar
                if (sym, d, ib) in SIGBARS or bucket(st["fo"][ib]) != bk: continue
                r1, r2 = (trade(B[d], ib, atr, st["lod"][ib], ex) for ex in ("E1", "E2"))
                if r1 is not None: C1R.setdefault((d, ib, bk), []).append((sym, r1[0], r2[0]))
            for ib, K in k2:                                  # C2: compressed but in the bottom 30% of the range
                if not (st["rng"][ib] <= K and st["pos"][ib] <= 0.3): continue
                r1, r2 = (trade(B[d], ib, atr, st["lod"][ib], ex) for ex in ("E1", "E2"))
                if r1 is not None: C2R.setdefault((d, ib, K), []).append((sym, r1[0], r2[0]))
        if n_ % 100 == 0: print(f"pass B {n_}/{len(syms)}", flush=True)

    def pick(pool, key, me, ex):
        c = [x for x in pool.get(key, []) if x[0] != me]
        if not c: return np.nan
        x = c[int(RNG.integers(len(c)))]
        return x[1] if ex == "E1" else x[2]
    S0["c1"] = [pick(C1R, (r.date, r.ib, r.bk), r.symbol, r.ex) for r in S0.itertuples()]
    S0["c2"] = [pick(C2R, (r.date, r.ib, r.K), r.symbol, r.ex) for r in S0.itertuples()]

    rows, ALLT = [], []
    NS = len(DATES)
    print(f"sessions {NS}; family N {N_FAMILY}: BAR90 {T_FAM}; own N {N_OWN}: BAR90 {T_OWN}")
    for K, ex, M in GRID:
        nm = f"NH1-K{K}-{ex}-{M}"
        t = S0[(S0.K == K) & (S0.ex == ex)]
        if M == "M1": t = t[t.spy_up]
        t = t.copy()
        if not len(t): rows.append(dict(config=nm, n=0)); continue
        t["config"] = nm; ALLT.append(t)
        S = G.summary(t); tr_, va_ = G.summary(t[t.date <= SPLIT]), G.summary(t[t.date > SPLIT]); lv = G.summary(t[t.date >= LIVE0])
        x1 = G.summary(t.dropna(subset=["c1"]).assign(r=lambda x: x.r - x.c1))
        x2 = G.summary(t.dropna(subset=["c2"]).assign(r=lambda x: x.r - x.c2))
        ty = t.groupby(t.date.map(dtype)).r.agg(["mean", "size"])
        mo = t.groupby(pd.to_datetime(t.date).dt.to_period("M")).r.mean()
        gd = t.groupby("date").r.sum(); share = round(gd.max() / gd.sum(), 2) if gd.sum() > 0 else None
        busiest = round(float(t.groupby("date").size().max() / len(t)), 3)
        row = dict(config=nm, n=S["n"], days=S["days"], per_sess=round(S["n"] / NS, 2), avg_r=S["exp_r"], t=S.get("t"),
                   gross=round(t.gross.mean(), 3), wo_best=S.get("ex_best_day"), best_share=share, busiest_day_trades=busiest,
                   train=tr_.get("exp_r"), valid=va_.get("exp_r"), valid_t=va_.get("t"), live_n=lv.get("n", 0), live=lv.get("exp_r"),
                   up=round(ty["mean"].get("up", np.nan), 3), down=round(ty["mean"].get("down", np.nan), 3),
                   quiet=round(ty["mean"].get("quiet", np.nan), 3), n_up=int(ty["size"].get("up", 0)),
                   n_down=int(ty["size"].get("down", 0)), n_quiet=int(ty["size"].get("quiet", 0)),
                   wf_pos=round(float((mo > 0).mean()), 2), c1_ex=x1.get("exp_r"), c1_t=x1.get("t"), c1_n=x1.get("n", 0),
                   c2_ex=x2.get("exp_r"), c2_t=x2.get("t"), cost_r_med=round(float(t.cost_r.median()), 3),
                   stops=round(float((t.kind == "stop").mean()), 2))
        base = ((row["train"] or -1) > 0 and (row["valid"] or -1) > 0 and (row["up"] or -1) > 0 and (row["down"] or -1) > 0
                and row["wf_pos"] >= .54 and (row["wo_best"] or -1) > 0 and (share is None or share < .5))
        row["lead_own_bar"] = bool(base and (row["t"] or 0) >= T_OWN and (row["c1_t"] or 0) >= T_OWN)
        row["bar90_family"] = bool(base and (row["t"] or 0) >= T_FAM and (row["c1_t"] or 0) >= T_FAM)
        rows.append(row); print(nm, "done", flush=True)

    R = pd.DataFrame(rows); pd.set_option("display.width", 420); pd.set_option("display.max_columns", 80)
    print(R.to_string(index=False))
    # north-star check (descriptive): Move Hunt long movers (non-blackout, decision >= 09:50) that NH1 K0.8 flagged at/before
    mv_p = ROOT / "research/bdi/moves/moves.csv"
    if mv_p.exists():
        mv = pd.read_csv(mv_p); mv = mv[(mv.side == "long") & (mv.blackout.astype(str) != "True") & (mv.decision >= "09:50")]
        mv["date"] = pd.to_datetime(mv.date).dt.date
        fired = S0[(S0.K == 0.8) & (S0.ex == "E1")][["date", "symbol", "tod"]]
        m = mv.merge(fired, on=["date", "symbol"], how="left")
        dec = m.decision.str.replace(":", "").astype(int)
        hit = m.tod.notna() & (m.tod <= dec)
        print(f"\nMove Hunt north-star (descriptive): {int(hit.sum())} of {len(mv)} non-blackout long movers (decision >= 09:50) "
              f"flagged by NH1 K0.8 at/before the decision bar; {int(m.tod.notna().sum())} flagged that day at any time.")
    print("\nentry next 5-min bar open (1-min SIP cache); stop LOD so far - 0.05 ATR_d (skip < 0.15 / > 1.0 ATR_d); E1 15:55, E2 BE +1R /"
          "\ntrail 1R from +2R on closes; stop-first, gaps fill at the open; costs production + 4.4bp spread (tod multiplier on entry)."
          "\nc1 = excess over a same-minute random non-signal universe long in the same fromOpen bucket (PASS control);"
          "\nc2 = over a same-minute random compressed name in the BOTTOM 30% of its range (descriptive); day type SPY o-c +-0.25%.")
    print(f"configs {len(GRID)}; family N {N_FAMILY} BAR90 {T_FAM}: pass {int(R.bar90_family.fillna(False).sum())}; "
          f"own N {N_OWN} BAR90 {T_OWN} (lead only): {int(R.lead_own_bar.fillna(False).sum())}")
    R.to_csv(HERE / "nh1_results.csv", index=False)
    if ALLT: pd.concat(ALLT).to_csv(HERE / "nh1_trades.csv", index=False)
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
