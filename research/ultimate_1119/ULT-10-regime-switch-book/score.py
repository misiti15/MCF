"""ULT-10 scoring: ULT-09 component grid (fit, needed for set b), the 4 book configs (fit), selection, fitsel freeze,
single check score, random control, diagnostics.
    python score.py WORK fit        # ULT-09 grid + book grid on FIT, writes fit_grid.json + fitsel.json
    python score.py WORK check      # chosen config ONCE on CHECK (+ random control), then the plateau diagnostic
Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bt  # noqa: E402

MOD = bt.load_mod()
PRIO = {leg: i for i, leg in enumerate(["02", "04", "09", "03", "05", "07", "01", "06", "08"])}
BOOK = {"10a": (0.30, "a", "T30-first"), "10b": (0.30, "b", "T30-fitsel"), "10c": (0.50, "a", "T50-first"),
        "10d": (0.50, "b", "T50-fitsel")}


def regime_col(S, t):
    s930, r30 = S.s930.to_numpy(), S.r30.to_numpy()
    out = np.full(len(S), "", dtype=object)
    with np.errstate(invalid="ignore"):
        ok = np.isfinite(s930)
        fl = ok & np.isfinite(r30) & (r30 < -t)
        dn = ok & ~fl & (s930 <= -t)
        up = ok & ~fl & ~dn & (s930 >= t)
        fa = ok & ~fl & ~dn & ~up
    out[fl], out[dn], out[up], out[fa] = "flush", "down", "up", "flat"
    return out


def candidates(S, legs):
    """legs: list of (leg, flag mask (bool array), exit spec, window hi or None). -> long candidate table."""
    parts = []
    for leg, m, ex in legs:
        side = 1 if MOD.LEG_SIDE[leg] == "long" else -1
        sd = "L" if side == 1 else "S"
        c = S.loc[m, ["symbol", "date", "tod", "entry", "R", "adv20"]].copy()
        c["leg"], c["side"], c["ex"] = leg, side, ex
        c["px"], c["kind"], c["xt"] = (S.loc[m, f"{a}_{sd}{ex}"].to_numpy() for a in ("px", "k", "x"))
        c["dn"] = bt.SPECS[ex][1]
        c["src"] = S.index[m]
        parts.append(c)
    C = pd.concat(parts)
    C = C[C.kind >= 0]
    C["prio"] = C.leg.map(PRIO)
    return C


def chassis(C, cap=30):
    C = C.sort_values(["date", "tod", "adv20", "prio"], ascending=[True, True, False, True], kind="mergesort")
    keep = []
    for _, g in C.groupby("date", sort=False):
        n_day, st = 0, {}
        for i, sym, t, x in zip(g.index, g.symbol.to_numpy(), bt.m2(g.tod.to_numpy()), g.xt.to_numpy()):
            if cap and n_day >= cap:
                break
            n, free = st.get(sym, (0, -1))
            if n >= 2 or t < free:
                continue
            keep.append(i); n_day += 1; st[sym] = (n + 1, x + 30)
    s = C.loc[keep].copy()
    s["r"] = bt.r_after_cost(s.entry.to_numpy(), s.R.to_numpy(), s.tod.to_numpy(), s.px.to_numpy(), s.kind.to_numpy(),
                             s.side.to_numpy(), s.dn.to_numpy())
    s["hold"] = s.xt - bt.m2(s.tod.to_numpy())
    return s


def stats(s, days, daytype=None):
    nd = len(days)
    if not len(s):
        return dict(trades=0, per_session=0.0, total=0.0, avg=float("nan"))
    by = s.groupby("date").r.sum()
    tot = float(s.r.sum())
    best = by.idxmax()
    wo = s[s.date != best]
    out = dict(trades=int(len(s)), per_session=len(s) / nd, traded_sessions=int(by.size), win=float((s.r > 0).mean()),
               avg=float(s.r.mean()), avg_wo_best=float(wo.r.mean()) if len(wo) else float("nan"),
               best_day=str(best), best_day_r=float(by.max()),
               best_share=float(by.max() / tot) if tot > 0 else None, total=tot, r_session=tot / nd,
               worst_day=float(by.min()), worst_day_date=str(by.idxmin()), median_hold=float(s.hold.median()),
               side={k: dict(n=int(len(g)), avg=float(g.r.mean()), total=float(g.r.sum()))
                     for k, g in s.groupby(np.where(s.side > 0, "long", "short"))},
               leg={k: dict(n=int(len(g)), avg=float(g.r.mean()), total=float(g.r.sum())) for k, g in s.groupby("leg")})
    if daytype is not None:
        dt = s.date.map(daytype)
        out["daytype"] = {k: dict(n=int(len(g)), avg=float(g.r.mean()), total=float(g.r.sum()))
                          for k, g in s.groupby(dt)}
    return out


def spy_daytype(half):
    d = pads.dataset(str(bt.CACHE / "SPY.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    tz = "America/New_York"
    L0, L1, C0 = (pd.Timestamp(x, tz=tz) for x in ("2024-11-01", "2025-03-01", "2025-10-01"))
    filt = ((fld < L0) | ((fld >= L1) & (fld < C0))) if half == "fit" else (fld >= C0)
    b = d.to_table(filter=filt).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(tz)
    bt.no_locked(np.unique(b.index.date))
    hm = b.index.hour * 100 + b.index.minute
    b = b[(hm >= 930) & (hm <= 1559)]
    g = b.groupby(b.index.date)
    ret = (g.close.last() / g.open.first() - 1) * 100
    return {str(k): ("up" if v > 0.30 else "down" if v < -0.30 else "flat") for k, v in ret.items()}


def ult09_grid(S, days):
    out = {}
    for name, p in bt.U09.items():
        m = (S.f_09sup.to_numpy() & (S.s950.to_numpy() <= p["s_t"]) & (S.tod.to_numpy() <= p["w_hi"]))
        s = chassis(candidates(S, [("09", m, p["exit"])]))
        out[name] = dict(p, **stats(s, days))
    elig = {k: v for k, v in out.items() if v["per_session"] >= 2.0}
    pool = elig or out
    sel = max(pool, key=lambda k: (round(pool[k]["total"], 9), -list(bt.U09).index(k)))
    return out, sel, bool(elig)


def book_legs(S, t, cfg_set, sel09):
    reg = regime_col(S, t)
    legs = []
    for leg, p in MOD.CONFIGS[cfg_set].items():
        if leg == "09":
            q = bt.U09["09a" if cfg_set == "a" else sel09]
            m = S.f_09sup.to_numpy() & (S.s950.to_numpy() <= q["s_t"]) & (S.tod.to_numpy() <= q["w_hi"])
            ex = q["exit"]
        else:
            m = S["f_" + p["cfg"]].to_numpy()
            ex = p["exit"]
        legs.append((leg, m & (reg == MOD.LEG_REGIME[leg]), ex))
    return legs


def load(W, half):
    S = pd.read_parquet(W / f"walked_{half}.parquet")
    days = pd.read_parquet(W / f"days_{half}.parquet").date.tolist()
    bt.no_locked(S.date.unique()); bt.no_locked(days)
    return S, days


def random_control(W, half, s, seeds=(1, 2, 3)):
    """Same symbol-session, same leg window, same side and exit; random intake-U bar; no chassis."""
    P = pd.read_parquet(W / f"pool_{half}.parquet")
    P = P.set_index(["symbol", "date"]).sort_index()
    rows = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        for r in s.itertuples():
            lo, hi = cfg_window(r.leg)
            try:
                g = P.loc[(r.symbol, r.date)]
            except KeyError:
                continue
            g = g[(g.tod >= lo) & (g.tod <= hi)]
            if not len(g):
                continue
            q = g.iloc[int(rng.integers(len(g)))]
            rows.append(dict(seed=seed, symbol=r.symbol, date=r.date, tod=int(q.tod), entry=float(q.close),
                             R=0.25 * float(q.atr_d), side=int(r.side), ex=r.ex, dn=float(r.dn)))
    Rn = pd.DataFrame(rows).reset_index(drop=True)
    Wk = bt.walk(Rn, half)
    sd = np.where(Wk.side > 0, "L", "S")
    px = np.array([Wk.at[i, f"px_{a}{e}"] for i, a, e in zip(Wk.index, sd, Wk.ex)], float)
    kd = np.array([Wk.at[i, f"k_{a}{e}"] for i, a, e in zip(Wk.index, sd, Wk.ex)], float)
    ok = kd >= 0
    r = bt.r_after_cost(Wk.entry.to_numpy()[ok], Wk.R.to_numpy()[ok], Wk.tod.to_numpy()[ok], px[ok], kd[ok],
                        Wk.side.to_numpy()[ok], Wk.dn.to_numpy()[ok])
    return dict(n=int(ok.sum()), avg=float(np.mean(r)), per_seed={int(k): float(np.mean(r[Wk.seed.to_numpy()[ok] == k]))
                                                                   for k in seeds})


_CUR = {}


def cfg_window(leg):
    return _CUR["windows"][leg]


def set_windows(cfg_set, sel09):
    w = {leg: p["window"] for leg, p in MOD.CONFIGS[cfg_set].items()}
    q = bt.U09["09a" if cfg_set == "a" else sel09]
    w["09"] = (1030, q["w_hi"])
    _CUR["windows"] = w


def jd(o, p):
    p.write_text(json.dumps(o, indent=1, default=lambda x: None if isinstance(x, float) and np.isnan(x) else str(x)))


if __name__ == "__main__":
    W, half = Path(sys.argv[1]), sys.argv[2]
    if half == "fit":
        S, days = load(W, "fit")
        dtp = spy_daytype("fit")
        g09, sel09, ok09 = ult09_grid(S, days)
        print("ULT-09 grid (fit):")
        for k, v in g09.items():
            print(f"  {k} S_T {v['s_t']:+.2f} W{v['w_hi']} {v['exit']:>4}  n {v['trades']:5d} /s {v['per_session']:.2f} "
                  f"avg {v.get('avg', float('nan')):+.3f} tot {v['total']:+.1f}")
        print("  selected", sel09, "reached 2/session:", ok09)
        res = {}
        for name, (t, st, lab) in BOOK.items():
            s = chassis(candidates(S, book_legs(S, t, st, sel09)))
            res[name] = dict(T=t, set=st, label=lab, **stats(s, days, dtp))
            crash = s[~s.date.between("2025-04-03", "2025-04-09")]
            res[name]["avg_ex_apr_crash"] = float(crash.r.mean())
            sc = chassis(candidates(S, book_legs(S, t, st, sel09)), cap=0)
            res[name]["uncapped"] = stats(sc, days)
            v = res[name]
            print(f"{name} {lab:11s} n {v['trades']:5d} /s {v['per_session']:5.2f} win {v['win']:.3f} avg {v['avg']:+.4f} "
                  f"wo {v['avg_wo_best']:+.4f} share {v['best_share']} tot {v['total']:+.1f} worst {v['worst_day']:+.1f}")
        elig = {k: v for k, v in res.items() if v["per_session"] >= 2.0}
        pool = elig or res
        chosen = max(pool, key=lambda k: (round(pool[k]["total"], 9), -list(BOOK).index(k)))
        jd(dict(ult09_grid=g09, ult09_selected=sel09, ult09_reached_2=ok09, book=res), HERE / "fit_grid.json")
        jd(dict(id="ULT-10-regime-switch-book", config=chosen, T=BOOK[chosen][0], set=BOOK[chosen][1],
                label=BOOK[chosen][2], ult09_selected=sel09, reached_2_per_session=bool(elig),
                rule="PLAN sec.5: highest fit total R among configs >= 2 trades/session (secondary check: avg R w/o best "
                     "day reported); ranking never by avg R/trade",
                fit=res[chosen], frozen_utc=datetime.now(timezone.utc).isoformat()), HERE / "fitsel.json")
        print("chosen", chosen)
    else:
        fs = json.loads((HERE / "fitsel.json").read_text())
        chosen, sel09 = fs["config"], fs["ult09_selected"]
        S, days = load(W, "check")
        dtp = spy_daytype("check")
        t, st, lab = BOOK[chosen]
        s = chassis(candidates(S, book_legs(S, t, st, sel09)))
        out = dict(config=chosen, label=lab, **stats(s, days, dtp))
        mid = days[len(days) // 2]
        out["first_half_avg"] = float(s[s.date < mid].r.mean())
        out["second_half_avg"] = float(s[s.date >= mid].r.mean())
        out["split_date"] = mid
        out["regime_mix"] = s.assign(reg=s.leg.map(MOD.LEG_REGIME)).groupby("reg").r.agg(["size", "mean", "sum"]).to_dict()
        jd(out, HERE / "check_once.json")
        s.drop(columns=["src"]).to_csv(HERE / "check_trades.csv", index=False)
        print(json.dumps({k: out[k] for k in ("trades", "per_session", "win", "avg", "avg_wo_best", "best_share", "total",
                                              "r_session", "worst_day", "first_half_avg", "second_half_avg")}, indent=1))
        # random controls (fit and check) for the chosen config
        set_windows(st, sel09)
        rc = dict(check=random_control(W, "check", s))
        Sf, df_ = load(W, "fit")
        sf = chassis(candidates(Sf, book_legs(Sf, t, st, sel09)))
        rc["fit"] = random_control(W, "fit", sf)
        rc["fit_signal_avg"], rc["check_signal_avg"] = float(sf.r.mean()), float(s.r.mean())
        jd(rc, HERE / "random_control.json")
        print("random", json.dumps(rc))
        # plateau diagnostic (after the single score; never used to re-select)
        pl = {}
        for name, (tt, ss, ll) in BOOK.items():
            x = chassis(candidates(S, book_legs(S, tt, ss, sel09)))
            pl[name] = dict(label=ll, **{k: v for k, v in stats(x, days, dtp).items() if k not in ("leg",)})
            print(f"plateau {name} {ll:11s} n {pl[name]['trades']} /s {pl[name]['per_session']:.2f} avg {pl[name]['avg']:+.4f} "
                  f"wo {pl[name]['avg_wo_best']:+.4f} tot {pl[name]['total']:+.1f}")
        jd(pl, HERE / "check_plateau.json")
