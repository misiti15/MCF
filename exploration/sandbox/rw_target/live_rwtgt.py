"""RW-TGT125 live what-if: every closed run-1 RW3-FD / RW5-FD trade (exact parent names, all 10 journals via
`git show origin/<data branch>:journal.db`, read-only; identical signals counted once) from 2026-10-23, replayed on
Alpaca 1-minute SIP bars (GET only) twice: parent bracket (journal stop / target) and target 1.25x from the signal
reference (entry / (1 + side x slip_bps/1e4), as WAVE2 Y1), take-profit rounded toward entry (11-20 rule), stop unchanged.
Bars rescaled to the fill when they differ by > 3% (split adjustment, W5 rule). Inside a bar: stop first; a target needs a 3 bp (min 1c) trade-through; flatten at the 15:55 bar open (12:55 on half
days). Exit costs per arm (LR8 live model): target 0 (limit), stop max(2c, 4 bp), flatten max(1c, 1 bp); entry cost and
fees are the same in both arms and cancel in the paired delta. Writes WORK/live_pairs.parquet.
Usage (cwd repo): python live_rwtgt.py WORK load|bars|replay.  Educational only - not financial advice."""
import sys, sqlite3, subprocess, tempfile, json
from datetime import datetime
import numpy as np, pandas as pd
W = sys.argv[1]; ST = sys.argv[2]
RW = ["RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"]
ORDER = ["primary", "testing", "testing2", "explore1", "livelab", "testingd", "testinge", "testingf", "gen", "graveyard"]
if ST == "load":
    from mcf.config import load_config
    from mcf.costs import cost_r_lr8
    from mcf.research.shadow_calib import BRANCHES
    cfg = load_config(); out = []
    for acct in ORDER:
        raw = subprocess.run(["git", "-C", "/home/user/MCF", "show", f"origin/{BRANCHES[acct]}:journal.db"], capture_output=True).stdout
        if not raw:
            continue
        with tempfile.NamedTemporaryFile(suffix=".db", dir=W) as f:
            f.write(raw); f.flush(); del raw
            c = sqlite3.connect(f.name)
            q = ",".join("?" * len(RW))
            x = pd.read_sql(f"SELECT strategy, symbol, side, date, signal_time, entry_time, exit_time, entry, stop, target, exit, "
                            f"exit_reason, shares, pnl, pnl_adj, r_multiple, mae_r, mfe_r, slip_bps, meta FROM trades WHERE run_id=1 "
                            f"AND exit_time IS NOT NULL AND strategy IN ({q})", c, params=RW)
            c.close()
        x["account"] = acct; out.append(x); print(acct, len(x), flush=True)
    t = pd.concat(out, ignore_index=True)
    t["date"] = t.date.astype(str).str[:10]
    t = t[t.date >= "2026-10-23"].copy()
    assert not t.date.between("2024-11-01", "2025-02-28").any()
    t["r_live"] = cost_r_lr8(t.reset_index(drop=True), cfg).to_numpy(float)
    t["ak"] = t.account.map({a: i for i, a in enumerate(ORDER)})
    t = t.sort_values("ak").drop_duplicates(["strategy", "symbol", "date", "side", "signal_time"]).drop(columns=["meta"])
    t.reset_index(drop=True).to_parquet(f"{W}/live_rw.parquet"); print(len(t), t.groupby(["strategy", "account"]).size())
elif ST == "bars":
    from mcf.data.priors import _bars, _client
    t = pd.read_parquet(f"{W}/live_rw.parquet"); dc = _client(); out = []
    for d, g in t.groupby("date"):
        m = _bars(dc, sorted(set(g.symbol)), datetime.fromisoformat(d + "T13:00:00+00:00"),
                  datetime.fromisoformat(d + "T21:05:00+00:00"), 1, "sip")
        out.append(m.reset_index()); print(d, g.symbol.nunique(), len(m), flush=True)
    pd.concat(out, ignore_index=True).to_parquet(f"{W}/live_1m.parquet")
elif ST == "replay":
    t = pd.read_parquet(f"{W}/live_rw.parquet"); b = pd.read_parquet(f"{W}/live_1m.parquet")
    b["ts"] = pd.to_datetime(b.timestamp, utc=True).dt.tz_convert("America/New_York")
    b["d"] = b.ts.dt.strftime("%Y-%m-%d"); b["mn"] = b.ts.dt.hour * 60 + b.ts.dt.minute
    G = {k: g.sort_values("mn") for k, g in b.groupby(["d", "symbol"])}
    half = {"2026-11-27"}
    def walk(g, start_mn, side, entry, stop, tgt, flat):
        s = g[(g.mn >= start_mn) & (g.mn < flat)]
        for r in s.itertuples():
            if (side > 0 and r.low <= stop) or (side < 0 and r.high >= stop):
                return (min(r.open, stop) if side > 0 else max(r.open, stop)), "stop", r.mn
            thr = max(0.01, 3e-4 * tgt)
            if (side > 0 and r.high >= tgt + thr) or (side < 0 and r.low <= tgt - thr):
                return tgt, "target", r.mn
        a = g[g.mn >= flat]
        if len(a):
            return float(a.open.iloc[0]), "market", flat
        return (float(s.close.iloc[-1]), "market", flat) if len(s) else (np.nan, "none", -1)
    def xcost(px, kind):
        return 0.0 if kind == "target" else (max(0.02, 4e-4 * px) if kind == "stop" else max(0.01, 1e-4 * px))
    rows = []
    for r in t.itertuples():
        g = G.get((r.date, r.symbol))
        et = pd.Timestamp(r.entry_time)
        et = (et.tz_localize("UTC") if et.tzinfo is None else et).tz_convert("America/New_York")
        st_mn = et.hour * 60 + et.minute + 1          # entry bar's remaining range: from the next full minute
        flat = 12 * 60 + 55 if r.date in half else 15 * 60 + 55
        side = int(r.side); risk = abs(r.entry - r.stop)
        slip = r.slip_bps if r.slip_bps == r.slip_bps and r.slip_bps is not None else 0.0
        ref = r.entry / (1 + side * slip / 1e4)
        if g is None or not risk > 0 or not (r.target == r.target):
            rows.append(dict(i=r.Index, ok=False)); continue
        tv = ref + side * 1.25 * abs(r.target - ref)
        tv = np.ceil(round(tv * 100, 6)) / 100 if side < 0 else np.floor(round(tv * 100, 6)) / 100
        o = dict(i=r.Index, ok=True, tgt_v=tv, rescaled=False)
        ref_bar = g[g.mn <= st_mn - 1]
        if len(ref_bar):
            k = r.entry / float(ref_bar.close.iloc[-1])
            if abs(k - 1) > 0.03:     # split-adjusted bars vs unadjusted fill (W5 rule): rescale the day's bars
                g = g.assign(open=g.open * k, high=g.high * k, low=g.low * k, close=g.close * k); o["rescaled"] = True
        for arm, tg in (("p", r.target), ("v", tv)):
            px, kd, mn = walk(g, st_mn, side, r.entry, r.stop, tg, flat)
            o[f"px_{arm}"], o[f"kind_{arm}"], o[f"xmn_{arm}"] = px, kd, mn
            o[f"rg_{arm}"] = (side * (px - r.entry) - xcost(px, kd)) / risk
        rows.append(o)
    a = pd.DataFrame(rows).set_index("i"); t = t.join(a)
    t.to_parquet(f"{W}/live_pairs.parquet"); print(t.ok.sum(), "replayed of", len(t))
