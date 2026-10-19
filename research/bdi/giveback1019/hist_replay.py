"""Step 5b: replay the 8 pre-declared exit/entry rules (PLAN.md addendum) on the long-history entries of the Primary lab
setups, 1-min SIP bars from data/cache_hist (open history only; the entries file carries no locked dates and this
script asserts it). Same simulator and costs as the live replays; entry cost 1c + 1 bps x the time-of-day multiplier.
Writes hist_results.csv, hist_by_setup.csv, hist_out.txt. Educational only - not financial advice."""
import math
import sys
import types
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
from common import OUT, S, SLIP_BPS, SLIP_SH, simulate, TZ  # noqa: E402
from mcf.research import gates as G  # noqa: E402

GEOMK = G.GEOMK
VAR = {"BASE": {}, "WIDE125": dict(stop_mult=1.25), "WIDE150": dict(stop_mult=1.5), "TS30": dict(time_n=30),
       "TS60": dict(time_n=60), "BE050": dict(be_at=0.5), "SO05BE": dict(scale_at=0.5, scale_be=True)}
FILTERS = ["NOISE4", "CUT1100"]
N_TOTAL = 71
BAR = max(1.5, math.sqrt(2 * math.log(N_TOTAL)))


def one_symbol(args):
    sym, ent = args
    f = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"
    if not f.exists():
        return []
    b = pd.read_parquet(f, columns=["open", "high", "low", "close"])
    b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ) if b.index.tz is not None else b.index.tz_localize(TZ)
    days = {str(d): g for d, g in b.groupby(b.index.date)}
    out = []
    for e in ent.itertuples():
        d = str(e.date)
        bd = days.get(d)
        if bd is None:
            continue
        up, dn = GEOMK[e.geom]
        Ru = 0.25 * e.atr_d
        s = 1 if e.side == "long" else -1
        hh, mm = divmod(int(e.tod), 100)
        t0 = pd.Timestamp(f"{d} {hh:02d}:{mm:02d}", tz=TZ)
        r = types.SimpleNamespace(date=d, symbol=sym, side=s, entry=float(e.close), R=dn * Ru, shares=1,
                                  target=float(e.close) + s * up * Ru, exit_reason="stop", nt=t0 - pd.Timedelta(minutes=1),
                                  et=None)
        entry_cost = (SLIP_SH + e.close * SLIP_BPS / 1e4) * float(G.tod_cost_mult([e.tod])[0])
        pre = bd[bd.index < t0].tail(15)
        atr1 = np.nan
        if len(pre) >= 5:
            tr = np.maximum(pre.high - pre.low, np.maximum((pre.high - pre.close.shift()).abs(), (pre.low - pre.close.shift()).abs()))
            atr1 = tr.iloc[1:].mean()
        row = dict(date=d, symbol=sym, setup=e.setup, tod=int(e.tod), frame_r=e.frame_r, stop_atr1=(dn * Ru) / atr1 if atr1 > 0 else np.nan)
        ok = True
        for k, kw in VAR.items():
            v = simulate(r, b=bd, **kw)
            if v is None:
                ok = False
                break
            row[k] = (v[0] - entry_cost) / (dn * Ru)          # original R, costs in
            if k == "BASE":
                row["base_reason"] = v[1]
        if ok:
            out.append(row)
    return out


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / math.sqrt(len(x))) if len(x) > 1 and x.std(ddof=1) > 0 else np.nan


if __name__ == "__main__":
    E = pd.read_parquet(S / "hist_entries.parquet")
    ds = E.date.astype(str)
    assert not ((ds >= "2024-11-01") & (ds <= "2025-02-28")).any(), "locked block present"
    with Pool(4) as p:
        res = p.map(one_symbol, list(E.groupby("symbol")), chunksize=4)
    H = pd.DataFrame([x for r in res for x in r])
    H["split"] = np.where(H.date <= "2025-12-31", "train", np.where(H.date <= "2026-10-07", "valid", "forward"))
    H["NOISE4"] = np.where(H.stop_atr1 < 4, 0.0, H.BASE)                  # filter: skipped trade = 0 R
    H["CUT1100"] = np.where(H.tod >= 1100, 0.0, H.BASE)
    H.to_parquet(S / "hist_sim.parquet", index=False)
    sys.path.insert(0, str(ROOT / "research/history2y"))
    from lib import regimes
    rg = regimes().reset_index()
    rg["date"] = rg["date"].astype(str)
    rcol = "regime"
    H = H.merge(rg[["date", "regime"]], on="date", how="left")
    out = []
    P = lambda *x: out.append(" ".join(str(y) for y in x))
    P(f"entries simulated {len(H)} of {len(E)}; baseline fidelity: corr(sim BASE, frame production R) {H.BASE.corr(H.frame_r):.3f}, "
      f"mean BASE {H.BASE.mean():+.4f} vs frame {H.frame_r.mean():+.4f}; stop/ATR1m median {H.stop_atr1.median():.2f}, share < 4: {(H.stop_atr1 < 4).mean():.2f}")
    rows = []
    for k in list(VAR)[1:] + FILTERS:
        for sp in ("train", "valid", "forward"):
            x = H[H.split == sp]
            dd = (x[k] - x.BASE).groupby(x.date).sum()
            mo = (x[k] - x.BASE).groupby(x.date.str[:7]).sum()
            rows.append(dict(config=k, split=sp, n=len(x), days=len(dd), base_exp=round(x.BASE.mean(), 4), var_exp=round(x[k].mean(), 4),
                             delta=round((x[k] - x.BASE).mean(), 4), t_day=round(tstat(dd), 2), months_pos=f"{int((mo > 0).sum())}/{len(mo)}",
                             d_up=round((x[k] - x.BASE)[x.regime == "up"].mean(), 4), d_down=round((x[k] - x.BASE)[x.regime == "down"].mean(), 4)))
    Rz = pd.DataFrame(rows)
    def verdict(k):
        tr, va = Rz[(Rz.config == k) & (Rz.split == "train")].iloc[0], Rz[(Rz.config == k) & (Rz.split == "valid")].iloc[0]
        ok = tr.delta > 0 and va.delta > 0 and va.t_day >= BAR and va.d_up > 0 and va.d_down > 0
        return "supports" if ok else "not supported"
    Rz["verdict"] = Rz.config.map({k: verdict(k) for k in Rz.config.unique()})
    Rz.to_csv(OUT / "hist_results.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    P(f"bar (N={N_TOTAL}) {BAR:.2f}; regimes column used: {rcol}")
    P(Rz.to_string(index=False))
    bs = []
    for (st, sp), x in H[H.split != "forward"].groupby(["setup", "split"]):
        d = {"setup": st, "split": sp, "n": len(x), "BASE": round(x.BASE.mean(), 3)}
        for k in list(VAR)[1:] + FILTERS:
            d[k] = round((x[k] - x.BASE).mean(), 3)
        bs.append(d)
    B = pd.DataFrame(bs)
    B.to_csv(OUT / "hist_by_setup.csv", index=False)
    P("\nper setup: baseline exp R and each rule's delta (R/trade)")
    P(B.to_string(index=False))
    P("\nbaseline exit reasons:", H.base_reason.value_counts().to_dict())
    open(OUT / "hist_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
    print("\n".join(out))
