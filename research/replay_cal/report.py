"""Render a scorecard directory (score.py output) as SCORECARD.md: per account + pooled vs the targets, per setup
(>= 10 live trades, every one listed), daily R. Educational only - not financial advice.

    python research/replay_cal/report.py research/replay_cal/heldout "HELD-OUT 2026-11-02..2026-11-16"
"""
import json
import math
import sys
from pathlib import Path

import pandas as pd

d, title = Path(sys.argv[1]), sys.argv[2]
c = json.loads((d / "scorecard.json").read_text())
f = lambda x, p=3: "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{p}f}"  # noqa: E731
ok = lambda b: "PASS" if b else "FAIL"  # noqa: E731
L = [f"# Replay calibration scorecard — {title}", "",
     "*Educational only — not financial advice. Calibrated session replay (mcf/replay/livecal.py, params_v2) vs the live "
     "paper journals; targets pre-registered in TARGETS.md; R after LR8 costs on each side's own fills.*", "",
     "| account | sessions | live trades | replay trades | match (exact bar) | match ±1 min | extra | R bias (95% CI, session-clustered) | not optimistic | daily R corr | sign agree | skip-reason match | worst day | all targets |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for s in c["accounts"] + [c["pooled"]]:
    v = s["verdict"]
    L.append(f"| {s['account']} | {s['sessions']} | {s['live_trades']} | {s['replay_trades']} | {f(100*s['match'],1)}% {ok(v['T1_match'])} | "
             f"{f(100*s['match_pm1'],1)}% | {f(100*s['extra'],1)}% {ok(v['T2_extra'])} | {f(s['bias'],4)} [{f(s['bias_lo'],4)}, {f(s['bias_hi'],4)}] {ok(v['T3_bias'])} | "
             f"{ok(v['T3_no_optimism'])} | {f(s['daily_corr'])} | {f(100*s['sign_agree'],0)}% {ok(v['T4_daily'])} | {f(100*s['skip_match'],1)}% {ok(v['T5_skip'])} | "
             f"{ok(v['T6_worst'])} | **{ok(v['all'])}** |")
L += ["", "Live R vs replay R (sum, after LR8 costs): " + "; ".join(
    f"{s['account']} {s['live_r']:+.1f} vs {s['replay_r']:+.1f}" for s in c["accounts"] + [c["pooled"]]), ""]
L += ["## Biggest status mismatches (matched signals, live -> replay)", ""]
for s in c["accounts"]:
    L.append(f"- **{s['account']}**: " + "; ".join(f"{k} ×{n}" for k, n in list(s["top_mismatch"].items())[:6]))
ps = pd.read_csv(d / "per_setup.csv")
ps = ps[ps["live_trades"] >= 10].sort_values(["account", "live_trades"], ascending=[True, False])
L += ["", f"## Per setup (≥ 10 live trades: {len(ps)} setups, all listed)", "",
      "| account | setup | live | replay | match | extra | live avg R | replay avg R | bias (matched) |", "|---|---|---|---|---|---|---|---|---|"]
for r in ps.itertuples():
    L.append(f"| {r.account} | {r.setup} | {r.live_trades} | {r.replay_trades} | {f(100*r.match,0)}% | {f(100*r.extra,0)}% | "
             f"{f(r.live_avg_r)} | {f(r.replay_avg_r)} | {f(r.bias)} |")
dd = pd.read_csv(d / "daily.csv")
L += ["", "## Daily R (account-session)", "", "| account | day | live trades | replay trades | live R | replay R |", "|---|---|---|---|---|---|"]
for r in dd.itertuples():
    L.append(f"| {r.account} | {r.day} | {r.live_n} | {r.replay_n} | {r.live_r:+.2f} | {r.replay_r:+.2f} |")
L += ["", "Educational only — not financial advice."]
(d / "SCORECARD.md").write_text("\n".join(L) + "\n")
print("\n".join(L[:12]))
