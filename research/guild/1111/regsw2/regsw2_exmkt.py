"""REGSW-2 follow-up (Skeptic skeptic-20261111-1651-2): is 'trades AGAINST the market state are better than the same
setup-day's other trades' a market move or a setup effect? Reporting only, the SAME S2-S4 switches (no new configs):
  (1) ex-market: gross - beta_setup x spy_move (SPY % move over the trade's own hold; beta fitted per setup on TRAIN);
  (2) on the 11-setup winning base AND on every setup in trades_tagged (full lab base), blackout removed.
TRAIN is in-sample for the 11-setup base (it was chosen on TRAIN). Same within-setup-day control as regsw2.py.
    python regsw2_exmkt.py          Educational only - not financial advice."""
import numpy as np, pandas as pd
import regsw2 as RG

B = pd.read_parquet(RG.R / "compassbf/trades_tagged.parquet",
                    columns=["setup", "side", "symbol", "date", "tod", "r", "gross", "spy_move", "e_checkpoint", "e_w60", "e_spy_fo"])
B = B[~RG.GD._blackout(B.symbol.to_numpy(), B.date.to_numpy())].dropna(subset=["spy_move"]).reset_index(drop=True)
B["per"] = np.where(B.date <= RG.TR_END, "TRAIN", np.where(B.date <= RG.VA_END, "VALID", "FWD"))
beta = {}
for s, g in B[B.per == "TRAIN"].groupby("setup"):
    beta[s] = np.polyfit(g.spy_move, g.gross, 1)[0] if len(g) >= 30 else (1.0 if g.side.iloc[0] > 0 else -1.0)
B["beta"] = B.setup.map(beta).fillna(B.side.astype(float))
B["exm"] = B.gross - B.beta * B.spy_move
S = RG.spy_days(); keep = set(pd.read_csv(RG.HERE / "base.csv").setup)
rows = []
for base_name, bb in (("winning 11", B[B.setup.isin(keep)]), (f"full {B.setup.nunique()}", B)):
    bb = bb.reset_index(drop=True); SW = RG.switches(bb, S)
    for name in ("S2 CHK", "S3 W60", "S4 SPYFO"):
        for per in ("TRAIN", "VALID", "FWD"):
            m = (bb.per == per).to_numpy(); b, s_ = bb[m].reset_index(drop=True), SW[name][m]
            days = sorted(b.date.unique()); r = dict(base=base_name, switch=name, period=per, days=len(days), trades=len(b))
            for col, tag in (("gross", "gross"), ("exm", "exmkt"), ("r", "net")):
                ex, _ = RG.score_one(b, s_, col, days)
                r[f"{tag}_excess"] = round(ex.sum(), 1); r[f"{tag}_t"] = round(RG.tday(ex), 2)
            rows.append(r)
O = pd.DataFrame(rows); pd.set_option("display.width", 220)
print("excess of switching OFF trades against the state, vs a random off-set of the same size in the same setup-day "
      "(negative = the against-state trades are BETTER than their setup-day peers)")
print(O.to_string(index=False)); O.to_csv(RG.HERE / "exmkt_results.csv", index=False)
print("Educational only - not financial advice.")
