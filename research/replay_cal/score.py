"""Score a session replay against the live paper journals with the pre-registered targets (research/replay_cal/TARGETS.md).

    python research/replay_cal/score.py --run DIR --dates 2026-11-02..2026-11-16 --accounts primary,testing,testing2 \
        --live-dir DIR_WITH_JOURNALS --out research/replay_cal/heldout [--tag heldout]

Live trade = a filled live entry (trades run 1, one per broker order id); match = same setup + symbol + side + decision
bar (from the client order id; exact minute, +-1 reported too). Also scores the rule-21 audit (R21 below: decision-bar
match >= 95%, avg R gap within +-0.03R and never optimistic, fresh sessions after the replay's fit date only). R per trade = LR8 live cost model on each side's own
fills (mcf.costs.lot_costs, every day). Writes scorecard.json, per_account.csv, per_setup.csv, daily.csv.
Educational only - not financial advice."""

from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf import costs as C  # noqa: E402
from mcf.replay import store  # noqa: E402

COID = re.compile(r'"coid": "[^"]*-(\d{8})-(\d{4})')
BRANCH_DB = {"primary": "mcf-data", "testing": "mcf-data-testing", "testing2": "mcf-data-testing2"}
MODEL = yaml.safe_load((ROOT / "config" / "default.yaml").read_text())["costs"]["live_model"]
T = {"match": 0.98, "extra": 0.02, "bias": 0.01, "z": 1.645, "corr": 0.95, "sign": 0.90, "skip": 0.95}
# Rule 21 audit (docs/RESEARCH_RULES.md 21; owner "RULE21-DB yes", 2026-11-17): live trades are matched on the live
# signal's DECISION bar (client order id HHMM = info.bar_time), never the broker fill minute (fills land +1/+2 min later,
# research/guild/1112/obs-fillclock/NOTES.md). Guards: >= 95% match; avg R gap (replay - live) within +-0.03R on matched
# pairs AND on all trades; never optimistic (matched-pair gap - 1.645 SE <= 0); fresh sessions only (after the replay's
# fit date, so no session that tuned the replay is scored).
R21 = {"match": 0.95, "gap": 0.03, "z": 1.645}
PARAMS = ROOT / "research" / "replay_cal" / "params_v2.json"


def _min_coid(meta) -> int | None:
    m = COID.search(str(meta or ""))
    return None if not m else int(m.group(2)[:2]) * 60 + int(m.group(2)[2:])


def _min_info(info, ts) -> int | None:
    try:
        bt = json.loads(info or "{}").get("bar_time")
    except (ValueError, AttributeError):
        bt = None
    if bt and re.fullmatch(r"\d{4}", str(bt)):
        return int(bt[:2]) * 60 + int(bt[2:])
    try:
        t = pd.Timestamp(ts).tz_convert("America/New_York")
        return t.hour * 60 + t.minute - 1
    except (TypeError, ValueError):
        return None


def lots(tr: pd.DataFrame) -> pd.DataFrame:
    """One row per entry lot: setup, symbol, side, day, minute, R after LR8 costs on its own fills."""
    if tr is None or not len(tr):
        return pd.DataFrame(columns=["setup", "symbol", "side", "day", "min", "r"])
    rows = []
    key = tr["date"].astype(str).str[:10] + "|" + tr["broker_order_id"].astype(str)   # replay ids repeat across sessions
    for oid, g in tr.groupby(key):
        f = g.iloc[0]
        e, s = float(f["entry"]), float(f["stop"])
        q = float(pd.to_numeric(g["shares"], errors="coerce").abs().sum())
        risk = abs(e - s) * q
        day = str(f.get("date") or str(f["entry_time"])[:10])[:10]
        side = int(f["side"])
        parts = [p for _, row in g.iterrows() for p in C.parts_from_row(row)]
        pnl = float(pd.to_numeric(g["pnl"], errors="coerce").sum())
        cost = C.lot_costs(side, e, q, parts, f.get("target"), day, MODEL)["total"]
        mn = _min_coid(f.get("meta"))
        rows.append(dict(setup=str(f["strategy"]), symbol=str(f["symbol"]), side=side, day=day,
                         min=mn, r=(pnl - cost) / risk if risk > 0 else np.nan, oid=oid))
    return pd.DataFrame(rows)


def match(a: pd.DataFrame, b: pd.DataFrame, tol: int = 0) -> list[tuple[int, int]]:
    """Greedy one-to-one on (day, setup, symbol, side), decision minute within tol (closest first)."""
    idx: dict = {}
    for j, y in enumerate(b.itertuples()):
        idx.setdefault((y.day, y.setup, y.symbol, y.side), []).append((j, y.min))
    used, out = set(), []
    for i, x in enumerate(a.itertuples()):
        best = None
        for j, m in idx.get((x.day, x.setup, x.symbol, x.side), []):
            if j in used or m is None or x.min is None or pd.isna(m) or pd.isna(x.min):
                continue
            d = abs(int(x.min) - int(m))
            if d <= tol and (best is None or d < best[0]):
                best = (d, j)
        if best is not None:
            used.add(best[1])
            out.append((i, best[1]))
    return out


