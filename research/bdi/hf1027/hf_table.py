"""hf1027 tasks 1-2: high-frequency setups (live paper, all accounts merged by setup name as the dashboard does,
sessions 2026-10-09..2026-10-27) and what the profitable vs unprofitable ones share.
HF = >= 10 live trades per traded session and >= 3 sessions. Costs in (rc = pnl_adj / $ risk).
be_win as combined.py (avg loss / (avg win + avg loss) on journal r_multiple). exbest / best_share = one-big-day check
(owner 2026-10-25) on R after costs. t_day = day-clustered t (rule 4).
Usage: python hf_table.py <scratch>  -> hf_setups.csv, hf_table_out.txt   Educational only - not financial advice."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent
T = pd.read_parquet(S / "all_trades.parquet"); T = T[T.date >= "2026-10-09"]
A = json.load(open("/home/user/MCF/docs/live/assignments.json"))["setups"]
import yaml
N = {k: (v.get("name") if isinstance(v, dict) else v) or "" for k, v in yaml.safe_load(open("/home/user/MCF/config/setup_names.yaml")).items()}
out = []
for s, g in T.groupby("strategy"):
    r = g.r_multiple.astype(float); rc = g.rc
    n = len(g); day = g.groupby("date").rc.sum(); k = len(day)
    aw = r[r > 0].mean(); al = -r[r <= 0].mean()
    bd = day.idxmax(); bn = int((g.date == bd).sum()); tot = rc.sum()
    ex = lambda m: round(g[m].rc.mean(), 3) if m.any() else np.nan
    out.append(dict(setup=s, name=N.get(s, ""), now=",".join(A.get(s, {}).get("accounts", ["-"])), accts=",".join(sorted(g.acct.unique())),
        trades=n, sessions=k, per_sess=round(n / k, 1), win=round(g.win.mean(), 3),
        be_win=round(al / (aw + al), 3) if aw == aw and al == al else np.nan,
        avgR_c=round(rc.mean(), 3), totR=round(tot, 1),
        exbest=round((tot - day.max()) / (n - bn), 3) if k >= 2 and n > bn else np.nan, best_day=bd,
        best_share=round(day.max() / tot, 2) if tot > 0 else np.nan,
        t_day=round(day.mean() / (day.std(ddof=1) / k ** .5), 2) if k > 2 else np.nan,
        pos_days=f"{(day > 0).sum()}/{k}",
        tgt_r=round(g.tgt_r.median(), 2), stop_bps=round(g.stop_bps.median(), 1),
        cost_r=round(g.cost_r.mean(), 3), slip_r=round(g.slip_r.mean(), 3), stopx_r=round(g.stopx_r.mean(), 3),
        gross_r=round(g.gross_r.mean(), 3),
        avg_win=round(rc[rc > 0].mean(), 3), avg_loss=round(rc[rc <= 0].mean(), 3),
        mfe1=round((g.mfe_r >= 1).mean(), 3), mfe05=round((g.mfe_r >= 0.5).mean(), 3),
        never=round(((g.mfe_r < 0.2) & ~g.win).mean(), 3),
        repeat_sh=round((g.seq > 1).mean(), 2), first_R=ex(g.seq == 1), repeat_R=ex(g.seq > 1),
        stack_sh=round((g.lot_no > 1).mean(), 2), stacked_R=ex(g.lot_no > 1),
        side="long" if (g.side == 1).all() else ("short" if (g.side == -1).all() else "mixed"),
        med_hhmm=int(g.hhmm.median()), top_exit=g.exit_reason.value_counts().index[0]))
C = pd.DataFrame(out)
C.to_csv(OUT / "all_setups.csv", index=False)
H = C[(C.per_sess >= 10) & (C.sessions >= 3)].sort_values("avgR_c", ascending=False)
H.to_csv(OUT / "hf_setups.csv", index=False)
pd.set_option("display.width", 400); pd.set_option("display.max_columns", 60); pd.set_option("display.max_colwidth", 44)
L = [f"live paper, sessions {T.date.min()}..{T.date.max()} ({T.date.nunique()}), {len(T)} trades, {C.shape[0]} setups; "
     f"HF (>=10/session, >=3 sessions): {len(H)} setups, {H.trades.sum()} trades"]
L.append(H[["setup", "name", "now", "trades", "sessions", "per_sess", "win", "be_win", "avgR_c", "totR", "exbest", "best_day",
            "best_share", "t_day", "pos_days", "side"]].to_string(index=False))
L.append("\n-- mechanics --")
L.append(H[["setup", "avgR_c", "gross_r", "cost_r", "slip_r", "stopx_r", "tgt_r", "stop_bps", "avg_win", "avg_loss", "mfe05", "mfe1",
            "never", "repeat_sh", "first_R", "repeat_R", "stack_sh", "stacked_R", "med_hhmm", "top_exit"]].to_string(index=False))
# all setups: does frequency predict per-trade edge?
C2 = C[C.sessions >= 3]
L.append(f"\n-- all setups with >=3 sessions ({len(C2)}): trades/session bucket vs avg R after costs (trade-weighted) --")
C2 = C2.assign(fb=pd.cut(C2.per_sess, [0, 3, 10, 20, 1e9], labels=["<3", "3-10", "10-20", "20+"]))
L.append(C2.groupby("fb", observed=True).apply(lambda d: pd.Series(dict(setups=len(d), trades=d.trades.sum(),
    pos_setups=int((d.avgR_c > 0).sum()), wavgR=round((d.avgR_c * d.trades).sum() / d.trades.sum(), 3),
    totR=round(d.totR.sum(), 1)))).to_string())
L.append(f"spearman(per_sess, avgR_c) = {C2.per_sess.corr(C2.avgR_c, method='spearman'):.3f}; "
         f"spearman(per_sess, |totR|) = {C2.per_sess.corr(C2.totR.abs(), method='spearman'):.3f}")
# profitable vs unprofitable HF
L.append("\n-- HF trade-level: profitable setups (avgR_c > 0) vs unprofitable --")
T2 = T[T.strategy.isin(H.setup)].copy(); T2["grp"] = np.where(T2.strategy.isin(H[H.avgR_c > 0].setup), "profitable", "unprofitable")
L.append(T2.groupby("grp").agg(setups=("strategy", "nunique"), n=("rc", "size"), avgR=("rc", "mean"), gross=("gross_r", "mean"),
    cost=("cost_r", "mean"), tgt_r=("tgt_r", "median"), stop_bps=("stop_bps", "median"), win=("win", "mean"),
    mfe1=("mfe_r", lambda x: (x >= 1).mean()), repeat=("seq", lambda x: (x > 1).mean()), stack=("lot_no", lambda x: (x > 1).mean()),
    long=("side", lambda x: (x == 1).mean())).round(3).to_string())
L.append("\nby target size bucket (HF trades):")
T2["tb"] = pd.cut(T2.tgt_r, [0, 0.6, 0.9, 1.6, 99], labels=["<=0.5R", "0.6-0.9R", "1-1.5R", ">1.5R"])
L.append(T2.groupby("tb", observed=True).agg(setups=("strategy", "nunique"), n=("rc", "size"), win=("win", "mean"), avgR=("rc", "mean"),
    gross=("gross_r", "mean"), cost=("cost_r", "mean")).round(3).to_string())
L.append("\nby stop width (bps of price) quintile, HF trades:")
T2["sb"] = pd.qcut(T2.stop_bps, 5)
L.append(T2.groupby("sb", observed=True).agg(n=("rc", "size"), avgR=("rc", "mean"), gross=("gross_r", "mean"), cost=("cost_r", "mean"),
    win=("win", "mean")).round(3).to_string())
L.append("\nby cost share of R (cost_r) bucket, HF trades:")
T2["cb"] = pd.cut(T2.cost_r, [-9, 0, 0.05, 0.1, 0.2, 9])
L.append(T2.groupby("cb", observed=True).agg(n=("rc", "size"), avgR=("rc", "mean"), gross=("gross_r", "mean"), win=("win", "mean")).round(3).to_string())
L.append("\nby entry hour, HF trades:")
L.append(T2.groupby([T2.nt.dt.hour, "grp"]).rc.agg(["size", "mean"]).unstack().round(3).to_string())
L.append("\nby symbol-day sequence (1 = first trade of the setup in that symbol that day), HF trades:")
T2["sq"] = pd.cut(T2.seq, [0, 1, 2, 4, 999], labels=["1", "2", "3-4", "5+"])
L.append(T2.groupby(["sq", "grp"], observed=True).rc.agg(["size", "mean"]).unstack().round(3).to_string())
L.append("\nby lot number (concurrent lots, same setup + symbol), HF trades:")
L.append(T2.groupby([T2.lot_no.clip(upper=3), "grp"]).rc.agg(["size", "mean"]).unstack().round(3).to_string())
L.append("\nexit reasons, HF trades:")
L.append(T2.groupby(["grp", "exit_reason"]).rc.agg(["size", "mean"]).round(3).to_string())
txt = "\n".join(L) + "\n\nEducational only - not financial advice.\n"
open(OUT / "hf_table_out.txt", "w").write(txt); print(txt)
