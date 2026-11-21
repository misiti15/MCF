"""BD&I 1121: weekly give-back review 11-16..11-20 for Primary, On Deck and Testing A-F (paper, R after costs).
Curve = the runner's per-poll mtm snapshots on each state branch (polls/<date>/*.jsonl.gz: realized rr + open lots' ur;
rr/ur after costs from 11-12). Peak = max marked-to-market total; give-back = peak - close. Attribution of peak -> close:
lots open at the peak (final booked R - their ur at the peak; winners ur > 0 / losers), entries after the peak (booked R),
twins (same symbol + side entered by another setup <= 3 min earlier), late flatten (exit flatten/eod). Plus run-2 what-ifs
of signals blocked by the per-setup -2R latch and the twin cap (r_multiple carries engine costs).
Usage: python giveback.py <scratch with <acct>/journal.db>     Educational only - not financial advice."""
import gzip, json, sqlite3, subprocess, sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent / "giveback"; ROOT = "/home/user/MCF"
DAYS = [f"2026-11-{d:02d}" for d in range(16, 21)]
AC = {"primary": ("Primary", "mcf-data"), "testing": ("On Deck", "mcf-data-testing"), "testing2": ("Testing A", "mcf-data-testing2"),
      "explore1": ("Testing B", "mcf-data-explore1"), "livelab": ("Testing C", "mcf-data-livelab"), "testingd": ("Testing D", "mcf-data-testingd"),
      "testinge": ("Testing E", "mcf-data-testinge"), "testingf": ("Testing F", "mcf-data-testingf"), "gen": ("Gen", "mcf-data-gen"),
      "graveyard": ("Graveyard", "mcf-data-graveyard")}
git = lambda *a: subprocess.run(["git", "-C", ROOT, *a], capture_output=True).stdout


def snaps(br, d):
    names = git("ls-tree", "--name-only", f"origin/{br}", f"polls/{d}/").decode().split()
    out = []
    for n in sorted(names):
        raw = git("show", f"origin/{br}:{n}")
        try: txt = gzip.decompress(raw).decode()
        except Exception: continue
        for line in txt.splitlines():
            try: j = json.loads(line)
            except Exception: continue
            m = j.get("mtm")
            if m and "rr" in m: out.append((j["t"], m["rr"] + m["ur"], m["pos"]))
    return out


rows, setrows, caps = [], [], []
for a, (nm, br) in AC.items():
    c = sqlite3.connect(S / a / "journal.db")
    J = pd.read_sql("select date, symbol, strategy, side, entry, stop, shares, pnl_adj, exit_reason, entry_time, exit_time "
                    "from trades where run_id=1 and exit is not null", c)
    J = J[J.date.isin(DAYS)].copy()
    J["R"] = J.pnl_adj / ((J.entry - J.stop).abs() * J.shares)
    J["nt"] = pd.to_datetime(J.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
    J = J.sort_values("nt").reset_index(drop=True)
    J["twin"] = False
    for i, r in J.iterrows():
        p = J[(J.date == r.date) & (J.symbol == r.symbol) & (J.side == r.side) & (J.strategy != r.strategy) &
              (J.nt < r.nt) & (J.nt >= r.nt - pd.Timedelta(minutes=3))]
        J.loc[i, "twin"] = len(p) > 0
    W = pd.read_sql("select date, strategy, r_multiple, meta from trades where run_id=2 and exit is not null", c)
    W = W[W.date.isin(DAYS)]; W["why"] = W.meta.fillna("").str.extract(r"why=([^;]*)")[0].fillna("")
    W["rule"] = np.where(W.why.str.contains("daily loss limit"), "latch -2R", np.where(W.why.str.contains("twin"), "twin cap", ""))
    for rsn in ("latch -2R", "twin cap"):
        for d in DAYS:
            x = W[(W.rule == rsn) & (W.date == d)]
            if len(x): caps.append(dict(acct=nm, day=d[5:], rule=rsn, n=len(x), net=round(x.r_multiple.sum(), 2),
                                        setups=x.groupby("strategy").r_multiple.sum().round(1).to_dict()))
    for d in DAYS:
        j = J[J.date == d]
        if not len(j): continue
        sn = [s for s in snaps(br, d) if s[0] >= "09:30"]
        if not sn: continue
        tot = np.array([s[1] for s in sn]); k = int(tot.argmax()); pt, pk, pos = sn[k]
        close = j.R.sum()
        ptime = pd.Timestamp(f"{d} {pt}", tz="America/New_York")
        used = set(); cw = cl = 0.0; wset, aset = {}, {}
        for sym, st, side, ent, last, ur, _ in pos:
            m = j[(j.symbol == sym) & (j.strategy == st) & (j.nt <= ptime + pd.Timedelta(seconds=90)) & ~j.index.isin(used)]
            if not len(m): continue
            m = m.iloc[(m.entry - ent).abs().argsort()[:1]]; used.add(m.index[0])
            ctr = float(m.R.iloc[0]) - ur
            if ur > 0: cw += ctr; wset[st] = wset.get(st, 0) + ctr
            else: cl += ctr
        aft = j[j.nt > ptime + pd.Timedelta(seconds=90)]
        for st, v in aft.groupby("strategy").R.sum().items(): aset[st] = v
        trail = j[j.index.isin(used) | j.index.isin(aft.index)]
        em = np.sort((j.nt.dt.hour * 60 + j.nt.dt.minute).to_numpy())
        burst = int(max(((em >= m) & (em < m + 10)).sum() for m in em)) if len(em) else 0
        rows.append(dict(acct=nm, day=d[5:], max10=burst, peak=round(pk, 2), peak_t=pt[:5], close=round(close, 2), giveback=round(pk - close, 2),
                         open_win=round(cw, 2), open_lose=round(cl, 2), after_peak=round(aft.R.sum(), 2), n_after=len(aft),
                         twins_tail=round(trail[trail.twin].R.sum(), 2), late_tail=round(trail[trail.exit_reason.isin(["flatten", "eod"])].R.sum(), 2),
                         n_trades=len(j), worst_open=min(wset.items(), key=lambda x: x[1], default=("", 0)),
                         worst_after=min(aset.items(), key=lambda x: x[1], default=("", 0))))
        for st in set(wset) | set(aset):
            setrows.append(dict(acct=nm, day=d[5:], strategy=st, open_win=wset.get(st, 0.0), after=aset.get(st, 0.0)))
R = pd.DataFrame(rows); C = pd.DataFrame(caps); SR = pd.DataFrame(setrows)
R.to_csv(OUT / "giveback_week.csv", index=False); C.to_csv(OUT / "caps_week.csv", index=False); SR.to_csv(OUT / "giveback_setups.csv", index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 60)
txt = R.to_string(index=False)
txt += "\n\nweek sums (R):\n" + R.groupby("acct", sort=False)[["giveback", "open_win", "open_lose", "after_peak", "twins_tail", "late_tail"]].sum().round(1).to_string()
txt += "\n\nlatch / twin-cap blocked signals (run 2, r_multiple with engine costs; latch cost-in from 11-12):\n" + (C.to_string(index=False) if len(C) else "none")
if len(C): txt += "\n\nsums:\n" + C.groupby(["acct", "rule"]).agg(n=("n", "sum"), net=("net", "sum")).round(1).to_string()
txt += "\n\ngive-back by setup (sum over week, R): open winners lost / after-peak entries\n" + SR.groupby(["acct", "strategy"])[["open_win", "after"]].sum().round(1).sort_values("open_win").head(15).to_string()
open(OUT / "giveback_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
