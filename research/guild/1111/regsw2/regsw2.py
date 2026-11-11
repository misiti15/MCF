"""REGSW-2 (plan PLAN.md, frozen 2026-11-11 08:45 ET; Skeptic audit skeptic-20261111-0902-3 applied). Stage 1 (--base-only):
the WINNING base, chosen on lab TRAIN gross and live net only (VALID / FWD outcomes not read), printed and frozen to
base.csv; committed before stage 2 scores any switch.
  base: setups in research/compassbf/trades_tagged.parquet (2y lab lists with point-in-time compass tags) with
    (a) TRAIN (<= 2025-09-30) mean GROSS R > 0 and (b) live paper net avg R > 0 over >= 20 trades (whatworks_all.csv,
    journals to 11-10, trades pooled over accounts). Earnings-blackout days (+-4 sessions) are removed from the base.
    The live check is IN-SAMPLE by construction (Skeptic): reported, labelled, never evidence.
    python regsw2.py --base-only          Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
HERE = Path(__file__).resolve().parent; R = HERE.parent
sys.path.insert(0, "/home/user/MCF")
from mcf.research.generator import data as GD
TR_END = "2025-09-30"


def base():
    T = pd.read_parquet(R / "compassbf/trades_tagged.parquet", columns=["setup", "side", "symbol", "date", "tod", "r", "gross"])
    assert not ((T.date >= "2024-11-01") & (T.date <= "2025-02-28")).any()
    assert GD.EARN.exists(), "earnings file missing (blackout would silently be all False)"
    tr = T[T.date <= TR_END].groupby("setup").agg(train_n=("gross", "size"), train_gross=("gross", "mean"), train_net=("r", "mean"))
    W = pd.read_csv(R / "whatworks/whatworks_all.csv")
    W["tot"] = W.avg_r * W.n
    lv = W.groupby("setup").agg(live_n=("n", "sum"), live_tot=("tot", "sum"), accounts=("account", lambda a: ",".join(sorted(set(a)))))
    lv["live_avg"] = lv.live_tot / lv.live_n
    J = tr.join(lv, how="inner")
    J["in_base"] = (J.train_gross > 0) & (J.live_avg > 0) & (J.live_n >= 20)
    return T, J.sort_values(["in_base", "train_gross"], ascending=False)


# ------------------------------------------------------------------------------------------- stage 2: switches
VA_END = "2026-10-07"
NPERM = 2000
RNG = np.random.default_rng(20261111)


def spy_days():
    """SPY per session: gap (first 1-min open / prior session's last close - 1; NaN after a > 5-day gap, as
    regsw_rebreak/base.py) and open->close, from the 1-min SIP cache, locked block never read."""
    import pyarrow.dataset as pds
    NY = "America/New_York"; TL0, TL1 = pd.Timestamp("2024-11-01", tz=NY), pd.Timestamp("2025-03-01", tz=NY)
    ix = "__index_level_0__"
    s = pds.dataset("/home/user/MCF/data/cache_hist/1Min/SPY.parquet", format="parquet").to_table(
        filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
    if ix in s.columns: s = s.set_index(ix)
    s.index = pd.DatetimeIndex(s.index).tz_convert(NY); s = s[~s.index.duplicated(keep="last")].sort_index()
    m = s.index.hour * 60 + s.index.minute; s = s[(m >= 570) & (m < 960)]
    g = s.groupby(s.index.date).agg(o=("open", "first"), c=("close", "last"))
    g.index = pd.Index([str(d) for d in g.index], name="date")
    prev_c = g.c.shift(1); gapd = pd.to_datetime(pd.Series(g.index)).diff().dt.days.to_numpy()
    g["gap"] = np.where(gapd <= 5, g.o / prev_c - 1, np.nan)
    g["oc"] = g.c / g.o - 1
    g["mkt"] = np.where(g.oc > 0.0025, "up", np.where(g.oc < -0.0025, "down", "quiet"))
    return g


def switches(B, S):
    side = B.side.to_numpy(); out = {}
    gap = B.date.map(S.gap).to_numpy(float)
    st = np.where(np.nan_to_num(gap) > 0.0025, 1, np.where(np.nan_to_num(gap) < -0.0025, -1, 0))   # score.py th(gap, .0025)
    out["S1 GAP-U"] = ((side < 0) & (st == 1)) | ((side > 0) & (st == -1))
    ck = B.e_checkpoint.to_numpy()
    out["S2 CHK"] = ((side < 0) & (ck == "UP")) | ((side > 0) & (ck == "DOWN"))
    w = B.e_w60.to_numpy()
    out["S3 W60"] = ((side < 0) & (w == "UP-confirmed")) | ((side > 0) & (w == "DOWN-confirmed"))
    fo = B.e_spy_fo.to_numpy(float)
    out["S4 SPYFO"] = ((side < 0) & (fo >= 0.003)) | ((side > 0) & (fo <= -0.003))
    return out


def tday(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 and x.std() > 0 else np.nan


def score_one(B, sw, col, days_all):
    """Excess of switching `sw` off, per day: delta = -sum(R off); within-setup-day control (expected value of a random
    off-set of the same size in the same setup-day) for intraday states; for S1 (whole setup-days off) the control is
    the shared-day permutation null instead (one day permutation shared by all setups per draw)."""
    R = B[col].to_numpy(float); sd = (B.setup + "|" + B.date).to_numpy()
    k = pd.Series(sw.astype(float)).groupby(sd).transform("sum").to_numpy()
    n = pd.Series(1.0, index=range(len(B))).groupby(sd).transform("sum").to_numpy()
    tot = pd.Series(R).groupby(sd).transform("sum").to_numpy()
    delta = -R * sw
    ctrl = -(k / n) * tot / np.where(k > 0, k, 1) * sw          # spreads the setup-day's expected random delta over its off trades
    ex = pd.Series(delta - ctrl).groupby(B.date.to_numpy()).sum().reindex(days_all, fill_value=0.0)
    dl = pd.Series(delta).groupby(B.date.to_numpy()).sum().reindex(days_all, fill_value=0.0)
    return ex, dl


def shared_null(B, sw, col, days_all):
    """S1: day-level state permuted across days (one permutation for all setups); 95th pct of the null delta sum."""
    R = B[col].to_numpy(float); dd = B.date.to_numpy()
    st_day = pd.Series(sw, index=range(len(B))).groupby([dd, B.side.to_numpy()]).max()
    days = np.array(sorted(set(dd))); di = pd.Index(days).get_indexer(dd)
    lo = st_day.xs(1, level=1).reindex(days, fill_value=False).to_numpy() if 1 in st_day.index.get_level_values(1) else np.zeros(len(days), bool)
    sh = st_day.xs(-1, level=1).reindex(days, fill_value=False).to_numpy() if -1 in st_day.index.get_level_values(1) else np.zeros(len(days), bool)
    side = B.side.to_numpy(); res = np.empty(NPERM)
    for i in range(NPERM):
        p = RNG.permutation(len(days))
        off = np.where(side > 0, lo[p][di], sh[p][di])
        res[i] = -(R * off).sum()
    return np.percentile(res, 95), res.mean()


def stage2():
    T, J = base()
    keep = set(pd.read_csv(HERE / "base.csv").setup)
    B = pd.read_parquet(R / "compassbf/trades_tagged.parquet",
                        columns=["setup", "side", "symbol", "date", "tod", "r", "gross", "e_checkpoint", "e_w60", "e_spy_fo"])
    B = B[B.setup.isin(keep)].reset_index(drop=True)
    B = B[~GD._blackout(B.symbol.to_numpy(), B.date.to_numpy())].reset_index(drop=True)
    S = spy_days()
    B["per"] = np.where(B.date <= TR_END, "TRAIN", np.where(B.date <= VA_END, "VALID", "FWD"))
    SW = switches(B, S)
    rows, pers = [], []
    for name, sw in SW.items():
        for per in ("TRAIN", "VALID", "FWD", "ALL"):
            m = (B.per == per).to_numpy() if per != "ALL" else np.ones(len(B), bool)
            b, s_ = B[m].reset_index(drop=True), sw[m]
            days = sorted(b.date.unique())
            r = dict(switch=name, period=per, days=len(days), trades=len(b), off_share=round(s_.mean(), 3))
            for col in ("gross", "r"):
                ex, dl = score_one(b, s_, col, days)
                tag = "g" if col == "gross" else "n"
                r[f"{tag}_delta"] = round(dl.sum(), 1); r[f"{tag}_excess"] = round(ex.sum(), 1); r[f"{tag}_t"] = round(tday(ex), 2)
                r[f"{tag}_wo_best"] = round(ex.sum() - ex.max(), 1)
                if name.startswith("S1"):
                    p95, mu = shared_null(b, s_, col, days)
                    r[f"{tag}_null_mean"] = round(mu, 1); r[f"{tag}_null95"] = round(p95, 1)
                    r[f"{tag}_excess"] = round(dl.sum() - mu, 1)
                    r[f"{tag}_t"] = np.nan          # day-clustered t not defined vs a permutation null; use null95
                if col == "r":
                    mk = pd.Series(ex.to_numpy(), index=days).groupby(pd.Index(days).map(S.mkt)).sum().round(1).to_dict()
                    r["n_excess_by_spy"] = mk
            # per setup (net, per trade)
            if per in ("VALID", "ALL"):
                ex_s = {}
                for su, g in b.groupby("setup"):
                    e, _ = score_one(g.reset_index(drop=True), s_[g.index.to_numpy()], "r", sorted(g.date.unique()))
                    ex_s[su] = e.sum() / len(g)
                v = pd.Series(ex_s); r["setups_better"] = int((v > 0).sum()); r["setups_worse"] = int((v < 0).sum())
                r["worst_setup_per_trade"] = round(v.min(), 4)
                r["by_side"] = {sd: round(float(pd.Series(-b.r.to_numpy() * s_)[(b.side == sd).to_numpy()].sum()), 1) for sd in (1, -1)}
            rows.append(r)
    O = pd.DataFrame(rows)
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)
    print(f"REGSW-2 stage 2: base {len(keep)} setups, {len(B)} trades (blackout removed), {B.date.nunique()} days; "
          f"bar: net excess t >= 2.74 (BAR90, lineage N 103) and the plan's other conditions")
    print(O.to_string(index=False))
    O.to_csv(HERE / "regsw2_results.csv", index=False)
    print("S1's excess = delta - shared-day permutation mean (Skeptic); pass on S1 needs delta > null95 in TRAIN and VALID.")
    print("ATR units = 0.25 x R units on these lists (R = 0.25 ATR_d), so ATR excess t equals R excess t.")
    print("Educational only - not financial advice.")


if __name__ == "__main__" and "--base-only" not in sys.argv:
    stage2(); sys.exit()

if __name__ == "__main__":
    T, J = base()
    pd.set_option("display.width", 220)
    print(f"setups with lab list AND live record: {len(J)}; in base: {int(J.in_base.sum())}")
    print(J.round(4).to_string())
    B = J[J.in_base]
    bt = T[T.setup.isin(B.index)].copy()
    bl = GD._blackout(bt.symbol.to_numpy(), bt.date.to_numpy())
    print(f"base trades {len(bt)} on {bt.date.nunique()} days; earnings-blackout trades removed {int(bl.sum())} ({bl.mean():.1%})")
    J.to_csv(HERE / "base_selection.csv"); B.reset_index()[["setup"]].to_csv(HERE / "base.csv", index=False)
    print("frozen: base.csv (stage 2 reads it; VALID / FWD outcomes not read here). Educational only - not financial advice.")
