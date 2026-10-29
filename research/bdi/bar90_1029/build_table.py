"""bar90_1029: one candidate table from every stored source, pre-screened against BAR90 (RESEARCH_RULES 22).

BAR90: day-clustered t >= 0.9 x max(1.5, sqrt(2 ln N)) (never below 1.35), N = lineage tries (all prior tries);
walk-forward positive months >= 54%; exp > 0 in up AND down sessions (rule 19, n >= 30 each where the source
stores n); beats random where stored. The stored lineage bar of each study is used (N only grows, so this is
lenient by at most a few hundredths), and N_now from the latest study touching the lineage where known.

Read-only over research/ and docs/live/assignments.json. Writes candidates.csv here.
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
LIVE = {s for v in json.load(open(ROOT / "docs/live/assignments.json"))["accounts"].values() for s in v}


def bar_full(n):
    return max(1.5, math.sqrt(2 * math.log(max(n, 1))))


def bar90_from_bar(b):
    return max(1.35, 0.9 * b)


def n_from_bar(b):
    return float(np.exp(b * b / 2)) if b and b > 1.5 else np.nan


# lineage N now (all prior tries; the largest count reported by any study on that lineage)
LINEAGE_N = {
    "L3": 316_000, "ST": 227_400, "NS": 165_764, "RW": 934_562, "RW6/NS2 (rw81430)": 82_102, "EXH/RW2": 934_562,
    "CWT14": 121_400, "CWT04-B1 (cwt)": n_from_bar(5.074), "MISC (HL/HS)": n_from_bar(4.569), "MF": n_from_bar(4.80),
    "arena-am": 43_457, "arena-mid-long": 74_087, "arena-mid-short": 135_277, "arena-pm": 189_093,
    "arena-index-etf": 266_882, "HL-T75 (tf1019)": 34_108, "generator": 27_228, "earnings (daily)": 414,
}

rows: list[dict] = []


def add(**k):
    rows.append(k)


def best(g, col):
    v = pd.to_numeric(g[col], errors="coerce")
    return None if v.notna().sum() == 0 else g.loc[v.idxmax()]


def num(x):
    try:
        x = float(x)
        return x if np.isfinite(x) else np.nan
    except Exception:
        return np.nan


# --- 1. swarm1017 reworks (2-yr, gate columns stored) -----------------------------------------------------------
st = pd.read_csv(ROOT / "research/swarm1017/rework-st/finalists.csv")
for _, r in st.iterrows():
    lin = "L3" if str(r.fam) == "L3" else "ST"
    add(source="swarm1017/rework-st/finalists", id=f"{r.parent}|{r.filters}|{r.side}|{r.geom}|{r.win}|refire={r.refire}",
        lineage=lin, side=r.side, n=r.n_all, exp_train=r.exp_tr, exp_valid=r.exp_va, exp_2y=r.exp_all, t=r.t_all,
        up=r.up_exp, down=r.dn_exp, n_up=r.up_n, n_down=r.dn_n, wf=r.wf_share, ex_best_day=r.ex_best_day,
        per_day=r.n_all / 426, bar_stored=r.bar, beats_random=bool(r.g_random))
ns = pd.read_csv(ROOT / "research/swarm1017/rework-ns/finalists.csv")
for _, r in ns.iterrows():
    add(source="swarm1017/rework-ns/finalists", id=f"{r.parent}|{r.filters}|{r.side}|{r.geom}|{r.win}|refire={r.refire}",
        lineage="NS", side=r.side, n=r.n_all, exp_train=r.exp_tr, exp_valid=r.exp_va, exp_2y=r.exp_all, t=r.t_all,
        up=r.up_exp, down=r.dn_exp, n_up=r.up_n, n_down=r.dn_n, wf=r.wf_share, ex_best_day=r.ex_best_day,
        per_day=r.n_all / 426, bar_stored=4.90, beats_random=bool(r.g_random))
rw = pd.read_csv(ROOT / "research/swarm1017/rework-rw/finalists.csv")
for _, r in rw.iterrows():
    add(source="swarm1017/rework-rw/finalists", id=f"{r.parent}|{r.desc}|{r.side}|{r.geom}|{r.window}",
        lineage="EXH/RW2" if r.lineage == "EXH" else "RW6/NS2 (rw81430)", side=r.side, n=r.n_all, exp_train=r.exp_tr,
        exp_valid=r.exp_va, exp_2y=r.exp_all, t=r.t_all, up=r.reg_up, down=r.reg_down, n_up=r.n_up, n_down=r.n_down,
        wf=r.wf_share, ex_best_day=r.ex_best_day, per_day=r.per_day, bar_stored=r.bar, beats_random=r.xt_all > 2)
mf = pd.read_csv(ROOT / "research/swarm1017/rework-mf/finalists.csv")
for _, r in mf.iterrows():
    add(source="swarm1017/rework-mf/finalists", id=f"{r.parent}|{r.desc}|{r.side}|{r.geom}|{r.window}", lineage="MF",
        side=r.side, n=r.n_all, exp_train=r.exp_tr, exp_valid=r.exp_va, exp_2y=r.exp_all, t=r.t_all, up=r.reg_up,
        down=r.reg_down, wf=r.wf_share, ex_best_day=r.ex_best_day, per_day=r.per_day, bar_stored=4.80,
        beats_random=r.xt_all > 2)
mi = pd.read_csv(ROOT / "research/swarm1017/rework-misc/nearmiss.csv")
for _, r in mi.iterrows():
    add(source="swarm1017/rework-misc/nearmiss", id=f"{r.fam}|{r.cfg}|{r.side}|{r.geom}|{r.window}", lineage="MISC (HL/HS)",
        side=r.side, n=r.n_all, exp_train=r.exp_tr, exp_valid=r.exp_va, exp_2y=r.exp_all, t=r.t_all, up=r.up_exp,
        down=r.down_exp, n_down=r.down_n, wf=r.wf_share, ex_best_day=r.ex_best_day, per_day=r.per_day,
        bar_stored=r.t_bar, beats_random=bool(r.beat_random))
cw = pd.read_csv(ROOT / "research/swarm1017/rework-cwt/finalists.csv")
for _, r in cw.iterrows():
    add(source="swarm1017/rework-cwt/finalists", id=f"{r.fam}|{r.vid}|{r.f1}|{r.f2}|{r.side}|{r.exit}|{r.win}",
        lineage="CWT04-B1 (cwt)", side=r.side, n=r.n_all, exp_train=r.exp_tr, exp_valid=r.exp_va, exp_2y=r.exp_all,
        t=r.t_all, up=r.reg_up, down=r.reg_dn, n_up=r.reg_up_n, n_down=r.reg_dn_n, wf=r.wf_share,
        ex_best_day=r.ex_best_day, best_share=r.max_day_share, per_day=r.per_day, bar_stored=r.bar,
        beats_random=bool(r.g_rand))
c14 = pd.read_csv(ROOT / "research/swarm1017/rework-cwt14/results.csv")
c14 = c14[c14.cand.astype(str) == "True"] if (c14.cand.astype(str) == "True").any() else c14.nlargest(20, "t_all")
for _, r in c14.iterrows():
    add(source="swarm1017/rework-cwt14/results", id=f"{r.L}|p{r.p}|k{r.k}|{r.filters}|{r.side}|{r.exit}|{r.win}",
        lineage="CWT14", side=r.side, n=r.n_all, exp_train=r.exp_tr, exp_valid=r.exp_va, exp_2y=r.exp_all, t=r.t_all,
        up=r.up_exp, down=r.down_exp, wf=r.wf_share, ex_best_day=r.ex_best_day, per_day=r.n_all / 426,
        bar_stored=r.bar, beats_random=r.xt_all > 2)

# --- 2. arenas (stored train / valid; combined t estimated) ------------------------------------------------------
ar = OUT / "arena_bar90.csv"
if ar.exists():
    for _, r in pd.read_csv(ar).iterrows():
        add(source=f"swarm1017/{r.arena}", id=f"{r.conds}|{r.window}|{r.geom}", lineage=r.arena.replace("-short", "")
            if "am" in r.arena else r.arena, side=r.get("side", "short" if "short" in r.arena else "long"),
            n=num(r.get("tr_n", np.nan)) + num(r.get("va_n", np.nan)), exp_train=r.get("tr_exp"),
            exp_valid=r.get("va_exp"), t=r.t_all_est, bar_stored={"arena-am-short": 4.62, "arena-pm-both": 4.93}.get(r.arena, 4.9),
            note="arena stored-pass (t est.)")

# --- 3. tf1019 near-miss, trendguard, cutoff, swarm1010 w1/w2, rescore (gates columns) --------------------------
tf = pd.read_csv(ROOT / "research/tf1019/nearmiss/results.csv")
for s, g in tf.groupby("setup"):
    r = best(g, 't')
    if r is None:
        continue
    add(source="tf1019/nearmiss", id=f"{s}|{r.minutes}m|{r.variant}", lineage="HL-T75 (tf1019)" if "HL" in s else s,
        side="short" if "short" in s else "long", n=r.n, exp_train=r.exp_train, exp_valid=r.exp_valid, exp_2y=r.exp_r,
        t=r.t, up=r.up_r, down=r.down_r, n_up=r.up_n, n_down=r.down_n, wf=r.wf_share, per_day=r.per_day,
        bar_stored=r.t_required, beats_random=r.excess_t > 2, live=s in LIVE)
tg = pd.read_csv(ROOT / "research/bdi/trendguard/results.csv")
for s, g in tg.groupby("setup"):
    r = best(g, 't')
    if r is None:
        continue
    add(source="trendguard", id=f"{s}|{r.guard}|{r.exit}", lineage=str(r.lineage), side=r.side, n=r.n, exp_2y=r.exp_r,
        t=r.t, up=r.up_exp, down=r.down_exp, n_up=r.up_n, n_down=r.down_n, wf=r.wf_share_pos,
        ex_best_day=r.ex_best_day, per_day=r.per_day, bar_stored=r.t_required, n_lineage=r.tries)
for f, src in [("research/bdi/cutoff/results.csv", "cutoff"), ("research/history2y/rescore.csv", "history2y/rescore")]:
    d = pd.read_csv(ROOT / f)
    for s, g in d.groupby("setup"):
        tcol = "t"
        r = best(g, tcol)
        if r is None:
            continue
        add(source=src, id=f"{s}|{r.get('set', r.get('window', ''))}", lineage=s, side=r.get("side", ""), n=r.n,
            exp_2y=r.exp_r, t=r.t, up=r.up_exp, down=r.down_exp, n_up=r.up_n, n_down=r.down_n,
            wf=r.get("wf_share", r.get("wf_share_pos")), ex_best_day=r.ex_best_day, per_day=r.per_day,
            bar_stored=num(r.get("t_req", r.get("t_required"))), live=s.split("|")[0] in LIVE or s in LIVE)
w1 = pd.read_csv(ROOT / "research/swarm1010/w1_variants/results.csv")
for s, g in w1.groupby("family"):
    r = best(g, 't')
    if r is None:
        continue
    add(source="swarm1010/w1_variants", id=f"{s}|{r.stage}|{r.variant}|{r.geom}", lineage=str(r.lineage), side=r.side,
        n=r.n, exp_2y=r.exp, t=r.t, up=r.exp_up, down=r.exp_down, n_up=r.n_up, n_down=r.n_down, wf=r.wf,
        ex_best_day=r.ex_best_day, per_day=r.per_day, bar_stored=r.t_required)
w2 = pd.read_csv(ROOT / "research/swarm1010/w2_neutral/results.csv")
r = w2.loc[w2.t.idxmax()]
add(source="swarm1010/w2_neutral", id=f"{r.part}|{r.list}|{r.set}|{r.side}|{r.geom}|{r.hedge}", lineage="w2 hedged",
    side=r.side, n=r.n, exp_2y=r.exp_r, t=r.t, up=r.up_exp, down=r.down_exp, n_up=r.up_n, n_down=r.down_n,
    wf=r.wf_share, ex_best_day=r.ex_best_day, bar_stored=r.t_req)

# --- 4. swarm15_1029 (latest variant swarm of the 15 most-traded live setups) -------------------------------------
s15 = pd.read_csv(ROOT / "research/bdi/swarm15_1029/results.csv")
for s, g in s15.groupby("setup"):
    r = best(g, 't_tv')
    if r is None:
        continue
    add(source="bdi/swarm15_1029", id=f"{s}|{r['var']}|{r.knob}", lineage=s, side="short" if "short" in s else "long",
        n=r.n_tv, exp_train=r.exp_train, exp_valid=r.exp_valid, exp_2y=r.exp_tv, t=r.t_tv, up=r.up, down=r.down,
        ex_best_day=r.ex_best_day, best_share=r.best_share, per_day=r.per_day_tv, bar_stored=r.bar,
        n_lineage=r.lineage_N)

# --- 5. top5 (2-yr, per-setup best variant per study) ------------------------------------------------------------
for f in sorted((ROOT / "research/bdi").glob("top5_10*/results.csv")):
    d = pd.read_csv(f)
    if "t_tv" not in d or "setup" not in d:
        continue
    for s, g in d.groupby("setup"):
        g = g[pd.to_numeric(g.t_tv, errors="coerce").notna()]
        if not len(g):
            continue
        r = best(g, 't_tv')
        if r is None:
            continue
        add(source=f"bdi/{f.parent.name}", id=f"{s}|{r.get('variant', r.get('var', r.get('config', '')))}", lineage=s,
            side="short" if "short" in s else "long", n=r.get("n_tv"), exp_train=r.get("exp_train"),
            exp_valid=r.get("exp_valid"), exp_2y=r.exp_tv, t=r.t_tv, up=r.get("up"), down=r.get("down"),
            ex_best_day=r.get("ex_best_day"), per_day=r.get("per_day_tv"),
            bar_stored=num(r.get("bar_lineage", np.nan)) if "bar_lineage" in r else 4.8)

# --- 6. generator (27,228 specs; top-50 finalists and picks of every run) -----------------------------------------
for f in sorted((ROOT / "research/generator/runs").glob("*.json")):
    d = json.load(open(f))
    cands = list(d.get("top50_finalists", []))
    cands += [dict(p.get("screen", {}), name=p["name"]) for p in d.get("picks", [])]
    for x in cands:
        a = x.get("all") or {}
        tr, va = x.get("train", {}), x.get("valid", {})
        t = a.get("t")
        if t is None and tr.get("n") and va.get("n") and tr.get("t") and va.get("t"):
            n_ = tr["n"] + va["n"]
            e_ = (tr["n"] * tr["exp_r"] + va["n"] * va["exp_r"]) / n_
            se = math.sqrt((tr["n"] * tr["exp_r"] / tr["t"]) ** 2 + (va["n"] * va["exp_r"] / va["t"]) ** 2) / n_
            t = e_ / se if se else np.nan
        add(source=f"generator/{f.stem}", id=x.get("name", x.get("key")), lineage="generator",
            side=(x.get("spec") or {}).get("side", "long" if str(x.get("name", "")).endswith("long") else "short"),
            n=(tr.get("n") or 0) + (va.get("n") or 0), exp_train=tr.get("exp_r"), exp_valid=va.get("exp_r"),
            exp_2y=a.get("exp_r"), t=t, up=x.get("exp_up"), down=x.get("exp_down"), per_day=x.get("per_day"),
            bar_stored=bar_full(27_228), live=x.get("name") in LIVE)

# --- 7. backlog: every entry, parsed (status, N, looks, best t mentioned) -----------------------------------------
for line in open(ROOT / "research/backlog.jsonl"):
    e = json.loads(line)
    txt = f"{e.get('hypothesis', '')} {e.get('notes', '')}"
    ts = [float(x) for x in re.findall(r"\bt[ =(]*(-?[0-9]+\.[0-9]+)", txt)]
    bars = [float(x) for x in re.findall(r"bar[^0-9]{0,12}([0-9]\.[0-9]+)", txt)]
    add(source="backlog", id=e["id"], lineage=e.get("parent") or e["id"], side="", status=e["status"],
        n_lineage=e.get("configs_tried"), looks=e.get("holdout_look"), t=max(ts) if ts else np.nan,
        bar_stored=max(bars) if bars else np.nan, note="t = largest t quoted in the entry text (parsed, may be a "
        "train-only / improvement t)", category=e.get("category"))

df = pd.DataFrame(rows)
for c in ["n", "exp_train", "exp_valid", "exp_2y", "t", "up", "down", "n_up", "n_down", "wf", "ex_best_day",
          "per_day", "bar_stored", "n_lineage"]:
    df[c] = pd.to_numeric(df.get(c), errors="coerce")
KEYS = [("CWT14", "CWT14"), ("L3", "L3"), ("exhaustion", "EXH/RW2"), ("RW2", "EXH/RW2"), ("RW", "RW"), ("MF", "MF"),
        ("NS", "NS"), ("ST", "ST"), ("heat_fade", "MISC (HL/HS)"), ("CWT04", "CWT04-B1 (cwt)"), ("CWT12-coil", "coil"),
        ("LIQ", "LIQ"), ("primary", "RW")]
LINEAGE_N.update({"coil": 639, "LIQ": 7_757})


def key_lineage(r):
    if r.source != "backlog":
        return r.lineage
    for k, v in KEYS:
        if k in str(r.id) or k in str(r.lineage):
            return v
    return r.lineage


df["lineage_root"] = df.apply(key_lineage, axis=1)
df["N_now"] = df.lineage_root.map(LINEAGE_N)
df.loc[df.source != "backlog", "N_now"] = df.loc[df.source != "backlog", "lineage"].map(LINEAGE_N)
df["N_now"] = df[["N_now", "n_lineage"]].max(axis=1)
df["N_now"] = df.N_now.fillna(df.bar_stored.map(n_from_bar))
df["bar_full"] = [max(b if np.isfinite(b) else 0, bar_full(n) if np.isfinite(n) else 0) or np.nan
                  for b, n in zip(df.bar_stored, df.N_now)]
df["bar90"] = df.bar_full.map(lambda b: bar90_from_bar(b) if np.isfinite(b) else np.nan)
df["live"] = df.get("live", False).fillna(False).astype(bool) | df.id.astype(str).str.split("|").str[0].isin(LIVE)


def verdict(r):
    if r.source == "backlog":
        if r.status in ("holdout_failed", "failed_locked"):
            return "excluded: failed a locked/holdout look"
        if not np.isfinite(r.t):
            return "no stored t"
        return "parsed only" if r.t < (r.bar90 if np.isfinite(r.bar90) else 1.35) else "parsed t >= bar90: check"
    fails = []
    if not (r.exp_2y > 0 or (np.isfinite(r.exp_train) and r.exp_train > 0 and r.exp_valid > 0)):
        fails.append("exp<=0")
    if np.isfinite(r.exp_train) and np.isfinite(r.exp_valid) and (r.exp_train <= 0 or r.exp_valid <= 0):
        fails.append("train or valid <= 0")
    if not (r.t >= r.bar90):
        fails.append(f"t {r.t:.2f} < {r.bar90:.2f}")
    if not (r.up > 0 and r.down > 0):
        fails.append("regime")
    elif np.isfinite(r.n_down) and r.n_down < 30:
        fails.append("regime n_down<30")
    if np.isfinite(r.wf) and r.wf < 0.54:
        fails.append("wf<0.54")
    if r.live:
        fails.append("live")
    return "clears BAR90 (stored)" if not fails else "; ".join(fails)


df["verdict"] = df.apply(verdict, axis=1)
df.to_csv(OUT / "candidates.csv", index=False)
print("rows", len(df), "| by source family:")
print(df.source.str.split("/").str[0].value_counts().to_string())
print(df.verdict.str.split(";").str[0].str.replace(r"t [-0-9.]+ < [0-9.]+", "t < bar90", regex=True)
      .value_counts().head(20).to_string())
print(df[df.verdict.str.startswith(("clears", "parsed t"))][["source", "id", "lineage", "t", "bar90", "status",
                                                               "verdict"]].to_string())
