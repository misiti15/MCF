"""Replay vs true live: the replayed sessions (python -m mcf.replay run --as-live ...) against the paper journals of the
accounts' data branches (journal.db, trades / signals run_id 1).

    python research/replay/validate.py --run data/replay/runs/val-paper [--out research/replay/validation.json]

Signals are matched on (setup, symbol, decision bar HH:MM) within +-1 minute (the decision bar is info.bar_time, the
same field the runner journals live); trades on (setup, symbol, decision bar) parsed from the entry's client order id.
Educational only - not financial advice."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf.replay import harness, store  # noqa: E402
from mcf.replay.export import setup_stats  # noqa: E402

COID = re.compile(r'"coid": "[^"]*-(\d{8})-(\d{4})"')


def live_journal(account: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"{harness.data_branch(account)}:journal.db"],
                       capture_output=True)
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        f.write(r.stdout)
        f.flush()
        con = sqlite3.connect(f.name)
        sig = pd.read_sql("SELECT * FROM signals WHERE run_id=1", con)
        tr = pd.read_sql("SELECT * FROM trades WHERE run_id=1", con)
        con.close()
    return sig, tr


def _bar_min(info, ts) -> int | None:
    try:
        bt = json.loads(info or "{}").get("bar_time")
    except ValueError:
        bt = None
    if not bt:
        try:
            t = pd.Timestamp(ts).tz_convert("America/New_York")
            return t.hour * 60 + t.minute - 1
        except Exception:
            return None
    return int(bt[:2]) * 60 + int(bt[2:])


def _trade_min(meta) -> int | None:
    m = COID.search(str(meta or ""))
    return None if not m else int(m.group(2)[:2]) * 60 + int(m.group(2)[2:])


def match(a: pd.DataFrame, b: pd.DataFrame, tol: int = 1) -> list[tuple[int, int]]:
    """Greedy one-to-one pairs of rows (index a, index b) with equal (day, strategy, symbol) and |minute diff| <= tol."""
    pairs, used = [], set()
    bg = {k: g for k, g in b.groupby(["day", "strategy", "symbol"])}
    for k, g in a.groupby(["day", "strategy", "symbol"]):
        h = bg.get(k)
        if h is None:
            continue
        for i, m in zip(g.index, g["min"]):
            best = None
            for j, n in zip(h.index, h["min"]):
                if j in used or m is None or n is None or pd.isna(m) or pd.isna(n):
                    continue
                d = abs(int(m) - int(n))
                if d <= tol and (best is None or d < best[0]):
                    best = (d, j)
            if best is not None:
                used.add(best[1])
                pairs.append((i, best[1]))
    return pairs


def compare(account: str, run: Path) -> dict:
    lsig, ltr = live_journal(account)
    rdir = run / account
    days = sorted(p.parent.name for p in rdir.glob("*/stats.json") if (p.parent / "signals.csv.gz").exists())
    days = [d for d in days if d in set(lsig.day)]
    rs, rt, stats = [], [], []
    for d in days:
        s = pd.read_csv(rdir / d / "signals.csv.gz")
        t = pd.read_csv(rdir / d / "trades.csv.gz")
        rs.append(s.assign(day=d))
        rt.append(t.assign(day=d))
        stats.append(json.loads((rdir / d / "stats.json").read_text()))
    rs = pd.concat(rs, ignore_index=True) if rs else pd.DataFrame()
    rt = pd.concat(rt, ignore_index=True) if rt else pd.DataFrame()
    ls = lsig[lsig.day.isin(days)].copy()
    lt = ltr[ltr.date.isin(days)].copy()
    lt["day"] = lt["date"]
    replayed = set().union(*[set(x.get("setups") or []) for x in stats]) if stats else set()
    for x in (ls, rs):
        x["min"] = [_bar_min(i, t) for i, t in zip(x["info"], x["ts"])]
    for x, sg in ((lt, ls), (rt, rs)):         # a trade's decision bar: its entry signal's (by order id), else its coid
        by_oid = {(d, str(o)): m for d, o, m in zip(sg["day"], sg["broker_order_id"], sg["min"])
                  if o is not None and not pd.isna(o)}            # replay order ids restart every session: key by day
        x["min"] = [by_oid.get((d, str(o)), _trade_min(m)) for d, o, m in zip(x["day"], x["broker_order_id"], x["meta"])]
    lab = set(store.symbols())
    out = {"account": account, "sessions": days, "replayed_setups": len(replayed)}
    # ---- signals
    pairs = match(ls, rs)
    li, ri = {i for i, _ in pairs}, {j for _, j in pairs}
    l_un, r_un = ls.loc[~ls.index.isin(li)], rs.loc[~rs.index.isin(ri)]
    cause = np.where(~l_un.symbol.isin(lab), "symbol not in replay universe",
                     np.where(~l_un.strategy.isin(replayed), "setup not replayed (module missing)", "other"))
    out["signals"] = {"live": len(ls), "replay": len(rs), "matched": len(pairs),
                      "match_rate_live": round(len(pairs) / max(1, len(ls)), 3),
                      "match_rate_replay": round(len(pairs) / max(1, len(rs)), 3),
                      "live_only_by_cause": pd.Series(cause).value_counts().to_dict(),
                      "live_only_in_universe": int((cause == "other").sum()),
                      "replay_only": len(r_un),
                      "replay_only_symbol_in_live_universe_but_no_live_signal": int(len(r_un))}
    # live_only 'other' broken down by live status
    oth = l_un[cause == "other"]
    out["signals"]["live_only_other_by_status"] = oth.status.value_counts().to_dict()
    # status agreement on matched signals
    st = pd.DataFrame([(ls.at[i, "status"], ls.at[i, "reason"], rs.at[j, "status"], rs.at[j, "reason"])
                       for i, j in pairs], columns=["live_status", "live_reason", "replay_status", "replay_reason"])
    same = (st.live_status == st.replay_status) if len(st) else pd.Series(dtype=bool)
    out["signals"]["status_agree"] = round(float(same.mean()), 3) if len(st) else None
    dis = st[~same] if len(st) else st
    if len(dis):
        key = dis.live_status + ": " + dis.live_reason.str.replace(r"\d+", "#", regex=True).str[:40] + "  ->  " + \
            dis.replay_status + ": " + dis.replay_reason.str.replace(r"\d+", "#", regex=True).str[:40]
        out["signals"]["status_disagreements"] = key.value_counts().head(12).to_dict()
    # ---- trades
    tp = match(lt, rt)
    out["trades"] = {"live": len(lt), "replay": len(rt), "matched": len(tp),
                     "match_rate_live": round(len(tp) / max(1, len(lt)), 3),
                     "match_rate_replay": round(len(tp) / max(1, len(rt)), 3)}
    if tp:
        a = lt.loc[[i for i, _ in tp]].reset_index(drop=True)
        b = rt.loc[[j for _, j in tp]].reset_index(drop=True)
        side = a.side.astype(float)
        e_bps = side * (b.entry - a.entry) / a.entry * 1e4
        x_bps = side * (b.exit - a.exit) / a.exit * 1e4
        dr = b.r_multiple - a.r_multiple
        out["trades"].update({
            "entry_diff_bps_median": round(float(e_bps.median()), 2), "entry_diff_bps_mean_abs": round(float(e_bps.abs().mean()), 2),
            "exit_diff_bps_median": round(float(x_bps.median()), 2), "exit_diff_bps_mean_abs": round(float(x_bps.abs().mean()), 2),
            "r_diff_mean": round(float(dr.mean()), 3), "r_diff_median": round(float(dr.median()), 3),
            "r_diff_mean_abs": round(float(dr.abs().mean()), 3),
            "same_exit_reason": round(float((a.exit_reason.str.replace("trail", "stop") ==
                                             b.exit_reason.str.replace("trail", "stop")).mean()), 3),
            "matched_live_r": round(float(a.r_multiple.sum()), 2), "matched_replay_r": round(float(b.r_multiple.sum()), 2),
            "exit_reasons": (a.exit_reason + " -> " + b.exit_reason).value_counts().head(8).to_dict()})
    # ---- per setup
    rows = []
    for n in sorted(set(lt.strategy) | set(rt.strategy)):
        x = setup_stats(lt[lt.strategy == n])
        y = setup_stats(rt[rt.strategy == n].assign(session=rt.loc[rt.strategy == n, "day"]))
        rows.append({"setup": n, "live_trades": x["trades"], "live_avg_r": x["avg_r"], "live_total_r": x["total_r"],
                     "replay_trades": y["trades"], "replay_avg_r": y["avg_r"], "replay_total_r": y["total_r"]})
    out["per_setup"] = rows
    out["system"] = {"live_total_r": round(float(lt.r_multiple.sum()), 2),
                     "replay_total_r": round(float(rt.r_multiple.sum()), 2),
                     "live_avg_r": round(float(lt.r_multiple.mean()), 3) if len(lt) else None,
                     "replay_avg_r": round(float(rt.r_multiple.mean()), 3) if len(rt) else None,
                     "live_trades": len(lt), "replay_trades": len(rt)}
    lu = lt[lt.symbol.isin(lab)]
    out["system_in_universe"] = {"live_trades": len(lu), "live_total_r": round(float(lu.r_multiple.sum()), 2),
                                 "live_avg_r": round(float(lu.r_multiple.mean()), 3) if len(lu) else None,
                                 "replay_trades": len(rt), "replay_total_r": round(float(rt.r_multiple.sum()), 2),
                                 "replay_avg_r": round(float(rt.r_multiple.mean()), 3) if len(rt) else None}
    lsu = ls[ls.symbol.isin(lab)]
    out["signals"]["live_in_universe"] = len(lsu)
    out["signals"]["live_submitted_in_universe"] = int((lsu.status == "submitted").sum())
    out["signals"]["replay_submitted"] = int((rs.status == "submitted").sum()) if len(rs) else 0
    out["sec_per_session"] = round(float(np.mean([x.get("seconds", 0) for x in stats])), 1) if stats else None
    out["fast_check"] = {k: int(sum((x.get("fast_check") or {}).get(k, 0) for x in stats))
                         for k in ("samples", "frame_diff", "mask_diff", "rvol_diff")}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--accounts", default="primary,testing,testing2")
    ap.add_argument("--out")
    a = ap.parse_args()
    res = {acct: compare(acct, Path(a.run)) for acct in a.accounts.split(",") if (Path(a.run) / acct).exists()}
    txt = json.dumps(res, indent=1, default=str)
    if a.out:
        Path(a.out).write_text(txt)
    for acct, r in res.items():
        print(f"== {acct} {r['sessions'][0] if r['sessions'] else ''}..{r['sessions'][-1] if r['sessions'] else ''}")
        print(" signals", {k: v for k, v in r["signals"].items() if not isinstance(v, dict)})
        print(" trades ", {k: v for k, v in r["trades"].items() if not isinstance(v, dict)})
        print(" system ", r["system"])
        print(" in-universe", r["system_in_universe"])
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    main()
