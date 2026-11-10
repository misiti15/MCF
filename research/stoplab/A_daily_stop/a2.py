"""A2: realised + open (marked on 1-min closes) R at each entry minute <= -L blocks new entries (latched).
Only setup-days whose trades all have 1-min bars (date <= 2026-11-04, symbol cached). Marks are gross (no costs).
Educational only - not financial advice."""
from pathlib import Path
import numpy as np, pandas as pd

BARS = Path("/home/user/MCF/data/cache_hist/1Min")
LAST_BAR = "2026-11-04"

def main(MAIN, run, level_table, mu, P, LEVELS, HERE, fmt):
    have = {p.stem for p in BARS.glob("*.parquet")}
    D = MAIN.copy()
    ok_row = (D.date <= LAST_BAR) & D.symbol.isin(have)
    ok_unit = ok_row.groupby([D.account, D.setup, D.date]).transform("all")
    D = D[ok_unit].copy()
    P(f"\n=== A2 realised + open R (1-min marks) - coverage: {len(D)} of {len(MAIN)} rows, "
      f"{D.groupby(['account','setup','date']).ngroups} units ===")
    closes = {}
    for sym, g in D.groupby("symbol"):
        b = pd.read_parquet(BARS / f"{sym}.parquet", columns=["close"])
        lo = pd.Timestamp(min(g.date), tz="America/New_York"); hi = pd.Timestamp(max(g.date), tz="America/New_York") + pd.Timedelta(days=1)
        b = b[(b.index >= lo) & (b.index < hi)]
        ts = ((b.index.tz_convert("UTC") - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta("1s")).to_numpy()
        closes[sym] = (np.asarray(ts, np.int64), b.close.to_numpy(float))

    def factory(g):
        sy = g.symbol.to_numpy(); en = g.entry.to_numpy(float); sd = g.side.to_numpy(float)
        rp = np.abs(g.entry.to_numpy(float) - g.stop.to_numpy(float)); et = g.ent_s.to_numpy()
        n = len(sy); M = np.full((n, n), np.nan)          # M[i, j] = marked R of trade j at entry i
        for s_ in set(sy):
            ts, c = closes[s_]
            k = np.searchsorted(ts, et - 60, side="right") - 1   # last completed 1-min bar before entry i
            px = np.where(k >= 0, c[np.clip(k, 0, None)] if len(c) else np.nan, np.nan)
            js = np.flatnonzero(sy == s_)
            for j in js:
                if rp[j] > 0:
                    M[:, j] = sd[j] * (px - en[j]) / rp[j]
        def om(i, opn):
            if not len(opn): return 0.0
            v = M[i, opn]
            return None if np.isnan(v).any() else float(v.sum())
        return om

    confs = [("off", "latch", None)] + [(str(L), "latch", L) for L in LEVELS]
    U1 = run(D, confs, "a2_real")
    confs_o = [("off", "latch", None)] + [(str(L), "open", L) for L in LEVELS]
    U2 = run(D, confs_o, "a2_open", openmark_factory=factory)
    miss = U2[[f"R_{L}" for L in LEVELS]].isna().any(axis=1)
    P(f"units with a missing mark (dropped from both): {int(miss.sum())}")
    U1 = U1[~miss.to_numpy()]; U2 = U2[~miss.to_numpy()]
    U1.to_csv(HERE / "units_a2_realised.csv.gz", index=False); U2.to_csv(HERE / "units_a2_open.csv.gz", index=False)
    names = ["off"] + [str(L) for L in LEVELS]
    t1 = level_table(U1, mu, "off", names); t2 = level_table(U2, mu, "off", names)
    t1.to_csv(HERE / "A2_realised_same_coverage.csv", index=False); t2.to_csv(HERE / "A2_open_marked.csv", index=False)
    cols = ["level", "R", "n", "avgR", "worst_day", "R_wo_best_day", "d_vs_off", "c_d_vs_off", "v_d_vs_off", "v_t", "v_excess"]
    P("A1 realised (same coverage):"); P(fmt(t1, cols))
    P("A2 realised + open:"); P(fmt(t2, cols))
    d = t2.set_index("level")[["R", "c_R", "v_R"]] - t1.set_index("level")[["R", "c_R", "v_R"]]
    P("A2 minus A1 (R, choose, validate):"); P(d.to_string(float_format=lambda v: f"{v:,.1f}"))
