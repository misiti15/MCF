"""FWDREP ledger: calibrate forward replay against live, then combine live + forward-replay evidence per setup.

    python research/fwdrep/report.py            # reads research/fwdrep/trades/*.csv + the live journals (data branches)

Writes (research/fwdrep/):
  calibration.csv     per family + ALL: replay vs live on setup-sessions where the setup ran live (match rate, R diff on
                      matched trades, replay-only / live-only shares, haircut = replay avg R - live avg R per trade)
  ledger.csv          per setup: live record | forward-replay record (raw + haircut) | combined effective reps
  gen_fasttrack.csv   Gen setups clearing REPS-MIN 8/30 (effective) + OD-IN (E5) on the combined record, ranked
Live = closed run_id=1 paper trades of the setup in ANY account (merged by setup id, as research/ondeck_build).
R after costs everywhere: live pnl_adj / (|entry - stop| x shares); replay simulated P/L after costs / same risk.
Replay reps are SIMULATED and always labelled; they never enter a live figure. Educational only - not financial advice.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run as RUN  # noqa: E402

MATCH_MIN = 5            # entry within 5 minutes
SHRINK_K = 150           # trades: family haircut / weight shrunk toward ALL with this prior weight
W_MIN, W_MAX = 0.2, 0.8  # replay weight bounds (a replay rep never counts as much as a live rep)


def family(sid: str) -> str:
    if sid.startswith("GEN-"):
        return "GEN"
    tok = re.split(r"[-_]", sid)[0]
    if tok.startswith("NM"):
        return "NM"
    m = re.match(r"[A-Za-z]+", tok)
    f = m.group(0) if m else tok
    return {"L": "L3", "heat": "heat", "orb": "orb", "exhaustion": "exhaustion", "intraday": "momentum"}.get(f, f)


def live_trades() -> pd.DataFrame:
    rows = []
    for acc, br in RUN.BRANCH.items():
        raw = RUN.git("show", f"origin/{br}:journal.db", text=False)
        if not raw:
            continue
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.write(raw)
        try:
            c = sqlite3.connect(f.name)
            t = pd.read_sql("select date, strategy as setup, symbol, side, entry_time, entry, stop, shares, pnl, pnl_adj "
                            "from trades where run_id=1 and exit is not null", c)
            c.close()
        finally:
            os.unlink(f.name)
        t["acct"] = acc
        rows.append(t)
    T = pd.concat(rows, ignore_index=True)
    T["pnl_adj"] = T.pnl_adj.fillna(T.pnl)
    risk = (T.entry - T.stop).abs() * T.shares
    T = T[risk > 0].copy()
    T["R"] = T.pnl_adj / risk[risk > 0]
    T["date"] = T.date.astype(str)
    T["et"] = pd.to_datetime(T.entry_time, utc=True, format="mixed")
    return T


def replay_trades() -> pd.DataFrame:
    fs = sorted((HERE / "trades").glob("????-??-??.csv"))
    if not fs:
        return pd.DataFrame({c: pd.Series(dtype=t) for c, t in (("date", str), ("setup", str), ("symbol", str),
                             ("side", int), ("R", float), ("et", "datetime64[ns, UTC]"))})
    X = pd.concat([pd.read_csv(f) for f in fs if f.stat().st_size > 5], ignore_index=True)
    X["date"] = X.date.astype(str)
    X = X[np.isfinite(X.r)].copy()
    X["R"] = X.r
    X["et"] = pd.to_datetime(X.entry_time, utc=True, format="mixed")
    return X


def replayed_sessions() -> dict[str, set]:
    """setup -> sessions it was replayed on (from the per-day meta files), traded or not."""
    out: dict[str, set] = {}
    for f in sorted((HERE / "trades").glob("????-??-??.meta.json")):
        m = json.loads(f.read_text())
        for s in m.get("setups", []):
            out.setdefault(s, set()).add(m["date"])
    return out


def match(rep: pd.DataFrame, liv: pd.DataFrame, window: float = MATCH_MIN) -> list[tuple[int, int]]:
    """Greedy nearest-entry matching on (setup, date, symbol, side), |entry diff| <= MATCH_MIN minutes."""
    pairs = []
    if not len(rep) or not len(liv):
        return pairs
    L = liv.reset_index()
    for k, g in rep.reset_index().groupby(["setup", "date", "symbol", "side"]):
        cand = L[(L.setup == k[0]) & (L.date == k[1]) & (L.symbol == k[2]) & (L.side == k[3])]
        if not len(cand):
            continue
        used = set()
        for _, r in g.sort_values("et").iterrows():
            d = (cand.et - r.et).abs().dt.total_seconds() / 60
            d = d[(d <= window) & ~cand["index"].isin(used)]
            if len(d):
                j = d.idxmin()
                used.add(cand.loc[j, "index"])
                pairs.append((r["index"], cand.loc[j, "index"]))
    return pairs


def stats(day_r: pd.Series, n: int, R: pd.Series | None = None, ndays: pd.Series | None = None) -> dict:
    """Record stats from per-trade R (R) or a per-date R series with per-date trade counts."""
    if not n:
        return dict(trades=0, sessions=0, totR=0.0, avgR=np.nan, shrunk=np.nan, exbest=np.nan, share=np.nan,
                    one_day=False, last5=np.nan)
    tot = float(day_r.sum())
    k = int((ndays > 0).sum()) if ndays is not None else len(day_r)
    bd = day_r.idxmax()
    bn = float(ndays.loc[bd]) if ndays is not None else 1
    exb = (tot - day_r.max()) / (n - bn) if k >= 2 and n > bn else np.nan
    share = day_r.max() / tot if tot > 0 and k >= 2 and day_r.max() > 0 else np.nan
    last = sorted(day_r.index)[-5:]
    l5 = float(day_r.loc[last].sum() / max(ndays.loc[last].sum(), 1e-9)) if ndays is not None else np.nan
    return dict(trades=round(n, 2), sessions=k, totR=round(tot, 3), avgR=tot / n, shrunk=tot / (n + 20), exbest=exb,
                share=share, one_day=bool(share == share and share >= 0.5), last5=l5)


def per_day(g: pd.DataFrame, w: float = 1.0) -> tuple[pd.Series, pd.Series]:
    if not len(g):
        return pd.Series(dtype=float), pd.Series(dtype=float)
    return g.groupby("date").R.sum() * w, g.groupby("date").size().astype(float) * w


OD_IN = dict(ses=5, n=15, shrunk=-0.02, exbest=-0.20, last5=-0.30, bt=-0.15)     # research/ondeck_build E5
REPS_MIN = dict(ses=8, n=30)
CAND = dict(shrunk=0.03, exbest=0.0, share=0.60)                                   # ROT balanced Candidate (lenient part)


def od_in(m: dict, bt) -> bool:
    if m["trades"] < OD_IN["n"] or m["sessions"] < OD_IN["ses"]:
        return False
    if not m["shrunk"] > OD_IN["shrunk"]:
        return False
    if not (m["exbest"] == m["exbest"] and m["exbest"] >= OD_IN["exbest"]):
        return False
    if not m["last5"] > OD_IN["last5"]:
        return False
    return not (bt == bt and bt is not None and bt < OD_IN["bt"])


def gen_screen() -> dict:
    """GEN setup -> generator screen expectancy (all, pre-creation lab sample; the Gen stand-in for the 2y backtest)."""
    snap = RUN.bjson("mcf-data-gen", "setups/2026-11-10.json") or {}
    out = {}
    for k, v in (snap.get("strategies") or {}).items():
        sc = ((v.get("gen") or {}).get("screen") or {}).get("all") or {}
        if "exp_r" in sc:
            out[k] = sc["exp_r"]
    return out


def bt2y() -> dict:
    p = RUN.ROOT / "research" / "rotation_design" / "inventory.csv"
    if not p.exists():
        return {}
    I = pd.read_csv(p)
    return {s: b for s, b in zip(I.setup, I.bt2y) if b == b}


def main():
    inv = pd.read_csv(HERE / "inventory.csv", keep_default_na=False)
    S = RUN.snapshots("9999")
    live_on = set(zip(S[S.enabled].setup, S[S.enabled].date))          # (setup, date) enabled in some live account
    L = live_trades()
    X = replay_trades()
    RS = replayed_sessions()
    X["family"] = X.setup.map(family)
    L["family"] = L.setup.map(family)

    # ---------------------------------------------------------------- 1. calibration (setup-sessions live AND replayed)
    X["live_on"] = pd.Series([(s, d) in live_on for s, d in zip(X.setup, X.date)], index=X.index, dtype=bool)
    cal_keys = {(s, d) for s, ds in RS.items() for d in ds if (s, d) in live_on}
    Xc = X[pd.Series([(s, d) in cal_keys for s, d in zip(X.setup, X.date)], index=X.index, dtype=bool)]
    Lc = L[pd.Series([(s, d) in cal_keys for s, d in zip(L.setup, L.date)], index=L.index, dtype=bool)]
    pairs = match(Xc, Lc)
    p10 = match(Xc, Lc, 10.0)                       # sensitivity: live polls can enter 5-6 min after the decision bar
    m10x = {a for a, _ in p10}
    mx = {a for a, _ in pairs}
    ml = {b for _, b in pairs}
    X["matched"] = X.index.isin(mx)
    L["matched"] = L.index.isin(ml)
    pr = pd.DataFrame([(X.loc[a, "family"], X.loc[a, "R"], L.loc[b, "R"],
                        abs((X.loc[a, "et"] - L.loc[b, "et"]).total_seconds()) / 60) for a, b in pairs],
                      columns=["family", "rep", "live", "entry_gap_min"])
    home = dict(zip(inv.setup, inv.home_tag))
    Xc = Xc.assign(acct=Xc.setup.map(home))
    Lc = Lc.assign(acct=Lc.setup.map(home))
    pr["acct"] = [home.get(X.loc[a, "setup"]) for a, _ in pairs]
    rows = []
    groups = [("family", f) for f in sorted(set(Xc.family) | set(Lc.family))] + \
             [("acct", a) for a in sorted(set(Xc.acct.dropna()) | set(Lc.acct.dropna()))] + [("family", "ALL")]
    for col, fam in groups:
        xa = Xc if fam == "ALL" else Xc[Xc[col] == fam]
        la = Lc if fam == "ALL" else Lc[Lc[col] == fam]
        pa = pr if fam == "ALL" else pr[pr[col] == fam]
        fam = fam if col == "family" else f"account:{fam}"
        nm = len(pa)
        d = pa.rep - pa.live
        rows.append(dict(family=fam, setup_sessions=len({(s, dd) for s, dd in zip(xa.setup, xa.date)} | {(s, dd) for s, dd in zip(la.setup, la.date)}),
                         replay_trades=len(xa), live_trades=len(la), matched=nm,
                         match_rate_live=nm / len(la) if len(la) else np.nan,
                         replay_only_share=1 - nm / len(xa) if len(xa) else np.nan,
                         live_only_share=1 - nm / len(la) if len(la) else np.nan,
                         jaccard=nm / (len(xa) + len(la) - nm) if (len(xa) + len(la) - nm) else np.nan,
                         rdiff_matched_mean=d.mean() if nm else np.nan, rdiff_matched_sd=d.std() if nm > 1 else np.nan,
                         same_minute_share=(pa.entry_gap_min < 1).mean() if nm else np.nan,
                         match_rate_live_10min=(len(m10x & set(xa.index)) / len(la)) if len(la) else np.nan,
                         replay_avgR=xa.R.mean() if len(xa) else np.nan, live_avgR=la.R.mean() if len(la) else np.nan,
                         replay_totR=xa.R.sum(), live_totR=la.R.sum()))
    C = pd.DataFrame(rows)
    C["haircut_raw"] = C.replay_avgR - C.live_avgR
    C.to_csv(HERE / "calibration_raw.csv", index=False, float_format="%.4f")
    allrow = C[C.family == "ALL"].iloc[0]
    n = C.replay_trades + C.live_trades
    for col, base in (("haircut_raw", allrow.haircut_raw), ("jaccard", allrow.jaccard)):
        C[col.replace("_raw", "") + "_shrunk"] = (C[col].fillna(base) * n + base * SHRINK_K) / (n + SHRINK_K)
    C["haircut"] = C.haircut_shrunk.clip(lower=0)     # conservative: a family where replay UNDERstates live gets 0, not a bonus
    C["weight"] = C.jaccard_shrunk.clip(W_MIN, W_MAX)
    C.loc[C.family == "ALL", ["haircut", "weight"]] = [max(allrow.haircut_raw, 0), float(np.clip(allrow.jaccard, W_MIN, W_MAX))]
    C.to_csv(HERE / "calibration.csv", index=False, float_format="%.4f")
    H = dict(zip(C.family, C.haircut))
    Wt = dict(zip(C.family, C.weight))
    hall, wall = H["ALL"], Wt["ALL"]

    # ---------------------------------------------------------------- 2./3. per-setup ledger
    gs, bt = gen_screen(), bt2y()
    out = []
    for r in inv.itertuples():
        s, fam = r.setup, family(r.setup)
        h, w = H.get(fam, hall), Wt.get(fam, wall)
        lv = L[L.setup == s]
        xr = X[(X.setup == s) & (X.date >= r.freeze)].copy()
        xr["R"] = xr.R - h                                            # haircut per trade
        ses_rep = sorted(d for d in RS.get(s, set()) if d >= r.freeze)
        live_ses = sorted({d for (ss, d) in live_on if ss == s})
        m_live = stats(*per_day(lv)[:1], len(lv), ndays=per_day(lv)[1]) if len(lv) else stats(pd.Series(dtype=float), 0)
        m_rep_raw = stats(per_day(X[(X.setup == s) & (X.date >= r.freeze)])[0], int(len(xr)),
                          ndays=per_day(xr)[1]) if len(xr) else stats(pd.Series(dtype=float), 0)
        m_rep = stats(per_day(xr)[0], int(len(xr)), ndays=per_day(xr)[1]) if len(xr) else stats(pd.Series(dtype=float), 0)
        # combined: live as is + replay trades that are NOT a copy of a live trade (replay-only on live sessions, and
        # every replay trade on sessions the setup did not run live), each at weight w, haircut applied
        add = xr[~xr.matched]
        dl, nl = per_day(lv)
        da, na = per_day(add, w)
        dc = dl.add(da, fill_value=0.0)
        nc = nl.add(na, fill_value=0.0)
        m_c = stats(dc, float(nc.sum()), ndays=nc) if nc.sum() > 0 else stats(pd.Series(dtype=float), 0)
        if len(nc):
            m_c["sessions"] = int(len(set(dl.index) | set(da.index)))
            m_c["eff_sessions"] = round(len(dl) + w * len(set(da.index) - set(dl.index)), 2)
        else:
            m_c["eff_sessions"] = 0
        b = gs.get(s, bt.get(s, np.nan))
        rec = dict(setup=s, family=fam, home=r.home_tag, side=r.side, freeze=r.freeze, gen=r.gen,
                   fwd_sessions_replayed=len(ses_rep), live_enabled_sessions=len(live_ses), haircut=h, weight=w,
                   bt=b, bt_src=("gen screen (all)" if s in gs else "2y" if s in bt else ""))
        for pre, m in (("live", m_live), ("fwd_raw", m_rep_raw), ("fwd", m_rep), ("comb", m_c)):
            for k in ("trades", "sessions", "totR", "avgR", "shrunk", "exbest", "share", "one_day", "last5"):
                rec[f"{pre}_{k}"] = m.get(k)
        rec["comb_eff_sessions"] = m_c.get("eff_sessions", 0)
        se = float(xr.R.std() / np.sqrt(len(xr))) if len(xr) > 1 else np.nan
        rec["fwd_se"] = se
        # rule 21 conservative value (replay as a filter): lower of replay avg R (haircut) and the backtest, minus one SE
        rec["r21_value"] = (min(m_rep["avgR"], b) if b == b else m_rep["avgR"]) - se if len(xr) > 1 else np.nan
        rec["fwd_added_trades"] = int(len(add))
        rec["fwd_added_on_dark_sessions"] = int((~add.live_on).sum())
        rec["reps_min"] = bool(rec["comb_eff_sessions"] >= REPS_MIN["ses"] and rec["comb_trades"] >= REPS_MIN["n"])
        mc = {**m_c, "sessions": rec["comb_eff_sessions"]}
        rec["od_in"] = bool(od_in(mc, b)) if m_c["trades"] else False
        rec["od_in_live_only"] = bool(od_in(m_live, b)) if m_live["trades"] else False
        rec["candidate"] = bool(rec["od_in"] and m_c["shrunk"] >= CAND["shrunk"] and (m_c["exbest"] or -1) > CAND["exbest"]
                                and not (m_c["share"] == m_c["share"] and m_c["share"] > CAND["share"]))
        out.append(rec)
    D = pd.DataFrame(out)
    D.to_csv(HERE / "ledger.csv", index=False, float_format="%.4f")

    # ---------------------------------------------------------------- 4. Gen fast-track
    G = D[D.gen & D.reps_min & D.od_in].copy().sort_values(["comb_shrunk", "comb_eff_sessions"], ascending=False)
    cnt = {"Testing A": 0, "Testing B": 0, "Testing C": 0}
    sug = []
    for x in G.itertuples():
        if x.candidate and not x.comb_one_day:
            sug.append("On Deck")
            continue
        busy = x.fwd_raw_trades / max(x.fwd_sessions_replayed, 1) > 3 or x.live_trades / max(x.live_sessions, 1) > 3
        tgt = "Testing A" if busy else min(("Testing B", "Testing C"), key=lambda k: cnt[k])
        cnt[tgt] += 1
        sug.append(tgt)
    G["from"] = G.home
    G["suggested"] = sug
    cols = ["setup", "from", "suggested", "side", "freeze", "live_trades", "live_sessions", "live_avgR", "live_totR",
            "fwd_sessions_replayed", "fwd_raw_trades", "fwd_sessions", "fwd_raw_avgR", "fwd_avgR", "fwd_totR",
            "fwd_added_trades", "weight", "haircut", "comb_trades", "comb_eff_sessions", "comb_avgR", "comb_shrunk",
            "comb_exbest", "comb_share", "comb_one_day", "comb_last5", "od_in_live_only", "candidate", "bt", "r21_value"]
    G[cols].to_csv(HERE / "gen_fasttrack.csv", index=False, float_format="%.4f")
    pd.set_option("display.width", 250)
    print(C.round(3).to_string(index=False))
    print(f"\nledger: {len(D)} setups; gen fast-track: {len(G)}")
    print(G[cols[:3] + ["live_trades", "live_avgR", "fwd_raw_trades", "fwd_avgR", "comb_trades", "comb_eff_sessions",
                        "comb_avgR", "comb_exbest", "comb_one_day"]].head(15).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
