"""VRL-1125 (BDI step 3, COVERAGE: a long that earns on the V-days where Primary's gap-down shorts lose).
V-Reclaim Laggard Long: when SPY, after a morning dip, reclaims its open, buy the liquid names still well below their
own open and below VWAP (the Move Hunt precursor of 11-25: long movers came from fromOpen q1 / below VWAP / far from
HOD; the family's stopped names closed above their stops). Different from bdi1027-index-reclaim-leaders-long (parked:
bought the LEADERS on a QQQ reclaim; every row lost in down sessions).

Pre-declared, 2 configs (A, B), written before the first run:
  Trigger (per session): SPY lab spy_fo min over the 09:50.. rows so far <= -0.50%; first 5-min bar 10:30..13:30 with
           spy_fo >= 0 while the previous bar's spy_fo < 0.  At most one trigger per session.
  Names:   adv20 >= $95M, close >= $5, vwapDistPct < 0, fromOpen in daily-ATR units <= -0.5 (A) / <= -1.0 (B), at the
           trigger bar.  One lot per symbol-day.
  Trade:   buy at the trigger bar close; stop = entry - 0.5 x daily ATR (1R); exit at the stop (5-min bar low through it,
           filled at the stop + 2c slippage cost) or at the last bar <= 15:55 close.  No target.
  Costs:   LR8 research basis = entry (1c + 1 bp) x mcf.research.gates.tod_cost_mult, exit 1c + 1 bp, +2c on stops.
  Control: every adv20 >= $95M name (close >= $5) at the same trigger bar, same geometry (day-matched random long).
Data: research/history2y frames, 22 open months 2024-10..2026-11; the locked block 2024-11-01..2025-02-28 is never read
(lib refuses it; asserted below). 5-min exits are coarser than the live 1-minute book.
Pass (BAR90 Testing bar, N = 2 -> t >= 1.35): avg R after costs > 0, day-clustered t >= 1.35, >= 20 trigger days,
w/o best day > 0 and best-day share < 50%, > 0 in fit AND check halves, > 0 in up AND down sessions (SPY open->close
+-0.3%), positive months >= 54%, avg R minus control > 0.
Usage: python vrl_lab.py.   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, "/home/user/MCF")
import research.history2y.lib as lib  # noqa: E402
from mcf.research.gates import tod_cost_mult  # noqa: E402

COLS = ["symbol", "date", "tod", "close", "high", "low", "fromOpen", "vwapDistPct", "atr_d", "adv20", "spy_fo"]
THR = {"A": -0.5, "B": -1.0}


def month(m):
    f = lib.load_month(m, columns=None, context=True)[COLS]
    f["symbol"] = f.symbol.astype(str); f["date"] = f.date.astype(str)
    assert not ((f.date >= "2024-11-01") & (f.date <= "2025-02-28")).any(), "locked row"
    out = []
    for d, g in f.groupby("date"):
        sp = g.groupby("tod").spy_fo.first().sort_index()
        mn = sp.cummin(); prev = sp.shift(1)
        ok = (sp.index >= 1030) & (sp.index <= 1330) & (mn <= -0.5).to_numpy() & (sp >= 0).to_numpy() & (prev < 0).to_numpy()
        if not ok.any():
            continue
        tt = sp.index[np.argmax(ok)]
        x = g[(g.tod == tt) & (g.adv20 >= 95e6) & (g.close >= 5) & (g.atr_d > 0)].copy()
        x["fo_atr"] = x.fromOpen / 100 * x.close / x.atr_d
        x = x[np.isfinite(x.fo_atr)]
        later = g[(g.tod > tt) & (g.tod <= 1555)].sort_values("tod")
        lw = later.groupby("symbol")
        for r in x.itertuples():
            if r.symbol not in lw.groups:
                continue
            p = lw.get_group(r.symbol)
            e = r.close; rps = 0.5 * r.atr_d; st = e - rps
            hit = p.low.to_numpy() <= st
            if hit.any():
                px, kind = st, 1
            else:
                px, kind = float(p.close.iloc[-1]), 0
            ec = (0.01 + e * 1e-4) * float(tod_cost_mult(np.array([tt]))[0])
            xc = 0.01 + px * 1e-4 + (0.02 if kind else 0.0)
            out.append(dict(date=d, tod=int(tt), symbol=r.symbol, fo_atr=r.fo_atr, vwap=r.vwapDistPct, entry=e, px=px, kind=kind,
                            r=(px - e - ec - xc) / rps, r_gross=(px - e) / rps, spy_at=float(sp.loc[tt]), spy_min=float(mn.loc[tt])))
    return pd.DataFrame(out)


def ct(t):
    m = t.r.mean(); e = (t.r - m).groupby(t.date).sum(); se = np.sqrt((e ** 2).sum()) / len(t)
    return m / se if se > 0 else np.nan


def summ(t, spy, name):
    day = t.groupby("date").r.sum(); best = day.idxmax(); tot = day.sum()
    fit = (t.date <= "2024-10-31") | ((t.date >= "2025-03-01") & (t.date <= "2025-09-30")); chk = t.date >= "2025-10-01"
    ty = t.date.map(spy); mo = t.groupby(t.date.str[:7]).r.sum()
    return dict(cfg=name, n=len(t), days=day.size, avg_r=round(t.r.mean(), 4), avg_r_gross=round(t.r_gross.mean(), 4), win=round((t.r > 0).mean(), 3),
                total_r=round(tot, 1), t_day=round(ct(t), 2), avg_wo_best=round(t.loc[t.date != best, "r"].mean(), 4), best_day=best,
                best_share=round(day.max() / tot, 3) if tot > 0 else None, avg_fit=round(t[fit].r.mean(), 4), avg_check=round(t[chk].r.mean(), 4),
                avg_up=round(t[ty == "up"].r.mean(), 4), n_up=int((ty == "up").sum()), avg_down=round(t[ty == "down"].r.mean(), 4),
                n_down=int((ty == "down").sum()), avg_flat=round(t[ty == "flat"].r.mean(), 4), pos_months=f"{(mo > 0).sum()}/{len(mo)}",
                stops=round(t.kind.mean(), 3))


if __name__ == "__main__":
    ms = [m for m in lib.months() if m not in lib.LOCKED_MONTHS]
    T = pd.concat([month(m) for m in ms], ignore_index=True)
    sys.path.insert(0, str(HERE.parents[2] / "research/ultimate_1119/top10"))
    import bench10 as B
    spy = B.spy_t1()
    rows = [summ(T, spy, "control (all liquid names at the trigger bar)")]
    for k, th in THR.items():
        rows.append(summ(T[(T.fo_atr <= th) & (T.vwap < 0)], spy, f"{k} (fo <= {th} ATR, below VWAP)"))
    R = pd.DataFrame(rows); pd.set_option("display.width", 250)
    print(f"trigger sessions {T.date.nunique()} of {len(spy)} open sessions; months {len(ms)}")
    print(R.T.to_string())
    for k, th in THR.items():
        x = T[(T.fo_atr <= th) & (T.vwap < 0)]; c = T.groupby("date").r.mean(); a = x.groupby("date").r.mean()
        j = pd.concat([a, c], axis=1, keys=["a", "c"]).dropna(); dif = j.a - j.c
        print(f"{k} minus control per trigger day: {dif.mean():+.4f}R (days {len(dif)}, t {dif.mean() / (dif.std(ddof=1) / np.sqrt(len(dif))):+.2f})")
    x = T[T.date == "2026-11-25"]
    print("11-25 in the lab frames:", "absent" if x.empty else f"trigger {x.tod.iloc[0]}, A n {((x.fo_atr <= -0.5) & (x.vwap < 0)).sum()} avg {x[(x.fo_atr <= -0.5) & (x.vwap < 0)].r.mean():+.3f}R")
    R.to_csv(HERE / "vrl_lab_results.csv", index=False)
    print("Educational only - not financial advice.")
