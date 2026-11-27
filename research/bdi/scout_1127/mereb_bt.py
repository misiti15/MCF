"""SCOUT-1127 MEREB1: month-end pension-rebalancing flow into the close (backlog scout-1127-mereb1-*).

PRE-REGISTERED 2026-11-27 (evening, market closed), before any trade below was simulated or scored.
Educational only - not financial advice.
Mechanism (sources, via WebSearch summaries): balanced funds / pensions rebalance to fixed equity-bond weights at month-end;
broker desks (BNP, GS, Citadel Securities 2026) publish month-end US-equity buy/sell estimates driven by month-to-date equity
vs bond performance, and note the biggest month-end moves come "on the upside at the end of periods of equity
underperformance"; academic: month-end liquidity-demand pressure and reversal (RFS 33(1)). Long side = after equities
LAGGED bonds month-to-date, rebalancers must BUY equities into the last session's close.
Signal S = SPY MTD - TLT MTD, both from the prior month's last close to the PRIOR day's close (known before the open;
daily SIP bars, adjustment=all, fetched GET-only from Alpaca). Event day = last trading session of the calendar month.
Trade: SPY, entry at the open of the T bar, stop = entry -/+ 0.25 x SPY ATR14 (RTH daily true range, prior 14 sessions),
no target, flat at the 15:55 bar open (stop-first, a bar opening through the stop fills at its open).
Grid (8 configs): side {LONG if S < -th, SHORT if S > +th} x th {0, 2%} x T {14:00, 15:00}.
Data: SPY 1-min RTH 2016-01..2026-11-04 (2016-22 SIP raw from the QQQOPEN-1127 scratch, read-only; cache_fresh; cache_hist).
Locked block 2024-11-01..2025-02-28 dropped at load (minute AND daily) and asserted absent; months whose MTD base or event
day falls in it are skipped (Nov 2024 - Mar 2025 base). Splits: EARLY 2016-01..2022-09, T2 2022-10..2024-09,
RECENT 2024-10..2026-11-04 (lock removed).
Costs: LIVE-L (primshorts_1126 cells, as IDXDIP-1127) first, LR8 alongside.
Controls: (a) same side/time/stop on every NON-event day (unconditional drift); (b) 500 random draws of the same number of
non-event days (rule day-mean must be >= 95th pct); (c) the opposite-signal event days (complement).
Pass (Testing bar, rule 22): t (per-trade = per-day here) >= 0.9 x max(1.5, sqrt(2 ln N)), N = run total 8 + ASYMREV1 6 = 14
(bar 2.07; within-lineage bar 0.9 x t_req(8) = 1.835 also printed); positive in EARLY, T2 and RECENT; avg R w/o best day
> 0 and best day share < 50%; positive years >= 54%; control (b) >= 95th pct; n >= 30.
Usage: python mereb_bt.py SPY_RAW_2016_2022 DAILY_DIR -> mereb_bt_out.txt
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
MAIN = Path("/home/user/MCF"); sys.path.insert(0, str(MAIN))
from mcf.research.gates import tod_cost_mult, t_required  # noqa: E402
HERE = Path(__file__).resolve().parent
LOCK = ("2024-11-01", "2025-02-28")
CELLS = json.load(open(HERE.parents[1] / "primshorts_1126/cells_live.json"))
PB = [0, 5, 10, 20, 50, 100, 1e9]; PBL = ["<5", "5-10", "10-20", "20-50", "50-100", "100+"]; KIND = {0: "market", 1: "stop"}
rng = np.random.default_rng(20261127); NDRAW = 500
NRUN = 14; TB = round(max(1.35, 0.9 * t_required(NRUN)), 3); TB8 = round(max(1.35, 0.9 * t_required(8)), 3)
inlock = lambda d: (pd.Series(d).astype(str) >= LOCK[0]).to_numpy() & (pd.Series(d).astype(str) <= LOCK[1]).to_numpy()

def load_min(raw):
    parts = [pd.read_parquet(raw), pd.read_parquet(MAIN / "data/cache_fresh/1Min/SPY.parquet"), pd.read_parquet(MAIN / "data/cache_hist/1Min/SPY.parquet")]
    out = []
    for p in parts:
        p = p[["open", "high", "low", "close"]].copy(); p.index = pd.DatetimeIndex(p.index).tz_convert("America/New_York"); out.append(p)
    df = pd.concat(out).sort_index(); df = df[~df.index.duplicated(keep="last")].between_time("09:30", "15:59")
    df = df[~inlock(df.index.date)]; df = df[df.index.date <= pd.Timestamp("2026-11-04").date()]
    assert not inlock(df.index.date).any(); return df

def load_daily(dd, sym):
    d = pd.read_parquet(Path(dd) / f"{sym}_daily.parquet"); d["date"] = pd.to_datetime(d.t).dt.tz_convert("America/New_York").dt.date.astype(str)
    d = d[~inlock(d.date)]; d = d[d.date <= "2026-11-04"]; assert not inlock(d.date).any()
    return d.set_index("date").c

def main(raw, dd):
    M = load_min(raw); M["date"] = M.index.date.astype(str); M["mn"] = M.index.hour * 60 + M.index.minute
    days = sorted(M.date.unique())
    # daily RTH stats from minute bars for ATR14
    g = M.groupby("date"); DH, DL, DC = g.high.max(), g.low.min(), g.close.last()
    pcl = DC.shift(1); tr = pd.concat([DH - DL, (DH - pcl).abs(), (DL - pcl).abs()], axis=1).max(axis=1)
    gapok = pd.Series(pd.to_datetime(days), index=days).diff().dt.days <= 5   # reset across the lock hole
    atr = tr.where(gapok).rolling(14, min_periods=14).mean().shift(1)
    spy, tlt = load_daily(dd, "SPY"), load_daily(dd, "TLT")
    dl = pd.DataFrame({"spy": spy, "tlt": tlt}).dropna(); dl.index = dl.index.astype(str)
    mon = pd.Series(dl.index.str[:7], index=dl.index)
    last = dl.groupby(mon.values).apply(lambda x: x.index.max())   # last session per month (daily file)
    ev = []
    mlist = sorted(last.index)
    for i, m in enumerate(mlist):
        if i == 0: continue
        pm = mlist[i - 1]; base = last[pm]; d = last[m]
        if (pd.Period(m, "M") - pd.Period(pm, "M")).n != 1: continue
        if m == "2026-11" or inlock([base, d]).any(): continue
        if pd.Timestamp(d).day < 25: continue          # month truncated by a data hole
        prev = dl.index[dl.index.get_loc(d) - 1]
        if prev <= base: continue
        S = (dl.spy[prev] / dl.spy[base] - 1) - (dl.tlt[prev] / dl.tlt[base] - 1)
        ev.append((d, S))
    EV = pd.DataFrame(ev, columns=["date", "S"]).set_index("date")
    o = {d: v for d, v in M.groupby("date")}
    def trade(d, side, T):
        x = o.get(d); a = atr.get(d, np.nan)
        if x is None or not np.isfinite(a): return None
        mn = x.mn.to_numpy(); j = np.searchsorted(mn, T)
        if j >= len(mn) or mn[j] != T: return None
        O, H, L = x.open.to_numpy(), x.high.to_numpy(), x.low.to_numpy()
        fill = O[j]; risk = 0.25 * a; stop = fill - side * risk; kind = 0; px = None
        for k in range(j, len(O)):
            if mn[k] >= 955: px = O[k]; break
            if (L[k] <= stop) if side == 1 else (H[k] >= stop):
                px = O[k] if (k > j and ((O[k] < stop) if side == 1 else (O[k] > stop))) else stop; kind = 1; break
        if px is None: px = x.close.to_numpy()[-1]
        return dict(date=d, side=side, T=T, entry=fill, exit_px=px, risk=risk, kind=kind, gross=side * (px - fill) / risk)
    def costs(t):
        price, risk, kind = t.entry.to_numpy(float), t.risk.to_numpy(float), t.kind.to_numpy(int)
        pb = pd.cut(price, PB, labels=PBL, right=False).astype(str)
        ab = np.array([CELLS.get(f"{p}|{KIND[k]}", CELLS[f"*|{KIND[k]}"])[:2] for p, k in zip(pb, kind)])
        t["r"] = t.gross - (ab[:, 0] / (risk / price * 1e4) + ab[:, 1])
        tod = (t["T"] // 60 * 100 + t["T"] % 60).to_numpy()
        ec = (0.01 + price * 1e-4) * tod_cost_mult(tod); xc = 0.01 + t.exit_px.to_numpy(float) * 1e-4 + np.where(kind == 1, 0.02, 0.0)
        br = np.where(t.side.to_numpy() < 0, 1.2e-4 * price, 0.0); t["r_lr8"] = t.gross - (ec + xc + br) / risk
        return t
    split = lambda d: np.where(d <= "2022-09-30", "EARLY", np.where(d <= "2024-09-30", "T2", "RECENT"))
    def st(x):
        x = np.asarray(x, float); n = len(x)
        return (n, round(x.mean(), 3) if n else None, round(x.mean() / (x.std(ddof=1) / np.sqrt(n)), 2) if n > 2 else None)
    out = []
    def p(*a): out.append(" ".join(map(str, a))); print(out[-1], flush=True)
    p(f"SCOUT-1127 MEREB1 | SPY 1-min 2016-01..2026-11-04 (lock dropped) | events {len(EV)} month-ends | configs 8 (run total {NRUN}; bar {TB}, within-lineage {TB8}) | LIVE-L costs, LR8 alongside")
    p(f"S (SPY MTD - TLT MTD at prior close): mean {EV.S.mean():+.4f}, share < 0 {(EV.S < 0).mean():.0%}, share < -2% {(EV.S < -.02).mean():.0%}, > +2% {(EV.S > .02).mean():.0%}")
    nonev = [d for d in days if d not in EV.index]
    for T in (840, 900):
        for side in (1, -1):
            A = pd.DataFrame([r for r in (trade(d, side, T) for d in nonev) if r]); A = costs(A)
            p(f"-- control (a) all non-event days, {'LONG' if side == 1 else 'SHORT'} {T // 60}:00: n {len(A)} avg {A.r.mean():+.3f} (gross {A.gross.mean():+.3f}, LR8 {A.r_lr8.mean():+.3f}) t {st(A.r)[2]}")
            for th in (0.0, 0.02):
                sel = EV.index[(EV.S < -th) if side == 1 else (EV.S > th)]; com = EV.index[~((EV.S < -th) if side == 1 else (EV.S > th))]
                X = pd.DataFrame([r for r in (trade(d, side, T) for d in sel) if r])
                name = f"MEREB1|{'L' if side == 1 else 'S'}|th{th:.0%}|{T // 60}:00"
                if len(X) < 5: p(f"== {name}: n {len(X)} too few"); continue
                X = costs(X); C = costs(pd.DataFrame([r for r in (trade(d, side, T) for d in com) if r]))
                n, m, t = st(X.r); gd = X.set_index("date").r
                share = gd.max() / gd.sum() if gd.sum() > 0 else float("nan"); wob = gd.drop(gd.idxmax()).mean()
                sp = {k: st(X.r[split(X.date) == k]) for k in ("EARLY", "T2", "RECENT")}
                yrs = X.groupby(X.date.str[:4]).r.mean(); py = float((yrs > 0).mean())
                dm = A.r.to_numpy(); draws = np.array([rng.choice(dm, n, replace=False).mean() for _ in range(NDRAW)]); pct = float((draws < m).mean())
                ok = (t or 0) >= TB and all((v[1] or -1) > 0 for v in sp.values()) and wob > 0 and share < .5 and py >= .54 and pct >= .95 and n >= 30
                p(f"== {name}: n {n} avg {m:+.3f} t {t} | gross {X.gross.mean():+.3f} LR8 {X.r_lr8.mean():+.3f} | stops {int((X.kind == 1).sum())} | w/o best day {wob:+.3f} best share {share:.0%}")
                p(f"   EARLY {sp['EARLY']} T2 {sp['T2']} RECENT {sp['RECENT']} | positive years {py:.0%} {yrs.round(3).to_dict()}")
                p(f"   control (b) random non-event days ({NDRAW} draws): mean {draws.mean():+.3f} p95 {np.quantile(draws, .95):+.3f} -> pct {pct:.0%} | complement event days avg {C.r.mean():+.3f} (n {len(C)})")
                p(f"   PASS (Testing bar t {TB}) {ok}")
    p("Educational only - not financial advice.")
    (HERE / "mereb_bt_out.txt").write_text("\n".join(out) + "\n")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