def fresh_days(days: list[str], fit_until: str | None) -> list[str]:
    """Rule 21 'fresh sessions only': sessions strictly after the replay's fit date (none dropped if no fit date)."""
    return [d for d in days if not fit_until or str(d) > str(fit_until)]


def rule21(s: dict, fit_until: str | None) -> dict:
    """Rule 21 audit verdict for one account (or pooled) summary scored on decision-bar matches."""
    gap_all = s["replay_avg_r"] - s["live_avg_r"]
    days = s.get("days") or []
    v = dict(match=s["match"], gap_matched=s["bias"], gap_all=gap_all, fit_until=fit_until,
             fresh=bool(days) and all(str(d) > str(fit_until) for d in days) if fit_until else bool(days))
    ok = lambda x: x is not None and not math.isnan(x)  # noqa: E731
    v["match_ok"] = s["match"] >= R21["match"]
    v["gap_ok"] = ok(s["bias"]) and ok(gap_all) and abs(s["bias"]) <= R21["gap"] and abs(gap_all) <= R21["gap"]
    v["no_optimism"] = ok(s["bias"]) and ok(s["bias_se"]) and s["bias"] - R21["z"] * s["bias_se"] <= 0 and gap_all <= R21["gap"]
    v["pass"] = bool(v["match_ok"] and v["gap_ok"] and v["no_optimism"] and v["fresh"])
    return v


def reason_cat(status, reason) -> str:
    r = re.sub(r"[-+]?\d+(\.\d+)?", "#", str(reason or ""))
    return f"{status}:{r.split(':')[0].strip()}"


def clustered(d: pd.DataFrame) -> tuple[float, float, int]:
    """Mean of d.x and its session-clustered SE."""
    n = len(d)
    if n == 0:
        return float("nan"), float("nan"), 0
    m = float(d["x"].mean())
    g = d.groupby("day")["x"].apply(lambda v: float((v - m).sum()))
    k = len(g)
    se = math.sqrt(k / max(1, k - 1) * float((g ** 2).sum())) / n if k > 1 else float("nan")
    return m, se, n


