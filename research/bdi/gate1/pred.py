"""GATE1 predictive tables: from the state at checkpoint T, rest-of-day SPY direction / day type, and the avg R of
trades entered after T by state (side, family x side). Usage: python pred.py <scratch>. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
CPS = [600, 630, 660, 690, 720, 750, 780, 840]
SN = {1: "UP", -1: "DOWN", 0: "MIXED"}


def wn(d):
    return "TRAIN" if d < "2026-01-01" else ("VALID" if d <= "2026-10-05" else "LIVE")


S = Path(sys.argv[1])
st = pd.read_parquet(S / "state.parquet"); st["date"] = st.date.astype(str)
st = st[st.date >= "2024-10-01"].dropna(subset=["close"]); st["w"] = st.date.map(wn)
st["rod"] = st.close / st.px - 1
rows = []
for (w, T, s), g in st[st["T"].isin(CPS)].groupby(["w", "T", "st"]):
    base = st[(st.w == w) & (st["T"] == T)]
    agree = (np.sign(g.rod) == s).mean() if s else np.nan
    rows.append(dict(w=w, T=f"{T//60}:{T%60:02d}", state=SN[s], days=len(g), share=round(len(g) / len(base), 2),
                     rod_agree=round(agree, 3) if s else np.nan, rod_up=round((g.rod > 0).mean(), 3), base_rod_up=round((base.rod > 0).mean(), 3),
                     rod_mean_pct=round(100 * g.rod.mean(), 3), eod_same_type=round((g.dtype == {1: "up", -1: "down", 0: "quiet"}[s]).mean(), 3),
                     eod_up=round((g.dtype == "up").mean(), 2), eod_down=round((g.dtype == "down").mean(), 2), eod_quiet=round((g.dtype == "quiet").mean(), 2),
                     quiet_tag=round(g.quiet.mean(), 2)))
P = pd.DataFrame(rows); P.to_csv(HERE / "pred_direction.csv", index=False)

T = pd.read_parquet(S / "trades.parquet")
T = T[T.w.isin(["TRAIN", "VALID", "LIVE"])]
out = []
for cp in CPS:
    L = T[T.m >= cp].merge(st[st["T"] == cp][["date", "st"]].rename(columns={"st": "s_cp"}), on="date", how="inner")
    for key in ["side", "fs"]:
        g = L.groupby(["w", key, "s_cp"]).agg(n=("r", "size"), days=("date", "nunique"), avg=("r", "mean")).reset_index()
        g["T"] = f"{cp//60}:{cp%60:02d}"; g["unit"] = key; g = g.rename(columns={key: "u"})
        out.append(g)
R = pd.concat(out); R["state"] = R.s_cp.map(SN); R = R.drop(columns="s_cp"); R["avg"] = R.avg.round(4)
R.to_csv(HERE / "pred_r_by_state.csv", index=False)
pd.set_option("display.width", 250)
print(P[P.state != "MIXED"].pivot_table(index=["T"], columns=["w", "state"], values=["rod_agree"]).to_string())
print(P.pivot_table(index="T", columns=["w", "state"], values="days").to_string())
print(P[P.w == "TRAIN"].to_string())
sd = R[R.unit == "side"].pivot_table(index=["T", "u"], columns=["w", "state"], values="avg").round(3)
print(sd.to_string())
