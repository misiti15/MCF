"""Nightly 2026-11-09 forward shadows gate1-checkpoint-gate + comp15-w60-early (journal-only, no trading change).
Uses the LIVE compass record (origin/mcf-data-compass compass/2026-11-09.csv: gate1_state at each 30-min checkpoint from
11:00, W60 readings every 15 min) instead of recomputing breadth; rule as research/bdi/1106/forward_1106.py.
R = pnl_adj / $ risk (costs in), journals run 1, all 7 accounts (nightly1109/trades.csv).
Usage: python forward_gate1.py   Educational only - not financial advice."""
import io, subprocess
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; D = "2026-11-09"; TZ = "America/New_York"
C = pd.read_csv(io.StringIO(subprocess.run(["git", "-C", str(ROOT), "show", f"origin/mcf-data-compass:compass/{D}.csv"],
                                           capture_output=True, text=True, check=True).stdout))
T = pd.read_csv(HERE / "trades.csv"); T = T[T.run_id == 1].copy()
T["nt"] = pd.to_datetime(T.nt, utc=True, format="mixed").dt.tz_convert(TZ)
out = []; P = out.append
cp = C[C["T"].isin([f"{h:02d}:{m:02d}" for h in range(11, 16) for m in (0, 30)])][["T", "gate1_state"]]
st = {pd.Timestamp(f"{D} {t}", tz=TZ): v for t, v in zip(cp["T"], cp["gate1_state"])}
P("GATE1 checkpoint states (live compass): " + "; ".join(f"{k:%H:%M} {v}" for k, v in st.items()))
A = pd.read_csv(HERE.parent / "gate1" / "shadow_rule_setup_states.csv"); allow = {r.setup: set(str(r.allowed).split(",")) for _, r in A.iterrows()}
cps = sorted(st)
T["state"] = T.nt.map(lambda t: (lambda k: st[k[-1]] if k else None)([c for c in cps if c <= t]))
g = T[T.strategy.isin(allow) & T.state.notna()].copy(); g["drop"] = [s not in allow[k] for k, s in zip(g.strategy, g.state)]
d_, k_ = g[g["drop"]], g[~g["drop"]]
P(f"gate1: listed-setup entries after 11:00 {len(g)}; dropped {len(d_)} {d_.radj.sum():+.2f}R (avg {d_.radj.mean() if len(d_) else float('nan'):+.3f}); "
  f"kept {len(k_)} {k_.radj.sum():+.2f}R; gated - ungated {-d_.radj.sum():+.2f}R; by account " + str({a: round(-x.radj.sum(), 2) for a, x in d_.groupby('acct')}))
P("dropped by setup " + str(d_.groupby(["acct", "strategy"]).radj.agg(["size", "sum"]).round(2).to_dict("index")))
p = T[T.acct == "p"]
P(f"Primary: {len(p)} entries, {int((p.nt >= pd.Timestamp(f'{D} 11:00', tz=TZ)).sum())} at/after 11:00 "
  f"({p[p.nt >= pd.Timestamp(f'{D} 11:00', tz=TZ)].strategy.value_counts().to_dict()}); listed in gate: "
  f"{sorted(set(p.strategy) & set(allow))} -> dropped {int(d_[d_.acct == 'p'].shape[0])}")
mf4 = p[p.strategy == "MF4-h40-open-flowsell-FD"]
P(f"MF4-FD (not a gate-listed setup): {len(mf4)} entries {mf4.nt.min():%H:%M}-{mf4.nt.max():%H:%M}, {mf4.radj.sum():+.2f}R - all before the first checkpoint")
# comp15 W60
w = C[["T", "w60", "votes", "w60_low_conf"]]
conf = w[w.w60.str.contains("confirmed", na=False)]
first = (conf.iloc[0]["T"] + " " + conf.iloc[0]["w60"]) if len(conf) else "never confirmed"
side = w.w60.map(lambda s: 1 if "up" in str(s).lower() else -1 if "down" in str(s).lower() else 0)
flips = int(sum(1 for a, b in zip(side, side[1:]) if a * b < 0))
c30 = C[C.c30.notna()].c30
P(f"comp15: W60 first confirmed {first}; 30-min compass first confirmed "
  f"{(C[C.c30.astype(str).str.contains('confirmed')].iloc[0].c30_at) if C.c30.astype(str).str.contains('confirmed').any() else 'never'}; "
  f"side flips {flips}; readings " + " ".join(f"{t} {v}" for t, v in zip(w["T"], w["w60"])))
txt = "\n".join(out); (HERE / "forward_gate1_out.txt").write_text(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
