"""swing1118-L15 'EOD-loser short cover' - ONE pre-registered 2-year backtest (BDI 2026-11-18; rule fixed in
research/bdi/swings/hypotheses.jsonl before this script was run; configs = 1).

Rule: at the 15:30 5-min bar close, every short lot still open (entry tod <= 15:00, own exit xtod > 15:30) whose symbol is
<= -2.0% from today's open at that close is closed at that close. Alternative R = side x (c1530 - entry) / Ru minus 2 x
(1c + 1 bp) / Ru (both sides charged, conservative vs the booked r). Others keep their own exit.
Data: bt_lab1104 uncapped lab lists (production costs in r); entry = frames close at the entry tod; Ru = 0.25 x atr_d x geom
stop (as burst1/enrich.py); c1530 from research/bdi/cwt/test_b/data/headtail.parquet; open = c1500 / (1 + fromOpen1500/100).
Locked block 2024-11-01..2025-02-28 never read (lib.months() excludes it; asserted).
Usage: python l15_bt.py -> l15_bt_out.txt next to this file.  Educational only - not financial advice."""
import re, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402
BT = ROOT / "research/history2y/data/bt_lab1104"; HT = ROOT / "research/bdi/cwt/test_b/data/headtail.parquet"
DN = {"t1s1": 1.0, "t05s1": 1.0, "t1s05": 0.5, "t05s05": 0.5}; THR = -2.0; BAR = 1.5
LK = ("2024-11-01", "2025-02-28"); HERE = Path(__file__).resolve().parent
fam = lambda s: re.sub(r"\d.*", "", s).split("-")[0]
PRIM = ("L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD")
rows = []
for m in lib.months():
    assert m not in lib.LOCKED_MONTHS
    p = BT / f"sig_{m}.parquet"
    if not p.exists(): continue
    T = pd.read_parquet(p); T = T[(T.side == -1) & (T.tod <= 1500) & (T.xtod > 1530)].copy()
    if T.empty: continue
    T["date"] = T.date.astype(str); T["symbol"] = T.symbol.astype(str)
    f = lib.load_month(m, columns=["symbol", "date", "tod", "close", "fromOpen", "atr_d"])
    f["symbol"] = f.symbol.astype(str); f["date"] = f.date.astype(str)
    e = f.rename(columns={"close": "entry"})[["symbol", "date", "tod", "entry", "atr_d"]]
    T = T.merge(e, on=["symbol", "date", "tod"], how="left")
    o = f[f.tod == 1500][["symbol", "date", "close", "fromOpen"]]; o["open"] = o.close / (1 + o.fromOpen / 100)
    T = T.merge(o[["symbol", "date", "open"]], on=["symbol", "date"], how="left")
    a = pd.Timestamp(m + "-01")
    h = pd.read_parquet(HT, columns=["symbol", "date", "tod", "c"],
                        filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1)), ("tod", "==", 1530)])
    h["symbol"] = h.symbol.astype(str); h["date"] = pd.to_datetime(h.date).dt.date.astype(str)
    T = T.merge(h[["symbol", "date", "c"]], on=["symbol", "date"], how="left")
    rows.append(T); del f, h
    print(m, len(T), flush=True)
T = pd.concat(rows, ignore_index=True)
assert not T.date.between(*LK).any()
n0 = len(T); T = T.dropna(subset=["entry", "atr_d", "open", "c", "r"]); T = T[T.atr_d > 0]
T["Ru"] = 0.25 * T.atr_d * T.geom.map(DN); T["fo1530"] = (T.c / T.open - 1) * 100
T["alt"] = -(T.c - T.entry) / T.Ru - 2 * (0.01 + T.entry * 1e-4) / T.Ru
T["loser"] = T.fo1530 <= THR; T["d"] = T.alt - T.r; T["fam"] = T.setup.map(fam)
T["split"] = np.where(T.date <= "2025-12-31", "TRAIN", np.where(T.date <= "2026-10-05", "VALID", "LATE"))
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(out[-1], flush=True)
tt = lambda x: x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 and x.std() > 0 else np.nan
p(f"swing1118-L15 EOD-loser short cover | configs 1 | bar t {BAR} | short lots open at 15:30: {len(T)} (dropped {n0-len(T)} without marks)")
res = {}
for lab, X in (("RULE (loser <= -2% at 15:30)", T[T.loser]), ("MIRROR (not loser, reported only)", T[~T.loser])):
    p(f"== {lab}")
    for sp in ("TRAIN", "VALID", "LATE"):
        x = X[X.split == sp]; dd = x.groupby("date").d.sum()
        wo = dd.sum() - dd.max() if len(dd) else np.nan
        p(f"  {sp}: lots {len(x)} days {dd.size} | actual {x.r.mean():+.3f}R alt {x.alt.mean():+.3f}R | delta {x.d.sum():+.1f}R "
          f"({x.d.mean():+.3f}/lot) day-t {tt(dd):.2f} | {100*(dd>0).mean() if len(dd) else 0:.0f}% days better | best day "
          f"{dd.idxmax() if len(dd) else '-'} {dd.max() if len(dd) else 0:+.1f}R, w/o best {wo:+.1f}R")
        res[(lab[:4], sp)] = (x.d.sum(), tt(dd), wo)
R = T[T.loser]; V = R[R.split == "VALID"]
fv = V.groupby("fam").d.agg(["count", "sum", "mean"]); fv = fv[fv["count"] >= 30]
p(f"VALID families (>=30 lots): {int((fv['sum']>0).sum())} better / {int((fv['sum']<=0).sum())} worse: " +
  ", ".join(f"{k} {v['sum']:+.1f}" for k, v in fv.sort_values('sum', ascending=False).iterrows()))
sv = V.groupby("setup").d.agg(["count", "sum"]); sv = sv[sv["count"] >= 20]
p(f"VALID setups (>=20 lots): {int((sv['sum']>0).sum())} better ({sv.loc[sv['sum']>0,'sum'].sum():+.1f}R) / "
  f"{int((sv['sum']<=0).sum())} worse ({sv.loc[sv['sum']<=0,'sum'].sum():+.1f}R); worst " +
  ", ".join(f"{k} {v:+.1f}" for k, v in sv['sum'].nsmallest(4).items()))
for s in PRIM:
    x = R[R.setup == s]
    p(f"Primary short {s}: " + "; ".join(f"{sp} n {len(x[x.split==sp])} delta {x[x.split==sp].d.sum():+.1f}R" for sp in ("TRAIN", "VALID", "LATE")))
fam_ok = len(fv) > 0 and (fv["sum"] > 0).mean() >= 0.60
ok = res[("RULE", "VALID")][1] >= BAR and res[("RULE", "TRAIN")][0] > 0 and res[("RULE", "VALID")][2] > 0 and fam_ok
p(f"PASS {bool(ok)} (VALID t {res[('RULE','VALID')][1]:.2f} >= {BAR}; TRAIN delta {res[('RULE','TRAIN')][0]:+.1f}; "
  f"VALID w/o best {res[('RULE','VALID')][2]:+.1f}; families >= 60% better {fam_ok})")
p("Educational only - not financial advice.")
(HERE / "l15_bt_out.txt").write_text("\n".join(out) + "\n")
