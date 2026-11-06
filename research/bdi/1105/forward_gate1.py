"""Forward tally 2026-11-05 for gate1-checkpoint-gate (hypotheses.jsonl): GATE1 state every 30 min from 11:00 ET
(UP: SPY >= +0.15% from open AND above session VWAP AND breadth_open >= 0.50 AND (QQQ or IWM up); DOWN mirrored; else MIXED;
breadth_open = share of the day's universe (cov bars, ADV >= $60M) above its 09:30 open, using bars closed by the checkpoint).
Entries of setups in research/bdi/gate1/shadow_rule_setup_states.csv after 11:00 are dropped when the latest state is not
allowed. Journals run 1, all 7 accounts. Usage: python forward_gate1.py <scratch>. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent; TZ = "America/New_York"
B = pd.read_parquet(S / "cov/days/2026-11-05/bars.parquet"); B.index = pd.to_datetime(B.index, utc=True).tz_convert(TZ)
cl = B.pivot_table(index=B.index, columns="symbol", values="close"); op = B.pivot_table(index=B.index, columns="symbol", values="open").iloc[0]
br = (cl.ffill() > op).mean(axis=1)
def ser(s):
    g = B[B.symbol == s]; tp = (g.high + g.low + g.close) / 3; vw = (tp * g.volume).cumsum() / g.volume.cumsum()
    return (g.close / g.open.iloc[0] - 1) * 100, g.close, vw
spy_fo, spy_c, spy_vw = ser("SPY"); q, _, _ = ser("QQQ"); iw, _, _ = ser("IWM")
st = {}
for cp in pd.date_range("2026-11-05 11:00", "2026-11-05 15:30", freq="30min", tz=TZ):
    t = cp - pd.Timedelta("1min")
    up = spy_fo.asof(t) >= 0.15 and spy_c.asof(t) > spy_vw.asof(t) and br.asof(t) >= 0.5 and (q.asof(t) > 0 or iw.asof(t) > 0)
    dn = spy_fo.asof(t) <= -0.15 and spy_c.asof(t) < spy_vw.asof(t) and br.asof(t) <= 0.5 and (q.asof(t) < 0 or iw.asof(t) < 0)
    st[cp] = "UP" if up else "DOWN" if dn else "MIXED"
    print(f"{cp:%H:%M} SPY {spy_fo.asof(t):+.2f}% vwap {'above' if spy_c.asof(t) > spy_vw.asof(t) else 'below'} breadth_open {br.asof(t):.2f} QQQ {q.asof(t):+.2f} IWM {iw.asof(t):+.2f} -> {st[cp]}")
A = pd.read_csv(HERE.parent / "gate1" / "shadow_rule_setup_states.csv"); allow = {r.setup: set(str(r.allowed).split(",")) for _, r in A.iterrows()}
T = pd.read_csv(HERE.parent / "nightly1105" / "trades.csv"); T = T[T.run_id == 1].copy()
T["nt"] = pd.to_datetime(T.nt, utc=True, format="mixed").dt.tz_convert(TZ)
cps = sorted(st)
def state(t):
    k = [c for c in cps if c <= t]; return st[k[-1]] if k else None
T["state"] = T.nt.map(state)
g = T[T.strategy.isin(allow) & T.state.notna()].copy(); g["drop"] = [s not in allow[k] for k, s in zip(g.strategy, g.state)]
d = g[g["drop"]]; k = g[~g["drop"]]
print(f"gated setups traded after 11:00: {g.strategy.nunique()} setups / {len(g)} entries; dropped {len(d)} ({d.radj.sum():+.2f}R, avg {d.radj.mean():+.3f}); "
      f"kept {len(k)} ({k.radj.sum():+.2f}R); gated - ungated = {-d.radj.sum():+.2f}R; by acct " + "; ".join(f"{a} drop {len(x)} {x.radj.sum():+.1f}R" for a, x in d.groupby('acct')))
