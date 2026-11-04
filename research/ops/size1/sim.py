"""SIZE1 sizing simulator + full pre-registered grid (research/ops/size1/PLAN.md). Educational only - not financial advice.

usage: python sim.py <scratch_dir>   (needs lab.pkl / live.pkl from prep.py). Writes results.csv, daily.csv next to this file.
"""
import itertools
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

S = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
HERE = Path(__file__).resolve().parent
TRAIN = lambda d: (d < "2024-11-01") | ((d >= "2025-03-01") & (d <= "2025-12-31"))  # noqa: E731
VALID = lambda d: (d >= "2026-01-01") & (d <= "2026-10-05")  # noqa: E731
LIVE_A = ["MF2-open-rsimidhi-flowsell-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
          "L3-gap-slope-fromopen-FD", "NM-MF3-qqqdn-gapdn-FD"]
PRIMARY = ["L3-gap-slope-fromopen-FD", "L3-gap-slope-rsi5hi-FD", "ST7-rsi50dn-long-pm-t1s1-FD",
           "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "MF2-open-rsimidhi-flowsell-FD",
           "MF4-h40-open-flowsell-FD", "MF4-h40-open-flowsell", "NS1-rsidip-rsi5pop-long", "NS5-sma50-flush-oversold-long"]
RISKS = [0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]
BPS = [1, 2, 4]
ALLOCS = ["FC", "QS", "QX", "FAM"]
BASE = dict(risk=0.25, bp=4, alloc="FC", wt=False, hq1=False, hq2=False, hb=False, cap=None)
CAP0 = 100_000.0


def family(s):
    if "flowsell" in s or s.startswith(("MF", "RW1-", "RW3-", "RW5-", "NM-MF3")):
        return "FLOW-S"
    return s.split("-")[0]


def twin(s):
    return s[:-3] if s.endswith("-FD") else s


def shrunk(v, k=20):
    return v.mean() * len(v) / (len(v) + k)


