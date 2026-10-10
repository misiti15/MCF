"""Spread calibration from the SIP NBBO sample (data/nbbo_sample.parquet) and fills vs NBBO (data/fill_quotes.parquet).

Compares the quoted half-spread (the cost of crossing for a marketable order) with the production cost model
(mcf/research/gates.py: 1c + 1 bps per side; config/default.yaml costs) by time of day, and computes the open-window
spread multiplier: per symbol-day, median spread in 09:30-09:50 / median spread in 10:30-15:30. Prints markdown.
Educational only - not financial advice.
"""
import os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SLIP_PS, SLIP_BPS = 0.01, 1e-4
q = pd.read_parquet(os.path.join(HERE, "data", "nbbo_sample.parquet"))
q["t"] = pd.to_datetime(q["t"]).dt.tz_convert("America/New_York")
q["date"] = q.t.dt.date; q["hm"] = q.t.dt.hour * 100 + q.t.dt.minute
q["mid"] = (q.bid + q.ask) / 2; q["spr"] = q.ask - q.bid; q["spr_bps"] = q.spr / q.mid * 1e4
q["model_ps"] = SLIP_PS + SLIP_BPS * q.mid          # model per-side cost, $
q["half_over_model"] = (q.spr / 2) / q.model_ps
B = [(930, 931, "09:30"), (931, 935, "09:31-09:34"), (935, 940, "09:35-09:39"), (940, 950, "09:40-09:49"),
     (950, 1000, "09:50-09:59"), (1000, 1030, "10:00-10:29"), (1030, 1200, "10:30-11:59"), (1200, 1400, "12:00-13:59"),
     (1400, 1530, "14:00-15:29"), (1530, 1600, "15:30-15:55")]
q["bucket"] = None
for a, b, n in B: q.loc[(q.hm >= a) & (q.hm < b), "bucket"] = n
q["pxb"] = pd.cut(q.mid, [0, 20, 50, 150, 400, 1e9], labels=["<$20", "$20-50", "$50-150", "$150-400", ">$400"])

print("Educational only - not financial advice.\n")
print(f"Sample: {q.symbol.nunique()} symbols x {q.date.nunique()} sessions ({min(q.date)}..{max(q.date)}), "
      f"{len(q):,} symbol-time NBBO snapshots (last valid quote in the 3 s before each sample time).\n")
print("## 1. Quoted spread by time of day (all symbols pooled)\n")
print("| bucket | n | median spread bps | mean spread bps | median half-spread / model per-side | share half-spread > model | p90 half/model |")
print("|---|---|---|---|---|---|---|")
for _, _, n in B:
    g = q[q.bucket == n]
    print(f"| {n} | {len(g)} | {g.spr_bps.median():.1f} | {g.spr_bps.mean():.1f} | {g.half_over_model.median():.2f} | "
          f"{(g.half_over_model > 1).mean():.0%} | {g.half_over_model.quantile(.9):.2f} |")

base = q[(q.hm >= 1030) & (q.hm < 1530)].groupby(["symbol", "date"]).spr.median().rename("base")
def mult(lo, hi):
    w = q[(q.hm >= lo) & (q.hm < hi)].groupby(["symbol", "date"]).spr.median().rename("w")
    m = pd.concat([w, base], axis=1).dropna(); m = m[m.base > 0]
    return (m.w / m.base)
print("\n## 2. Open-window spread multiplier (per symbol-day median spread in window / median 10:30-15:30)\n")
print("| window | symbol-days | median multiplier | mean | p75 | p90 |")
print("|---|---|---|---|---|---|")
for lo, hi, n in [(930, 935, "09:30-09:34"), (935, 950, "09:35-09:49"), (930, 950, "09:30-09:49 (open window)"),
                  (950, 1030, "09:50-10:29"), (1530, 1600, "15:30-15:55")]:
    r = mult(lo, hi)
    print(f"| {n} | {len(r)} | {r.median():.2f} | {r.mean():.2f} | {r.quantile(.75):.2f} | {r.quantile(.9):.2f} |")

print("\n## 3. By price band: median half-spread / model per-side cost\n")
print("| price band | symbols | 09:30-09:49 | 09:50-10:29 | 10:30-15:29 | open-window multiplier (median) |")
print("|---|---|---|---|---|---|")
ow = mult(930, 950).rename("m").reset_index()
pb = q.groupby("symbol").mid.median()
ow["pxb"] = pd.cut(ow.symbol.map(pb), [0, 20, 50, 150, 400, 1e9], labels=["<$20", "$20-50", "$50-150", "$150-400", ">$400"])
for b in ["<$20", "$20-50", "$50-150", "$150-400", ">$400"]:
    g = q[q.pxb == b]
    f = lambda lo, hi: g[(g.hm >= lo) & (g.hm < hi)].half_over_model.median()
    print(f"| {b} | {g.symbol.nunique()} | {f(930,950):.2f} | {f(950,1030):.2f} | {f(1030,1530):.2f} | {ow[ow.pxb==b].m.median():.2f} |")

