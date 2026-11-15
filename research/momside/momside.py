"""MOMSIDE scorer (PLAN.md frozen 2026-11-14 before any score). Steps:
  python momside.py --selftest            synthetic: planted aligned effect recovered, null ~0 (reads no real outcome)
  python momside.py --fetch               daily closes 2023-09-01..2026-11-13 (after 16:05 ET / weekends only)
  python momside.py --score               the ONE score (refuses unless PLAN.md is committed)
Educational only - not financial advice."""
import os, subprocess, sys, time
from pathlib import Path
import numpy as np, pandas as pd
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
HERE = Path(__file__).resolve().parent; R = HERE.parent; ROOT = Path("/home/user/MCF")
DATA = HERE / "data"; TR_END, VA_END = "2025-09-30", "2026-10-07"; LB0, LB1 = "2024-11-01", "2025-02-28"
HALF_DAYS = {"2025-07-03", "2025-11-28", "2025-12-24"}     # early-close sessions outside the locked block (checklist 42)
CFG = {"C1": (3, 8, False, 252), "C2": (2, 9, False, 252), "C3": (3, 8, True, 252), "C4": (3, 8, False, 126)}
# (low decile max, high decile min, longs only, lookback sessions: 252 = 12-1, 126 = 6-1 [Amendment 1])


def momentum(px: pd.DataFrame, dates, lb: int = 252) -> pd.DataFrame:
    """px: index = session dates (str, sorted), columns = symbols, values = close. Returns (date x symbol) decile table
    for each trade date: 12-1 from sessions strictly before D, NaN if the window touches the locked block or < 253 prior."""
    sess = np.array(px.index); out = {}
    blk = (sess >= LB0) & (sess <= LB1)
    for D in dates:
        i = int(np.searchsorted(sess, D, side="left"))          # sessions strictly before D: sess[:i]
        if i - lb < 0:
            continue
        lo, hi = i - lb, i - 1                                   # window [D_-lb, D_-1]
        assert lo >= 0
        if blk[lo:hi + 1].any():
            continue
        m = px.iloc[i - 21] / px.iloc[i - lb] - 1
        m = m.dropna()
        if len(m) < 50:
            continue
        out[D] = np.ceil(m.rank(method="first") / len(m) * 10).clip(1, 10)
    return pd.DataFrame(out).T


def tag(B, dec, cfg):
    lo, hi, longs_only, _lb = CFG[cfg]
    st = dec.stack()                                         # (date, symbol) -> decile, vectorised lookup
    d = st.reindex(pd.MultiIndex.from_arrays([B.date.to_numpy(), B.symbol.astype(str).to_numpy()])).to_numpy(float)
    side = B.side.to_numpy()
    counter = ((side > 0) & (d <= lo)) | (((side < 0) & (d >= hi)) if not longs_only else False)
    return counter & np.isfinite(d), np.isfinite(d)


def score(B, skip, col):
    """REGSW-2 score_one: excess of skipping `skip` vs a same-count random skip within setup-day, per day."""
    Rv = B[col].to_numpy(float); sd = (B.setup + "|" + B.date).to_numpy()
    k = pd.Series(skip.astype(float)).groupby(sd).transform("sum").to_numpy()
    n = pd.Series(1.0, index=range(len(B))).groupby(sd).transform("sum").to_numpy()
    tot = pd.Series(Rv).groupby(sd).transform("sum").to_numpy()
    delta = -Rv * skip; ctrl = -(k / n) * tot / np.where(k > 0, k, 1) * skip
    days = sorted(B.date.unique())
    ex = pd.Series(delta - ctrl).groupby(B.date.to_numpy()).sum().reindex(days, fill_value=0.0)
    t = ex.mean() / (ex.std(ddof=1) / np.sqrt(len(ex))) if len(ex) > 2 and ex.std() > 0 else np.nan
    return dict(excess=ex.sum(), t=t, wo_best=ex.sum() - ex.max(), best_share=ex.max() / ex.sum() if ex.sum() > 0 else np.nan,
                skip_share=skip.mean(), skipped_avg=Rv[skip].mean() if skip.any() else np.nan, kept_avg=Rv[~skip].mean())


