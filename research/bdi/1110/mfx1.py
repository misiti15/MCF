"""MFX1 (research/bdi/1110/MFX1_PLAN.md, pre-registered and committed before this read): midday-flip open-book exit.
ONE config. 2-year lab lists bt_lab1104 enriched with 5-min marks (burst1/enrich.py -> <enr>), SPY 1-min cache, costs in,
locked block excluded (asserted). Also scores live 11-10 from the 7 journals + SIP 1-min bars.
Usage: python mfx1.py <enr dir> <scratch with <acct>/journal.db and bars/>   Educational only - not financial advice."""
import math, re, sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
E, S = Path(sys.argv[1]), Path(sys.argv[2]); HERE = Path(__file__).resolve().parent; TZ = "America/New_York"
LOCK = ("2024-11-01", "2025-02-28")
fam = lambda s: re.sub(r"\d.*", "", s).split("-")[0]
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(out[-1], flush=True)


def flip_of(mm, c, o):
    """mm: minute-of-day bar starts, c: 1-min closes; returns (M, F minute-of-day end, closes side) per MFX1."""
    i = np.searchsorted(mm, 719)            # 11:59 bar
    if i >= len(mm) or mm[i] != 719: return 0, None
    M = int(np.sign(c[i] / o - 1))
    if M == 0: return 0, None
    run = 0
    for k in range(i + 1, len(mm)):
        if mm[k] < 720 or mm[k] > 929: continue
        run = run + 1 if np.sign(c[k] / o - 1) == -M else 0
        if run == 15: return M, int(mm[k]) + 1
    return M, None


# ------------------------------------------------------------ SPY day facts (2 years)
b = pd.read_parquet("/home/user/MCF/data/cache_hist/1Min/SPY.parquet")
b["date"] = b.index.strftime("%Y-%m-%d"); b = b[~((b.date >= LOCK[0]) & (b.date <= LOCK[1]))]
b["mm"] = b.index.hour * 60 + b.index.minute; b = b[(b.mm >= 570) & (b.mm < 960)]
DAY = {}
for d, g in b.groupby("date"):
    if g.mm.iloc[0] != 570: continue
    o = g.open.iloc[0]; mm = g.mm.to_numpy(); c = g.close.to_numpy(float)
    M, F = flip_of(mm, c, o)
    j10 = np.searchsorted(mm, 599); oc = c[-1] / o - 1
    DAY[d] = dict(M=M, F=F, oc=oc, fo10=(c[j10] / o - 1) if j10 < len(c) else np.nan)
D = pd.DataFrame(DAY).T
assert not ((D.index >= LOCK[0]) & (D.index <= LOCK[1])).any()
D["dtype"] = np.where(D.oc > 0.0025, "up", np.where(D.oc < -0.0025, "down", "quiet"))
D["false_flip"] = D.F.notna() & (np.sign(D.oc.astype(float)) == D.M.astype(float))
fl = D[D.F.notna()]
p(f"SPY days {len(D)} (locked block excluded); flip days {len(fl)} ({len(fl) / len(D):.0%}); median flip "
  f"{int(fl.F.median()) // 60}:{int(fl.F.median()) % 60:02d}; false flips (closed back on the morning side) {int(fl.false_flip.sum())}")

