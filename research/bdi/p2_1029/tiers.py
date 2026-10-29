"""Rule-21 trade-rate tiers for every setup currently assigned to Testing 1 / Testing 2 (docs/live/assignments.json).
Entry date = first session of the setup's current continuous enabled run in the account's daily freeze files
(state branch setups/<date>.json); sessions = freeze-file sessions from then through the last full session (10-28).
Trades = live (paper) journal rows run_id=1 in that account since entry. Signals = journal 'signals' rows (any status).
Usage: python tiers.py <scratch>  (expects <scratch>/t1|t2/journal.db, <scratch>/frz/testing|testing2/*.json)
Educational only - not financial advice."""
import sys, json, sqlite3
from pathlib import Path
import pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; LAST = "2026-10-28"
A = json.load(open("/home/user/MCF/docs/live/assignments.json"))
rows = []
for acct, d, j in (("testing", "testing", "t1"), ("testing2", "testing2", "t2")):
    days = sorted(p.stem for p in (S / "frz" / d).glob("*.json") if p.stem <= LAST)
    en = {}
    for day in days:
        st = json.load(open(S / "frz" / d / f"{day}.json"))["strategies"]
        en[day] = {k for k, v in st.items() if isinstance(v, dict) and v.get("enabled")}
    c = sqlite3.connect(S / j / "journal.db")
    T = pd.read_sql("select date, strategy from trades where run_id=1", c)
    G = pd.read_sql("select day, strategy, status from signals where run_id=1", c)
    for s in A["accounts"][acct]:
        on = [day for day in days if s in en[day]]
        # current continuous run: walk back from last day
        run = []
        for day in reversed(days):
            if s in en[day]: run.append(day)
            else: break
        run = sorted(run)
        start = run[0] if run else None
        n_s = len(run)
        tr = T[(T.strategy == s) & (T.date >= (start or "9"))  & (T.date <= LAST)]
        sg = G[(G.strategy == s) & (G.day >= (start or "9")) & (G.day <= LAST)]
        rate = len(tr) / n_s if n_s else float("nan")
        tier = "young" if n_s < 10 else ("dormant" if len(tr) == 0 else ("low" if rate < 1.5 else "normal"))
        rows.append(dict(acct=acct, setup=s, start=start, first_freeze=days[0], start_is_first_file=(start == days[0]),
                         sessions=n_s, trades=len(tr), per_sess=round(rate, 2), signals=len(sg),
                         sig_status=";".join(f"{k}:{v}" for k, v in sg.status.value_counts().items()), tier=tier,
                         since=A["setups"].get(s, {}).get("since")))
R = pd.DataFrame(rows).sort_values(["acct", "tier", "per_sess"])
R.to_csv(OUT / "tiers.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200); pd.set_option("display.max_colwidth", 60)
print(R.drop(columns=["first_freeze"]).to_string(index=False))
print(R.groupby(["acct", "tier"]).size())
