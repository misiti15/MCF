"""BDI 1125 step 1 (copy of research/bdi/1124/patterns.py, unchanged): per-trade loss types for Primary + contenders (On Deck, Testing A-F), appended to research/bdi/patterns.csv.
Loss classifier = research/bdi/1106/trades_bdi.py order (stopped_then_reversed / wrong_side_after_big_swing /
gave_back_gains / late_hold / never_worked / small MFE then failed), plus one new label checked first among stops:
near_target_then_stopped (journal mfe_r >= 80% of the target distance, then a full stop; nightly 11-19 idea / swing1119-L16).
Tags in notes: lot number per (account, setup, symbol), leveraged / inverse ETF and its underlying + exposure sign.
R = pnl_adj / $risk (after costs). Usage: python patterns.py <scratch> <day>. Educational only - not financial advice."""
import sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
S, D = Path(sys.argv[1]), sys.argv[2]; TZ = "America/New_York"; MD = D[5:7] + D[8:10]
HERE = Path(__file__).resolve().parent; OUT = HERE.parent / "patterns.csv"
ACC = {"p": "primary", "od": "ondeck", "ta": "testing_a", "tb": "testing_b", "tc": "testing_c", "td": "testing_d", "te": "testing_e", "tf": "testing_f"}
# leveraged / inverse ETPs: symbol -> (underlying, market exposure sign of a LONG position)
LEV = {"SQQQ": ("QQQ", -1), "SPXS": ("SPY", -1), "SPXU": ("SPY", -1), "SDS": ("SPY", -1), "SH": ("SPY", -1), "PSQ": ("QQQ", -1),
       "QID": ("QQQ", -1), "SOXS": ("SOXX", -1), "TZA": ("IWM", -1), "SRTY": ("IWM", -1), "TECS": ("XLK", -1), "FAZ": ("XLF", -1),
       "UVXY": ("VIX", -1), "UVIX": ("VIX", -1), "VXX": ("VIX", -1), "VIXY": ("VIX", -1), "SDOW": ("DIA", -1), "LABD": ("XBI", -1),
       "TSLQ": ("TSLA", -1), "NVDQ": ("NVDA", -1), "TSDD": ("TSLA", -1), "DUST": ("GDX", -1), "YANG": ("FXI", -1),
       "TQQQ": ("QQQ", 1), "SPXL": ("SPY", 1), "UPRO": ("SPY", 1), "SSO": ("SPY", 1), "QLD": ("QQQ", 1), "SOXL": ("SOXX", 1),
       "TNA": ("IWM", 1), "TECL": ("XLK", 1), "FAS": ("XLF", 1), "LABU": ("XBI", 1), "NVDL": ("NVDA", 1), "TSLL": ("TSLA", 1),
       "MUU": ("MU", 1), "NUGT": ("GDX", 1), "YINN": ("FXI", 1), "UDOW": ("DIA", 1), "SVIX": ("VIX", 1), "SVXY": ("VIX", 1),
       "CONL": ("COIN", 1), "MSTU": ("MSTR", 1), "ETHU": ("ETH", 1), "BITX": ("BTC", 1)}
