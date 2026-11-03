"""top20 conditions deep dive (2026-11-03), two-year second opinion. BACKTEST: gates1021 live-shaped signal rows
(production R, costs in, x3 extended tier) on the open history, TRAIN (<= 2025-12) + VALID (2026-01..03, 07..09-15);
HOLD rows dropped; the locked block 2024-11-01..2025-02-28 is never loaded (gates1021 loaders assert).
Same pre-declared buckets as conditions_live.py; ATR% = daily ATR / price; SPY at 10:00 = close of the 09:59 1-minute
bar vs the 09:30 open (data/cache_hist). Parents only - no tuning here.

    G21SCR=/dev/shm/t5_1103/g python research/bdi/top20/conditions_2y.py   -> hist_buckets.csv, hist_summary.csv, hist_out.txt
Educational only - not financial advice."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT.parents[1] / "bdi" / "gates1021" / "scripts"))
sys.path.insert(0, str(OUT))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
from load import load_sig  # noqa: E402
from conditions_live import kind  # noqa: E402

SETUPS = ["MF2-open-rsimidhi-flowsell-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
          "L3-gap-slope-fromopen-FD", "NM-MF3-qqqdn-gapdn-FD", "L3-gap-slope-rsi5hi-FD", "NS4-pm-vwap-reclaim-oversold-short-FD",
          "NS5-sma50-flush-oversold-long", "L3-gap-slope-lowdist-FD", "RW1-gapdn-bounce-flowsell-short-FD",
          "ST7-rsi50dn-long-pm-t1s1-FD"]
SIDE = {"NS5-sma50-flush-oversold-long": 1, "ST7-rsi50dn-long-pm-t1s1-FD": 1}


def spy10():
    x = pd.read_parquet("/home/user/MCF/data/cache_hist/1Min/SPY.parquet")
    x = x[(x.index < "2024-11-01") | (x.index >= "2025-03-01")]
    d = x.index.strftime("%Y-%m-%d")
    op = x.groupby(d).open.first()
    m = x.index.hour * 100 + x.index.minute
    c10 = x[m == 959].groupby(d[m == 959]).close.last()
    return ((c10 / op - 1) * 100).rename("spy10")


def split(d):
    d = pd.to_datetime(d)
    tr = d <= "2025-12-31"
    va = ((d >= "2026-01-01") & (d <= "2026-03-31")) | ((d >= "2026-07-01") & (d <= "2026-09-15"))
    return np.where(tr, "train", np.where(va, "valid", "hold"))


def main():
    S = load_sig(SETUPS)
    S["sp"] = split(S["date"])
    S = S[S.sp != "hold"].copy()
    S["dkey"] = pd.to_datetime(S["date"]).dt.strftime("%Y-%m-%d")
    S = S.join(spy10(), on="dkey")
    uni = pd.read_csv("/home/user/MCF/data/universe.csv")[["symbol", "name"]]
    S["kind"] = S.symbol.map(dict(zip(uni.symbol, uni.name.map(kind)))).fillna("stock")
    b = lambda v, lo, hi: np.where(v > hi, "above", np.where(v < lo, "below", "flat"))
    S["day"] = np.where(S.spy_o2c > 0.25, "up", np.where(S.spy_o2c < -0.25, "down", "quiet"))
    S["spy10b"] = b(S.spy10, -0.10, 0.10)
    S["spyfob"] = b(S.spy_fo, -0.10, 0.10)
    S["todb"] = pd.cut(S.tod, [0, 1030, 1130, 1300, 1400, 1700], right=False,
                       labels=["0950-1030", "1030-1130", "1130-1300", "1300-1400", "1400-1600"]).astype(str)
    S["gapb"] = pd.cut(S.gap, [-1e9, -3, -1, 1, 3, 1e9], labels=["<-3", "-3..-1", "-1..+1", "+1..+3", ">+3"]).astype(str)
    S["advb"] = pd.cut(S.adv20, [0, 1e8, 3e8, 1e9, 1e15], right=False, labels=["<100M", "100-300M", "300M-1B", ">=1B"]).astype(str)
    S["pxb"] = pd.cut(S.close, [0, 20, 50, 150, 1e9], right=False, labels=["<20", "20-50", "50-150", ">=150"]).astype(str)
    S["atrb"] = pd.cut(S.atr_d / S.close * 100, [0, 2, 3.5, 5, 1e9], right=False, labels=["<2", "2-3.5", "3.5-5", ">=5"]).astype(str)
    S["sideb"] = np.where(S.setup.map(SIDE).fillna(-1) > 0, "long", "short")
    from conditions_live import DIMS, PIT
    rows, summ, txt = [], [], []
    for s in SETUPS:
        d = S[S.setup == s].reset_index(drop=True)
        if not len(d):
            continue
        day = d.groupby("date").r.sum()
        top = d.r >= d.r.quantile(0.9)
        o = dict(setup=s, n=len(d), sessions=day.size, avg=d.r.mean(), train=d[d.sp == "train"].r.mean(),
                 valid=d[d.sp == "valid"].r.mean(), up=d[d.day == "up"].r.mean(), down=d[d.day == "down"].r.mean(),
                 quiet=d[d.day == "quiet"].r.mean(), exbest=(d.r.sum() - day.max()) / max(len(d) - 1, 1),
                 best_share=day.max() / d.r.sum() if d.r.sum() > 0 else np.nan)
        for dim, lab in DIMS:
            for k, g in d.groupby(dim):
                rows.append(dict(setup=s, dim=dim, label=lab, bucket=k, n=len(g), share=len(g) / len(d), avg=g.r.mean(),
                                 train=g[g.sp == "train"].r.mean(), valid=g[g.sp == "valid"].r.mean(),
                                 totR=g.r.sum(), top_dec_share=top[g.index].sum() / max(top.sum(), 1)))
        bb = pd.DataFrame([r for r in rows if r["setup"] == s])
        sk = bb[bb.dim.isin(PIT) & (bb.share < 0.999)].copy()
        sk["kept"], sk["top_kept"] = 1 - sk.share, 1 - sk.top_dec_share
        sk["avg_after"] = (d.r.sum() - sk.totR) / (len(d) - sk.n).clip(lower=1)
        # skip a bucket only if it loses in TRAIN and in VALID (consistent), and keeps 70% / 90%
        ok = sk[(sk.kept >= 0.70) & (sk.top_kept >= 0.90) & (sk.train < 0) & (sk.valid < 0) & (sk.n >= 30)]
        if len(ok):
            f = ok.loc[ok.avg_after.idxmax()]
            o["skip_2y"] = (f"skip {f.label} {f.bucket} (TRAIN {f.train:+.3f} / VALID {f.valid:+.3f}): {o['avg']:+.3f} -> "
                            f"{f.avg_after:+.3f}R, keeps {f.kept:.0%} / {f.top_kept:.0%} top-decile")
        else:
            o["skip_2y"] = "none (70% / 90% and losing in TRAIN and VALID)"
        pit = bb[bb.dim.isin(PIT) & (bb.n >= 30) & (bb.share >= 0.15) & (bb.share < 0.999)]
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
    pd.DataFrame(rows).round(4).to_csv(OUT / "hist_buckets.csv", index=False)
    pd.DataFrame(summ).round(4).to_csv(OUT / "hist_summary.csv", index=False)
    (OUT / "hist_out.txt").write_text("Educational only - not financial advice. BACKTEST, TRAIN+VALID, costs in, locked block never loaded.\n\n"
                                      + "\n".join(txt))
    with pd.option_context("display.width", 250, "display.max_colwidth", 90):
        print(pd.DataFrame(summ).round(3).to_string())


if __name__ == "__main__":
    main()
