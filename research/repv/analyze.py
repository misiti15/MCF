"""REPV steps 2-3: rep multipliers and time-to-verdict for the focus set (On Deck roster + next in line + Gen top),
from research/repv/audit_*.csv (live) and research/repv/potential/<day>.csv (no-cap replay).

    python research/repv/analyze.py        # writes focus_multipliers.csv, time_to_verdict.csv, testingA_pool.csv
Educational only - not financial advice."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ONDECK = ["CWT09-gapdn-vwaploss-g10-short", "RW1-gapdn-bounce-flowsell-short-FD", "L3-gap-slope-lowdist-FD",
          "CWT09-gapdn-bounce-g10-lowerhalf-short", "NS1-rsidip-rsi5pop-long", "MF4-h40-open-flowsell",
          "NM-HL-T75-pm-long", "RW7-gapdn-bounce-early-short-FD", "MF3-open-flowsell-rsi5hi",
          "ST6-volspikeup-short-mid-t1s1-FD", "orb20_a"]
NEXT = ["CWT05-flush-m05-v5-long", "CWT13-vwapstretch-z075-short", "MF2-open-rsimidhi-flowsell-FD",
        "L3-gap-slope-rsi5hi-FD", "NS4-pm-vwap-reclaim-oversold-short-FD", "ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD",
        "NM-MF3-qqqdn-gapdn-FD"]
CLASH = ("opposite side held", "lot cap", "already in symbol", "twin held")   # pooling artefacts: own account takes them
CF = 0.15
GATES = ((8, 30), (15, 60))
START = pd.Timestamp("2026-11-12")
HOLIDAYS = {pd.Timestamp("2026-11-26")}


def sessions_to_date(n: float) -> str:
    if n is None or not np.isfinite(n):
        return "never at this rate"
    n = int(math.ceil(n))
    if n <= 0:
        return "met"
    d, k = START, 0
    while True:
        if d.weekday() < 5 and d not in HOLIDAYS:
            k += 1
            if k == n:
                return str(d.date())
        d += pd.Timedelta(days=1)


def need(ts, n, p, r, gate):
    gs, gn = gate
    a = 0 if ts >= gs else ((gs - ts) / p if p > 0 else np.inf)
    b = 0 if n >= gn else ((gn - n) / r if r > 0 else np.inf)
    return max(a, b)


UNLOCKABLE = ("cost_filter", "split_gate", "setup_cap", "buying_power", "twin", "slots", "account_halt", "latch")
RISK_STAGE = ("setup_cap", "account_halt", "latch", "twin", "slots", "split_gate")


def live_unlock(focus: list[str], P: pd.DataFrame) -> pd.DataFrame:
    """Live-based rep multiplier per setup (all accounts except Primary, which is frozen): entries + signals lost to
    unlockable blocks x the account's downstream pass rate, plus (Testing A sessions from 11-04) the top-500 pool share
    measured in the no-cap replay. Also the sessions a setup had signals but no entry only because of unlockable blocks."""
    import sys
    sys.path.insert(0, str(HERE))
    from audit import ACCOUNTS, bucket, load

    U = pd.read_csv(HERE / "unlock_base.csv")
    rows = []
    sigs = []
    for acct, (branch, tag) in ACCOUNTS.items():
        if acct == "primary":
            continue
        sig, _ = load(branch)
        s1 = sig[(sig.run_id == 1) & sig.strategy.isin(focus)].copy()
        s1["b"] = [bucket(a, r) for a, r in zip(s1.status, s1.reason)]
        s1["account"] = acct
        sigs.append(s1)
    G = pd.concat(sigs, ignore_index=True)
    pr = U[U.bucket == "taken"].set_index("account").conversion.to_dict()
    bp = U[U.bucket == "buying_power"].set_index("account").lost_per_session.to_dict()
    tk = U[U.bucket == "taken"].set_index("account").lost_per_session.to_dict()
    ent = P[P.entry] if len(P) else P
    for s in focus:
        g = G[G.strategy == s]
        E = int((g.b == "taken").sum())
        extra = 0.0
        by = {}
        for (acct, b), n in g[g.b.isin(UNLOCKABLE)].groupby(["account", "b"]).size().items():
            conv = pr.get(acct, 0.6) if b in RISK_STAGE else 1.0 if b == "buying_power" else \
                1 - bp.get(acct, 0) / max(1e-9, tk.get(acct, 0) + bp.get(acct, 0))
            extra += n * conv
            by[b] = by.get(b, 0) + n * conv
        e = ent[ent.strategy == s] if len(ent) else ent
        share = float(e.in_top500.mean()) if len(e) else None
        t2 = int(((g.account == "testing2") & (g.day >= "2026-11-04") & (g.b == "taken")).sum())
        pool_extra = t2 * (1 / share - 1) if share and share > 0 else 0.0
        by["pool_top500"] = pool_extra
        # sessions with signals but no entry where an unlockable block took at least one signal
        dd = g.groupby("day").agg(taken=("b", lambda x: (x == "taken").sum()), unl=("b", lambda x: x.isin(UNLOCKABLE).sum()))
        rescued = int(((dd.taken == 0) & (dd.unl > 0)).sum())
        m = (E + extra + pool_extra) / E if E else None
        rows.append({"setup": s, "live_entries_ex_primary": E, "extra_unlock": round(extra + pool_extra, 1),
                     "live_multiplier": None if m is None else round(m, 2), "rescued_sessions": rescued,
                     "top500_share_replay": None if share is None else round(share, 2),
                     **{f"extra_{k}": round(v, 1) for k, v in by.items()}})
    return pd.DataFrame(rows)


def main():
    S = pd.read_csv(HERE / "audit_by_account.csv")
    D = pd.read_csv(HERE / "live_daily.csv")
    gen = [x for x in (HERE / "gen_top.txt").read_text().split() if x]
    focus = ONDECK + NEXT + gen
    files = sorted((HERE / "potential").glob("????-??-??.csv"))
    P = pd.concat([pd.read_csv(f) for f in files], ignore_index=True) if files else pd.DataFrame()
    days = sorted(P.day.unique()) if len(P) else []
    P["reason"] = P.reason.fillna("")
    P["entry"] = (P.status == "submitted") | P.reason.str.startswith(CLASH)
    P["entry_cf"] = P.entry & (P.stop_cost_r <= CF)
    rows = []
    # live, merged across accounts
    Dm = D.groupby(["setup", "day"]).agg(trades=("trades", "sum"), signals=("signals", "sum")).reset_index()
    for s in focus:
        L = Dm[Dm.setup == s]
        sess = L.day.nunique()
        tot_tr, tot_ts = int(L.trades.sum()), int((L.trades > 0).sum())
        LW = L[L.day.isin(days)]
        p = P[P.strategy == s]
        spread_live = S[S.setup == s].lost_spread_crosscheck.sum() / max(1, S[S.setup == s].signals.sum())
        pot = p.groupby("day").agg(sig=("entry", "size"), ent=("entry", "sum"), ent_cf=("entry_cf", "sum"),
                                    top=("in_top500", "sum")).reindex(days, fill_value=0)
        pe = pot.ent.mean() * (1 - spread_live) if len(days) else np.nan
        pts = (pot.ent > 0).mean() if len(days) else np.nan
        live_w = LW.trades.sum() / max(1, LW.day.nunique()) if len(LW) else np.nan
        acc = "+".join(sorted(S[(S.setup == s) & (S.live_sessions > 0)].account.unique()))
        r_now = tot_tr / sess if sess else 0
        p_now = tot_ts / sess if sess else 0
        row = {"setup": s, "group": "ondeck" if s in ONDECK else "next" if s in NEXT else "gen", "accounts": acc,
               "live_sessions": sess, "trades": tot_tr, "traded_sessions": tot_ts,
               "trades_per_session_now": round(r_now, 2), "traded_share_now": round(p_now, 2),
               "traded_sessions_per_week_now": round(5 * p_now, 2),
               "replay_days": len(days), "live_days_in_replay": int(LW.day.nunique()),
               "live_trades_per_session_replaydays": None if np.isnan(live_w) else round(live_w, 2),
               "pot_signals_per_session": round(pot.sig.mean(), 2) if len(days) else None,
               "pot_entries_per_session": round(pe, 2) if len(days) else None,
               "pot_entries_cf015_per_session": round(pot.ent_cf.mean() * (1 - spread_live), 2) if len(days) else None,
               "pot_top500_share": round(pot.top.sum() / max(1, pot.sig.sum()), 2) if len(days) else None,
               "pot_traded_share": round(pts, 2) if len(days) else None,
               "multiplier": round(pe / live_w, 2) if len(days) and live_w and live_w > 0 else None}
        for gs, gn in GATES:
            n0 = need(tot_ts, tot_tr, p_now, r_now, (gs, gn))
            row[f"to_{gs}_{gn}_now_sessions"] = None if not np.isfinite(n0) else round(n0, 1)
            row[f"to_{gs}_{gn}_now_date"] = sessions_to_date(n0)
            if len(days):
                n1 = need(tot_ts, tot_tr, max(p_now, pts), max(r_now, pe), (gs, gn))
                row[f"to_{gs}_{gn}_unlocked_sessions"] = None if not np.isfinite(n1) else round(n1, 1)
                row[f"to_{gs}_{gn}_unlocked_date"] = sessions_to_date(n1)
        rows.append(row)
    F = pd.DataFrame(rows)
    LU = live_unlock(focus, P)
    F = F.merge(LU, on="setup", how="left")
    # unlocked time-to-verdict from the LIVE multiplier (replay multiplier kept as a cross-check column)
    for i, r in F.iterrows():
        m = r.live_multiplier if pd.notna(r.live_multiplier) else 1.0
        r_u = r.trades_per_session_now * max(1.0, m)
        p_u = min(1.0, (r.traded_sessions + r.rescued_sessions) / max(1, r.live_sessions))
        F.loc[i, "trades_per_session_unlocked"] = round(r_u, 2)
        F.loc[i, "traded_share_unlocked"] = round(p_u, 2)
        for gs, gn in GATES:
            n1 = need(r.traded_sessions, r.trades, p_u, r_u, (gs, gn))
            F.loc[i, f"to_{gs}_{gn}_unlocked_sessions"] = None if not np.isfinite(n1) else round(n1, 1)
            F.loc[i, f"to_{gs}_{gn}_unlocked_date"] = sessions_to_date(n1)
    F = F.rename(columns={"multiplier": "replay_multiplier"})
    F.to_csv(HERE / "focus_multipliers.csv", index=False)
    # every setup in the replay (all testing areas + Gen picks): potential vs live
    allrows = []
    for s, p in P.groupby("strategy"):
        L = Dm[(Dm.setup == s) & Dm.day.isin(days)]
        pot = p.groupby("day").agg(ent=("entry", "sum"), sig=("entry", "size"), top=("in_top500", "sum"),
                                    ent_cf=("entry_cf", "sum")).reindex(days, fill_value=0)
        live_w = L.trades.sum() / L.day.nunique() if L.day.nunique() else np.nan
        allrows.append({"setup": s, "home": p.home.iloc[0], "live_days_in_replay": int(L.day.nunique()),
                        "live_trades_per_session": None if np.isnan(live_w) else round(live_w, 2),
                        "pot_signals_per_session": round(pot.sig.mean(), 2), "pot_entries_per_session": round(pot.ent.mean(), 2),
                        "pot_entries_cf_per_session": round(pot.ent_cf.mean(), 2),
                        "pot_entries_top500_share": round(p[p.entry].in_top500.mean(), 2) if p.entry.any() else None,
                        "pot_traded_share": round((pot.ent > 0).mean(), 2),
                        "multiplier": round(pot.ent.mean() / live_w, 2) if live_w and live_w > 0 else None})
    pd.DataFrame(allrows).to_csv(HERE / "all_multipliers.csv", index=False)
    print(F.to_string())
    return F


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 50)
    main()
