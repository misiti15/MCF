"""REGSW step 1: targets, ETB-restricted lab base (B0), live trades, market features at the decision times.
Usage: python research/regime_switch/base.py <scratch>
  needs <scratch>/j/<branch>.db (git show origin/<branch>:journal.db), <scratch>/live_bars.parquet (fetch_live.py),
  <scratch>/live_compass.parquet (research/l3leash/live_compass.py).
Writes <scratch>/{targets.csv, lab_base.parquet, live_trades.parquet, feats.parquet}.
Locked block 2024-11-01..2025-02-28 never read (filtered at load and asserted). Educational only - not financial advice."""
import glob, importlib.util, io, re, sqlite3, subprocess, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path("/home/user/MCF"); HERE = Path(__file__).resolve().parent; S = Path(sys.argv[1])
LOCK = ("2024-11-01", "2025-02-28")
DT = [590, 600, 630, 660, 720, 780]                      # 09:50 10:00 10:30 11:00 12:00 13:00
FOMC = {"2024-09-18", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
        "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28"}
ACCTS = {"mcf-data": "Primary", "mcf-data-testing": "Testing1", "mcf-data-testing2": "Testing2", "mcf-data-graveyard": "Graveyard",
         "mcf-data-livelab": "LiveLab", "mcf-data-explore1": "Explore1", "mcf-data-gen": "Gen"}
TEAM6 = ["RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "L3-gap-slope-fromopen-FD",
         "ST7-rsi50dn-long-pm-t1s1-FD", "NS5-sma50-flush-oversold-long"]


def split(d):
    return "TRAIN" if d <= "2025-12-31" else ("VALID" if d <= "2026-10-05" else ("FWD" if d <= "2026-11-04" else "AFTER"))


def family(s, side):
    return ("S" if side < 0 else "L") + ":" + re.match(r"[A-Za-z]+", s.split("-")[0]).group(0)


def bucket(e):
    """index of the last decision time <= entry minute (-1 = before 09:50, always ON)."""
    return np.searchsorted(np.array(DT), np.asarray(e, float), side="right") - 1


# ------------------------------------------------------------------ targets
def targets():
    lab = pd.read_csv(ROOT / "research/history2y/data/bt_lab1104/setups.csv").setup.unique()
    labn = set(pd.concat(pd.read_parquet(f, columns=["setup"]) for f in glob.glob(str(ROOT / "research/history2y/data/bt_lab1104/sig_*.parquet"))).setup)
    top20 = re.findall(r"^\| 2026-11-10 \| \d+ \| ([^ ]+) ", (ROOT / "research/bdi/top20/CONDITIONS.md").read_text(), re.M)
    n = []
    for b in ("mcf-data", "mcf-data-testing", "mcf-data-testing2"):
        c = sqlite3.connect(S / "j" / f"{b}.db")
        n.append(pd.read_sql("select strategy, count(*) n from trades where run_id=1 group by strategy", c))
    n = pd.concat(n).groupby("strategy").n.sum()
    rows = []
    for s in sorted(set(TEAM6) | set(top20) | set(n[n >= 20].index)):
        rows.append(dict(setup=s, core=s in TEAM6 or s in top20, team6=s in TEAM6, top20=s in top20,
                         live_n_PT=int(n.get(s, 0)), in_lab=s in labn))
    t = pd.DataFrame(rows); t.to_csv(S / "targets.csv", index=False)
    return t


# ------------------------------------------------------------------ ETB proxy (L3LEASH-2 E90)
def etb_rate():
    git = lambda *a: subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, check=True).stdout
    snaps = []
    for br in ("mcf-data", "mcf-data-testing", "mcf-data-testing2"):
        for h in git("log", "--format=%H", f"origin/{br}", "--", "universe.csv").split():
            snaps.append(pd.read_csv(io.StringIO(git("show", f"{h}:universe.csv")), usecols=["symbol", "shortable", "easy_to_borrow", "built_at"]))
    U = pd.concat(snaps).drop_duplicates(["symbol", "built_at"])
    U["day"] = pd.to_datetime(U.built_at, utc=True).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
    U["ok"] = (U.shortable.astype(bool) & U.easy_to_borrow.astype(bool)).astype(float)
    DF = U.groupby(["day", "symbol"]).ok.mean().reset_index()
    print("ETB snapshot days", DF.day.nunique(), DF.day.min(), DF.day.max(), flush=True)
    return DF.groupby("symbol").ok.mean()


