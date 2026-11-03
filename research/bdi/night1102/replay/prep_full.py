"""Full live universe store (research only): for each session, read-only Alpaca fetch of 1-minute SIP bars for the
union of the five accounts' live universe.csv (~4,700 names, not only the 1,226 lab names) and the live prep's priors
(mcf.data.priors.build_priors with the real historical client, exactly as the morning prep calls it) for the same
names. Written to $MCF_REPLAY_STORE (a separate private store). Educational only - not financial advice."""
import gzip
import os
import pickle
import shutil
import sys
from pathlib import Path

from mcf.replay import store
from mcf.data.priors import build_priors

BR = ["mcf-data", "mcf-data-testing", "mcf-data-testing2", "mcf-data-graveyard", "mcf-data-gen"]
DST = Path(os.environ["MCF_REPLAY_STORE"])
src = Path(sys.argv[1])
for f in ("daily.parquet", "spreads.json"):
    if not (DST / f).exists():
        shutil.copy(src / f, DST / f)
for d in sys.argv[2:]:
    u = set().union(*[store.live_universe(d, "origin/" + b) or set() for b in BR]) | set(store.symbols())
    syms = sorted(u)
    (DST / "universe").mkdir(parents=True, exist_ok=True)
    (DST / "universe" / f"{d}.txt").write_text("\n".join(syms))
    store.fetch_1min([d], syms=syms)
    p = store.priors_path(d)
    if not p.exists():
        pri = build_priors(syms, store._d(d), feed="sip", client=None, log=print)
        p.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(p, "wb", compresslevel=6) as f:
            pickle.dump(pri, f)
        print("priors", d, len(pri), flush=True)
print("Educational only - not financial advice.")
