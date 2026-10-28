"""hf1027 task 3-4 (live side): replay every half-R HF trade (target <= 0.6R in the journal) on SIP 1-min bars from
its live fill with its live stop, and 4 target settings: as live (journal target price), 0.5R, 0.75R, 1.0R from the
fill; flat 15:55; stop-first inside a bar (conservative), the entry minute's bar included.
Costs (backtest model, rule 1): entry 1c + 1 bp; non-target exit 1c + 1 bp, + 2c on stops; target exits free.
The 0.35R live scale-out (coil-k4, 10 trades) is ignored in the replay. Parity: replay "live" vs the journal rc.
Usage: python replay.py <scratch> -> replay.parquet (scratch), replay_out.txt   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent; TZ = "America/New_York"
H = pd.read_csv(HERE / "hf_setups.csv")
T = pd.read_parquet(S / "all_trades.parquet")
T = T[(T.date >= "2026-10-09") & T.strategy.isin(H.setup)]
T = T[T.strategy.isin(T.groupby("strategy").tgt_r.median().loc[lambda x: x <= 0.6].index)].copy()
TG = {"live": None, "t050": 0.5, "t075": 0.75, "t100": 1.0}
cache = {}
def bars(d, s):
    k = (d, s)
    if k not in cache:
        f = S / "bars" / d / f"{s}.parquet"
        b = pd.read_parquet(f) if f.exists() else None
        if b is not None:
            b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
        cache[k] = b
    return cache[k]
out = []
for r in T.itertuples():
    b = bars(r.date, r.symbol)
    if b is None: continue
    w = b[(b.index >= r.nt.floor("1min")) & (b.index.hour * 100 + b.index.minute <= 1555)]
    if w.empty: continue
    sd, e, R = r.side, r.entry, r.Rps
    hi, lo, cl = w.high.to_numpy(), w.low.to_numpy(), w.close.to_numpy()
    ec = 0.01 + e * 1e-4
    rec = dict(id=r.id, acct=r.acct, strategy=r.strategy, date=r.date, symbol=r.symbol, hhmm=r.hhmm, rc=r.rc, Rps=R, entry=e,
               stop_bps=r.stop_bps, tgt_r=r.tgt_r, cost_frac=ec / R)
    # full-session MFE before the stop (how far it went in our favour before stopping, or by 15:55)
    adv = lo if sd == 1 else hi; fav = hi if sd == 1 else lo
    hit = np.flatnonzero(sd * (adv - r.stop) <= 0)
    kstop = hit[0] if len(hit) else len(w)
    rec["mfe_full"] = max(0.0, float((sd * (fav[:kstop] - e)).max()) / R) if kstop > 0 else 0.0
    for name, u in TG.items():
        tgt = r.target if u is None else e + sd * u * R
        x, why = cl[-1], "flat"
        for k in range(len(w)):
            if sd * (adv[k] - r.stop) <= 0: x, why = r.stop, "stop"; break
            if sd * (fav[k] - tgt) >= 0: x, why = tgt, "target"; break
        xc = 0.0 if why == "target" else 0.01 + x * 1e-4 + (0.02 if why == "stop" else 0.0)
        rec[name] = sd * (x - e) / R - (ec + xc) / R
        rec[name + "_gross"] = sd * (x - e) / R
        rec[name + "_x"] = why
    out.append(rec)
X = pd.DataFrame(out); X.to_parquet(S / "replay.parquet", index=False)

def dayt(g, col):
    d = g.groupby("date")[col].sum(); return d.mean() / (d.std(ddof=1) / len(d) ** .5) if len(d) > 2 else np.nan
L = [f"replayed {len(X)} of {len(T)} half-R HF trades ({X.strategy.nunique()} setups); 4 target settings = 4 configurations per setup",
     "parity: journal rc vs replay 'live' (same target/stop as live, model costs)"]
L.append(X.groupby("strategy").agg(n=("rc", "size"), journal=("rc", "mean"), replay_live=("live", "mean"),
         agree_sign=("live", lambda s: (np.sign(s) == np.sign(X.loc[s.index, "rc"])).mean())).round(3).to_string())
L.append("\navg R after costs by target (day-clustered t in brackets is for the delta vs live):")
rows = []
for s, g in list(X.groupby("strategy")) + [("ALL half-R HF", X)]:
    row = dict(setup=s, n=len(g))
    for n in TG:
        row[n] = round(g[n].mean(), 3)
        row[n + "_win"] = round((g[n] > 0).mean(), 3)
    for n in ("t075", "t100"):
        g2 = g.assign(dl=g[n] - g["live"]); row[n + "_dt"] = round(dayt(g2, "dl"), 2)
    row["cost_live"] = round((g.live_gross - g.live).mean(), 3); row["cost_t100"] = round((g.t100_gross - g.t100).mean(), 3)
    row["mfe_full>=1"] = round((g.mfe_full >= 1).mean(), 3)
    rows.append(row)
R = pd.DataFrame(rows); R.to_csv(HERE / "replay_targets.csv", index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40)
L.append(R.to_string(index=False))
txt = "\n".join(L) + "\n\nEducational only - not financial advice.\n"
open(HERE / "replay_out.txt", "w").write(txt); print(txt)
