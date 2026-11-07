"""Markdown rows for NOTES.md from all_setups.csv (PREVAL 1107). Educational only - not financial advice."""
import pandas as pd, numpy as np
C = pd.read_csv("all_setups.csv").set_index("setup")
def f(v, p=3, sign=True):
    return "-" if v != v else (f"{v:+.{p}f}" if sign else f"{v:.{p}f}")
def row(k, verdict):
    c = C.loc[k]
    bd = "-" if c.best_share != c.best_share else f"{c.best_share:.0%}" + (" `1 day`" if c.best_share >= 0.5 else "")
    bt = f(c.bt2y) + ("" if str(c.bt2y_n) in ("nan", "") else (f" (n {int(float(c.bt2y_n)):,})" if str(c.bt2y_n).replace('.', '').isdigit() else f" ({c.bt2y_n})"))
    return (f"| {c['name']} `{k.replace(' [P only]', '').replace(' [GY only]', '')}`{' **P only**' if 'P only' in k else ''}{' **GY only**' if 'GY only' in k else ''} | {c.now} | {c.seg} | {int(c.trades)} / {int(c.sessions)} | {f(c.avgR)} | {f(c.exbest)} ({bd}) | "
            f"{c.green:.0%} / {c.worst:+.1f} ({c.worst_day[5:]}) | {f(c.last10)} | {f(c.exmkt)} (β {f(c.beta, 2, False)}) | {bt} | {c.regx} | {f(c.since1029)} ({int(c.n1029)}) | {verdict} |")
HDR = ("| Setup | now | segment | trades / sessions | avg R | w/o best day (share) | green days / worst day | last-10 | ex-market (beta) | 2y R | REGX | since 10-29 (n) | call |\n"
       "|---|---|---|---|---|---|---|---|---|---|---|---|---|")
import sys
print(HDR)
for line in sys.stdin:
    if line.strip():
        k, v = line.rstrip("\n").split("\t")
        print(row(k, v))
