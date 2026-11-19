"""C: spotlight ranking input (Lead 11-18 19:00; shortlist FINAL.md #3). Descriptive, 0 configs, an input to the owner's
spotlight rotation only. Live reps ONLY (SRCV1): live setup-days per week of ELIGIBLE sessions = traded_days / active_days x 5,
from MCF docs/live/arena_reps.json (active days come from each session's setup snapshot, so benched / away / family-capped
sessions are already excluded - the REPS3 eligibility, done at the source). 2-year backtest quality is shown BESIDE it and is
never blended into the rank (guild research/momside/data/trades_full.parquet, 1,226 lab symbols, locked block absent).
    python spotc.py [--n 15]          Educational only - not financial advice."""
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd
MCF = Path("/home/user/MCF"); HERE = Path(__file__).parent
ARENA = ["testing2", "explore1", "livelab", "gen", "testingd", "testinge", "testingf"]   # Testing A-F + Setup Generator (owner 11-12)
LBL = {"testing2": "Testing A", "explore1": "Testing B", "livelab": "Testing C", "gen": "Generator", "testingd": "Testing D",
       "testinge": "Testing E", "testingf": "Testing F"}


def rank(reps: dict, home: dict, n: int, min_active: int = 0) -> pd.DataFrame:
    rows = []
    for s, acc in home.items():
        r = reps.get(s)
        if not r or not r.get("active_days"):
            rows.append(dict(setup=s, account=LBL[acc], active_days=0, traded_days=0, trades=0, shadow_days=(r or {}).get("shadow_days", 0),
                             live_days_per_wk=np.nan, triage=",".join((r or {}).get("triage", [])), note="no active day yet"))
            continue
        rows.append(dict(setup=s, account=LBL[acc], active_days=r["active_days"], traded_days=r["traded_days"], trades=r["trades"],
                         shadow_days=r.get("shadow_days", 0), live_days_per_wk=5 * r["traded_days"] / r["active_days"],
                         triage=",".join(r.get("triage", [])), note=""))
    D = pd.DataFrame(rows); D = D[D.active_days >= min_active]
    return D.sort_values(["live_days_per_wk", "active_days"], ascending=[True, False], na_position="first").head(n).reset_index(drop=True)


def bt2y(setups) -> pd.DataFrame:
    T = pd.read_parquet(HERE.parent / "momside" / "data" / "trades_full.parquet", columns=["setup", "date", "r"])
    d = pd.to_datetime(T.date)
    assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any(), "locked block rows present (#43)"
    T = T[T.setup.isin(set(setups))]
    out = []
    for s, g in T.groupby("setup"):
        day = g.groupby("date").r.sum(); b = day.idxmax()
        out.append(dict(setup=s, bt_trades=len(g), bt_days=len(day), bt_avg_r=g.r.mean(),
                        bt_avg_r_wo_best_day=g[g.date != b].r.mean(), bt_days_per_wk=5 * len(day) / d.dt.date.nunique()))
    return pd.DataFrame(out, columns=["setup", "bt_trades", "bt_days", "bt_avg_r", "bt_avg_r_wo_best_day", "bt_days_per_wk"])


def selftest():
    reps = {"a": dict(active_days=10, traded_days=1, trades=1), "b": dict(active_days=10, traded_days=8, trades=20),
            "c": dict(active_days=20, traded_days=2, trades=2), "d": dict(active_days=0, traded_days=0, trades=0)}
    R = rank(reps, {"a": "gen", "b": "gen", "c": "testinge", "d": "testingd"}, 3)
    assert list(R.setup) == ["d", "c", "a"], R          # never-active first; tie at 0.5/wk -> more active days first
    assert abs(R.loc[1, "live_days_per_wk"] - 0.5) < 1e-9
    R5 = rank(reps, {"a": "gen", "b": "gen", "c": "testinge", "d": "testingd"}, 3, 5)
    assert list(R5.setup) == ["c", "a", "b"], R5        # min_active drops the never-active one
    print("selftest ok: rate = 5 x traded/active, never-active first, tie -> more active days")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=15); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    rep = json.loads((MCF / "docs/live/arena_reps.json").read_text()); asg = json.loads((MCF / "docs/live/assignments.json").read_text())
    home = {s: k for k in ARENA for s in asg["accounts"].get(k, [])}
    MIN = 5   # a rate needs a few eligible sessions; newer setups are listed apart, not ranked
    allr = rank(rep["setups"], home, len(home))
    new = allr[allr.active_days < MIN].sort_values("active_days")
    R = rank(rep["setups"], home, a.n, MIN)
    B = bt2y(R.setup); R = R.merge(B, on="setup", how="left")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 46)
    print(f"C spotlight input: {len(home)} arena setups (assignments as of {asg.get('asof_session')}); reps until {rep['until']}; "
          f"{a.n} least-traded by LIVE setup-days per eligible week (rank uses live only, SRCV1)")
    cols = ["setup", "account", "active_days", "traded_days", "trades", "live_days_per_wk", "shadow_days", "triage", "note"]
    print(R[cols].round(2).to_string(index=False))
    print("\n2-year backtest quality BESIDE the rank (never blended; screening only; 1,226 lab symbols, survivorship; NaN = no record):")
    print(R[["setup", "bt_trades", "bt_days", "bt_days_per_wk", "bt_avg_r", "bt_avg_r_wo_best_day"]].round(3).to_string(index=False))
    print(f"\nToo new to rate (< {MIN} active days; listed, not ranked): {len(new)}")
    print(new[["setup", "account", "active_days", "traded_days", "trades"]].to_string(index=False))
    print(f"\n2-year backtest coverage: {R.bt_trades.notna().sum()} of {len(R)} ranked setups have a record in the guild file "
          f"(it holds 40 of the {len(home)} arena setups; index / breadth / Workbench / GEN setups are not in it).")
    R.to_csv(HERE / "spotc_out.csv", index=False)
    print("Descriptive input to the owner's spotlight rotation; 0 configs; no verdicts (< 15 active days AND 30 trades, C3-ROT). "
          "Educational only - not financial advice.")


if __name__ == "__main__":
    main()
