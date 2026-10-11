"""Markdown tables for CASES.md from panel_at_turns.csv / moments.csv / market.csv / confluence.csv / signatures.csv.
Educational only - not financial advice."""
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
d = pd.read_csv(HERE / "panel_at_turns.csv")
OWN_L, OWN_S = ["M1", "M4"], ["M2", "M3", "M5"]
ALL_L, ALL_S = ["M1", "M1b", "M1c", "M4", "M4b"], ["M2", "M3", "M3a", "M3b", "M5", "M5b"]


def f(x, nd=2):
    return "" if pd.isna(x) else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


out = []
for m, g in d.groupby("moment", sort=False):
    x = g[g.flag_at_T].copy()
    x["timing"] = x.share_of_prior60_flagged < 0.5
    x = x.sort_values(["timing", "lift"], ascending=[False, False]).head(14)
    out.append(f"\n#### {m} table ({len(g[g.flag_at_T])} of {len(g)} flags lit at T; top 14, timing flags first)\n")
    out.append("| feature | value at T | pct (20d) | lit run began, min before T | share of prior 60 min lit | onsets / session | precision 1R | lift | lift 2R | onsets / hits 10-09 |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in x.itertuples():
        out.append(f"| {r.feature} | {f(r.value_T)} | {f(r.pct_T, 0)} | {f(r.lit_run_started_min_before, 0)} | {f(r.share_of_prior60_flagged)} | "
                   f"{f(r.onsets_per_session)} | {f(r.precision_20d)} | {f(r.lift)} | {f(r.lift2)} | {r.onsets_1009} / {r.hits_1009} |")
    aft = g[g.only_after_T].feature.tolist()
    out.append(f"\nLit only after the extreme (T+1..T+5, confirmation): {', '.join(aft) if aft else 'none'}\n")
(HERE / "tables_moments.md").write_text("\n".join(out))

# family tally (any timeframe)
d["fam_tf"] = d.feature
rows = []
for fam, g in d.groupby("feature"):
    def lit(ms):
        return int(g[g.moment.isin(ms)].flag_at_T.sum())
    def timing(ms):
        gg = g[g.moment.isin(ms)]
        return int((gg.flag_at_T & (gg.share_of_prior60_flagged < 0.5)).sum())
    rows.append(dict(feature=fam, owner_long_2=lit(OWN_L), owner_short_3=lit(OWN_S), all_long_5=lit(ALL_L),
                     all_short_6=lit(ALL_S), timing_lit_all_11=timing(ALL_L + ALL_S),
                     med_onsets_per_session=g.onsets_per_session.median(), med_lift=g.lift.median()))
t = pd.DataFrame(rows)
t["lit_all_11"] = t.all_long_5 + t.all_short_6
t = t.sort_values(["lit_all_11", "med_lift"], ascending=False)
t.to_csv(HERE / "family_tally.csv", index=False)
print(t.head(40).to_string())
print((HERE / "tables_moments.md").read_text()[:3000])