def selftest():
    rng = np.random.default_rng(1); rows = []
    syms = [f"S{i}" for i in range(300)]; dates = [f"2026-0{m}-{d:02d}" for m in (3, 4, 5) for d in range(1, 29)]
    dec = pd.DataFrame(rng.integers(1, 11, (len(dates), len(syms))), index=dates, columns=syms).astype(float)
    for planted in (0.30, 0.0):
        rows = []
        for D in dates:
            for st in ("A", "B", "C"):
                for _ in range(20):
                    s = syms[rng.integers(300)]; side = 1 if rng.random() < .5 else -1; dd = dec.at[D, s]
                    al = (side > 0 and dd >= 8) or (side < 0 and dd <= 3); co = (side > 0 and dd <= 3) or (side < 0 and dd >= 8)
                    r = rng.normal(-0.05, 1) + (planted if al else -planted if co else 0)
                    rows.append(dict(setup=st, date=D, symbol=s, side=side, gross=r))
        B = pd.DataFrame(rows); skip, _ = tag(B, dec, "C1"); res = score(B, skip, "gross")
        print(f"selftest planted {planted}: excess {res['excess']:+.1f} t {res['t']:+.2f} skip share {res['skip_share']:.2f}")
        assert (res["t"] > 5) if planted else (abs(res["t"]) < 3)
    # point-in-time + locked restart unit check
    sess = [str(d.date()) for d in pd.bdate_range("2023-09-01", "2026-06-30")]
    px = pd.DataFrame({"X": np.arange(len(sess), dtype=float) + 100}, index=sess)
    dq = momentum(pd.concat([px] + [px.rename(columns={"X": f"Y{i}"}) * (1 + i / 100) for i in range(60)], axis=1),
                  ["2024-10-15", "2025-06-02", "2026-03-02", "2026-06-01"])
    print("selftest dates with a decile (2025-06-02 must be absent: its window touches the block; 2026-03-02's window starts after it):", list(dq.index))
    assert "2025-06-02" not in dq.index and "2024-10-15" in dq.index and "2026-06-01" in dq.index
    d6 = momentum(pd.concat([px] + [px.rename(columns={"X": f"Y{i}"}) * (1 + i / 100) for i in range(60)], axis=1),
                  ["2025-06-02", "2025-09-15", "2026-03-02"], lb=126)
    print("selftest 6-1 dates (2025-06-02 absent: touches the block; 2025-09-15 present):", list(d6.index))
    assert "2025-06-02" not in d6.index and "2025-09-15" in d6.index
    print("selftest ok. Educational only - not financial advice.")


def fetch():
    """Daily closes (Alpaca SIP 1Day, split-adjusted) for the lab list + SPY in TWO ranges that skip the locked block, so
    its prices are never requested (rule 19). Refused 07:30-16:05 ET on weekdays."""
    import requests
    now = pd.Timestamp.now(tz="America/New_York"); hm = now.hour * 100 + now.minute
    assert now.dayofweek >= 5 or not (730 <= hm < 1605), "refusing: weekday 07:30-16:05 ET (live jobs' rate budget)"
    sys.path.insert(0, str(ROOT / "research/history2y")); import download as DL
    syms = sorted(set((ROOT / "research/lab_symbols.txt").read_text().split()) | {"SPY"})
    sess = requests.Session()
    sess.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
    rows = []
    sys.path.insert(0, str(R)); import builder_blockguard as BG                     # checklist 43
    for a, b in (("2023-09-01", "2024-10-31"), ("2025-03-01", "2026-11-13")):
        BG.check(a, b)
        for i in range(0, len(syms), 100):
            params = {"symbols": ",".join(syms[i:i + 100]), "timeframe": "1Day", "start": a, "end": b, "feed": "sip",
                      "adjustment": "split", "limit": 10000}
            while True:
                j = DL._get(sess, params)
                for sy, bl in (j.get("bars") or {}).items():
                    rows += [(sy, x["t"][:10], float(x["c"])) for x in bl]
                tok = j.get("next_page_token")
                if not tok:
                    break
                params["page_token"] = tok
        print(f"fetched {a}..{b}: {len(rows)} rows so far", flush=True)
    D = pd.DataFrame(rows, columns=["symbol", "date", "close"]).drop_duplicates(["symbol", "date"])
    assert not ((D.date >= LB0) & (D.date <= LB1)).any()
    DATA.mkdir(exist_ok=True); D.to_parquet(DATA / "daily_closes.parquet", index=False)
    print(f"saved {len(D)} rows, {D.symbol.nunique()} symbols, {D.date.min()}..{D.date.max()}. Educational only - not financial advice.")


