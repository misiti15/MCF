"""FAMC forward shadow (FORWARD_AMC.md, frozen 2026-11-10 11:40 ET). Journal-only; nothing trades.
    python famc_shadow.py --date 2026-11-11 --calendar famc_calendar.csv      (nightly, after 16:00 ET)
    python famc_shadow.py --selftest
Educational only - not financial advice."""
import argparse, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); HERE = Path(__file__).resolve().parent
SL, BP, SP, SX = 0.01, 1e-4, 4.4e-4, 0.02
TOD_MULT_0951 = 2.1                                          # gates.TOD_COST: bar-close < 09:50 -> 3.8, < 10:30 -> 2.1 (09:51 entry)
CAP = 0.75; START = "2026-11-11"               # cap = 1.5 x expected session sd (~0.5R with 2-3 timed events/session; Skeptic fix 6)


def fade_trade(m1, side, atr):
    """m1: 1-min frame (minute index -> o,h,l,c) for 09:51..15:55; side = -sign(gap). -> (net R, gross R, kind, exit position) or None."""
    if m1 is None or not len(m1) or not (atr and np.isfinite(atr) and atr > 0): return None
    e = float(m1.iloc[0].o); stop = e - side * atr; px, kind, xi = float(m1.iloc[-1].c), "time", len(m1) - 1
    for i, r in enumerate(m1.itertuples()):
        if i > 0 and side * (r.o - stop) <= 0: px, kind, xi = float(r.o), "stop", i; break
        if (side > 0 and r.l <= stop) or (side < 0 and r.h >= stop): px, kind, xi = float(stop), "stop", i; break
    tier = 3.0 if e < 5 else 1.0
    cost = tier * ((SL + e * BP) * TOD_MULT_0951 + SP * e * TOD_MULT_0951 + SL + px * BP + (SX if kind == "stop" else 0))
    g = side * (px - e) / atr
    return g - cost / atr, g, kind, xi


def leg_spy(spy, m1_leg, xi):
    """SPY % move over a leg's OWN hold: its first minute's open -> the close of its exit minute (Skeptic fix 2)."""
    t0, t1 = m1_leg.index[0], m1_leg.index[xi]
    a, b = spy.loc[spy.index >= t0], spy.loc[spy.index <= t1]
    return float(b.iloc[-1].c) / float(a.iloc[0].o) - 1 if len(a) and len(b) else np.nan


def adv_tercile(adv, cuts):
    return 0 if adv < cuts[0] else (1 if adv < cuts[1] else 2)


def gap_bucket(g):
    a = abs(g)
    return None if a < .01 else ("1-2%" if a < .02 else ("2-5%" if a < .05 else ">5%"))


def selftest():
    idx = range(4)
    m = pd.DataFrame(dict(o=[100, 99.5, 99, 98.5], h=[100.2, 99.7, 99.1, 98.6], l=[99.4, 98.9, 98.4, 98.0], c=[99.5, 99, 98.5, 98.2]), index=idx)
    r = fade_trade(m, -1, 2.0); assert r[2] == "time" and abs(r[1] - (100 - 98.2) / 2.0) < 1e-9 and r[0] < r[1]   # short a gap-up
    up = pd.DataFrame(dict(o=[100, 101, 102.5], h=[100.5, 102.1, 103], l=[99.8, 100.9, 102.4], c=[100.4, 102, 102.8]), index=range(3))
    r = fade_trade(up, -1, 2.0); assert r[2] == "stop" and abs(r[1] + 1.0) < 1e-9                                  # stop at +1 ATR
    gapthru = pd.DataFrame(dict(o=[100, 102.5], h=[100.5, 103], l=[99.9, 102.4], c=[100.2, 102.8]), index=range(2))
    r = fade_trade(gapthru, -1, 2.0); assert r[2] == "stop" and abs(r[1] + 1.25) < 1e-9                             # opens through
    assert fade_trade(m, -1, 2.0)[3] == 3 and fade_trade(up, -1, 2.0)[3] == 1
    spy = pd.DataFrame(dict(o=[10.0, 10.1, 10.2, 10.3], c=[10.05, 10.15, 10.25, 10.35]), index=idx)
    assert abs(leg_spy(spy, up, 1) - (10.15 / 10.0 - 1)) < 1e-12                                          # own hold only
    assert adv_tercile(50, (100, 200)) == 0 and adv_tercile(150, (100, 200)) == 1 and adv_tercile(300, (100, 200)) == 2
    assert gap_bucket(0.005) is None and gap_bucket(-0.03) == "2-5%" and gap_bucket(0.07) == ">5%"
    sys.path.insert(0, str(ROOT.parent / "guild/research/xaeproc"))
    try:
        from eproc import eprocess
        e = eprocess(np.full(30, 0.2), CAP); assert e["edge_alarm_day"] is not None and e["harm_alarm_day"] is None
    except ImportError:
        pass
    print("selftest ok: fade trade (time exit, 1-ATR stop, gap-through fill, costs), gap buckets, e-process hook")


