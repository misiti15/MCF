"""Owner item 2 (2026-11-20) breakeven grid - live replay (descriptive; PLAN.md). Every live trade (run 1, all 10
journals, LR8 R) is replayed on 1-minute SIP bars from the minute after entry to its actual exit minute; if a breakeven
rule's stop fires first, the exit becomes the BE fill (level, or the bar open if it opened through) with the trade's own
LR8 cost plus $0.01 + 1 bp stop slippage. Same 216 rules as lab_be.py (half size = 0.5 x delta).
Usage: python live_be.py live_trades.parquet live_bars.parquet OUT.parquet. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from lab_be import CFG, BIG, SPYTH, itype  # noqa: E402

M0, M1 = 570, 960


def first(m):
    return int(np.argmax(m)) if m.any() else BIG


def main():
    d = pd.read_parquet(sys.argv[1]); B = pd.read_parquet(sys.argv[2]); OUT = sys.argv[3]
    d = d.drop_duplicates(["account", "id"])
    d = d[d.exit_time.notna() & d.entry.notna() & d.stop.notna()].copy()
    Gd = {}
    for (day, sym), g in B.groupby(["day", "symbol"]):
        a = np.full((4, M1 - M0), np.nan); i = g.m.to_numpy() - M0; ok = (i >= 0) & (i < M1 - M0)
        for k, col in enumerate("ohlc"): a[k, i[ok]] = g[col].to_numpy()[ok]
        a[3] = pd.Series(a[3]).ffill().bfill().to_numpy()
        for k in range(3): a[k] = np.where(np.isnan(a[k]), a[3], a[k])
        Gd[(day, sym)] = a
    d["m_in"] = d.entry_time.dt.hour * 60 + d.entry_time.dt.minute
    d["m_out"] = np.minimum(d.exit_time.dt.hour * 60 + d.exit_time.dt.minute, M1 - 1)
    rows, dl = [], []
    for r in d.itertuples():
        a = Gd.get((r.date, r.symbol)); spy = Gd.get((r.date, "SPY")); rps = abs(r.entry - r.stop); s = int(r.side)
        if a is None or not rps > 0 or r.m_out <= r.m_in: continue
        i0, i1 = r.m_in - M0 + 1, r.m_out - M0
        if i0 < 0 or i1 < i0: continue
        o, h, l, c = a[0, i0:i1 + 1], a[1, i0:i1 + 1], a[2, i0:i1 + 1], a[3, i0:i1 + 1]
        n = len(c); m_ = np.arange(r.m_in + 1, r.m_out + 1); e = r.entry
        if s > 0: fv, wv, ov = (h - e) / rps, (l - e) / rps, (o - e) / rps
        else: fv, wv, ov = (e - l) / rps, (e - h) / rps, (e - o) / rps
        gross = s * (r.exit - e) / rps; cost = gross - r.R; slip = (0.01 + 1e-4 * e) / rps
        u_ = r.tgtR if r.tgtR == r.tgtR and r.tgtR > 0 else np.inf
        cm = np.maximum.accumulate(fv)
        ks = np.array([.3, .5, .75, 1.0, .5 * u_, .8 * u_])
        tb = np.searchsorted(cm, ks, "left"); tb = np.where((tb >= n) | ~np.isfinite(ks), BIG, tb)
        if n >= 5:
            w = np.lib.stride_tricks.sliding_window_view(wv, 5).min(axis=1); piv = np.flatnonzero(wv[2:n - 2] <= w) + 2
        else: piv = np.array([], int)
        if len(piv):
            p = np.searchsorted(piv, tb, "right"); asw = np.where(p < len(piv), piv[np.minimum(p, len(piv) - 1)] + 3, BIG)
        else: asw = np.full(6, BIG)
        A = np.stack([tb + 1, tb + 11, np.maximum(tb + 1, 30), asw], axis=1); A = np.where(tb[:, None] >= BIG, BIG, A)
        ipm = int(np.searchsorted(m_, 780, "left"))
        if spy is not None:
            ref = spy[3, r.m_in - M0]; rr = s * (spy[3, m_ - M0] / ref - 1); isp = first(rr <= -SPYTH); isp = isp + 1 if isp < BIG else BIG
        else: isp = BIG
        AA = np.minimum(np.maximum(A[:, :, None], np.array([0, ipm, isp])[None, None, :]), n)
        Ls = np.array([0.0, max(cost, 0.0), -0.25]); ar = np.arange(n); out = np.empty((3,) + AA.shape)
        for li, L in enumerate(Ls):
            idx = np.where(wv <= L, ar, BIG); nh = np.r_[np.minimum.accumulate(idx[::-1])[::-1], BIG]; out[li] = nh[AA]
        ibe = np.moveaxis(out, 0, 1).astype(np.int64)
        hit = ibe < n
        xb = np.minimum(ov[np.minimum(ibe, n - 1)], Ls[None, :, None, None])
        vr = xb - cost - slip
        dd = np.where(hit, vr - r.R, 0.0).ravel()
        rows.append((r.account, r.id, r.strategy, r.family, s, r.symbol, itype(r.symbol), r.date, r.R, r.exit_reason,
                     np.isfinite(u_))); dl.append(dd.astype(np.float32))
    X = pd.DataFrame(rows, columns=["account", "id", "setup", "family", "side", "symbol", "itype", "date", "R", "exit_reason", "has_tgt"])
    X = pd.concat([X, pd.DataFrame(np.array(dl), columns=[f"d{i}" for i in range(len(CFG))])], axis=1)
    X.to_parquet(OUT, index=False)
    print("live trades replayed", len(X), "of", len(d), "avg R", round(X.R.mean(), 4))


if __name__ == "__main__":
    main()
