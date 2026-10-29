"""p3_1029 step 1+2: Primary's last 10 live (paper) sessions 2026-10-15..10-28 - loser autopsy by type and funding-gate math.

Journal: origin/mcf-data:journal.db (run 1 = real paper trades), copied to <scratch>/p/journal.db
(`git show origin/mcf-data:journal.db > <scratch>/p/journal.db`). SIP 1-min bars (read-only Alpaca market data, as
nightly1028/fetch.py) for every Primary loser's symbol-day -> <scratch>/bars_p3/<date>/<sym>.parquet.

Costs in: P/L = journal pnl_adj; R = pnl_adj / $ risk (|entry - stop| x shares).

Loser = pnl_adj < 0. Types (tags can overlap; the exclusive type uses the order A, B, C, Other):
  A  execution: stop exit filled > 2c/share beyond the stop price, OR the entry's quote was a spread-gate near-miss
     (spread_bps >= 24 = 80% of the 30 bps gate, or spread >= 20% of the stop distance = 80% of the 25% gate).
  B  correlated: another Primary LOSER on the same symbol, or on the same sector ETF (research/bdi/indexlink/linkage.csv
     sector_etf) on the same side, entered within 30 min of this one on the same day (different trade).
  C  late reversal: the trade was open at 15:30 and was at >= 0 R (mark at the 15:29 1-min close, before costs) at 15:30,
     and closed as a loser at/after 15:30 (stop after 15:30 or the 15:55 flatten).
Usage: python autopsy.py <scratch>     Educational only - not financial advice."""
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/user/MCF")
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; TZ = "America/New_York"
DAYS = ["2026-10-15", "2026-10-16", "2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23",
        "2026-10-26", "2026-10-27", "2026-10-28"]
c = sqlite3.connect(S / "p" / "journal.db")
T = pd.read_sql("select * from trades where run_id=1 and date between ? and ?", c, params=(DAYS[0], DAYS[-1]))
assert sorted(T.date.unique()) == DAYS, sorted(T.date.unique())
T["risk"] = (T.entry - T.stop).abs() * T.shares
T["R"] = np.where(T.risk > 0, T.pnl_adj / T.risk, np.nan)
for x, y in [("nt", "entry_time"), ("et", "exit_time")]:
    T[x] = pd.to_datetime(T[y], utc=True, format="mixed").dt.tz_convert(TZ)
meta = T.meta.fillna("{}").map(lambda m: json.loads(m[:m.rfind("}") + 1] or "{}") if "{" in m else {})
T["spread_bps"] = meta.map(lambda m: m.get("spread_bps"))
T["bid"] = meta.map(lambda m: m.get("bid")); T["ask"] = meta.map(lambda m: m.get("ask"))
T["spread_frac"] = (T.ask - T.bid) / (T.entry - T.stop).abs()
T["stop_slip"] = np.where(T.exit_reason == "stop", T.side * (T.stop - T.exit), np.nan)   # $/share beyond the stop (+ = adverse)
lk = pd.read_csv("/home/user/MCF/research/bdi/indexlink/linkage.csv", usecols=["symbol", "sector_etf", "is_etf"])
sec = dict(zip(lk.symbol, lk.sector_etf))
T["sector"] = T.symbol.map(sec).fillna("?")
L = T[T.pnl_adj < 0].copy()

# --- Type C needs the 15:29 1-min close (SIP)
from mcf.data.alpaca_data import _client, fetch_bars  # noqa: E402
cl = None
px1529 = {}
late = L[(L.nt.dt.strftime("%H:%M") < "15:30") & (L.et.dt.strftime("%H:%M") >= "15:30")]
for d, g in late.groupby("date"):
    D = S / "bars_p3" / d; D.mkdir(parents=True, exist_ok=True)
    need = [s for s in g.symbol.unique() if not (D / f"{s}.parquet").exists()]
    if need:
        cl = cl or _client()
        a = pd.Timestamp(f"{d} 15:25", tz=TZ).tz_convert("UTC").to_pydatetime()
        z = pd.Timestamp(f"{d} 15:31", tz=TZ).tz_convert("UTC").to_pydatetime()
        for s, b in fetch_bars(need, a, z, feed="sip", client=cl).items():
            b.to_parquet(D / f"{s}.parquet")
    for s in g.symbol.unique():
        f = D / f"{s}.parquet"
        if f.exists():
            b = pd.read_parquet(f); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
            b = b[b.index.strftime("%H:%M") == "15:29"]
            if len(b):
                px1529[(d, s)] = float(b.close.iloc[-1])
L["px1529"] = [px1529.get((d, s)) for d, s in zip(L.date, L.symbol)]
L["R1530"] = L.side * (L.px1529 - L.entry) / (L.entry - L.stop).abs()

# --- tags
L["A_slip"] = L.stop_slip > 0.02
L["A_spread"] = (L.spread_bps >= 24) | (L.spread_frac >= 0.20)
L["A"] = L.A_slip | L.A_spread
b_sym, b_sec = [], []
for r in L.itertuples():
    o = L[(L.date == r.date) & (L.id != r.id) & ((L.nt - r.nt).abs() <= pd.Timedelta(minutes=30))]
    b_sym.append(bool((o.symbol == r.symbol).any()))
    b_sec.append(bool(((o.sector == r.sector) & (o.side == r.side) & (r.sector != "?")).any()))
