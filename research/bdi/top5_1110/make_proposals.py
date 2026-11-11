"""Write top5_1110 backlog lines (research/backlog.jsonl format) to backlog_proposals.jsonl; the lead appends them.
One line per setup grid (status failed: nothing met the Testing bar) plus one per variant that beat its parent at the
pre-declared bar (status rework, tag top5-tune). Educational only - not financial advice."""
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
R = pd.read_csv(OUT / "results.csv")
SRC = "BDI top-5 execution tune 2026-11-10 (nineteenth run) (research/bdi/top5_1110/NOTES.md)"
E = " Educational only - not financial advice."
ACCT = {"RW7-gapdn-bounce-early-short-FD": "testing1", "MF2-open-rsimidhi-flowsell-FD": "primary",
        "RW3-gapdn-rsi5pop-flowsell-short-FD": "primary", "L3-gap-slope-fromopen-FD": "primary",
        "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "primary"}
LIVE = {"G01": "stop 1.5 x the live stop, target price unchanged (same $ risk -> fewer shares).",
        "G02": "stop 0.75 x the live stop, target price unchanged (same $ risk -> more shares).",
        "G05": "needs live partial exits (Alpaca bracket leg qty cannot be changed; scale-out caps apply).",
        "G06": "runner time stop: 30 minutes if best < +0.25R.", "G07": "runner time stop: 60 minutes if best < +0.25R.",
        "G08": "config only: clock exit 13:00 (trades opened before 13:00 flatten at 13:00).", "G11": "config only: window end 11:00.", "G12": "config only: window start 11:00.",
        "G13": "CF (live.max_stop_cost_r 0.15) is live in Testing 1/2 since 10-30 (so RW7-FD already runs it); Primary does not run CF.",
        "G14": "lab filter: skip price < $20 (overlaps CF).",
        "G15": "runner cap: first 5 signals per session.",
        "G16": "lab filter: SPY-side (shorts skip SPY above its open, longs skip SPY below it).",
        "G17": "needs the compass in the runner (today display only): skip entries against a W60-confirmed compass.",
        "G18": "needs the compass in the runner: half size against a W60-confirmed compass.",
        "G19": "config only: ADV floor x1.2 (L3-fromopen: ADV >= 95M).",
        "G10": "entry timing: next bar's close."}
GRIDT = {"default": "stop x1.5/x0.75 at same $, target x0.75/x1.5, half off at 0.5 x target + BE, 30/60-min time stop, clock exit 13:00, limit entry 0.1R, next-bar entry, entries before / from 11:00, CF stop-cost <= 0.15R, skip price < $20, first 5 per session, SPY-side filter, skip / half size against a W60-confirmed compass, ADV floor x1.2"}
BARS = json.loads((OUT / "summary.json").read_text())["bar_setup"]
COMMON = ("open two-year history, locked block 2024-11..2025-02 never loaded; TRAIN <= 2025-12, VALID 2026-01..03 + "
          "07..09-15; production + tod costs, x3 extended tier; entries = gates1021 live-shaped signals rebuilt; parity vs "
          "production R (see NOTES.md); exits = top5_1028 5-minute simulator; stop-distance variants at the same $ risk; "
          "study N 95, bars 2.43 (setup) / 3.02 (study); Testing bar = rule 22 BAR90 on lineage N (4.28-4.72) + WF >= 54%; 2-year frames per research/bdi/1104/DATA.md.")
EXTRA = {"L3-gap-slope-fromopen-FD": (" Closest call again (as top5_1104): G14 skip price < $20 / G13 CF / G19 ADV >= 95M are positive in"
    " TRAIN and VALID, in up and down sessions, without the best day and vs random, and G14 / G13 pass the no-strangle screen (keep 72% / 81% of trades,"
    " 98% / 100% of top-decile winners; G19 keeps 73% / 89.7%, just under), but t TRAIN+VALID 0.90-1.07 vs BAR90 4.50 and VALID only +0.004..+0.015R. Not a Testing candidate.")}


def fmt(r):
    return (f"n {int(r.n_tv)}, win {r.win_tv:.3f} (break-even {r.be_win:.3f}), exp {r.exp_tv:+.4f}R, TRAIN {r.exp_train:+.4f} / "
            f"VALID {r.exp_valid:+.4f} (t {r.t_valid}), t TRAIN+VALID {r.t_tv}, WF {r.wf_pos:.2f}, up {r.up:+.3f} / down {r.down:+.3f}, excess vs random {r.excess_vs_random:+.4f}R")


new = []
for s, d in R.groupby("setup", sort=False):
    p = d[d.is_parent].iloc[0]
    v = d[~d.is_parent]
    v = v.assign(t_improve=v.t_improve.fillna(-99))
    best = v.sort_values("t_improve", ascending=False).iloc[0]
    new.append({"id": f"top5-1110-{s}-exec",
                "title": f"{s}: execution variants ({GRIDT.get(s, GRIDT['default'])})",
                "category": "setup", "parent": None, "tags": [ACCT[s], "top5-tune", "bdi", "bdi-1110"],
                "hypothesis": "An execution change converts the live setup's win rate into more R per trade.",
                "status": "parked", "configs_tried": len(v),
                "notes": (f"top5_1110 (PLAN.md pre-declared). {len(v)} one-knob variants. {COMMON} Parent {fmt(p)}. "
                          f"{int((v.exp_tv > 0).sum())} of {len(v)} variants exp > 0; {int(v.beats_parent.sum())} beat the parent; "
                          f"best {best['var']} ({best['knob']}) {best['exp_tv']:+.4f}R, d {best['d_tv']:+.4f}R, t {best['t_improve']}; best TRAIN+VALID t {v.t_tv.max()} vs BAR90 {p.bar90}. "
                          f"Testing bar: 0. Parent avg R without its best day {p.ex_best_day:+.4f}." + EXTRA.get(s, "") + E)})
    for _, r in v[v.beats_parent.fillna(False).astype(bool)].iterrows():
        new.append({"id": f"top5-1110-{s}-{r['var']}-{r['knob']}",
                    "title": f"{s} with {r['knob']} ({r['var']}, top5_1110 PLAN.md section 3)",
                    "category": "setup", "parent": f"top5-1110-{s}-exec",
                    "tags": [ACCT[s], "top5-tune", "bdi", "bdi-1110", "beats-parent"],
                    "hypothesis": "This execution change raises the live parent's R per trade on TRAIN and on VALID.",
                    "status": "rework", "configs_tried": len(v), "live_support": LIVE.get(r["var"], ""),
                    "notes": (f"top5_1110 beats parent: d {r['d_tv']:+.4f}R (TRAIN {r['d_train']:+.4f}, VALID {r['d_valid']:+.4f}), "
                              f"day-clustered t {r['t_improve']} vs setup bar {BARS[s]}. Variant {fmt(r)}. Fails the Testing bar "
                              f"(variant still loses after costs in at least one period or in up/down sessions). " + COMMON + E)})
with open(OUT / "backlog_proposals.jsonl", "w") as fh:
    for n in new:
        fh.write(json.dumps({"added": "2026-11-10", "source": SRC, "module": None, "variant": None, **n}) + "\n")
print(len(new), "proposals written")