def prepare(t, setups, q, wts, live):
    t = t[t.setup.isin(setups)].copy()
    if live:
        t["T0"] = t.ent; t["T1"] = t.ext
        t = t.drop_duplicates(["setup", "symbol", "date", "tod"])
    else:
        t["T0"] = (t.tod // 100 * 60 + t.tod % 100) * 60.0; t["T1"] = (t.xtod // 100 * 60 + t.xtod % 100) * 60.0
    t["bar"] = (t.tod // 100 * 60 + t.tod % 100)
    rng = np.random.default_rng(20261104)
    t["rnd"] = rng.random(len(t))
    t["qs"] = t.setup.map(q["qs"]); t["qx"] = t.setup.map(q["qx"])
    t["w"] = t.setup.map(wts).fillna(1.0)
    t["fam"] = t.setup.map(family); t["tw"] = t.setup.map(twin)
    t["q1"] = t.spy_fo.abs() < 0.15
    t["q2"] = t.rng30 < t.rng_med20
    return t.sort_values(["date", "T0"]).reset_index(drop=True)


def day_arrays(t):
    out = []
    for d, g in t.groupby("date", sort=True):
        out.append((d, {c: g[c].to_numpy() for c in ["T0", "T1", "bar", "rnd", "qs", "qx", "w", "r", "sf", "q1", "q2"]},
                    g.setup.to_numpy(), g.symbol.to_numpy(), g.side.to_numpy(), g.fam.to_numpy(), g.tw.to_numpy()))
    return out


def run(days, sessions, cfg):
    f = cfg["risk"] / 100.0; bp = cfg["bp"]; alloc = cfg["alloc"]
    eq = CAP0; rows = []
    by = {d: (a, s, y, sd, fm, tw) for d, a, s, y, sd, fm, tw in days}
    for d in sessions:
        if d not in by:
            rows.append((d, 0, 0.0, 0.0, 0.0, eq)); continue
        a, st, sy, sd, fm, tw = by[d]
        n = len(st)
        if alloc in ("FC", "FAM"):
            order = np.lexsort((a["rnd"], a["T0"], a["bar"]))
        else:
            order = np.lexsort((a["rnd"], -np.nan_to_num(a["qs" if alloc == "QS" else "qx"], nan=-9.0), a["bar"]))
        risk = f * eq
        opn = []  # (T1, notional, setup, symbol, side, twin, R)
        lots = {}; per_setup = {}; real_setup = {}; real_acct = 0.0
        used_fam_bar = {}; fam_hist = {}
        taken_R = 0.0; ntk = 0; msum = 0.0; T = 0.0; onot = 0.0
        for i in order:
            T = max(T, a["T0"][i]) if ntk or opn else a["T0"][i]
            if opn:
                keep = []
                for o in opn:
                    if o[0] <= T:
                        onot -= o[1]
                        lots[o[3]] = (lots[o[3]][0] - 1, o[4]); per_setup[o[2]] -= 1
                        real_setup[o[2]] = real_setup.get(o[2], 0.0) + o[6]; real_acct += o[6]
                    else:
                        keep.append(o)
                opn = keep
            s = st[i]; y = sy[i]; side = sd[i]
            if real_acct <= -20 or real_setup.get(s, 0.0) <= -2:
                continue
            c, sside = lots.get(y, (0, side))
            if c > 0 and (sside != side or c >= 3):
                continue
            if c > 0 and any(o[3] == y and o[5] == tw[i] and o[2] != s for o in opn):
                continue
            if per_setup.get(s, 0) >= 30 or len(opn) >= 77:
                continue
            b = a["bar"][i]
            if alloc == "FAM" and used_fam_bar.get((fm[i], b)):
                continue
            m = a["w"][i] if cfg["wt"] else 1.0
            if cfg["hq1"] and a["q1"][i]:
                m *= 0.5
            if cfg["hq2"] and a["q2"][i]:
                m *= 0.5
            if cfg["hb"]:
                h = [x for x in fam_hist.get(fm[i], []) if x > T - 900]
                if len(h) >= 2:
                    m *= 0.5
            notional = m * risk / max(a["sf"][i], 1e-6)
            if cfg["cap"]:
                notional = min(notional, cfg["cap"] * eq)
            m_eff = notional * a["sf"][i] / risk
            if onot + notional > bp * eq:
                continue
            R = m_eff * a["r"][i]
            onot += notional
            opn.append((a["T1"][i], notional, s, y, side, tw[i], R))
            lots[y] = (c + 1, side); per_setup[s] = per_setup.get(s, 0) + 1
            used_fam_bar[(fm[i], b)] = True
            fam_hist.setdefault(fm[i], []).append(T)
            taken_R += R; ntk += 1; msum += m_eff
        pnl = taken_R * risk
        rows.append((d, ntk, taken_R, msum, pnl / eq, eq + pnl))
        eq += pnl
    return pd.DataFrame(rows, columns=["date", "n", "R", "msum", "ret", "equity"])


def metrics(s):
    e = np.r_[CAP0, s.equity.to_numpy()]
    dd = ((e - np.maximum.accumulate(e)) / np.maximum.accumulate(e)).min()
    tot = e[-1] / CAP0 - 1
    act = s[s.n > 0]
    n = int(s.n.sum()); R = s.R.sum()
    bi = s.R.idxmax() if len(s) else None
    wob = (R - s.R[bi]) / max(n - s.n[bi], 1) if n else np.nan
    sh = s.R[bi] / R if R > 0 else np.nan
    sd = s.ret.std()
    return dict(ret=100 * tot, dd=100 * dd, rdd=tot / abs(dd) if dd < 0 else np.nan, green=100 * (act.R > 0).mean() if len(act) else np.nan,
                avgR=R / n if n else np.nan, avgR_wob=wob, best_share=100 * sh if sh == sh else np.nan, trades=n,
                t=s.ret.mean() / sd * np.sqrt(len(s)) if sd > 0 else np.nan, R_per_risk=R / s.msum.sum() if n else np.nan, days=len(s))


def tdiff(a, b):
    x = a.ret.to_numpy() - b.ret.to_numpy()
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if x.std() > 0 else np.nan


def cfgname(c):
    m = [k.upper() for k in ("wt", "hq1", "hq2", "hb") if c[k]]
    return f"{c['risk']:.2f}%/{c['bp']}x/{c['alloc']}" + ("+" + "+".join(m) if m else "") + (f"/cap{int(c['cap'] * 100)}%" if c["cap"] else "")


G = {}


def _job(args):
    book, win, cfg = args
    days, sess = G[(book, win)]
    return book, win, cfgname(cfg), cfg, run(days, sess, cfg)


def main():
    lab = pd.read_pickle(S / "lab.pkl"); live = pd.read_pickle(S / "live.pkl")
    tr = lab[TRAIN(lab.date)]
    q = pd.DataFrame({"qs": tr.groupby("setup").r.apply(shrunk), "qx": tr.groupby("setup").r_xm.apply(shrunk),
                      "n": tr.groupby("setup").size(), "avg": tr.groupby("setup").r.mean()})
    pool = ["L3-gap-slope-fromopen-FD", "L3-gap-slope-rsi5hi-FD", "ST7-rsi50dn-long-pm-t1s1-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
            "RW3-gapdn-rsi5pop-flowsell-short-FD", "MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD", "MF4-h40-open-flowsell",
            "NS5-sma50-flush-oversold-long", "exhaustion_short-FD", "NS1-rsidip-rsi5pop-long-FD", "NS4-pm-vwap-reclaim-oversold-short-FD",
            "L3-gap-slope-lowdist-FD", "RW7-gapdn-bounce-early-short-FD", "CWT05-flush-m05-v3-long", "RW3S-gapdn-flowsell-short-FD",
            "NM-AR-AM-gapdown-capitulation-long", "NM-HL-T75-pm-long", "NM-MF3-qqqdn-gapdn-FD", "CWT13-vwapstretch-z05-long",
            "CWT14-failbrk-pdl-p10-long", "CWT14-failbrk-pdl-p10-lowvol-long", "RW1-gapdn-bounce-flowsell-short-FD",
            "RW2-exhaustion-noon-adv150-short-FD", "CWT14-failbrk-orl-p10-lowvol-long", "CWT14-failbrk-orl-p10-long",
            "CWT14-failbrk-orl-p05-lowvol-long", "CWT14-failbrk-orl-p05-long", "NS2-sma50break-overbought-short",
            "NS2-sma50break-overbought-short-FD", "MF1-945-flowsell-vwapup-FD", "ST1-ordn-long-pm-t05s1-FD", "ST2-slope20up-long-am-t05s1-FD",
            "RW6-ns2-up3-short-FD", "CWT14-failbrk-pdh-p05-lowvol-short", "CWT14-failbrk-pdh-p10-lowvol-short", "CWT14-failbrk-pdh-p10-short",
            "CWT13-vwapstretch-z05-short", "CWT09-gapdn-vwaploss-g5-short", "CWT12-coil-k6-long", "CWT12-coil-k4-long",
            "CWT14-failbrk-pdl-p05-long", "CWT14-failbrk-pdl-p05-lowvol-long", "NS3-failed-vwap-reclaim-short-FD", "RW4-ns3-adv150-short-FD",
            "MF3-open-flowsell-rsi5hi-FD", "MF5-flowsell-vwapup-rsi5hi-FD", "NS5-sma50-flush-oversold-long-FD", "RW6G1-ns2-up3-vwap2sd-short-FD"]
    qp = q.loc[[p for p in pool if p in q.index]]
    qp = qp[qp.n >= 100].sort_values("qs", ascending=False)
    A2 = qp.head(5).index.tolist()
    with open(HERE / "train_rank.txt", "w") as fh:
        fh.write("TRAIN ranking of the 49-setup pool (shrunk avg R, n>=100); book A 2-year = top 5\n" + qp.round(4).to_string() + "\n")
    print("A 2-year (TRAIN top 5):", A2, flush=True)

    def weights(setups):
        sub = q.loc[[s for s in setups if s in q.index]].sort_values("qs", ascending=False)
        parts = np.array_split(np.arange(len(sub)), 3)
        w = {}
        for tier, idx in zip([1.5, 1.0, 0.5], parts):
            for j in idx:
                w[sub.index[j]] = tier
        n = tr[tr.setup.isin(w)].setup.value_counts()
        scale = sum(n[k] for k in w) / sum(w[k] * n[k] for k in w)
        return {k: v * scale for k, v in w.items()}

    books = {"A": (A2, LIVE_A), "B": (PRIMARY, PRIMARY)}
    info = {}
    for b, (s2, sl) in books.items():
        wts2 = weights(s2); wtsl = weights(sl)
        info[b] = dict(two_year=s2, live=sl, w2=wts2, wl=wtsl)
        for win, src, setups, wts, lv in [("TRAIN", lab[TRAIN(lab.date)], s2, wts2, False), ("VALID", lab[VALID(lab.date)], s2, wts2, False),
                                          ("LIVE", live, sl, wtsl, True)]:
            t = prepare(src, setups, q, wts, lv)
            sess = sorted(src.date.unique())
            G[(b, win)] = (day_arrays(t), sess)
    with open(HERE / "books.txt", "w") as fh:
        for b, v in info.items():
            fh.write(f"Book {b}: 2-year setups {v['two_year']}\n  live setups {v['live']}\n  WT weights 2-year {dict((k, round(x, 3)) for k, x in v['w2'].items())}\n"
                     f"  WT weights live {dict((k, round(x, 3)) for k, x in v['wl'].items())}\n")
        fh.write("\nTRAIN quality per setup (qs = shrunk avg R, qx = shrunk ex-market avg R)\n" + q.loc[sorted(set(PRIMARY + LIVE_A + A2))].round(4).to_string() + "\n")

    stage1 = [dict(BASE, risk=r, bp=p, alloc=a) for r, p, a in itertools.product(RISKS, BPS, ALLOCS)]
    res = {}
    with Pool(4) as pool_:
        # Stage 1 on TRAIN (selection), then all windows for every config (VALID/LIVE read only for finalists in the notes)
        for b in books:
            for bk, win, nm, cfg, s in pool_.imap_unordered(_job, [(b, "TRAIN", c) for c in stage1]):
                res[(bk, win, nm)] = (cfg, s)
        sel = {}
        for b in books:
            rows = [(nm, metrics(s)) for (bk, w, nm), (c, s) in res.items() if bk == b and w == "TRAIN"]
            best = max(m["rdd"] for _, m in rows)
            near = [(nm, m) for nm, m in rows if m["rdd"] >= best - 0.05 * abs(best)]
            s1 = max(near, key=lambda x: x[1]["ret"])[0]
            ok = [(nm, m) for nm, m in rows if m["dd"] >= -10]
            s2 = max(ok, key=lambda x: x[1]["ret"])[0] if ok else s1
            sel[b] = (s1, s2)
        # Stage 2 + sensitivity, on TRAIN first (ALL depends on TRAIN)
        st2 = {}
        for b in books:
            c1 = res[(b, "TRAIN", sel[b][0])][0]
            lst = []
            for basecfg in (BASE, c1):
                for k in ("wt", "hq1", "hq2", "hb"):
                    lst.append(dict(basecfg, **{k: True}))
            st2[b] = lst
            for bk, win, nm, cfg, s in pool_.imap_unordered(_job, [(b, "TRAIN", c) for c in lst]):
                res[(bk, win, nm)] = (cfg, s)
            ref = metrics(res[(b, "TRAIN", sel[b][0])][1])["rdd"]
            good = [k for k in ("wt", "hq1", "hq2", "hb") if metrics(res[(b, "TRAIN", cfgname(dict(c1, **{k: True})))][1])["rdd"] > ref]
            allc = [dict(bc, **{k: True for k in good}) for bc in (BASE, c1)] if good else [dict(bc, wt=True, hq1=True, hq2=True, hb=True) for bc in (BASE, c1)]
            caps = [dict(BASE, cap=0.10), dict(c1, cap=0.10)]
            extra = allc + caps
            st2[b] += extra
            for bk, win, nm, cfg, s in pool_.imap_unordered(_job, [(b, "TRAIN", c) for c in extra]):
                res[(bk, win, nm)] = (cfg, s)
            info[b]["all_rules"] = good
        allcfg = {b: stage1 + st2[b] for b in books}
        jobs = [(b, w, c) for b in books for w in ("VALID", "LIVE") for c in allcfg[b]]
        for bk, win, nm, cfg, s in pool_.imap_unordered(_job, jobs, chunksize=4):
            res[(bk, win, nm)] = (cfg, s)
    out = []; daily = []
    for (b, w, nm), (c, s) in res.items():
        m = metrics(s); base = res[(b, w, cfgname(BASE))][1]
        m.update(book=b, window=w, config=nm, stage="1" if c in stage1 else "2", t_vs_base=tdiff(s, base) if nm != cfgname(BASE) else np.nan)
        out.append(m)
        daily.append(s.assign(book=b, window=w, config=nm)[["book", "window", "config", "date", "n", "R", "ret"]])
    r = pd.DataFrame(out)
    n_cfg = r.groupby("book").config.nunique()
    r.to_csv(HERE / "results.csv", index=False, float_format="%.4f")
    pd.concat(daily).to_csv(S / "daily_all.csv", index=False, float_format="%.6f")
    with open(HERE / "selection.txt", "w") as fh:
        fh.write(f"configs per book {n_cfg.to_dict()}, total {int(n_cfg.sum())}; bar = max(1.5, sqrt(2 ln N)) = {max(1.5, np.sqrt(2 * np.log(n_cfg.sum()))):.2f}\n")
        for b in books:
            fh.write(f"Book {b}: TRAIN-selected (ret/DD) {sel[b][0]}; TRAIN best return with DD>=-10% {sel[b][1]}; ALL rules (raised TRAIN ret/DD): {info[b]['all_rules']}\n")
    print(open(HERE / "selection.txt").read())


if __name__ == "__main__":
    main()
