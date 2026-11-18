"""REPS3 scorer (rule fixed in NOTES.md before 11-12). Realized setup-days/week per account vs the frozen forecast.
Window: sessions >= 2026-11-12 in the journals (need >= 5). realized = 5 x #(setup, day) with >= 1 submitted signal / sessions.
Also: per setup-source (live / lab / unrated), Gen halt / buying-power skip counts per session vs REPS1b (66.3 / 60.4),
Testing A signals per session before (10-20..11-11) vs after.
    python -I score.py --selftest
    python -I score.py <journal dir> <forecast_setups.csv> [--end YYYY-MM-DD]     (--end = the session refresh.py checked)
Educational only - not financial advice."""
import sys, os, glob, sqlite3, re, pandas as pd
START = "2026-11-12"; END = "9999-12-31"
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
    a = S[(S.day >= START) & (S.day <= END)]; n = a.day.nunique()
    sd = a[a.status == "submitted"].groupby(["account", "strategy"]).day.nunique()
    return n, sd
def selftest():
    S = pd.DataFrame(dict(day=["2026-11-12", "2026-11-12", "2026-11-13", "2026-11-11"], strategy=["x", "x", "y", "x"],
                          status=["submitted", "submitted", "skipped", "submitted"], reason=[None, None, "halted", None], account=["Gen"] * 4))
    n, sd = realized(S); assert n == 2 and sd.to_dict() == {("Gen", "x"): 1}, (n, sd)
    global END; END = "2026-11-12"; n, sd = realized(S); assert n == 1, n; END = "9999-12-31"   # --end excludes later sessions
    S2 = pd.DataFrame(dict(day=["2026-11-12", "2026-11-13", "2026-11-17", "2026-11-17", "2026-11-17"], strategy=["x", "x", "x-WB1", "x", "y"],
                           status=["submitted"] * 5, reason=[None] * 5, account=["Gen", "Testing A", "Testing B", "Testing A", "Testing F"]))
    F2 = pd.DataFrame(dict(account=["Gen", "On Deck"], setup=["x", "y"], p_day=[0.5, 0.0], src=["live", "live"]))
    import io, contextlib; buf = io.StringIO()
    with contextlib.redirect_stdout(buf): report_fixes(S2, F2, 3)
    o = buf.getvalue()
    assert "realized 6.7/wk (2 of 2" in o and "1 setups, realized 1.7/wk" in o, o
    assert "outside their forecast account: 1" in o and "On Deck, Testing F" in o and "y: forecast On Deck -> realized in Testing F" in o, o
    assert "11-12..11-16 (pre-TSZ1): 2 sessions" in o and "11-17..end" in o, o
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
    a = S[(S.day >= START) & (S.day <= END)]; g = a[a.account == "Gen"]
    for lab, rx in (("account halt", r"^halted"), ("buying power", r"buying_power|insufficient buying power")):
        print(f"Gen {lab} skips/session: {g.reason.fillna('').str.contains(rx, regex=True).sum() / max(n, 1):.1f} (REPS1b 10-20..11-10: "
              f"{'66.3' if lab == 'account halt' else '60.4'})")
    ta = S[S.account == "Testing A"]
    print(f"Testing A signals/session: before {len(ta[ta.day < START]) / max(1, ta[ta.day < START].day.nunique()):.1f}, "
          f"after {len(ta[(ta.day >= START) & (ta.day <= END)]) / max(1, n):.1f} (full universe from 11-12)")
    report_fixes(S, F.reset_index(), n)
    print("Educational only - not financial advice.")

TSZ1 = "2026-11-17"
def report_fixes(S, F, n):
    """Skeptic skeptic-20261118-1550-1/-1551-2, Lead lead-20261118-1100-1: reporting only, the forecast is unchanged."""
    a = S[(S.day >= START) & (S.day <= END) & (S.status == "submitted")]
    by_setup = a.groupby(["strategy", "account"]).day.nunique().groupby(level=0).sum()
    fset = set(F.setup)
    inF = by_setup[by_setup.index.isin(fset)]; notF = by_setup[~by_setup.index.isin(fset)]
    print(f"\n(1) forecast setups matched by SETUP id, any account: forecast {5 * F.p_day.sum():.1f}/wk, realized {5 * inF.sum() / n:.1f}/wk "
          f"({len(inF)} of {len(fset)} forecast setups signalled)")
    print(f"(2) setups NOT in the frozen 11-11 forecast (Workbench copies, new or moved-in names): {len(notF)} setups, realized {5 * notF.sum() / n:.1f}/wk")
    for k, v in notF.sort_values(ascending=False).head(10).items(): print(f"      {k}: {5 * v / n:.1f}/wk")
    home = F.groupby("setup").account.first()
    now = a.groupby("strategy").account.agg(lambda x: ", ".join(sorted(set(x))))
    mv = [(k, home[k], now[k]) for k in now.index if k in home.index and home[k] not in now[k].split(", ")]
    flagged = sorted({h for _, h, _ in mv} | {x for _, _, w in mv for x in w.split(", ")})
    print(f"(3) setups that signalled outside their forecast account: {len(mv)}; per-account diffs are NOT like-for-like in: {', '.join(flagged) or 'none'}")
    for k, h, w in mv[:15]: print(f"      {k}: forecast {h} -> realized in {w}")
    for lab, lo, hi in (("11-12..11-16 (pre-TSZ1)", START, "2026-11-16"), ("11-17..end (TSZ1: testing half-size lots, cap 100)", TSZ1, END)):
        b = a[(a.day >= lo) & (a.day <= hi)]; m = b.day.nunique()
        if m: print(f"(4) {lab}: {m} sessions, realized {5 * b.groupby(['account', 'strategy']).day.nunique().sum() / m:.1f}/wk; "
                    f"forecast setups only {5 * b[b.strategy.isin(fset)].groupby(['account', 'strategy']).day.nunique().sum() / m:.1f}/wk")
    try:
        import json as _j
        L = [_j.loads(l) for l in open("/home/user/MCF/research/ledger.jsonl") if l.strip()]
        ch = [x for x in L if START <= str(x.get("effective", x.get("date", ""))) <= (END if END != "9999-12-31" else "2100-01-01")]
        print(f"(5) ledger entries effective {START}..{END if END != '9999-12-31' else 'now'} (owner rule 11-02): {len(ch)}")
        for x in ch: print(f"      {x.get('effective', x.get('date'))} {x.get('id')}: {str(x.get('title', ''))[:100]}")
    except Exception as e:
        print(f"(5) ledger context unavailable ({e.__class__.__name__})")
if __name__ == "__main__":
    if "--end" in sys.argv: END = sys.argv[sys.argv.index("--end") + 1]
    selftest() if sys.argv[1] == "--selftest" else main(sys.argv[1], sys.argv[2])
