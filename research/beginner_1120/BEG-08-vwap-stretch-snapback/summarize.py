"""BEG-08 summary: T1 combined from the booked fit + check files, the verdict vs the top-10 standard, controls.
python summarize.py WORK -> results.json beside this file. Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402

TH = dict(comb=-0.0383, check=-0.0464, comb_wo=-0.0674, check_wo=-0.0781, comb_rps=-0.4862, check_rps=-0.5218,
          t2=-0.1048)


def verdict(r):
    c, k, t2 = r["T1_combined"], r["T1_check"], r["T2"]
    legs = {"comb_avg": (c["avg_r"], TH["comb"]), "check_avg": (k["avg_r"], TH["check"]),
            "comb_wo": (c["avg_r_wo_best_day"], TH["comb_wo"]), "check_wo": (k["avg_r_wo_best_day"], TH["check_wo"]),
            "comb_rps": (c["total_r_per_session"], TH["comb_rps"]),
            "check_rps": (k["total_r_per_session"], TH["check_rps"]), "t2_avg": (t2["avg_r"], TH["t2"])}
    fails = {n: round(v - th, 4) for n, (v, th) in legs.items() if v < th}
    enough = k["trades"] >= 20 and t2["trades"] >= 20
    if not fails and enough:
        tier = "MEETS"
    elif enough and all(g >= -0.02 for g in fails.values()):
        tier = "NEAR"
    else:
        tier = "FAIL"
    rb = (c["avg_r"] <= -0.05 and c["t_day_clustered"] <= -2.0) or all(
        x < -0.03 for x in (r["T1_fit"]["avg_r"], k["avg_r"], t2["avg_r"]))
    return tier, fails, rb


def main(W):
    W = Path(W)
    spy1 = B.spy_t1()
    spy1 = spy1[spy1.index <= "2026-11-04"]
    out = {}
    for v in ("base", "fresh3", "tgthalf", "stop125"):
        r = {}
        for part in ("fit", "check", "t2"):
            f = W / f"res_{v}_{part}.json"
            if f.exists():
                r.update(json.loads(f.read_text()))
        if "T1_fit" in r and "T1_check" in r:
            bk = pd.concat([pd.read_parquet(W / f"bk_{v}_{p}.parquet") for p in ("fit", "check")])
            r["T1_combined"] = B.stats(bk, 446, spy1)
        if all(k in r for k in ("T1_combined", "T1_check", "T2")):
            tier, fails, rb = verdict(r)
            r["verdict"] = dict(tier=tier, failing_legs_gap=fails, really_bad=rb)
        out[v] = r
    ctl = {}
    for f in sorted(W.glob("res_base_rnd*_*.json")):
        ctl[f.stem.replace("res_", "")] = {k: {x: v.get(x) for x in ("trades", "avg_r", "avg_r_wo_best_day",
                                                                        "t_day_clustered")}
                                          for k, v in json.loads(f.read_text()).items()}
    out["controls"] = ctl
    (HERE / "results.json").write_text(json.dumps(out, indent=1, default=float))
    keys = ("trades", "trades_per_session", "win", "avg_r", "avg_r_gross", "avg_r_wo_best_day", "best_day",
            "best_day_share", "total_r_per_session", "worst_day", "t_day_clustered", "avg_r_spy_up", "avg_r_spy_flat",
            "avg_r_spy_down", "median_hold_min")
    for v, r in out.items():
        if v == "controls":
            continue
        print("==", v, r.get("verdict"))
        for t in ("T1_fit", "T1_check", "T1_combined", "T2"):
            if t in r:
                print(" ", t, {k: r[t].get(k) for k in keys})
    for k, v in ctl.items():
        print("ctl", k, v)


if __name__ == "__main__":
    main(sys.argv[1])
