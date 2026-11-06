"""top20 conditions deep dive (2026-11-06), two-year second opinion from the BDI 1104 trade lists
(research/history2y/data/bt_lab1104, research/bdi/1104/DATA.md: production costs, stop first, 15:55 flatten, R per unit
of live risk). BACKTEST, TRAIN (<= 2025-12) + VALID (2026-01..03, 07..09-15); HOLD rows dropped; the locked block
2024-11-01..2025-02-28 is not in the lists (asserted) and the daily table is read without it (lib.daily()).
All 22 open months are built now (11-04's CWT13 / CWT14 reads had 11 of 22).

Same pre-declared buckets as conditions_live.py. Point-in-time features from the daily table: gap = open vs prior close
(NaN across the locked gap), ADV = adv20 (prior 20 sessions), price = prior close, ATR% = 14-session ATR of prior
sessions / prior close; SPY vs open at 10:00 = close of the 09:59 1-minute bar, SPY vs open at entry = close of the bar
before the entry minute (data/cache_hist). Parents only - no tuning here.

    python research/bdi/top20/conditions_2y_bt.py SETUP [SETUP ...] -> hist_bt_buckets.csv, hist_bt_summary.csv, hist_bt_out.txt
Educational only - not financial advice."""
import glob
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = Path("/home/user/MCF")
sys.path.insert(0, str(OUT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
import lib  # noqa: E402
from conditions_live import kind, DIMS, PIT  # noqa: E402


def split(d):
    d = pd.to_datetime(d)
    tr = d <= "2025-12-31"
    va = ((d >= "2026-01-01") & (d <= "2026-03-31")) | ((d >= "2026-07-01") & (d <= "2026-09-15"))
    return np.where(tr, "train", np.where(va, "valid", "hold"))


def feats(S):
    d = lib.daily().sort_values(["symbol", "date"]).copy()
    g = d.groupby("symbol")
    pc = g.close.shift(1)
    gapdays = pd.to_datetime(d.date).groupby(d.symbol).diff().dt.days
    d["gap"] = np.where(gapdays <= 5, (d.open / pc - 1) * 100, np.nan)
    tr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs()))
    d["atrp"] = tr.groupby(d.symbol).transform(lambda x: x.shift(1).rolling(14, min_periods=10).mean()) / pc * 100
    d["pclose"] = pc
    d["dkey"] = d.date.astype(str)
    S = S.merge(d[["symbol", "dkey", "gap", "atrp", "pclose", "adv20"]], on=["symbol", "dkey"], how="left")
    x = pd.read_parquet(ROOT / "data/cache_hist/1Min/SPY.parquet")
    x = x[(x.index < "2024-11-01") | (x.index >= "2025-03-01")]
    dk = x.index.strftime("%Y-%m-%d")
    op = x.groupby(dk).open.first()
    cl = x.groupby(dk).close.last()
    m = x.index.hour * 100 + x.index.minute
    S["spy10"] = S.dkey.map((x[m == 959].groupby(dk[m == 959]).close.last() / op - 1) * 100)
    S["spy_o2c"] = S.dkey.map((cl / op - 1) * 100)
    # SPY at the close of the bar before the entry minute
    key = pd.Series(x.close.to_numpy(), index=pd.MultiIndex.from_arrays([dk, m]))
    hh, mm = S.tod // 100, S.tod % 100
    prev = (hh * 60 + mm - 1)
    k = list(zip(S.dkey, (prev // 60) * 100 + prev % 60))
    S["spy_fo"] = (key.reindex(k).to_numpy() / S.dkey.map(op).to_numpy() - 1) * 100
    return S


def main():
    want = sys.argv[1:]
    T = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(ROOT / "research/history2y/data/bt_lab1104/sig_*.parquet")))])
    T = T[T.setup.isin(want)].copy()
    dd = pd.to_datetime(T.date)
    assert not ((dd >= "2024-11-01") & (dd <= "2025-02-28")).any()
    T["sp"] = split(T.date)
    T = T[T.sp != "hold"].copy()
    T["dkey"] = pd.to_datetime(T.date).dt.strftime("%Y-%m-%d")
    T = feats(T)
    uni = pd.read_csv(ROOT / "data/universe.csv")[["symbol", "name"]]
    T["kind"] = T.symbol.map(dict(zip(uni.symbol, uni.name.map(kind)))).fillna("stock")
    b = lambda v, lo, hi: np.where(v > hi, "above", np.where(v < lo, "below", np.where(np.isnan(v), "nan", "flat")))
    T["day"] = np.where(T.spy_o2c > 0.25, "up", np.where(T.spy_o2c < -0.25, "down", "quiet"))
    T["spy10b"] = b(T.spy10.to_numpy(float), -0.10, 0.10)
    T["spyfob"] = b(T.spy_fo.to_numpy(float), -0.10, 0.10)
    T["todb"] = pd.cut(T.tod, [0, 1030, 1130, 1300, 1400, 1700], right=False,
                       labels=["0950-1030", "1030-1130", "1130-1300", "1300-1400", "1400-1600"]).astype(str)
    T["gapb"] = pd.cut(T.gap, [-1e9, -3, -1, 1, 3, 1e9], labels=["<-3", "-3..-1", "-1..+1", "+1..+3", ">+3"]).astype(str)
    T["advb"] = pd.cut(T.adv20, [0, 1e8, 3e8, 1e9, 1e15], right=False, labels=["<100M", "100-300M", "300M-1B", ">=1B"]).astype(str)
    T["pxb"] = pd.cut(T.pclose, [0, 20, 50, 150, 1e9], right=False, labels=["<20", "20-50", "50-150", ">=150"]).astype(str)
    T["atrb"] = pd.cut(T.atrp, [0, 2, 3.5, 5, 1e9], right=False, labels=["<2", "2-3.5", "3.5-5", ">=5"]).astype(str)
    T["sideb"] = np.where(T.side > 0, "long", "short")
    rows, summ, txt = [], [], []
    for s in want:
        d = T[T.setup == s].reset_index(drop=True)
        if not len(d):
            print("no 2-year list:", s)
            continue
        day = d.groupby("date").r.sum()
        top = d.r >= d.r.quantile(0.9)
        o = dict(setup=s, n=len(d), sessions=day.size, avg=d.r.mean(), train=d[d.sp == "train"].r.mean(),
                 valid=d[d.sp == "valid"].r.mean(), up=d[d.day == "up"].r.mean(), down=d[d.day == "down"].r.mean(),
                 quiet=d[d.day == "quiet"].r.mean(), exbest=(d.r.sum() - day.max()) / max(len(d) - 1, 1),
                 best_share=day.max() / d.r.sum() if d.r.sum() > 0 else np.nan)
        bl = []
        for dim, lab in DIMS:
            for k, g in d.groupby(dim):
                bl.append(dict(setup=s, dim=dim, label=lab, bucket=k, n=len(g), share=len(g) / len(d), avg=g.r.mean(),
                               train=g[g.sp == "train"].r.mean(), valid=g[g.sp == "valid"].r.mean(),
                               totR=g.r.sum(), top_dec_share=top[g.index].sum() / max(top.sum(), 1)))
        rows += bl
        bb = pd.DataFrame(bl)
        sk = bb[bb.dim.isin(PIT) & (bb.share < 0.999) & (bb.bucket != "nan")].copy()
        sk["kept"], sk["top_kept"] = 1 - sk.share, 1 - sk.top_dec_share
        sk["avg_after"] = (d.r.sum() - sk.totR) / (len(d) - sk.n).clip(lower=1)
        ok = sk[(sk.kept >= 0.70) & (sk.top_kept >= 0.90) & (sk.train < 0) & (sk.valid < 0) & (sk.n >= 30)]
        if len(ok):
            f = ok.loc[ok.avg_after.idxmax()]
            o["skip_2y"] = (f"skip {f.label} {f.bucket} (TRAIN {f.train:+.3f} / VALID {f.valid:+.3f}): {o['avg']:+.3f} -> "
                            f"{f.avg_after:+.3f}R, keeps {f.kept:.0%} / {f.top_kept:.0%} top-decile")
        else:
            o["skip_2y"] = "none (70% / 90% and losing in TRAIN and VALID)"
        pit = bb[bb.dim.isin(PIT) & (bb.n >= 30) & (bb.share >= 0.15) & (bb.share < 0.999) & (bb.bucket != "nan")]
        cons = pit[(np.sign(pit.train - o["train"]) == np.sign(pit.valid - o["valid"]))]
        if len(cons):
            hi, lo = cons.loc[cons.avg.idxmax()], cons.loc[cons.avg.idxmin()]
            o["thrives_2y"] = f"{hi.label} {hi.bucket} ({hi.avg:+.3f}R, T {hi.train:+.3f} / V {hi.valid:+.3f}, n {hi.n})"
            o["struggles_2y"] = f"{lo.label} {lo.bucket} ({lo.avg:+.3f}R, T {lo.train:+.3f} / V {lo.valid:+.3f}, n {lo.n})"
        summ.append(o)
        txt.append(f"=== {s}  BACKTEST n {len(d)} sessions {day.size} avg {o['avg']:+.4f} TRAIN {o['train']:+.4f} VALID {o['valid']:+.4f} "
                   f"up {o['up']:+.3f} down {o['down']:+.3f} quiet {o['quiet']:+.3f} w/o best day {o['exbest']:+.4f}")
        txt.append(bb.set_index(["label", "bucket"])[["n", "avg", "train", "valid", "top_dec_share"]].round(3).to_string())
        txt.append("")
    pd.DataFrame(rows).round(4).to_csv(OUT / "hist_bt_buckets.csv", index=False)
    pd.DataFrame(summ).round(4).to_csv(OUT / "hist_bt_summary.csv", index=False)
    (OUT / "hist_bt_out.txt").write_text("Educational only - not financial advice. BACKTEST (bt_lab1104 lists), TRAIN+VALID, costs in, "
                                         "locked block never loaded.\n\n" + "\n".join(txt))
    print("missing:", T[["gap", "adv20", "atrp", "spy10", "spy_fo"]].isna().mean().round(3).to_dict())
    with pd.option_context("display.width", 250, "display.max_colwidth", 100):
        print(pd.DataFrame(summ).round(3).T.to_string())


if __name__ == "__main__":
    main()
