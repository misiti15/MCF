"""Owner follow-up 2026-11-17: design the automated dip-buying rule (trigger x size ladder x allocation cap x trim) on
TRAIN 2016-01..2021-12, check on VALID 2022-01..2024-10-31 and SEG-B 2025-03-03..2026-11-16 (each run fresh from
$100k, nothing straddles the locked block). Account-level, compounding sizes (% of current equity), SPXL, costs
$0.01/share + 1 bp per side, idle cash in T-bills (BIL). Pre-declared choice: highest TRAIN CAGR among configs whose
TRAIN max drawdown is no worse than 1.2 x SPY buy-and-hold's TRAIN max drawdown.
Benchmarks per window: SPY buy-and-hold; static SPXL at the chosen cap (monthly rebalanced, rest T-bills); the same
dollars as the chosen rule spent evenly (one buy every k sessions, same cap/trim); random-day draws of the same buys.
Usage: python design.py DAILY.parquet OUTDIR. Educational only - not financial advice."""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_daily  # noqa: E402
from partA import dd_stats  # noqa: E402

WIN = {"TRAIN": ("2016-01-04", "2021-12-31"), "VALID": ("2022-01-03", "2024-10-31"),
       "SEG-B": ("2025-03-03", "2026-11-16")}
LADDERS = {  # (dip from previous close, % of current equity bought) -- the deepest tier reached sets the target
    "flat0.5@1": [(0.01, 0.005)],
    "L1 0.25/0.5/1": [(0.005, 0.0025), (0.01, 0.005), (0.02, 0.01)],
    "L2 0.5/1/2": [(0.005, 0.005), (0.01, 0.01), (0.02, 0.02)],
    "L3 1/2/4": [(0.005, 0.01), (0.01, 0.02), (0.02, 0.04)],
}
TRIGGERS = ["gap", "close", "either"]
CAPS = [0.25, 0.40, 0.60, 1.00]
TRIMS = ["none", "to_cap"]
CPS, BPS, E0 = 0.01, 1e-4, 100_000.0
INSTR = "SPXL"


def tier(drop, ladder):
    t = 0.0
    for x, sz in ladder:
        if drop >= x - 1e-12:
            t = sz
    return t


def sim(d, lo, hi, ladder, trig, cap, trim, forced_days=None):
    """Returns dates, equity, ETF weight, buy dates (with % bought). forced_days: {date_index: pct} replaces triggers."""
    idx = d["close"].index[(d["close"].index >= lo) & (d["close"].index <= hi)]
    o, c = d["open"]["SPY"][idx].values, d["close"]["SPY"][idx].values
    eo, ec = d["open"][INSTR][idx].values, d["close"][INSTR][idx].values
    bil = d["close"]["BIL"][idx].pct_change().fillna(0).values
    cash, sh = E0, 0.0
    eq, w, buys = np.zeros(len(idx)), np.zeros(len(idx)), {}
    for i in range(len(idx)):
        cash *= 1 + bil[i]
        bought = 0.0
        if forced_days is None and i > 0:
            if trig in ("gap", "either"):
                p = tier((c[i - 1] - o[i]) / c[i - 1], ladder)
                if p > 0:
                    cash, sh, got = buy(cash, sh, p, eo[i], cap)
                    bought += got
        if forced_days is None and i > 0 and trig in ("close", "either"):
            p = tier((c[i - 1] - c[i]) / c[i - 1], ladder)
            if trig == "either":
                p = max(0.0, p - bought)          # top up to the close-depth tier
            if p > 0:
                cash, sh, got = buy(cash, sh, p, ec[i], cap)
                bought += got
        if forced_days is not None and i in forced_days:
            cash, sh, got = buy(cash, sh, forced_days[i], ec[i], cap)
            bought += got
        if bought:
            buys[i] = bought
        val = sh * ec[i]
        e = cash + val
        if trim == "to_cap" and val > 1.25 * cap * e:
            sell = (val - cap * e) / ec[i]
            cash += sell * (ec[i] * (1 - BPS) - CPS)
            sh -= sell
            val = sh * ec[i]
            e = cash + val
        eq[i], w[i] = e, val / e
    return idx, eq, w, buys


def buy(cash, sh, pct, px, cap):
    e = cash + sh * px
    room = max(0.0, cap * e - sh * px)
    dollars = min(pct * e, room, cash)
    if dollars < 25:
        return cash, sh, 0.0
    sh += dollars / (px * (1 + BPS) + CPS)
    return cash - dollars, sh, dollars / e


def static(d, lo, hi, wt):
    idx = d["close"].index[(d["close"].index >= lo) & (d["close"].index <= hi)]
    r = d["close"][INSTR][idx].pct_change().fillna(0).values
    b = d["close"]["BIL"][idx].pct_change().fillna(0).values
    m = idx.to_period("M")
    eq, cur = np.zeros(len(idx)), E0
    w = wt
    for i in range(len(idx)):
        if i > 0:
            cur = cur * (1 + w * r[i] + (1 - w) * b[i])
            w = w * (1 + r[i]) / (1 + w * r[i] + (1 - w) * b[i])
            if m[i] != m[i - 1]:
                cur -= abs(w - wt) * cur * 2e-4
                w = wt
        eq[i] = cur
    return idx, eq


