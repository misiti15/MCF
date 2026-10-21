"""Write top5_1021 backlog PROPOSALS (research/backlog.jsonl format) to research/bdi/top5_1021/backlog_proposals.jsonl.
It does NOT touch research/backlog.jsonl; the lead appends these lines. Educational only - not financial advice.
One entry per setup grid, plus one per variant that beat its parent on TRAIN and VALID at the pre-declared bar
(tag top5-tune). Status follows the PLAN bars: 'testing-candidate' only if the Testing bar is met, else 'rework'
(beats parent) / 'failed' (grid)."""
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
R = pd.read_csv(OUT / "results.csv")
SRC = "BDI top-5 execution tune 2026-10-21 (sixth run) (research/bdi/top5_1021/NOTES.md)"
E = " Educational only - not financial advice."
PARENTS = {"CWT14": "cwt-b-b3-failed-breakout-reversal", "CWT12": "cwt-b-b4-coil-flag-breakout"}
LIVE = {
    "E04": "module only: new research module, GEOM 'S', stop_price = close -/+ 1.25 x 0.25 x atr_d, target_price = parent's "
           "target price; scale_out_r must be re-expressed in the new R (parent trigger / 1.25) so the trigger price stays put. "
           "LabStrategy sizes by the stop distance, so $ risk stays the same. Plus a config entry.",
    "E05": "as E04 with 1.5 x 0.25 x atr_d (scale_out_r / 1.5).",
    "E06": "config only: scale_out_r (live scale-out runs since the 2026-10-19 runner fix).",
    "E07": "config only: scale_out_r.",
    "E14": "config: breakeven trigger (check LabStrategy support).", "E15": "as E14.", "E01": "needs a time-stop exit for lab setups (time_stop_bars / time_stop_r); check LabStrategy support before proposing.",
    "E02": "as E01.",
    "R0": "config only: scale_out_r null / live_scale_out false.",
    "E08": "needs code (entry_delay_bars).",
    "E09": "config only: window.", "E10": "config only: window.", "E11": "config only: window.",
    "E12": "new module with context [spy_fo].", "E13": "roughly refire + cooldown (counts from the signal, not the exit).",
    "T1": "new module (p x 0.8).", "T2": "new module (p x 1.2).", "E03": "module with GEOM 'S' (0.85 x 0.25 x atr_d)."}
COMMON = ("open two-year history, locked block 2024-11..2025-02 never loaded; TRAIN <= 2025-12, VALID 2026-01..03 + "
          "07..09-15; production + tod costs; top5_1019 5-minute path simulator with parity to gates.lab_trades on 2025-06 "
          "(mean |diff| <= 4e-5 R, 100% within 0.01R, all 4 setups); parent = live config (coil-k4 incl. its 0.35R scale-out); "
          "stop-distance variants scored at the same $ risk; random control = 5 same-minute symbols, same mechanics.")


def fmt(r):
    return (f"n {int(r.n_tv)}, win {r.win_tv:.3f}, avg win {r.avg_win:+.3f} / avg loss {r.avg_loss:+.3f} (break-even win {r.be_win:.3f}), "
            f"exp {r.exp_tv:+.4f}R (t {r.t_tv}), TRAIN {r.exp_train:+.4f} / VALID {r.exp_valid:+.4f} (t {r.t_valid}), "
            f"up {r.up:+.3f} / down {r.down:+.3f}, excess vs random {r.excess_vs_random:+.4f}R")


new = []
for s, d in R.groupby("setup", sort=False):
    acct = {"CWT14-failbrk-pdl-p10-lowvol-long": "primary", "CWT12-coil-k6-long": "testing1+testing2"}.get(s, "testing2")
    p = d[d.is_parent].iloc[0]
    v = d[~d.is_parent]
    best = v.sort_values("t_improve", ascending=False).iloc[0]
    both = v[(v.d_train > 0) & (v.d_valid > 0)]
    knobs = ", ".join(f"{r['var']} {r['knob']}" for _, r in v.iterrows())
    nt = int(v.testing_bar.sum())
    note = (f"top5_1021 (scan_1021.py / report_1021.py, pre-declared in PLAN.md). {len(v)} one-knob execution variants ({knobs}); "
            f"{COMMON} Parent TRAIN+VALID {fmt(p)}. {int((v.exp_tv > 0).sum())} of {len(v)} variants have exp > 0; "
            f"{int(v.beats_parent.sum())} beat the parent at the setup bar {p.bar_setup}; {len(both)} improve on both TRAIN and VALID; "
            f"best {best['var']} ({best['knob']}) {best['exp_tv']:+.4f}R, d {best['d_tv']:+.4f}R, t_improve {best['t_improve']} "
            f"(setup bar {best['bar_setup']}, lineage bar {best['bar_lineage']}). Testing bar (VALID t >= {p.t_testing_bar}, exp > 0, "
            f"both regimes): {nt}.")
    new.append({"id": f"top5-1021-{s}-exec",
                "title": f"{s}: execution variants (scale-out toggle/levels, time stop, stop x0.85/1.25/1.5 at same $, wait one bar, window, SPY-direction filter, re-entry cooldown, thresholds +-20%, coil-k6 breakeven)",
                "category": "setup", "parent": PARENTS[s[:5]], "tags": [acct, s[:5].lower(), "top5-tune", "bdi"],
                "hypothesis": "An execution change (exit management, entry timing or one filter) converts the live setup's win rate into more R per trade.",
                "status": "testing-candidate" if nt else "failed", "configs_tried": int(p.lineage_N), "notes": note + E})
    for _, r in v[v.beats_parent].iterrows():
        new.append({"id": f"top5-1021-{s}-{r['var']}-{r['knob']}",
                    "title": f"{s} with {r['knob']} ({r['var']}, top5_1021 PLAN.md section 3)",
                    "category": "setup", "parent": PARENTS[s[:5]], "tags": [acct, s[:5].lower(), "top5-tune", "bdi", "beats-parent"],
                    "hypothesis": "This execution change raises the live parent's R per trade on TRAIN and on VALID.",
                    "status": "testing-candidate" if r["testing_bar"] else "rework", "configs_tried": int(r["lineage_N"]),
                    "live_support": LIVE.get(r["var"], ""),
                    "notes": (f"top5_1021 beats parent: d {r['d_tv']:+.4f}R (TRAIN {r['d_train']:+.4f}, VALID {r['d_valid']:+.4f}), "
                              f"day-block bootstrap t {r['t_improve']} vs setup bar {r['bar_setup']} (lineage bar {r['bar_lineage']}: "
                              f"{'met' if r['t_improve'] >= r['bar_lineage'] else 'not met'}). Variant {fmt(r)}. "
                              + ("Meets the Testing bar. " if r["testing_bar"] else
                                 "Fails the Testing bar (variant exp or VALID t, regimes); status rework = pair round (rule 18) or forward sessions. ")
                              + COMMON + E)})
with open(OUT / "backlog_proposals.jsonl", "w") as fh:
    for n in new:
        fh.write(json.dumps({"added": "2026-10-21", "source": SRC, "module": None, "variant": None, **n}) + "\n")
print(len(new), "proposals written")
