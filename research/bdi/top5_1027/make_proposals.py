"""Write top5_1027 backlog lines (research/backlog.jsonl format) to backlog_proposals.jsonl; the lead appends them.
One line per setup grid (status failed: nothing met the Testing bar) plus one per variant that beat its parent at the
pre-declared bar (status rework, tag top5-tune). Educational only - not financial advice."""
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
R = pd.read_csv(OUT / "results.csv")
SRC = "BDI top-5 execution tune 2026-10-27 (tenth run) (research/bdi/top5_1027/NOTES.md)"
E = " Educational only - not financial advice."
ACCT = {"CWT12-coil-k4-long": "testing2", "CWT14-failbrk-pdl-p10-lowvol-long": "testing2",
        "NM-AR-AM-gapdown-capitulation-long": "testing2", "exhaustion_short": "testing1",
        "L3-gap-slope-lowdist-FD": "testing1"}
LIVE = {"K01": "lab module / config: stop 2.0 x 0.25 x atr_d, target price unchanged (same $ risk -> fewer shares).",
        "K02": "stop 2.5 x 0.25 x atr_d (same $ risk).", "E04": "stop x1.25 of the live stop, target price unchanged (same $ risk).",
        "E05": "as E04 with x1.5.", "K08": "config only: window end 13:00.", "K12": "config only: window end 10:30 (coil) / limit entry (pdl).",
        "E11": "config only: window start.", "E12": "config only: window end.", "E13": "config only: window change.",
        "K07": "needs a window gap (skip 10:00-10:29) - two windows or a module filter.",
        "K13": "needs a window gap or new target.", "K14": "needs a window gap (skip 10:30-11:29).",
        "E06": "live scale-out: half at +0.5 x 0.25 x atr_d, rest to breakeven (scale_out_r 0.5 + live_scale_out).",
        "K09": "module filter on context spy_fo / stock fromOpen.", "K10": "module filter on context spy_fo / stock fromOpen.",
        "K11": "module filter on context spy_fo (coil) / limit entry (pdl).",
        "E14": "module filter on context spy_fo sign.", "E18": "module filter on context spy_fo +-0.5%."}
GRIDT = {"CWT12-coil-k4-long": "stop x2.0 at same $, targets 0.75/1.0R (scale kept) and 1.0R no scale, time stops 15/90 min, clock exit 13:00, window end 10:30, skip 10:00-10:29, SPY-crash / SPY-chase / stock-crash filters, limit entry 0.1R",
         "CWT14-failbrk-pdl-p10-lowvol-long": "stop x2.0/x2.5 at same $, targets 0.35/0.75R, time stops 15/90 min, clock exit 14:00, window end 13:00, skip 10:00-10:29 / 10:30-11:29, SPY-crash / SPY-chase / stock-crash filters, limit entry 0.1R",
         "default": "time stops 15/30/60 min, stop x0.85/1.25/1.5 at same $, scale-out, breakeven, two targets, wait one bar, three window rows, SPY-sign and SPY 0.5% filters, clock exit, limit entry 0.1R"}
BARS = json.loads((OUT / "summary.json").read_text())["bar_setup"]
COMMON = ("open two-year history, locked block 2024-11..2025-02 never loaded; TRAIN <= 2025-12, VALID 2026-01..03 + "
          "07..09-15; production + tod costs, x3 extended tier; CWT entries = top5_1021 kernels (first signal per "
          "symbol-day; parity vs top5_1021 parents), NM-AR-AM / exhaustion_short / L3-lowdist-FD entries = gates1021 "
          "live-shaped signals rebuilt (parity vs cached production R); exits = top5_1026 5-minute simulator; "
          "stop-distance variants at the same $ risk; R in units of the live stop; study N 81, bars 2.26-2.40 (setup) / "
          "2.96 (study).")


EXTRA = {"NM-AR-AM-gapdown-capitulation-long": (" The parent's positive TRAIN/VALID backtest is IN-SAMPLE: swarm1017 fitted "
            "this near-miss on the same TRAIN and picked its plateau on VALID, and its forward/holdout follow-up failed "
            "(swarm1017/followup: 88 trades -0.254R). All signals fall 10:30-11:00 (60-minute return), so window rows "
            "E11/E13 equal the parent and E12 (until 10:30) is empty; all three are counted."),
         "exhaustion_short": " Parent is flat after costs (+0.0035R; TRAIN -0.053 / VALID +0.105, up sessions -0.062)."}


def fmt(r):
    return (f"n {int(r.n_tv)}, win {r.win_tv:.3f} (break-even {r.be_win:.3f}), exp {r.exp_tv:+.4f}R, TRAIN {r.exp_train:+.4f} / "
            f"VALID {r.exp_valid:+.4f} (t {r.t_valid}), up {r.up:+.3f} / down {r.down:+.3f}, excess vs random {r.excess_vs_random:+.4f}R")


new = []
for s, d in R.groupby("setup", sort=False):
    p = d[d.is_parent].iloc[0]
    v = d[~d.is_parent]
    best = v.sort_values("t_improve", ascending=False).iloc[0]
    new.append({"id": f"top5-1027-{s}-exec",
                "title": f"{s}: execution variants ({GRIDT.get(s, GRIDT['default'])})",
                "category": "setup", "parent": None, "tags": [ACCT[s], "top5-tune", "bdi", "bdi-1027"],
                "hypothesis": "An execution change converts the live setup's win rate into more R per trade.",
                "status": "failed", "configs_tried": len(v),
                "notes": (f"top5_1027 (PLAN.md pre-declared). {len(v)} one-knob variants. {COMMON} Parent {fmt(p)}. "
                          f"{int((v.exp_tv > 0).sum())} of {len(v)} variants exp > 0; {int(v.beats_parent.sum())} beat the parent; "
                          f"best {best['var']} ({best['knob']}) {best['exp_tv']:+.4f}R, d {best['d_tv']:+.4f}R, t {best['t_improve']}. "
                          f"Testing bar: 0. Parent avg R without its best day {p.ex_best_day:+.4f}." + EXTRA.get(s, "") + E)})
    for _, r in v[v.beats_parent.fillna(False).astype(bool)].iterrows():
        new.append({"id": f"top5-1027-{s}-{r['var']}-{r['knob']}",
                    "title": f"{s} with {r['knob']} ({r['var']}, top5_1027 PLAN.md section 3)",
                    "category": "setup", "parent": f"top5-1027-{s}-exec",
                    "tags": [ACCT[s], "top5-tune", "bdi", "bdi-1027", "beats-parent"],
                    "hypothesis": "This execution change raises the live parent's R per trade on TRAIN and on VALID.",
                    "status": "rework", "configs_tried": len(v), "live_support": LIVE.get(r["var"], ""),
                    "notes": (f"top5_1027 beats parent: d {r['d_tv']:+.4f}R (TRAIN {r['d_train']:+.4f}, VALID {r['d_valid']:+.4f}), "
                              f"day-clustered t {r['t_improve']} vs setup bar {BARS[s]}. Variant {fmt(r)}. Fails the Testing bar "
                              f"(variant still loses after costs in at least one period or in up/down sessions). " + COMMON + E)})
with open(OUT / "backlog_proposals.jsonl", "w") as fh:
    for n in new:
        fh.write(json.dumps({"added": "2026-10-27", "source": SRC, "module": None, "variant": None, **n}) + "\n")
print(len(new), "proposals written")
