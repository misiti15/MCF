"""Move Hunt (BDI step 0a, owner 2026-10-29): catalogue the day's biggest intraday moves and score live capture.

Definition (v1, fixed before looking at today's list):
  * Universe: liquid names = live-identical priors ADV >= $95M (the live lab floor) and universe_ok (config/default.yaml).
    Earnings-blackout names (state earnings/<day>.json, +-4 trading days) are KEPT and flagged.
  * Decision points: every 5-minute bar close 09:35..15:00 ET (decision price = that bar's close).
  * Move: from the decision close to the max high (long) / min low (short) of the 1-minute bars in the next 90 minutes,
    capped at 15:55 (the flatten). In daily-ATR units (atr_d of the lab frames). Per symbol and side the best decision
    point is kept; the catalogue = top 25 long + top 25 short symbols by move (one row per symbol-side).
  * Caught: a live trade (run 1, any of the 5 accounts) on the symbol in the move's direction with entry between
    decision - 30 min and the extreme. Captured R = sum of those trades' after-cost R (pnl_adj / $ risk).
  * Miss reason (first that applies): blackout / skipped signal (reason) / wrong side only / traded outside the move /
    no setup signalled.
Usage: python moves.py <scratch> <day> [--top 25]  -> research/bdi/moves/moves.csv (appends/replaces the day) and
<scratch>/mh/<day>/rows.parquet (every decision row with forward moves, for the precursor study).
Educational only - not financial advice."""
import json, pickle, sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd, yaml
sys.path.insert(0, "/home/user/MCF")
from mcf.backtest.engine import DayContext, universe_ok

S, D = Path(sys.argv[1]), sys.argv[2]
TOP = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 25
OUT = Path("/home/user/MCF/research/bdi/moves/moves.csv")
TZ = "America/New_York"
ACCTS = ("p", "t1", "t2", "gy", "gen")
day = pd.Timestamp(D).date()

F = pd.read_parquet(S / "mh" / D / "frames.parquet")
B1 = pd.read_parquet(S / "cov" / "days" / D / "bars.parquet")
PRI = pickle.loads((S / "cov" / "days" / D / "priors.pkl").read_bytes())
EB = json.loads((S / "p" / "earn.json").read_text())["symbols"]
cfg = yaml.safe_load(open("/home/user/MCF/config/default.yaml"))

# ---------------------------------------------------------------- liquid universe
liq = set()
for s, p in PRI.items():
    ctx = DayContext(symbol=s, date=day, bars=None, prev_close=p.prev_close, prev_high=p.prev_high, prev_low=p.prev_low,
                     atr=p.atr, avg_dollar_volume=p.adv, avg_cum_volume=p.avg_cum, avg_move=p.avg_move)
    if p.adv >= 95e6 and universe_ok(ctx, cfg):
        liq.add(s)

# ---------------------------------------------------------------- forward moves per decision row
rows = []
for s, g in B1.groupby("symbol"):
    if s not in liq:
        continue
    f = F[F.symbol == s]
    if f.empty:
        continue
    g = g.sort_index(); t1 = g.index; hi = g.high.to_numpy(); lo = g.low.to_numpy(); v = g.volume.to_numpy()
    mins = ((t1.hour - 9) * 60 + t1.minute - 30).to_numpy()
    cumv = np.cumsum(v); avgc = PRI[s].avg_cum
    for _, r in f.iterrows():
        tod = int(r.tod); m0 = (tod // 100 - 9) * 60 + tod % 100 - 30          # decision minute (bar close)
        w = (mins >= m0) & (mins < min(m0 + 90, 385))
        if w.sum() < 5 or not np.isfinite(r.atr_d) or r.atr_d <= 0:
            continue
        c = r.close; wh, wl, wm = hi[w], lo[w], mins[w]
        iu, idn = int(np.argmax(wh)), int(np.argmin(wl))
        k = np.searchsorted(mins, m0) - 1
        rvol = cumv[k] / avgc[min(k, len(avgc) - 1)] if k >= 0 and avgc is not None and avgc[min(k, len(avgc) - 1)] > 0 else np.nan
        rows.append(dict(symbol=s, tod=tod, close=c, atr_d=r.atr_d,
                         up_atr=(wh[iu] - c) / r.atr_d, up_min=int(wm[iu] - m0), up_mae=(c - wl[:iu + 1].min()) / r.atr_d,
                         dn_atr=(c - wl[idn]) / r.atr_d, dn_min=int(wm[idn] - m0), dn_mae=(wh[:idn + 1].max() - c) / r.atr_d,
                         rvol=rvol, **{k2: r[k2] for k2 in ("gap", "fromOpen", "vwapDistPct", "rsi", "rsi5", "volumeRatio", "volumeSurge",
                                                           "buyPressure", "heat", "dist_hod_atr", "dist_lod_atr", "dist_pdh_atr",
                                                           "dist_pdl_atr", "atrPct", "momentum", "spy_fo", "qqq_fo", "breadth",
                                                           "sma20_dist_pct", "pricePosition")}))
R = pd.DataFrame(rows)
R["blackout"] = R.symbol.isin(EB); R["adv"] = R.symbol.map(lambda s: PRI[s].adv)
R["atr_pct_d"] = R.atr_d / R.close * 100
R.to_parquet(S / "mh" / D / "rows.parquet")

# ---------------------------------------------------------------- live trades and signals, all accounts
T, G = [], []
for a in ACCTS:
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select symbol, strategy, side, entry_time, exit_time, entry, stop, shares, pnl_adj from trades "
                    "where date=? and run_id=1", c, params=(D,)); t["acct"] = a; T.append(t)
    sg = pd.read_sql("select symbol, strategy, side, ts, status, reason from signals where day=? and run_id=1", c, params=(D,))
    sg["acct"] = a; G.append(sg)
