"""Nightly 2026-11-03 cards: marks (monitor.json), watches (pdl p10-lowvol, R2A legs, RW3S), candidate cards, Primary
-2R per-setup stop (blocked signals + what-if on SIP 1-min bars), BRAKE-1 shadow (family stops -> half size after the 3rd).
Costs in: R = pnl_adj / $ risk. What-ifs are before costs (entry at the signal's ref price, stop / target / 15:50 close).
Usage: python today.py <scratch>   (needs fetch.py bars; fetches missing what-if symbols)
Educational only - not financial advice."""
import sys, sqlite3
from datetime import datetime, timezone
from pathlib import Path
import numpy as np, pandas as pd
WT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-nightly"
sys.path.insert(0, WT)
from mcf import setup_names
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; D = "2026-11-03"; TZ = "America/New_York"
rows = []
for a in ("p", "t1", "t2", "gy", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, strategy, symbol, side, entry, stop, target, shares, pnl, pnl_adj, exit_reason, entry_time, exit_time, mfe_r "
                    "from trades where run_id=1 and exit is not null", c)
    t["acct"] = a; rows.append(t)
T = pd.concat(rows, ignore_index=True); T["risk"] = (T.entry - T.stop).abs() * T.shares
T = T[T.risk > 0].copy(); T["R"] = T.pnl_adj / T.risk
T["nt"] = pd.to_datetime(T.entry_time, utc=True, format="mixed").dt.tz_convert(TZ)
T["et"] = pd.to_datetime(T.exit_time, utc=True, format="mixed").dt.tz_convert(TZ)
out = []; P = out.append


def card(code, since=None, acct=None):
    d = T[T.strategy == code]
    if acct: d = d[d.acct.isin(acct)]
    if since: d = d[d.date >= since]
    nm = setup_names.name(code)
    if d.empty: return f"{nm} ({code}){' since ' + since if since else ''}: no trades"
    by = d.groupby("date").R.agg(["sum", "size"]); best = by["sum"].idxmax(); tot = d.R.sum()
    ex = d[d.date != best].R.mean() if len(by) > 1 else np.nan
    busy = by.sort_values("size", ascending=False).head(3).index
    sess = by["sum"]
    return (f"{nm} ({code}){' since ' + since if since else ''}{' ' + ','.join(acct) if acct else ''}: {len(d)} trades / {len(by)} sessions "
            f"({(sess > 0).sum()} green), win {100 * (d.pnl_adj > 0).mean():.1f}%, avg R {d.R.mean():+.3f}, sum {tot:+.2f}R, ${d.pnl_adj.sum():+.2f}; "
            f"w/o best day ({best}) {ex:+.3f} (share {sess.max() / tot * 100 if tot > 0 else np.nan:.0f}%); 3 busiest avg {d[d.date.isin(busy)].R.mean():+.3f}; "
            f"today {int((d.date == D).sum())} trades {d[d.date == D].R.sum():+.2f}R ${d[d.date == D].pnl_adj.sum():+.2f}; per session {dict(sess.round(2))}")


P("== marks"); P(card("NS4-pm-vwap-reclaim-oversold-short-FD", "2026-10-27")); P(card("NS4-pm-vwap-reclaim-oversold-short-FD"))
G = "GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short"
P(card(G, "2026-10-27")); P(card(G))
P("== watches"); P(card("CWT14-failbrk-pdl-p10-lowvol-long", "2026-10-28")); P(card("CWT14-failbrk-pdl-p10-lowvol-long"))
for k in ("CWT14-failbrk-pdl-p05-R2A-long", "CWT14-failbrk-pdl-p05-R2A-short"): P(card(k))
r2 = T[(T.strategy == "CWT14-failbrk-pdl-p05-R2A-long") & (T.date == D)]
sc = r2.exit_reason.str.startswith("scaled")
P(f"R2A long today exits {r2.exit_reason.value_counts().to_dict()}; scaled {sc.sum()} avg {r2[sc].R.mean():+.3f}, plain {(~sc).sum()} avg {r2[~sc].R.mean():+.3f}; "
  f"plain with journal MFE >= 0.083R: {int(((~sc) & (r2.mfe_r >= 0.0833)).sum())}")
P(card("RW3S-gapdn-flowsell-short-FD", "2026-11-03"))
P("== candidates / Primary")
for k in ("NM-AR-AM-gapdown-capitulation-long", "MF1-945-flowsell-vwapup", "intraday_momentum", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
          "RW3-gapdn-rsi5pop-flowsell-short-FD", "MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD", "L3-gap-slope-fromopen-FD",
          "L3-gap-slope-rsi5hi-FD", "NS5-sma50-flush-oversold-long", "ST7-rsi50dn-long-pm-t1s1-FD", "NM-MF3-qqqdn-gapdn-FD", "NS4-pm-vwap-reclaim-oversold-short-FD"):
    P(card(k))
