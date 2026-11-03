"""MH4 (BDI 2026-11-02, Move Hunt day 3): opening GROUP move - when a name's industry peers (residual-return correlation
peers, not raw beta) move together in the first 10-20 minutes, trade the name in the group's direction.

Why: three Move Hunt days in a row show the day's big tradable moves arriving in groups at the open (10-29 cyber +
defence, 10-30 cyber + retail, 11-02 packaged food CPB / GIS / HRL / CAG / KMB short 09:45-09:55 and alternative asset
managers BN / BAM / APO / ARES / KKR long 09:35-09:40). MH3 (10-30) showed a name-level opening signal is only the day's
beta; this test asks whether the *group* adds anything beyond the day: every score is also given as the excess over a
DAY-MATCHED baseline (all eligible names at the same date and bar close, same side and exit), so a market-direction
effect cannot pass. This is the rework named in mh-1029-earnings-sympathy (industry-like peers + the 09:35 frame).

Pre-declared (written before any two-year row was scored):
  data    research/bdi/timeofday/data/open (5-minute lab rows 09:35..10:30 from the 1-minute SIP cache; the locked block
          2024-11-01..2025-02-28 dropped at build time, asserted absent) + research/history2y daily closes for the peer
          table, with the locked block DROPPED before any computation. adv20 >= $95M; earnings blackout (+-4 trading
          days) removed for the traded name (reporters stay in the peer median - that is the sympathy information).
  peers   per calendar month, from the trailing 120 non-locked sessions before the month (>= 50 needed): daily returns
          minus beta x SPY return (beta from the same window); the 10 names with the highest residual correlation
          (>= 0.30) are the peers. Nothing after the month start is used.
  move    z = (fromOpen % / ATR_d %) minus the cross-sectional median of that at the same date + bar close (all adv20
          >= $95M rows) - a name's move from the open in ATR units, in excess of the market.
          P = median z over the peers present at that bar (>= 6 of 10), agree = share of peers with z of P's sign.
  signal  first of the 09:40 / 09:45 / 09:50 bar closes per symbol-day where |P| >= g and agree >= 0.7, side = sign P;
          mode lag:  own z on the group's side < P / 2 (has not followed yet: catch-up)
          mode lead: own z on the group's side >= P (moving with or ahead of the group: continuation)
  g       0.40, 0.60 (ATR units)
  exits   t1s1 lab target / stop 0.25 x ATR_d (frame outcome, exit by 15:55), production costs with the tod multiplier;
          h1030 stop 0.25 x ATR_d on later 5-minute highs / lows, else out at the 10:30 close (same costs as MH3)
  configs 2 sides x 2 modes x 2 g x 2 exits = 16. Split train <= 2025-09-30, valid after. Bars: full
          max(1.5, sqrt(2 ln 16)) = 2.35, BAR90 = 2.12; a pass also needs walk-forward months >= 54% positive, both
          regimes positive, and a positive DAY-MATCHED excess with day-clustered t >= 1.5 (declared before scoring).
  today   one-day hindsight check on research/bdi/moves rows (11-02): precision of >= 0.5 ATR in the signal's direction
          within 90 min vs the base rate at the same bars (descriptive only).
  (added after the first scoring, no new config: the day-matched excess is also split train / valid)
Usage: python research/bdi/1102/mh4_group.py <scratch with mh/2026-11-02/rows.parquet> > research/bdi/1102/mh4_out.txt
Educational only - not financial advice."""
import glob, json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research import gates as G
from mcf.research.generator import data as GD

LK0, LK1 = pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date()
SPLIT = pd.Timestamp("2025-09-30").date()
K, MINC, WIN, MINW = 10, 0.30, 120, 50

# ---------------------------------------------------------------- daily residual returns (locked block dropped first)
D = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "close"])
D["date"] = pd.to_datetime(D["date"]).dt.date
D = D[~((D.date >= LK0) & (D.date <= LK1))]
RET = D.pivot(index="date", columns="symbol", values="close").sort_index().pct_change(fill_method=None)
spy = RET["SPY"]


def peer_table(end_excl):
    w = RET[RET.index < end_excl].tail(WIN)
    if len(w) < MINW:
        return {}
    w = w.loc[:, w.notna().mean() >= 0.9]
    s = spy.reindex(w.index)
    beta = w.apply(lambda c: np.cov(c.fillna(0), s.fillna(0))[0, 1] / max(np.var(s.fillna(0)), 1e-12))
    res = (w - np.outer(s.fillna(0), beta)).fillna(0)
    res = res.drop(columns=[c for c in ("SPY", "QQQ", "IWM", "DIA") if c in res])
    C = np.corrcoef(res.to_numpy().T); np.fill_diagonal(C, -1)
    cols = res.columns.to_numpy(); out = {}
    for i, c in enumerate(cols):
        j = np.argsort(-C[i])[:K]; j = j[C[i, j] >= MINC]
        if len(j) >= 6:
            out[c] = list(cols[j])
    return out


