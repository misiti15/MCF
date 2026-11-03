"""eu1103/universe step 2: universe buckets and universe rules on the two-year trades of score2y.py (8 busiest live
setups, TRAIN / VALID, costs in). Rules were written down before this script was run (NOTES.md "Pre-declared rules").
Point-in-time symbol attributes from lib.daily() (locked block dropped by the loader, never read):
  dATR% = atr_d / price at the trade; dollar-ATR = adv20 x ATR% (the day's dollars moved), ranked per date among the
  names that pass the live floor; move-history = share of the previous 60 open sessions on which the name was a
  top-50 |open->close| / ATR(14) mover among ADV >= $50M names; idiosyncratic = max residual (ex-SPY) daily-return
  correlation with the 11 sector SPDRs < 0.15, fitted on TRAIN dates only (applied unchanged to VALID).
Random control = the same symbol-day's mean production R over every bar 09:50-15:00 (same side / geometry).
    python analyze2y.py <scratch> -> analyze2y_out.txt, rules2y.csv here
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research/history2y")]
import lib  # noqa: E402

S = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
SPDR = "XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC".split()
FLOOR = {"heat_fade_short-FD": 125e6, "RW2-exhaustion-noon-adv150-short-FD": 150e6, "L3-gap-slope-fromopen-FD": 0.0}


def load():
    T = pd.concat([pd.read_parquet(p) for p in sorted((S / "t2y").glob("20??-??.parquet"))], ignore_index=True)
    C = pd.concat([pd.read_parquet(p) for p in sorted((S / "t2y").glob("*_ctrl.parquet"))], ignore_index=True)
    T["date"] = pd.to_datetime(T["date"]).dt.date
    C["date"] = pd.to_datetime(C["date"]).dt.date
    T = T.merge(C, on=["date", "symbol", "side", "geom"], how="left")
    T["floor"] = T.setup.map(FLOOR).fillna(95e6)
    return T


def attrs(T):
    d = lib.daily().sort_values(["symbol", "date"]).reset_index(drop=True)
    pc = d.groupby("symbol").close.shift()
    tr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs()))
    d["atr"] = tr.groupby(d.symbol).transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
    d["mv"] = (d.close - d.open).abs() / d.atr
    d["adv"] = d.adv20
    ok = (d.adv >= 50e6) & d.mv.notna()
    d["rk"] = np.where(ok, d.groupby("date").mv.rank(ascending=False), np.nan)
    d["top50"] = (d.rk <= 50).astype(float)
    d["elig"] = ok.astype(float)
    g = d.groupby("symbol")
    d["mh60"] = (g.top50.transform(lambda s: s.shift(1).rolling(60, min_periods=20).sum()) /
                 g.elig.transform(lambda s: s.shift(1).rolling(60, min_periods=20).sum()).replace(0, np.nan))
    T = T.merge(d[["symbol", "date", "mh60"]], on=["symbol", "date"], how="left")
    # sector / idiosyncratic from TRAIN dates only
    tr_dates = set(T.loc[T.split == "TRAIN", "date"])
    d["ret"] = g.close.pct_change()
    R = d[d.date.isin(tr_dates)].pivot(index="date", columns="symbol", values="ret")
    spy = R["SPY"]
    beta = R.apply(lambda s: s.cov(spy) / spy.var())
    res = R - np.outer(spy.fillna(0), beta.fillna(0))
    corr = pd.DataFrame({e: res.corrwith(res[e]) for e in SPDR if e in res})
    sec = corr.idxmax(axis=1)
    sec[corr.max(axis=1) < 0.15] = "none"
    for e in SPDR:
        sec[e] = "fund"
    T["sector"] = T.symbol.map(sec).fillna("n/a")
    u = pd.read_csv(ROOT / "data/universe.csv")
    import importlib.util
    spec = importlib.util.spec_from_file_location("lb", HERE / "live_buckets.py")
    lb = importlib.util.module_from_spec(spec)
    sys.argv = [sys.argv[0], str(S)]
    spec.loader.exec_module(lb)
    kind = u.set_index("symbol").name.map(lb.kind)
    T["kind"] = T.symbol.map(kind).fillna("stock")
    T.loc[T.kind != "stock", "sector"] = "fund"
    T["etb"] = T.symbol.map(u.set_index("symbol").easy_to_borrow.astype(str)).fillna("?")
    T["atrp"] = T.atr_d / T.px * 100
    T["datr"] = T.adv20 * T.atrp
    return T


def stat(x, col="r"):
    if not len(x):
        return dict(n=0)
    ds = x.groupby("date")[col].agg(["sum", "size"])
    mu = x[col].mean()
    se = np.sqrt(((ds["sum"] - ds["size"] * mu) ** 2).sum()) / len(x) if len(ds) > 1 else np.nan
    return dict(n=len(x), per_day=round(len(x) / max(1, len(ds)), 1), avgR=round(mu, 4), t=round(mu / se, 2) if se > 0 else np.nan)


def bucket(T, col, label):
    rows = []
    for (sp, k), x in T.groupby(["split", col], observed=True):
        a, b = stat(x), stat(x, "exc")
        rows.append(dict(split=sp, bucket=str(k), n=a["n"], avgR=a["avgR"], t=a["t"], vs_rand=b["avgR"], vs_rand_t=b["t"],
                         excS=round(x.excS.mean(), 4)))
    return f"\n== {label}\n" + pd.DataFrame(rows).to_string(index=False)


def main():
    T = attrs(load())
    T["exc"] = T.r - T.rc
    T["excS"] = T.r - T.groupby(["setup", "split"]).r.transform("mean")
    base = T[T.adv20 >= T.floor].copy()          # the live universe floor per setup
    base["excS"] = base.r - base.groupby(["setup", "split"]).r.transform("mean")
    lines = ["Educational only - not financial advice. Two-year lab trades (8 busiest live setups, production costs, TRAIN "
             "2024-10 + 2025-03..12, VALID 2026-01..03 + 07..09-15; locked block never loaded). vs_rand = trade R minus the same "
             "symbol-day random-entry R; excS = R minus the setup's split mean (setup mix removed).",
             "\nPer setup at its live floor:\n" + pd.DataFrame([dict(setup=s, split=sp, **stat(x), vs_rand=round(x.exc.mean(), 4))
                                                               for (s, sp), x in base.groupby(["setup", "split"])]).to_string(index=False)]
    T["adv_b"] = pd.cut(T.adv20, [0, 50e6, 95e6, 150e6, 300e6, 1e9, 1e14], labels=["20-50M", "50-95M", "95-150M", "150-300M", "300M-1B", ">1B"])
    for c, lab in (("adv_b", "ADV bucket (no floor; < live floor rows are survivor-biased lab names)"),):
        lines.append(bucket(T, c, lab))
    base["px_b"] = pd.cut(base.px, [0, 10, 20, 50, 100, 250, 1e9], labels=["<10", "10-20", "20-50", "50-100", "100-250", ">250"])
    base["atr_b"] = pd.cut(base.atrp, [0, 2, 3, 4, 6, 10, 1e3], labels=["<2%", "2-3%", "3-4%", "4-6%", "6-10%", ">10%"])
    base["mh_b"] = pd.cut(base.mh60, [-1, 0, 0.02, 0.05, 0.1, 1.1], labels=["0", "<2%", "2-5%", "5-10%", ">=10%"])
    base["sidel"] = base.side
    for c, lab in (("px_b", "price"), ("atr_b", "ATR% of price"), ("kind", "stock / ETF / leveraged"), ("etb", "ETB flag (10-05 snapshot)"),
                   ("sector", "sector (TRAIN-fitted; none = idiosyncratic)"), ("mh_b", "move history (top-50 mover share, prior 60 sessions)")):
        lines.append(bucket(base, c, lab))
    for c in ("atr_b", "sector"):
        for s in ("long", "short"):
            lines.append(bucket(base[base.side == s], c, f"{c} x {s}"))
    # ---------------------------------------------------------------- pre-declared universe rules
    base["datr_rank"] = base.groupby("date").datr.rank(ascending=False, method="first")
    # rank among ALL names passing 95M that day (not only traded names): use the daily table
    d = lib.daily()
    pcl = d.sort_values(["symbol", "date"])
    rules = {
        "S1 top-300 dollar-ATR": None, "S1 top-500 dollar-ATR": None, "S1 top-800 dollar-ATR": None,
        "S2 move history >= 3% (prior 60d)": base.mh60 >= 0.03,
        "S3 ATR% >= 3": base.atrp >= 3,
        "S4 drop idiosyncratic (sector none)": base.sector != "none",
        "S5 ADV >= 300M": base.adv20 >= 300e6,
    }
    # point-in-time dollar-ATR rank among all lab names with adv20 >= 95M on the date (ATR from daily, prior 14d)
    pcl["pc"] = pcl.groupby("symbol").close.shift()
    tr = np.maximum(pcl.high - pcl.low, np.maximum((pcl.high - pcl.pc).abs(), (pcl.low - pcl.pc).abs()))
    pcl["atr"] = tr.groupby(pcl.symbol).transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
    pcl["datr"] = pcl.adv20 * pcl.atr / pcl.pc
    pcl = pcl[pcl.adv20 >= 95e6]
    pcl["rk"] = pcl.groupby("date").datr.rank(ascending=False)
    base = base.merge(pcl[["symbol", "date", "rk"]], on=["symbol", "date"], how="left")
    for n in (300, 500, 800):
        rules[f"S1 top-{n} dollar-ATR"] = base.rk <= n
    for k in list(rules):
        if k.startswith("S2"):
            rules[k] = base.mh60 >= 0.03
        elif k.startswith("S3"):
            rules[k] = base.atrp >= 3
        elif k.startswith("S4"):
            rules[k] = base.sector != "none"
        elif k.startswith("S5"):
            rules[k] = base.adv20 >= 300e6
    rows = []
    for name, keep in rules.items():
        keep = keep.fillna(False).to_numpy(bool)
        for sp in ("TRAIN", "VALID"):
            m = (base.split == sp).to_numpy()
            for s in ["ALL"] + sorted(base.setup.unique()):
                ms = m & ((base.setup == s).to_numpy() if s != "ALL" else True)
                k, dr = base[ms & keep], base[ms & ~keep]
                a, b0 = stat(k), stat(base[ms])
                # kept minus dropped, day-clustered: per-date difference of means
                dd = pd.concat([k.groupby("date").r.mean().rename("k"), dr.groupby("date").r.mean().rename("d")], axis=1).dropna()
                diff = dd.k - dd.d
                gd = k.groupby("date").r.sum()
                rows.append(dict(rule=name, split=sp, setup=s, n_base=b0["n"], n_kept=a["n"], kept_share=round(a["n"] / max(1, b0["n"]), 3),
                                 base_R=b0["avgR"], kept_R=a.get("avgR"), dropped_R=round(dr.r.mean(), 4) if len(dr) else np.nan,
                                 kept_vs_rand=round(k.exc.mean(), 4) if len(k) else np.nan,
                                 kd_diff=round(diff.mean(), 4) if len(diff) else np.nan,
                                 kd_t=round(diff.mean() / (diff.std() / np.sqrt(len(diff))), 2) if len(diff) > 2 else np.nan,
                                 green_kept=round((gd > 0).mean(), 3) if len(gd) else np.nan,
                                 green_base=round((base[ms].groupby("date").r.sum() > 0).mean(), 3)))
    L = T[(T.adv20 >= 50e6) & (T.adv20 < T.floor)]
    for sp in ("TRAIN", "VALID"):
        for s in ["ALL"] + sorted(T.setup.unique()):
            ms = (L.split == sp) & ((L.setup == s) if s != "ALL" else True)
            b0 = base[(base.split == sp) & ((base.setup == s) if s != "ALL" else True)]
            a = stat(L[ms])
            rows.append(dict(rule="L1 floor 50M: ADDED names only (50M..floor)", split=sp, setup=s, n_base=len(b0), n_kept=a["n"],
                             kept_share=round(a["n"] / max(1, len(b0)), 3), base_R=round(b0.r.mean(), 4), kept_R=a.get("avgR"),
                             kept_vs_rand=round(L[ms].exc.mean(), 4) if a["n"] else np.nan))
    R = pd.DataFrame(rows)
    R.to_csv(HERE / "rules2y.csv", index=False)
    lines.append("\n== Universe rules (ALL = pooled 8 setups; kd = kept minus dropped per session, day-clustered)")
    lines.append(R[R.setup == "ALL"].to_string(index=False))
    lines.append("\n== per setup, VALID")
    lines.append(R[(R.setup != "ALL") & (R.split == "VALID")][["rule", "setup", "n_base", "kept_share", "base_R", "kept_R", "dropped_R", "kd_diff", "kd_t"]].to_string(index=False))
    lines.append("\n== per setup, TRAIN")
    lines.append(R[(R.setup != "ALL") & (R.split == "TRAIN")][["rule", "setup", "n_base", "kept_share", "base_R", "kept_R", "dropped_R", "kd_diff", "kd_t"]].to_string(index=False))
    (HERE / "analyze2y_out.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
