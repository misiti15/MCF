"""Live replay (paper record, current-8 Primary trades 10-08..10-29) of the p1_1029 backlog idea 'wider stop at the same
$ risk' for the short family (RW3-FD / RW5-FD / MF2-FD / MF4 / MF4-FD): stop at k x the live stop distance, shares / k,
target price unchanged, walk SIP 1-min bars from the entry minute, stop first inside a bar, flatten at the 15:55 close.
Costs: 1c + 1bp per side, +2c on a stop, no exit cost on a target. k = 1 is the calibration row (replay vs live).
Longs are left as traded. Usage: python live_wide.py <scratch-pr29> [--fetch]   Educational only - not financial advice."""
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
S = Path(sys.argv[1]); TZ = "America/New_York"; B = S / "livebars"; B.mkdir(exist_ok=True)
t = pd.read_csv(S / "live_ctx.csv"); t["nt"] = pd.to_datetime(t.nt); t["xt"] = pd.to_datetime(t.xt)
tt = pd.read_csv(S / "live_all.csv")[["id", "target"]] if "target" in pd.read_csv(S / "live_all.csv", nrows=1) else None
if "--fetch" in sys.argv:
    from mcf.data.alpaca_data import _client, fetch_bars
    cl = _client()
    for d, g in t.groupby("date"):
        syms = sorted(s for s in g.symbol.unique() if not (B / f"{d}_{s}.parquet").exists())
        if not syms:
            continue
        a = datetime.fromisoformat(d).replace(hour=13, tzinfo=timezone.utc); b = a + timedelta(hours=7, minutes=30)
        for s, x in fetch_bars(syms, a, b, feed="sip", client=cl).items():
            x.to_parquet(B / f"{d}_{s}.parquet")
        print(d, len(syms), flush=True)
import sqlite3
c = sqlite3.connect(S / "p" / "journal.db")
tg = pd.read_sql("select id, target from trades where run_id=1", c)
t = t.merge(tg, on="id", how="left")
out = []
for r in t.itertuples():
    f = B / f"{r.date}_{r.symbol}.parquet"
    if not f.exists():
        out.append(dict(id=r.id, ok=False)); continue
    b = pd.read_parquet(f); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
    end = r.nt.normalize() + pd.Timedelta(hours=15, minutes=55)
    w = b[(b.index >= r.nt.floor("1min")) & (b.index <= end)]
    rps = abs(r.entry - r.stop); s = r.side; row = dict(id=r.id, ok=len(w) > 0)
    for k in (1.0, 1.5, 2.0, 2.5):
        st = r.entry - s * k * rps; px, kind = (w.close.iloc[-1] if len(w) else r.entry), 0
        for _, x in w.iterrows():
            if (s == -1 and x.high >= st) or (s == 1 and x.low <= st):
                px, kind = st, 1; break
            if (s == -1 and x.low <= r.target) or (s == 1 and x.high >= r.target):
                px, kind = r.target, 2; break
        cost = 0.01 + r.entry * 1e-4 + (0 if kind == 2 else 0.01 + px * 1e-4) + (0.02 if kind == 1 else 0)
        row[f"R{k}"] = (s * (px - r.entry) - cost) / (k * rps)
    out.append(row)
o = t.merge(pd.DataFrame(out), on="id")
o = o[o.ok]
print(f"trades with bars {len(o)} of {len(t)}; calibration k=1 replay vs live R: corr {np.corrcoef(o['R1.0'], o.R)[0,1]:.3f}, "
      f"mean replay {o['R1.0'].mean():+.3f} vs live {o.R.mean():+.3f}")
rows = []
for k in (1.0, 1.5, 2.0, 2.5):
    rr = np.where(o.fam == "S", o[f"R{k}"], o.R) if k != 1.0 else o.R.to_numpy()     # k=1 row = live as traded
    if k != 1.0:   # use the replay for the family's change relative to its own k=1 replay (removes replay bias)
        rr = np.where(o.fam == "S", o.R + (o[f"R{k}"] - o["R1.0"]), o.R)
    x = o.assign(rr=rr, usd=rr * o.risk)
    day = x.groupby("date").agg(R=("rr", "sum"), usd=("usd", "sum")); c2 = day.R.cumsum()
    rows.append(dict(k=k, trades=len(x), avgR=x.rr.mean(), totR=x.rr.sum(), usd=x.usd.sum(), worst=day.R.min(), today=day.R.get("2026-10-29"),
                     today_usd=day.usd.get("2026-10-29"), d1022=day.R.get("2026-10-22"), red=int((day.R < 0).sum()), maxdd=float((c2.cummax() - c2).max()),
                     ex_best=x.rr.sum() - day.R.max()))
print(pd.DataFrame(rows).round(3).to_string(index=False))
