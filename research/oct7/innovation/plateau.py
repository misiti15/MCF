"""Plateau / ablation checks for the 3 stage-2 gate passes (pre-declared neighbour sets; all counted).
Educational only - not financial advice."""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
sys.path.insert(0, "research/oct7/innovation")
sys.path.insert(0, "research/heat/candidates")
import bdlib as B  # noqa: E402
import regime_5  # noqa: E402


def c(d, k):
    return d[k].to_numpy(dtype=float)


def e2(g, x, add, rsi_on=True):
    def f(d):
        m = c(d, "gap") <= -g
        if rsi_on:
            m &= c(d, "rsi3") >= x
        if add == "fo>0":
            m &= c(d, "fromOpen") > 0
        elif add == "vwap>0":
            m &= c(d, "vwapDistPct") > 0
        return m
    return f


def hfl(n, x, pdl):
    def f(d):
        m = regime_5.score(d) >= regime_5.LONG_AT
        if n:
            m &= c(d, f"rsi{n}") <= x
        if pdl is not None:
            m &= c(d, "dist_pdl_atr") < pdl
        return m
    return f


CHECKS = []
for add in ("fo>0", "vwap>0"):
    fin = f"E2-g0.88-rsi3ge70+{add}"
    for g, x in ((0.88, 70), (0.5, 70), (1.66, 70), (0.88, 50), (0.88, 85)):
        CHECKS.append((fin, f"g{g}-x{x}", e2(g, x, add), "short", (1300, 1430), "t1s1"))
    CHECKS.append((fin, "no-rsi3", e2(0.88, 70, add, rsi_on=False), "short", (1300, 1430), "t1s1"))
    CHECKS.append((fin, "no-add", e2(0.88, 70, None), "short", (1300, 1430), "t1s1"))
    for g_ in ("t05s1", "t1s05"):
        CHECKS.append((fin, f"geom-{g_}", e2(0.88, 70, add), "short", (1300, 1430), g_))
    for w in ((1230, 1430), (1300, 1500), (1330, 1430), (1300, 1400)):
        CHECKS.append((fin, f"win{w[0]}-{w[1]}", e2(0.88, 70, add), "short", w, "t1s1"))
fin = "hfl-rsi3le50+belowPDL"
for n, x, pdl in ((3, 50, 0.0), (3, 40, 0.0), (3, 60, 0.0), (2, 50, 0.0), (4, 50, 0.0), (None, None, 0.0),
                  (3, 50, -0.25), (3, 50, 0.25), (3, 50, None)):
    CHECKS.append((fin, f"rsi{n}le{x}-pdl{pdl}", hfl(n, x, pdl), "long", (1105, 1330), "t1s1"))


def main():
    tr, va = B.load("train"), B.load("valid")
    rows = []
    for fin, nb, fn, side, win, g in CHECKS:
        a, b = B.score(tr, fn(tr), side, g, win), B.score(va, fn(va), side, g, win)
        rows.append({"finalist": fin, "variant": nb, "geom": g, "window": f"{win[0]}-{win[1]}", **B.flat("tr", a), **B.flat("va", b), "gate": B.gate(a, b)})
    out = pd.DataFrame(rows)
    out.to_csv("research/oct7/innovation/plateau_results.csv", index=False)
    cols = ["finalist", "variant", "tr_n", "tr_exp_r_prod", "tr_t_day", "tr_t_st", "va_n", "va_exp_r_prod", "va_t_day", "va_t_st", "va_ex_best", "va_best_share", "gate"]
    pd.set_option("display.width", 250)
    print("configs:", len(out))
    print(out[cols].to_string())


if __name__ == "__main__":
    main()
