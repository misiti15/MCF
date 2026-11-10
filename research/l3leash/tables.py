"""L3LEASH: markdown tables for NOTES.md from configs.csv. Educational only - not financial advice."""
from pathlib import Path
import pandas as pd
H = Path(__file__).resolve().parent
M = pd.read_csv(H / "configs.csv")
MAIN = "L3-gap-slope-fromopen-FD"
NAME = dict(B0="base (-2R latch)", K01="BLOCK on UP-conf", K02="SCALE 0.5 pre-conf / 0 UP", K03="SCALE 0.5 pre-conf / 0.5 UP",
            K04="RAMP 0.5x < 10:30", K05="RAMP 0.5x < 10:45", K06="RAMP 0.5x < 11:15", K07="RAMP<10:30 + BLOCK",
            K08="SPY>=+0.20% skip", K09="SPY>=+0.40% skip", K10="SPY>=+0.20% half", K11="SPY>=+0.40% half", K12="-1R latch after UP-conf")
f = lambda v, d=1: "" if pd.isna(v) else f"{v:+.{d}f}"
o = []
for sp in ("TRAIN", "VALID", "FWD"):
    o.append(f"\n**{MAIN} - {sp} (lab, costs in)**\n")
    o.append("| cfg | leash | trades | total R | R/trade | day-t | dR vs base (paired t) | red-day R removed | green-day R given up | green days | worst day | worst 5 | avg R w/o best day |")
    o.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in M[(M.setup == MAIN) & (M.split == sp)].itertuples():
        o.append(f"| {r.cfg} | {NAME[r.cfg]} | {r.trades} | {r.R:+.1f} | {r.R_per_trade:+.3f} | {r.day_t:.2f} | {f(r.dR)} ({f(r.pair_t, 2)}) | "
                 f"{f(r.red_removed)} of {r.red_base:.1f} ({r.red_removed_pct:.0f}%) | {f(r.green_given)} of {r.green_base:.1f} ({r.green_given_pct:.0f}%) | "
                 f"{r.green_days}/{r.days} | {r.worst_day:+.1f} | {r.worst5:+.1f} | {f(r.avgR_wo_best, 3)} |")
for s, lab in (("Primary:" + MAIN, "LIVE Primary 10-21..11-09 (run 1 + latch what-ifs)"), ("Testing1:" + MAIN, "LIVE Testing 1 10-13..10-29 (run 1; -2R latch applied in sim)")):
    o.append(f"\n**{lab}**\n")
    o.append("| cfg | trades | total R | dR | red-day R removed | green-day R given up | worst day | best-day share |")
    o.append("|---|---|---|---|---|---|---|---|")
    for r in M[(M.setup == s) & (M.split == "LIVE")].itertuples():
        o.append(f"| {r.cfg} | {r.trades} | {r.R:+.2f} | {f(r.dR, 2)} | {f(r.red_removed, 2)} of {r.red_base:.2f} | {f(r.green_given, 2)} of {r.green_base:.2f} | {r.worst_day:+.2f} | "
                 f"{'' if pd.isna(r.best_share) else f'{r.best_share:.0%}'} |")
x = M[(M.setup == "Primary:" + MAIN) & (M.split.str.startswith("LIVE-11-10"))]
o.append("\n**Primary 11-10 so far (9 trades, partial, in-sample - the day that prompted the question)**: " +
         "; ".join(f"{r.cfg} {r.R:+.2f}R" for r in x.itertuples()))
sis = M[~M.setup.isin([MAIN]) & ~M.setup.str.contains(":")]
o.append("\n**Sisters (lab): setups better / worse vs their own base, sum of dR**\n")
o.append("| cfg | TRAIN better/worse, dR | VALID better/worse, dR | FWD better/worse, dR | worst sister VALID | worst sister FWD |")
o.append("|---|---|---|---|---|---|")
for c in NAME:
    if c == "B0":
        continue
    cells = []
    for sp in ("TRAIN", "VALID", "FWD"):
        y = sis[(sis.cfg == c) & (sis.split == sp)]
        cells.append(f"{(y.dR > 0).sum()}/{(y.dR < 0).sum()}, {y.dR.sum():+.0f}")
    wv = sis[(sis.cfg == c) & (sis.split == "VALID")].nsmallest(1, "dR").iloc[0]
    wf = sis[(sis.cfg == c) & (sis.split == "FWD")].nsmallest(1, "dR").iloc[0]
    o.append(f"| {c} {NAME[c]} | " + " | ".join(cells) + f" | {wv.setup} {wv.dR:+.0f} | {wf.setup} {wf.dR:+.0f} |")
o.append("\n**Sister base R (lab, -2R latch, caps)**: " + "; ".join(
    f"{s} T {sis[(sis.setup == s) & (sis.cfg == 'B0') & (sis.split == 'TRAIN')].R.iloc[0]:+.0f} / V {sis[(sis.setup == s) & (sis.cfg == 'B0') & (sis.split == 'VALID')].R.iloc[0]:+.0f} / F {sis[(sis.setup == s) & (sis.cfg == 'B0') & (sis.split == 'FWD')].R.iloc[0]:+.0f}"
    for s in sorted(sis.setup.unique())))
(H / "tables.md").write_text("\n".join(o) + "\n\nEducational only - not financial advice.\n")
print("\n".join(o))