L["B_sym"], L["B_sec"] = b_sym, b_sec
L["B"] = L.B_sym | L.B_sec
L["C"] = L.R1530.notna() & (L.R1530 >= 0) & (L.et.dt.strftime("%H:%M") >= "15:30")
L["type"] = np.select([L.A, L.B, L.C], ["A", "B", "C"], "Other")

out = []
P = lambda *x: out.append(" ".join(str(y) for y in x))
P(f"Primary run 1, {DAYS[0]}..{DAYS[-1]} (10 sessions): {len(T)} trades, {len(L)} losers (pnl_adj < 0), "
  f"losers' R {L.R.sum():+.2f}, $ {L.pnl_adj.sum():+.2f}; all trades R {T.R.sum():+.2f}, $ {T.pnl_adj.sum():+.2f}")
P(f"losers with a 15:29 SIP mark (open at 15:30): {L.px1529.notna().sum()} of {len(late)}")
P("\n-- exclusive type (order A, B, C, Other)")
g = L.groupby("type").agg(n=("id", "size"), R=("R", "sum"), usd=("pnl_adj", "sum"), avgR=("R", "mean")).round(3)
g["share_of_loser_usd"] = (g.usd / L.pnl_adj.sum()).round(3)
P(g.to_string())
P("\n-- tags (overlapping)")
for k in ("A_slip", "A_spread", "A", "B_sym", "B_sec", "B", "C"):
    d = L[L[k]]
    P(f"{k:9s} n {len(d):3d}  R {d.R.sum():+7.2f}  $ {d.pnl_adj.sum():+9.2f}")
P("\n-- stop exits (all trades): slip $/share beyond stop: n", int(T.stop_slip.notna().sum()), "median",
  round(T.stop_slip.median(), 4), "mean", round(T.stop_slip.mean(), 4), "share > 2c", round((T.stop_slip > 0.02).mean(), 3),
  "| extra R cost of slip beyond 2c (losers):",
  round(((L.stop_slip.clip(lower=0.02) - 0.02) * L.shares).sum(), 2), "$")
P("\n-- by date (losers)")
P(L.groupby(["date", "type"]).agg(n=("id", "size"), usd=("pnl_adj", "sum")).unstack(fill_value=0).round(2).to_string())
P("\n-- by setup (losers)")
P(L.groupby(["strategy", "type"]).agg(n=("id", "size"), R=("R", "sum")).unstack(fill_value=0).round(2).to_string())
P("\n-- type B clusters (losers, same day, sector/symbol, within 30 min)")
for (d, s, sd), gg in L[L.B].groupby(["date", "sector", "side"]):
    P(d, s, "long" if sd == 1 else "short", len(gg), "trades", gg.symbol.tolist(), sorted(set(gg.strategy)), f"{gg.pnl_adj.sum():+.2f}$", f"{gg.R.sum():+.2f}R")
P("\n-- worst 15 losers")
P(L.sort_values("pnl_adj")[["date", "symbol", "strategy", "side", "nt", "exit_reason", "R", "pnl_adj", "stop_slip", "spread_bps",
                            "spread_frac", "sector", "type"]].head(15).round(3).to_string())
L.drop(columns=["meta"]).to_csv(OUT / "losers.csv", index=False)

# --- step 2: funding-gate math (live paper, after costs)
day = T.groupby("date").agg(n=("id", "size"), R=("R", "sum"), usd=("pnl_adj", "sum"), usd_before=("pnl", "sum"))
P("\n== funding gate: Primary last 10 sessions (live paper, after costs)")
P(day.round(2).to_string())
net_usd, net_R = day.usd.sum(), day.R.sum()
gu = day.usd[day.usd > 0]; gr = day.R[day.R > 0]
P(f"green days: R {int((day.R > 0).sum())}/10, $ {int((day.usd > 0).sum())}/10 | net $ {net_usd:+.2f}, net R {net_R:+.2f}")
P(f"best day $ {day.usd.max():+.2f} ({day.usd.idxmax()}): {day.usd.max() / net_usd:.0%} of net $, {day.usd.max() / gu.sum():.0%} of gross green $"
  if net_usd > 0 else f"best day $ {day.usd.max():+.2f} ({day.usd.idxmax()}): net $ <= 0, so share of net is undefined; {day.usd.max() / gu.sum():.0%} of gross green $")
P(f"best day R {day.R.max():+.2f} ({day.R.idxmax()}): {day.R.max() / gr.sum():.0%} of gross green R" + (f", {day.R.max() / net_R:.0%} of net R" if net_R > 0 else ", net R <= 0"))
P(f"per trade: n {len(T)}, mean R {T.R.mean():+.4f}, sd {T.R.std():.3f}; per day: mean R {day.R.mean():+.3f}, sd {day.R.std():.3f}, "
  f"trades/day {day.n.mean():.1f}")
day.to_csv(OUT / "days.csv")
T.drop(columns=["meta"]).to_csv(OUT / "trades10.csv", index=False)
txt = "\n".join(out) + "\n\nEducational only - not financial advice.\n"
open(OUT / "autopsy_out.txt", "w").write(txt); print(txt)