def load_spy_types():
    sys.path.insert(0, str(R)); import guild_read as GR
    d = GR.read_daily(columns=["symbol", "date", "open", "close"]); s = d[d.symbol == "SPY"].set_index("date")
    oc = s.close / s.open - 1
    return dict(zip(s.index, np.where(oc > .0025, "up", np.where(oc < -.0025, "down", "quiet"))))


def run_score():
    sys.path.insert(0, str(ROOT)); from mcf.research.generator import data as GD
    D = pd.read_parquet(DATA / "daily_closes.parquet"); assert not ((D.date >= LB0) & (D.date <= LB1)).any()
    px = D.pivot(index="date", columns="symbol", values="close").sort_index()
    # sessions inside the block are absent from px; insert their dates (as NaN rows) so offsets count real sessions and
    # the restart test sees them
    # block session dates from the public NYSE calendar (no locked file is opened): business days minus NYSE closures
    closed = {"2024-11-28", "2024-12-25", "2025-01-01", "2025-01-09", "2025-01-20", "2025-02-17"}
    bd = [str(d.date()) for d in pd.bdate_range(LB0, LB1) if str(d.date()) not in closed]
    px = pd.concat([px, pd.DataFrame(np.nan, index=bd, columns=px.columns)]).sort_index()
    labs = set((ROOT / "research/lab_symbols.txt").read_text().split()); px = px[[c for c in px.columns if c in labs]]
    # Amendment 2 (Lead 11-14 13:00): FULL-DAY 2-year lab lists (all entry times), built by build_full.py
    B = pd.read_parquet(HERE / "data/trades_full.parquet", columns=["setup", "side", "symbol", "date", "r", "gross", "spy_move"])
    assert not ((B.date >= LB0) & (B.date <= LB1)).any()
    B = B[~GD._blackout(B.symbol.to_numpy(), B.date.to_numpy())].dropna(subset=["spy_move"]).reset_index(drop=True)
    nh = int(B.date.isin(HALF_DAYS).sum()); B = B[~B.date.isin(HALF_DAYS)].reset_index(drop=True)   # Amendment 4 (checklist 42)
    print(f"half-day sessions dropped: {nh} trades")
    B["per"] = np.where(B.date <= TR_END, "TRAIN", np.where(B.date <= VA_END, "VALID", "FWD"))
    beta = {s: (np.polyfit(g.spy_move, g.gross, 1)[0] if len(g) >= 30 else float(g.side.iloc[0])) for s, g in B[B.per == "TRAIN"].groupby("setup")}
    B["exm"] = B.gross - B.setup.map(beta).fillna(B.side.astype(float)) * B.spy_move
    dates = sorted(B.date.unique()); DEC = {lb: momentum(px, dates, lb) for lb in (252, 126)}
    out, ps = [], []
    for c, (_, _, _, lb) in CFG.items():
        skip_all, tagged = tag(B, DEC[lb], c)
        for per in ("TRAIN", "VALID", "FWD"):
            m = ((B.per == per).to_numpy()) & tagged
            b = B[m].reset_index(drop=True); s_ = skip_all[m]
            if not len(b):
                out.append(dict(cfg=c, per=per, trades=0)); continue
            row = dict(cfg=c, per=per, trades=len(b), days=b.date.nunique())
            for col in ("gross", "exm", "r"):
                res = score(b, s_, col); row.update({f"{col}_{k}": v for k, v in res.items()})
                se = abs(res["excess"] / res["t"]) if res["t"] and np.isfinite(res["t"]) and res["t"] != 0 else np.nan
                row[f"{col}_MDE80_per_skip"] = 2.8 * se / max(int(s_.sum()), 1)          # guild standard 2026-11-15
                row[f"{col}_MDEbar_per_skip"] = (2.91 + 0.84) * se / max(int(s_.sum()), 1)
                # control's own avg R (checklist 10): a random same-count skip's expected R = its setup-day mean
                sdm = pd.Series(b[col].to_numpy(float)).groupby((b.setup + "|" + b.date).to_numpy()).transform("mean").to_numpy()
                row[f"{col}_ctrl_avg"] = float(sdm[s_].mean()) if s_.any() else np.nan
            if per == "VALID":
                v = {}
                for su, g in b.groupby("setup"):
                    sk = s_[g.index.to_numpy()]
                    if sk.sum() >= 10:
                        v[su] = score(g.reset_index(drop=True), sk, "exm")["excess"] / len(g)
                tot_s = {su: score(g.reset_index(drop=True), s_[g.index.to_numpy()], "exm")["excess"]
                         for su, g in b.groupby("setup") if s_[g.index.to_numpy()].sum() >= 10}
                ts = pd.Series(tot_s); pos = ts[ts > 0].sort_values(ascending=False)
                top5 = pos.head(5).sum() / ts.sum() if ts.sum() > 0 else np.nan      # Skeptic/Lead 11-14: concentration
                v = pd.Series(v); row.update(setups=len(v), better=int((v > 0).sum()), worse=int((v < 0).sum()),
                                             worst=round(v.min(), 4) if len(v) else np.nan,
                                             top5_share=round(top5, 3) if np.isfinite(top5) else np.nan,
                                             top5=",".join(pos.head(5).index))
                ps.append(v.rename(c))
            row["skip_share_long"] = float(s_[(b.side > 0).to_numpy()].mean()) if (b.side > 0).any() else np.nan
            row["skip_share_short"] = float(s_[(b.side < 0).to_numpy()].mean()) if (b.side < 0).any() else np.nan
            if per == "VALID":                     # Skeptic: is the excess one SPY-direction cell?
                spy = load_spy_types()
                ex, _ = None, None
                Rv = b.exm.to_numpy(float); sd = (b.setup + "|" + b.date).to_numpy()
                k = pd.Series(s_.astype(float)).groupby(sd).transform("sum").to_numpy(); n = pd.Series(1.0, index=range(len(b))).groupby(sd).transform("sum").to_numpy()
                tot = pd.Series(Rv).groupby(sd).transform("sum").to_numpy()
                exd = pd.Series(-Rv * s_ + (k / n) * tot / np.where(k > 0, k, 1) * s_).groupby(b.date.to_numpy()).sum()
                row["exm_excess_by_spy"] = {kk: round(float(v), 1) for kk, v in exd.groupby(exd.index.map(lambda d: spy.get(d, "na"))).sum().items()}
            row["by_side_exm"] = {sd: round(float(-(b.exm.to_numpy() * s_)[(b.side == sd).to_numpy()].sum()), 1) for sd in (1, -1)}
            out.append(row)
    O = pd.DataFrame(out); O.to_csv(HERE / "momside_results.csv", index=False)
    if ps:
        pd.concat(ps, axis=1).to_csv(HERE / "momside_per_setup_valid.csv")
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 50)
    print(f"MOMSIDE (PLAN.md + Amendment 1, one score): {len(B)} trades after blackout; family 187, BAR90 2.91")
    print(O.round(4).to_string(index=False))
    c1v = O[(O.cfg == "C1") & (O.per == "VALID")].iloc[0]; c1t = O[(O.cfg == "C1") & (O.per == "TRAIN")].iloc[0]
    gates = {"1 VALID exm excess > 0, t >= 2.91": bool(c1v.exm_excess > 0 and c1v.exm_t >= 2.91),
             "2 TRAIN exm excess > 0 (sign)": bool(c1t.get("exm_excess", np.nan) > 0),
             "3 >= 60% setups better (VALID)": bool(c1v.setups and c1v.better / c1v.setups >= 0.6),
             "4 best day < 50% (VALID)": bool(c1v.exm_best_share < 0.5) if np.isfinite(c1v.exm_best_share) else False,
             "5 VALID gross excess > 0": bool(c1v.gross_excess > 0)}
    c3v = O[(O.cfg == "C3") & (O.per == "VALID")].iloc[0]
    verdict = "PASS" if all(gates.values()) else "CLOSED"
    if verdict == "PASS" and not (c3v.exm_excess > 0):
        verdict += " (short-leg-driven, survivorship-suspect: C3 longs-only <= 0)"
    print("C1 gates:", gates); print("VERDICT C1:", verdict)
    if verdict.startswith("CLOSED"):
        print(f"C1: nothing above {c1v.exm_MDEbar_per_skip:.4f}R per skipped trade at the bar (MDE80 {c1v.exm_MDE80_per_skip:.4f}R); smaller unknown")
    print(f"configs shown: {len(CFG)} x 3 periods x 3 R columns")
    print("C2/C3/C4 are reported; a C2-C4-only pass is a lead. Survivorship: see PLAN. Educational only - not financial advice.")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest(); sys.exit()
    if "--score" in sys.argv:
        st = subprocess.run(["git", "-C", str(HERE), "status", "--porcelain", "PLAN.md"], capture_output=True, text=True).stdout
        assert not st.strip(), "PLAN.md must be committed before the score"
        run_score(); sys.exit()
    if "--fetch" in sys.argv:
        fetch(); sys.exit()
