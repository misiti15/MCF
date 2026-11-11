"""REGSW-2 (plan PLAN.md, frozen 2026-11-11 08:45 ET; Skeptic audit skeptic-20261111-0902-3 applied). Stage 1 (--base-only):
the WINNING base, chosen on lab TRAIN gross and live net only (VALID / FWD outcomes not read), printed and frozen to
base.csv; committed before stage 2 scores any switch.
  base: setups in research/compassbf/trades_tagged.parquet (2y lab lists with point-in-time compass tags) with
    (a) TRAIN (<= 2025-09-30) mean GROSS R > 0 and (b) live paper net avg R > 0 over >= 20 trades (whatworks_all.csv,
    journals to 11-10, trades pooled over accounts). Earnings-blackout days (+-4 sessions) are removed from the base.
    The live check is IN-SAMPLE by construction (Skeptic): reported, labelled, never evidence.
    python regsw2.py --base-only          Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
HERE = Path(__file__).resolve().parent; R = HERE.parent
sys.path.insert(0, "/home/user/MCF")
from mcf.research.generator import data as GD
TR_END = "2025-09-30"


def base():
    T = pd.read_parquet(R / "compassbf/trades_tagged.parquet", columns=["setup", "side", "symbol", "date", "tod", "r", "gross"])
    assert not ((T.date >= "2024-11-01") & (T.date <= "2025-02-28")).any()
    assert GD.EARN.exists(), "earnings file missing (blackout would silently be all False)"
    tr = T[T.date <= TR_END].groupby("setup").agg(train_n=("gross", "size"), train_gross=("gross", "mean"), train_net=("r", "mean"))
    W = pd.read_csv(R / "whatworks/whatworks_all.csv")
    W["tot"] = W.avg_r * W.n
    lv = W.groupby("setup").agg(live_n=("n", "sum"), live_tot=("tot", "sum"), accounts=("account", lambda a: ",".join(sorted(set(a)))))
    lv["live_avg"] = lv.live_tot / lv.live_n
    J = tr.join(lv, how="inner")
    J["in_base"] = (J.train_gross > 0) & (J.live_avg > 0) & (J.live_n >= 20)
    return T, J.sort_values(["in_base", "train_gross"], ascending=False)


if __name__ == "__main__":
    T, J = base()
    pd.set_option("display.width", 220)
    print(f"setups with lab list AND live record: {len(J)}; in base: {int(J.in_base.sum())}")
    print(J.round(4).to_string())
    B = J[J.in_base]
    bt = T[T.setup.isin(B.index)].copy()
    bl = GD._blackout(bt.symbol.to_numpy(), bt.date.to_numpy())
    print(f"base trades {len(bt)} on {bt.date.nunique()} days; earnings-blackout trades removed {int(bl.sum())} ({bl.mean():.1%})")
    J.to_csv(HERE / "base_selection.csv"); B.reset_index()[["setup"]].to_csv(HERE / "base.csv", index=False)
    print("frozen: base.csv (stage 2 reads it; VALID / FWD outcomes not read here). Educational only - not financial advice.")
