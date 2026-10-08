"""Stage 2 (rule-18 style rework, pre-declared before running): for 7 promising stage-1 families, take the
3 configurations with the best TRAIN same-time-control t (train n >= 60; valid not looked at for the
choice) and add ONE condition from a 16-item library. 7 x 3 x 16 = 336 configurations, same strict gate.
Educational only - not financial advice."""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
sys.path.insert(0, "research/oct7/innovation")
import bdlib as B  # noqa: E402
from scan import specs  # noqa: E402


def c(d, k):
    return d[k].to_numpy(dtype=float)


LIB = {
    "gap<0": lambda d: c(d, "gap") < 0, "gap>0": lambda d: c(d, "gap") > 0,
    "vwap<0": lambda d: c(d, "vwapDistPct") < 0, "vwap>0": lambda d: c(d, "vwapDistPct") > 0,
    "rsi3>=70": lambda d: c(d, "rsi3") >= 70, "rsi3<=30": lambda d: c(d, "rsi3") <= 30,
    "slope<0": lambda d: c(d, "sma20_slope_pct") < 0, "slope>0": lambda d: c(d, "sma20_slope_pct") > 0,
    "vr<1": lambda d: c(d, "volumeRatio") < 1, "vr>=1.5": lambda d: c(d, "volumeRatio") >= 1.5,
    "fo<0": lambda d: c(d, "fromOpen") < 0, "fo>0": lambda d: c(d, "fromOpen") > 0,
    "uwick>=0.4": lambda d: c(d, "upper_wick") >= 0.4, "lwick>=0.4": lambda d: c(d, "lower_wick") >= 0.4,
    "abovePDH": lambda d: c(d, "dist_pdh_atr") < 0, "belowPDL": lambda d: c(d, "dist_pdl_atr") < 0,
}

FAMS = {
    "C-fade-up": lambda r: r.tag.str.startswith("C-fade-up"),
    "C-follow-dn": lambda r: r.tag.str.startswith("C-follow-dn"),
    "E1": lambda r: r.family.eq("E1"), "E2": lambda r: r.family.eq("E2"),
    "D6": lambda r: r.family.eq("D6"), "D4": lambda r: r.family.eq("D4"),
    "A-hfl": lambda r: r.tag.str.startswith("A-hfl"),
}


def main():
    s1 = pd.read_csv("research/oct7/innovation/scan_results.csv")
    sp = {tag: (fam, side, win, fn, params) for fam, tag, params, side, win, geoms, fn in specs()}
    tr, va = B.load("train"), B.load("valid")
    rows = []
    for fname, sel in FAMS.items():
        cand = s1[sel(s1) & (s1.tr_n >= 60)].sort_values("tr_t_st", ascending=False).head(3)
        for _, core in cand.iterrows():
            fam, side, win, fn, params = sp[core.base_tag]
            g = core.geom
            mtr, mva = np.asarray(fn(tr), bool), np.asarray(fn(va), bool)
            for an, af in LIB.items():
                a = B.score(tr, mtr & af(tr), side, g, win)
                b = B.score(va, mva & af(va), side, g, win)
                rows.append({"stage2_family": fname, "core": core.tag, "add": an, "tag": f"{core.tag}+{an}", "side": side,
                             "geom": g, "window": f"{win[0]}-{win[1]}", **B.flat("tr", a), **B.flat("va", b), "gate": B.gate(a, b)})
        print(fname, "done", len(rows), flush=True)
    out = pd.DataFrame(rows)
    out.to_csv("research/oct7/innovation/stage2_results.csv", index=False)
    print("configs:", len(out), "gate passes:", int(out.gate.sum()))
    cols = ["tag", "tr_n", "tr_exp_r_prod", "tr_t_day", "tr_t_st", "va_n", "va_exp_r_prod", "va_t_day", "va_t_st", "va_ex_best", "va_best_share"]
    print(out[out.gate].sort_values("va_t_day", ascending=False)[cols].to_string())


if __name__ == "__main__":
    main()
