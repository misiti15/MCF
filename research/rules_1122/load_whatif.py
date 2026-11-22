"""What-if rows (signals not taken, journal run kind 'whatif') of every mcf-data* branch, for the skip reasons this study
needs (per-setup daily loss latch, per-setup position cap, account slots / halts, burst brake). r_multiple is the journal's
what-if R (before costs); a cost estimate is added in the part scripts. Usage: python load_whatif.py CHECKOUT OUT.parquet
Educational only - not financial advice."""
import collections, sqlite3, subprocess, sys, tempfile
import pandas as pd
CK, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, CK)
from mcf.research.shadow_calib import BRANCHES
parts, cnt = [], collections.Counter()
for acct, br in BRANCHES.items():
    raw = subprocess.run(["git", "-C", CK, "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        f.write(raw); f.flush()
        con = sqlite3.connect(f.name)
        rid = [r[0] for r in con.execute("select id from runs where kind='whatif'")]
        if not rid:
            continue
        x = pd.read_sql(f"SELECT strategy, symbol, side, date, entry_time, exit_time, entry, stop, target, exit, exit_reason, "
                        f"shares, r_multiple, meta FROM trades WHERE run_id={rid[0]}", con)
        con.close()
    x["why"] = x["meta"].str.extract(r"why=(.*)$")[0].fillna("")
    cnt.update((acct + ": " + x["why"].str.replace(r"\d+", "#", regex=True)).tolist())
    keep = x["why"].str.contains("loss limit|max positions|slot|concurrent|burst|halt|lot cap", case=False)
    x = x[keep].drop(columns=["meta"])
    x["account"] = acct
    parts.append(x)
t = pd.concat(parts, ignore_index=True)
t["date"] = t["date"].astype(str).str[:10]
t["side"] = t["side"].map(lambda s: 1 if str(s).lower() in ("1", "long", "buy") else -1)
t.to_parquet(OUT, index=False)
print(t.shape); print(t.groupby(["account", "why"]).size().to_string())
for k, v in cnt.most_common(40):
    print(v, k)
