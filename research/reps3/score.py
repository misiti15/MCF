"""REPS3 scorer (rule fixed in NOTES.md before 11-12). Realized setup-days/week per account vs the frozen forecast.
Window: sessions >= 2026-11-12 in the journals (need >= 5). realized = 5 x #(setup, day) with >= 1 submitted signal / sessions.
Also: per setup-source (live / lab / unrated), Gen halt / buying-power skip counts per session vs REPS1b (66.3 / 60.4),
Testing A signals per session before (10-20..11-11) vs after.
    python -I score.py --selftest
    python -I score.py <journal dir> <forecast_setups.csv>        Educational only - not financial advice."""
import sys, os, glob, sqlite3, re, pandas as pd
START = "2026-11-12"
NAME = {"mcf-data": "Primary", "mcf-data-testing": "On Deck", "mcf-data-testing2": "Testing A", "mcf-data-explore1": "Testing B",
        "mcf-data-livelab": "Testing C", "mcf-data-testingd": "Testing D", "mcf-data-testinge": "Testing E",
        "mcf-data-testingf": "Testing F", "mcf-data-gen": "Gen", "mcf-data-graveyard": "Graveyard"}
def load(J):
    out = []
    for p in sorted(glob.glob(f"{J}/mcf-data*.db")):
        b = os.path.basename(p)[:-3]
        if os.path.getsize(p) == 0 or b not in NAME: continue
        c = sqlite3.connect(p); pid = ",".join(str(r[0]) for r in c.execute("select id from runs where kind='paper'"))
        if not pid: continue
        s = pd.read_sql(f"select day, strategy, status, reason from signals where run_id in ({pid}) and day >= '2026-10-20'", c)
        s["account"] = NAME[b]; out.append(s)
    return pd.concat(out, ignore_index=True)
def realized(S):
    a = S[S.day >= START]; n = a.day.nunique()
    sd = a[a.status == "submitted"].groupby(["account", "strategy"]).day.nunique()
    return n, sd
def selftest():
    S = pd.DataFrame(dict(day=["2026-11-12", "2026-11-12", "2026-11-13", "2026-11-11"], strategy=["x", "x", "y", "x"],
                          status=["submitted", "submitted", "skipped", "submitted"], reason=[None, None, "halted", None], account=["Gen"] * 4))
    n, sd = realized(S); assert n == 2 and sd.to_dict() == {("Gen", "x"): 1}, (n, sd)
    print("selftest ok")
def main(J, FC):
    S = load(J); F = pd.read_csv(FC); n, sd = realized(S)
    print(f"sessions since {START}: {n}{'  (< 5: provisional, do not read)' if n < 5 else ''}")
    real = (5 * sd.groupby(level=0).sum() / n).rename("realized_wk")
    fc = (5 * F.groupby("account").p_day.sum()).rename("forecast_wk")
    T = pd.concat([fc, real], axis=1).fillna(0); T["diff"] = T.realized_wk - T.forecast_wk
    print(T.round(1).to_string()); print(f"TOTAL forecast {T.forecast_wk.sum():.1f} realized {T.realized_wk.sum():.1f}")
    F = F.set_index(["account", "setup"]); r = (5 * sd / n).rename("real")
    J2 = F.join(r.rename_axis(["account", "setup"]), how="left").fillna({"real": 0})
    print("\nby forecast source (setups, forecast/week, realized/week):")
    for src, g in J2.groupby("src"): print(f"   {src:8s} {len(g):3d}  {5 * g.p_day.sum():7.1f}  {g.real.sum():7.1f}")
    a = S[S.day >= START]; g = a[a.account == "Gen"]
    for lab, rx in (("account halt", r"^halted"), ("buying power", r"buying_power|insufficient buying power")):
        print(f"Gen {lab} skips/session: {g.reason.fillna('').str.contains(rx, regex=True).sum() / max(n, 1):.1f} (REPS1b 10-20..11-10: "
              f"{'66.3' if lab == 'account halt' else '60.4'})")
    ta = S[S.account == "Testing A"]
    print(f"Testing A signals/session: before {len(ta[ta.day < START]) / max(1, ta[ta.day < START].day.nunique()):.1f}, "
          f"after {len(ta[ta.day >= START]) / max(1, n):.1f} (full universe from 11-12)")
    print("Rule-change context: owner restructure c64d75df0 effective 11-12 (9 ledger entries 2026-11-12-*). Educational only - not financial advice.")
if __name__ == "__main__":
    selftest() if sys.argv[1] == "--selftest" else main(sys.argv[1], sys.argv[2])
