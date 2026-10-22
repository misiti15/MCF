"""st7_1022: QQQ's VWAP side at every live (paper) ST7-FD entry (decision-bar close, read-only SIP bars already fetched
by regime1022 into its scratch), i.e. what the H1 filter would have kept. Writes live_h1.csv. Educational only."""
import json
import pandas as pd
from sc import HERE, RG22, W

t = pd.read_csv(W / "live_all.csv")
b = pd.read_parquet(RG22 / "idx_live_1min.parquet")
q = b[b.symbol == "QQQ"].copy()
q["date"] = q["date"].astype(str)
rows = []
for _, r in t.iterrows():
    x = q[q.date == r["date"]]
    typ = (x["high"] + x["low"] + x["close"]) / 3
    vw = (typ * x["volume"]).cumsum() / x["volume"].cumsum()
    st = pd.Timestamp(r["signal_time"]).tz_convert("America/New_York")
    dec = st.floor("5min")                     # decision bar close
    m = x.index < dec
    qv = (x["close"][m].iloc[-1] / vw[m].iloc[-1] - 1) * 100
    rows.append({"date": r["date"], "symbol": r["symbol"], "signal_et": st.strftime("%H:%M"), "r": round(r["r_multiple"], 3),
                 "pnl": r["pnl"], "qqq_vwap_dist_pct": round(qv, 3), "H1_keeps": qv <= 0})
d = pd.DataFrame(rows)
d.to_csv(HERE / "live_h1.csv", index=False)
print(d.to_string())
for k, g in d.groupby("H1_keeps"):
    print("H1 keeps" if k else "H1 skips", len(g), "trades, avg R", round(g.r.mean(), 3), "sum R", round(g.r.sum(), 2), "P/L $", round(g.pnl.sum(), 2))
