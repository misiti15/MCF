"""Anecdote (NOTES.md 1.9): the 10 trades the owner flagged on 2026-10-08 plus GEV. One live paper session - a diagnosis,
not evidence. Guard values at the live signal bar (last 5-min bar completed at signal time) with the same feature code as
the history (features.py), from the read-only 1-min bars in data/cache/bdi1008; E1 / E2 / C re-walked on 1-minute bars
from the live fill with the live stop and target (engine cost model, as score.sim1).
Output: anecdote.csv.   python research/bdi/trendguard/anecdote.py
Educational only - not financial advice.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(HERE)]
import features as FT  # noqa: E402
import score as S  # noqa: E402
from mcf.backtest.engine import Costs  # noqa: E402
from mcf.config import load_config  # noqa: E402

IDS = [121, 128, 123, 118, 108, 124, 112, 126, 127, 120, 113]      # owner's 10 worst + GEV (E2 case)
DAY = "2026-10-08"


def main():
    cs = Costs.from_cfg(load_config()["costs"])
    T = pd.read_csv(ROOT / "research/bdi/daily/2026-10-08/trades.csv")
    T = T[T["id"].isin(IDS)].set_index("id").loc[IDS].reset_index()
    out = []
    for t in T.itertuples():
        m1 = pd.read_parquet(ROOT / "data/cache/bdi1008" / f"{t.symbol}.parquet")
        F = FT.features(m1)
        F["dayid"] = pd.factorize(F["date"])[0]
        F = F.reset_index(names="ts")
        sd = int(t.side)
        st = pd.Timestamp(f"{DAY} {t.signal_time}")
        mm = st.hour * 60 + st.minute
        tod5 = (mm // 5 * 5) // 60 * 100 + (mm // 5 * 5) % 60
        row = F.index[(F["date"] == pd.Timestamp(DAY)) & (F["tod"] == tod5)]
        if not len(row):
            continue
        r = int(row[0])
        bl = S.block_arrays(F, sd)
        trig, div = S.confirm_arrays(F, sd)
        x = F.loc[r]
        rec = {"id": t.id, "symbol": t.symbol, "setup": t.setup, "side": "S" if sd == -1 else "L", "signal_bar_end": tod5,
               "r_live": t.r_live, "vwap_dist_pct": round((x.close / x.vwap - 1) * 100, 2), "vwap_sd_z": round((x.close - x.vwap) / x.vsd, 2) if x.vsd > 0 else None,
               "ema9_dist_pct": round((x.close / x.ema9 - 1) * 100, 2), "ema9_slope": "up" if x.ema9_sl > 0 else "down",
               "ema21_slope": "up" if x.ema21_sl > 0 else "down", "rsi": round(x.rsi, 1), "cmf": round(x.cmf, 3),
               "cmf_rising": bool(x.cmf_sl > 0), "obv_slope_pos": bool(x.obv_sl > 0), "adx": round(x.adx, 1),
               "di_gap": round(x.pdi - x.mdi, 1), "above_vah": bool(x.close > x.vah), "below_val": bool(x.close < x.val)}
        for k, v in bl.items():
            rec[k] = bool(v[r])
        # 1-min path of the day from the live fill
        d = m1[m1.index.strftime("%Y-%m-%d") == DAY].copy()
        end = d.index + pd.Timedelta(minutes=1)
        d["tod_end"] = np.where(end.minute % 5 == 0, end.hour * 100 + end.minute, -1)
        e9 = F[F["date"] == pd.Timestamp(DAY)].set_index("tod")["ema9"]
        E9 = d["tod_end"].map(e9).to_numpy(float)
        HM = (d.index.hour * 100 + d.index.minute).to_numpy(np.int64)
        et = pd.Timestamp(f"{DAY} {t.entry_time}")
        j = int(np.searchsorted(HM, et.hour * 100 + et.minute))
        O, H, L, C = (d[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        tgt = float(t.target) if pd.notna(t.target) else np.nan
        e2 = (x.hi6 + 0.1 * t.atr_d) if sd == -1 else (x.lo6 - 0.1 * t.atr_d)
        for mode, ex in enumerate(S.EXITS):
            rec[f"sim_{ex}"] = round(S.sim1(j, sd, float(t.entry), float(t.stop), tgt if np.isfinite(tgt) else 0.0, bool(np.isfinite(tgt)), mode, e2,
                                            O, H, L, C, E9, HM, cs.bps, cs.per_share, cs.stop_extra_per_share), 2)
        rec["E2_stop_dist_R"] = round(min(1.5, sd * (float(t.entry) - e2) / abs(float(t.entry) - float(t.stop))), 2)
        for N in (3, 6, 12):
            e = S.c_entries(np.array([r]), N, sd, F["high"].to_numpy(), F["low"].to_numpy(), trig, div, F["tod"].to_numpy(np.int64),
                            F["dayid"].to_numpy(np.int64), 1500)[0]
            if e < 0:
                rec[f"C{N}"] = "dropped"
                continue
            px = F.loc[e, "close"]
            fill = px * (1 + sd * cs.bps / 1e4) + sd * cs.per_share
            stop = fill + (float(t.stop) - float(t.entry))
            tg = tgt + (fill - float(t.entry)) if np.isfinite(tgt) else 0.0
            jj = int(np.searchsorted(HM, F.loc[e, "tod"]))
            rr = S.sim1(jj, sd, fill, stop, tg, bool(np.isfinite(tgt)), 0, np.nan, O, H, L, C, E9, HM, cs.bps, cs.per_share, cs.stop_extra_per_share)
            rec[f"C{N}"] = f"{int(F.loc[e, 'tod'])}: {rr:+.2f}"
        out.append(rec)
    df = pd.DataFrame(out)
    df.to_csv(HERE / "anecdote.csv", index=False)
    pd.set_option("display.width", 300, "display.max_columns", 80)
    print(df.to_string())


if __name__ == "__main__":
    main()
