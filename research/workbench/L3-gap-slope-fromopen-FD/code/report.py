import math, pandas as pd, numpy as np
r = pd.concat([pd.read_csv("results_main.csv"), pd.read_csv("results_combo.csv").query("cfg != 'PARENT'")])
x = pd.read_csv("extras.csv")
P = {t: r[(r.cfg == "PARENT") & (r.test == t) & (r.split == "ALL")].iloc[0] for t in ("replay", "2y")}
WB = {"V01 window end 15:00->13:00 (P6)": "WB1", "V09 gap <=-2.66->-3.2 (P4+P10)": "WB2", "C1 window end 13:00 + gap <=-3.2 (P6+P4/P10)": "WB3"}
def verdict(c):
    why = []
    for t in ("replay", "2y"):
        a = r[(r.cfg == c) & (r.test == t) & (r.split == "ALL")].iloc[0]; p = P[t]
        meets = a.avg >= p.avg - 0.01 or (p.avg > 0 and a.avg >= 0.95 * p.avg)
        if not meets: why.append(f"{t} avg R {a.avg:+.3f} < parent {p.avg:+.3f}")
        if a.avg_wo_best < p.avg_wo_best - 0.02: why.append(f"{t} w/o best day {a.avg_wo_best:+.3f} vs {p.avg_wo_best:+.3f}")
        if a.worst_day < p.worst_day * 1.10: why.append(f"{t} worst day {a.worst_day:+.1f}R vs {p.worst_day:+.1f}R (>10% worse)")
    return ("PASS" if not why else "FAIL"), "; ".join(why)
N = r.cfg.nunique() - 1; bar = max(1.5, math.sqrt(2 * math.log(N)))
L = ["# Workbench results - Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` vs its copies", "",
     "Educational only — not financial advice. Mechanic job 2026-11-16 (market hours: research only; no config change).", "",
     f"**Configs tried: {N}** (12 one-part tweaks V01-V12 pre-declared in `variants_decl` before any score + 1 combined copy C1 of two that passed alone). "
     f"Bar for the paired day-t on the improvement: max(1.5, sqrt(2 ln {N})) = {bar:.2f} (lineage incl. L3LEASH/L3LEASH-2's 26: N 39, bar {math.sqrt(2*math.log(39)):.2f}). "
     "Under the owner's clarified pass rule (2026-11-16: meet-or-exceed the parent on the identical backtests; 'meets' = within 0.01R or >= 95%; "
     "not worse on avg R w/o best day by > 0.02R or on worst day by > 10%; no t hurdle) the t is reported, not used to pass. **No copy clears the t bar** — "
     "the improvements are small and not statistically distinguishable from noise; they pass on meet-or-exceed only.", "",
     "## Method (identical for parent and every copy)",
     "- **Replay of the live sessions (backtest, not live results):** every symbol-day on which the parent signalled live in any account and passed the "
     "shortable+ETB check, 2026-10-12..11-13 (384 symbol-days, 23 sessions with signals). 1-min SIP bars (read-only GET) -> lab frame (mcf.report.engine.lab_frame "
     "+ daily priors as live). Limit: symbols that never signalled live are not in it, so copies that LOOSEN a condition cannot be replayed (none of the shortlist loosens).",
     "- **2-year backtest:** lab frames 2024-10..2026-11-04, **locked block 2024-11-01..2025-02-28 never read** (asserted), restricted to names shortable+ETB on >= 90% of "
     "26 universe snapshots 10-07..11-13 (E90 proxy, research/l3leash2). Splits TRAIN <= 2025-12-31, VALID 2026-01..10-05, FWD 10-06..11-04.",
     "- Same engine for both: signals on 5-min bar close, refire chain (cooldown), entry at signal-bar close, price >= $5, exits walked on 1-min bars "
     "(stop first; target fills only when traded through by >= $0.01 — UGP 10-26 touched without filling; flat 15:55), **LR8 costs** (entry 1 bp + SEC + TAF + CAT; "
     "stop max($0.02, 4 bps); time exit max($0.01, 1 bp); target at limit), live book (<= 30 open lots, <= 3 per symbol, -2R net latch). "
     "Parent's live journal record NOT used in the pass decision (owner).",
     "- Rule changes inside the replay window (ledger): LR1/LR3/LR5/LR7 (11-12), LR8 cost model (11-12), Primary -2R latch (10-29), Primary size/cap 30 (10-28), "
     "moves Testing 1 <-> Primary (10-20, 10-22, 10-30), TEAM-6 (11-10). The replay applies today's rules to every session, so these do not mix into the comparison.", "",
     "## Side by side (ALL = whole test)", "",
     "| copy | change | test | trades | win % | avg R | avg R w/o best day | total R | worst day | t vs parent (paired by day) | dR vs parent | verdict |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|"]
order = ["PARENT"] + [c for c in r.cfg.unique() if c != "PARENT"]
for c in order:
    v, why = ("—", "") if c == "PARENT" else verdict(c)
    for t in ("replay", "2y"):
        a = r[(r.cfg == c) & (r.test == t) & (r.split == "ALL")].iloc[0]
        L.append(f"| {WB.get(c, '' if c != 'PARENT' else 'parent')} | {c} | {t} | {a.trades} | {a.win:.1%} | {a.avg:+.3f} | {a.avg_wo_best:+.3f} | {a.total:+.1f} | "
                 f"{a.worst_day:+.1f} | {a.t_vs_parent:+.2f} | {a.dR_vs_parent:+.1f} | {v if t == 'replay' else why} |")
L += ["", "## 2-year by split (consistency check)", "", "| config | TRAIN avg R (n) | VALID avg R (n) | FWD avg R (n) | TRAIN dR | VALID dR | FWD dR |", "|---|---|---|---|---|---|---|"]
for c in order:
    s = {sp: r[(r.cfg == c) & (r.test == "2y") & (r.split == sp)].iloc[0] for sp in ("TRAIN", "VALID", "FWD")}
    L.append(f"| {c} | " + " | ".join(f"{s[k].avg:+.3f} ({s[k].trades})" for k in s) + " | " + " | ".join(f"{s[k].dR_vs_parent:+.1f}" for k in s) + " |")
L += ["", "## Shape (avg win / avg loss, median hold min, exit mix; 2-year by SPY day type open->close >+0.25% up / <-0.25% down)", "",
      "| config | test | avg win | avg loss | median hold | stop share | target share | up-day avg R | flat | down |", "|---|---|---|---|---|---|---|---|---|---|"]
for _, e in x.iterrows():
    f = lambda v: "" if pd.isna(v) else f"{v:+.3f}"
    L.append(f"| {e.cfg} | {e.test} | {e.avg_win:+.3f} | {e.avg_loss:+.3f} | {e.hold_med:.0f} | {e.stop_share:.0%} | {e.tgt_share:.0%} | {f(e.up)} | {f(e.flat)} | {f(e.down)} |")
open("RESULTS_body.md", "w").write("\n".join(L) + "\n")
for c in order[1:]: print(c, *verdict(c))
