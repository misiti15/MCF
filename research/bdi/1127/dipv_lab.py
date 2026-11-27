"""DIPV-1127 (BDI step 3, CAPTURE + COVERAGE): Dip-Morning In-Play Reversal Long.
Source: 11-27 Move Hunt (research/bdi/moves/moves_1127_out.txt, k6_today_out.txt): SPY was -0.56% from its open at 09:50
(low -0.73% 10:05) and closed the half day +0.49%; the MOVEHUNT_1127 ranker's 09:50 top-20 held 4 of the day's 34 big
movers (10x chance) and all 5 movers in its top 50 REVERSED their 09:30-09:49 direction (down early, up after); 11-25
showed the same shape (long movers = names below their open decided around SPY's morning low). MOVEHUNT_1127 found
direction a coin flip unconditionally and S2 FADE failed on all days; this asks whether the fade works on the day type
where it should: an index-dip morning.
Mechanism tag (C3-MECH): day-type condition known at 09:50 = SPY <= -0.40% from its open; reason = on index-dip
mornings the early weakness of in-play names is largely index beta plus opening-auction selling, and the index's open
dip tends to mean-revert (IDX3 / QQQOPEN_1127: SPY -0.75% by 09:55, n 57, +0.42R, t 2.20); in-play names should carry
that rebound with higher beta. Falsifiable: if the names do no better than all down-from-open liquid names bought at the
same bar (control), the edge is the index, not the selection.

Pre-declared, 1 config (written before the first run; nothing tuned after):
  Trigger (per session): lab spy_fo at the 09:50 bar (tod 950) <= -0.40%.
  List:    adv20 >= $95M, close >= $5, atr_d > 0; in-play rank = mean of the day's percentile ranks at 09:50 of
           range_atr = dist_hod_atr + dist_lod_atr, |gap| / atr_pct_d, volumeRatio (fixed equal weights = the unfitted
           MOVEHUNT K5 combo on lab columns; K6's fitted weights need 1-min features the lab frames lack); top 20.
  Names:   of the top 20, those with fromOpen < 0 at 09:50 (down from their open).
  Trade:   buy at the 09:50 bar close; stop = the day's low so far (close - dist_lod_atr x atr_d) - 0.10 x atr_d, risk
           floored at 0.10 x atr_d; exit at the stop (5-min low through it; filled at the stop, +2c) or the last bar
           <= 15:55 close (half days: the last bar). No target.
  Costs:   LR8 research basis (as vrl_lab): entry (1c + 1 bp) x tod_cost_mult, exit 1c + 1 bp, +2c on stops.
  Control: every liquid (adv20 >= $95M, close >= $5) name down from its open at the same bar, same geometry.
Data: research/history2y frames, 22 open months 2024-10..2026-11 (to 11-04); the locked block 2024-11-01..2025-02-28 is
never read (lib refuses it; asserted). 5-min exits are coarser than the live 1-minute book.
Pass (BAR90 Testing bar, N = 1 -> day t >= 1.28): avg R after costs > 0, day-clustered t >= 1.28, >= 20 trigger days,
w/o best day > 0 and best-day share < 50%, > 0 in fit AND check, > 0 in up AND down sessions (SPY open->close +-0.3%),
positive months >= 54%, avg R minus control per trigger day > 0.
Usage: python dipv_lab.py.   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, "/home/user/MCF")
import research.history2y.lib as lib  # noqa: E402
from mcf.research.gates import tod_cost_mult  # noqa: E402

COLS = ["symbol", "date", "tod", "close", "low", "fromOpen", "gap", "volumeRatio", "dist_hod_atr", "dist_lod_atr", "atr_d", "adv20", "spy_fo"]


def month(m):
    f = lib.load_month(m, columns=None, context=True)[COLS]
    f["symbol"] = f.symbol.astype(str); f["date"] = f.date.astype(str)
    assert not ((f.date >= "2024-11-01") & (f.date <= "2025-02-28")).any(), "locked row"
    out = []
    ec = float(tod_cost_mult(np.array([950]))[0])
    for d, g in f.groupby("date"):
        x = g[g.tod == 950]
        if x.empty or x.spy_fo.iloc[0] > -0.40:
            continue
        x = x[(x.adv20 >= 95e6) & (x.close >= 5) & (x.atr_d > 0)].copy()
        x["range_atr"] = x.dist_hod_atr + x.dist_lod_atr
        x["gap_atr"] = (x.gap / 100 * x.close / x.atr_d).abs()
        x["inplay"] = (x.range_atr.rank(pct=True) + x.gap_atr.rank(pct=True) + x.volumeRatio.rank(pct=True)) / 3
        x["top20"] = x.inplay.rank(ascending=False, method="first") <= 20
        x = x[x.fromOpen < 0]
        later = g[(g.tod > 950) & (g.tod <= 1555)].sort_values("tod"); lw = later.groupby("symbol")
        for r in x.itertuples():
            if r.symbol not in lw.groups:
                continue
            p = lw.get_group(r.symbol); e = r.close
            st = e - r.dist_lod_atr * r.atr_d - 0.10 * r.atr_d; rps = max(e - st, 0.10 * r.atr_d); st = e - rps
            hit = p.low.to_numpy() <= st
            px, kind = (st, 1) if hit.any() else (float(p.close.iloc[-1]), 0)
            c_in = (0.01 + e * 1e-4) * ec; c_out = 0.01 + px * 1e-4 + (0.02 if kind else 0.0)
            out.append(dict(date=d, symbol=r.symbol, top20=bool(r.top20), spy_at=float(r.spy_fo), entry=e, px=px, kind=kind,
                            r=(px - e - c_in - c_out) / rps, r_gross=(px - e) / rps))
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
    A = T[T.top20]
    R = pd.DataFrame([summ(T, spy, "control (all liquid names down from open at 09:50)"), summ(A, spy, "DIPV A (in-play top 20, down from open)")])
    pd.set_option("display.width", 250)
    print(f"trigger sessions {T.date.nunique()} of {len(spy)} open sessions; months {len(ms)}")
    print(R.T.to_string())
    c = T.groupby("date").r.mean(); a = A.groupby("date").r.mean()
    j = pd.concat([a, c], axis=1, keys=["a", "c"]).dropna(); dif = j.a - j.c
    print(f"A minus control per trigger day: {dif.mean():+.4f}R (days {len(dif)}, t {dif.mean() / (dif.std(ddof=1) / np.sqrt(len(dif))):+.2f})")
    ok = [R.avg_r[1] > 0, R.t_day[1] >= 1.28, R.days[1] >= 20, R.avg_wo_best[1] > 0, (R.best_share[1] or 9) < 0.5, R.avg_fit[1] > 0,
          R.avg_check[1] > 0, R.avg_up[1] > 0, R.avg_down[1] > 0, eval(R.pos_months[1]) >= 0.54, dif.mean() > 0]
    print("pass checks [avg>0, t>=1.28, days>=20, wo_best>0, share<50%, fit>0, check>0, up>0, down>0, months>=54%, minus control>0]:", ok,
          "->", "PASS" if all(ok) else "FAIL")
    R.to_csv(HERE / "dipv_lab_results.csv", index=False)
    print("Educational only - not financial advice.")