# ------------------------------------------------------------------ B0 simulation (-2R latch, <=3 lots/symbol, <=30 open)
def sim_setup(g):
    g = g.sort_values(["date", "e", "x"]).reset_index(drop=True)
    took = np.zeros(len(g), np.int8)
    for _, idx in g.groupby("date").indices.items():
        e = g.e.values[idx]; x = g.x.values[idx]; r = g.r.values[idx]; sym = g.symbol.values[idx]
        open_ = []; real = 0.0
        for j in range(len(idx)):
            still = []
            for (xx, s, rc) in open_:
                if xx <= e[j]:
                    real += rc
                else:
                    still.append((xx, s, rc))
            open_ = still
            if real <= -2.0 + 1e-12 or len(open_) >= 30 or sum(1 for o in open_ if o[1] == sym[j]) >= 3:
                continue
            took[idx[j]] = 1; open_.append((x[j], sym[j], r[j]))
    g["took"] = took
    return g[g.took == 1].drop(columns="took")


def lab_base(T):
    keep = set(T[T.in_lab].setup)
    L = []
    for f in sorted(glob.glob(str(ROOT / "research/history2y/data/bt_lab1104/sig_*.parquet"))):
        x = pd.read_parquet(f); x = x[x.setup.isin(keep) & ~x.date.between(*LOCK)]
        L.append(x)
    L = pd.concat(L, ignore_index=True)
    assert not L.date.between(*LOCK).any()
    rate = etb_rate()
    sh = L.side < 0
    L["etb_rate"] = L.symbol.map(rate)
    n0 = L.groupby("setup").size()
    L = L[~sh | (L.etb_rate >= 0.9)].copy()
    print("ETB E90 kept share (shorts):", (L[L.side < 0].groupby("setup").size() / n0).dropna().round(3).to_dict(), flush=True)
    L["e"] = (L.tod // 100) * 60 + L.tod % 100
    L["x"] = (L.xtod // 100) * 60 + L.xtod % 100
    with Pool(4) as p:
        B = pd.concat(p.map(sim_setup, [g for _, g in L.groupby("setup")]), ignore_index=True)
    B["split"] = B.date.map(split)
    B = B[B.split != "AFTER"]
    B["fam"] = [family(s, sd) for s, sd in zip(B.setup, B.side)]
    B["b"] = bucket(B.e)
    B[["setup", "fam", "side", "symbol", "date", "split", "e", "x", "b", "r"]].to_parquet(S / "lab_base.parquet")
    print("lab base trades", len(B), B.groupby("split").size().to_dict(), flush=True)
    return B


# ------------------------------------------------------------------ live trades (run 1 = real paper)
def live(T):
    keep = set(T.setup)
    out = []
    for b, acct in ACCTS.items():
        c = sqlite3.connect(S / "j" / f"{b}.db")
        t = pd.read_sql("select symbol, strategy setup, side, date, entry_time, exit_time, entry, stop, shares, pnl_adj, r_multiple "
                        "from trades where run_id=1", c)
        t = t[t.setup.isin(keep)].copy()
        den = (t.entry - t.stop).abs() * t.shares
        t["r"] = np.where(den > 0, t.pnl_adj / den, np.nan)
        for col, k in (("entry_time", "e"), ("exit_time", "x")):
            ts = pd.to_datetime(t[col], utc=True, format="mixed").dt.tz_convert("America/New_York")
            t[k] = ts.dt.hour * 60 + ts.dt.minute + ts.dt.second / 60
        t["account"] = acct
        out.append(t.dropna(subset=["r", "e", "x"]))
    L = pd.concat(out, ignore_index=True)
    L["fam"] = [family(s, sd) for s, sd in zip(L.setup, L.side)]
    L["b"] = bucket(L.e); L["split"] = "LIVE"
    L[["account", "setup", "fam", "side", "symbol", "date", "split", "e", "x", "b", "r"]].to_parquet(S / "live_trades.parquet")
    print("live trades", len(L), L.groupby("account").size().to_dict(), L.date.min(), L.date.max(), flush=True)


# ------------------------------------------------------------------ market features at decision times
def minute_days(b):
    b = b.copy(); b.index = pd.to_datetime(b.index)
    if b.index.tz is None:
        b.index = b.index.tz_localize("America/New_York")
    b = b.tz_convert("America/New_York")
    m = b.index.hour * 60 + b.index.minute
    b = b[(m >= 570) & (m < 960)]
    m = (b.index.hour * 60 + b.index.minute).values - 570
    d = b.index.strftime("%Y-%m-%d").values
    D = {}
    for day in pd.unique(d):
        if LOCK[0] <= day <= LOCK[1]:
            continue
        k = d == day
        C = np.full(390, np.nan); C[m[k]] = b.close.values[k]; C = pd.Series(C).ffill().values
        D[day] = dict(o=float(b.open.values[k][0]), c=C)
    return D


def feats():
    LB = pd.read_parquet(S / "live_bars.parquet")
    LB.index = pd.to_datetime(LB.index); LB.index = LB.index.tz_convert("America/New_York") if LB.index.tz else LB.index.tz_localize("America/New_York")
    ETF = {}
    for s in ("SPY", "QQQ", "IWM", "XLK", "XLP", "XLU", "VXX"):
        D = minute_days(pd.read_parquet(ROOT / f"data/cache_hist/1Min/{s}.parquet")[["open", "close"]])
        D.update(minute_days(LB[LB.symbol == s][["open", "close"]]))
        ETF[s] = D
    days = sorted(ETF["SPY"])
    assert not any(LOCK[0] <= d <= LOCK[1] for d in days)
    # compass W60 history (same code as L3LEASH-2)
    spec = importlib.util.spec_from_file_location("state15", ROOT / "research/bdi/hc1/state15.py")
    a0 = sys.argv; sys.argv = ["x", str(S)]; s15 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s15); sys.argv = a0
    st = s15.hist().dropna(subset=["fo"]).sort_values(["date", "T"]).reset_index(drop=True)
    st = st[~st.date.between(*LOCK)]
    sg = lambda x: np.nan_to_num(np.sign(np.asarray(x, float))).astype(int)
    st["s"] = sg(st.fo)
    base = st.s + sg(st.vw) + np.where(st.breadth_open > 0.5, 1, np.where(st.breadth_open < 0.5, -1, 0)) + \
        np.where((st.s == sg(st.qqq_fo)) & (st.s == sg(st.iwm_fo)), st.s, 0)
    piv = st.pivot(index="date", columns="T", values="s")
    pW = np.zeros(len(st), int); nm = np.zeros(len(st), int)
    for T in sorted(st["T"].unique()):
        mk = [t for t in piv.columns if T - 60 < t <= T]
        sub = piv[mk]; same = sub.eq(sub[T], axis=0).all(axis=1) & (sub[T] != 0)
        i = (st["T"] == T).values
        pW[i] = np.where(same.reindex(st.date[i]).values, piv[T].reindex(st.date[i]).values, 0); nm[i] = len(mk)
    v = base.values + pW
    st["W60"] = np.where((v >= 4) & (pW == 1) & (nm >= 2), 2, np.where(v >= 2, 1, np.where((v <= -4) & (pW == -1) & (nm >= 2), -2,
                         np.where(v <= -2, -1, 0))))
    W = st.pivot(index="date", columns="T", values="W60")
    LC = pd.read_parquet(S / "live_compass.parquet")
    LC["T"] = LC["T"].str[:2].astype(int) * 60 + LC["T"].str[3:].astype(int)
    LC["W60"] = LC.w60.map({"UP-confirmed": 2, "leaning up": 1, "neutral": 0, "leaning down": -1, "DOWN-confirmed": -2}).fillna(0)
    WL = LC.pivot(index="date", columns="T", values="W60")
    # breadth: lab context (last completed 5-min bar before T), live days after the cache from the 200 compass names
    ctx = pd.concat(pd.read_parquet(p) for p in sorted((ROOT / "research/history2y/data/context").glob("month=*.parquet")))
    ctx["date"] = pd.to_datetime(ctx.date).dt.strftime("%Y-%m-%d")
    ctx = ctx[~ctx.date.between(*LOCK)]
    ctx["m"] = (ctx.tod // 100) * 60 + ctx.tod % 100
    CB = {d: g.sort_values("m") for d, g in ctx.groupby("date")}
    H = LB[LB.hunch & ~LB.symbol.isin(["SPY", "QQQ", "IWM", "XLK", "XLP", "XLU", "VXX"])].copy()
    H["m"] = H.index.hour * 60 + H.index.minute
    rows = []
    rv_hist = {T: [] for T in DT}
    for i, d in enumerate(days):
        spy = ETF["SPY"][d]; prev = days[i - 1] if i else None
        pc = ETF["SPY"][prev]["c"][-1] if prev else np.nan
        pdt = (ETF["SPY"][prev]["c"][-1] / ETF["SPY"][prev]["o"] - 1) if prev else np.nan
        hb = H[H.date == d] if d not in CB else None
        for T in DT:
            k = T - 571
            fo = lambda s: (ETF[s][d]["c"][k] / ETF[s][d]["o"] - 1) if d in ETF[s] else np.nan
            c = spy["c"][:k + 1]; lr = np.abs(np.diff(np.log(np.r_[spy["o"], c])))
            rv = np.nansum(lr)
            hist_rv = rv_hist[T][-20:]
            rvol = rv / np.median(hist_rv) if len(hist_rv) >= 10 else np.nan
            rv_hist[T].append(rv)
            vx = ETF["VXX"].get(d); vxp = ETF["VXX"].get(prev) if prev else None
            vxx = vx["c"][k] / vxp["c"][-1] - 1 if (vx is not None and vxp is not None) else np.nan
            w = np.nan
            for Wm in ((WL, W) if d in WL.index else (W,)):
                if d in Wm.index:
                    cols = [t for t in Wm.columns if t <= T]
                    w = Wm.loc[d, cols[-1]] if cols else 0
                    break
            if d in CB:
                g = CB[d]; g = g[g.m <= T - 5]
                bo, bv = (g.breadth_open.iloc[-1], g.breadth.iloc[-1]) if len(g) else (np.nan, np.nan)
            else:
                up_o, up_v = [], []
                for s, gg in hb.groupby("symbol"):
                    x = gg[gg.m < T]
                    if not len(x):
                        continue
                    tp = (x.high + x.low + x.close) / 3; vw = (tp * x.volume).sum() / max(x.volume.sum(), 1)
                    up_o.append(x.close.iloc[-1] > gg.open.iloc[0]); up_v.append(x.close.iloc[-1] > vw)
                bo, bv = (np.mean(up_o), np.mean(up_v)) if up_o else (np.nan, np.nan)
            rows.append(dict(date=d, T=T, w60=w, spy_fo=fo("SPY"), qqq_fo=fo("QQQ"), iwm_fo=fo("IWM"), gap=spy["o"] / pc - 1,
                             bo=bo, bv=bv, rvol=rvol, vxx=vxx, pdt=pdt, sect=fo("XLK") - (fo("XLP") + fo("XLU")) / 2,
                             dow=pd.Timestamp(d).dayofweek, fomc=int(d in FOMC and T >= 780)))
    F = pd.DataFrame(rows); F.to_parquet(S / "feats.parquet")
    print("feats", F.date.nunique(), "days", F.date.min(), F.date.max(), "NaN share:", F.isna().mean().round(3).to_dict(), flush=True)


if __name__ == "__main__":
    T = targets(); print(T.to_string(), flush=True)
    live(T)
    feats()
    lab_base(T)
