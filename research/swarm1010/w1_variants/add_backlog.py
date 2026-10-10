"""Append the sw-w1-* backlog entries (candidates and failures) from results.csv / summary.csv / verify.json. Run once
(skips ids already present). Educational only - not financial advice."""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BL = ROOT / "research" / "backlog.jsonl"
SRC = "Swarm 2026-10-10 W1 indicator-variant sweep (research/swarm1010/w1_variants/NOTES.md, results.csv)"
TAIL = (" Open history 2024-10..2026-10-07 minus the rule-19 locked block (426 sessions), full day 09:50-15:00, first "
        "bar per symbol-day, production costs. Not scored on the locked block. Educational only - not financial advice.")


def main():
    have = {json.loads(l)["id"] for l in BL.read_text().splitlines() if l.strip()}
    s = pd.read_csv(HERE / "summary.csv")
    x = pd.read_csv(HERE / "results.csv")
    v = json.loads((HERE / "verify.json").read_text())
    tot = len(x)
    E = []
    C = [("sw-w1-ns3-sma100-vol2-short", "W1-NS3-vwapreclaim-sma100-vol2-short", "NS3-failed-vwap-reclaim-short",
          "bdi-ns3-failed-vwap-reclaim-short", "NS3 failed VWAP reclaim with SMA100 (for SMA50) + volumeRatio >= 2, full day",
          "n 212 (0.50/day) +0.139R t 2.53 (t_req 4.22); up +0.133 / flat +0.109 / down +0.174; WF 0.857; plateau +0.065; "
          "ex-best-day +0.125; busiest day 3.8%. Controls: SMA term dropped on the same afternoon bars -0.023R; SMA100 side "
          "flipped -0.052R. Overlaps W1-ST6 on 25% of symbol-days."),
         ("sw-w1-st6-sma100above-short", "W1-ST6-volspikeup-sma100above-short", "ST6-volspikeup-short-mid-t1s1",
          "bdi-st-st6-volspikeup-short-mid-t1s1", "ST6 volume-spike short + close above SMA100, full day",
          "n 237 (0.56/day) +0.171R t 3.23 (t_req 4.84); up +0.150 / down +0.175; WF 0.75; plateau +0.118; ex-best-day "
          "+0.150; busiest day 7.6%. Controls: same afternoon bars without the SMA100 side +0.003R; flipped (below SMA100) "
          "-0.135R."),
         ("sw-w1-st1-sma100below-long", "W1-ST1-ordn-sma100below-long", "ST1-ordn-long-pm-t05s1",
          "bdi-st-st1-ordn-long-pm-t05s1", "ST1 OR-low break long + close below SMA100, full day",
          "scan n 567 +0.075R t 2.29 (module list 561, +0.073R, t 2.20; t_req 4.84); up +0.111 / down +0.094; WF 0.688; "
          "plateau +0.028; ex-best-day +0.070; busiest 4.4%. Control: same afternoon bars without the SMA100 side +0.061R "
          "t 1.55 (most of the gain is the afternoon restriction SMA100 implies)."),
         ("sw-w1-st8-sma100below-long-t05s1", "W1-ST8-volspikedn-sma100below-long-t05s1", "ST8-volspikedn-long-pm-t1s1",
          "bdi-st-st8-volspikedn-long-pm-t1s1", "ST8 volume-spike long + close below SMA100, exit t05s1, full day",
          "n 353 (0.83/day) +0.078R t 2.06 (t_req 4.84); up +0.056 / down +0.004 (weakest: down ~0); WF 0.923; plateau "
          "+0.043; ex-best-day +0.060; busiest 5.4%. Control without the SMA100 side +0.057R t 1.59.")]
    for eid, mod, fam, parent, title, note in C:
        n_f = int((x.family == fam).sum())
        ver = v[mod]
        E.append({"id": eid, "title": title, "added": "2026-10-10", "source": SRC, "category": "setup",
                  "hypothesis": "A one-step indicator variant of the family (SMA100 trend layer) is positive in up AND down sessions.",
                  "module": None, "variant": None, "status": "testing", "parent": parent,
                  "lab_module": f"research/swarm1010/w1_variants/modules/{mod}.py", "configs_tried": n_f,
                  "notes": ("LIVE-PROBATION candidate (meets the RULES.md bar), not keep: t below the try-count bar. " + note
                            + f" Configurations of this family in W1: {n_f} (whole study {tot}). Needs a live column "
                            "sma100_dist_pct (SMA100 on prior 60 + today's 5-min bars; exists from ~12:50 ET) - the module "
                            "is fail-safe without it. Verify: offline scan "
                            f"{ver['scan_n']} / module {ver['module_n']}; live-shaped sample agree {ver['live_sample']['agree_share']:.0%} "
                            f"of {ver['live_sample']['symbol_days']} symbol-days. Staged: research/swarm1010/w1_variants/"
                            "account_testing_w1.yaml." + TAIL)})
    for grp, eid, title in (("lab", "sw-w1-lab-variants-fail", "W1 variants of the lab/heat families (heat, exhaustion, MF, RW, NS, ST, RW8)"),
                            ("reddit", "sw-w1-reddit-variants-fail", "W1 variants of the 20 Reddit rules x long/short"),
                            ("trigger", "sw-w1-trigger-variants-fail", "W1 variants of the 18 stack1009 trigger families x up/dn x long/short")):
        g = s[s.group == grp]
        if grp == "lab":
            g = g[g.lineage != "L3"]
        fails = g[g.probation_passers == 0]
        E.append({"id": eid, "title": title, "added": "2026-10-10", "source": SRC, "category": "setup",
                  "hypothesis": "Changing one indicator parameter (RSI 5/9/14/21 and levels, EMA 8/9/13 x 20/21, SMA 20/50/100, VWAP SD band 1-2.5, volume ratio 1.25-3, fromOpen 1-4%, gap, exits incl. 1.5R / 0.75R) finds a regime-robust version.",
                  "module": None, "variant": None, "status": "failed", "configs_tried": int(g.configs.sum()),
                  "notes": (f"{len(g)} base lists, {int(g.configs.sum())} configurations; {len(fails)} lists with no probation "
                            f"passer. Variants with n >= 150 positive in up AND down sessions: {int(g.both_pos_n150.sum())} of "
                            f"{int(g.variants_n150.sum())}. Bases: longs win in up sessions and lose in down sessions, shorts the "
                            "reverse; no RSI length, EMA pair, SMA length, VWAP band, volume or exit variant changes that, "
                            "except the SMA100 layer on four ST/NS stacks (see sw-w1-* testing entries)." + TAIL)})
    l3 = s[s.lineage == "L3"]
    E.append({"id": "sw-w1-l3-variants-fail", "title": "W1 variants of L3 gap/slope shorts (min_adv 0)", "added": "2026-10-10",
              "source": SRC, "category": "setup", "hypothesis": "Threshold / exit / volume variants rescue L3.", "module": None,
              "variant": None, "status": "failed", "parent": "L3-gap-slope-fromopen", "configs_tried": int(l3.configs.sum()),
              "notes": (f"{int(l3.configs.sum())} configurations over the 3 L3 bases (all adv, gap <= -1% rows); best robust "
                        f"{l3.best_robust.max():.2f}; no variant positive in both regimes with n >= 150. Bases -0.04 / -0.10 / "
                        "-0.04R full day." + TAIL)})
    E.append({"id": "sw-w1-asymmetry-finding", "title": "Finding: indicator variants do not change the up/down asymmetry",
              "added": "2026-10-10", "source": SRC, "category": "analysis", "module": None, "variant": None, "status": "idea",
              "hypothesis": "Regime dependence is a property of the trade direction, not of indicator settings.",
              "notes": ("Across 145 base lists and 4,663 configurations, 54 of 3,993 variants with n >= 150 are positive in both "
                        "regimes (1.4%), and only 4 pass the pre-declared 'asymmetry changed' reading (both regimes, min t >= 1, "
                        "neighbours both-positive): ST1 / ST6 (x2) with the SMA100 layer, and R14-ict-fvg-short p 0.2 + VWAP "
                        "+1 SD (a 2025Q2 cluster, WF 0.375). The in-play layer |fromOpen| >= 1-4% raises exp by +0.01..+0.03R and "
                        "narrows the up/down spread but never makes both positive; t05s1 narrows the spread mechanically. "
                        "Next: direction-neutral structures (pairs / beta-hedged), as regime1009 suggested." + TAIL)})
    E.append({"id": "sw-w1-live-sma100-column", "title": "Live frame: add sma100_dist_pct (SMA100 on prior 60 + today's 5-min bars)",
              "added": "2026-10-10", "source": SRC, "category": "setup", "module": None, "variant": None, "status": "idea",
              "hypothesis": "Needed by the four sw-w1 candidates; one line in mcf.research.setup_lab.extra_features.",
              "notes": ("x['sma100_dist_pct'] = (c / c.rolling(100).mean() - 1) * 100 on hist = PRIOR5_BARS (60) prior bars + "
                        "today's bars (NaN until today's 40th bar, ~12:50 ET; that NaN is part of the tested rule). Also note: the "
                        "variants needing RSI 9/21 or EMA 8/13/20 or exits t15s1 / t1s075 would need columns / GEOMS entries the "
                        "live code lacks; none of them passed, so nothing else is requested." + TAIL)})
    new = [e for e in E if e["id"] not in have]
    with BL.open("a") as f:
        for e in new:
            f.write(json.dumps(e) + "\n")
    print("appended", [e["id"] for e in new])


if __name__ == "__main__":
    main()
