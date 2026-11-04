"""Write top5_1104 backlog lines (research/backlog.jsonl format) to backlog_proposals.jsonl; the lead appends them.
One line per setup grid (status failed: nothing met the Testing bar) plus one per variant that beat its parent at the
pre-declared bar (status rework, tag top5-tune). Educational only - not financial advice."""
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
R = pd.read_csv(OUT / "results.csv")
SRC = "BDI top-5 execution tune 2026-11-04 (fifteenth run) (research/bdi/top5_1104/NOTES.md)"
E = " Educational only - not financial advice."
ACCT = {"RW7-gapdn-bounce-early-short-FD": "testing1", "L3-gap-slope-fromopen-FD": "primary+testing1",
        "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "primary", "RW3-gapdn-rsi5pop-flowsell-short-FD": "primary",
        "MF2-open-rsimidhi-flowsell-FD": "primary"}
LIVE = {"G01": "stop 1.5 x the live stop, target price unchanged (same $ risk -> fewer shares).",
        "G02": "stop 2.0 x the live stop, target price unchanged (same $ risk).",
        "G05": "needs live partial exits (Alpaca bracket leg qty cannot be changed; scale-out caps apply).",
        "G11": "config only: window end.", "G12": "config only: window start.",
        "G13": "lab filter: skip when the stock is down > 2% from the open.",
        "G14": "lab filter: SPY-side (shorts skip SPY above its open, longs skip SPY below it).",
        "G11": "config only: window end.", "G12": "config only: window start.",
        "G15": "runner cap: first 5 signals per session.",
        "G17": "lab filter: skip when SPY is within +/-0.10% of its open at the signal.",
        "G16": "already live in Testing 1/2 since 10-30 (CF, live.max_stop_cost_r 0.15); Primary has no CF.",
        "G10": "lab filter: shorts skip SPY up > 0.5% from the open."}
GRIDT = {"default": "stop x1.5/x2.0 at same $, target x0.75/x1.5, half off at 0.5 x target + BE, clock exit, 60-min time stop, limit entry 0.1R, next-bar entry, SPY 0.5% veto, window first/second part, stock down > 2% skip, SPY-side filter, first 5 per session, CF stop-cost <= 0.15R, skip SPY flat (+/-0.10%) at the signal, skip price >= $150"}
BARS = json.loads((OUT / "summary.json").read_text())["bar_setup"]
COMMON = ("open two-year history, locked block 2024-11..2025-02 never loaded; TRAIN <= 2025-12, VALID 2026-01..03 + "
          "07..09-15; production + tod costs, x3 extended tier; entries = gates1021 live-shaped signals rebuilt; parity vs "
          "production R mean |d| <= 0.00007R; exits = top5_1028 5-minute simulator; stop-distance variants at the same $ risk; "
          "study N 90, bars 2.40 (setup) / 3.00 (study); Testing bar = rule 22 BAR90 on lineage N (4.28-4.72); 2-year frames rebuilt 11-04 (research/bdi/1104/DATA.md) + WF >= 54%.")
EXTRA = {"L3-gap-slope-fromopen-FD": " CF (G16) beats the parent at t 4.00 and is positive in TRAIN, VALID, up and down sessions (+0.054R, WF 0.65, vs random +0.075R) but its TRAIN+VALID t is 0.95 vs BAR90 4.50 and avg R without its best day is only +0.004R. CF is already live for the Testing 1 copy; Primary has none.",
         "MF2-open-rsimidhi-flowsell-FD": " Parent R here is per unit of the 0.5-unit stop (t1s05): -0.117R, twice the 0.25-ATR-unit figure of earlier reports.",
         "RW3-gapdn-rsi5pop-flowsell-short-FD": " 6 variants beat the parent; every one still loses in TRAIN and VALID and in SPY-up sessions."}


def fmt(r):
    return (f"n {int(r.n_tv)}, win {r.win_tv:.3f} (break-even {r.be_win:.3f}), exp {r.exp_tv:+.4f}R, TRAIN {r.exp_train:+.4f} / "
            f"VALID {r.exp_valid:+.4f} (t {r.t_valid}), t TRAIN+VALID {r.t_tv}, WF {r.wf_pos:.2f}, up {r.up:+.3f} / down {r.down:+.3f}, excess vs random {r.excess_vs_random:+.4f}R")


new = []
for s, d in R.groupby("setup", sort=False):
    p = d[d.is_parent].iloc[0]
    v = d[~d.is_parent]
    v = v.assign(t_improve=v.t_improve.fillna(-99))
    best = v.sort_values("t_improve", ascending=False).iloc[0]
    new.append({"id": f"top5-1104-{s}-exec",
                "title": f"{s}: execution variants ({GRIDT.get(s, GRIDT['default'])})",
                "category": "setup", "parent": None, "tags": [ACCT[s], "top5-tune", "bdi", "bdi-1104"],
                "hypothesis": "An execution change converts the live setup's win rate into more R per trade.",
                "status": "parked", "configs_tried": len(v),
                "notes": (f"top5_1104 (PLAN.md pre-declared). {len(v)} one-knob variants. {COMMON} Parent {fmt(p)}. "
                          f"{int((v.exp_tv > 0).sum())} of {len(v)} variants exp > 0; {int(v.beats_parent.sum())} beat the parent; "
                          f"best {best['var']} ({best['knob']}) {best['exp_tv']:+.4f}R, d {best['d_tv']:+.4f}R, t {best['t_improve']}; best TRAIN+VALID t {v.t_tv.max()} vs BAR90 {p.bar90}. "
                          f"Testing bar: 0. Parent avg R without its best day {p.ex_best_day:+.4f}." + EXTRA.get(s, "") + E)})
    for _, r in v[v.beats_parent.fillna(False).astype(bool)].iterrows():
        new.append({"id": f"top5-1104-{s}-{r['var']}-{r['knob']}",
                    "title": f"{s} with {r['knob']} ({r['var']}, top5_1104 PLAN.md section 3)",
                    "category": "setup", "parent": f"top5-1104-{s}-exec",
                    "tags": [ACCT[s], "top5-tune", "bdi", "bdi-1104", "beats-parent"],
                    "hypothesis": "This execution change raises the live parent's R per trade on TRAIN and on VALID.",
                    "status": "rework", "configs_tried": len(v), "live_support": LIVE.get(r["var"], ""),
                    "notes": (f"top5_1104 beats parent: d {r['d_tv']:+.4f}R (TRAIN {r['d_train']:+.4f}, VALID {r['d_valid']:+.4f}), "
                              f"day-clustered t {r['t_improve']} vs setup bar {BARS[s]}. Variant {fmt(r)}. Fails the Testing bar "
                              f"(variant still loses after costs in at least one period or in up/down sessions). " + COMMON + E)})
with open(OUT / "backlog_proposals.jsonl", "w") as fh:
    for n in new:
        fh.write(json.dumps({"added": "2026-11-04", "source": SRC, "module": None, "variant": None, **n}) + "\n")
print(len(new), "proposals written")
