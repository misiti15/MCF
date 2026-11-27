"""S8-CAP live replay on the journals (PLAN.md). Educational only - not financial advice.
Usage: python live.py prep | python live.py run BOOK"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.dataset as pads

SP = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
W = SP / "s8cap"; TZ = "America/New_York"; HIST = Path("/home/user/MCF/data/cache_hist/1Min")


def mins(s):
    t = pd.to_datetime(s, utc=True, format="mixed").dt.tz_convert(TZ)
    return (t.dt.hour * 60 + t.dt.minute).to_numpy()


def prep():
    t = pd.read_parquet(SP / "capfit/all_trades.parquet")
    t = t[(t.date <= "2026-11-24")].copy(); t["wi"] = False
    t["side_n"] = np.where(t.side.astype(str).str.lower().isin(["1", "long", "buy"]), 1, -1)
    t["risk"] = (t.entry - t.stop).abs()
    t = t[t.risk > 0]
    t["cost"] = t.side_n * (t.exit - t.entry) / t.risk - t.r
    gap = t.groupby("strategy").cost.median()
    w = pd.read_parquet(SP / "capfit/whatif.parquet")
    w = w[w.why.str.startswith("setup daily loss limit") & (w.date <= "2026-11-24")].copy()
    w["side_n"] = np.where(w.side.astype(str).str.lower().isin(["1", "long", "buy"]), 1, -1)
    w["risk"] = (w.entry - w.stop).abs(); w = w[(w.risk > 0) & w.exit.notna() & w.exit_time.notna()]
    w["cost"] = w.strategy.map(gap).fillna(gap.median())
    w["r"] = w.side_n * (w.exit - w.entry) / w.risk - w.cost
    w["wi"] = True
    cols = ["account", "strategy", "symbol", "date", "entry_time", "exit_time", "entry", "exit", "side_n", "risk", "cost", "r", "wi"]
    t = pd.concat([t[cols], w[cols]], ignore_index=True)
    t["em"] = mins(t.entry_time); t["xm"] = np.maximum(mins(t.exit_time), t.em)
    t["e_ns"] = pd.to_datetime(t.entry_time, utc=True, format="mixed").astype("int64")
    t = t[(t.em >= 570) & (t.em < 960)].copy()
    t["xm"] = t.xm.clip(upper=959)
    # minute closes
    G = pd.read_parquet(SP / "pyramid/G/live_bars.parquet", columns=["close", "symbol"])
    G.index = pd.DatetimeIndex(G.index).tz_convert(TZ)
    grids = {}
    need = set(zip(t.symbol, t.date))
    for sym, g in t.groupby("symbol"):
        bs = []
        p = HIST / f"{sym}.parquet"
        if p.exists():
            f = pads.field("__index_level_0__")
            b = pads.dataset(str(p), format="parquet").to_table(filter=f >= pd.Timestamp("2026-10-06", tz=TZ),
                                                                columns=["close", "__index_level_0__"]).to_pandas()
            if "__index_level_0__" in b.columns:
                b = b.set_index("__index_level_0__")
            b.index = pd.DatetimeIndex(b.index).tz_convert(TZ); bs.append(b)
        gb = G[G.symbol == sym][["close"]]
        if len(gb):
            bs.append(gb)
        if not bs:
            continue
        b = pd.concat(bs); b = b[~b.index.duplicated()].sort_index()
        day = b.index.date.astype(str); mm = b.index.hour * 60 + b.index.minute
        for d in g.date.unique():
            ix = np.flatnonzero(day == d)
            if not len(ix):
                continue
            a = np.full(390, np.nan, np.float32)
            k = mm[ix] - 570; ok = (k >= 0) & (k < 390)
            a[k[ok]] = b.close.to_numpy()[ix][ok]
            grids[(sym, d)] = pd.Series(a).ffill().bfill().to_numpy(np.float32)
    keys = list(grids); K = {k: i for i, k in enumerate(keys)}
    t["gi"] = [K.get((s, d), -1) for s, d in zip(t.symbol, t.date)]
    np.save(W / "live_grid.npy", np.stack([grids[k] for k in keys]))
    t.drop(columns=["entry_time", "exit_time"]).to_parquet(W / "live_lots.parquet", index=False)
    print(len(t), "lots;", t.wi.sum(), "what-if;", (t.gi >= 0).mean().round(3), "share with bars;", len(keys), "grids")


CFG = {"ACT": (None, None, False, False), "NOW": (True, None, False, True), "REF": (True, None, True, True),
       "K4N": (False, None, True, True)}
for L in (6, 8, 10):
    CFG[f"C{L}L"] = (True, float(L), True, True); CFG[f"C{L}N"] = (False, float(L), True, True)
CFG["CSL"] = (True, "S", True, True); CFG["CSN"] = (False, "S", True, True)


def run(book):
    T = pd.read_parquet(W / "live_lots.parquet"); GR = np.load(W / "live_grid.npy")
    shift = {}
    if book == "NEUTRAL":
        shift = pd.read_csv(W / "live_avg.csv").set_index("strategy").a.to_dict()
    T["sh"] = T.strategy.map(shift).fillna(0.0)
    T = T.sort_values(["account", "date", "e_ns"]).reset_index(drop=True)
    AD = [(a, d, g) for (a, d), g in T.groupby(["account", "date"])]
    allrows = []
    for cfg, (latch, cap, acct, use_wi) in CFG.items():
        hist_acct = {}; hist_set = {}
        for a, d, g in AD:
            g = g if (latch is False) else g[~g.wi]
            if cfg == "ACT":
                g = g[~g.wi]
            S = sorted(g.strategy.unique()); si = g.strategy.map({s: i for i, s in enumerate(S)}).to_numpy(); N = len(S)
            em, xm, gi = g.em.to_numpy(), g.xm.to_numpy(), g.gi.to_numpy()
            side, ent, risk, cost, rr, sh = (g.side_n.to_numpy(float), g.entry.to_numpy(float), g.risk.to_numpy(float),
                                             g.cost.to_numpy(float), g.r.to_numpy(float), g.sh.to_numpy(float))
            rr = rr - sh; dur = np.maximum(xm - em, 1).astype(float)
            ha = hist_acct.get(a, [])
            X = None
            if acct:
                X = float(np.clip(4 * np.std(ha, ddof=1), 2.5 * N, 8 * N)) if len(ha) >= 10 else 8.0 * N
            H = max(20.0, 0.6 * X) if X is not None else (20.0 if latch is not None else 1e9)
            Ls = np.full(N, np.inf)
            if cap == "S":
                for i, s in enumerate(S):
                    h = hist_set.get(s, [])
                    Ls[i] = float(np.clip(1.5 * np.std(h, ddof=1), 4, 12)) if len(h) >= 8 else 8.0
            elif cap is not None:
                Ls[:] = cap
            realized = np.zeros(N); nl = np.zeros(N, int); capped = np.zeros(N, bool); capm = np.full(N, -1)
            open_ = []; halted = stopped = False; trough = 0.0; stop_m = -1
            by_m = {}
            for k in range(len(g)):
                by_m.setdefault(em[k], []).append(k)
            for m in range(570, 960):
                for k in by_m.get(m, ()):
                    # realize exits up to m
                    keep = []
                    for q in open_:
                        if xm[q] <= m:
                            realized[si[q]] += rr[q]
                        else:
                            keep.append(q)
                    open_ = keep
                    s = si[k]
                    if halted or stopped or capped[s]:
                        continue
                    if latch and realized[s] <= -2.0 + 1e-12:
                        continue
                    nl[s] += 1; open_.append(k)
                keep = []
                for q in open_:
                    if xm[q] <= m:
                        realized[si[q]] += rr[q]
                    else:
                        keep.append(q)
                open_ = keep
                if open_:
                    o = np.array(open_)
                    c = np.where(gi[o] >= 0, GR[np.maximum(gi[o], 0), m - 570], ent[o])
                    mk = side[o] * (c - ent[o]) / risk[o] - cost[o] - sh[o] * np.clip((m - em[o]) / dur[o], 0, 1)
                    ps = realized + np.bincount(si[o], weights=mk, minlength=N)
                else:
                    o = np.zeros(0, int); mk = np.zeros(0); ps = realized.copy()
                hit = (~capped) & (ps <= -Ls + 1e-12)
                if hit.any():
                    for s in np.flatnonzero(hit):
                        capped[s] = True; capm[s] = m
                        realized[s] += mk[si[o] == s].sum()
                    kk = ~capped[si[o]]; o = o[kk]; mk = mk[kk]; open_ = list(o)
                tot = ps.sum(); trough = min(trough, tot)
                if tot <= -H + 1e-12:
                    halted = True
                if X is not None and tot <= -X + 1e-12:
                    stopped = True; stop_m = m
                    for q, v in zip(o, mk):
                        realized[si[q]] += v
                    open_ = []
                    break
            for q in open_:
                realized[si[q]] += rr[q]
            hist_acct.setdefault(a, []).append(realized.sum())
            hist_acct[a] = hist_acct[a][-250:]
            for i, s in enumerate(S):
                if nl[i] > 0:
                    hist_set.setdefault(s, []).append(realized[i])
                allrows.append(dict(cfg=cfg, account=a, date=d, strategy=s, R=realized[i], lots=nl[i], capm=capm[i],
                                    L=Ls[i], X=X if X is not None else np.nan, stop_m=stop_m, trough=trough))
        print(book, cfg, round(sum(r["R"] for r in allrows if r["cfg"] == cfg), 1), flush=True)
    out = pd.DataFrame(allrows)
    out.to_parquet(W / f"live_{book}.parquet", index=False)
    if book == "RAW":
        r = out[out.cfg == "REF"].groupby("strategy").agg(R=("R", "sum"), n=("lots", "sum"))
        (r.R / r.n.clip(lower=1)).rename("a").to_csv(W / "live_avg.csv")


if __name__ == "__main__":
    prep() if sys.argv[1] == "prep" else run(sys.argv[2])