# ------------------------------------------------------------ lab trades
rows = []
for f in sorted(E.glob("*.parquet")):
    t = pd.read_parquet(f); mk = np.load(str(f).replace(".parquet", "_mk.npy")).astype(np.float32)
    t = t.reset_index(drop=True)
    assert not ((t.date >= LOCK[0]) & (t.date <= LOCK[1])).any()
    t["Fm"] = t.date.map(D.F); t["M"] = t.date.map(D.M)
    t = t[t.Fm.notna() & (t.side == t.M)]
    if t.empty: continue
    Fm = t.Fm.astype(int).to_numpy()
    bstart = ((Fm - 5) // 5) * 5                      # last 5-min bar closing at or before F
    m0 = (t.tod // 100 * 60 + t.tod % 100).to_numpy(); xm = (t.xtod // 100 * 60 + t.xtod % 100).to_numpy()
    aff = (m0 < bstart) & (xm > bstart) & (bstart >= 590)
    t = t[aff].copy(); idx = t.index.to_numpy(); bs = bstart[aff]
    sl = np.clip((bs - 590) // 5, 0, 73)
    mrow = mk[idx]
    # mark at slot sl, ffill earlier slots if that bar is missing
    mm_ = pd.DataFrame(mrow).ffill(axis=1).to_numpy()
    t["mark"] = mm_[np.arange(len(t)), sl]
    t["cost"] = (1e-4 + 0.01 / t.entry) / t.stop_pct
    t["alt"] = t.mark - t.cost
    rows.append(t)
T = pd.concat(rows, ignore_index=True).dropna(subset=["alt", "r"])
T["d"] = T.alt - T.r; T["fam"] = T.setup.map(fam)
T["split"] = np.where(T.date <= "2025-12-31", "TRAIN", np.where(T.date <= "2026-10-05", "VALID", "LATE"))
T["dtype"] = T.date.map(D.dtype); T["s10"] = np.where(T.date.map(D.fo10).astype(float) >= 0, "above", "below")
T["ff"] = T.date.map(D.false_flip)
p(f"affected lab trades {len(T):,} ({T.setup.nunique()} setups, {T.date.nunique()} days); actual avg {T.r.mean():+.4f}R, "
  f"closed-at-flip avg {T.alt.mean():+.4f}R")
res = {}
for sp in ("TRAIN", "VALID", "LATE"):
    g = T[T.split == sp]
    if g.empty: continue
    daily = g.groupby("date").d.sum()
    t_ = daily.mean() / (daily.std(ddof=1) / math.sqrt(len(daily))) if len(daily) > 2 else np.nan
    best = daily.max(); res[sp] = dict(delta=daily.sum(), t=t_, wob=daily.sum() - best)
    p(f"{sp}: affected {len(g):,} on {len(daily)} flip days | actual {g.r.sum():+.1f}R ({g.r.mean():+.4f}) -> at flip "
      f"{g.alt.sum():+.1f}R ({g.alt.mean():+.4f}) | delta {daily.sum():+.1f}R, day-t {t_:.2f}, days better "
      f"{(daily > 0).mean():.0%}; best day {daily.idxmax()} {best:+.1f}R, delta w/o best {daily.sum() - best:+.1f}R")
    for col in ("dtype", "s10", "ff", "side"):
        x = g.groupby(col).agg(n=("d", "size"), delta=("d", "sum"), days=("date", "nunique"))
        p(f"   by {col}: " + "; ".join(f"{k} {int(v.n)} trades / {int(v.days)} days {v.delta:+.1f}R" for k, v in x.iterrows()))
V = T[T.split == "VALID"]
fg = V.groupby("fam").agg(n=("d", "size"), act=("r", "sum"), delta=("d", "sum"))
fg = fg[fg.n >= 30].sort_values("delta")
nb, nw = int((fg.delta > 0).sum()), int((fg.delta < 0).sum())
p(f"VALID families (>= 30 affected): {nb} better, {nw} worse of {len(fg)}")
for k, v in fg.iterrows(): p(f"   {k}: {int(v.n)} trades, actual {v.act:+.1f}R, delta {v.delta:+.1f}R")
sg = V.groupby("setup").agg(n=("d", "size"), delta=("d", "sum")); sg = sg[sg.n >= 30]
p(f"VALID setups (>= 30 affected): {int((sg.delta > 0).sum())} better / {int((sg.delta < 0).sum())} worse; worst 3: " +
  "; ".join(f"{k} {v.delta:+.1f}R" for k, v in sg.sort_values('delta').head(3).iterrows()) + "; best 3: " +
  "; ".join(f"{k} {v.delta:+.1f}R" for k, v in sg.sort_values('delta').tail(3).iterrows()))
v = res.get("VALID", {}); tr = res.get("TRAIN", {})
ok = (v.get("t", 0) >= 2.66 and tr.get("delta", 0) > 0 and v.get("wob", 0) > 0 and nb >= 0.6 * max(len(fg), 1))
p(f"VERDICT: VALID t {v.get('t', np.nan):.2f} vs full 2.66 / BAR90 2.39; TRAIN delta {tr.get('delta', np.nan):+.1f}R; "
  f"VALID w/o best {v.get('wob', np.nan):+.1f}R; families better {nb}/{len(fg)} -> {'PASS' if ok else 'FAIL'}"
  f"{'' if ok else (' (BAR90 met)' if v.get('t', 0) >= 2.39 and tr.get('delta', 0) > 0 and v.get('wob', 0) > 0 else '')}")

# ------------------------------------------------------------ live 11-10 (in-sample day of the idea)
spy = pd.read_parquet(S / "bars" / "SPY.parquet"); spy.index = pd.to_datetime(spy.index, utc=True).tz_convert(TZ)
mm = (spy.index.hour * 60 + spy.index.minute).to_numpy(); M, F = flip_of(mm, spy.close.to_numpy(float), spy.open.iloc[0])
p(f"\nLIVE 2026-11-10: morning side {M:+d}, flip F {F // 60}:{F % 60:02d} ET" if F else f"LIVE: no flip (M {M})")
if F:
    Ft = pd.Timestamp("2026-11-10", tz=TZ) + pd.Timedelta(minutes=F)
    bt = pd.Timestamp("2026-11-10", tz=TZ) + pd.Timedelta(minutes=((F - 5) // 5) * 5 + 5)   # close of that 5-min bar
    cache = {}
    def px(sym):
        if sym not in cache:
            f = S / "bars" / f"{sym}.parquet"
            if not f.exists(): cache[sym] = np.nan
            else:
                x = pd.read_parquet(f); x.index = pd.to_datetime(x.index, utc=True).tz_convert(TZ)
                x = x[x.index <= bt - pd.Timedelta(minutes=1)]; cache[sym] = float(x.close.iloc[-1]) if len(x) else np.nan
        return cache[sym]
    for a in ("p", "t1", "t2", "gy", "gen", "ex1", "ll"):
        c = sqlite3.connect(S / a / "journal.db")
        t = pd.read_sql("select * from trades where date='2026-11-10' and run_id=1", c)
        for col in ("entry_time", "exit_time"): t[col] = pd.to_datetime(t[col], utc=True, format="mixed").dt.tz_convert(TZ)
        t["risk"] = (t.entry - t.stop).abs() * t.shares; t["radj"] = t.pnl_adj / t.risk
        o_ = t[(t.side == M) & (t.entry_time < bt) & (t.exit_time > bt)].copy()
        if o_.empty: p(f"   {a}: 0 open on side {M:+d}"); continue
        sd = (o_.entry - o_.stop).abs()
        o_["alt"] = [M * (px(s) - e) / d - (1e-4 * px(s) + 0.01) / d for s, e, d in zip(o_.symbol, o_.entry, sd)]
        dl = (o_.alt - o_.radj); g = o_.assign(dl=dl).groupby("strategy").dl.sum()
        p(f"   {a}: {len(o_)} open lots actual {o_.radj.sum():+.2f}R -> at flip {o_.alt.sum():+.2f}R (delta {dl.sum():+.2f}R); "
          f"setups better {int((g > 0).sum())} / worse {int((g < 0).sum())}")
(HERE / "mfx1_out.txt").write_text("\n".join(out) + "\n\nEducational only - not financial advice.\n")