for k in ("L3-gap-slope-fromopen-FD", "L3-gap-slope-rsi5hi-FD", "ST7-rsi50dn-long-pm-t1s1-FD"):
    P(card(k, "2026-10-26" if k.startswith("ST7") else "2026-10-30", ["p"]))
Pd = T[T.acct == "p"].groupby("date").agg(n=("R", "size"), R=("R", "sum"), adj=("pnl_adj", "sum"), pnl=("pnl", "sum")).round(2)
s = Pd[Pd.index >= "2026-10-23"]
P("-- Primary per session since Day 1\n" + s.to_string())
P(f"since Day 1: {len(s)} sessions, {(s.adj > 0).sum()} positive, ${s.adj.sum():+.2f} after costs (${s.pnl.sum():+.2f} before); since start {len(Pd)} sessions, "
  f"{(Pd.adj > 0).sum()} positive, ${Pd.adj.sum():+.2f}")

# ---- -2R latch: blocked Primary signals today, what-if on bars
c = sqlite3.connect(S / "p" / "journal.db")
sg = pd.read_sql("select ts, symbol, strategy, side, ref_price, stop, target, reason from signals where day=? and run_id=1", c, params=(D,))
bl = sg[sg.reason.fillna("").str.contains("setup daily loss limit")].copy()
need = sorted(x for x in set(bl.symbol) if not (S / "bars" / f"{x}.parquet").exists())
if need:
    from mcf.data.alpaca_data import _client, fetch_bars
    a, b = datetime(2026, 11, 3, 14, 25, tzinfo=timezone.utc), datetime(2026, 11, 3, 21, 5, tzinfo=timezone.utc)
    for sym, g in fetch_bars(need, a, b, feed="sip", client=_client()).items(): g.to_parquet(S / "bars" / f"{sym}.parquet")


def whatif(r):
    f = S / "bars" / f"{r.symbol}.parquet"
    if not f.exists(): return np.nan
    b = pd.read_parquet(f); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
    t0 = pd.to_datetime(r.ts, utc=True).tz_convert(TZ).floor("1min") + pd.Timedelta(minutes=1)
    w = b[(b.index >= t0) & (b.index <= pd.Timestamp(f"{D} 15:50", tz=TZ))]
    e, st, tg = r.ref_price, r.stop, r.target; R = abs(e - st)
    if w.empty or not R: return np.nan
    for x in w.itertuples():
        if r.side == 1:
            if x.low <= st: return -1.0
            if tg == tg and tg and x.high >= tg: return (tg - e) / R
        else:
            if x.high >= st: return -1.0
            if tg == tg and tg and x.low <= tg: return (e - tg) / R
    return (w.close.iloc[-1] - e) / R * r.side


bl["wi"] = [whatif(r) for r in bl.itertuples()]
P("== -2R latch (Primary)")
for k, g in T[(T.acct == "p") & (T.date == D)].sort_values("et").groupby("strategy"):
    cum = g.R.cumsum(); hit = g[cum <= -2]
    P(f"{k}: day R {g.R.sum():+.2f}" + (f", latched after exit {hit.et.iloc[0].strftime('%H:%M:%S')}" if len(hit) else ""))
P(f"blocked {len(bl)}: " + str(bl.groupby("strategy").agg(n=("wi", "size"), first=("ts", "min"), wi_sum=("wi", "sum"), wi_avg=("wi", "mean")).round(3).to_dict("index")))
P(bl[["ts", "symbol", "strategy", "wi"]].round(2).to_string(index=False))

# ---- BRAKE-1 shadow: after the 3rd family stop of the day, new family lots at half size
FAM = {"RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "MF2-open-rsimidhi-flowsell-FD",
       "MF4-h40-open-flowsell", "MF4-h40-open-flowsell-FD"}
p = T[(T.acct == "p") & (T.date == D)].copy()
f = p[p.strategy.isin(FAM)]; stops = f[f.exit_reason == "stop"].sort_values("et")
P("== BRAKE-1 shadow")
P(f"family stops {len(stops)}: " + ", ".join(f"{r.strategy.split('-')[0]}{'-FD' if r.strategy.endswith('-FD') else ''} {r.symbol} {r.et.strftime('%H:%M')}" for r in stops.itertuples()))
act = p.R.sum()
if len(stops) >= 3:
    t3 = stops.et.iloc[2]; half = f[f.nt > t3]
    brake = act - 0.5 * half.R.sum()
    P(f"trigger at {t3.strftime('%H:%M:%S')}; family lots after: {len(half)} sum {half.R.sum():+.2f}R (${half.pnl_adj.sum():+.2f}); "
      f"Primary R actual {act:+.2f} -> with brake {brake:+.2f} (diff {brake - act:+.2f}R, ${-0.5 * half.pnl_adj.sum():+.2f})")
else:
    P(f"no trigger; actual = brake {act:+.2f}R")
txt = "\n".join(out); open(OUT / "today_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
