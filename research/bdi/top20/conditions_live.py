"""top20 conditions deep dive (2026-11-06), live part. Live = paper fills (rule 7), run_id 1, Primary + Testing 1 +
Testing 2 + Graveyard + Live Lab + Explore 1 (from 11-05), every session since start (10-06..11-06), GEN-* and S6 out, "-FD" copies are their own setup.
Top 20 = the dashboard leaderboard order (mcf.report.daily_post.leaderboard: shrunk avg R = avgR * n / (n + 20), setups
enabled somewhere now) with >= 20 trades.

Buckets (pre-declared, written before any bucket was read):
  day type (HINDSIGHT, known at the close): SPY open->close  up > +0.25%, down < -0.25%, quiet otherwise
  SPY vs its open at 10:00 (point-in-time from 10:00): above > +0.10%, below < -0.10%, flat otherwise
  SPY vs its open at entry (point-in-time): same bands
  time of day of entry: 09:50-10:30, 10:30-11:30, 11:30-13:00, 13:00-14:00, 14:00-16:00
  gap (today's open vs prior close): <-3%, -3..-1, -1..+1, +1..+3, >+3%
  ADV (20 prior sessions, $): <100M, 100-300M, 300M-1B, >=1B;  price: <20, 20-50, 50-150, >=150
  ATR% (14 prior sessions): <2, 2-3.5, 3.5-5, >=5;  type: stock / ETF / leveraged ETF (universe name);  side
  ex-market R = R - side * beta * SPY return (entry minute -> exit minute) * entry / risk-per-share, beta from daily
  returns 2026-07-01..10-05 (before the first live session), shrunk halfway to 1.
  "Thrives / struggles" = best / worst point-in-time bucket with n >= 8 and >= 15% of the setup's trades.
  Filter screen (no strangling): skipping one point-in-time bucket must keep >= 70% of trades and >= 90% of the
  top-decile winners (by R); otherwise it is only a sizing / "on deck" idea.

Usage: python conditions_live.py <scratch>   (scratch from fetch_live.py) -> live_buckets.csv, live_summary.csv,
live_out.txt. Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # this checkout (docs/live at HEAD)
from mcf.report.daily_post import leaderboard  # noqa: E402

S = Path(sys.argv[1]) if len(sys.argv) > 1 else None; OUT = Path(__file__).resolve().parent
TZ = "America/New_York"


def top20():
    rows = [r for r in leaderboard("2026-11-06", top=500) if (r["trades"] or 0) >= 20][:20]
    return pd.DataFrame([{"rank": i + 1, "setup": r["setup"], "acct_now": r["acct"], "lb_n": r["trades"],
                          "lb_avg": r["avg_r"], "lb_shrunk": r["rank_score"]} for i, r in enumerate(rows)])


def kind(name: str) -> str:
    n = (name or "").lower()
    lev = any(k in n for k in ("2x", "3x", "-1x", "ultra", "leveraged", "daily bull", "daily bear", "bull 2", "bull 3",
                               "bear 2", "bear 3", "inverse", "2x long", "short qqq"))
    etf = lev or any(k in n for k in (" etf", " etn", " fund", "ishares", "spdr", "proshares", "direxion", "invesco qqq",
                                       "vaneck", "graniteshares", "t-rex", "defiance", "tradr", "grayscale"))
    return "lev_etf" if lev else "etf" if etf else "stock"


def features():
    T = pd.read_parquet(S / "trades.parquet")
    T = T[~T.strategy.str.startswith("S6") & ~T.strategy.str.upper().str.startswith("GEN")].copy()
    for c in ("entry_time", "exit_time"):
        T[c] = pd.to_datetime(T[c], utc=True, format="mixed").dt.tz_convert(TZ)
    T["tod"] = T.entry_time.dt.hour * 100 + T.entry_time.dt.minute
    D = pd.read_parquet(S / "daily.parquet")
    D["date"] = pd.to_datetime(D["timestamp"], utc=True).dt.tz_convert(TZ).dt.strftime("%Y-%m-%d")
    D = D.sort_values(["symbol", "date"])
    g = D.groupby("symbol")
    D["prev_close"] = g.close.shift(1)
    D["gap"] = (D.open / D.prev_close - 1) * 100
    D["adv"] = g.apply(lambda x: (x.close * x.volume).shift(1).rolling(20, min_periods=10).mean()).reset_index(level=0, drop=True)
    tr = np.maximum(D.high - D.low, np.maximum((D.high - D.prev_close).abs(), (D.low - D.prev_close).abs()))
    D["atrp"] = (tr.groupby(D.symbol).transform(lambda x: x.shift(1).rolling(14, min_periods=10).mean()) / D.prev_close) * 100
    D["ret"] = D.close / D.prev_close - 1
    # beta (pre-live): daily returns 07-01..10-05 vs SPY, shrunk halfway to 1
    pre = D[D.date <= "2026-10-05"].pivot(index="date", columns="symbol", values="ret")
    spy = pre["SPY"]
    beta = {}
    for s in pre.columns:
        x = pd.concat([pre[s], spy], axis=1).dropna()
        beta[s] = 0.5 + 0.5 * (np.cov(x.iloc[:, 0], x.iloc[:, 1])[0, 1] / x.iloc[:, 1].var()) if len(x) >= 30 else 1.0
    T = T.merge(D[["symbol", "date", "gap", "adv", "atrp"]], on=["symbol", "date"], how="left")
    T["beta"] = T.symbol.map(beta).fillna(1.0)
    uni = pd.read_csv("/home/user/MCF/data/universe.csv")[["symbol", "name"]]
    T["kind"] = T.symbol.map(dict(zip(uni.symbol, uni.name.map(kind)))).fillna("stock")
    # SPY intraday
    M = pd.read_parquet(S / "spy_1m.parquet")
    M["ts"] = pd.to_datetime(M.ts, utc=True).dt.tz_convert(TZ)
    M["date"] = M.ts.dt.strftime("%Y-%m-%d")
    M["m"] = M.ts.dt.hour * 100 + M.ts.dt.minute
    op = M.groupby("date").open.first()
    cl = M.groupby("date").close.last()
    o2c = (cl / op - 1) * 100
    at10 = M[M.m == 959].set_index("date").close / op - 1   # close of the 09:59 bar = SPY at 10:00
    T["spy_o2c"] = T.date.map(o2c)
    T["spy10"] = T.date.map(at10 * 100)
    Mi = M.set_index("ts").close
    ent = Mi.reindex(T.entry_time.dt.floor("min") - pd.Timedelta(minutes=1), method="ffill").to_numpy()
    ext = Mi.reindex(T.exit_time.dt.floor("min"), method="ffill").to_numpy()
    T["spy_fo"] = (ent / T.date.map(op).to_numpy() - 1) * 100
    spy_ret = ext / ent - 1
    rps = (T.entry - T.stop).abs()
    T["mkt_r"] = np.where(rps > 0, T.side * T.beta * spy_ret * T.entry / rps, 0.0)
    T["exmkt_r"] = T.r_multiple - np.nan_to_num(T.mkt_r)
    b = lambda v, lo, hi: np.where(v > hi, "above", np.where(v < lo, "below", "flat"))
    T["day"] = np.where(T.spy_o2c > 0.25, "up", np.where(T.spy_o2c < -0.25, "down", "quiet"))
    T["spy10b"] = b(T.spy10, -0.10, 0.10)
    T["spyfob"] = b(T.spy_fo, -0.10, 0.10)
    T["todb"] = pd.cut(T.tod, [0, 1030, 1130, 1300, 1400, 1700], right=False,
                       labels=["0950-1030", "1030-1130", "1130-1300", "1300-1400", "1400-1600"]).astype(str)
    T["gapb"] = pd.cut(T.gap, [-1e9, -3, -1, 1, 3, 1e9], labels=["<-3", "-3..-1", "-1..+1", "+1..+3", ">+3"]).astype(str)
    T["advb"] = pd.cut(T.adv, [0, 1e8, 3e8, 1e9, 1e15], right=False, labels=["<100M", "100-300M", "300M-1B", ">=1B"]).astype(str)
    T["pxb"] = pd.cut(T.entry, [0, 20, 50, 150, 1e9], right=False, labels=["<20", "20-50", "50-150", ">=150"]).astype(str)
    T["atrb"] = pd.cut(T.atrp, [0, 2, 3.5, 5, 1e9], right=False, labels=["<2", "2-3.5", "3.5-5", ">=5"]).astype(str)
    T["sideb"] = np.where(T.side > 0, "long", "short")
    return T


DIMS = [("day", "day type (hindsight)"), ("spy10b", "SPY vs open at 10:00"), ("spyfob", "SPY vs open at entry"),
        ("todb", "time"), ("gapb", "gap %"), ("advb", "ADV"), ("pxb", "price"), ("atrb", "ATR%"), ("kind", "type"),
        ("sideb", "side")]
PIT = [d for d, _ in DIMS if d != "day"]


def one(d: pd.DataFrame):
    r = d.r_multiple
    n = len(d)
    day = d.groupby("date").r_multiple.sum()
    tot = r.sum()
    best = day.idxmax()
    exb = d[d.date != best].r_multiple.mean() if day.size > 1 else np.nan
    share = day.max() / tot if tot > 0 else np.nan
    se_day = day.std(ddof=1) / np.sqrt(day.size) if day.size > 1 else np.nan
    w, l = d[r > 0], d[r <= 0]
    out = dict(n=n, sessions=day.size, avg=r.mean(), shrunk=r.mean() * n / (n + 20), win=(r > 0).mean(), totR=tot,
               t_day=(day.mean() / se_day) if se_day and se_day > 0 else np.nan, exbest=exb, best_day=best,
               best_share=share, exmkt=d.exmkt_r.mean(), mkt=np.nanmean(d.mkt_r), avg_win=w.r_multiple.mean(),
               avg_loss=l.r_multiple.mean(), med_mfe=d.mfe_r.abs().median(), losers_never_02=(l.mfe_r.abs() < 0.2).mean()
               if len(l) else np.nan)
    return out


def buckets(s, d):
    rows = []
    top = d.r_multiple >= d.r_multiple.quantile(0.9)
    for dim, lab in DIMS:
        for k, g in d.groupby(dim):
            rows.append(dict(setup=s, dim=dim, label=lab, bucket=k, n=len(g), share=len(g) / len(d), avg=g.r_multiple.mean(),
                             exmkt=g.exmkt_r.mean(), totR=g.r_multiple.sum(), win=(g.r_multiple > 0).mean(),
                             top_dec_share=top[g.index].sum() / max(top.sum(), 1), losers_R=g.r_multiple[g.r_multiple < 0].sum()))
    return rows


def main():
    T = features()
    T.to_parquet(S / "live_feat.parquet")
    top = top20()
    summ, B, txt = [], [], []
    for x in top.to_dict("records"):
        s = x["setup"]
        d = T[T.strategy == s].reset_index(drop=True)
        o = {**x, **one(d)}
        bb = pd.DataFrame(buckets(s, d))
        B.append(bb)
        pit = bb[bb.dim.isin(PIT) & (bb.n >= 8) & (bb.share >= 0.15) & (bb.share < 0.999)]
        if len(pit):
            hi, lo = pit.loc[pit.avg.idxmax()], pit.loc[pit.avg.idxmin()]
            o["thrives"] = f"{hi.label} {hi.bucket} ({hi.avg:+.2f}R, n {hi.n})"
            o["struggles"] = f"{lo.label} {lo.bucket} ({lo.avg:+.2f}R, n {lo.n})"
        # where losers cluster: the bucket holding the largest share of losing R (point-in-time dims)
        lr = d.r_multiple[d.r_multiple < 0].sum()
        cl = bb[bb.dim.isin(PIT) & (bb.share < 0.999)].copy()
        cl["loser_share"] = cl.losers_R / lr if lr < 0 else np.nan
        cl["excess"] = cl.loser_share - cl.share
        c = cl.loc[cl.excess.idxmax()] if cl.excess.notna().any() else None
        o["losers_cluster"] = (f"{c.label} {c.bucket}: {c.loser_share:.0%} of losing R on {c.share:.0%} of trades"
                               if c is not None else "")
        # filter screen: skip one point-in-time bucket
        sk = bb[bb.dim.isin(PIT) & (bb.share < 0.999)].copy()
        sk["kept"] = 1 - sk.share
        sk["top_kept"] = 1 - sk.top_dec_share
        sk["avg_after"] = (d.r_multiple.sum() - sk.totR) / (len(d) - sk.n).clip(lower=1)
        ok = sk[(sk.kept >= 0.70) & (sk.top_kept >= 0.90)]
        if len(ok):
            f = ok.loc[ok.avg_after.idxmax()]
            o["skip_ok"] = (f"skip {f.label} {f.bucket}: {o['avg']:+.3f} -> {f.avg_after:+.3f}R, keeps {f.kept:.0%} trades / "
                            f"{f.top_kept:.0%} top-decile")
        else:
            o["skip_ok"] = "none passes 70% / 90%"
        summ.append(o)
        txt.append(f"=== {x['rank']}. {s} ({x['acct_now']}; live {len(d)} trades, {o['sessions']} sessions)")
        txt.append(f"avg {o['avg']:+.3f}R  shrunk {o['shrunk']:+.3f}  win {o['win']:.1%}  total {o['totR']:+.1f}R  t(day) {o['t_day']:.2f}"
                   f"  w/o best day {o['exbest']:+.3f}R (best {o['best_day']} = {o['best_share']:.0%} of total)  ex-market {o['exmkt']:+.3f}R")
        piv = bb.pivot_table(index=["label", "bucket"], values=["n", "avg", "exmkt", "win", "top_dec_share"], sort=False)
        txt.append(piv[["n", "avg", "exmkt", "win", "top_dec_share"]].round(3).to_string())
        txt.append("by account:\n" + d.groupby("acct").r_multiple.agg(["size", "mean", "sum"]).round(3).to_string())
        txt.append("")
    pd.DataFrame(summ).to_csv(OUT / "live_summary.csv", index=False)
    pd.concat(B).round(4).to_csv(OUT / "live_buckets.csv", index=False)
    (OUT / "live_out.txt").write_text("Educational only - not financial advice. Live paper trades 10-06..11-06, run_id 1.\n\n"
                                      + "\n".join(txt))
    cols = ["rank", "setup", "n", "avg", "exbest", "best_share", "exmkt", "thrives", "struggles", "losers_cluster", "skip_ok"]
    with pd.option_context("display.width", 250, "display.max_colwidth", 80):
        print(pd.DataFrame(summ)[cols].round(3).to_string())
    print("missing feats:", T[["gap", "adv", "atrp", "spy10", "spy_fo"]].isna().mean().round(3).to_dict())
    print(T.kind.value_counts().to_dict())


if __name__ == "__main__":
    main()