def stats(idx, eq):
    yrs = (idx[-1] - idx[0]).days / 365.25
    mdd, uw = dd_stats(eq)
    return dict(cagr=(eq[-1] / eq[0]) ** (1 / yrs) - 1, maxdd=mdd, underwater=uw, final=eq[-1])


def main(daily_path, outdir):
    out = Path(outdir)
    d = load_daily(daily_path)
    rows = []
    bh = {}
    for wn, (lo, hi) in WIN.items():
        idx = d["close"].index[(d["close"].index >= lo) & (d["close"].index <= hi)]
        s = d["close"]["SPY"][idx].values
        bh[wn] = stats(idx, E0 * s / s[0])
    for lad, trig, cap, trim in itertools.product(LADDERS, TRIGGERS, CAPS, TRIMS):
        for wn, (lo, hi) in WIN.items():
            idx, eq, w, buys = sim(d, pd.Timestamp(lo), pd.Timestamp(hi), LADDERS[lad], trig, cap, trim)
            rows.append(dict(ladder=lad, trigger=trig, cap=cap, trim=trim, window=wn, buys=len(buys),
                             avg_weight=w.mean(), end_weight=w[-1], **stats(idx, eq),
                             spy_cagr=bh[wn]["cagr"], spy_maxdd=bh[wn]["maxdd"]))
    res = pd.DataFrame(rows)
    res.to_csv(out / "design_grid.csv", index=False, float_format="%.5g")
    tr = res[res.window == "TRAIN"]
    ok = tr[tr.maxdd >= 1.2 * bh["TRAIN"]["maxdd"]]
    pick = ok.sort_values(["cagr"], ascending=False).iloc[0]
    print("chosen", pick.to_dict())
    # benchmarks for the chosen rule in each window
    rng = np.random.default_rng(1117)
    bench, curves = [], {}
    lad, trig, cap, trim = pick.ladder, pick.trigger, pick.cap, pick.trim
    for wn, (lo, hi) in list(WIN.items()) + [("SEG-A continuous", ("2016-01-04", "2024-10-31"))]:
        lo, hi = pd.Timestamp(lo), pd.Timestamp(hi)
        idx, eq, w, buys = sim(d, lo, hi, LADDERS[lad], trig, cap, trim)
        n = len(idx)
        nb = max(1, len(buys))
        tot = sum(buys.values())
        k = max(1, n // nb)
        sched = {i: tot / nb for i in range(1, n, k)[:nb]}
        _, eqs, ws, _ = sim(d, lo, hi, LADDERS[lad], trig, cap, trim, forced_days=sched)
        rnd = []
        for _ in range(100):
            days = rng.choice(np.arange(1, n), nb, replace=False)
            rnd.append(sim(d, lo, hi, LADDERS[lad], trig, cap, trim, forced_days={int(i): tot / nb for i in days})[1][-1])
        _, eqst = static(d, lo, hi, cap)
        s = d["close"]["SPY"][idx].values
        eqb = E0 * s / s[0]
        v = idx >= pd.Timestamp(WIN["VALID"][0])
        for lab, e in (("dip rule", eq), ("same $ on a schedule", eqs), ("static SPXL at cap", eqst),
                       ("SPY buy-and-hold", eqb)):
            bench.append(dict(window=wn, book=lab, **stats(idx, e)))
            curves[(wn, lab)] = (idx, e)
            if wn == "SEG-A continuous":   # the VALID years inside a run that started in 2016 (warm book)
                bench.append(dict(window="VALID inside the 2016 run", book=lab, **stats(idx[v], e[v])))
        bench.append(dict(window=wn, book="same $ on random days (100 draws, mean final)", final=np.mean(rnd),
                          pct_rule_beats=np.mean(eq[-1] > np.array(rnd))))
        bench.append(dict(window=wn, book="dip rule: buys / avg weight / end weight", cagr=len(buys),
                          maxdd=w.mean(), underwater=w[-1]))
        if wn == "SEG-B":
            pd.DataFrame({"date": idx, "equity": eq, "weight": w}).to_csv(out / "rule_segB_daily.csv", index=False)
    pd.DataFrame(bench).to_csv(out / "design_benchmarks.csv", index=False, float_format="%.5g")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw={"width_ratios": [5, 1.4]})
    colors = {"dip rule": "#1f6feb", "same $ on a schedule": "#8b949e", "static SPXL at cap": "#d29922",
              "SPY buy-and-hold": "#2da44e"}
    for ax, wn in zip(axes, ["SEG-A continuous", "SEG-B"]):
        for lab, col in colors.items():
            i, e = curves[(wn, lab)]
            ax.plot(i, e / 1000, color=col, lw=1.6 if lab == "dip rule" else 1.0, label=lab)
        ax.set_title(wn, fontsize=9)
        ax.tick_params(labelsize=7)
    axes[0].set_ylabel("account equity (USD k, from 100k)")
    import matplotlib.dates as mdates
    axes[1].xaxis.set_major_locator(mdates.MonthLocator(bymonth=[3, 9]))
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%y-%m"))
    axes[0].legend(fontsize=7, frameon=False)
    fig.suptitle(f"Chosen rule (TRAIN pick): {trig} trigger, ladder {lad}, cap {cap:.0%} of equity in SPXL, trim {trim}; "
                 "real data, costs in, idle cash in T-bills, from USD 100k in each segment. Educational only - not financial advice.",
                 fontsize=8.5)
    fig.tight_layout()
    fig.savefig(out / "design_equity.png", dpi=110)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