def main():
    import pyarrow.dataset as pds
    ap = argparse.ArgumentParser(); ap.add_argument("--date", required=True); ap.add_argument("--calendar", required=True)
    ap.add_argument("--live-earnings", required=True, help="mcf-data earnings/<D>.json (all names with earnings within +-4 sessions)")
    a = ap.parse_args(); D1 = pd.Timestamp(a.date).date()
    assert a.date >= START, "forward-only shadow: sessions from 2026-11-11"
    sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y")); sys.path.insert(0, str(HERE.parent / "xaeproc"))
    import lib
    from eproc import eprocess
    Dd = lib.daily().sort_values(["symbol", "date"]); Dd = Dd[Dd.date <= D1]
    pc = Dd.groupby("symbol").close.shift(1)
    tr = np.maximum(Dd.high - Dd.low, np.maximum((Dd.high - pc).abs(), (Dd.low - pc).abs()))
    Dd["pc"] = pc; Dd["atr"] = tr.groupby(Dd.symbol).transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
    Dd["ret"] = Dd.close / pc - 1; S = Dd[Dd.symbol == "SPY"].set_index("date"); Dd["sr"] = Dd.date.map(S.ret)
    def _b(g):
        x, y = g.sr.shift(1), g.ret.shift(1)
        return ((x * y).rolling(60, min_periods=40).mean() - x.rolling(60, min_periods=40).mean() * y.rolling(60, min_periods=40).mean()) / x.rolling(60, min_periods=40).var(ddof=0)
    Dd["beta"] = Dd.groupby("symbol", group_keys=False).apply(_b)
    T = Dd[Dd.date == D1].set_index("symbol")
    cal = pd.read_csv(a.calendar); cal["report_date"] = pd.to_datetime(cal.report_date).dt.date
    sess = sorted(Dd[Dd.symbol == "SPY"].date)
    prev = [d for d in sess if d < D1][-1]
    sel = cal[(cal.report_date == prev) & cal.timing.str.lower().isin(["amc", "time-after-hours"])]
    open_ = pd.Timestamp(f"{D1} 09:30", tz="America/New_York")
    snap = pd.to_datetime(sel.snapshot_at, utc=True).dt.tz_convert("America/New_York")
    assert (snap < open_).all(), "calendar snapshot not provably pre-open (Skeptic fix 3)"
    ev = set(sel.symbol)
    import json
    live = json.load(open(a.live_earnings)); assert live.get("day") == a.date, "live earnings snapshot is for another day"
    near = set(live.get("symbols", {})) | set(cal[(pd.to_datetime(cal.report_date) - pd.Timestamp(D1)).abs().dt.days <= 6].symbol)
    cuts = tuple(np.nanquantile(T.adv20.to_numpy(float), [1 / 3, 2 / 3]))                   # adv20 terciles that day (fix 4)
    def m1(sym):
        p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"
        if not p.exists(): return None
        df = pds.dataset(str(p), format="parquet").to_table().to_pandas()
        ix = "__index_level_0__"; df = df.set_index(ix) if ix in df.columns else df
        df = df[df.index.date == D1]; mm = df.index.hour * 60 + df.index.minute
        x = df[(mm >= 591) & (mm <= 955)][["open", "high", "low", "close"]]; x.columns = list("ohlc"); return x
    def day_gap(sym):
        p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"
        if sym not in T.index or not p.exists(): return None
        df = pds.dataset(str(p), format="parquet").to_table().to_pandas(); ix = "__index_level_0__"
        df = df.set_index(ix) if ix in df.columns else df; df = df[df.index.date == D1]; mm = df.index.hour * 60 + df.index.minute
        o = df[mm == 570]
        return float(o.open.iloc[0]) / float(T.loc[sym, "pc"]) - 1 if len(o) else None
    spy = m1("SPY"); assert spy is not None and len(spy), "no SPY bars for the session"
    rng = np.random.default_rng(int(pd.Timestamp(D1).strftime("%Y%m%d")))
    lab = [s.strip() for s in open(ROOT / "research/lab_symbols.txt") if s.strip()]
    rows = []
    for s in sorted(ev):
        if s not in T.index or not (T.loc[s, "adv20"] >= 60e6): continue
        g = day_gap(s); b = gap_bucket(g) if g is not None else None
        if b is None: continue
        side = -int(np.sign(g)); r = fade_trade(m1(s), side, float(T.loc[s, "atr"]))
        if r is None: continue
        beta = T.loc[s, "beta"] if np.isfinite(T.loc[s, "beta"]) else 1.0
        ms = m1(s); e_px = float(ms.iloc[0].o); ex = r[0] - side * beta * leg_spy(spy, ms, r[3]) * e_px / float(T.loc[s, "atr"])
        tq = adv_tercile(float(T.loc[s, "adv20"]), cuts)
        ctl = None
        for c in rng.permutation([x for x in lab if x not in near and x not in ev and x in T.index]):
            if not (T.loc[c, "adv20"] >= 60e6): continue
            if adv_tercile(float(T.loc[c, "adv20"]), cuts) != tq: continue
            gc = day_gap(c)
            if gc is None or gap_bucket(gc) != b: continue
            mc = m1(c); sc = -int(np.sign(gc)); rc = fade_trade(mc, sc, float(T.loc[c, "atr"]))
            if rc is None: continue
            bc = T.loc[c, "beta"] if np.isfinite(T.loc[c, "beta"]) else 1.0
            ctl = (c, rc[0], rc[1], rc[0] - sc * bc * leg_spy(spy, mc, rc[3]) * float(mc.iloc[0].o) / float(T.loc[c, "atr"])); break
        rows.append(dict(date=a.date, symbol=s, gap=round(g, 4), bucket=b, side=side, net=r[0], gross=r[1], kind=r[2], ex=ex,
                         ctl=ctl[0] if ctl else "", ctl_net=ctl[1] if ctl else np.nan, ctl_gross=ctl[2] if ctl else np.nan,
                         ctl_ex=ctl[3] if ctl else np.nan))
    out = HERE / "famc_forward.csv"
    F = pd.read_csv(out) if out.exists() else pd.DataFrame()
    F = pd.concat([F[F.date != a.date] if len(F) else F, pd.DataFrame(rows)], ignore_index=True); F.to_csv(out, index=False)
    x = F.dropna(subset=["ctl_ex"]).groupby("date").apply(lambda g: g.ex.mean() - g.ctl_ex.mean())
    st = eprocess(x.to_numpy(), CAP) if len(x) else None
    print(f"{a.date}: AMC events {len(ev)}, traded rows {len(rows)}; sessions so far {len(x)}; "
          f"RAW mean delta {x.mean():+.3f} R (unclipped; fix 5) vs clipped at cap {CAP}: {np.clip(x, -CAP, CAP).mean():+.3f}; "
          f"gross mean {F.gross.mean():+.3f}" + (f"; K_edge {st['K_edge']} K_harm {st['K_harm']} "
          f"(alarms at 20: edge day {st['edge_alarm_day']}, harm day {st['harm_alarm_day']})" if st else ""))
    print("Journal-only shadow; nothing trades. Educational only - not financial advice.")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
