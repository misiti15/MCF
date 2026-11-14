"""UPDAY-LONG (Lead lead-20261114-0100-2; descriptive, 0 configs): do existing LONG lab setups carry cross-sectional edge on
up-reading days, beyond index beta? 2-year lab lists with point-in-time compass tags (research/compassbf/trades_tagged.parquet,
locked block never read), earnings-blackout trades removed. Reading at ENTRY = SPY from-open at the last completed bar
strictly before entry (e_spy_fo, strict < tag): up > 0, down < 0. Ex-market gross = gross R - beta_setup x spy_move over the
hold (beta fitted per setup on TRAIN, regsw2_exmkt.py); ATR units = R x 0.25 (R = 0.25 ATR_d). Family = name prefix before
the first '-' ('-FD' twins share it). Per family x reading x period: trades, days, mean ex-market ATR/trade, day-clustered t,
total without its best day. Periods TRAIN <= 2025-09-30, VALID <= 2026-10-07, FWD after.
    python updaylong.py          Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
HERE = Path(__file__).resolve().parent; R = HERE.parent
sys.path.insert(0, "/home/user/MCF")
from mcf.research.generator import data as GD
TR_END, VA_END = "2025-09-30", "2026-10-07"

B = pd.read_parquet(R / "compassbf/trades_tagged.parquet", columns=["setup", "side", "symbol", "date", "tod", "gross", "spy_move", "e_spy_fo"])
assert not ((B.date >= "2024-11-01") & (B.date <= "2025-02-28")).any()
assert GD.EARN.exists()
B = B[B.side > 0]
B = B[~GD._blackout(B.symbol.to_numpy(), B.date.to_numpy())].dropna(subset=["spy_move", "e_spy_fo"]).reset_index(drop=True)
B["per"] = np.where(B.date <= TR_END, "TRAIN", np.where(B.date <= VA_END, "VALID", "FWD"))
beta = {s: (np.polyfit(g.spy_move, g.gross, 1)[0] if len(g) >= 30 else 1.0) for s, g in B[B.per == "TRAIN"].groupby("setup")}
B["beta"] = B.setup.map(beta).fillna(1.0)
B["exm_atr"] = 0.25 * (B.gross - B.beta * B.spy_move)
B["gross_atr"] = 0.25 * B.gross
B["read"] = np.where(B.e_spy_fo > 0, "up", np.where(B.e_spy_fo < 0, "down", "flat"))
B["fam"] = B.setup.str.split("-").str[0]


def cell(g, col):
    d = g.groupby("date")[col].sum()
    t = d.mean() / (d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 2 and d.std() > 0 else np.nan
    return pd.Series(dict(trades=len(g), days=len(d), mean=g[col].mean(), t_day=t, tot=d.sum(), tot_wo_best=d.sum() - d.max(),
                          best_share=d.max() / d.sum() if d.sum() > 0 else np.nan))


rows = []
for (f, rd, p), g in B[B.read != "flat"].groupby(["fam", "read", "per"]):
    c = cell(g, "exm_atr"); c["gross_mean"] = g.gross_atr.mean()
    rows.append(dict(fam=f, read=rd, per=p, setups=g.setup.nunique(), **c.to_dict()))
O = pd.DataFrame(rows)
W = O.pivot_table(index=["fam"], columns=["read", "per"], values="mean")
TT = O.pivot_table(index=["fam"], columns=["read", "per"], values="t_day")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print(f"UPDAY-LONG: {B.setup.nunique()} long setups, {len(B)} trades (blackout removed), {B.date.nunique()} days, "
      f"{B.fam.nunique()} families; up-reading share {np.mean(B.read == 'up'):.2f}")
print("\nmean EX-MARKET ATR per trade by family x reading x period (t_day below):")
print(W.round(4).to_string()); print(TT.round(2).to_string())
up = O[O.read == "up"].set_index(["fam", "per"])
both = up.unstack("per")
cand = [f for f in both.index if all(both.loc[f, ("mean", p)] > 0 for p in ("TRAIN", "VALID") if ("mean", p) in both.columns and pd.notna(both.loc[f, ("mean", p)]))]
print("\nfamilies with POSITIVE ex-market mean on up-reading days in BOTH TRAIN and VALID:", cand)
print(O[(O.read == "up") & O.fam.isin(cand)].round(4).to_string(index=False))
# pooled all-long, by reading
P = pd.DataFrame([dict(read=rd, per=p, **cell(g, "exm_atr").to_dict(), gross_mean=g.gross_atr.mean(), raw_r_mean=g.gross.mean())
                  for (rd, p), g in B[B.read != "flat"].groupby(["read", "per"])])
print("\nALL long setups pooled:"); print(P.round(4).to_string(index=False))
O.round(5).to_csv(HERE / "updaylong_cells.csv", index=False)
print("\nDescriptive only (0 configs): a positive up-day family is a lead to plan and test, not a verdict. "
      "Ex-market removes each setup's TRAIN beta to SPY over its own hold. Educational only - not financial advice.")
