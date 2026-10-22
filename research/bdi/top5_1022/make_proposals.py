"""Write top5_1022 backlog lines (research/backlog.jsonl format) to backlog_proposals.jsonl; the lead appends them.
One line per setup grid (status failed: nothing met the Testing bar) plus one per variant that beat its parent at the
pre-declared bar (status rework, tag top5-tune). Educational only - not financial advice."""
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
R = pd.read_csv(OUT / "results.csv")
SRC = "BDI top-5 execution tune 2026-10-22 (seventh run) (research/bdi/top5_1022/NOTES.md)"
E = " Educational only - not financial advice."
ACCT = {"MF3-open-flowsell-rsi5hi-FD": "testing1", "RW7-gapdn-bounce-early-short-FD": "testing1",
        "RW4-ns3-adv150-short-FD": "testing1+testing2", "exhaustion_short-FD": "testing1+testing2",
        "MF5-flowsell-vwapup-rsi5hi-FD": "testing2", "RW1-gapdn-bounce-flowsell-short-FD": "testing2"}
LIVE = {"E04": "lab module / config: stop 1.25 x 0.25 x atr_d with the target price unchanged (same $ risk -> fewer shares); "
               "same mechanism as ns3var1022 V1 (r_atr_frac) - check that the target stays at the parent's price.",
        "E05": "as E04 with 1.5 x 0.25 x atr_d.",
        "E11": "config only: window start 10:30.", "E12": "config only: window end 13:00.",
        "E13": "needs a window gap (skip 10:00-10:29) - two windows or a module filter.",
        "E14": "module filter on context spy_fo <= 0 (shorts only while SPY is not up from its open)."}
COMMON = ("open two-year history, locked block 2024-11..2025-02 never loaded; TRAIN <= 2025-12, VALID 2026-01..03 + "
          "07..09-15; production + tod costs; entries = gates1021 cached live-shaped signals, exits = top5_1019 5-minute "
          "simulator (parent parity vs cached production R: mean |d| 0.004R, 99.5% within 0.05R on 2025-06); stop-distance "
          "variants at the same $ risk; study N 90, bars 2.33 (setup) / 3.00 (study).")


def fmt(r):
    return (f"n {int(r.n_tv)}, win {r.win_tv:.3f} (break-even {r.be_win:.3f}), exp {r.exp_tv:+.4f}R, TRAIN {r.exp_train:+.4f} / "
            f"VALID {r.exp_valid:+.4f} (t {r.t_valid}), up {r.up:+.3f} / down {r.down:+.3f}, excess vs random {r.excess_vs_random:+.4f}R")


new = []
for s, d in R.groupby("setup", sort=False):
    p = d[d.is_parent].iloc[0]
    v = d[~d.is_parent]
    best = v.sort_values("t_improve", ascending=False).iloc[0]
    new.append({"id": f"top5-1022-{s}-exec",
                "title": f"{s}: execution variants (time stops, stop x0.85/1.25/1.5 at same $, scale-out, breakeven, target 0.75/1.5R, wait one bar, windows, skip 10:00-10:29, SPY-up filter)",
                "category": "setup", "parent": None, "tags": [ACCT[s], "top5-tune", "bdi", "bdi-1022"],
                "hypothesis": "An execution change converts the live setup's win rate into more R per trade.",
                "status": "failed", "configs_tried": len(v),
                "notes": (f"top5_1022 (PLAN.md pre-declared). {len(v)} one-knob variants. {COMMON} Parent {fmt(p)}. "
                          f"{int((v.exp_tv > 0).sum())} of {len(v)} variants exp > 0; {int(v.beats_parent.sum())} beat the parent; "
                          f"best {best['var']} ({best['knob']}) {best['exp_tv']:+.4f}R, d {best['d_tv']:+.4f}R, t {best['t_improve']}. "
                          f"Testing bar: 0." + E)})
    for _, r in v[v.beats_parent.fillna(False).astype(bool)].iterrows():
        new.append({"id": f"top5-1022-{s}-{r['var']}-{r['knob']}",
                    "title": f"{s} with {r['knob']} ({r['var']}, top5_1022 PLAN.md section 3)",
                    "category": "setup", "parent": f"top5-1022-{s}-exec",
                    "tags": [ACCT[s], "top5-tune", "bdi", "bdi-1022", "beats-parent"],
                    "hypothesis": "This execution change raises the live parent's R per trade on TRAIN and on VALID.",
                    "status": "rework", "configs_tried": 15, "live_support": LIVE.get(r["var"], ""),
                    "notes": (f"top5_1022 beats parent: d {r['d_tv']:+.4f}R (TRAIN {r['d_train']:+.4f}, VALID {r['d_valid']:+.4f}), "
                              f"day-clustered t {r['t_improve']} vs setup bar 2.33. Variant {fmt(r)}. Fails the Testing bar "
                              f"(variant still loses after costs in at least one period / up sessions). " + COMMON + E)})
with open(OUT / "backlog_proposals.jsonl", "w") as fh:
    for n in new:
        fh.write(json.dumps({"added": "2026-10-22", "source": SRC, "module": None, "variant": None, **n}) + "\n")
print(len(new), "proposals written")
