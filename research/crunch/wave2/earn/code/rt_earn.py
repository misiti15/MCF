"""RT-EARN (Wave 2 item 2): one pre-registered config EARN-GO-2Y (see ../PLAN.md) on the round-4 ULT-28 chassis.
Reuses research/ultimate_1119/round4/ULT-28/bt.py (signals, events, costs, 1-minute walk) with two changes fixed in
PLAN.md: time exit 60 min (TX-60, 2u = 0.5 dATR catastrophic stop, R per 2u) and one entry per symbol-session.
    python -I rt_earn.py WORK sig|walk|score
Locked block 2024-11-01..2025-02-28 never read. Educational only - not financial advice."""
import importlib.util, inspect, json, sys, time
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
BT = REPO / "research/ultimate_1119/round4/ULT-28/bt.py"
sys.path.insert(0, str(REPO))
_s = importlib.util.spec_from_file_location("ult28bt", BT)
B = importlib.util.module_from_spec(_s); sys.modules["ult28bt"] = B; _s.loader.exec_module(B)
B.EARN = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ult/research/ultimate_1119/round4/data/earnings_yf.parquet")
assert B.sha(B.EARN).startswith("b80cdc46")
B.EXITS = {"X": (None, 2.0)}
src = inspect.getsource(B.walk_job).replace("m2(hm[j0]) + 44)", "m2(hm[j0]) + 59)")
assert "+ 59)" in src
exec(compile(src, str(BT), "exec"), B.__dict__)          # TX-60: time exit at 60 minutes
KEY = "25X"
SEASONS = [("Oct-24", "2024-10-01", "2024-10-31"), ("Apr-May-25", "2025-04-01", "2025-05-31"),
           ("Jul-Aug-25", "2025-07-01", "2025-08-31"), ("Oct-Nov-25", "2025-10-01", "2025-11-30"),
           ("Jan-Feb-26", "2026-01-15", "2026-02-28"), ("Apr-May-26", "2026-04-01", "2026-05-31"),
           ("Jul-Aug-26", "2026-07-01", "2026-08-31"), ("Oct-Nov-26", "2026-10-01", "2026-11-04")]


def select(S, evt=1, cap=30):
    S = B.bind(S, KEY)
    m = (S.evt == evt) & (S.tod >= 950) & (S.tod <= 1230) & (S.side * S.gap >= 3.0) & S.r.notna()
    s = S[m].sort_values(["symbol", "date", "tod"], kind="mergesort").groupby(["symbol", "date"]).head(1)
    s = s.sort_values(["date", "tod", "adv20"], ascending=[True, True, False], kind="mergesort")
    return s.groupby("date", sort=False).head(cap) if cap else s


