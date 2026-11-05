"""Wrapper: run research/history2y/download.py from /home/user/MCF with the STOP_UTC guard moved past tonight."""
import sys, runpy
from datetime import datetime, timezone
sys.path.insert(0, "/home/user/MCF/research/history2y")
import download as D
D.STOP_UTC = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
sys.argv = ["download.py"] + sys.argv[1:]
import multiprocessing as mp, time
from pathlib import Path
a_start, a_end, workers, symf = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
syms = Path(symf).read_text().split()
D.OUT.mkdir(parents=True, exist_ok=True)
t0 = time.time(); done = 0; failed = []
args = {"start": f"{a_start}T00:00:00Z", "end": f"{a_end}T00:00:00Z"}
with mp.get_context("fork").Pool(workers, initializer=D._init, initargs=(args,)) as pool:
    for sym, status, n in pool.imap_unordered(D.fetch, syms):
        done += 1
        if status.startswith("failed") or status in ("empty", "stopped"):
            failed.append(f"{sym}\t{status}")
        if done % 50 == 0 or status.startswith("failed"):
            print(f"{done}/{len(syms)} {sym} {status} {n} bars ({time.time()-t0:.0f}s)", flush=True)
(D.OUT / "failed.txt").write_text("\n".join(failed) + ("\n" if failed else ""))
print(f"finished {done} symbols, {len(failed)} not ok, {time.time()-t0:.0f}s", flush=True)
