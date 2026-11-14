"""NEWSMID scorer - frozen plan research/newsmid/PLAN.md + Amendment 1. Educational only - not financial advice.
    python -I newsmid.py --selftest
    python -I newsmid.py --dry   <news_rth.csv.gz> <hodsep dir>   # funnel + lexicon table only; reads NO price after entry
    python -I newsmid.py --score <news_rth.csv.gz> <hodsep dir>   # the one look (11-12)"""
import sys, re, numpy as np, pandas as pd
# Amendment 2 (lexicon sanity A5, before outcomes): inflected up/downgrade forms only ('Contract To Upgrade Airport ...' was a
# false hit), and credit-agency / guidance / list headlines excluded.
AN_UP = r"\b(?:upgrade[sd]\b|raises? (?:its )?price target|boosts? price target|initiates? .*(?:buy|outperform|overweight))"
AN_DN = r"\b(?:downgrade[sd]\b|lowers? (?:its )?price target|cuts? price target|initiates? .*(?:sell|underperform|underweight))"
EXCL = r"moody|s&p global|fitch|dbrs|\bdebt\b|credit rating|guidance|outlook|top \d+ (?:up|down)grades"
EARN = r"earnings|Q[1-4] 20\d\d|results|guidance|transcript"
ETF = set("SPY XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY".split())
def hit(p, h): return re.search(p, h, re.I) is not None and (p not in (AN_UP, AN_DN) or re.search(EXCL, h, re.I) is None)
def entry_hm(ts):
    """first 5-min bar whose start >= ts + 1 min (strict); returns hhmm int"""
    t = ts + pd.Timedelta(minutes=1)
    t = t.ceil("5min")
    return t.hour * 100 + t.minute
def selftest():
    T = lambda s: pd.Timestamp(s, tz="America/New_York")
    assert entry_hm(T("2026-10-08 10:03:20")) == 1005
    assert entry_hm(T("2026-10-08 10:04:00")) == 1005
    assert entry_hm(T("2026-10-08 10:04:01")) == 1010
    assert entry_hm(T("2026-10-08 10:00:00")) == 1005
    assert entry_hm(T("2026-10-08 10:09:00")) == 1010
    assert entry_hm(T("2026-10-08 14:29:59")) == 1435  # > 14:30 -> dropped by the caller
    assert hit(AN_UP, "RBC Capital Maintains Sector Perform on Gilead Sciences, Raises Price Target to $126")
    assert hit(AN_DN, "Morgan Stanley Maintains Equal-Weight on Evercore, Lowers Price Target to $315")
    assert hit(AN_UP, "Goldman Upgrades Foo To Buy") and not hit(AN_DN, "Goldman Upgrades Foo To Buy")
    assert hit(AN_DN, "Citi Downgrades Bar to Sell") and not hit(AN_UP, "Citi Downgrades Bar to Sell")
    assert not hit(AN_UP, "Leidos Receives $672M Transportation Security Administration Contract To Upgrade Airport Checkpoint Security")
    assert hit(AN_UP, "Jefferies Upgrades Foo to Buy, Raises Price Target to $50")
    assert hit(AN_DN, "Keybanc Downgrades Vistra to Sector Weight") and hit(AN_UP, "Morgan Stanley Analyst Upgrades Archer-Daniels-Midland Company")
    assert not hit(AN_UP, "Moody's Ratings Upgrades Fairfax Financial Debt Ratings") and not hit(AN_UP, "NTG Upgrades Full-Year 2026 Guidance")
    assert hit(EARN, "MKS Instruments Q3 2026 Earnings Call Transcript") and not hit(EARN, "Wells Fargo Lowers Price Target for Arm")
    x = np.array([1.0, -1.0, 2.0, 0.0]); d = np.array(["a", "a", "b", "c"])
    g = pd.Series(x).groupby(d).mean(); assert np.isclose(g.mean(), (0 + 2 + 0) / 3)
    print("selftest ok")
