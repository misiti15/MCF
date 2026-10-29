"""swarm15_1029: NOTES tables from results.csv + live_vs_bt.csv -> tables_out.md. Educational only - not financial advice."""
from pathlib import Path
import pandas as pd
H = Path(__file__).resolve().parent
R = pd.read_csv(H / "results.csv"); LB = pd.read_csv(H / "live_vs_bt.csv").set_index("setup")
NAMES = {"CWT14-failbrk-orl-p05-long": "Failed Opening-Range-Low Break Long (0.05 ATR)", "CWT14-failbrk-pdl-p05-long": "Failed Prior-Day-Low Break Long (shallow)",
         "CWT14-failbrk-orl-p05-lowvol-long": "Failed OR-Low Break Long (0.05 ATR, low volume)", "heat_fade_short-FD": "Morning Bounce Fade (all day)",
         "CWT12-coil-k4-long": "Coil Under the High (4 bars)", "CWT14-failbrk-pdl-p05-lowvol-long": "Failed PD-Low Break Long (0.05 ATR, low volume)",
         "CWT14-failbrk-orl-p10-long": "Failed OR-Low Break Long (0.1 ATR)", "CWT14-failbrk-pdl-p10-long": "Failed Prior-Day-Low Break Long",
         "CWT14-failbrk-orl-p10-lowvol-long": "Failed OR-Low Break Long (low volume)", "CWT14-failbrk-pdh-p05-lowvol-short": "Failed PD-High Break Short (0.05 ATR, low volume)",
         "CWT14-failbrk-pdh-p10-short": "Failed PD-High Break Short (0.1 ATR)", "RW7-gapdn-bounce-early-short-FD": "(no display name)",
         "RW2-exhaustion-noon-adv150-short-FD": "(no display name)", "LIQ-orl-sweep-open15-s25-long": "Opening-Range Low Sweep Reversal",
         "L3-gap-slope-fromopen-FD": "Gap-Down Recovery Fade (all day)"}
f = lambda x, d=3: "" if pd.isna(x) else f"{x:+.{d}f}"  # noqa: E731
L = ["| # | setup | live n | live avg R | live w/o best day (share) | 2-yr avg R (TRAIN+VALID, n) | z live-bt | best variant | its TRAIN / VALID avg R | t (TRAIN+VALID) vs bar | d vs parent t (TRAIN / VALID) | HOLD (look) | verdict |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for i, s in enumerate(NAMES, 1):
    g = R[R.setup == s]; p = g[g["var"] == "P"].iloc[0]; v = g[g["var"] != "P"]
    b = v.sort_values("exp_tv", ascending=False).iloc[0]; lv = LB.loc[s]
    sh = "1 day" if (pd.notna(lv.live_best_share) and lv.live_best_share >= 0.5) else ("total < 0" if pd.isna(lv.live_best_share) else f"{lv.live_best_share:.0%}")
    hold = f"{b.hold_exp:+.3f} (n {int(b.hold_n)}, t {b.hold_t:.2f}){'' if b.hold_official else ' extra look'}" if pd.notna(b.get("hold_n")) else "not looked"
    L.append(f"| {i} | {NAMES[s]}, `{s}` | {int(lv.live_n)} | {f(lv.live_avg)} | {f(lv.live_wo_best)} ({sh}) | {f(p.exp_tv)} ({int(p.n_tv)}) | {lv.z:+.2f} | {b['var']} {b.knob} | {f(b.exp_train)} / {f(b.exp_valid)} | {b.t_tv:.2f} vs {b.bar:.2f} | {b.t_imp_train:.1f} / {b.t_imp_valid:.1f} | {hold} | {b.verdict} |")
L += ["", "Family readout (rows that beat their parent on TRAIN and VALID / rows scored; median d vs parent per parent trade):", "",
      "| family | rows | beat parent | exp > 0 TRAIN and VALID | median d (TRAIN) |", "|---|---|---|---|---|"]
v = R[R["var"] != "P"].copy(); v["fam"] = v["var"].str[0]
FAM = {"S": "stop x2/2.5/3 same $", "T": "target / scale-out", "X": "time stop 45/180", "W": "entry window", "C": "context filter", "R": "re-entry / caps", "K": "cost floor"}
for k, g in v.groupby("fam"):
    L.append(f"| {FAM[k]} | {len(g)} | {int(g.beats_parent.sum())} | {int(g.pos_train_valid.sum())} | {g.d_train.median():+.4f} |")
(H / "tables_out.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
