"""[1127 half-day copy of research/bdi/1125/l19_live.py: exit at the 12:55 open (the half-day flatten) instead of 15:55,
stopped names entered only before 12:55; rule otherwise unchanged.]
swing1125-L19 live shadow (rule fixed in research/bdi/swings/hypotheses.jsonl): the gap-down short family's stop
cluster as a long trigger, on the live journals of all 10 accounts (run 1). Family stop = a family short lot whose exit
price is at / beyond its stop (exit >= stop - 1c). Trigger T = first minute 10:30-14:30 ET with >= 10 distinct symbols
stopped in the last 10 minutes (any account). Shadow long = each symbol first stopped in [T, 14:30]: buy at that
minute's 1-min close, 1R = that short's |entry - stop| per share, stop at entry - 1R (1-min lows from the next minute),
else the 15:55 open; LR8 costs (entry 1c + 1 bp x tod multiplier, exit 1c + 1 bp, +2c on stops). Read-only.
Usage: python l19_live.py <scratch> <day> [--in-sample]; <scratch>/<acct>/journal.db (p od ta tb tc td te tf gen gy),
<scratch>/bars/<SYM>.parquet (1-min SIP). Appends to research/bdi/swings/forward.csv (hyp L19).
Educational only - not financial advice."""
import sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research.gates import tod_cost_mult

S, D = Path(sys.argv[1]), sys.argv[2]; INS = "--in-sample" in sys.argv; TZ = "America/New_York"
HERE = Path(__file__).resolve().parent
FAM = ("L3-gap-slope-", "RW3-gapdn-rsi5pop-flowsell-short", "RW5-heat30-flowsell-rsi5pop-gapdn-short", "RW1-gapdn-bounce-flowsell-short",
       "RW7-gapdn-bounce-early-short", "RW3S-gapdn-flowsell-short")
T = []
for a in ("p", "od", "ta", "tb", "tc", "td", "te", "tf", "gen", "gy"):
    t = pd.read_sql("select symbol, strategy, side, exit_time, entry, stop, exit, shares, pnl_adj from trades where date=? and run_id=1 and side=-1",
                    sqlite3.connect(S / a / "journal.db"), params=(D,)); t["acct"] = a; T.append(t)
T = pd.concat(T)
T = T[T.strategy.str.startswith(FAM)].copy()
T["xt"] = pd.to_datetime(T.exit_time, utc=True, format="mixed").dt.tz_convert(TZ)
T["xm"] = T.xt.dt.hour * 60 + T.xt.dt.minute
T["stopped"] = T.exit >= T.stop - 0.01
T["rps"] = (T.entry - T.stop).abs()
st = T[T.stopped].sort_values("xm").groupby("symbol").first().reset_index()
print(f"family short lots {len(T)}, stopped lots {T.stopped.sum()}, stopped symbols {len(st)}")
trig = None
for m in range(630, 871):
    if st[(st.xm > m - 10) & (st.xm <= m)].symbol.nunique() >= 10:
        trig = m; break
rows = []
if trig is None:
    print("no trigger")
else:
    print(f"trigger T {trig // 60:02d}:{trig % 60:02d} ET")
    for r in st[(st.xm >= trig) & (st.xm <= 870) & (st.xm < 775)].itertuples():
        f = S / "bars" / f"{r.symbol}.parquet"
        if not f.exists():
            continue
        b = pd.read_parquet(f); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
        hm = b.index.hour * 60 + b.index.minute
        i0 = np.flatnonzero(hm == r.xm)
        if not len(i0):
            continue
        e = float(b.close.iloc[i0[0]]); s = e - r.rps; px, kind = None, 0
        for k in range(i0[0] + 1, len(b)):
            if hm[k] >= 775:
                px = float(b.open.iloc[k]); break
            if b.low.iloc[k] <= s:
                px, kind = float(min(b.open.iloc[k], s)), 1; break
        if px is None:
            px = float(b.close.iloc[-1])
        ec = (0.01 + e * 1e-4) * float(tod_cost_mult(np.array([(r.xm // 60) * 100 + r.xm % 60]))[0])
        xc = 0.01 + px * 1e-4 + (0.02 if kind else 0.0)
        rows.append(dict(symbol=r.symbol, m=r.xm, entry=e, px=px, kind=kind, r=(px - e - ec - xc) / r.rps, r_gross=(px - e) / r.rps))
L = pd.DataFrame(rows)
note = "no trigger" if trig is None else (f"T {trig // 60:02d}:{trig % 60:02d}; n {len(L)} avg {L.r.mean():+.3f}R after costs "
                                         f"(gross {L.r_gross.mean():+.3f}), total {L.r.sum():+.1f}R, stops {L.kind.mean():.0%}, win {(L.r > 0).mean():.0%}")
print(note)
if len(L):
    L["hh"] = L.m // 60
    print(L.groupby("hh").r.agg(["count", "mean", "sum"]).round(3).to_string())
fp = HERE.parent / "swings" / "forward.csv"
F = pd.read_csv(fp)
F = F[~((F.date == D) & (F.hyp == "L19"))]
F = pd.concat([F, pd.DataFrame([dict(date=D, hyp="L19", n=len(L), avgR=round(L.r.mean(), 3) if len(L) else np.nan, note=note, in_sample=INS)])])
F.to_csv(fp, index=False)
print("Educational only - not financial advice.")