def load(news_f, hd):
    n = pd.read_csv(news_f, sep="\t", quoting=3).dropna(subset=["symbols", "headline"])
    n["t"] = pd.to_datetime(n.created_at, utc=True).dt.tz_convert("America/New_York")
    n["date"] = n.t.dt.strftime("%Y-%m-%d"); n["hm"] = n.t.dt.hour * 100 + n.t.dt.minute
    n["syms"] = n.symbols.str.split("|"); n["k"] = n.syms.str.len()
    xc = n.headline.str.contains(EXCL, case=False, regex=True)
    n["up"] = n.headline.str.contains(AN_UP, case=False, regex=True) & ~xc
    n["dn"] = n.headline.str.contains(AN_DN, case=False, regex=True) & ~xc
    n["earn"] = n.headline.str.contains(EARN, case=False, regex=True)
    m = pd.read_csv(f"{hd}/m5.csv.gz")
    m["t"] = pd.to_datetime(m.t, utc=True).dt.tz_convert("America/New_York")
    m["date"] = m.t.dt.strftime("%Y-%m-%d"); m["hm"] = m.t.dt.hour * 100 + m.t.dt.minute
    m = m[(m.hm >= 930) & (m.hm <= 1555)]
    d = pd.read_csv(f"{hd}/daily.csv.gz"); d["date"] = d.t.str[:10]; d = d.sort_values(["symbol", "date"])
    pc = d.groupby("symbol").c.shift(1); d["tr"] = np.maximum(d.h, pc) - np.minimum(d.l, pc)
    d["atrp"] = d.groupby("symbol").tr.transform(lambda x: x.rolling(14).mean().shift(1)) / pc
    return n, m, d.set_index(["symbol", "date"]).atrp
def events(n, sessions, lab):
    f = {}
    prev = {sessions[i]: sessions[i - 1] for i in range(1, len(sessions))}
    ex = n.explode("syms")
    s = n[(n.k == 1) & (n.source == "benzinga")].copy(); s["sym"] = s.syms.str[0]
    f["single-symbol benzinga items"] = len(s)
    s = s[s.sym.isin(lab) & s.date.isin(prev) & (s.hm >= 1000) & (s.hm < 1430)]; f["lab name, 10:00-14:30, test session"] = len(s)
    s = s[s.up ^ s.dn]; f["one lexicon leg"] = len(s)
    s = s.sort_values("t").groupby(["sym", "date"]).head(1).copy(); f["first per name-day"] = len(s)
    s["s"] = np.where(s.up, 1, -1); s["ehm"] = s.t.map(entry_hm); s = s[s.ehm <= 1430]; f["entry bar <= 14:30"] = len(s)
    an = ex[ex.up | ex.dn]; keep = []; nre = nearn = nopp = 0
    E = ex[ex.earn]
    for r in s.itertuples():
        D = r.date; p0 = pd.Timestamp(f"{prev[D]} 16:00", tz="America/New_York"); d16 = pd.Timestamp(f"{D} 16:00", tz="America/New_York")
        if ((E.syms == r.sym) & (E.t >= p0) & (E.t < d16)).any(): nearn += 1; continue
        a = an[an.syms == r.sym]
        pre = a[(a.t >= pd.Timestamp(f"{D} 04:00", tz="America/New_York")) & (a.t < pd.Timestamp(f"{D} 10:00", tz="America/New_York"))]
        if len(pre): nre += 1; continue
        estart = pd.Timestamp(f"{D} {r.ehm // 100:02d}:{r.ehm % 100:02d}", tz="America/New_York")
        opp = a[(a.date == D) & (a.t <= estart) & ((a.dn if r.s > 0 else a.up))]
        if len(opp): nopp += 1; continue
        keep.append(r.Index)
    f["dropped: earnings D-1 16:00..D 16:00"] = nearn; f["dropped: re-post (analyst item D 04:00-10:00), A2"] = nre
    f["dropped: opposite leg before entry"] = nopp
    s = s.loc[keep]; f["events after exclusions"] = len(s)
    return s, f, ex, prev
