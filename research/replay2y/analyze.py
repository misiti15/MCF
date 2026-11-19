"""2-year live-code replay: per-setup records, overlap check vs live, comparison with the old 2-year sources.

    python research/replay2y/analyze.py --runs RUNS_DIR[,RUNS_DIR...] --overlap OVERLAP_RUN --live-dir JOURNALS \
        --out research/replay2y

RUNS_DIR: mcf.replay run output (<account>/<day>/{trades,signals}.csv.gz + stats.json) of the 2-year sessions.
OVERLAP_RUN: the same engine run --as-live on live sessions. JOURNALS: <data-branch>.db live journals.
R per entry lot = (pnl - LR8 live cost model on that side's own fills) / risk (research/replay_cal/score.py::lots),
for replay and live alike. Writes per_setup.csv, overlap_account.csv, overlap_setup.csv, compare.csv, summary.json.
Educational only - not financial advice."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "replay_cal"))
import score as SC  # noqa: E402  (research/replay_cal/score.py: lots, match, clustered)

ACCTS = ["primary", "testing", "testing2", "explore1", "livelab", "testingd", "testinge", "testingf", "gen", "graveyard"]
DB = {"primary": "mcf-data", **{a: f"mcf-data-{a}" for a in ACCTS if a != "primary"}}
LIVE_END = "2026-11-17"            # last complete live session (11-18 was in progress)
HAIRCUT = 0.027                    # research/replay_cal: replay optimism haircut per trade


def period(day: str) -> str:
    return "2024-10" if day < "2025-01-01" else ("2025H1" if day < "2025-07-01" else "2025H2+")


def load_runs(dirs: list[Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(lots of every replayed 2-year session, sessions run per account with the enabled setups)."""
    lots, ran = [], []
    for base in dirs:
        for st in sorted(base.glob("*/*/stats.json")):
            acct, day = st.parent.parent.name, st.parent.name
            s = json.loads(st.read_text())
            if "error" in s:
                continue
            if any((r["account"] == acct and r["day"] == day) for r in ran):
                continue
            ran.append(dict(account=acct, day=day, setups=s.get("setups") or [], seconds=s.get("seconds")))
            t = pd.read_csv(st.parent / "trades.csv.gz")
            if len(t):
                t = t[t["broker_order_id"].notna()].copy()
                t["date"] = day
                L = SC.lots(t)
                L["account"] = acct
                lots.append(L)
    return (pd.concat(lots, ignore_index=True) if lots else pd.DataFrame()), pd.DataFrame(ran)


def record(L: pd.DataFrame) -> dict:
    """trades, sessions with a trade, avg R, total R, win %, avg R w/o best day, best day share, green-day %."""
    r = L["r"].dropna()
    if not len(r):
        return dict(trades=0)
    day = L.dropna(subset=["r"]).groupby("day")["r"].sum()
    best = day.idxmax()
    rest = L[(L["day"] != best)]["r"].dropna()
    tot = float(r.sum())
    return dict(trades=int(len(r)), trade_days=int(len(day)), avg_r=round(float(r.mean()), 4), total_r=round(tot, 2),
                win_pct=round(float((r > 0).mean()) * 100, 1),
                avg_r_wo_best=round(float(rest.mean()), 4) if len(rest) else np.nan,
                best_day=best, best_day_share=round(float(day.max()) / tot * 100, 1) if tot > 0 else np.nan,
                green_day_pct=round(float((day > 0).mean()) * 100, 1))


