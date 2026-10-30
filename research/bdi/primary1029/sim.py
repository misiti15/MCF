"""primary1029 portfolio simulator for Primary's current 8 setups on the open two-year signals (p3_1029 bt.py output,
<scratch>/p3/p3bt/sig_*.parquet; locked months are never loaded - asserted). Same account rules as p3_1029 evalp.py
(setup_order priority within a poll, <= 3 same-side lots per symbol, no opposite side, 30 lots per setup, 77 in all,
5-min path, stop first, 15:55 flatten, production costs), plus per-trade context recorded at entry:
  lot_seq   1 + same-symbol same-side lots open at entry (any setup)
  poll_k    lots taken on the same symbol+side in the same poll (decision bar)
  open_unr  min unrealized R (at this entry price) of the open same-symbol lots, NaN if none
  fam       'S' = short family RW3-FD / RW5-FD / MF2-FD / MF4 / MF4-FD, else the setup prefix
  tgt_ago   minutes since a same-symbol same-side lot last exited at its target (NaN if none today)
  sym_stops same-symbol same-side stop exits realized before this entry today
  fam_stops short-family stop exits realized before this entry today (any symbol)
  day_real  account realized R (full lots) before this entry today
A config may block entries (changes the trade list; frees slots) and/or set a size weight w per trade (keeps every trade).
Educational only - not financial advice."""
import os, sys, zlib, math
from pathlib import Path
import numpy as np, pandas as pd, yaml
ROOT = Path("/home/user/MCF")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "history2y"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "primary1029 sweeps never read the locked block"
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
TRAIN_END = "2025-12-31"
CFG = yaml.safe_load((ROOT / "config" / "default.yaml").read_text())
ORDER = {s: i for i, s in enumerate(CFG["live"]["setup_order"])}
FAMS = ("RW3", "RW5", "MF2", "MF4")


def load(sigdir, allow_locked=False):
    sig = pd.concat([pd.read_parquet(f) for f in sorted(Path(sigdir).glob("sig_*.parquet"))], ignore_index=True)
    d = pd.to_datetime(sig.date).dt.date
    inl = (d >= LOCK[0]) & (d <= LOCK[1])
    if allow_locked:
        assert inl.all()
    else:
        assert not inl.any(), "locked row"
    sig["date"] = d.astype(str)
    sig["prio"] = sig.setup.map(ORDER).fillna(99)
    sig["tie"] = [zlib.crc32(f"{a}|{b}|{c}".encode()) for a, b, c in zip(sig.symbol, sig.date, sig.setup)]
    sig["fam"] = [("S" if s.split("-")[0] in FAMS else s.split("-")[0]) for s in sig.setup]
    return sig.sort_values(["date", "tod", "prio", "tie"]).reset_index(drop=True)


def tmin(t):
    return (t // 100) * 60 + t % 100


def simulate(sig, block=None, lots=3):
    """block(ctx) -> True to skip. Returns the taken trades with context columns."""
    r = sig.r_base.to_numpy(float); x = sig.x_base.to_numpy(int); k = sig.k_base.to_numpy(int)
    D, T, SY, SD, ST, FA = (sig[c].to_numpy() for c in ("date", "tod", "symbol", "side", "setup", "fam"))
    E = sig.entry.to_numpy(float); RR = (sig.R * sig.geom.map({"t1s1": 1.0}).fillna(1.0)).to_numpy(float)
    RPS = sig.R_ps.to_numpy(float)
    FO = sig["from_open"].to_numpy(float) if "from_open" in sig else np.full(len(sig), np.nan)
    GP = sig.gap.to_numpy(float)
    BO = sig["breadth_open"].to_numpy(float) if "breadth_open" in sig else np.full(len(sig), np.nan)
    out = []; cur = None
    for i in range(len(sig)):
        if D[i] != cur:
            cur = D[i]; openl = []; closed = []; polln = {}
        t = T[i]
        still = []
        for o in openl:
            (still if o["x"] > t else closed).append(o)
        openl = still
        same = [o for o in openl if o["sym"] == SY[i]]
        if any(o["side"] != SD[i] for o in same) or len(same) >= lots:
            continue
        if sum(1 for o in openl if o["setup"] == ST[i]) >= 30 or len(openl) >= 77:
            continue
        cs = [o for o in closed if o["sym"] == SY[i] and o["side"] == SD[i]]
        tg = [o["x"] for o in cs if o["k"] == 2]
        ctx = dict(lot_seq=len(same) + 1, poll_k=polln.get((t, SY[i], SD[i]), 0) + 1,
                   open_unr=min((SD[i] * (E[i] - o["e"]) / o["rps"] for o in same), default=np.nan),
                   tgt_ago=(tmin(t) - tmin(max(tg))) if tg else np.nan,
                   sym_stops=sum(1 for o in cs if o["k"] == 1),
                   acct_stops=sum(1 for o in closed if o["k"] == 1),
                   fam_stops=sum(1 for o in closed if o["fam"] == "S" and o["k"] == 1),
                   fam_real=sum(o["r"] for o in closed if o["fam"] == "S"),
                   day_real=sum(o["r"] for o in closed),
                   setup_real=sum(o["r"] for o in closed if o["setup"] == ST[i]),
                   sym_fam_lots=sum(1 for o in same if o["fam"] == FA[i]),
                   from_open=FO[i], gap=GP[i], breadth_open=BO[i], fam=FA[i], setup=ST[i], side=SD[i], tod=t, date=D[i], symbol=SY[i], r=r[i], k=k[i], x=x[i])
        if block is not None and block(ctx):
            continue
        polln[(t, SY[i], SD[i])] = ctx["poll_k"]
        openl.append(dict(x=x[i], sym=SY[i], side=SD[i], setup=ST[i], fam=FA[i], e=E[i], rps=RPS[i], k=k[i], r=r[i]))
        out.append(ctx)
    tr = pd.DataFrame(out)
    # final poll size (all lots of this symbol+side taken in the same poll) - known at decision time
    tr["poll_n"] = tr.groupby(["date", "tod", "symbol", "side"]).r.transform("size")
    return tr