B = pd.read_parquet(S / "cov/days" / D / "bars.parquet", columns=["symbol", "high", "low", "close"])
BG = {s: g for s, g in B.groupby("symbol")}
spy = BG["SPY"].close; spy_fo = (spy / spy.iloc[0] - 1) * 100
rows, X = [], []
for a, nm in ACC.items():
    t = pd.read_sql("select symbol, strategy, side, entry_time, exit_time, entry, stop, target, exit_reason, shares, pnl_adj, mfe_r "
                    "from trades where date=? and run_id=1", sqlite3.connect(S / a / "journal.db"), params=(D,))
    if t.empty: continue
    t["nt"] = pd.to_datetime(t.entry_time, utc=True, format="mixed").dt.tz_convert(TZ)
    t["et"] = pd.to_datetime(t.exit_time, utc=True, format="mixed").dt.tz_convert(TZ)
    t["R"] = t.pnl_adj / ((t.entry - t.stop).abs() * t.shares)
    t = t.sort_values("nt"); t["lot"] = t.groupby(["strategy", "symbol"]).cumcount() + 1
    for r in t.itertuples():
        b = BG.get(r.symbol); s = int(r.side); fo = np.nan
        if b is not None:
            pre = b[b.index < r.nt.floor("min")]; fo = (pre.close.iloc[-1] / b.close.iloc[0] - 1) * 100 if len(pre) else 0.0
        sf = float(spy_fo[spy_fo.index < r.nt.floor("min")].iloc[-1]) if (spy_fo.index < r.nt.floor("min")).any() else 0.0
        mfe = r.mfe_r if r.mfe_r == r.mfe_r else 0.0
        tgt_frac = abs(r.target - r.entry) / abs(r.entry - r.stop) if r.target == r.target and r.target else np.nan
        lt = "win"
        if r.pnl_adj < 0:
            post = b[b.index > r.et.floor("min")] if b is not None else pd.DataFrame()
            if r.exit_reason == "stop" and tgt_frac == tgt_frac and mfe >= 0.8 * tgt_frac:
                lt = "near_target_then_stopped"
            elif r.exit_reason == "stop" and r.target == r.target and len(post) and ((post.high.max() >= r.target) if s == 1 else (post.low.min() <= r.target)):
                lt = "stopped_then_reversed"
            elif fo == fo and abs(fo) >= 3 and np.sign(fo) == -s:
                lt = "wrong_side_after_big_swing"
            elif mfe >= 0.5: lt = "gave_back_gains"
            elif r.exit_reason in ("flatten", "eod"): lt = "late_hold"
            elif mfe < 0.15: lt = "never_worked"
            else: lt = "small MFE then failed (0.15-0.5R)"
        lev = LEV.get(r.symbol)
        exp = (lev[1] * s) if lev else s
        X.append(dict(account=nm, symbol=r.symbol, setup=r.strategy, side=s, R=r.R, ltype=lt, lot=r.lot, lev=lev[0] if lev else "",
                      exposure=exp, entry=f"{r.nt:%H:%M}", spy_fo=sf, mfe=mfe))
        if lt != "win":
            rows.append(dict(date=D, account=nm, symbol=r.symbol, setup=r.strategy, side="long" if s == 1 else "short", loss_type=lt,
                             notes=f"bdi{MD}; r {r.R:.2f}; mfe {mfe:.2f}; lot {r.lot}; spyfo {sf:+.2f}; entry {r.nt:%H:%M}"
                                   + (f"; levETF {lev[0]} market-exposure {'long' if exp > 0 else 'short'}" if lev else "")))
X = pd.DataFrame(X); P = pd.DataFrame(rows)
old = pd.read_csv(OUT); old = old[old.date != D]; pd.concat([old, P]).to_csv(OUT, index=False)
print(f"{D}: {len(X)} trades, {len(P)} losers appended to patterns.csv")
print(X[X.ltype != "win"].pivot_table(index="ltype", columns="account", values="R", aggfunc="sum", fill_value=0).round(1).to_string())
print("\nloss type totals:", X[X.ltype != "win"].groupby("ltype").R.agg(["size", "sum"]).round(2).to_dict("index"))
st = X.assign(stack=np.where(X.lot >= 2, "lot2+", "lot1")).groupby(["stack"]).R.agg(["size", "sum", "mean"]).round(3)
print("\nsame-symbol stacking (lot = nth entry of the same setup on the symbol today):\n", st.to_string())
lv = X[X.lev != ""]
print("\nleveraged/inverse ETPs by underlying (exposure = market sign of the position):")
print(lv.groupby(["lev", "exposure", "account"]).R.agg(["size", "sum"]).round(2).to_string() if len(lv) else "none")
print("\nall trades by market exposure sign:", X.groupby("exposure").R.agg(["size", "sum", "mean"]).round(3).to_dict("index"))