def main(mode, news_f, hd):
    n, m, A = load(news_f, hd)
    sessions = sorted(m.date.unique()); sessions = [x for x in sessions if x >= "2026-10-07"]
    lab = set(m.symbol.unique()) - ETF
    ev, f, ex, prev = events(n, sessions, lab)
    print("FUNNEL"); [print(f"  {k}: {v}") for k, v in f.items()]
    print(f"  per-day events: min {ev.groupby('date').size().min()}, median {ev.groupby('date').size().median():.0f}, days {ev.date.nunique()}")
    rng = np.random.default_rng(11)
    for lg, nm in ((1, "an_up"), (-1, "an_dn")):
        h = ev[ev.s == lg].headline; print(f"\nLEXICON SANITY {nm} (20 random of {len(h)}):")
        for x in h.sample(min(20, len(h)), random_state=11): print("   ", x[:110])
    # pre-entry quantities (prices at or before the entry bar open only)
    O = m.set_index(["symbol", "date", "hm"])
    o930 = m[m.hm == 930].set_index(["symbol", "date"]).o
    def px(sym, D, hm, col): return O[col].get((sym, D, hm), np.nan)
    ev["entry"] = [px(r.sym, r.date, r.ehm, "o") for r in ev.itertuples()]
    ev["atrp"] = [A.get((r.sym, r.date), np.nan) for r in ev.itertuples()]
    ev["o930"] = [o930.get((r.sym, r.date), np.nan) for r in ev.itertuples()]
    b = len(ev); ev = ev.dropna(subset=["entry", "atrp", "o930"]); ev = ev[(ev.entry >= 5) & (ev.atrp > 0)]
    print(f"\n  with entry bar / ATR / 09:30 open and price >= $5: {len(ev)} (dropped {b - len(ev)})")
    ev["pm"] = ev.s * (ev.entry / ev.o930 - 1) / ev.atrp
    if mode == "--dry":
        print("DRY RUN: no price after entry read. Educational only - not financial advice."); return
    # ---------------- the one look ----------------
    ev["exit"] = [px(r.sym, r.date, 1550, "c") for r in ev.itertuples()]
    spy_o = {(D, hm): v for (s_, D, hm), v in O.o.items() if s_ == "SPY"}
    spy_c = {D: v for (s_, D, hm), v in O.c.items() if s_ == "SPY" and hm == 1550}
    ev = ev.dropna(subset=["exit"])
    ev["spy"] = [spy_c[r.date] / spy_o[(r.date, r.ehm)] - 1 for r in ev.itertuples()]
    ev["c"] = ev.s * ((ev.exit / ev.entry - 1) - ev.spy) / ev.atrp
    ev["cost"] = ((0.01 + ev.entry * (1.4e-4 + 4.4e-4)) / ev.entry + (0.01 + ev.exit * 1e-4) / ev.exit) / ev.atrp
    # A6 created_at sanity
    late = []
    for r in ev.itertuples():
        w = m[(m.symbol == r.sym) & (m.date == r.date)]
        tt = w.t; sel = w[(tt >= r.t - pd.Timedelta(minutes=30)) & (tt <= r.t + pd.Timedelta(minutes=30))]
        if len(sel): late.append(sel.loc[sel.v.idxmax(), "t"] < r.t - pd.Timedelta(minutes=5))
    print(f"A6: share of events whose peak-volume bar (+-30 min) starts > 5 min BEFORE created_at: {np.mean(late):.3f} (n {len(late)})")
    # control: same date + entry bar, names with no news from prev 16:00 to entry start, same pm/ATR terciles
    pe = np.quantile(ev.pm, [1 / 3, 2 / 3]); ae = np.quantile(ev.atrp, [1 / 3, 2 / 3])
    close1550 = m[m.hm == 1550].set_index(["symbol", "date"]).c
    exs = ex[["syms", "t"]]
    ctl = []
    for (D, hm), g in ev.groupby(["date", "ehm"]):
        p0 = pd.Timestamp(f"{prev[D]} 16:00", tz="America/New_York")
        es = pd.Timestamp(f"{D} {hm // 100:02d}:{hm % 100:02d}", tz="America/New_York")
        newsy = set(exs[(exs.t >= p0) & (exs.t < es)].syms)
        bar = m[(m.date == D) & (m.hm == hm)].set_index("symbol").o
        cand = [x for x in bar.index if x in lab and x not in newsy]
        C = pd.DataFrame({"entry": bar[cand]})
        C["exit"] = [close1550.get((x, D), np.nan) for x in C.index]; C["o930"] = [o930.get((x, D), np.nan) for x in C.index]
        C["atrp"] = [A.get((x, D), np.nan) for x in C.index]; C = C.dropna(); C = C[(C.entry >= 5) & (C.atrp > 0)]
        spy = spy_c[D] / spy_o[(D, hm)] - 1
        for r in g.itertuples():
            pm = r.s * (C.entry / C.o930 - 1) / C.atrp
            same = (np.digitize(pm, pe) == np.digitize([r.pm], pe)[0]) & (np.digitize(C.atrp, ae) == np.digitize([r.atrp], ae)[0])
            cc = r.s * ((C.exit / C.entry - 1) - spy) / C.atrp
            ctl.append((r.Index, cc[same].mean() if same.sum() >= 5 else np.nan, int(same.sum())))
    cd = pd.DataFrame(ctl, columns=["i", "ctl", "nctl"]).set_index("i"); ev = ev.join(cd)
    nb = len(ev); ev = ev.dropna(subset=["ctl"]); print(f"control cell >= 5 names: {len(ev)} of {nb}; median control names {ev.nctl.median():.0f}")
    ev["x"] = ev.c - ev.ctl
    def t_(df, col):
        g = df.groupby("date")[col].mean(); return g.mean(), g.mean() / (g.std(ddof=1) / np.sqrt(len(g))), len(g)
    def rep(df, tag):
        mx, tx, nd = t_(df, "x"); mc, tc, _ = t_(df, "c")
        print(f"{tag}: n {len(df)}, days {nd}, excess {mx:+.4f} ATR (t {tx:+.2f}), c {mc:+.4f} (t {tc:+.2f}), median c {df.c.median():+.4f}, "
              f"control {df.ctl.mean():+.4f}, cost {df.cost.mean():.4f}, pre-move {df.pm.mean():+.3f}")
        return mx, tx
    print()
    mx, tx = rep(ev, "ALL EVENTS")
    for lg, nm in ((1, "an_up (long)"), (-1, "an_dn (short)")): rep(ev[ev.s == lg], "  " + nm)
    h1, h2 = ev[ev.date <= "2026-10-23"], ev[ev.date >= "2026-10-26"]; rep(h1, "  first half"); rep(h2, "  second half")
    ev["pmt"] = np.digitize(ev.pm, pe)
    for k in range(3): rep(ev[ev.pmt == k], f"  pre-move tercile {k} (A3: 2 = moved most their way)")
    for lo, hi, nm in ((1000, 1100, "10:00-11:00"), (1100, 1230, "11:00-12:30"), (1230, 1431, "12:30-14:30")):
        rep(ev[(ev.ehm >= lo) & (ev.ehm < hi)], f"  entry {nm}")
    spyday = {D: spy_c[D] / spy_o[(D, 930)] - 1 for D in ev.date.unique() if (D, 930) in spy_o}
    ev["spyup"] = ev.date.map(spyday) > 0
    rep(ev[ev.spyup], "  SPY up days (reporting only)"); rep(ev[~ev.spyup], "  SPY down days (reporting only)")
    dirn = 1 if mx > 0 else -1
    net = dirn * ev.c.mean() - ev.cost.mean()
    gd = ev.groupby("date").x.sum() * dirn; bd = gd.idxmax(); wob = dirn * ev[ev.date != bd].x.mean()
    legs = [np.sign(ev[ev.s == lg].x.mean()) == dirn for lg in (1, -1)]
    halves = [np.sign(h.x.mean()) == dirn for h in (h1, h2)]
    longnet = ev[ev.s == 1].c.mean() * dirn - ev[ev.s == 1].cost.mean()
    p1 = abs(tx) >= 2.84 and net > 0; p2 = wob > 0 and all(legs) and all(halves); p3 = longnet > 0
    print(f"\nDIRECTION picked by sign (A4, counted): {'follow' if dirn > 0 else 'FADE (not pre-registered)'}; net {net:+.4f} ATR/trade;"
          f" w/o best day {wob:+.4f}; legs {legs}; halves {halves}; long leg net {longnet:+.4f}")
    print(f"PASS 1 {p1}; PASS 2 {p2}; PASS 3 {p3} -> {'PASS' if p1 and p2 else 'FAIL - NEWSMID closed'}{'' if p3 else ' (long leg flag)'}")
    print("configs 2, family 147, BAR90 2.84. Educational only - not financial advice.")
    ev.drop(columns=["syms"]).to_csv("newsmid_events.csv.gz", index=False)
if __name__ == "__main__":
    if sys.argv[1] == "--selftest": selftest()
    else: main(sys.argv[1], sys.argv[2], sys.argv[3])
