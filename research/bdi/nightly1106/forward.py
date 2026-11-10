"""Nightly 2026-11-06 forward shadows (no live change, journal-only):
  REG2  (owner "REG2 shadow" 11-05, day 3 of 5): Primary trades entered at/after 10:00 tagged kept / dropped by REG1 switch A
        (SPY at or above its 09:30 open at 10:00 -> keep shorts, drop longs; below -> keep longs, drop shorts). Appends
        research/bdi/reg2_shadow.csv (one row per Primary trade).
  FLOW1 flow1-book-sensor forward tally (best merged T 10:15 k 3 win filter; best Primary T 10:15 k 3 sumR filter; SPY rule control).
  L1    swing1103-L1 vol / inverse ETP long guard (proxy: symbol list, not the 20-session beta - documented).
  L2    swing1103-L2 rotation-turn trigger (QQQ new HOD 10:30-11:30 while IWM >= +0.40% and >= 0.10% under its HOD 5 min);
        sector exclusion (XLK / SMH names) not applied - no sector map in the journals.
  L3    swing1103-L3 up-morning day test (SPY >= +0.15% and IWM >= +0.25% at 10:00).
  L6    swing1103-L6 counter-index entries (short with SPY >= +0.25% from open at the entry bar, long with SPY <= -0.25%).
  LATCH latch1103-category-shadow: per account, latched setup-days and what-if of latch-skipped signals (raw delta = -sum what-if;
        excess = blocked what-if vs the setup's own live avg R from combined.csv).
  GEN   GEN-261026-03 halted-signal what-if (Gen account halt).
R = pnl_adj / $ risk (costs in) for trades; what-ifs before costs (SIP 1-min, entry at ref price, stop / target / 15:50).
Usage: python forward.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3, json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np, pandas as pd
WT = "/home/user/MCF"
sys.path.insert(0, WT); sys.path.insert(0, WT + "/research/bdi/flow1_1104")
import flow1
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; D = "2026-11-06"; TZ = "America/New_York"
out = []; P = out.append
T = pd.read_csv(OUT / "trades.csv")
T["nt"] = pd.to_datetime(T.nt, utc=True, format="mixed").dt.tz_convert(TZ)
T["et"] = pd.to_datetime(T.et, utc=True, format="mixed").dt.tz_convert(TZ)
T["r"] = T.radj


def bars(sym):
    b = pd.read_parquet(S / "bars" / f"{sym}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ); return b


spy, qqq, iwm = bars("SPY"), bars("QQQ"), bars("IWM")
o_spy, o_iwm = spy.open.iloc[0], iwm.open.iloc[0]
at10 = lambda b: b[b.index < pd.Timestamp(f"{D} 10:00", tz=TZ)].close.iloc[-1]   # last closed bar before 10:00
spy10, iwm10 = at10(spy) / o_spy - 1, at10(iwm) / o_iwm - 1
P(f"SPY vs open at 10:00 {spy10 * 100:+.2f}% (IWM {iwm10 * 100:+.2f}%) -> REG1 day {'UP (keep shorts)' if spy10 >= 0 else 'DOWN (keep longs)'}")

# ---- REG2
p = T[T.acct == "p"].copy()
after = p.nt >= pd.Timestamp(f"{D} 10:00", tz=TZ)
keep_side = -1 if spy10 >= 0 else 1
p["reg2"] = np.where(~after, "pre10", np.where(p.side == keep_side, "kept", "dropped"))
k, d = p[p.reg2 == "kept"], p[p.reg2 == "dropped"]
act = p.r.sum(); kept_only = p[p.reg2 != "dropped"].r.sum()
P(f"== REG2 day 3: Primary {len(p)} trades, actual {act:+.2f}R (${p.pnl_adj.sum():+.2f}); pre-10:00 {int((p.reg2 == 'pre10').sum())} "
  f"({p[p.reg2 == 'pre10'].r.sum():+.2f}R); kept {len(k)} avg {k.r.mean():+.3f} ({k.r.sum():+.2f}R, ${k.pnl_adj.sum():+.2f}); dropped {len(d)} "
  f"avg {d.r.mean():+.3f} ({d.r.sum():+.2f}R, ${d.pnl_adj.sum():+.2f}); kept-only book {kept_only:+.2f}R "
  f"(${p[p.reg2 != 'dropped'].pnl_adj.sum():+.2f}), diff {kept_only - act:+.2f}R")
rc = OUT.parent / "reg2_shadow.csv"
rows = p.assign(entry_et=p.nt.dt.strftime("%H:%M:%S"), spy_vs_open_1000=round(spy10, 5))[
    ["date", "entry_et", "symbol", "strategy", "side", "spy_vs_open_1000", "reg2", "r", "pnl_adj"]].rename(columns={"r": "R_costs"})
rows["R_costs"] = rows.R_costs.round(4); rows["pnl_adj"] = rows.pnl_adj.round(2)
if rc.exists():
    old = pd.read_csv(rc); old = old[old.date != D]; rows = pd.concat([old, rows], ignore_index=True)
rows.to_csv(rc, index=False)
reg2 = dict(date=D, spy10=round(spy10, 5), actual=round(act, 2), kept_only=round(kept_only, 2), n_kept=len(k), kept_avg=round(k.r.mean(), 3),
            n_dropped=len(d), dropped_avg=round(d.r.mean(), 3) if len(d) else None)

# ---- FLOW1 (flow1.py functions on today's trades)
acct = {"p": "primary", "t1": "testing", "t2": "testing2", "gy": "graveyard", "gen": "gen", "ex1": "explore1", "ll": "livelab"}
F = pd.DataFrame(dict(acct=T.acct.map(acct), date=T.date, side=T.side, ent=T.nt.dt.hour * 60 + T.nt.dt.minute + T.nt.dt.second / 60,
                      ext=T.et.dt.hour * 60 + T.et.dt.minute + T.et.dt.second / 60, r=T.r))
sp = spy.rename(columns=dict(open="o", high="h", low="l", close="c", volume="v"))
ctx = flow1.spy_ctx(sp)
flow = {}
for book, tt, (Tm, kk, m) in (("merged", F, (615, 3, "win")), ("primary", F[F.acct == "primary"], (615, 3, "sumR"))):
    L = flow1.later(tt, Tm, ctx); days = [D]
    w, st = flow1.weights(L, kk, m, "filter"); s = flow1.score(L, w, days)
    sig = flow1.signals(tt, Tm)
    ws = np.where(L.x_spy >= 0, 1.0, 0.0); ss = flow1.score(L, ws, days)
    ks = (L.x_spy >= 0).to_numpy(); on = float((L.r[ks] * (w[ks] - 1)).sum())
    flow[book] = dict(cfg=f"T{Tm // 60}:{Tm % 60:02d} k{kk} {m} filter", delta=s["delta"], excess=s["excess"], n_later=s["n_later"],
                      n_drop=s["n_drop"], kept_avg=s["kept_avg"], drop_avg=s["drop_avg"], on_spy=round(on, 2), spy_rule_delta=ss["delta"])
    P(f"== FLOW1 {book} {flow[book]['cfg']}: side states at 10:15 {sig[['side', 'n', 'sumR', 'win']].round(2).to_dict('records')}; "
      f"later {s['n_later']}, dropped {s['n_drop']} (avg {s['drop_avg']}), kept avg {s['kept_avg']}; delta {s['delta']:+.2f}R, excess {s['excess']:+.2f}R, "
      f"on top of SPY rule {on:+.2f}R; SPY-rule control delta {ss['delta']:+.2f}R")

# ---- L1 vol / inverse ETP longs
INV = {"UVIX", "UVXY", "VXX", "VIXY", "VIXM", "SVIX", "SVXY", "SQQQ", "SOXS", "SPXU", "SPXS", "SDS", "SH", "PSQ", "QID", "TZA", "SRTY",
       "FAZ", "SDOW", "DXD", "TECS", "LABD", "YANG", "DUST", "TSLQ", "NVDQ", "SPDN", "RWM", "TWM", "SCO", "KOLD", "ZSL", "WEBS", "HIBS"}
lg = T[T.side == 1]; A = lg[lg.symbol.isin(INV)]; B = lg[~lg.symbol.isin(INV) & lg.strategy.isin(A.strategy.unique())]
l1 = dict(n_A=len(A), A_avg=round(A.r.mean(), 3) if len(A) else None, n_B=len(B), B_avg=round(B.r.mean(), 3) if len(B) else None)
P(f"== L1 inverse/vol ETP longs: A {len(A)} {A.groupby('strategy').r.agg(['size', 'sum']).round(2).to_dict('index') if len(A) else ''} "
  f"avg {l1['A_avg']}; same setups elsewhere B {len(B)} avg {l1['B_avg']}")

# ---- L2 rotation-turn trigger
q = qqq.copy(); i = iwm.copy()
q["hod"] = q.high.cummax(); i["hod"] = i.high.cummax(); i["fo"] = i.close / o_iwm - 1; i["below"] = i.close <= i.hod * (1 - 0.001)
i["cond"] = (i.fo >= 0.004) & i.below
i["run5"] = i.cond.rolling(5).sum() >= 5
newhi = q.high > q.hod.shift(1)
win = (q.index >= pd.Timestamp(f"{D} 10:30", tz=TZ)) & (q.index <= pd.Timestamp(f"{D} 11:30", tz=TZ))
trig = q.index[win & newhi.values & i.run5.reindex(q.index).fillna(False).values]
FAM = ("RW3", "RW5", "MF2", "MF4")
fam = T[(T.side == -1) & T.strategy.str.startswith(FAM)]
if len(trig):
    t0 = trig[0]; tg = fam[(fam.nt >= t0) & (fam.nt <= t0 + pd.Timedelta(minutes=30))]; ot = fam[~fam.index.isin(tg.index)]
    l2 = dict(trigger=t0.strftime("%H:%M"), n_tag=len(tg), tag_avg=round(tg.r.mean(), 3) if len(tg) else None, n_other=len(ot), other_avg=round(ot.r.mean(), 3))
else:
    l2 = dict(trigger=None, n_tag=0, n_other=len(fam), other_avg=round(fam.r.mean(), 3))
P(f"== L2 rotation turn: {l2}")

# ---- L3 up-morning
qual = spy10 >= 0.0015 and iwm10 >= 0.0025
l3 = dict(qualifying=bool(qual), spy10=round(spy10 * 100, 2), iwm10=round(iwm10 * 100, 2))
P(f"== L3 up-morning day: {l3} (family shorts today {len(fam)} avg {fam.r.mean():+.3f})")

# ---- L6 counter-index entries
sc = spy.close / o_spy - 1
T["spy_at"] = [sc.asof(t.floor("1min")) for t in T.nt]
T["counter"] = ((T.side == -1) & (T.spy_at >= 0.0025)) | ((T.side == 1) & (T.spy_at <= -0.0025))
cm = T.groupby("strategy").r.transform("mean")
c, o = T[T.counter], T[~T.counter]
exc = (c.r - cm[T.counter]).mean() if len(c) else np.nan
l6 = dict(n_counter=len(c), counter_avg=round(c.r.mean(), 3), n_other=len(o), other_avg=round(o.r.mean(), 3), diff=round(c.r.mean() - o.r.mean(), 3),
          setup_adj_excess=round(exc, 3))
P(f"== L6 counter-index entries (all 5 accounts): {l6}; by account " +
  str(T.groupby(["acct", "counter"]).r.agg(["size", "mean"]).round(3).to_dict("index")))

# ---- LATCH shadow (accounts with a latched per-setup stop today: setup daily loss limit skips)
C = pd.read_csv(OUT / "combined.csv").set_index("setup")
from mcf.data.alpaca_data import _client, fetch_bars
lat = {}
allbl = []
for a in acct:
    cc = sqlite3.connect(S / a / "journal.db")
    sg = pd.read_sql("select ts, symbol, strategy, side, ref_price, stop, target, reason from signals where day=? and run_id=1", cc, params=(D,))
    bl = sg[sg.reason.fillna("").str.contains("setup daily loss limit")].copy(); bl["acct"] = a
    allbl.append(bl)
BL = pd.concat(allbl, ignore_index=True)
need = sorted(x for x in set(BL.symbol) if not (S / "bars" / f"{x}.parquet").exists())
if need:
    cl = _client()
    for j in range(0, len(need), 100):
        for sym, g in fetch_bars(need[j:j + 100], datetime(2026, 11, 6, 14, 25, tzinfo=timezone.utc), datetime(2026, 11, 6, 21, 5, tzinfo=timezone.utc),
                                 feed="sip", client=cl).items():
            g.to_parquet(S / "bars" / f"{sym}.parquet")
_bc = {}


def whatif(r):
    f = S / "bars" / f"{r.symbol}.parquet"
    if not f.exists(): return np.nan
    if r.symbol not in _bc: _bc[r.symbol] = bars(r.symbol)
    b = _bc[r.symbol]
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


BL = BL.sort_values("ts").drop_duplicates(["acct", "symbol", "strategy"])   # first skip per setup-symbol (refires repeat each poll)
BL["wi"] = [whatif(r) for r in BL.itertuples()]
BL["own"] = BL.strategy.map(C.avgR_c).fillna(0)
for a, g in BL.groupby("acct"):
    lat[a] = dict(setups_latched=int(g.strategy.nunique()), blocked=len(g), priced=int(g.wi.notna().sum()), raw_delta=round(-g.wi.sum(), 2),
                  excess_delta=round(-(g.wi - g.own).sum(), 2),
                  long=round(-g[g.side == 1].wi.sum(), 2), short=round(-g[g.side == -1].wi.sum(), 2))
P(f"== LATCH shadow (raw delta = R saved by the latch before costs; excess = vs setup's own live avg R): {lat}")
P("   GY latched setups: " + str(BL[BL.acct == "gy"].groupby("strategy").wi.agg(["size", "sum"]).round(1).sort_values("sum").to_dict("index")))

# ---- GEN-261026-03 halted signals what-if (Gen account halt from 10:50)
cg = sqlite3.connect(S / "gen" / "journal.db")
g3 = pd.read_sql("select ts, symbol, strategy, side, ref_price, stop, target, reason from signals where day=? and run_id=1 and strategy like 'GEN-261026-03%'", cg, params=(D,))
need = sorted(x for x in set(g3.symbol) if not (S / "bars" / f"{x}.parquet").exists())
if need:
    for sym, g in fetch_bars(need, datetime(2026, 11, 6, 14, 25, tzinfo=timezone.utc), datetime(2026, 11, 6, 21, 5, tzinfo=timezone.utc), feed="sip", client=_client()).items():
        g.to_parquet(S / "bars" / f"{sym}.parquet")
g3["wi"] = [whatif(r) for r in g3.itertuples()]
P(f"== GEN-261026-03 today: {len(g3)} signals, all {g3.reason.unique().tolist()}; what-if {g3.wi.sum():+.2f}R ({g3.wi.round(2).tolist()})")

json.dump(dict(reg2=reg2, flow1=flow, L1=l1, L2=l2, L3=l3, L6=l6, latch=lat), open(OUT / "forward.json", "w"), indent=1, default=str)
txt = "\n".join(out); open(OUT / "forward_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
# per-setup Primary latch (deduped first skip per setup-symbol), appended nightly1105
pp = BL[BL.acct == "p"].groupby("strategy").agg(n=("wi", "size"), first=("ts", "min"), wi=("wi", "sum")).round(2)
print("Primary latch per setup (deduped):", pp.to_dict("index"))
open(OUT / "forward_out.txt", "a").write("\nPrimary latch per setup (deduped): " + str(pp.to_dict("index")) + "\n")
