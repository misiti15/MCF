"""LATCH review 2026-11-17 (research only; PLAN.md written before scoring).

usage: python research/latch_review_1117/analysis.py <journal_dir> <opens.csv> <out_dir>
journal_dir holds <branch>.db copies of journal.db from the mcf-data* state branches.
Educational only - not financial advice."""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from mcf.costs import cost_r  # noqa: E402

ACCOUNTS = {"mcf-data": "Primary", "mcf-data-testing": "On Deck", "mcf-data-testing2": "Testing A",
            "mcf-data-explore1": "Testing B", "mcf-data-livelab": "Testing C", "mcf-data-testingd": "Testing D",
            "mcf-data-testinge": "Testing E", "mcf-data-testingf": "Testing F", "mcf-data-gen": "Gen"}
LOCK = ("2024-11-01", "2025-02-28")
LOT_CAP = 3
LEVELS = [2.0, 3.0, 4.0, None]
TZ = "America/New_York"
LAG = pd.Timedelta(minutes=float(os.environ.get("LATCH_LAG_MIN", "2")))  # exit -> journal (reconcile) lag; calibrated in NOTES


def family(s: str) -> str:
    s = str(s)
    return s.split("-")[0] if "-" in s else s


def latch_on(acct: str, day: str) -> bool:
    """Per-setup -2R latch configured for this account-day (ledger: 10-20 twin/setup-loss, ST-A off in testing 10-23,
    ST-P Primary from 10-29)."""
    if acct == "Primary":
        return day >= "2026-10-29"     # no latch skips in Primary before ST-P (10-29) in the journal
    if acct in ("On Deck", "Testing A", "Gen"):
        return "2026-10-20" <= day <= "2026-10-22"
    return False


def halt_r(acct: str, day: str) -> float:
    if acct == "Primary":
        return 20.0
    if acct == "On Deck" and day < "2026-10-19":
        return 60.0
    return 300.0 if day >= "2026-11-12" else 120.0


def basis_cost(acct: str, day: str) -> bool:      # LR3: Primary counts R after costs from 11-12
    return acct == "Primary" and day >= "2026-11-12"


def load(jdir: str):
    live, wi, sig = [], [], []
    for br, acct in ACCOUNTS.items():
        p = os.path.join(jdir, br + ".db")
        if not os.path.exists(p):
            continue
        c = sqlite3.connect(p)
        t = pd.read_sql("select * from trades where run_id=1", c)
        t["acct"] = acct
        t["rc"] = cost_r(t).values
        live.append(t)
        w = pd.read_sql("select * from trades where run_id=2 and meta like '%why=setup daily loss limit%'", c)
        w["acct"] = acct
        wi.append(w)
        s = pd.read_sql("select day, ts, symbol, strategy, side from signals where status='skipped' and "
                        "reason='setup daily loss limit'", c).drop_duplicates()
        s["acct"] = acct
        sig.append(s)
    live, wi, sig = (pd.concat(x, ignore_index=True) for x in (live, wi, sig))
    for d in (live, wi):
        d["et"] = pd.to_datetime(d.entry_time, utc=True, format="mixed").dt.tz_convert(TZ)
        d["xt"] = pd.to_datetime(d.exit_time, utc=True, format="mixed").dt.tz_convert(TZ)
        d.drop(d[(d.date >= LOCK[0]) & (d.date <= LOCK[1])].index, inplace=True)
    live["rr"] = live.r_multiple.astype(float)
    # live gap r_raw - R after costs per setup/account (what-if cost haircut)
    g = live.assign(gap=live.rr - live.rc).groupby(["acct", "strategy"]).gap.agg(["mean", "size"])
    wi = wi.drop_duplicates(["acct", "strategy", "symbol", "signal_time"]).copy()
    wi["rr"] = wi.r_multiple.astype(float)
    wi = wi.merge(g, left_on=["acct", "strategy"], right_index=True, how="left")
    wi["gap"] = np.where(wi["size"].fillna(0) >= 10, wi["mean"], 0.05)
    wi["gap"] = wi["gap"].fillna(0.05).clip(lower=0.0)
    wi["rc"] = wi.rr - wi.gap
    wi = wi.drop(columns=["mean", "size"])
    return live, wi, sig


