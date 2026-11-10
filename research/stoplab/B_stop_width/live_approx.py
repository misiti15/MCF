"""stoplab grid B2 (diagnostic, APPROXIMATE): per-trade stop width k on the LIVE paper trades (run_id 1, all 7 accounts).
Same $ risk (size / k), target price unchanged. Per trade, in original-R units: G1 = side*(exit-entry)/risk_ps (gross),
C = G1 - R (R = pnl_adj based, costs in). Then r_k is in units of the (unchanged) $ risk:
  k < 1: stopped if mae_r <= -k  -> r_k = (-k + s)/k, s = own (R + 1) if the trade was a stop exit, else the setup's
         median (R + 1) over its stop exits (stop slippage + costs); not stopped -> r_k = R / k (same exit, size x 1/k).
  k > 1: non-stop exits are unchanged in price -> r_k = R / k. Stop exits are continued on 1-min bars from the exit
         minute (cache_hist, to 2026-11-04 only) with the wider stop and the same target, flatten 15:55 close; new exit
         costs = the setup's median C for that exit kind. Stop exits without bars are dropped for k > 1 (counted).
Caveats: mfe/mae come from the runner's bar marks, so path order inside bars is unknown and mae can understate the
true excursion (some stop exits show mae_r > -1); this is a bound-style approximation, not a score.
Size-only control: r_sc = R / k (same trade, old stop, smaller size). Stop effect = r_k - r_sc.
Usage: python live_approx.py   -> live_trades_k.parquet (scratch) + live_setup_k.csv here. Educational only - not financial advice."""
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path("/home/user/MCF"); HERE = Path(__file__).resolve().parent
BARS = ROOT / "data" / "cache_hist" / "1Min"
KS = (0.75, 0.9, 1.0, 1.1, 1.25, 1.5)
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())


def main():
    t = pd.read_csv(HERE.parent / "trades.csv.gz")
    t = t[~t.whatif & t.exit_reason.isin(["target", "stop", "flatten", "timestop"])].copy()
    d = pd.to_datetime(t.date).dt.date
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any()
    s = np.where(t.side.astype(str).str.lower().isin(["long", "buy", "1"]), 1, -1)
    t["s"] = s
    t["rps"] = (t.entry - t.stop).abs()
    t = t[(t.rps > 0) & t.R.notna()].copy()
    t["G1"] = t.s * (t.exit - t.entry) / t.rps
    t["C"] = t.G1 - t.R
    t["kind"] = t.exit_reason.map({"target": "target", "stop": "stop"}).fillna("flat")
    gs = t[t.kind == "stop"].groupby("setup").R.median() + 1
    gall = float(t[t.kind == "stop"].R.median() + 1)
    t["s_net"] = np.where(t.kind == "stop", t.R + 1, t.setup.map(gs).fillna(gall))
    cmed = t.groupby(["setup", "kind"]).C.median()
    callk = t.groupby("kind").C.median()

    def cof(setup, kind):
        return cmed.get((setup, kind), callk[kind])

    for k in KS:
        if k == 1.0:
            t["r1.0"] = t.R
            continue
        if k < 1:
            # a stop exit reached -1R, so it is stopped at any k < 1 even when its bar-mark mae_r reads > -1
            stopped = (t.mae_r <= -k) | (t.kind == "stop")
            r = np.where(stopped, (-k + t.s_net) / k, t.R / k)
            r = np.where(t.mae_r.isna() & (t.kind != "stop"), np.nan, r)
            t[f"r{k}"] = r
        else:
            t[f"r{k}"] = np.where(t.kind == "stop", np.nan, t.R / k)
    # 1-min continuation for stop exits (k > 1)
    st = t[(t.kind == "stop")].copy()
    st["et"] = pd.to_datetime(st.exit_time, utc=True).dt.tz_convert("America/New_York")
    st["sym"] = st.symbol.astype(str)
    cont = {k: {} for k in KS if k > 1}
    nb = 0
    for sym, g in st.groupby("sym"):
        f = BARS / f"{sym}.parquet"
        if not f.exists():
            continue
        b = pd.read_parquet(f, columns=["high", "low", "close"])
        if b.index.tz is None:
            b.index = b.index.tz_localize("America/New_York")
        else:
            b.index = b.index.tz_convert("America/New_York")
        bd = b.index.date
        for r in g.itertuples():
            day = r.et.date()
            m = bd == day
            if not m.any():
                continue
            bb = b[m]
            bb = bb[(bb.index >= r.et.floor("min")) & (bb.index.strftime("%H%M").astype(int) <= 1555)]
            if not len(bb):
                continue
            nb += 1
            h, l, c = bb.high.to_numpy(), bb.low.to_numpy(), bb.close.to_numpy()
            for k in cont:
                stop = r.entry - r.s * k * r.rps
                kind, px = "flat", c[-1]
                for i in range(len(c)):
                    if (r.s == 1 and l[i] <= stop) or (r.s == -1 and h[i] >= stop):
                        kind, px = "stop", stop
                        break
                    if (r.s == 1 and h[i] >= r.target) or (r.s == -1 and l[i] <= r.target):
                        kind, px = "target", r.target
                        break
                g_ = r.s * (px - r.entry) / r.rps
                if kind == "stop":
                    rk = (-k + r.s_net) / k
                else:
                    rk = (g_ - cof(r.setup, kind)) / k
                cont[k][r.Index] = rk
    for k, dct in cont.items():
        sr = pd.Series(dct, dtype=float)
        t.loc[sr.index, f"r{k}"] = sr.to_numpy()
    print("stop exits", len(st), "continued on bars", nb)
    t["date"] = t.date.astype(str)
    keep = ["account", "setup", "symbol", "date", "kind", "R", "mfe_r", "mae_r", "s_net", "C"] + [f"r{k}" for k in KS]
    t[keep].to_parquet("/dev/shm/stopw_b/live_trades_k.parquet")


if __name__ == "__main__":
    main()
