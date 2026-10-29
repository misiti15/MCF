"""REPS audit (research rule 21): replayed sessions vs the live paper journals (trades / signals, run_id 1).

    MCF_REPLAY_STORE=<store> python research/bdi/replay_audit1029/compare.py [--out results.json]

Trade match = a live trade with a replay trade of the same setup + symbol + decision (entry-signal) minute on the same
session (exact minute; +-1 minute also reported). Windows: pre-fix 10-06..10-26 (live len(bars)%5 gate bug) and post-fix
10-27..10-29. Avg R: the journal r_multiple (Alpaca paper fills = half-spread crossing) and, on top, the production
cost layer (config costs: 1 bp + $0.01/share per side, +$0.02/share on stop exits; limit/target exits excluded) applied
identically to live and replay trades. Educational only - not financial advice."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path.insert(0, str(ROOT / "research" / "replay"))
sys.path.insert(0, str(ROOT))
from validate import _bar_min, _trade_min, live_journal, match  # noqa: E402

from mcf.replay import store  # noqa: E402

ACCTS = ["primary", "testing", "testing2", "graveyard", "gen"]
NAMES = {"primary": "Primary", "testing": "Testing 1", "testing2": "Testing 2", "graveyard": "Graveyard", "gen": "Gen"}
FIX = "2026-10-27"
SKIPCLASS = [("spread", "spread"), ("crosscheck", "quote crosscheck"), ("cross-check", "quote crosscheck"),
             ("quote", "quote crosscheck"), ("shortable", "borrow / ETB"), ("etb", "borrow / ETB"),
             ("borrow", "borrow / ETB"), ("twin", "twin"), ("daily loss", "-2R / daily-loss latch"),
             ("loss limit", "-2R / daily-loss latch"), ("halt", "halted"), ("lot cap", "lot cap / caps"),
             ("max positions", "lot cap / caps"), ("already in symbol", "already in symbol"),
             ("rejected", "broker reject"), ("stale", "stale data")]


def cls(status, reason) -> str:
    t = f"{status} {reason}".lower()
    if status == "submitted":
        return "submitted"
    for k, v in SKIPCLASS:
        if k in t:
            return v
    return f"other: {str(reason)[:30]}"


def cost_r(df: pd.DataFrame, c: dict) -> pd.Series:
    """Production cost layer in R per trade (both sides; exit side waived on target/limit exits)."""
    e, x = df.entry.astype(float), df.exit.astype(float)
    risk = (e - df.stop.astype(float)).abs().replace(0, np.nan)
    per = lambda p: p * c["slippage_bps"] / 1e4 + c["slippage_per_share"]  # noqa: E731
    reason = df.exit_reason.astype(str).str.lower()
    exit_c = np.where(reason.str.contains("target"), 0.0,
                      per(x) + np.where(reason.str.contains("stop|trail"), c["stop_slippage_per_share"], 0.0))
    return ((per(e) + exit_c) / risk).fillna(0.0)


def load(account: str, run: Path):
    lsig, ltr = live_journal(account)
    rdir = run / account
    days = sorted(p.parent.name for p in rdir.glob("*/stats.json") if (p.parent / "signals.csv.gz").exists())
    rs, rt, st = [], [], {}
    for d in days:
        s = pd.read_csv(rdir / d / "signals.csv.gz")
        t = pd.read_csv(rdir / d / "trades.csv.gz")
        rs.append(s.assign(day=d))
        rt.append(t.assign(day=d))
        st[d] = json.loads((rdir / d / "stats.json").read_text())
    rs = pd.concat(rs, ignore_index=True) if rs else pd.DataFrame(columns=lsig.columns)
    rt = pd.concat(rt, ignore_index=True) if rt else pd.DataFrame(columns=ltr.columns)
    ls = lsig[lsig.day.isin(days)].copy().reset_index(drop=True)
    lt = ltr[ltr.date.isin(days)].copy().reset_index(drop=True)
    lt["day"] = lt["date"]
    for x in (ls, rs):
        x["min"] = [_bar_min(i, t) for i, t in zip(x["info"], x["ts"])]
    for x, sg in ((lt, ls), (rt, rs)):
        by = {(d, str(o)): m for d, o, m in zip(sg["day"], sg["broker_order_id"], sg["min"]) if o is not None and not pd.isna(o)}
        x["min"] = [by.get((d, str(o)), _trade_min(m)) for d, o, m in zip(x["day"], x["broker_order_id"], x["meta"])]
    return ls, lt, rs, rt, st


def avg(x):
    return round(float(x.mean()), 3) if len(x) else None


def window(account, ls, lt, rs, rt, st, days, costs) -> dict:
    lab = set(store.symbols())
    ls, rs = ls[ls.day.isin(days)], rs[rs.day.isin(days)]
    lt, rt = lt[lt.day.isin(days)], rt[rt.day.isin(days)]
    replayed = set().union(*[set(st[d].get("setups") or []) for d in days if d in st]) if days else set()
    out = {"sessions": len(days), "first": min(days) if days else None, "last": max(days) if days else None}
    tp0 = match(lt, rt, tol=0)
    tp1 = match(lt, rt, tol=1)
    li = {i for i, _ in tp0}
    ri = {j for _, j in tp0}
    lt_c = lt.r_multiple.astype(float) - cost_r(lt, costs) if len(lt) else lt.r_multiple
    rt_c = rt.r_multiple.astype(float) - cost_r(rt, costs) if len(rt) else rt.r_multiple
    inu = lt.symbol.isin(lab)
    out.update(live_trades=len(lt), live_trades_in_lab_universe=int(inu.sum()), replay_trades=len(rt),
               matched_exact=len(tp0), matched_pm1=len(tp1),
               match_pct=round(100 * len(tp0) / max(1, len(lt)), 1),
               match_pct_pm1=round(100 * len(tp1) / max(1, len(lt)), 1),
               match_pct_in_universe=round(100 * len(tp0) / max(1, int(inu.sum())), 1),
               replay_only=len(rt) - len(ri), replay_only_pct_of_live=round(100 * (len(rt) - len(ri)) / max(1, len(lt)), 1),
               live_avg_r=avg(lt.r_multiple.astype(float)), replay_avg_r=avg(rt.r_multiple.astype(float)),
               live_avg_r_costs=avg(lt_c), replay_avg_r_costs=avg(rt_c),
               live_avg_r_in_universe_costs=avg(lt_c[inu]),
               live_total_r=round(float(lt.r_multiple.astype(float).sum()), 2),
               replay_total_r=round(float(rt.r_multiple.astype(float).sum()), 2))
    if out["live_avg_r_costs"] is not None and out["replay_avg_r_costs"] is not None:
        g = out["replay_avg_r_costs"] - out["live_avg_r_costs"]
        out["gap_costs"] = round(g, 3)
        out["within_003"] = abs(g) <= 0.03
        out["optimistic"] = g > 0.03
    if tp0:
        a = lt.loc[[i for i, _ in tp0]].r_multiple.astype(float).values
        b = rt.loc[[j for _, j in tp0]].r_multiple.astype(float).values
        out["matched_r_diff_mean"] = round(float((b - a).mean()), 3)
        out["matched_live_avg_r"] = round(float(a.mean()), 3)
        out["matched_replay_avg_r"] = round(float(b.mean()), 3)
        out["matched_same_exit"] = round(float(np.mean([str(x).replace("trail", "stop") == str(y).replace("trail", "stop")
                                                          for x, y in zip(lt.loc[[i for i, _ in tp0]].exit_reason,
                                                                          rt.loc[[j for _, j in tp0]].exit_reason)])), 3)
    # ---- why live trades are missing from the replay
    sp = match(ls, rs, tol=0)
    s_l2r = dict(sp)
    lsig_by_oid = {(d, str(o)): i for i, d, o in zip(ls.index, ls.day, ls.broker_order_id) if o is not None and not pd.isna(o)}
    miss = []
    for i in lt.index.difference(list(li)):
        r = lt.loc[i]
        if r.symbol not in lab:
            miss.append("symbol not in replay (lab) universe")
            continue
        if r.strategy not in replayed:
            miss.append("setup not replayable (module missing)")
            continue
        si = lsig_by_oid.get((r.day, str(r.broker_order_id)))
        j = s_l2r.get(si) if si is not None else None
        if j is None:
            # replay fired the same setup+symbol on a different minute?
            near = rs[(rs.day == r.day) & (rs.strategy == r.strategy) & (rs.symbol == r.symbol)]
            miss.append("replay signal at another minute" if len(near) else "no replay signal (data at decision minute)")
        else:
            rr = rs.loc[j]
            if rr.status == "submitted":
                miss.append("replay submitted, not filled / no trade")
            else:
                miss.append("replay skipped: " + cls(rr.status, rr.reason))
    out["live_only_causes"] = pd.Series(miss, dtype=object).value_counts().to_dict()
    # diagnostic ceiling (not the audit number): if the replay's spread draw had agreed with live's quote at the minute
    sp_n = out["live_only_causes"].get("replay skipped: spread", 0)
    out["diag_match_pct_if_spread_agreed"] = round(100 * (len(tp0) + sp_n) / max(1, len(lt)), 1)
    out["diag_match_pct_if_spread_agreed_in_universe"] = round(100 * (len(tp0) + sp_n) / max(1, int(inu.sum())), 1)
    # ---- why replay trades are extra
    r2l = {j: i for i, j in sp}
    rsig_by_oid = {(d, str(o)): j for j, d, o in zip(rs.index, rs.day, rs.broker_order_id) if o is not None and not pd.isna(o)}
    extra = []
    for j in rt.index.difference(list(ri)):
        r = rt.loc[j]
        sj = rsig_by_oid.get((r.day, str(r.broker_order_id)))
        i = r2l.get(sj) if sj is not None else None
        if i is None:
            near = ls[(ls.day == r.day) & (ls.strategy == r.strategy) & (ls.symbol == r.symbol)]
            extra.append("live signal at another minute" if len(near) else "no live signal" +
                         (" (pre-10-27 %5 gate era)" if r.day < FIX else ""))
        else:
            q = ls.loc[i]
            extra.append("live submitted, no live trade (unfilled / rejected)" if q.status == "submitted"
                         else "live skipped: " + cls(q.status, q.reason))
    out["replay_only_causes"] = pd.Series(extra, dtype=object).value_counts().to_dict()
    # ---- matched signals with different outcome
    dis = [f"{cls(ls.at[i,'status'], ls.at[i,'reason'])} -> {cls(rs.at[j,'status'], rs.at[j,'reason'])}" for i, j in sp
           if (ls.at[i, "status"] == "submitted") != (rs.at[j, "status"] == "submitted")]
    out["signals"] = {"live": len(ls), "replay": len(rs), "matched": len(sp),
                      "match_pct_live": round(100 * len(sp) / max(1, len(ls)), 1),
                      "live_in_lab_universe": int(ls.symbol.isin(lab).sum()),
                      "outcome_flips": pd.Series(dis, dtype=object).value_counts().head(12).to_dict()}
    # live-only skip reasons overall (what live did that the replay may not model)
    out["live_skip_reasons"] = pd.Series([cls(s, r) for s, r in zip(ls.status, ls.reason) if s != "submitted"],
                                         dtype=object).value_counts().head(12).to_dict()
    out["replay_skip_reasons"] = pd.Series([cls(s, r) for s, r in zip(rs.status, rs.reason) if s != "submitted"],
                                           dtype=object).value_counts().head(12).to_dict()
    # per setup (for the filter / review)
    rows = []
    for n in sorted(set(lt.strategy) | set(rt.strategy)):
        a, b = lt[lt.strategy == n], rt[rt.strategy == n]
        rows.append(dict(setup=n, live_n=len(a), live_avg_r=avg(a.r_multiple.astype(float)), replay_n=len(b),
                         replay_avg_r=avg(b.r_multiple.astype(float))))
    out["per_setup"] = rows
    out["errors"] = {d: st[d].get("error") for d in days if d in st and st[d].get("error")}
    out["missing_modules"] = sorted(set(sum([st[d].get("missing_modules") or [] for d in days if d in st], [])))
    return out


def pooled(parts: list[dict], frames) -> dict:
    """Overall: trade-weighted across accounts."""
    o = {}
    for k in ("live_trades", "replay_trades", "matched_exact", "matched_pm1", "replay_only", "live_trades_in_lab_universe"):
        o[k] = int(sum(p.get(k, 0) for p in parts))
    o["match_pct"] = round(100 * o["matched_exact"] / max(1, o["live_trades"]), 1)
    o["match_pct_pm1"] = round(100 * o["matched_pm1"] / max(1, o["live_trades"]), 1)
    o["match_pct_in_universe"] = round(100 * o["matched_exact"] / max(1, o["live_trades_in_lab_universe"]), 1)
    lc = pd.concat([f[0] for f in frames]) if frames else pd.Series(dtype=float)
    rc = pd.concat([f[1] for f in frames]) if frames else pd.Series(dtype=float)
    o["live_avg_r_costs"], o["replay_avg_r_costs"] = avg(lc), avg(rc)
    if o["live_avg_r_costs"] is not None and o["replay_avg_r_costs"] is not None:
        g = o["replay_avg_r_costs"] - o["live_avg_r_costs"]
        o.update(gap_costs=round(g, 3), within_003=abs(g) <= 0.03, optimistic=g > 0.03)
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=str(store.STORE / "runs" / "reps1029"))
    ap.add_argument("--out", default=str(ROOT / "research/bdi/replay_audit1029/results.json"))
    a = ap.parse_args()
    import yaml
    costs = yaml.safe_load((ROOT / "config/default.yaml").read_text())["costs"]
    res = {"_note": "Educational only - not financial advice.", "accounts": {}, "overall": {}}
    fr = {"pre": [], "post": [], "all": []}
    parts = {"pre": [], "post": [], "all": []}
    for ac in ACCTS:
        if not (Path(a.run) / ac).exists():
            continue
        ls, lt, rs, rt, st = load(ac, Path(a.run))
        days = sorted(st)
        res["accounts"][ac] = {}
        for w, dd in (("pre", [d for d in days if d < FIX]), ("post", [d for d in days if d >= FIX]), ("all", days)):
            r = window(ac, ls, lt, rs, rt, st, dd, costs)
            res["accounts"][ac][w] = r
            parts[w].append(r)
            x, y = lt[lt.day.isin(dd)], rt[rt.day.isin(dd)]
            fr[w].append((x.r_multiple.astype(float) - cost_r(x, costs) if len(x) else pd.Series(dtype=float),
                          y.r_multiple.astype(float) - cost_r(y, costs) if len(y) else pd.Series(dtype=float)))
    for w in parts:
        res["overall"][w] = pooled(parts[w], fr[w])
    Path(a.out).write_text(json.dumps(res, indent=1, default=str))
    for w in ("pre", "post", "all"):
        print(f"===== window {w}")
        for ac, r in res["accounts"].items():
            x = r[w]
            print(f"{NAMES[ac]:10s} s={x['sessions']:2d} live={x['live_trades']:5d} (lab {x['live_trades_in_lab_universe']}) "
                  f"rep={x['replay_trades']:5d} match={x['match_pct']}% (+-1 {x['match_pct_pm1']}%, in-univ "
                  f"{x['match_pct_in_universe']}%) extra={x['replay_only']} liveR={x['live_avg_r_costs']} "
                  f"repR={x['replay_avg_r_costs']} gap={x.get('gap_costs')} | spread-agreed ceiling "
                  f"{x['diag_match_pct_if_spread_agreed']}% / in-univ {x['diag_match_pct_if_spread_agreed_in_universe']}%")
        print("overall", res["overall"][w])
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    main()