def group_cols(F):
    """Adds z, P, agree to frame F (columns symbol, date, tod, fromOpen, atr_pct); peers per month."""
    F = F.copy()
    F["zr"] = F.fromOpen / F.atr_pct
    F["z"] = F.zr - F.groupby(["date", "tod"]).zr.transform("median")
    F["P"] = np.nan; F["agree"] = np.nan
    F["month"] = pd.to_datetime(F.date).dt.to_period("M")
    for m, fm in F.groupby("month"):
        peers = peer_table(m.to_timestamp().date())
        if not peers:
            continue
        zt = fm.pivot_table(index=["date", "tod"], columns="symbol", values="z")
        Pm = {}; Am = {}
        for s, pl in peers.items():
            pl = [p for p in pl if p in zt.columns]
            if s not in zt.columns or len(pl) < 6:
                continue
            Z = zt[pl]; ok = Z.notna().sum(axis=1) >= 6
            med = Z.median(axis=1).where(ok)
            ag = (np.sign(Z).eq(np.sign(med), axis=0) & Z.notna()).sum(axis=1) / Z.notna().sum(axis=1)
            Pm[s] = med; Am[s] = ag.where(ok)
        if not Pm:
            continue
        Ps = pd.DataFrame(Pm).stack().rename("P"); As = pd.DataFrame(Am).stack().rename("agree")
        J = pd.concat([Ps, As], axis=1).reset_index(); J.columns = ["date", "tod", "symbol", "P", "agree"]
        sub = fm[["symbol", "date", "tod"]].reset_index().merge(J, on=["symbol", "date", "tod"], how="left").set_index("index")
        F.loc[sub.index, "P"] = sub.P; F.loc[sub.index, "agree"] = sub.agree
    return F


def masks(F, side, mode, g):
    sg = 1 if side == "long" else -1
    P, z = F.P.to_numpy() * sg, F.z.to_numpy() * sg
    m = (P >= g) & (F.agree.to_numpy() >= 0.7) & F.tod.isin([940, 945, 950]).to_numpy()
    return m & ((z < P / 2) if mode == "lag" else (z >= P))


# ---------------------------------------------------------------- A. today's one-day check (hindsight labels)
if len(sys.argv) > 1:
    R = pd.read_parquet(Path(sys.argv[1]) / "mh/2026-11-02/rows.parquet")
    R["date"] = pd.Timestamp("2026-11-02").date(); R["atr_pct"] = R.atr_pct_d
    R = R[R.tod.isin([935, 940, 945, 950, 955, 1000])]
    Rg = group_cols(R)
    print("A. 2026-11-02 one-day check (decision rows 09:40-09:50, blackout names excluded from signals; label: >= 0.5 ATR "
          "in the signal's direction within 90 min)")
    for side in ("long", "short"):
        lab = (Rg.up_atr if side == "long" else Rg.dn_atr).to_numpy() >= 0.5
        base = Rg.tod.isin([940, 945, 950]).to_numpy() & ~Rg.blackout.to_numpy()
        for mode in ("lag", "lead"):
            for g in (0.4, 0.6):
                m = masks(Rg, side, mode, g) & ~Rg.blackout.to_numpy()
                idx = G.first_per_symbol_day(Rg.symbol.to_numpy(), Rg.date.to_numpy(), m)
                names = Rg.symbol.to_numpy()[idx]
                print(f"  {side:5s} {mode:4s} g{g}: {len(idx):3d} signals, precision {lab[idx].mean() if len(idx) else float('nan'):.0%} "
                      f"vs base {lab[base].mean():.0%}; e.g. {', '.join(sorted(names)[:12])}")
    cat = pd.read_csv(ROOT / "research/bdi/moves/moves.csv"); cat = cat[(cat.date == "2026-11-02") & (cat.set == "tradable")]
    hit = []
    for _, r in cat.iterrows():
        sg = 1 if r.side == "long" else -1
        x = Rg[(Rg.symbol == r.symbol) & Rg.tod.isin([940, 945, 950])]
        hit.append(bool(((x.P * sg >= 0.4) & (x.agree >= 0.7)).any()))
    cat["group"] = hit
    print(f"  tradable top-50 movers with a same-direction group signal (|P| >= 0.4, agree >= 0.7) at 09:40-09:50: "
          f"{sum(hit)} / {len(hit)}: {', '.join(cat[cat.group].symbol + '(' + cat[cat.group].side.str[0] + ')')}")

# ---------------------------------------------------------------- B. two-year test
COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "fromOpen", "adv20",
        "r_long_t1s1", "win_long_t1s1", "r_short_t1s1", "win_short_t1s1"]
F = pd.concat([pd.read_parquet(f, columns=COLS) for f in sorted(glob.glob(str(ROOT / "research/bdi/timeofday/data/open/*.parquet")))])
F["date"] = pd.to_datetime(F["date"]).dt.date
assert not ((F.date >= LK0) & (F.date <= LK1)).any()
F = F[(F.adv20 >= 95e6) & (F.atr_d > 0)]
F["atr_pct"] = F.atr_d / F.close * 100
F = F.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
F = group_cols(F)
F["bl"] = GD._blackout(F.symbol.to_numpy(), F.date.to_numpy())
REG = G.session_regimes(D[["date", "open", "close"]])

