"""Write top5_1026 backlog lines (research/backlog.jsonl format) to backlog_proposals.jsonl; the lead appends them.
One line per setup grid (status failed: nothing met the Testing bar) plus one per variant that beat its parent at the
pre-declared bar (status rework, tag top5-tune). Educational only - not financial advice."""
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
R = pd.read_csv(OUT / "results.csv")
SRC = "BDI top-5 execution tune 2026-10-26 (ninth run) (research/bdi/top5_1026/NOTES.md)"
E = " Educational only - not financial advice."
ACCT = {"CWT14-failbrk-pdl-p05-long": "testing1", "NS3-failed-vwap-reclaim-short-FD": "testing2",
        "MF2-open-rsimidhi-flowsell-FD": "primary", "MF4-h40-open-flowsell-FD": "primary",
        "L3-gap-slope-rsi5hi-FD": "testing2"}
LIVE = {"C01": "lab module / config: stop 1.5 x 0.25 x atr_d, target and scale-out price unchanged (same $ risk -> fewer shares).",
        "C02": "as C01 with 2.0 x 0.25 x atr_d.", "E04": "stop x1.25 of the live stop, target price unchanged (same $ risk).",
        "E05": "as E04 with x1.5.", "C08": "config only: window end 13:00.", "E12": "config only: window end 13:00.",
        "E18": "config only: window end 11:30.", "E11": "config only: window start 10:30.",
        "C10": "needs a window gap (skip 10:00-10:29) - two windows or a module filter.",
        "C15": "needs a window gap (skip 10:30-11:29) - two windows or a module filter.",
        "E13": "needs a window gap (skip 10:00-10:29) - two windows or a module filter.",
        "E06": "live scale-out: half at +0.25 x 0.25 x atr_d, rest to breakeven (scale_out_r 0.25 + live_scale_out).",
        "C11": "module filter on context spy_fo >= -0.5.", "C12": "module filter on the stock's fromOpen >= -2%.",
        "E14": "module filter on context spy_fo <= 0 (shorts only while SPY is not up from its open)."}
GRIDT = {"CWT14-failbrk-pdl-p05-long": "stop x1.5/x2.0 at same $, target 0.35/0.75R, time stops 15/90 min, clock exit 14:00, window end 13:00, skip 09:50-09:59 / 10:00-10:29 / 10:30-11:29, SPY-crash, SPY-chase and stock-crash filters, re-entry cd15, limit entry 0.1R",
         "default": "time stops 15/30/60 min, stop x0.85/1.25/1.5 at same $, scale-out, breakeven, two targets, wait one bar, windows, skip 10:00-10:29, SPY-up filter, clock exit 14:00, limit entry 0.1R"}
BARS = {"CWT14-failbrk-pdl-p05-long": 2.35, "NS3-failed-vwap-reclaim-short-FD": 2.40, "MF2-open-rsimidhi-flowsell-FD": 2.38,
        "MF4-h40-open-flowsell-FD": 2.40, "L3-gap-slope-rsi5hi-FD": 2.38}
COMMON = ("open two-year history, locked block 2024-11..2025-02 never loaded; TRAIN <= 2025-12, VALID 2026-01..03 + "
          "07..09-15; production + tod costs, x3 extended tier; CWT14 entries = top5_1019 kernels (first signal per "
          "symbol-day, parent = live t05s1 + 0.25R scale-out), short entries = gates1021 live-shaped signals rebuilt "
          "(parity vs cached production R, all rows of all 4 parents: mean |d| <= 0.00004R, 100% within 0.01R); exits = "
          "top5_1019 5-minute simulator; stop-distance variants at the same $ risk; R in units of the live stop; "
          "study N 86, bars 2.35-2.40 (setup) / 2.98 (study).")


def fmt(r):
    return (f"n {int(r.n_tv)}, win {r.win_tv:.3f} (break-even {r.be_win:.3f}), exp {r.exp_tv:+.4f}R, TRAIN {r.exp_train:+.4f} / "
            f"VALID {r.exp_valid:+.4f} (t {r.t_valid}), up {r.up:+.3f} / down {r.down:+.3f}, excess vs random {r.excess_vs_random:+.4f}R")


new = []
for s, d in R.groupby("setup", sort=False):
    p = d[d.is_parent].iloc[0]
    v = d[~d.is_parent]
    best = v.sort_values("t_improve", ascending=False).iloc[0]
    new.append({"id": f"top5-1026-{s}-exec",
                "title": f"{s}: execution variants ({GRIDT.get(s, GRIDT['default'])})",
                "category": "setup", "parent": None, "tags": [ACCT[s], "top5-tune", "bdi", "bdi-1026"],
                "hypothesis": "An execution change converts the live setup's win rate into more R per trade.",
                "status": "failed", "configs_tried": len(v),
                "notes": (f"top5_1026 (PLAN.md pre-declared). {len(v)} one-knob variants. {COMMON} Parent {fmt(p)}. "
                          f"{int((v.exp_tv > 0).sum())} of {len(v)} variants exp > 0; {int(v.beats_parent.sum())} beat the parent; "
                          f"best {best['var']} ({best['knob']}) {best['exp_tv']:+.4f}R, d {best['d_tv']:+.4f}R, t {best['t_improve']}. "
                          f"Testing bar: 0. Parent avg R without its best day {p.ex_best_day:+.4f}." + E)})
    for _, r in v[v.beats_parent.fillna(False).astype(bool)].iterrows():
        new.append({"id": f"top5-1026-{s}-{r['var']}-{r['knob']}",
                    "title": f"{s} with {r['knob']} ({r['var']}, top5_1026 PLAN.md section 3)",
                    "category": "setup", "parent": f"top5-1026-{s}-exec",
                    "tags": [ACCT[s], "top5-tune", "bdi", "bdi-1026", "beats-parent"],
                    "hypothesis": "This execution change raises the live parent's R per trade on TRAIN and on VALID.",
                    "status": "rework", "configs_tried": len(v), "live_support": LIVE.get(r["var"], ""),
                    "notes": (f"top5_1026 beats parent: d {r['d_tv']:+.4f}R (TRAIN {r['d_train']:+.4f}, VALID {r['d_valid']:+.4f}), "
                              f"day-clustered t {r['t_improve']} vs setup bar {BARS[s]}. Variant {fmt(r)}. Fails the Testing bar "
                              f"(variant still loses after costs in at least one period or in up/down sessions). " + COMMON + E)})
with open(OUT / "backlog_proposals.jsonl", "w") as fh:
    for n in new:
        fh.write(json.dumps({"added": "2026-10-26", "source": SRC, "module": None, "variant": None, **n}) + "\n")
print(len(new), "proposals written")
