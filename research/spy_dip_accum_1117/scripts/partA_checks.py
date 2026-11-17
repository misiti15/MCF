"""Part A finalists: one-big-period removals, per-year share of excess, SPY dip edge vs leverage, equity curves.
Usage: python partA_checks.py DAILY.parquet OUTDIR. Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ETFS, SEG  # noqa: E402
from partA import (E0, FAM_D, FAM_M, account, daily_triggers, dd_stats, cagr, load_daily, minute_fills,  # noqa: E402
                   outcomes, xirr_many)

FINALISTS = [("gap", 0.01), ("dayclose", 0.01), ("wkclose", 0.01), ("wkhigh", 0.01),
             ("m_gap", 0.01), ("m_1015", 0.01), ("m_1030", 0.01), ("m_pm1530", 0.01)]
WINDOWS = {"A": {"no_2020": ("2020-02-19", "2020-12-31"), "no_2022": ("2022-01-01", "2022-12-31"),
                 "no_2018q4": ("2018-10-01", "2018-12-31")},
           "B": {"no_apr2025": ("2025-03-03", "2025-05-30")}}
RNG = np.random.default_rng(11172)


def main(daily_path, outdir):
    out = Path(outdir)
    d = load_daily(daily_path)
    rows, yrows = [], []
    for seg in ["A", "B"]:
        idx, trig = daily_triggers(d, seg)
        tyr = np.asarray((idx - idx[0]).days / 365.25)
        bil = d["close"]["BIL"].reindex(idx).pct_change().fillna(0).values
        closes = {s: d["close"][s].reindex(idx) for s in ETFS}
        fills = {"open": {s: d["open"][s].reindex(idx).values for s in ETFS},
                 "close": {s: closes[s].values for s in ETFS}}
        if seg == "B":
            spy_px, pcs, mf = minute_fills(d, idx)
            for k in FAM_M:
                trig[(k, 0.01)] = (spy_px[k] <= pcs * 0.99).fillna(False).values.astype(bool)
                fills[k] = {s: mf[(k, s)] for s in ETFS}
        curves = {}
        for fam, x in FINALISTS:
            if fam.startswith("m_") and seg == "A":
                continue
            ft = FAM_D.get(fam, fam)
            elig = np.isfinite(fills[ft]["SPY"])
            res = {}
            for s in ("SPXL", "SPY"):
                sj, mu = outcomes(fills[ft][s], closes[s], "hold", ft != "close")
                res[s] = (sj, mu)
            for wname, win in [("all", None)] + list(WINDOWS[seg].items()):
                keep = elig.copy()
                if win:
                    keep &= ~((idx >= pd.Timestamp(win[0])) & (idx <= pd.Timestamp(win[1])))
                b = np.nonzero(trig[(fam, x)] & keep)[0]
                pool = np.nonzero(keep)[0]
                row = dict(seg=seg, family=fam, x=x, window=wname, n_buys=len(b))
                for s in ("SPXL", "SPY"):
                    sj, mu = res[s]
                    rr = xirr_many(tyr[b], tyr[sj[b]], mu[b])[0]
                    dr = np.array([np.sort(RNG.choice(pool, len(b), replace=False)) for _ in range(500)])
                    rd = xirr_many(tyr[dr], tyr[sj[dr]], mu[dr])
                    row[f"xirr_{s}"] = rr
                    row[f"xirr_rand_{s}"] = rd.mean()
                    row[f"pct_beaten_{s}"] = (rr > rd).mean()
                rows.append(row)
                if wname == "all":
                    # per-year share of the local excess (dip-day multiple minus nearby days' multiple, SPXL)
                    sj, mu = res["SPXL"]
                    # local baseline: mean multiple of eligible sessions within +-10 of the buy (same time to the end)
                    base = np.array([np.nanmean(mu[pool[(pool >= i - 10) & (pool <= i + 10) & (pool != i)]]) for i in b])
                    ex = pd.Series(mu[b] - base, index=idx[b].year)
                    tot = ex.sum()
                    for yr, v in ex.groupby(level=0).sum().items():
                        yrows.append(dict(seg=seg, family=fam, x=x, year=yr, n=int((ex.index == yr).sum()),
                                          excess_per_dollar_sum=v, share=v / tot))
            if (fam, x) in (("gap", 0.01), ("dayclose", 0.01), ("m_1015", 0.01)):
                b = np.nonzero(trig[(fam, x)] & elig)[0]
                pool = np.nonzero(elig)[0]
                k = max(1, len(pool) // len(b))
                sched = pool[0::k][:len(b)]
                rnd = np.sort(RNG.choice(pool, len(b), replace=False))
                D = 500.0
                for lab, bi, s in (("dip SPXL", b, "SPXL"), ("schedule SPXL", sched, "SPXL"),
                                   ("random days SPXL", rnd, "SPXL"), ("dip SPY", b, "SPY")):
                    sj, _ = outcomes(fills[ft][s], closes[s], "hold", ft != "close")
                    eq, _, _, _ = account(idx, bi, sj, fills[ft][s], closes[s].values, bil, D)
                    # P/L on deployed dollars: equity minus the cash it would have had without buying
                    cash_only = E0 * np.cumprod(1 + bil)
                    curves[(fam, lab)] = eq - cash_only
                    if (fam, x) == ("gap", 0.01) or (seg == "B" and fam == "m_1015"):
                        mdd, uw = dd_stats(eq)
                        rows.append(dict(seg=seg, family=fam, x=x, window="account_" + lab, acct_cagr=cagr(eq, idx),
                                         acct_maxdd=mdd, acct_underwater=uw, n_buys=len(bi)))
        # plot: P/L of the $500 slices vs benchmarks, and SPY buy-and-hold of $100k for scale
        fig, ax = plt.subplots(1, 1, figsize=(10, 5.2))
        fam = "gap"
        cols = {"dip SPXL": "#1f6feb", "schedule SPXL": "#8b949e", "random days SPXL": "#d29922", "dip SPY": "#2da44e"}
        for lab, col in cols.items():
            ax.plot(idx, curves[(fam, lab)], color=col, lw=1.6 if lab == "dip SPXL" else 1.1, label=lab)
        ax.axhline(0, color="#57606a", lw=0.6)
        n = int(trig[("gap", 0.01)].sum())
        ax.set_title(f"SEG-{seg} {idx[0].date()}..{idx[-1].date()}: P/L of \\$500 buys (gap-down >= 1% at the open, "
                     f"{n} buys) vs the same \\$ on a schedule / random days / SPY\n"
                     "Real ETF data, costs in, idle cash in T-bills. Educational only - not financial advice.",
                     fontsize=9)
        ax.set_ylabel("P/L vs holding cash (\\$)")
        ax.legend(fontsize=8, frameon=False)
        fig.tight_layout()
        fig.savefig(out / f"equity_seg{seg}.png", dpi=110)
        plt.close(fig)
    pd.DataFrame(rows).to_csv(out / "partA_checks.csv", index=False, float_format="%.5g")
    pd.DataFrame(yrows).to_csv(out / "partA_years.csv", index=False, float_format="%.5g")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