def st(t, n):
    if not len(t):
        return {"n": 0}
    day = t.groupby("date").r.sum(); tot = float(t.r.sum()); avg = float(t.r.mean()); best = day.idxmax()
    dev = (t.r - avg).groupby(t.date).sum(); se = float(np.sqrt((dev ** 2).sum())) / len(t)
    return {"n": int(len(t)), "per_session": round(len(t) / n, 3) if n else None, "sessions_traded": int(day.size),
            "win": round(float((t.r > 0).mean()), 3), "avg_r": round(avg, 4),
            "avg_r_wo_best_day": round(float(t.r[t.date != best].mean()), 4) if (t.date != best).any() else None,
            "best_day": str(best), "best_day_r": round(float(day.max()), 2),
            "best_day_share": round(float(day.max()) / tot, 3) if tot > 0 else None, "total_r": round(tot, 2),
            "worst_day_r": round(float(day.min()), 2), "t_day": round(avg / se, 2) if se > 0 else None}


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True); stage = sys.argv[2]
    if stage == "sig":
        for half in ("fit", "check"):
            sigs, days, nev = [], [], {}
            with Pool(2) as p:
                for mth, s, d, ne, ni in p.imap_unordered(B.month_job, B.half_months(half)):
                    print(half, mth, len(s), flush=True); sigs.append(s); days += d; nev.update({k: int(v) for k, v in ne.items()})
            S = pd.concat(sigs, ignore_index=True); S["date"] = S.date.astype(str)
            B.no_locked(S.date.unique()); B.no_locked(days)
            S.to_parquet(W / f"sig_{half}.parquet"); pd.DataFrame({"date": sorted(days)}).to_parquet(W / f"days_{half}.parquet")
    elif stage == "walk":
        for half in ("fit", "check"):
            S = pd.read_parquet(W / f"sig_{half}.parquet")
            S = S[S.evt == 1].groupby(["symbol", "date"]).head(1) if False else S   # walk the full superset (twin too)
            T = B.walk(S); T.to_parquet(W / f"walked_{half}.parquet"); print("walked", half, len(T), flush=True)
    elif stage == "score":
        out = {"config": "EARN-GO-2Y (PLAN.md)", "configs_counted": 1, "scored_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "plan_sha256": B.sha(HERE.parent / "PLAN.md")}
        tt, nn, tw = [], 0, []
        for half in ("fit", "check"):
            S = pd.read_parquet(W / f"walked_{half}.parquet"); B.no_locked(S.date.unique())
            n = len(pd.read_parquet(W / f"days_{half}.parquet")); nn += n
            t = select(S); tt.append(t); tw.append(select(S, evt=0))
            out["E" if half == "fit" else "L"] = st(t, n)
        t = pd.concat(tt); tw = pd.concat(tw)
        out["pooled"] = st(t, nn); out["sessions"] = nn
        out["by_side"] = {k: st(t[t.side == g], nn) for k, g in (("long", 1), ("short", -1))}
        out["by_half_side"] = {f"{h}_{k}": st(x[x.side == g], 0) for h, x in (("E", tt[0]), ("L", tt[1])) for k, g in (("long", 1), ("short", -1))}
        out["by_season"] = {nm: st(t[t.date.between(a, b)], 0) for nm, a, b in SEASONS}
        ins = np.zeros(len(t), bool)
        for _, a, b in SEASONS:
            ins |= t.date.between(a, b).to_numpy()
        out["off_season"] = st(t[~ins], 0)
        ag = t.side * t.gap
        out["by_gap"] = {k: st(t[m], 0) for k, m in (("3-5", ag < 5), ("5-10", (ag >= 5) & (ag < 10)), ("10+", ag >= 10))}
        out["by_entry"] = {k: st(t[m], 0) for k, m in (("0950-1025", t.tod < 1030), ("1030-1125", (t.tod >= 1030) & (t.tod < 1130)), ("1130-1230", t.tod >= 1130))}
        out["by_surprise"] = {k: st(t[m], 0) for k, m in (("agree", np.sign(t.e_surp) == t.side), ("disagree", np.sign(t.e_surp) == -t.side), ("missing", t.e_surp.isna() | (t.e_surp == 0)))}
        out["exit_mix"] = {str(k): int(v) for k, v in t.kd.map({0: "time", 1: "stop", 2: "target"}).value_counts().items()}
        out["median_hold_min"] = float(np.nanmedian(t.hold))
        out["bias_diag_sigclose_nofixes_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        out["twin_nonearnings"] = st(tw, nn)
        Rc = B.random_control(t, {"key": KEY}); ok = Rc.r.notna().to_numpy() & t.r.notna().to_numpy()
        out["random_same_name"] = {"avg_r": round(float(Rc.r.to_numpy()[ok].mean()), 4),
                                   "signal_minus_random": round(float(t.r.to_numpy()[ok].mean() - Rc.r.to_numpy()[ok].mean()), 4), "n": int(ok.sum())}
        p, E, L = out["pooled"], out["E"], out["L"]
        bars = {"1_avg_r_gt0": p["avg_r"] > 0, "2_wo_best_gt0_share_lt50": (p["avg_r_wo_best_day"] or -1) > 0 and (p["best_day_share"] or 9) < 0.5,
                "3_both_halves_gt0": E["avg_r"] > 0 and L["avg_r"] > 0, "4_t_ge_2": (p["t_day"] or 0) >= 2.0}
        out["bars"] = bars
        out["verdict"] = "PASS" if all(bars.values()) else ("PARTIAL" if all(list(bars.values())[:3]) else "FAIL")
        t[["symbol", "date", "tod", "side", "gap", "e_surp", "r", "kd", "hold"]].to_csv(HERE.parent / "trades.csv.gz", index=False)
        (HERE.parent / "scores.json").write_text(json.dumps(out, indent=1, default=float)); print(json.dumps(out, indent=1, default=float))