def load_live(db: Path, days: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    con = sqlite3.connect(str(db))
    sig = pd.read_sql("SELECT * FROM signals WHERE run_id=1", con)
    tr = pd.read_sql("SELECT * FROM trades WHERE run_id=1", con)
    con.close()
    sig = sig[sig["day"].astype(str).isin(days)]
    tr = tr[tr["date"].astype(str).str[:10].isin(days) & tr["broker_order_id"].notna()]
    return sig, tr


def load_run(run: Path, acct: str, days: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    sig, tr, have = [], [], []
    for d in days:
        p = run / acct / d
        if not (p / "stats.json").exists() or not (p / "signals.csv.gz").exists():
            continue
        have.append(d)
        s = pd.read_csv(p / "signals.csv.gz")
        s["day"] = d
        sig.append(s)
        t = pd.read_csv(p / "trades.csv.gz")
        if len(t):
            t["date"] = d
            tr.append(t[t["broker_order_id"].notna()])
    cat = lambda x: pd.concat(x, ignore_index=True) if x else pd.DataFrame()  # noqa: E731
    return cat(sig), cat(tr), have


def sig_rows(sig: pd.DataFrame) -> pd.DataFrame:
    if not len(sig):
        return pd.DataFrame(columns=["day", "setup", "symbol", "side", "min", "cat"])
    return pd.DataFrame(dict(day=sig["day"].astype(str).values, setup=sig["strategy"].astype(str).values,
                             symbol=sig["symbol"].astype(str).values, side=sig["side"].astype(int).values,
                             min=[_min_info(i, t) for i, t in zip(sig["info"], sig["ts"])],
                             cat=[reason_cat(s, r) for s, r in zip(sig["status"], sig["reason"])]))


def score_account(acct: str, run: Path, live_db: Path, days: list[str]) -> dict:
    rs, rt, have = load_run(run, acct, days)
    ls, lt = load_live(live_db, have)
    L, R = lots(lt), lots(rt)
    pairs = match(L, R, 0)
    pairs1 = match(L, R, 1)
    mi = {i for i, _ in pairs}
    mj = {j for _, j in pairs}
    pr = pd.DataFrame([dict(day=L.iloc[i]["day"], setup=L.iloc[i]["setup"], x=R.iloc[j]["r"] - L.iloc[i]["r"],
                            lr=L.iloc[i]["r"], rr=R.iloc[j]["r"]) for i, j in pairs])
    pr = pr.dropna(subset=["x"]) if len(pr) else pr
    m, se, n = clustered(pr) if len(pr) else (float("nan"), float("nan"), 0)
    # skip reasons (all live signals)
    LS, RS = sig_rows(ls), sig_rows(rs)
    sp = match(LS.rename(columns={}), RS, 0)
    same = sum(1 for i, j in sp if LS.iloc[i]["cat"] == RS.iloc[j]["cat"])
    mism: dict = {}
    for i, j in sp:
        a, b = LS.iloc[i]["cat"], RS.iloc[j]["cat"]
        if a != b:
            mism[f"{a} -> {b}"] = mism.get(f"{a} -> {b}", 0) + 1
    # daily
    dl = L.groupby("day")["r"].sum().reindex(have, fill_value=0.0)
    dr = R.groupby("day")["r"].sum().reindex(have, fill_value=0.0)
    daily = pd.DataFrame({"account": acct, "day": have, "live_r": dl.values, "replay_r": dr.values,
                          "live_n": L.groupby("day").size().reindex(have, fill_value=0).values,
                          "replay_n": R.groupby("day").size().reindex(have, fill_value=0).values})
    corr = float(np.corrcoef(dl.values, dr.values)[0, 1]) if len(have) > 2 and dl.std() > 0 and dr.std() > 0 else float("nan")
    sign = float((np.sign(dl.values) == np.sign(dr.values)).mean()) if len(have) else float("nan")
    wl = dl.idxmin() if len(have) else None
    wr = dr.idxmin() if len(have) else None
    worst_ok = bool(wl == wr and abs(dr[wl] - dl[wl]) <= max(0.10 * abs(dl[wl]), 2.0)) if wl else False
    # per setup
    L["m"] = [i in mi for i in range(len(L))]
    R["m"] = [j in mj for j in range(len(R))]
    ps = []
    for s in sorted(set(L["setup"]) | set(R["setup"])):
        a, b = L[L.setup == s], R[R.setup == s]
        p = pr[pr.setup == s] if len(pr) else pr
        ps.append(dict(account=acct, setup=s, live_trades=len(a), replay_trades=len(b), matched=int(a["m"].sum()),
                       match=a["m"].mean() if len(a) else np.nan,
                       extra=(len(b) - int(b["m"].sum())) / len(a) if len(a) else np.nan,
                       live_avg_r=a["r"].mean() if len(a) else np.nan, replay_avg_r=b["r"].mean() if len(b) else np.nan,
                       bias=p["x"].mean() if len(p) else np.nan, live_total_r=a["r"].sum(), replay_total_r=b["r"].sum()))
    res = dict(account=acct, sessions=len(have), days=list(have), live_trades=len(L), replay_trades=len(R), matched=len(pairs),
               matched_pm1=len(pairs1), match=len(pairs) / max(1, len(L)), match_pm1=len(pairs1) / max(1, len(L)),
               extra=(len(R) - len(mj)) / max(1, len(L)), bias=m, bias_se=se, bias_n=n,
               bias_lo=m - 1.96 * se, bias_hi=m + 1.96 * se, live_r=float(L["r"].sum()), replay_r=float(R["r"].sum()),
               live_avg_r=float(L["r"].mean()) if len(L) else float("nan"),
               replay_avg_r=float(R["r"].mean()) if len(R) else float("nan"), daily_corr=corr, sign_agree=sign, skip_match=same / max(1, len(LS)), live_signals=len(LS),
               worst_day_live=wl, worst_day_replay=wr, worst_ok=worst_ok,
               top_mismatch=dict(sorted(mism.items(), key=lambda kv: -kv[1])[:12]))
    return dict(summary=res, pairs=pr, daily=daily, setups=pd.DataFrame(ps))


def verdict(s: dict) -> dict:
    no_opt = (s["bias"] - T["z"] * s["bias_se"]) <= 0 if not math.isnan(s["bias_se"]) else False
    v = dict(T1_match=s["match"] >= T["match"], T2_extra=s["extra"] <= T["extra"],
             T3_bias=abs(s["bias"]) <= T["bias"] and no_opt, T3_no_optimism=no_opt,
             T4_daily=(s["daily_corr"] >= T["corr"]) and (s["sign_agree"] >= T["sign"]),
             T5_skip=s["skip_match"] >= T["skip"], T6_worst=bool(s.get("worst_ok")))
    v["all"] = all(v[k] for k in ("T1_match", "T2_extra", "T3_bias", "T4_daily", "T5_skip", "T6_worst"))
    return v


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True)
    p.add_argument("--dates", required=True)
    p.add_argument("--accounts", default="primary,testing,testing2")
    p.add_argument("--live-dir", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--fit-until", default=None, help="replay fit date (default: params_v2.json fit_until); rule 21 "
                   "scores only sessions after it")
    a = p.parse_args(argv)
    lo, hi = a.dates.split("..")
    fit = a.fit_until or (json.loads(PARAMS.read_text()).get("fit_until") if PARAMS.exists() else None)
    all_days = [str(d) for d in store.sessions(lo, hi)]
    days = fresh_days(all_days, fit)
    if len(days) < len(all_days):
        print(f"rule 21: fresh sessions only - dropped {len(all_days) - len(days)} session(s) on or before {fit}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    allp, alld, alls, summ = [], [], [], []
    for acct in a.accounts.split(","):
        r = score_account(acct, Path(a.run), Path(a.live_dir) / f"{BRANCH_DB[acct]}.db", days)
        s = r["summary"]
        s["verdict"] = verdict(s)
        s["rule21"] = rule21(s, fit)
        summ.append(s)
        allp.append(r["pairs"].assign(account=acct))
        alld.append(r["daily"])
        alls.append(r["setups"])
    P, D = pd.concat(allp, ignore_index=True), pd.concat(alld, ignore_index=True)
    P["day"] = P["account"] + ":" + P["day"]                     # cluster = account-session
    m, se, n = clustered(P)
    LT, RT = sum(s["live_trades"] for s in summ), sum(s["replay_trades"] for s in summ)
    MT = sum(s["matched"] for s in summ)
    LR = sum(s["live_r"] for s in summ)
    RR = sum(s["replay_r"] for s in summ)
    pooled = dict(account="pooled", sessions=int(D["day"].nunique()), days=sorted(set(D["day"])), live_trades=LT, replay_trades=RT, matched=MT,
                  matched_pm1=sum(s["matched_pm1"] for s in summ), match=MT / max(1, LT),
                  match_pm1=sum(s["matched_pm1"] for s in summ) / max(1, LT), extra=(RT - MT) / max(1, LT),
                  bias=m, bias_se=se, bias_n=n, bias_lo=m - 1.96 * se, bias_hi=m + 1.96 * se,
                  live_r=float(D["live_r"].sum()), replay_r=float(D["replay_r"].sum()),
                  live_avg_r=LR / LT if LT else float("nan"), replay_avg_r=RR / RT if RT else float("nan"),
                  daily_corr=float(np.corrcoef(D["live_r"], D["replay_r"])[0, 1]),
                  sign_agree=float((np.sign(D["live_r"]) == np.sign(D["replay_r"])).mean()),
                  skip_match=sum(s["skip_match"] * s["live_signals"] for s in summ) / max(1, sum(s["live_signals"] for s in summ)),
                  live_signals=sum(s["live_signals"] for s in summ), worst_ok=all(s["worst_ok"] for s in summ))
    pooled["verdict"] = verdict(pooled)
    pooled["rule21"] = rule21(pooled, fit)
    r21 = dict(targets=R21, fit_until=fit, matched_on="decision bar", per_account={s["account"]: s["rule21"]["pass"]
               for s in summ}, pooled=pooled["rule21"]["pass"])
    r21["pass"] = bool(r21["pooled"] and all(r21["per_account"].values()))
    card = dict(run=a.run, dates=a.dates, targets=T, rule21=r21, pooled=pooled, accounts=summ,
                note="Educational only - not financial advice.")
    (out / "scorecard.json").write_text(json.dumps(card, indent=1, default=str))
    pd.DataFrame([{k: v for k, v in s.items() if k not in ("top_mismatch", "verdict", "rule21", "days")} for s in summ + [pooled]]) \
        .to_csv(out / "per_account.csv", index=False, float_format="%.4f")
    pd.concat(alls, ignore_index=True).to_csv(out / "per_setup.csv", index=False, float_format="%.4f")
    D.to_csv(out / "daily.csv", index=False, float_format="%.3f")
    for s in summ + [pooled]:
        print(f"{s['account']:9s} n_live={s['live_trades']} n_rep={s['replay_trades']} match={s['match']:.3f} "
              f"(+-1 {s['match_pm1']:.3f}) extra={s['extra']:.3f} bias={s['bias']:+.4f} [{s['bias_lo']:+.4f},"
              f"{s['bias_hi']:+.4f}] corr={s['daily_corr']:.3f} sign={s['sign_agree']:.2f} skip={s['skip_match']:.3f} "
              f"worst={s['worst_ok']} ALL={s['verdict']['all']} rule21={s['rule21']['pass']}")
    print(f"rule 21 (decision bar, fresh sessions after {fit}): {'PASS' if r21['pass'] else 'FAIL'}")
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    main()
