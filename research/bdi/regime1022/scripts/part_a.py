"""regime1022 Part A: Primary setups with a big live loss. Live paper record (Primary only / all accounts), the 2-year
as-run backtest, R by regime, how often a day as bad as 10-21 happens, in which regime, and whether bad days cluster.
Writes part_a.csv, part_a_days.csv, part_a_out.md. Educational only - not financial advice."""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from live import journals, record
from rc import HERE, ROOT, SCR, gates
from regime import LABELS, day_table

BIG = -100.0   # PLAN: live P/L since start <= -$100, or 10-20 + 10-21 P/L <= -$100


def main():
    T = journals()
    dt = day_table()
    T["regime"] = T["date"].map(dt["regime"])
    prim = json.loads((ROOT / "docs" / "live" / "assignments.json").read_text())["accounts"]["primary"]
    p = T[T["acct"] == "p"]
    losers = []
    for s in prim:
        a = p[p["strategy"] == s]
        last2 = a[a["date"].astype(str).isin(["2026-10-20", "2026-10-21"])]["pnl_adj"].sum()
        if a["pnl_adj"].sum() <= BIG or last2 <= BIG:
            losers.append(s)
    src = sys.argv[1] if len(sys.argv) > 1 else "asrun"
    if src == "g21":
        A = pd.read_parquet("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/g1021/trades_A0.parquet")
        A = A.drop(columns=["regime"]).join(dt[["regime"]], on="date")
    else:
        A = pd.read_parquet(SCR / "asrun.parquet")
        A = A[A["asrun"]]
        A = A.assign(setup=A["names"].str.split(",")).explode("setup")
    out, days_out, md = [], [], []
    md.append("# Part A - Primary setups with a big live loss (paper live; 2-year as-run backtest)\n")
    md.append(f"Selected (live P/L since start <= ${BIG:.0f} or 10-20+10-21 <= ${BIG:.0f}): {', '.join(losers)}\n")
    for s in losers:
        rp = record(p[p["strategy"] == s])
        ra = record(T[T["strategy"] == s])
        live_days = p[p["strategy"] == s].groupby("date").agg(R=("radj", "sum"), pnl=("pnl_adj", "sum"),
                                                              n=("radj", "size"))
        live_days["regime"] = live_days.index.map(dt["regime"])
        x = A[A["setup"] == s]
        row = {"setup": s, **{f"live_p_{k}": v for k, v in rp.items()}, **{f"live_all_{k}": v for k, v in ra.items()}}
        md.append(f"\n## {s}\n")
        md.append(f"- Live Primary (paper): {rp}\n- Live all accounts merged (paper): {ra}\n")
        md.append("- Live Primary by day: " + "; ".join(f"{d} {r.regime} {r.n} trades {r.R:+.1f}R ${r.pnl:+.0f}"
                                                      for d, r in live_days.iterrows()) + "\n")
        if x.empty:
            md.append("- **No 2-year backtest** (not covered by the frame scan).\n")
            out.append(row)
            continue
        sm = gates.summary(x[["date", "r"]])
        row.update({"bt_n": sm["n"], "bt_avg_r": sm["exp_r"], "bt_t": sm["t"], "bt_days": x["date"].nunique()})
        for sp in ("train", "valid"):
            xs = x[x["split"] == sp]
            ss = gates.summary(xs[["date", "r"]])
            row.update({f"bt_{sp}_n": ss.get("n"), f"bt_{sp}_avg_r": ss.get("exp_r"), f"bt_{sp}_t": ss.get("t")})
        for lab in LABELS:
            xs = x[x["regime"] == lab]
            ss = gates.summary(xs[["date", "r"]]) if len(xs) else {}
            row.update({f"{lab}_n": len(xs), f"{lab}_avg_r": ss.get("exp_r"), f"{lab}_t": ss.get("t")})
        # setup-day distribution vs the worst live day
        sd = x.groupby("date").agg(R=("r", "sum"), n=("r", "size"))
        sd = sd.join(dt[["regime", "o2c"]])
        alld = dt.loc[(dt.index >= x["date"].min()) & (dt.index <= pd.Timestamp("2026-10-07").date())]
        alld = alld[alld["regime"].notna()]
        sessions = len(alld)
        worst_live = float(live_days["R"].min()) if len(live_days) else np.nan
        last = live_days["R"].iloc[-1] if len(live_days) else np.nan
        for thr_name, thr in (("live_worst", worst_live), ("m5", -5.0), ("m10", -10.0)):
            bad = sd[sd["R"] <= thr]
            row[f"days_le_{thr_name}"] = len(bad)
            row[f"days_le_{thr_name}_per_100_sessions"] = round(100 * len(bad) / sessions, 2)
            row[f"days_le_{thr_name}_regimes"] = json.dumps(bad["regime"].value_counts().to_dict())
            row[f"days_le_{thr_name}_R_share"] = round(float(bad["R"].sum() / sd["R"].sum()), 2) if sd["R"].sum() else None
        row["live_worst_day_R"] = worst_live
        row["live_last_day_R"] = last
        row["pctile_of_live_worst"] = round(100 * float((sd["R"] <= worst_live).mean()), 1)
        # streaks: P(bad | previous traded session bad) vs base rate; bad = bottom decile setup-day
        q10 = sd["R"].quantile(0.10)
        b = (sd["R"] <= q10).astype(int).to_numpy()
        cond = b[1:][b[:-1] == 1].mean() if b[:-1].sum() else np.nan
        row.update({"bad_q10_R": round(float(q10), 2), "p_bad": round(float(b.mean()), 3),
                    "p_bad_after_bad": round(float(cond), 3)})
        runs, cur = [], 0
        for v in b:
            cur = cur + 1 if v else 0
            if v:
                runs.append(cur)
        row["longest_bad_streak"] = int(max(runs) if runs else 0)
        # share of sessions it trades, by regime (how often it is "on")
        reg_days = sd.groupby("regime").agg(days=("R", "size"), R=("R", "sum"), avg_day_R=("R", "mean"))
        row["by_regime_days"] = json.dumps({k: {"days": int(v.days), "sum_R": round(float(v.R), 1),
                                                "avg_day_R": round(float(v.avg_day_R), 2)} for k, v in reg_days.iterrows()})
        out.append(row)
        sd["setup"] = s
        days_out.append(sd.reset_index())
        md.append(f"- 2-year as-run: n {sm['n']}, avg R {sm['exp_r']:+.3f} (t {sm['t']}); train "
                  f"{row['bt_train_avg_r']:+.3f} / valid {row['bt_valid_avg_r']:+.3f}\n")
        md.append("- By regime (avg R, n): " + "; ".join(f"{lab} {row[f'{lab}_avg_r'] if row[f'{lab}_avg_r'] is not None else float('nan'):+.3f} ({row[f'{lab}_n']})" for lab in LABELS) + "\n")
        md.append(f"- Worst live Primary day {worst_live:+.1f}R. On 2 years, {row['days_le_live_worst']} setup-days were "
                  f"that bad or worse ({row['days_le_live_worst_per_100_sessions']} per 100 sessions; percentile "
                  f"{row['pctile_of_live_worst']}% of its traded days); regimes {row['days_le_live_worst_regimes']}.\n")
        md.append(f"- Days <= -5R: {row['days_le_m5']} ({row['days_le_m5_regimes']}); <= -10R: {row['days_le_m10']} "
                  f"({row['days_le_m10_regimes']}).\n")
        md.append(f"- Clustering: bottom-decile day (<= {q10:+.1f}R) base rate {row['p_bad']:.2f}, after a bottom-decile "
                  f"day {row['p_bad_after_bad']:.2f}; longest run {row['longest_bad_streak']}.\n")
        md.append(f"- By regime, setup-days: {row['by_regime_days']}\n")
    pd.DataFrame(out).to_csv(HERE / "part_a.csv", index=False)
    if days_out:
        pd.concat(days_out).to_csv(HERE / "part_a_days.csv", index=False)
    (HERE / "part_a_out.md").write_text("".join(md))
    print("".join(md))


if __name__ == "__main__":
    main()