# h1030 for every row, vectorised: stopped if any later row of the symbol-day breaches the stop, else 10:30 close
key = F.symbol.astype(str) + "|" + F.date.astype(str)
rev = F.iloc[::-1]
nxt_lo = rev.groupby(key.iloc[::-1]).low.transform(lambda s: s.cummin().shift(1)).iloc[::-1].to_numpy()
nxt_hi = rev.groupby(key.iloc[::-1]).high.transform(lambda s: s.cummax().shift(1)).iloc[::-1].to_numpy()
last_cl = F.groupby(key).close.transform("last").to_numpy()
cl, Rr = F.close.to_numpy(), 0.25 * F.atr_d.to_numpy()
mult = G.tod_cost_mult(F.tod.to_numpy())
H = {}
for side, sg in (("long", 1), ("short", -1)):
    stopped = (nxt_lo <= cl - Rr) if sg > 0 else (nxt_hi >= cl + Rr)
    g = np.where(stopped, -1.0, sg * (last_cl - cl) / Rr)
    c = (G.SLIP_PS + cl * G.SLIP_BPS) * (mult + 1) + np.where(stopped, G.STOP_EXTRA, 0)
    H[side] = np.where(np.isfinite(nxt_lo), g - c / Rr, np.nan)
    H[side + "_t1s1"] = G.prod_r(F[f"r_{side}_t1s1"].to_numpy(), F[f"win_{side}_t1s1"].to_numpy(), cl, F.atr_d.to_numpy(),
                                 "t1s1", tod=F.tod.to_numpy())
elig = ~F.bl.to_numpy()
DM = {}
for k, v in H.items():
    s = pd.Series(np.where(elig, v, np.nan))
    DM[k] = s.groupby([F.date.to_numpy(), F.tod.to_numpy()]).transform("mean").to_numpy()

N = 16; tfull = G.t_required(N); t90 = round(max(1.35, 0.9 * tfull), 2)
print(f"\nB. two-year test: rows {len(F)} (adv20 >= 95M, 09:35..10:30), with a peer median {int(F.P.notna().sum())}; "
      f"dates {F.date.min()}..{F.date.max()} (locked block absent); N = {N}: full bar {tfull}, BAR90 {t90}")


def wf_share(t):
    m = t.groupby(pd.to_datetime(t.date).dt.to_period("M")).r.mean()
    return round(float((m > 0).mean()), 3), len(m)


out = []
for side in ("long", "short"):
    for mode in ("lag", "lead"):
        for g in (0.4, 0.6):
            for ex in ("t1s1", "h1030"):
                m = masks(F, side, mode, g) & elig
                idx = G.first_per_symbol_day(F.symbol.to_numpy(), F.date.to_numpy(), m)
                hk = side + "_t1s1" if ex == "t1s1" else side
                t = pd.DataFrame({"date": F.date.to_numpy()[idx], "symbol": F.symbol.to_numpy()[idx], "tod": F.tod.to_numpy()[idx],
                                  "r": H[hk][idx], "ex": H[hk][idx] - DM[hk][idx]})
                t = t[np.isfinite(t.r) & np.isfinite(t.ex)]
                s = G.summary(t); rg = G.regime_split(t, REG)
                tr, va = G.summary(t[t.date <= SPLIT]), G.summary(t[t.date > SPLIT])
                xs = G.summary(t.assign(r=t.ex)); wf, nm = wf_share(t)
                row = dict(config=f"MH4-group-{mode}-{side}-g{int(g * 100):02d}-{ex}", n=s["n"], days=s.get("days"),
                           per_day=round(s["n"] / max(1, s.get("days", 1)), 1), win=s.get("win_rate"), exp_r=s.get("exp_r"),
                           t=s.get("t"), ex_best_day=s.get("ex_best_day"), train=tr.get("exp_r"), valid=va.get("exp_r"),
                           valid_t=va.get("t"), up=rg["up"].get("exp_r"), down=rg["down"].get("exp_r"), wf_pos=wf, months=nm,
                           dm_excess=xs.get("exp_r"), dm_excess_t=xs.get("t"),
                           dm_ex_train=G.summary(t[t.date <= SPLIT].assign(r=t.ex)).get("exp_r"),
                           dm_ex_valid=G.summary(t[t.date > SPLIT].assign(r=t.ex)).get("exp_r"),
                           dm_ex_valid_t=G.summary(t[t.date > SPLIT].assign(r=t.ex)).get("t"))
                row["bar90_pass"] = bool((row["t"] or -9) >= t90 and wf >= 0.54 and rg["pass"] and (row["dm_excess_t"] or -9) >= 1.5)
                out.append(row)
O = pd.DataFrame(out)
pd.set_option("display.width", 260)
print(O.to_string(index=False))
O.to_csv(Path(__file__).with_name("mh4_results.csv"), index=False)
print(json.dumps({"configs": N, "pass_bar90": int(O.bar90_pass.sum()), "best_t": float(O.t.max()),
                  "best_dm_excess_t": float(O.dm_excess_t.max())}))
print("Educational only - not financial advice.")
