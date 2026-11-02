"""Write top5_1030 backlog lines (research/backlog.jsonl format) to backlog_proposals.jsonl; the lead appends them.
One line per setup grid (status failed: nothing met the Testing bar) plus one per variant that beat its parent at the
pre-declared bar (status rework, tag top5-tune). Educational only - not financial advice."""
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
R = pd.read_csv(OUT / "results.csv")
SRC = "BDI top-5 execution tune 2026-10-30 (twelfth run) (research/bdi/top5_1030/NOTES.md)"
E = " Educational only - not financial advice."
ACCT = {"L3-gap-slope-rsi5hi-FD": "primary", "MF5-flowsell-vwapup-rsi5hi-FD": "testing2",
        "NS3-failed-vwap-reclaim-short-FD": "testing2", "NS3V1-am-widestop-short": "testing2",
        "NS1-rsidip-rsi5pop-long-FD": "testing1"}
LIVE = {"G01": "stop 1.5 x the live stop, target price unchanged (same $ risk -> fewer shares).",
        "G02": "stop 2.0 x the live stop, target price unchanged (same $ risk).",
        "G11": "config only: window end 11:30."}
GRIDT = {"default": "stop x1.5/x2.0 at same $, target x0.75/x1.5, half off at 0.5 x target + BE, clock exit 12:00, 60-min time stop, limit entry 0.1R, next-bar entry, SPY 0.5% veto, window end/start 11:30 (NS3V1: start/end 10:30), stock > 2% from open skip, one entry per symbol-day, first 5 per session"}
BARS = json.loads((OUT / "summary.json").read_text())["bar_setup"]
COMMON = ("open two-year history, locked block 2024-11..2025-02 never loaded; TRAIN <= 2025-12, VALID 2026-01..03 + "
          "07..09-15; production + tod costs, x3 extended tier; entries = gates1021 live-shaped signals rebuilt (parity "
          "vs cached production R, mean |d| <= 0.00004R); exits = top5_1028 5-minute simulator; stop-distance variants at "
          "the same $ risk; R in units of the live stop; study N 75, bars 2.33 (setup) / 2.94 (study); Testing bar = rule 22 BAR90 on lineage N (4.41-4.72) + WF >= 54%.")
EXTRA = {"NS3-failed-vwap-reclaim-short-FD": " G13 (skip stock down > 2%) keeps 0 trades (every NS3 signal is already down > 2% from open); counted.",
         "NS3V1-am-widestop-short": " G13 keeps 0 trades (as NS3-FD); counted. The parent itself is the best row (+0.069R, t 2.39 vs BAR90 4.41).",
         "MF5-flowsell-vwapup-rsi5hi-FD": " G14 (one per symbol-day) is identical to the parent (no refire); counted.",
         "NS1-rsidip-rsi5pop-long-FD": " G13 is identical to the parent (no NS1 signal is down > 2% from open); counted."}


def fmt(r):
    return (f"n {int(r.n_tv)}, win {r.win_tv:.3f} (break-even {r.be_win:.3f}), exp {r.exp_tv:+.4f}R, TRAIN {r.exp_train:+.4f} / "
            f"VALID {r.exp_valid:+.4f} (t {r.t_valid}), t TRAIN+VALID {r.t_tv}, WF {r.wf_pos:.2f}, up {r.up:+.3f} / down {r.down:+.3f}, excess vs random {r.excess_vs_random:+.4f}R")


new = []
for s, d in R.groupby("setup", sort=False):
    p = d[d.is_parent].iloc[0]
    v = d[~d.is_parent]
    v = v.assign(t_improve=v.t_improve.fillna(-99))
    best = v.sort_values("t_improve", ascending=False).iloc[0]
    new.append({"id": f"top5-1030-{s}-exec",
                "title": f"{s}: execution variants ({GRIDT.get(s, GRIDT['default'])})",
                "category": "setup", "parent": None, "tags": [ACCT[s], "top5-tune", "bdi", "bdi-1030"],
                "hypothesis": "An execution change converts the live setup's win rate into more R per trade.",
                "status": "failed", "configs_tried": len(v),
                "notes": (f"top5_1030 (PLAN.md pre-declared). {len(v)} one-knob variants. {COMMON} Parent {fmt(p)}. "
                          f"{int((v.exp_tv > 0).sum())} of {len(v)} variants exp > 0; {int(v.beats_parent.sum())} beat the parent; "
                          f"best {best['var']} ({best['knob']}) {best['exp_tv']:+.4f}R, d {best['d_tv']:+.4f}R, t {best['t_improve']}; best TRAIN+VALID t {v.t_tv.max()} vs BAR90 {p.bar90}. "
                          f"Testing bar: 0. Parent avg R without its best day {p.ex_best_day:+.4f}." + EXTRA.get(s, "") + E)})
    for _, r in v[v.beats_parent.fillna(False).astype(bool)].iterrows():
        new.append({"id": f"top5-1030-{s}-{r['var']}-{r['knob']}",
                    "title": f"{s} with {r['knob']} ({r['var']}, top5_1030 PLAN.md section 3)",
                    "category": "setup", "parent": f"top5-1030-{s}-exec",
                    "tags": [ACCT[s], "top5-tune", "bdi", "bdi-1030", "beats-parent"],
                    "hypothesis": "This execution change raises the live parent's R per trade on TRAIN and on VALID.",
                    "status": "rework", "configs_tried": len(v), "live_support": LIVE.get(r["var"], ""),
                    "notes": (f"top5_1030 beats parent: d {r['d_tv']:+.4f}R (TRAIN {r['d_train']:+.4f}, VALID {r['d_valid']:+.4f}), "
                              f"day-clustered t {r['t_improve']} vs setup bar {BARS[s]}. Variant {fmt(r)}. Fails the Testing bar "
                              f"(variant still loses after costs in at least one period or in up/down sessions). " + COMMON + E)})
with open(OUT / "backlog_proposals.jsonl", "w") as fh:
    for n in new:
        fh.write(json.dumps({"added": "2026-10-30", "source": SRC, "module": None, "variant": None, **n}) + "\n")
print(len(new), "proposals written")
