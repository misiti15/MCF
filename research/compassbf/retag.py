"""COMPASSBF re-tag (Skeptic skeptic-20261110-0100-1, Lead lead-20261110-0100-2): a compass mark T is usable only from
T + 1 minute, so the entry tag uses the latest mark STRICTLY BEFORE the entry bar close, and m1030..m1200 only when the
entry is strictly after the mark. Adds (Scout scout-20261110-0118-1): gross (R before costs, bt_all's own cost formula
inverted; the exit-cost term uses the entry price, error < 0.001R) and spy_move (SPY % move from the entry bar close
to the exit bar close, 1-min SIP cache). Reports the share of entries whose tag changed vs the first tagging.
    python retag.py          Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib
from mcf.report import compass_live as CL
from mcf.research.gates import GEOMK, tod_cost_mult
HERE = Path(__file__).resolve().parent
NY = "America/New_York"; TL0, TL1 = pd.Timestamp("2024-11-01", tz=NY), pd.Timestamp("2025-03-01", tz=NY)
SL, BP, SX = 0.01, 1e-4, 0.02
KEEP = ["spy_fo", "votes", "w60", "c30", "checkpoint", "gate1_state", "agreement", "breadth_open"]

C = pd.read_parquet(HERE / "compass_2y.parquet")
C["Tm"] = C["T"].str[:2].astype(int) * 60 + C["T"].str[3:].astype(int)
Ci = C.set_index(["date", "Tm"])[KEEP]
OLD = pd.read_parquet(HERE / "trades_tagged.parquet")

T = pd.concat(pd.read_parquet(p) for p in sorted((ROOT / "research/history2y/data/bt_lab1104").glob("sig_*.parquet")))
T["date"] = pd.to_datetime(T.date).dt.date.astype(str); T["tod"] = T.tod.astype(int); T["xtod"] = T.xtod.astype(int)
T = T[(T.tod >= 1200) | T.setup.str.startswith("CWT12")].reset_index(drop=True)
assert len(T) == len(OLD) and (T.setup.values == OLD.setup.values).all() and (T.tod.values == OLD.tod.values).all()

# gross: invert bt_all's cost (entry close / atr_d / gap from the lab frames)
parts = []
for m in sorted(pd.to_datetime(T.date).dt.strftime("%Y-%m").unique()):
    f = lib.load_month(m, columns=["symbol", "date", "tod", "close", "atr_d", "gap"])
    f["date"] = f.date.astype(str); f["tod"] = f.tod.astype(int); f["symbol"] = f.symbol.astype(str)
    sub = T[pd.to_datetime(T.date).dt.strftime("%Y-%m") == m].reset_index()
    sub["symbol"] = sub.symbol.astype(str)
    parts.append(sub.merge(f, on=["symbol", "date", "tod"], how="left"))
J = pd.concat(parts).set_index("index").sort_index()
e = J.close.to_numpy(float); R = .25 * J.atr_d.to_numpy(float); dn = J.geom.map(lambda g: GEOMK[g][1]).to_numpy(float)
tier = np.where((J.gap.abs().to_numpy(float) >= 20) | (e < 5), 3.0, 1.0); kd = J.kind.to_numpy()
cost = (SL + e * BP) * tod_cost_mult(J.tod.to_numpy()) + np.where(kd == 2, 0.0, SL + e * BP) + np.where(kd == 1, SX, 0.0)
T["gross"] = T.r.to_numpy() * dn + tier * cost / R
T["gross"] = T.gross / dn                              # back to the list's R units (per stop distance)
print(f"gross rebuilt: missing {np.isnan(T.gross).mean():.2%}; mean net {T.r.mean():+.4f}, mean gross {T.gross.mean():+.4f}")

# spy_move: SPY close at the entry bar close -> exit bar close (1-min bars; bar ending HHMM = last minute HHMM-1)
p = ROOT / "data/cache_hist/1Min/SPY.parquet"; ix = "__index_level_0__"
s = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
if ix in s.columns: s = s.set_index(ix)
s.index = pd.DatetimeIndex(s.index).tz_convert(NY); s = s[~s.index.duplicated(keep="last")]
key = pd.Series(s.close.values, index=list(zip(s.index.strftime("%Y-%m-%d"), s.index.hour * 100 + s.index.minute)))
def last_min(t):                                       # bar end HHMM -> its last minute HHMM
    m = t // 100 * 60 + t % 100 - 1
    return m // 60 * 100 + m % 60
a = key.reindex(list(zip(T.date, T.tod.map(last_min)))).to_numpy(); b = key.reindex(list(zip(T.date, T.xtod.map(last_min)))).to_numpy()
T["spy_move"] = (b / a - 1) * 100
print(f"spy_move missing {np.isnan(T.spy_move).mean():.2%}")

# strict < re-tag
em = (T.tod // 100 * 60 + T.tod % 100).to_numpy()
T["mark_entry"] = [max([t for t in CL.MARKS if t < m], default=-1) for m in em]
for tag, mk in [("e", None), ("m1030", 630), ("m1100", 660), ("m1130", 690), ("m1200", 720)]:
    kk = list(zip(T.date, T.mark_entry if mk is None else np.where(em > mk, mk, -1)))
    sub = Ci.reindex(pd.MultiIndex.from_tuples(kk, names=["date", "Tm"]))
    for c in KEEP: T[f"{tag}_{c}"] = sub[c].to_numpy()
ch = {c: float((T[c].astype(str) != OLD[c].astype(str)).mean()) for c in ["mark_entry", "e_w60", "e_c30", "e_checkpoint", "e_gate1_state", "m1030_checkpoint", "m1200_checkpoint"]}
print("share of entries whose tag changed vs the first (<=) tagging:", {k: round(v, 4) for k, v in ch.items()})
print(f"untagged (no mark strictly before entry): {int((T.mark_entry < 0).sum())}")
T.to_parquet(HERE / "trades_tagged.parquet", index=False)
coil = T[T.setup.str.startswith("CWT12")]; coil.to_csv(HERE / "coil_tagged.csv.gz", index=False)
print(f"re-tagged {len(T)} trades; coil {len(coil)}. Educational only - not financial advice.")
