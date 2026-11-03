"""eu1103/open Part 3: the 09:50-09:55 dip / spike and the opposite swing (PLAN.md, 8 pre-declared configs O1..O8).
m = close(09:50 bar)/open - 1; b = (close(09:55) - close(09:50)) / daily ATR; entry at the 09:55 close, t1s1, flat 15:55.
Lab frames via lib.load_month (locked block refused). Costs gates.prod_r with the time-of-day multiplier (1.4x at 09:55).
    python reversal.py <scratch>   -> <scratch>/rev_trades.parquet, prints the report
Educational only - not financial advice."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y")]
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
S = Path(sys.argv[1])
TRAIN = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)]
VALID = ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
for mo in TRAIN + VALID:
    assert mo not in lib.LOCKED_MONTHS
COLS = ["symbol", "date", "tod", "close", "fromOpen", "atr_d", "adv20"] + [
    f"{k}_{s}_t1s1" for k in ("r", "win") for s in ("long", "short")]
CONFIGS = {  # name: (side, morning sign, bar sign, k, spy filter)
    "O1-dip-upmorning-k20-long": ("long", 1, -1, 0.20, None),
    "O2-dip-upmorning-k35-long": ("long", 1, -1, 0.35, None),
    "O3-spike-dnmorning-k20-short": ("short", -1, 1, 0.20, None),
    "O4-spike-dnmorning-k35-short": ("short", -1, 1, 0.35, None),
    "O5-dip-dnmorning-k20-long": ("long", -1, -1, 0.20, None),
    "O6-spike-upmorning-k20-short": ("short", 1, 1, 0.20, None),
    "O7-dip-upmorning-k20-spyup-long": ("long", 1, -1, 0.20, 1),
    "O8-spike-dnmorning-k20-spydn-short": ("short", -1, 1, 0.20, -1),
}


def prod(f, side, tod):
    return G.prod_r(f[f"r_{side}_t1s1"].to_numpy(float), f[f"win_{side}_t1s1"].to_numpy(float),
                    f["close"].to_numpy(float), f["atr_d"].to_numpy(float), "t1s1", tod=tod)


def month(mo, split):
    f = lib.load_month(mo, columns=COLS)
    if split == "VALID":
        f = f[f["date"].astype(str) <= "2026-09-15"]
    f = f[(f.adv20 >= 95e6) & (f.atr_d > 0) & (f.close >= 5)].copy()
    f["symbol"] = f["symbol"].astype(str)
    ctx = lib.load_context(mo)
    spy = ctx[ctx.tod == 955].set_index("date")["spy_fo"]
    # day-matched random: mean prod R of every 09:50-15:00 bar of the symbol-day, per side
    rc = {}
    for side in ("long", "short"):
        ok = np.isfinite(f[f"r_{side}_t1s1"].to_numpy(float))
        g = f.loc[ok, ["date", "symbol"]].assign(r=prod(f.loc[ok], side, f.loc[ok, "tod"].to_numpy(float)))
        rc[side] = g.groupby(["date", "symbol"]).r.mean()
    a = f[f.tod == 950].set_index(["date", "symbol"])
    b = f[f.tod == 955].set_index(["date", "symbol"])
    j = b.join(a[["close", "fromOpen"]], rsuffix="_950", how="inner")
    j["m"] = j["fromOpen_950"]
    j["b"] = (j["close"] - j["close_950"]) / j["atr_d"]
    j["spy_fo"] = j.index.get_level_values(0).map(spy)
    out = []
    for side in ("long", "short"):
        ok = np.isfinite(j[f"r_{side}_t1s1"].to_numpy(float))
        x = j[ok].copy()
        x["r"] = prod(x, side, np.full(len(x), 955.0))
        x["rc"] = rc[side].reindex(x.index).to_numpy()
        x["side"] = side
        x["st"] = x.groupby(level=0).r.transform("mean")      # same-time control: every eligible name, same side, 09:55
        out.append(x.reset_index()[["date", "symbol", "side", "m", "b", "spy_fo", "r", "rc", "st"]])
    t = pd.concat(out, ignore_index=True)
    t["split"] = split
    return t


def main():
    p = S / "rev_base.parquet"
    if p.exists():
        base = pd.read_parquet(p)
    else:
        base = pd.concat([month(mo, sp) for sp, ms in (("TRAIN", TRAIN), ("VALID", VALID)) for mo in ms], ignore_index=True)
        base.to_parquet(p, index=False)
    base["date"] = pd.to_datetime(base["date"]).dt.date
    d = lib.daily()
    spy = d[d.symbol == "SPY"].set_index("date")
    oc = (spy.close / spy.open - 1) * 100
    base["dtype"] = base["date"].map(lambda x: "up" if oc.get(x, 0) > 0.25 else ("down" if oc.get(x, 0) < -0.25 else "quiet"))
    rows, trades = [], []
    for name, (side, ms, bs, k, sf) in CONFIGS.items():
        x = base[base.side == side]
        msk = (np.sign(x.m) == ms) & ((x.b * bs) >= k)
        if sf is not None:
            msk &= np.sign(x.spy_fo) == sf
        t = x[msk].assign(config=name)
        trades.append(t)
        for sp in ("TRAIN", "VALID", "ALL"):
            u = t if sp == "ALL" else t[t.split == sp]
            nd = base[base.split == sp].date.nunique() if sp != "ALL" else base.date.nunique()
            if not len(u):
                rows.append(dict(config=name, split=sp, n=0)); continue
            day = u.groupby("date").r.sum()
            dm = u.groupby("date").r.mean()
            tday = dm.mean() / (dm.std(ddof=1) / np.sqrt(len(dm))) if len(dm) > 2 else np.nan
            best = day.idxmax()
            wo = u[u.date != best].r.mean()
            diff_st = (u.r - u.st).groupby(u.date).mean()
            diff_rc = (u.r - u.rc).groupby(u.date).mean()
            rr = dict(config=name, split=sp, n=len(u), sessions=nd, days_with=u.date.nunique(), per_session=len(u) / nd,
                      avgR=u.r.mean(), totR_per_session=u.r.sum() / nd, day_t=tday, wo_best=wo,
                      best_share=day.max() / day.sum() if day.sum() > 0 else np.nan,
                      vs_sametime=diff_st.mean(), vs_sametime_t=diff_st.mean() / (diff_st.std(ddof=1) / np.sqrt(len(diff_st))),
                      vs_random=diff_rc.mean(), live_friction=u.r.mean() - 0.041)
            for dt in ("up", "down", "quiet"):
                v = u[u.dtype == dt]
                rr[f"{dt}_n"], rr[f"{dt}_R"] = len(v), v.r.mean() if len(v) else np.nan
            rows.append(rr)
    r = pd.DataFrame(rows)
    r.to_csv(ROOT / "research/bdi/eu1103/open/reversal_results.csv", index=False, float_format="%.4f")
    pd.concat(trades).to_parquet(S / "rev_trades.parquet", index=False)
    pd.set_option("display.width", 250)
    print("Educational only - not financial advice.")
    print(r[["config", "split", "n", "per_session", "avgR", "totR_per_session", "day_t", "wo_best", "best_share",
             "vs_sametime", "vs_sametime_t", "vs_random", "up_R", "down_R", "quiet_R"]].round(3).to_string(index=False))
    # descriptive: all names, by b bucket and morning sign (no config, context for the owner's question)
    base["bb"] = pd.cut(base.b, [-9, -0.35, -0.2, -0.1, 0, 0.1, 0.2, 0.35, 9])
    base["msign"] = np.where(base.m > 0, "up-morning", "down-morning")
    print("\nDescriptive (not configs): avg R at the 09:55 close by 09:50-09:55 bar move (ATR) x morning sign, ALL splits")
    print(base.pivot_table(index="bb", columns=["msign", "side"], values="r", aggfunc="mean", observed=True).round(3).to_string())
    print(base.pivot_table(index="bb", columns=["msign", "side"], values="r", aggfunc="size", observed=True).to_string())


if __name__ == "__main__":
    main()
