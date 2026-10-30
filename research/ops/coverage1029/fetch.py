"""Read-only inputs for the 2026-10-29 coverage / funnel audit (OPS-AUDIT, LAB-RATE-PARITY).
1. State files of Primary from origin/mcf-data (journal.db, status.json, universe.csv, setups/<d>.json, earnings/<d>.json,
   polls/<d>/) - `git show`, nothing is checked out or written to the repo.
2. For each session: live-identical priors (mcf.data.priors.build_priors: daily stats + PRIOR5_BARS 5-minute warm-up) and
   SIP 1-minute RTH bars, for every symbol of today's universe.csv with ADV >= $60M (the setups need >= $95M; the margin
   catches names whose ADV on an earlier day was higher). Alpaca market-data GET only; no trading endpoint is touched.
Usage: python fetch.py <scratch> <day> [<day> ...]   -> <scratch>/p/..., <scratch>/days/<day>/{priors.pkl,bars.parquet}
Educational only - not financial advice."""
import gzip, pickle, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, "/home/user/MCF")
from mcf.data.bars import normalize, rth
from mcf.data.priors import _bars, _client, build_priors

REPO, BR = "/home/user/MCF", "origin/mcf-data"
S = Path(sys.argv[1]); DAYS = sys.argv[2:]


def show(path, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["git", "-C", REPO, "show", f"{BR}:{path}"], capture_output=True)
    if r.returncode == 0:
        out.write_bytes(r.stdout)
    return r.returncode == 0


for f in ("journal.db", "status.json", "universe.csv"):
    show(f, S / "p" / f)
for d in DAYS:
    for f in (f"setups/{d}.json", f"earnings/{d}.json"):
        show(f, S / "p" / f)
    ls = subprocess.run(["git", "-C", REPO, "ls-tree", "--name-only", f"{BR}", f"polls/{d}/"], capture_output=True, text=True)
    for f in ls.stdout.split():
        show(f, S / "p" / f)

uni = pd.read_csv(S / "p" / "universe.csv")
syms = sorted(uni.loc[uni.adv >= 60e6, "symbol"].astype(str))
print(len(syms), "symbols (universe ADV >= $60M)")
dc = _client()
for d in DAYS:
    out = S / "days" / d
    if (out / "bars.parquet").exists():
        print(d, "cached"); continue
    out.mkdir(parents=True, exist_ok=True)
    day = pd.Timestamp(d).date()
    pri = build_priors(syms, day, feed="sip", client=dc)
    (out / "priors.pkl").write_bytes(pickle.dumps(pri))
    a = datetime.combine(day, datetime.min.time()) + timedelta(hours=13)
    raw = _bars(dc, syms, a, a + timedelta(hours=8), 1, "sip")
    fr = []
    for s, g in raw.groupby(level=0):
        g = rth(normalize(g.droplevel(0)))
        g = g[g.index.date == day]
        if len(g):
            fr.append(g.assign(symbol=s))
    pd.concat(fr).to_parquet(out / "bars.parquet")
    print(d, len(pri), "priors,", len(fr), "symbols with bars")