def live_lots(live_dir: Path, until: str = LIVE_END, since: str | None = None) -> pd.DataFrame:
    out = []
    for a in ACCTS:
        p = live_dir / f"{DB[a]}.db"
        if not p.exists():
            continue
        con = sqlite3.connect(str(p))
        t = pd.read_sql("SELECT * FROM trades WHERE run_id=1", con)
        con.close()
        t = t[t["broker_order_id"].notna() & (t["date"].astype(str).str[:10] <= until)]
        if since:
            t = t[t["date"].astype(str).str[:10] >= since]
        if len(t):
            L = SC.lots(t)
            L["account"] = a
            out.append(L)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def overlap(run: Path, live_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Match / extra / bias per account and per setup (research/replay_cal/score.py matching: same setup + symbol +
    side + decision bar, exact minute; +-1 minute as a secondary number)."""
    rows, srows, pairs_all, Ls, Rs = [], [], [], [], []
    for a in ACCTS:
        days = sorted(p.name for p in (run / a).glob("*") if (p / "stats.json").exists()) if (run / a).exists() else []
        days = [d for d in days if "error" not in json.loads((run / a / d / "stats.json").read_text())]
        p = live_dir / f"{DB[a]}.db"
        if not days or not p.exists():
            continue
        _, rt, have = SC.load_run(run, a, days)
        _, lt = SC.load_live(p, have)
        L, R = SC.lots(lt), SC.lots(rt)
        if not len(L) and not len(R):
            continue
        L["account"], R["account"] = a, a
        pr = SC.match(L, R, 0) if len(L) and len(R) else []
        pr1 = SC.match(L, R, 1) if len(L) and len(R) else []
        d = pd.DataFrame([dict(day=L.iloc[i]["day"], setup=L.iloc[i]["setup"], x=R.iloc[j]["r"] - L.iloc[i]["r"])
                          for i, j in pr]).dropna() if pr else pd.DataFrame(columns=["day", "setup", "x"])
        m, se, n = SC.clustered(d) if len(d) else (np.nan, np.nan, 0)
        rows.append(dict(account=a, sessions=len(have), live_trades=len(L), replay_trades=len(R), matched=len(pr),
                         match_pct=round(len(pr) / len(L) * 100, 1) if len(L) else np.nan,
                         match_pm1_pct=round(len(pr1) / len(L) * 100, 1) if len(L) else np.nan,
                         extra_pct=round((len(R) - len(pr)) / len(L) * 100, 1) if len(L) else np.nan,
                         bias_r=round(m, 4), bias_se=round(se, 4) if se == se else np.nan,
                         live_avg_r=round(float(L["r"].mean()), 4) if len(L) else np.nan,
                         replay_avg_r=round(float(R["r"].mean()), 4) if len(R) else np.nan,
                         live_total_r=round(float(L["r"].sum()), 1), replay_total_r=round(float(R["r"].sum()), 1)))
        mi, mj = {i for i, _ in pr}, {j for _, j in pr}
        L["matched"] = [i in mi for i in range(len(L))]
        R["matched"] = [j in mj for j in range(len(R))]
        Ls.append(L)
        Rs.append(R)
        pairs_all.append(d.assign(account=a))
    acc = pd.DataFrame(rows)
    L = pd.concat(Ls, ignore_index=True) if Ls else pd.DataFrame()
    R = pd.concat(Rs, ignore_index=True) if Rs else pd.DataFrame()
    P = pd.concat(pairs_all, ignore_index=True) if pairs_all else pd.DataFrame()
    for s in sorted(set(L.get("setup", [])) | set(R.get("setup", []))):
        l, r = L[L.setup == s] if len(L) else L, R[R.setup == s] if len(R) else R
        p = P[P.setup == s] if len(P) else P
        srows.append(dict(setup=s, accounts=",".join(sorted(set(l.get("account", [])) | set(r.get("account", [])))),
                          live_trades=len(l), replay_trades=len(r), matched=int(l["matched"].sum()) if len(l) else 0,
                          match_pct=round(l["matched"].mean() * 100, 1) if len(l) else np.nan,
                          extra_pct=round((len(r) - int(r["matched"].sum())) / len(l) * 100, 1) if len(l) else np.nan,
                          bias_r=round(float(p["x"].mean()), 4) if len(p) else np.nan,
                          live_avg_r=round(float(l["r"].mean()), 4) if len(l) else np.nan,
                          replay_avg_r=round(float(r["r"].mean()), 4) if len(r) else np.nan))
    pooled = {}
    if len(acc):
        PP = P.assign(day=P["account"] + "|" + P["day"]) if len(P) else P     # cluster = account-session
        m, se, n = SC.clustered(PP) if len(PP) else (np.nan, np.nan, 0)
        lt, rt, mt = int(acc.live_trades.sum()), int(acc.replay_trades.sum()), int(acc.matched.sum())
        dl = L.groupby(["account", "day"])["r"].sum()
        dr = R.groupby(["account", "day"])["r"].sum().reindex(dl.index, fill_value=0.0)
        pooled = dict(sessions=sorted(set(L["day"])), live_trades=lt, replay_trades=rt, matched=mt,
                      match_pct=round(mt / lt * 100, 1), extra_pct=round((rt - mt) / lt * 100, 1),
                      bias_r=round(m, 4), bias_ci=[round(m - 1.96 * se, 4), round(m + 1.96 * se, 4)],
                      live_total_r=round(float(L["r"].sum()), 1), replay_total_r=round(float(R["r"].sum()), 1),
                      live_avg_r=round(float(L["r"].mean()), 4), replay_avg_r=round(float(R["r"].mean()), 4),
                      unmatched_replay_avg_r=round(float(R[~R.matched]["r"].mean()), 4),
                      unmatched_live_avg_r=round(float(L[~L.matched]["r"].mean()), 4),
                      daily_corr=round(float(np.corrcoef(dl.values, dr.values)[0, 1]), 3) if len(dl) > 2 else None,
                      daily_sign=round(float(np.mean(np.sign(dl.values) == np.sign(dr.values))) * 100, 1))
    return acc, pd.DataFrame(srows), pooled


def old_sources(names: set[str]) -> tuple[dict, dict]:
    si = json.loads((ROOT / "docs/live/sim_inputs.json").read_text())
    scr = {k: (v["backtest"]["avg_r"], v["backtest"]["trades"]) for k, v in si["setups"].items() if "backtest" in v}
    bt = {}
    for r in csv.DictReader(open(ROOT / "research/history2y/rescore.csv")):
        if not r["exp_r"]:
            continue
        name = r["setup"]
        if " " in name:   # "RW3 bdi-rw-..." -> the base live setup (as research/src_value/score.py)
            code = name.split()[0]
            m = [n for n in names if n.startswith(code + "-") and "-FD" not in n and "-WB" not in n]
            if len(m) != 1:
                continue
            name = m[0]
        bt[name] = (float(r["exp_r"]), int(float(r["n"])))
    return scr, bt


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--overlap")
    ap.add_argument("--live-dir", required=True)
    ap.add_argument("--out", default=str(ROOT / "research" / "replay2y"))
    a = ap.parse_args(argv)
    out = Path(a.out)
    lots, ran = load_runs([Path(x) for x in a.runs.split(",")])
    live = live_lots(Path(a.live_dir))
    live_rec = {s: record(g) for s, g in live.groupby("setup")} if len(live) else {}
    live_acc = live.groupby("setup")["account"].agg(lambda x: ",".join(sorted(set(x)))).to_dict() if len(live) else {}
    rows = []
    for acct, g in ran.groupby("account"):
        sess = sorted(g.day)
        enabled = sorted({s for ss in g.setups for s in ss})
        for s in enabled:
            Ls = lots[(lots.account == acct) & (lots.setup == s)] if len(lots) else pd.DataFrame(columns=["r", "day"])
            rec = record(Ls) if len(Ls) else dict(trades=0)
            per = {}
            for pname in ("2024-10", "2025H1", "2025H2+"):
                x = Ls[Ls.day.map(period) == pname] if len(Ls) else Ls
                per[pname] = (round(float(x["r"].mean()), 4) if len(x) else np.nan, len(x))
            lr = live_rec.get(s, {})
            rows.append(dict(account=acct, setup=s, sessions_run=len(sess), **{f"rp_{k}": v for k, v in rec.items()},
                             trades_per_session=round(rec.get("trades", 0) / len(sess), 2),
                             **{f"rp_avg_r_{p}": v[0] for p, v in per.items()},
                             **{f"rp_n_{p}": v[1] for p, v in per.items()},
                             live_accounts=live_acc.get(s, ""), live_trades=lr.get("trades", 0),
                             live_avg_r=lr.get("avg_r", np.nan), live_avg_r_wo_best=lr.get("avg_r_wo_best", np.nan),
                             live_best_day_share=lr.get("best_day_share", np.nan),
                             live_green_day_pct=lr.get("green_day_pct", np.nan)))
    ps = pd.DataFrame(rows)
    names = set(ps.setup) | set(live_rec)
    scr, bt = old_sources(names)
    ps["screen_avg_r"] = ps.setup.map(lambda s: scr.get(s, (np.nan, 0))[0])
    ps["screen_n"] = ps.setup.map(lambda s: scr.get(s, (np.nan, 0))[1])
    import re

    def bt_of(s):   # exact name, else the base setup the variant was built on (suffixes -FD / -WB# / -R2A etc. dropped)
        if s in bt:
            return bt[s] + ("exact",)
        base = re.sub(r"(-FD.*|-WB\d+)$", "", s)
        for k in (base, base.replace("-FD", "")):
            if k in bt:
                return bt[k] + ("base",)
        return (np.nan, 0, "")
    ps["backtest_exp_r"] = ps.setup.map(lambda s: bt_of(s)[0])
    ps["backtest_n"] = ps.setup.map(lambda s: bt_of(s)[1])
    ps["backtest_match"] = ps.setup.map(lambda s: bt_of(s)[2])
    ps["one_day_tag"] = ps["rp_best_day_share"] >= 50 if "rp_best_day_share" in ps else False

    def fast_lane(r) -> bool:
        pers = [(r[f"rp_avg_r_{p}"], r[f"rp_n_{p}"]) for p in ("2024-10", "2025H1", "2025H2+")]
        pers = [v for v, n in pers if n > 0]
        return bool(r["live_trades"] < 20 and r.get("rp_trades", 0) >= 30 and r["rp_avg_r"] > HAIRCUT
                    and r["rp_avg_r_wo_best"] > 0 and r["rp_best_day_share"] < 50 and r["rp_green_day_pct"] >= 50
                    and sum(v > 0 for v in pers) >= 2 and min(pers) > -0.10)

    ps["fast_lane_flag"] = [fast_lane(r) if r.get("rp_trades", 0) else False for _, r in ps.iterrows()]
    ps = ps.sort_values(["account", "setup"])
    ps.to_csv(out / "per_setup.csv", index=False)
    summ = dict(sessions_run=ran.groupby("account")["day"].apply(lambda x: sorted(x)).to_dict(),
                account_sessions=len(ran), replay_trades=int(len(lots)),
                avg_seconds=round(float(ran.seconds.mean()), 1) if len(ran) else None)
    if a.overlap:
        acc, st, pooled = overlap(Path(a.overlap), Path(a.live_dir))
        acc.to_csv(out / "overlap_account.csv", index=False)
        st.to_csv(out / "overlap_setup.csv", index=False)
        summ["overlap"] = pooled
    (out / "summary.json").write_text(json.dumps({**summ, "note": "Educational only - not financial advice."},
                                                 indent=1, default=str))
    print(json.dumps(summ.get("overlap", {}), indent=1, default=str))
    print(ps.head(3).T)


if __name__ == "__main__":
    main()
