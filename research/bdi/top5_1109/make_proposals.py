"""Write top5_1109 backlog lines (research/backlog.jsonl format) to backlog_proposals.jsonl; the lead appends them.
One line per setup grid (status failed: nothing met the Testing bar) plus one per variant that beat its parent at the
pre-declared bar (status rework, tag top5-tune). Educational only - not financial advice."""
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
R = pd.read_csv(OUT / "results.csv")
SRC = "BDI top-5 execution tune 2026-11-09 (eighteenth run) (research/bdi/top5_1109/NOTES.md)"
E = " Educational only - not financial advice."
ACCT = {"RW3S-gapdn-flowsell-short-FD": "testing2", "exhaustion_short-FD": "testing1", "RW1-gapdn-bounce-flowsell-short-FD": "testing2",
        "NM-AR-AM-gapdown-capitulation-long": "testing2", "L3-gap-slope-lowdist-FD": "testing1"}
LIVE = {"G01": "stop 1.5 x the live stop, target price unchanged (same $ risk -> fewer shares).",
        "G02": "stop 0.75 x the live stop, target price unchanged (same $ risk -> more shares).",
        "G05": "needs live partial exits (Alpaca bracket leg qty cannot be changed; scale-out caps apply).",
        "G06": "runner time stop: 30 minutes if best < +0.25R.", "G07": "runner time stop: 60 minutes if best < +0.25R.",
        "G08": "config only: clock exit.", "G11": "config only: window end.", "G12": "config only: window start.",
        "G13": "already live in Testing 1/2 since 10-30 (CF, live.max_stop_cost_r 0.15) - the lab parent is pre-CF.",
        "G14": "lab filter: skip price < $20 (overlaps CF).",
        "G15": "runner cap: first 5 signals per session.",
        "G16": "lab filter: SPY-side (shorts skip SPY above its open, longs skip SPY below it).",
        "G17": "needs the compass in the runner (today display only): skip entries against a W60-confirmed compass.",
        "G18": "needs the compass in the runner: half size against a W60-confirmed compass.",
        "G19": "config only: ADV floor x1.2 (L3-lowdist: ADV >= 95M).",
        "G10": "entry timing: next bar's close."}
GRIDT = {"default": "stop x1.5/x0.75 at same $, target x0.75/x1.5, half off at 0.5 x target + BE, 30/60-min time stop, clock exit, limit entry 0.1R, next-bar entry, window first/second part, CF stop-cost <= 0.15R, skip price < $20, first 5 per session, SPY-side filter, skip / half size against a W60-confirmed compass, ADV floor x1.2"}
BARS = json.loads((OUT / "summary.json").read_text())["bar_setup"]
COMMON = ("open two-year history, locked block 2024-11..2025-02 never loaded; TRAIN <= 2025-12, VALID 2026-01..03 + "
          "07..09-15; production + tod costs, x3 extended tier; entries = gates1021 live-shaped signals rebuilt; parity vs "
          "production R (see NOTES.md); exits = top5_1028 5-minute simulator; stop-distance variants at the same $ risk; "
          "study N 95, bars 2.43 (setup) / 3.02 (study); Testing bar = rule 22 BAR90 on lineage N (4.16-4.70) + WF >= 54%; 2-year frames per research/bdi/1104/DATA.md.")
EXTRA = {"NM-AR-AM-gapdown-capitulation-long": (" Parent is POSITIVE on two years (both splits, up and down sessions, WF 65%, +0.173R vs random)"
    " but carries a one-day concentration (best day 54% of total R; April 2025) and t 2.23 is far below BAR90 4.16; live 14 trades -0.713R"
    " (12 stops, 11-05 / 11-06 / 11-09). By W60 compass at signal (in-sample read, not a tested knob): DOWN-confirmed TRAIN +0.507 /"
    " VALID +0.337R, UP-confirmed -0.207 / +0.086R - a capitulation long belongs to down tape, so 'skip against the compass' (G17) is the wrong"
    " remedy for it (d -0.236R).")}


def fmt(r):
    return (f"n {int(r.n_tv)}, win {r.win_tv:.3f} (break-even {r.be_win:.3f}), exp {r.exp_tv:+.4f}R, TRAIN {r.exp_train:+.4f} / "
            f"VALID {r.exp_valid:+.4f} (t {r.t_valid}), t TRAIN+VALID {r.t_tv}, WF {r.wf_pos:.2f}, up {r.up:+.3f} / down {r.down:+.3f}, excess vs random {r.excess_vs_random:+.4f}R")


new = []
for s, d in R.groupby("setup", sort=False):
    p = d[d.is_parent].iloc[0]
    v = d[~d.is_parent]
    v = v.assign(t_improve=v.t_improve.fillna(-99))
    best = v.sort_values("t_improve", ascending=False).iloc[0]
    new.append({"id": f"top5-1109-{s}-exec",
                "title": f"{s}: execution variants ({GRIDT.get(s, GRIDT['default'])})",
                "category": "setup", "parent": None, "tags": [ACCT[s], "top5-tune", "bdi", "bdi-1109"],
                "hypothesis": "An execution change converts the live setup's win rate into more R per trade.",
                "status": "parked", "configs_tried": len(v),
                "notes": (f"top5_1109 (PLAN.md pre-declared). {len(v)} one-knob variants. {COMMON} Parent {fmt(p)}. "
                          f"{int((v.exp_tv > 0).sum())} of {len(v)} variants exp > 0; {int(v.beats_parent.sum())} beat the parent; "
                          f"best {best['var']} ({best['knob']}) {best['exp_tv']:+.4f}R, d {best['d_tv']:+.4f}R, t {best['t_improve']}; best TRAIN+VALID t {v.t_tv.max()} vs BAR90 {p.bar90}. "
                          f"Testing bar: 0. Parent avg R without its best day {p.ex_best_day:+.4f}." + EXTRA.get(s, "") + E)})
    for _, r in v[v.beats_parent.fillna(False).astype(bool)].iterrows():
        new.append({"id": f"top5-1109-{s}-{r['var']}-{r['knob']}",
                    "title": f"{s} with {r['knob']} ({r['var']}, top5_1109 PLAN.md section 3)",
                    "category": "setup", "parent": f"top5-1109-{s}-exec",
                    "tags": [ACCT[s], "top5-tune", "bdi", "bdi-1109", "beats-parent"],
                    "hypothesis": "This execution change raises the live parent's R per trade on TRAIN and on VALID.",
                    "status": "rework", "configs_tried": len(v), "live_support": LIVE.get(r["var"], ""),
                    "notes": (f"top5_1109 beats parent: d {r['d_tv']:+.4f}R (TRAIN {r['d_train']:+.4f}, VALID {r['d_valid']:+.4f}), "
                              f"day-clustered t {r['t_improve']} vs setup bar {BARS[s]}. Variant {fmt(r)}. Fails the Testing bar "
                              f"(variant still loses after costs in at least one period or in up/down sessions). " + COMMON + E)})
with open(OUT / "backlog_proposals.jsonl", "w") as fh:
    for n in new:
        fh.write(json.dumps({"added": "2026-11-09", "source": SRC, "module": None, "variant": None, **n}) + "\n")
print(len(new), "proposals written")
