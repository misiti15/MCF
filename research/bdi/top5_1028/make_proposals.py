"""Write top5_1028 backlog lines (research/backlog.jsonl format) to backlog_proposals.jsonl; the lead appends them.
One line per setup grid (status failed: nothing met the Testing bar) plus one per variant that beat its parent at the
pre-declared bar (status rework, tag top5-tune). Educational only - not financial advice."""
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
R = pd.read_csv(OUT / "results.csv")
SRC = "BDI top-5 execution tune 2026-10-28 (eleventh run) (research/bdi/top5_1028/NOTES.md)"
E = " Educational only - not financial advice."
ACCT = {"RW7-gapdn-bounce-early-short-FD": "testing1", "exhaustion_short-FD": "testing1+testing2",
        "MF3-open-flowsell-rsi5hi-FD": "testing1", "RW1-gapdn-bounce-flowsell-short-FD": "testing2",
        "RW4-ns3-adv150-short-FD": "testing1+testing2"}
LIVE = {"F01": "stop 2.0 x the live stop, target price unchanged (same $ risk -> fewer shares).",
        "F02": "stop 2.5 x the live stop, target price unchanged (same $ risk).",
        "F08": "module filter on context spy_fo > +0.5%.", "F09": "module filter on context spy_fo < -0.5%.",
        "F10": "module filter on stock fromOpen < -2%.", "F11": "config only: window end 11:30.",
        "F12": "config only: window start 11:30.", "F13": "needs a window gap (skip 10:30-11:29).",
        "F05": "clock exit 12:00 for trades opened before it.", "F06": "clock exit 14:00 for trades opened before it."}
GRIDT = {"default": "stop x2.0/x2.5 at same $, targets 0.5/2.0R, clock exits 12:00/14:00, limit entry 0.1R, SPY > +0.5% / < -0.5% skips, stock down > 2% skip, window end 11:30 / start 11:30, skip 10:30-11:29, 120-min time stop"}
BARS = json.loads((OUT / "summary.json").read_text())["bar_setup"]
COMMON = ("open two-year history, locked block 2024-11..2025-02 never loaded; TRAIN <= 2025-12, VALID 2026-01..03 + "
          "07..09-15; production + tod costs, x3 extended tier; entries = gates1021 live-shaped signals rebuilt (parity "
          "vs cached production R, mean |d| <= 0.00008R); exits = top5_1027 5-minute simulator; stop-distance variants at "
          "the same $ risk; R in units of the live stop; study N 70, bars 2.30 (setup) / 2.91 (study).")
EXTRA = {"RW4-ns3-adv150-short-FD": (" F10 (skip stock down > 2%) keeps 0 trades: every RW4 signal is a stock already down"
            " > 2% from open; counted.")}


def fmt(r):
    return (f"n {int(r.n_tv)}, win {r.win_tv:.3f} (break-even {r.be_win:.3f}), exp {r.exp_tv:+.4f}R, TRAIN {r.exp_train:+.4f} / "
            f"VALID {r.exp_valid:+.4f} (t {r.t_valid}), up {r.up:+.3f} / down {r.down:+.3f}, excess vs random {r.excess_vs_random:+.4f}R")


new = []
for s, d in R.groupby("setup", sort=False):
    p = d[d.is_parent].iloc[0]
    v = d[~d.is_parent]
    best = v.sort_values("t_improve", ascending=False).iloc[0]
    new.append({"id": f"top5-1028-{s}-exec",
                "title": f"{s}: execution variants ({GRIDT.get(s, GRIDT['default'])})",
                "category": "setup", "parent": None, "tags": [ACCT[s], "top5-tune", "bdi", "bdi-1028"],
                "hypothesis": "An execution change converts the live setup's win rate into more R per trade.",
                "status": "failed", "configs_tried": len(v),
                "notes": (f"top5_1028 (PLAN.md pre-declared). {len(v)} one-knob variants. {COMMON} Parent {fmt(p)}. "
                          f"{int((v.exp_tv > 0).sum())} of {len(v)} variants exp > 0; {int(v.beats_parent.sum())} beat the parent; "
                          f"best {best['var']} ({best['knob']}) {best['exp_tv']:+.4f}R, d {best['d_tv']:+.4f}R, t {best['t_improve']}. "
                          f"Testing bar: 0. Parent avg R without its best day {p.ex_best_day:+.4f}." + EXTRA.get(s, "") + E)})
    for _, r in v[v.beats_parent.fillna(False).astype(bool)].iterrows():
        new.append({"id": f"top5-1028-{s}-{r['var']}-{r['knob']}",
                    "title": f"{s} with {r['knob']} ({r['var']}, top5_1028 PLAN.md section 3)",
                    "category": "setup", "parent": f"top5-1028-{s}-exec",
                    "tags": [ACCT[s], "top5-tune", "bdi", "bdi-1028", "beats-parent"],
                    "hypothesis": "This execution change raises the live parent's R per trade on TRAIN and on VALID.",
                    "status": "rework", "configs_tried": len(v), "live_support": LIVE.get(r["var"], ""),
                    "notes": (f"top5_1028 beats parent: d {r['d_tv']:+.4f}R (TRAIN {r['d_train']:+.4f}, VALID {r['d_valid']:+.4f}), "
                              f"day-clustered t {r['t_improve']} vs setup bar {BARS[s]}. Variant {fmt(r)}. Fails the Testing bar "
                              f"(variant still loses after costs in at least one period or in up/down sessions). " + COMMON + E)})
with open(OUT / "backlog_proposals.jsonl", "w") as fh:
    for n in new:
        fh.write(json.dumps({"added": "2026-10-28", "source": SRC, "module": None, "variant": None, **n}) + "\n")
print(len(new), "proposals written")