def lot_cap(live: pd.DataFrame, wi: pd.DataFrame) -> pd.DataFrame:
    """Accept what-if lots in entry order only while live + accepted lots on the symbol (same account) < 3, same side."""
    keep = []
    for (acct, day, sym), w in wi.sort_values("et").groupby(["acct", "date", "symbol"], sort=False):
        L = live[(live.acct == acct) & (live.date == day) & (live.symbol == sym)]
        acc = []
        for i, r in w.iterrows():
            t = r.et
            op_live = L[(L.et <= t) & (L.xt > t)]
            op_h = [a for a in acc if a[0] <= t < a[1]]
            if (op_live.side != r.side).any():
                keep.append((i, False, "opposite side held"))
                continue
            if len(op_live) + len(op_h) >= LOT_CAP:
                keep.append((i, False, "lot cap"))
                continue
            acc.append((r.et, r.xt))
            keep.append((i, True, ""))
    k = pd.DataFrame(keep, columns=["i", "taken_cap", "cap_why"]).set_index("i")
    return wi.join(k)


def replay(trades: pd.DataFrame, level: float | None) -> pd.Series:
    """Single pass in exit order per account-day: per-setup latch at -level (None = off) and account halt.
    Returns a bool Series 'taken' aligned to trades.index."""
    taken = pd.Series(False, index=trades.index)
    for (acct, day), d in trades.groupby(["acct", "date"]):
        cb = basis_cost(acct, day)
        H = halt_r(acct, day)
        cum_s, latch_t, cum_a, halt_t = {}, {}, 0.0, None
        for i, r in d.sort_values(["xt", "et"]).iterrows():
            st = r.strategy
            lt = latch_t.get(st)
            if (lt is not None and r.et >= lt) or (halt_t is not None and r.et >= halt_t):
                continue
            taken[i] = True
            x = r.rc if cb else r.rr
            cum_s[st] = cum_s.get(st, 0.0) + x
            cum_a += x
            if level is not None and lt is None and cum_s[st] <= -level + 1e-9:
                latch_t[st] = r.xt + LAG
            if halt_t is None and cum_a <= -H + 1e-9:
                halt_t = r.xt + LAG
    return taken


def latch_days(live: pd.DataFrame, sig: pd.DataFrame) -> pd.DataFrame:
    """Setup-days whose running realized R (latch basis, exit order) reached <= -2 or that journaled latch skips."""
    rows = []
    for (acct, day, st), d in live.groupby(["acct", "date", "strategy"]):
        d = d.sort_values("xt")
        x = d.rc if basis_cost(acct, day) else d.rr
        cs = x.cumsum()
        hit = cs[cs <= -2 + 1e-9]
        if len(hit):
            rows.append((acct, day, st, d.loc[hit.index[0], "xt"]))
    ld = pd.DataFrame(rows, columns=["acct", "date", "strategy", "cross_t"])
    sk = sig.groupby(["acct", "day", "strategy"]).size().rename("blocked").reset_index().rename(columns={"day": "date"})
    ld = ld.merge(sk, on=["acct", "date", "strategy"], how="outer")
    ld["blocked"] = ld.blocked.fillna(0).astype(int)
    ld["kind"] = [("A actual" if (b > 0 or latch_on(a, dd)) else "B virtual")
                  for a, dd, b in zip(ld.acct, ld.date, ld.blocked)]
    return ld


def best_share(by_day: pd.Series) -> tuple[float, float]:
    tot = by_day.sum()
    if len(by_day) == 0:
        return float("nan"), float("nan")
    b = by_day.max()
    wo = (tot - b) / max(1, len(by_day) - 1) if len(by_day) > 1 else float("nan")
    share = b / tot if tot > 0 else float("nan")
    return wo, share


