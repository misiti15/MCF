"""hsscale: per-poll MTM snapshots (rr, ur, lots, gross, max lots per symbol, SPY%) + health flags, every account, every
poll day on its state branch (read-only git show). Usage (cwd inbox): python polls_extract.py OUT.parquet.
Educational only - not financial advice."""
import sys, json, gzip, subprocess
from collections import Counter
import pandas as pd
sys.path.insert(0, ".")
from mcf.report.intraday import BRANCH
def git(*a, binary=False):
    return subprocess.run(["git", *a], capture_output=True, text=not binary, timeout=120)
rows = []
for acct, br in BRANCH.items():
    if acct in ("testing1", "longhold", "hunch", "borrow"):
        continue
    r = git("ls-tree", "--name-only", f"origin/{br}:polls")
    days = [d for d in r.stdout.split() if d >= "2026-10-06"] if r.returncode == 0 else []
    for d in days:
        names = git("ls-tree", "--name-only", f"origin/{br}:polls/{d}").stdout.split()
        for n in sorted(x for x in names if x.endswith(".jsonl.gz")):
            b = git("show", f"origin/{br}:polls/{d}/{n}", binary=True).stdout
            try:
                raw = gzip.decompress(b).decode()
            except Exception:
                continue
            for line in raw.splitlines():
                if not line.strip():
                    continue
                p = json.loads(line)
                m = p.get("mtm") if isinstance(p.get("mtm"), dict) else {}
                h = p.get("health") if isinstance(p.get("health"), dict) else {}
                pos = m.get("pos") or []
                c = Counter(x[0] for x in pos)
                cs = Counter(x[1] for x in pos)
                spy = (m.get("idx") or {}).get("SPY") or [None, None]
                rows.append(dict(account=acct, date=d, t=p.get("t"), has_mtm=bool(m), rr=m.get("rr"), ur=m.get("ur"),
                                 nl=m.get("nl"), ns=m.get("ns"), gross=m.get("gross"), net=m.get("net"),
                                 nlots=len(pos), maxsym=max(c.values()) if c else 0, maxsym_name=(c.most_common(1)[0][0] if c else None),
                                 maxsetup=max(cs.values()) if cs else 0, n_null_ur=sum(1 for x in pos if x[5] is None),
                                 minlot_ur=min([x[5] for x in pos if x[5] is not None], default=None),
                                 spy=spy[1], stale=bool(p.get("data_stale") or h.get("data_stale")),
                                 mism=len(h.get("position_mismatch") or []), keys=",".join(sorted(p.keys()))[:300]))
        print(acct, d, len(rows), flush=True)
df = pd.DataFrame(rows)
df.to_parquet(sys.argv[1])
print(df.shape)
