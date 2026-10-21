"""gates1021: backlog_proposals.jsonl (research/backlog.jsonl format; NOT appended there). Educational only - not
financial advice."""
from __future__ import annotations

import json

import pandas as pd

from common import HERE

SRC = "BDI gates1021 2026-10-21 (research/bdi/gates1021/NOTES.md)"
COMMON = ("open two-year history, locked block 2024-11..2025-02 never loaded; TRAIN <= 2025-12, VALID 2026-01..10-07; "
          "production costs + tod entry costs, extended tier x3; live-shaped signals (account refire chain); study N 718, "
          "bar 3.63; no holdout scored.")


def main():
    cnt = json.load(open(HERE / "counts.json"))
    rb = pd.read_csv(HERE / "results_B.csv")
    rob = pd.read_csv(HERE / "robust.csv").set_index("setup")
    ra = pd.read_csv(HERE / "results_A.csv")
    out = []
    for _, x in rb[rb["B2_pick"]].iterrows():
        fin = x["verdict"] == "finalist"
        rr = rob.loc[x["setup"]]
        mod = f"research/bdi/gates1021/modules/{x['setup']}-g1.py" if (fin or x["setup"].startswith("NS3")) else None
        out.append({
            "added": "2026-10-21", "source": SRC, "category": "filter", "variant": None,
            "id": f"gates1021-{x['setup']}-g1", "title": f"{x['setup']} + check-gate: skip in state '{x['gate']}'",
            "module": None, "parent": x["setup"], "status": "finalist" if fin else "rework",
            "configs_tried": int(cnt["N_total"]),
            "tags": ["gates1021", "direction-gate", "bdi", x["accounts"].replace(",", "+"), "beats-parent"],
            "hypothesis": "Blocking entries only in the setup's historically worst market state (known at entry) raises avg R "
                          "on TRAIN and VALID while keeping >= 80% of the parent's trades.",
            "live_support": (f"module {mod}" if mod else "no module written (near-miss)") +
                            ("; needs a prior-session SPY close-to-close context column (spy_prev) - live code" if "prior day" in x["gate"]
                             else "; LabStrategy context columns only"),
            "notes": (f"{'FINALIST' if fin else 'near-miss (pooled t below bar)'}: blocked {x['train_blocked_pct']:.1f}% / "
                      f"{x['valid_blocked_pct']:.1f}% of trades (winners blocked {x['train_winners_blocked_pct']:.1f}% / "
                      f"{x['valid_winners_blocked_pct']:.1f}%); avg R train {x['train_parent_exp']:+.4f} -> {x['train_gated_exp']:+.4f}, "
                      f"valid {x['valid_parent_exp']:+.4f} -> {x['valid_gated_exp']:+.4f}; gate delta t train {x['train_delta_t']:.2f} / "
                      f"valid {x['valid_delta_t']:.2f} / pooled {x['all_delta_t']:.2f} (bar 3.63); choppy days blocked "
                      f"{x['choppy_blocked_pct']:.1f}%, delta {x['choppy_delta']:+.4f}; quarters positive {rr['quarters_positive']}; "
                      f"random same-minute control delta {rr['ctrl_delta_all']:+.4f} vs gate {rr['delta_all']:+.4f} "
                      f"(market-beta share {rr['beta_share']}); the gated setup is still negative after costs on valid. " + COMMON)})
    a = ra[ra["variant"] != "A0 parent-live (refire cd1 + lot cap 3)"]
    out.append({"added": "2026-10-21", "source": SRC, "category": "filter", "variant": None,
                "id": "gates1021-partA-tweaks", "title": "NS3-FD / L3-fromopen-FD one-layer tweaks: no re-entry after stop, one lot "
                "per symbol, first signal only, SPY/QQQ-up skips, peer-up skip, time-of-day cuts, open-lot caps, -2R daily stop",
                "module": None, "parent": "NS3-failed-vwap-reclaim-short-FD / L3-gap-slope-fromopen-FD", "status": "failed",
                "configs_tried": 32, "tags": ["gates1021", "bdi", "primary"],
                "hypothesis": "A small runner/context layer stops the false triggers of 2026-10-21.",
                "notes": "0/30 tweaks pass (participation >= 80% AND better avg R on train and valid AND pooled t >= 3.63). Best: "
                         "NS3-FD peer-median-up >= 1% skip (needs live code) kept 95%/94%, avg +0.009/-0.020 vs -0.005/-0.021, pooled t 3.01; "
                         "L3-FD no entries before 10:30 kept 93%/93%, avg -0.022/-0.023 vs -0.032/-0.029, pooled t 2.64. "
                         "-2R daily stop, lot caps and first-signal-only all LOWER avg R on history. " + COMMON})
    out.append({"added": "2026-10-21", "source": SRC, "category": "filter", "variant": None, "status": "idea",
                "id": "gates1021-L3-prior-day-up", "title": "L3-gap-slope-fromopen-FD: skip after a >= +0.5% SPY prior session (not tested)",
                "module": None, "parent": "L3-gap-slope-fromopen-FD", "configs_tried": 0, "tags": ["gates1021", "idea"],
                "hypothesis": "L3 shorts after an up prior session lose (descriptive A0 split: -0.24R train t -3.9 / -0.19R valid t -3.2, ~20% of trades).",
                "notes": "Seen in the descriptive state split only (states_A.csv); prior-day-alone was not a pre-declared gate, so it is untested. "
                         "Needs its own pre-declared test and live code for spy_prev."})
    with open(HERE / "backlog_proposals.jsonl", "w") as f:
        for e in out:
            f.write(json.dumps(e) + "\n")
    print(len(out), "entries")


if __name__ == "__main__":
    main()
