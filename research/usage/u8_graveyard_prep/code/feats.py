"""Entry features for Graveyard-resident live trades; streams one 1-min pack per day and deletes it."""
import os, sys, subprocess, json, numpy as np, pandas as pd
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/up_u8"
URL = "https://github.com/misiti15/MCF/releases/download/{tag}/1min-{d}.parquet"
t = pd.read_pickle(S + "/gy_trades.pkl")
daily = pd.read_parquet(S + "/packs/1day-2026-11-17.parquet")
daily["d"] = daily.ts.dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
daily["symbol"] = daily.symbol.astype(str)
out = []
for d, g in t.groupby("date"):
    assert not ("2024-11-01" <= d <= "2025-02-28")
    p = f"{S}/packs/1min-{d}.parquet"
    if not os.path.exists(p):
        subprocess.run(["curl", "-sSfL", "-o", p, URL.format(tag="bars-" + d[:7], d=d)], check=True)
    syms = set(g.symbol) | {"SPY"}
    m = pd.read_parquet(p, filters=[("symbol", "in", list(syms))])
    m["symbol"] = m.symbol.astype(str)
    m = m.sort_values(["symbol", "ts"])
    m["pv"] = (m.high + m.low + m.close) / 3 * m.volume
    m["cpv"] = m.groupby("symbol").pv.cumsum(); m["cv"] = m.groupby("symbol").volume.cumsum()
    m["vwap"] = m.cpv / m.cv.replace(0, np.nan)
    m["end"] = m.ts + pd.Timedelta(minutes=1)
    prev = daily[daily.d < d].sort_values("ts").groupby("symbol").tail(1).set_index("symbol").close
    op = m.groupby("symbol").open.first()
    spy = m[m.symbol == "SPY"].set_index("end")
    spy_gap = op.get("SPY") / prev.get("SPY") - 1
    for i, r in g.iterrows():
        et = pd.Timestamp(r.entry_time).tz_convert("UTC")
        b = m[(m.symbol == r.symbol) & (m.end <= et)]
        sb = spy[spy.index <= et]
        f = dict(idx=i, spy_gap=spy_gap,
                 spy_ret=(sb.close.iloc[-1] / op.get("SPY") - 1) if len(sb) else 0.0,
                 gap=(op.get(r.symbol, np.nan) / prev.get(r.symbol, np.nan) - 1) if r.symbol in prev.index else np.nan,
                 ret_open=(b.close.iloc[-1] / b.open.iloc[0] - 1) if len(b) else np.nan,
                 above_vwap=(b.close.iloc[-1] > b.vwap.iloc[-1]) if len(b) else np.nan)
        out.append(f)
    os.remove(p)
    print(d, len(g), flush=True)
F = pd.DataFrame(out).set_index("idx")
F.to_pickle(S + "/feats.pkl")
