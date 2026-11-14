"""OBS-UPDAY-NULL (Observer 2026-11-13 night): the benchmark every up-day rule must beat. From 2 years of SPY / QQQ RTH
minute bars (Alpaca SIP, split-adjusted; fetched outside 07:30-16:00 ET): P(close > prior close) and P(close > open)
given where the index stands at time t (move from prior close, in buckets), and the gap alone at the open. A rule that
says 'up day' at time t is only adding information if it beats this table at the same t. 0 configs (descriptive).
Educational only - not financial advice. usage (MCF checkout): python ../guild/research/obs-upday-null/upnull.py"""
import os, time, requests, pandas as pd, numpy as np
from pathlib import Path
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
OUT = Path(__file__).with_name("cache"); OUT.mkdir(exist_ok=True)
def bars(sym, start="2024-11-01", end="2026-11-14"):
    f = OUT / f"{sym}_1m.parquet"
    if f.exists(): return pd.read_parquet(f)
    p = {"timeframe": "1Min", "start": start, "end": end, "feed": "sip", "adjustment": "split", "limit": 10000}; rows = []
    while True:
        r = requests.get(f"https://data.alpaca.markets/v2/stocks/{sym}/bars", headers=H, params=p, timeout=60)
        if r.status_code == 429: time.sleep(3); continue
        r.raise_for_status(); j = r.json(); rows += j.get("bars") or []
        if not j.get("next_page_token"): break
        p["page_token"] = j["next_page_token"]; time.sleep(0.3)
    d = pd.DataFrame(rows); d["t"] = pd.to_datetime(d.t).dt.tz_convert("America/New_York"); d.to_parquet(f); return d
T = ["09:31", "10:00", "10:30", "11:00", "12:00", "13:00", "14:00", "15:00", "15:30"]
for sym in ["SPY", "QQQ"]:
    d = bars(sym); d = d[(d.t.dt.time >= pd.Timestamp("09:30").time()) & (d.t.dt.time < pd.Timestamp("16:00").time())].copy()
    d["day"] = d.t.dt.date; d["hm"] = d.t.dt.strftime("%H:%M")
    g = d.groupby("day"); day = pd.DataFrame({"o": g.o.first(), "c": g.c.last(), "n": g.size()}); day = day[day.n >= 300]
    day["pc"] = day.c.shift(1); day = day.dropna()
    day["up"] = day.c > day.pc; day["up_oc"] = day.c > day.o
    print(f"\n{sym}: {len(day)} sessions {day.index.min()}..{day.index.max()}; up days (close > prior close) {day.up.mean():.1%}; close > open {day.up_oc.mean():.1%}")
    px = d.pivot_table(index="day", columns="hm", values="c", aggfunc="last")
    edges = [-9, -1.0, -0.5, -0.25, -0.1, 0, 0.1, 0.25, 0.5, 1.0, 9]
    for t in T:
        if t not in px: continue
        m = ((px[t].reindex(day.index) / day.pc - 1) * 100); b = pd.cut(m, edges)
        tab = day.groupby(b, observed=True).agg(n=("up", "size"), p_up=("up", "mean"))
        # skill of the naive 'sign so far' call: accuracy of predicting up = (move so far > 0)
        acc = ((m > 0) == day.up).mean()
        print(f"  t={t}: sign-so-far accuracy {acc:.1%} | " + "  ".join(f"{str(k)}:{int(r.n)}/{r.p_up:.0%}" for k, r in tab.iterrows()))
print("\nReading: at each t, P(up close) given the move from prior close. An up-day signal must beat this at the same t "
      "(and its own costs) to add information. Educational only - not financial advice.")
print("\nTRADABLE PART: SPY / QQQ return from t to the close (bps), by the move-so-far bucket; mean, day-t, n.")
for sym in ["SPY", "QQQ"]:
    d = bars(sym); d = d[(d.t.dt.time >= pd.Timestamp("09:30").time()) & (d.t.dt.time < pd.Timestamp("16:00").time())].copy()
    d["day"] = d.t.dt.date; d["hm"] = d.t.dt.strftime("%H:%M"); g = d.groupby("day")
    day = pd.DataFrame({"c": g.c.last(), "n": g.size()}); day = day[day.n >= 300]; day["pc"] = day.c.shift(1); day = day.dropna()
    px = d.pivot_table(index="day", columns="hm", values="c", aggfunc="last")
    for t in ["10:00", "10:30", "11:00", "12:00", "13:00"]:
        m = (px[t].reindex(day.index) / day.pc - 1) * 100; rest = (day.c / px[t].reindex(day.index) - 1) * 1e4
        out = []
        for lab, sel in [("<= -0.5%", m <= -0.5), ("-0.5..0", (m > -0.5) & (m <= 0)), ("0..+0.5", (m > 0) & (m <= 0.5)), ("> +0.5%", m > 0.5)]:
            x = rest[sel].dropna(); out.append(f"{lab}: {x.mean():+.1f}bps t {x.mean()/(x.std(ddof=1)/np.sqrt(len(x))):+.2f} n {len(x)}")
        allr = rest.dropna(); print(f"  {sym} t={t}: all {allr.mean():+.1f}bps | " + " | ".join(out))
