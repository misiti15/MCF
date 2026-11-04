"""Store for the playtime1103 replays (research only): full live universe (union of the five accounts' universe.csv +
lab list) 1-minute SIP bars, live-prep priors, daily bars and journaled spreads, as research/bdi/night1102/replay/prep_full.py,
into $MCF_REPLAY_STORE. Read-only market data. Educational only - not financial advice."""
import gzip
import os
import pickle
import sys
from datetime import timedelta
from pathlib import Path

from mcf.data.priors import build_priors
from mcf.replay import store

BR = ["mcf-data", "mcf-data-testing", "mcf-data-testing2", "mcf-data-graveyard", "mcf-data-gen"]
DST = Path(os.environ["MCF_REPLAY_STORE"])
days = sys.argv[1:]
if not (DST / "spreads.json").exists():
    store.build_spreads()
if not (DST / "daily.parquet").exists():
    store.fetch_daily(store._d(days[0]) - timedelta(days=store.LOOKBACK_DAYS + 30), store._d(days[-1]))
for d in days:
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
    print("ready", d, len(syms), flush=True)
