"""Step 4: write NOTES.md section 2 (results) from results.csv, validation.json and anecdote.csv. Section 1 (the
pre-declaration) is kept byte for byte.   python research/bdi/trendguard/report.py
Educational only - not financial advice.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RETIRE = ["intraday_momentum", "orb20_a", "exhaustion_short", "MF1-945-flowsell-vwapup", "MF2-open-rsimidhi-flowsell",
          "MF4-h40-open-flowsell", "NS5-sma50-flush-oversold-long", "RW2 bdi-rw-exhaustion-noon-adv150", "RW8 bdi-rw-sma50up-spikefade"]


def fam(g: str) -> str:
    if g == "none":
        return "none"
    if g.startswith("C"):
        return "C"
    if g.startswith("L"):
        return "L"
    return "pair" if "+" in g else "single"


def f(v, d=3):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "-"
    return f"{v:+.{d}f}" if isinstance(v, float) else str(v)


def row(r) -> str:
    return (f"| {r.setup} | {r.guard} | {r.exit} | {int(r.n)} | {r.per_day} | {f(r.exp_r)} | {r.t} | {r.t_required} | "
            f"{f(r.up_exp)} ({int(r.up_n)}) | {f(r.flat_exp)} | {f(r.down_exp)} ({int(r.down_n)}) | {r.wf_share_pos} | {f(r.ex_best_day)} | "
            f"{r.dsr} | **{r.verdict}** | {r.failed_gates} |")


HDR = ["| setup | guard | exit | n | /day | exp R | t | t req | up exp (n) | flat exp | down exp (n) | WF +share | ex-best-day | DSR | verdict | failed gates |",
       "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]


def main():
    res = pd.read_csv(HERE / "results.csv")
    res = res[res["n"] > 0].copy() if "n" in res else res
    allr = pd.read_csv(HERE / "results.csv")
    val = json.loads((HERE / "validation.json").read_text())
    an = pd.read_csv(HERE / "anecdote.csv")
    res["family"] = res["guard"].map(fam)
    res["group"] = np.where(res["setup"].isin(RETIRE), "retire", "rework")
    keep = res[res["verdict"] == "keep"]
    n_cfg = len(allr)
    new = n_cfg - allr["setup"].nunique()
    both = res[(res.up_exp > 0) & (res.down_exp > 0) & (res.up_n >= 30) & (res.down_n >= 30)]
    L = ["", "## 2. Results (written after scoring; section 1 unchanged)", "",
         "*Educational only - not financial advice. Lab results on 426 open sessions of the 2-year history; no locked block "
         "was loaded or scored; nothing here is a live result.*", "",
         f"**Configurations scored: {n_cfg}** ({allr['setup'].nunique()} setups x 225; {new} new, the rest are the rescore "
         f"baselines re-simulated). At p = 0.05 about {round(new * 0.05)} would look significant by chance.", "",
         f"**Keep: {keep['setup'].nunique()} setups ({len(keep)} configurations).** "
         + ("No guard, confirmation delay or exit from the menu turns any of the 23 setups into a keep." if keep.empty else ""), "",
         "### Verdict and reading",
         "- **No setup reaches keep, under any guard, pair, confirmation delay, late-entry guard or exit.** All 9 'retire' setups stay "
         "retire-or-rework with negative or near-zero expectancy; none of the 15 rework-group setups (14 in rescore.csv) passes the t bar, "
         "and most fail the regime gate too. P (new long) fails decisively.",
         "- **Why:** the guards mostly remove trades in proportion, not selectively. Averaged over the 23 setups no single guard moves "
         "expectancy by more than +0.035R (G2e21/cur), and the up-session losses of the shorts are not fixed: the guards that cut most "
         "trades (G1k1, G2) leave the up-session expectancy of the MF/RW gap-down shorts at -0.2 to -0.5R.",
         "- **Strongest result, still a fail:** RW6 (NS2 lineage) with G1k2 (no short while a +2 SD VWAP excursion is unresolved): "
         "+0.26R, n 424, t 2.39, up +0.32 / down +0.08, WF 0.625; with G4 as second layer t 2.57, WF 0.71. The bar is 4.76 (N 82,102); "
         "G1k1 on the same setup is -0.02R (no plateau), so it is not even a candidate. NS2 with G1k2 shows the same shape (+0.18R, t 1.53).",
         "- **E1 / E2:** on the baseline entries E1 improves 4 of 23 setups (mean -0.011R) and E2 5 of 23 (mean -0.026R). E2 widens "
         "the up/down split of the shorts. The 10-08 give-backs E1/E2 would have saved are the hindsight pattern already seen in EXIT_STUDY.",
         "- **Anecdote vs history:** G2 (rising EMA9/21) would have blocked all 10 flagged trades at their signal bar, and G1/G5/Lr05 "
         "most of them. On two years the same guards are flat to negative. A rule that catches today's losers also removes yesterday's winners.",
         "- **Count:** 5,152 G/C/E/L + 6 P = 5,158 new configurations; about 258 would pass p = 0.05 by chance. Raw t >= 1.96 with n >= 60 "
         f"occurs in {int(((res.t >= 1.96) & (res.n >= 60)).sum())} configurations, all below their try-count bar.",
         "- Nothing was scored on the locked block. No lab module was written: there is no keep candidate to hand to the lead.", "",
         "### Failures first",
         f"- Configurations with exp > 0 in up AND down sessions (n >= 30 each): {len(both)} of {len(res)} "
         f"({both['setup'].nunique()} setups). Configurations with walk-forward share >= 0.6: {(res.wf_share_pos >= 0.6).sum()}. "
         f"Configurations with t >= their bar: {(res.t >= res.t_required).sum()}.",
         "- Verdict counts over all configurations: " + ", ".join(f"{k} {v}" for k, v in res["verdict"].value_counts().items()) + ".", ""]
    pres = pd.read_csv(HERE / "p_results.csv")
    L += ["### P: first pullback that holds VWAP after a morning low (new long, amendment A; 6 configurations, N = 6)", ""] + HDR
    for r in pres.assign(setup="P", guard="-").itertuples():
        L.append(row(r).replace("| P | - |", f"| P {r.geom} | - |"))
    L.append("")
    # per setup best (by t), retire group first
    L += ["### Best configuration per setup (highest day-clustered t among configurations with n >= 60; descriptive, not a selection)", "",
          f"Configurations with n < 60 ({(res.n < 60).sum()}) are excluded from the 'best' picks: e.g. NS5 with G1+G2e21 keeps 2 trades "
          "and shows t = 603 - a degenerate statistic, not a pass (they fail the regime and walk-forward gates anyway).", ""] + HDR
    resb = res[res["n"] >= 60]
    best = resb.sort_values("t", ascending=False).groupby("setup").head(1)
    best = best.assign(o=best["group"].map({"retire": 0, "rework": 1})).sort_values(["o", "setup"])
    for r in best.itertuples():
        L.append(row(r))
    # baseline vs family bests
    L += ["", "### Per setup: baseline and the best of each menu family (by t)", "",
          "| setup | rescore group | none/cur exp (n, t) | best single G | best C | best G pair | best L | none/E1 | none/E2 | best up&down-positive config |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for s, g in resb.groupby("setup"):
        b0 = g[(g.guard == "none") & (g.exit == "cur")].iloc[0]

        def bf(x):
            if x.empty:
                return "-"
            r = x.sort_values("t", ascending=False).iloc[0]
            return f"{r.guard}/{r.exit}: {f(r.exp_r)} (n {int(r.n)}, t {r.t}; up {f(r.up_exp)}, dn {f(r.down_exp)}, WF {r.wf_share_pos})"

        bb = g[(g.up_exp > 0) & (g.down_exp > 0) & (g.up_n >= 30) & (g.down_n >= 30)]
        L.append(f"| {s} | {g['group'].iloc[0]} | {f(b0.exp_r)} ({int(b0.n)}, {b0.t}) | {bf(g[g.family == 'single'])} | {bf(g[g.family == 'C'])} | "
                 f"{bf(g[g.family == 'pair'])} | {bf(g[g.family == 'L'])} | {bf(g[(g.guard == 'none') & (g.exit == 'E1')])} | {bf(g[(g.guard == 'none') & (g.exit == 'E2')])} | {bf(bb)} |")
    # guard-level average effect across setups
    L += ["", "### Average effect of each guard / exit across setups (mean change in exp R vs none/cur, and mean share of trades kept)", "",
          "| guard | exit | setups | mean d exp R | median d exp R | setups improved | mean trades kept | mean d up exp | mean d down exp |", "|---|---|---|---|---|---|---|---|---|"]
    base = res[(res.guard == "none") & (res.exit == "cur")].set_index("setup")
    g1 = res[(res.family != "pair")].copy()
    g1["d"] = g1["exp_r"] - g1["setup"].map(base["exp_r"])
    g1["kept"] = g1["n"] / g1["setup"].map(base["n"])
    g1["du"] = g1["up_exp"] - g1["setup"].map(base["up_exp"])
    g1["dd"] = g1["down_exp"] - g1["setup"].map(base["down_exp"])
    for (gs, ex), x in g1.groupby(["guard", "exit"], sort=False):
        if gs == "none" and ex == "cur":
            continue
        L.append(f"| {gs} | {ex} | {len(x)} | {x.d.mean():+.3f} | {x.d.median():+.3f} | {(x.d > 0).sum()} | {x.kept.mean():.2f} | {x.du.mean():+.3f} | {x.dd.mean():+.3f} |")
    # validation
    L += ["", "### Simulator checks", "",
          "- Lab exits: the 5-min simulator against the frames' own lab outcome on the baseline (none/cur):"]
    for k, v in val.items():
        if isinstance(v, dict) and "max_abs_diff_lab_r" in v:
            L.append(f"  - {k}: n {v['n']}, max |diff| {v['max_abs_diff_lab_r']}, share > 0.01R {v['share_diff_gt_0.01']}")
    for k in ("orb20_a", "intraday_momentum"):
        if k in val:
            v = val[k]
            L.append(f"- {k} 1-min re-simulation vs the recorded backtester r: n {v['n']}, median |diff| {v['median_abs_diff_r']}, "
                     f"share > 0.05R {v['share_diff_gt_0.05']}, re-sim exp {v['resim_exp']} vs recorded {v['recorded_exp']}.")
    miss = val.get("signals_without_feature_row", {})
    if miss:
        L.append(f"- Raw signal bars without a feature row (dropped): max share {max(miss.values())}.")
    # anecdote
    L += ["", "### Anecdote: the owner's 10 trades of 2026-10-08 (+ GEV). One paper session - a diagnosis, not evidence", "",
          "Guards at the live signal bar (block = the guard rejects that bar; under the layer rule a later bar of the same day could still have entered). sim_* = the live fill re-walked "
          "on 1-min bars with the live stop/target and engine costs (cur, E1, E2). C3/C6/C12 = confirmation entry time and its "
          "result with the live geometry, or 'dropped'.", "",
          "| id | sym | setup | side | vwap % (SD z) | EMA9 % / slope 9,21 | RSI | CMF (rising) | OBV+ | ADX (DI gap) | VAH/VAL | G1k1 | G1k2 | G2e9 | G2e21 | G3a | G3b | G4 25/5 | G4 30/10 | G5 | Lr05 | Lr10 | Lm60 | Lm120 | r live | sim cur | E1 | E2 (stop R) | C3 | C6 | C12 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    yn = lambda b: "**block**" if bool(b) else "-"
    for r in an.itertuples():
        va = "above VAH" if r.above_vah else ("below VAL" if r.below_val else "inside")
        L.append(f"| {r.id} | {r.symbol} | {r.setup.split('-')[0]} | {r.side} | {r.vwap_dist_pct:+.2f} ({r.vwap_sd_z}) | {r.ema9_dist_pct:+.2f} / {r.ema9_slope},{r.ema21_slope} | "
                 f"{r.rsi} | {r.cmf:+.3f} ({'up' if r.cmf_rising else 'down'}) | {'yes' if r.obv_slope_pos else 'no'} | {r.adx} ({r.di_gap:+.1f}) | {va} | "
                 f"{yn(r.G1k1)} | {yn(r.G1k2)} | {yn(r.G2e9)} | {yn(r.G2e21)} | {yn(r.G3a)} | {yn(r.G3b)} | {yn(r.G4a25d5)} | {yn(r.G4a30d10)} | {yn(r.G5)} | {yn(r.Lr05)} | {yn(r.Lr10)} | {yn(r.Lm60)} | {yn(r.Lm120)} | "
                 f"{r.r_live:+.2f} | {r.sim_cur:+.2f} | {r.sim_E1:+.2f} | {r.sim_E2:+.2f} ({r.E2_stop_dist_R}) | {r.C3} | {r.C6} | {r.C12} |")
    ap = pd.read_csv(HERE / "anecdote_p.csv")
    L += ["", "P (amendment A) on 2026-10-08 (anecdote; adv filter not applied): first P bar and its result, R after costs.", "",
          "| sym | fires | bar end | t1s1 | t1s1+E1 | t05s1 | t05s1+E1 | t1s05 | t1s05+E1 |", "|---|---|---|---|---|---|---|---|---|"]
    for r in ap.itertuples():
        L.append(f"| {r.symbol} | {r.p_fires} | {int(r.p_bar_end)} | {r.t1s1_cur:+.2f} | {r.t1s1_E1:+.2f} | {r.t05s1_cur:+.2f} | {r.t05s1_E1:+.2f} | {r.t1s05_cur:+.2f} | {r.t1s05_E1:+.2f} |")
    txt = (HERE / "NOTES.md").read_text()
    head = txt.split("\n## 2. Results")[0].rstrip("\n") + "\n"
    (HERE / "NOTES.md").write_text(head + "\n".join(L) + "\n")
    print("\n".join(L[:40]))


if __name__ == "__main__":
    main()