# implied cents: what flat per-side c would match the median half-spread in each window, on top of the 1 bps
print("\n## 4. Per-side cost implied by the quoted half-spread (mean over snapshots, $/share and bps)\n")
print("| window | mean half-spread $ | median half-spread $ | mean half-spread bps | model mean per-side $ |")
print("|---|---|---|---|---|")
for lo, hi, n in [(930, 950, "09:30-09:49"), (950, 1030, "09:50-10:29"), (1030, 1530, "10:30-15:29"), (1530, 1600, "15:30-15:55")]:
    g = q[(q.hm >= lo) & (q.hm < hi)]
    print(f"| {n} | {(g.spr/2).mean():.4f} | {(g.spr/2).median():.4f} | {(g.spr_bps/2).mean():.2f} | {g.model_ps.mean():.4f} |")

wide = q[(q.hm >= 1030) & (q.hm < 1530)].groupby("symbol").half_over_model.median().sort_values(ascending=False)
print("\nWidest names vs model mid-day (median half-spread / model):", ", ".join(f"{s} {v:.1f}" for s, v in wide.head(10).items()))

# ---- fills (paper account) vs NBBO
p = os.path.join(HERE, "data", "fill_quotes.parquet")
if os.path.exists(p):
    o = pd.read_parquet(os.path.join(HERE, "data", "orders.parquet")).merge(pd.read_parquet(p), on="id")
    o["px"] = o.filled_avg_price.astype(float); o["sgn"] = np.where(o.side == "buy", 1, -1)
    o["tod"] = pd.to_datetime(o.filled_at, format="ISO8601").dt.tz_convert("America/New_York")
    o["hm"] = o.tod.dt.hour * 100 + o.tod.dt.minute
    for k in ("sub", "fill"):
        mid = (o[f"bid_{k}"] + o[f"ask_{k}"]) / 2; half = (o[f"ask_{k}"] - o[f"bid_{k}"]) / 2
        o[f"slip_{k}"] = o.sgn * (o.px - mid)            # $ paid vs mid (positive = cost)
        o[f"half_{k}"] = half
    o["model_ps"] = SLIP_PS + SLIP_BPS * o.px
    print("\n## 5. Paper fills vs SIP NBBO (Alpaca paper account, 2026-10-06..09)\n")
    print("Paper fills are simulated by Alpaca against the NBBO, so this checks the simulator, not real market impact.\n")
    print("| order type | n | median $ vs mid at submit | mean $ vs mid at submit | mean half-spread at submit | mean model per-side | mean $ vs mid at fill |")
    print("|---|---|---|---|---|---|---|")
    for t in ["market", "stop", "limit"]:
        g = o[o.type == t]
        print(f"| {t} | {len(g)} | {g.slip_sub.median():.4f} | {g.slip_sub.mean():.4f} | {g.half_sub.mean():.4f} | {g.model_ps.mean():.4f} | {g.slip_fill.mean():.4f} |")
    st = o[(o.type == "stop") & o.stop_price.notna()]
    if len(st):
        s = st.sgn * (st.px - st.stop_price.astype(float))
        print(f"\nStop fills vs stop price: n {len(st)}, median {s.median():.4f} $/sh, mean {s.mean():.4f}, p90 {s.quantile(.9):.4f} "
              f"(model: 1c + 1 bps + 2c stop extra = mean {(st.model_ps + 0.02).mean():.4f}).")
    mk = o[o.type == "market"]
    for lo, hi, n in [(930, 950, "09:30-09:49"), (950, 1600, "09:50-16:00")]:
        g = mk[(mk.hm >= lo) & (mk.hm < hi)]
        if len(g): print(f"Market fills {n}: n {len(g)}, mean $ vs mid at submit {g.slip_sub.mean():.4f}, mean half-spread {g.half_sub.mean():.4f}, model {g.model_ps.mean():.4f}")

# ---- in R units (what the gates see): R = 0.25 x daily ATR (data/universe.csv atr, 20-day, built 2026-10-05)
u = pd.read_csv(os.path.join(HERE, "..", "..", "..", "data", "universe.csv"), usecols=["symbol", "atr"]).set_index("symbol").atr
q["R"] = 0.25 * q.symbol.map(u)
g0 = q[q.R > 0]
print("\n## 6. In R units (R = 0.25 x 20-day daily ATR): round-trip cost of crossing the quoted spread twice vs model\n")
print("Round trip = entry + exit, both marketable (the model's worst case: a non-target exit; stop extra not included).\n")
print("| window | symbol-snapshots | median spread / R (= 2 half-spreads) | mean spread / R | median model 2-side / R | mean model 2-side / R |")
print("|---|---|---|---|---|---|")
for lo, hi, n in [(930, 935, "09:30-09:34"), (935, 950, "09:35-09:49"), (950, 1030, "09:50-10:29"), (1030, 1530, "10:30-15:29"), (1530, 1600, "15:30-15:55")]:
    g = g0[(g0.hm >= lo) & (g0.hm < hi)]
    a = g.spr / g.R; m = 2 * g.model_ps / g.R
    print(f"| {n} | {len(g)} | {a.median():.3f} | {a.mean():.3f} | {m.median():.3f} | {m.mean():.3f} |")