def main(jdir, opens_csv, out):
    os.makedirs(out, exist_ok=True)
    live, wi, sig = load(jdir)
    wi = lot_cap(live, wi)
    ld = latch_days(live, sig)
    ld.to_csv(os.path.join(out, "latch_days.csv"), index=False)

    # ---------------- post-latch trades
    wi_c = wi[wi.taken_cap].copy()
    wi_c["src"] = "whatif"
    post_rows = [wi_c.assign(kind="A actual")[["acct", "date", "strategy", "symbol", "side", "et", "xt", "exit_reason",
                                               "rr", "rc", "src", "kind"]]]
    for r in ld[ld.kind == "B virtual"].itertuples():
        d = live[(live.acct == r.acct) & (live.date == r.date) & (live.strategy == r.strategy) & (live.et > r.cross_t)]
        post_rows.append(d.assign(src="live", kind="B virtual")[["acct", "date", "strategy", "symbol", "side", "et",
                                                                  "xt", "exit_reason", "rr", "rc", "src", "kind"]])
    post = pd.concat(post_rows, ignore_index=True)
    post.to_csv(os.path.join(out, "post_latch_trades.csv"), index=False)
    wi.assign(et=wi.et.astype(str), xt=wi.xt.astype(str))[
        ["acct", "date", "strategy", "symbol", "side", "signal_time", "et", "xt", "exit_reason", "rr", "gap", "rc",
         "taken_cap", "cap_why"]].to_csv(os.path.join(out, "blocked_whatifs.csv"), index=False)

    # ---------------- level replay
    allt = pd.concat([live.assign(src="live")[["acct", "date", "strategy", "symbol", "side", "et", "xt", "rr", "rc",
                                               "src"]],
                      wi_c[["acct", "date", "strategy", "symbol", "side", "et", "xt", "rr", "rc", "src"]]],
                     ignore_index=True)
    lvl = {}
    for L in LEVELS:
        tk = replay(allt, L)
        name = f"L{int(L)}" if L else "none"
        lvl[name] = allt.rc.where(tk, 0.0)
    for k, v in lvl.items():
        allt["R_" + k] = v
    # sanity: L2 vs actual live on actual-latch account-days (live trades only, those days)
    real = live.groupby(["acct", "date"]).rc.sum()
    sim2 = allt.groupby(["acct", "date"]).R_L2.sum()
    chk = pd.concat([real.rename("real"), sim2.rename("sim_L2")], axis=1).fillna(0)
    chk["diff"] = chk.sim_L2 - chk.real
    chk.to_csv(os.path.join(out, "sanity_L2_vs_real_by_account_day.csv"))

    keys = ld[["acct", "date", "strategy", "kind"]]
    sd = allt.groupby(["acct", "date", "strategy"])[[c for c in allt.columns if c.startswith("R_")]].sum().reset_index()
    sd = keys.merge(sd, on=["acct", "date", "strategy"], how="left").fillna(0.0)
    sd.to_csv(os.path.join(out, "latch_day_levels.csv"), index=False)

    # account-day totals under each level (every account-day, -20R halt in Primary)
    ad = allt.groupby(["acct"])[[c for c in allt.columns if c.startswith("R_")]].sum()
    ad.to_csv(os.path.join(out, "account_totals_by_level.csv"))

    # ---------------- per-setup table
    rows = []
    for st, g in ld.groupby("strategy"):
        p = post[post.strategy == st]
        byday = p.groupby(["acct", "date"]).rc.sum()
        wo, share = best_share(byday)
        bysym = p.groupby("symbol").rc.sum()
        pos = bysym[bysym > 0].sum()
        top_sym = bysym.idxmax() if len(bysym) else ""
        top_sym_share = (bysym.max() / pos) if pos > 0 else float("nan")
        s = sd[sd.strategy == st]
        r = dict(setup=st, family=family(st), accounts=",".join(sorted(g.acct.unique())),
                 latch_days=len(g), actual_days=int((g.kind == "A actual").sum()),
                 virtual_days=int((g.kind == "B virtual").sum()), blocked_signals=int(g.blocked.sum()),
                 post_trades=len(p), post_R=p.rc.sum(), post_R_per_trade=p.rc.mean() if len(p) else np.nan,
                 post_days_with_trades=len(byday), post_avgday_wo_best=wo, best_day_share=share,
                 top_symbol=top_sym, top_symbol_share_of_pos=top_sym_share)
        for k in lvl:
            r["dayR_" + k] = s["R_" + k].sum()
            sk = s["R_" + k]
            r["dayR_wo_best_" + k] = sk.sum() - sk.max() if len(sk) > 1 else np.nan
        rows.append(r)
    ps = pd.DataFrame(rows).sort_values(["latch_days", "post_R"], ascending=[False, False])

    def recommend(r):
        if r.latch_days < 5:
            return "keep -2 (< 5 latch days)"
        if not (r.post_R > 0 and r.post_avgday_wo_best > 0):
            return "keep -2 (post-latch not positive w/o best day)"
        if not (r.top_symbol_share_of_pos <= 0.5):
            return "keep -2 (one stock carries it)"
        best = max(["L3", "L4", "none"], key=lambda k: r["dayR_wo_best_" + k])
        if r["dayR_wo_best_" + best] > r["dayR_wo_best_L2"]:
            return f"candidate {best}"
        return "keep -2 (no level beats -2 w/o best day)"
    ps["verdict"] = ps.apply(recommend, axis=1)
    ps.to_csv(os.path.join(out, "per_setup_latch.csv"), index=False)

    # ---------------- Part 2 remedies on live trades
    op = pd.read_csv(opens_csv)[["symbol", "date", "open"]]
    lv = live.merge(op, on=["symbol", "date"], how="left")
    lv["mv"] = lv.entry / lv["open"] - 1.0
    lv["against"] = np.where(lv.side > 0, -lv.mv, lv.mv)          # >0 = moved against the trade direction
    rem = {}
    for X in (0.10, 0.15, 0.20):
        rem[f"FADEMOVE{int(X*100)}"] = (lv.against > X) & lv["open"].notna()
    lv = lv.sort_values("et")
    for N in (6, 12, None):
        drop = pd.Series(False, index=lv.index)
        for _, g in lv.groupby(["acct", "date", "strategy", "symbol"]):
            if len(g) < 2:
                continue
            stops = []
            for i, r in g.iterrows():
                blocked = any(sx <= r.et and (N is None or r.et < sx + pd.Timedelta(minutes=5 * N)) for sx in stops)
                if blocked:
                    drop[i] = True
                    continue
                if str(r.exit_reason) == "stop":
                    stops.append(r.xt)
        rem[f"REENTRY{N if N else 'DAY'}"] = drop
    rrows, frows, trows = [], [], []
    for name, mask in rem.items():
        lv["_d"] = mask.reindex(lv.index).fillna(False)
        g = lv.groupby(["acct", "strategy"])
        t = pd.DataFrame({"trades": g.size(), "R": g.rc.sum(), "removed": g._d.sum(),
                          "dR": -lv.rc.where(lv._d, 0.0).groupby([lv.acct, lv.strategy]).sum()}).reset_index()
        t["remedy"] = name
        t["family"] = t.strategy.map(family)
        rrows.append(t)
        f = t.groupby("family")[["trades", "removed", "R", "dR"]].sum().reset_index()
        f["remedy"] = name
        frows.append(f)
        aff = t[t.removed > 0]
        trows.append(dict(remedy=name, trades=int(t.trades.sum()), removed=int(t.removed.sum()),
                          removed_pct=t.removed.sum() / t.trades.sum(), dR_total=t.dR.sum(),
                          removed_R_per_trade=(-t.dR.sum() / t.removed.sum()) if t.removed.sum() else np.nan,
                          setups_affected=len(aff), improve=int((aff.dR > 0.005).sum()),
                          worsen=int((aff.dR < -0.005).sum()), improve_R=aff.dR[aff.dR > 0].sum(),
                          worsen_R=aff.dR[aff.dR < 0].sum(), worst_setup=aff.dR.min() if len(aff) else np.nan,
                          worst_setup_name=(aff.loc[aff.dR.idxmin(), "acct"] + " " + aff.loc[aff.dR.idxmin(), "strategy"])
                          if len(aff) else "",
                          best_setup=aff.dR.max() if len(aff) else np.nan,
                          best_setup_name=(aff.loc[aff.dR.idxmax(), "acct"] + " " + aff.loc[aff.dR.idxmax(), "strategy"])
                          if len(aff) else "",
                          days_dR_pos=int((lv.rc.where(lv._d, 0).groupby(lv.date).sum() < 0).sum()),
                          days_dR_neg=int((lv.rc.where(lv._d, 0).groupby(lv.date).sum() > 0).sum()),
                          dR_wo_best_day=(lambda s: s.sum() - s.max())(-lv.rc.where(lv._d, 0).groupby(lv.date).sum())))
    pd.concat(rrows).to_csv(os.path.join(out, "remedy_by_setup.csv"), index=False)
    pd.concat(frows).to_csv(os.path.join(out, "remedy_by_family.csv"), index=False)
    pd.DataFrame(trows).to_csv(os.path.join(out, "remedy_summary.csv"), index=False)
    lv[["acct", "date", "strategy", "symbol", "side", "entry", "open", "against"]].to_csv(
        os.path.join(out, "live_move_from_open.csv.gz"), index=False)
    print("live trades", len(live), "what-ifs", len(wi), "taken under lot cap", int(wi.taken_cap.sum()))
    print("latch days", len(ld), ld.kind.value_counts().to_dict())
    print("sanity max |L2 - real| per account-day on Primary:",
          chk.loc["Primary"]["diff"].abs().max() if "Primary" in chk.index.get_level_values(0) else None)


if __name__ == "__main__":
    main(*sys.argv[1:4])