T = pd.concat(T); G = pd.concat(G)
T["et"] = pd.to_datetime(T.entry_time, utc=True, format="mixed").dt.tz_convert(TZ)
T["risk"] = (T.entry - T.stop).abs() * T.shares
T["R"] = T.pnl_adj / T.risk.replace(0, np.nan)
G["et"] = pd.to_datetime(G.ts, utc=True, format="mixed").dt.tz_convert(TZ)
mod = lambda x: x.dt.hour * 60 + x.dt.minute - 570 + x.dt.second / 60
T["m"] = mod(T.et); G["m"] = mod(G.et)

# ---------------------------------------------------------------- catalogue
cat = []
for sset, RR in (("all", R), ("tradable", R[~R.blackout])):
  for side, col, mn, mae, sgn in (("long", "up_atr", "up_min", "up_mae", 1), ("short", "dn_atr", "dn_min", "dn_mae", -1)):
    best = RR.loc[RR.groupby("symbol")[col].idxmax()].sort_values(col, ascending=False).head(TOP)
    for rank, (_, r) in enumerate(best.iterrows(), 1):
        m0 = (r.tod // 100 - 9) * 60 + r.tod % 100 - 30; m1 = m0 + r[mn]
        ts = T[T.symbol == r.symbol]; gs = G[G.symbol == r.symbol]
        inwin = lambda x: x[(x.m >= m0 - 30) & (x.m <= m1)]
        right = inwin(ts[ts.side == sgn]); wrong = inwin(ts[ts.side == -sgn])
        sk = inwin(gs[(gs.side == sgn) & (gs.status != "submitted")])
        if len(right):
            why = "caught"
        elif r.blackout:
            why = "blackout"
        elif len(sk):
            why = "skipped: " + "; ".join(sorted(set(sk.reason.fillna("?").str[:40])))[:120]
        elif len(wrong):
            why = "wrong side only"
        elif len(ts):
            why = "traded outside the move"
        else:
            why = "no setup signalled"
        hhmm = lambda m: f"{int(9 + (m + 30) // 60):02d}:{int((m + 30) % 60):02d}"
        ed = EB.get(r.symbol, [])
        cat.append(dict(date=D, set=sset, side=side, rank=rank, symbol=r.symbol, decision=hhmm(m0), extreme=hhmm(m1), move_atr=round(r[col], 2),
                        move_pct=round(r[col] * r.atr_d / r.close * 100, 2), mae_before_atr=round(max(r[mae], 0), 2),
                        adv_musd=round(r.adv / 1e6), blackout=bool(r.blackout), earnings_dates=";".join(ed),
                        caught_by=";".join(f"{a}:{s}" for a, s in sorted(set(zip(right.acct, right.strategy)))),
                        n_right=len(right), r_captured=round(right.R.sum(), 2), n_wrong=len(wrong), r_wrong=round(wrong.R.sum(), 2),
                        miss_reason=why, any_trade_today=len(ts) > 0,
                        **{k: (round(float(r[k]), 3) if pd.notna(r[k]) else None) for k in
                           ("gap", "fromOpen", "vwapDistPct", "rsi", "rsi5", "rvol", "volumeRatio", "buyPressure", "heat",
                            "dist_hod_atr", "dist_lod_atr", "dist_pdh_atr", "dist_pdl_atr", "atr_pct_d", "spy_fo", "breadth")}))
C = pd.DataFrame(cat)
ALL = C
old = pd.read_csv(OUT) if OUT.exists() else pd.DataFrame()
if len(old):
    old = old[old.date != D]
pd.concat([old, ALL]).to_csv(OUT, index=False)
print(f"liquid names {len(liq)}, decision rows {len(R)}, live trades {len(T)} ({T.symbol.nunique()} symbols)")
for sset in ("all", "tradable"):
  C = ALL[ALL.set == sset]; print(f"\n===== set: {sset} (top {TOP} per side{'' if sset == 'all' else ', earnings-blackout names removed'})")
  print(C[["side", "rank", "symbol", "decision", "extreme", "move_atr", "move_pct", "mae_before_atr", "blackout", "n_right",
           "r_captured", "n_wrong", "miss_reason"]].to_string(index=False))
  cr = C.n_right.gt(0)
  print(f"\nCAPTURE RATE: {cr.sum()}/{len(C)} = {cr.mean():.0%} caught in the right direction; R captured {C.r_captured.sum():+.2f}; "
        f"wrong-direction trades {C.n_wrong.sum()} ({C.r_wrong.sum():+.2f}R)")
  for sd in ("long", "short"):
      x = C[C.side == sd]; print(f"  {sd}: {x.n_right.gt(0).sum()}/{len(x)} caught, R {x.r_captured.sum():+.2f}")
  nb = C[~C.blackout]; print(f"  excluding blackout names: {nb.n_right.gt(0).sum()}/{len(nb)}")
  print(C.miss_reason.str.split(":").str[0].value_counts().to_string())
A = ALL[(ALL.set == "all") & ALL.blackout]
prev = str((pd.Timestamp(D) - pd.offsets.BDay(1)).date())
ev = A.earnings_dates.fillna("").apply(lambda x: bool({D, prev} & set(x.split(";"))))
print(f"\nblackout movers in the 'all' set: {len(A)}; reporting today or after yesterday's close (event day): {ev.sum()}; "
      f"inside the +-4-day window but not the event day: {(~ev).sum()}")
