"""Phase 2 (owner 2026-10-08): re-score every live setup and every backlog lab module on the 2-year history, outside
the rule-19 locked block, with the gates of mcf/research/gates.py. Production costs throughout.

  lab setups   config/default.yaml type: lab (exhaustion_short, MF1-5, NS1-5) and the RW1-8 rework modules (backlog
               lab_module entries): module.mask(frame) & the YAML / docstring window & point-in-time adv20 >= min_adv;
               first qualifying bar per symbol-day; module GEOM outcome (lab R -> production R, gates.prod_r)
  heat setups  heat_fade_short / heat_fade_long: score(frame) crossing SHORT_AT / LONG_AT inside the window, adv20 >=
               min_adv, first per symbol-day, stop 1R / target 1R (= lab t1s1), as HeatStrategy
  1-minute     orb20_a, intraday_momentum: research/history2y/rescore_bt.py (production backtester), merged here
  VID1-8       GEOM None (structural hold-to-close exit + extra 1-minute features): LabStrategy cannot run them; listed
               as not scored

Outputs: research/history2y/rescore.csv, research/history2y/RESCORE.md, research/history2y/data/lab_trades.parquet.
    python research/history2y/rescore.py [--skip-scan]
Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from lib import DATA, LOCKED_MONTHS, load_month, months, regimes  # noqa: E402
from mcf.research import gates as G  # noqa: E402

TRADES = DATA / "lab_trades.parquet"
UNSEEN_BEFORE = "2026-03-10"     # first bar of any data MCF had before rule 19 (data/cache_q2 warm-up)

# configurations tried per lineage (sources: SWARM.md, HEAT_STUDY.md, primitives/marcoflow/NOTES.md, owner1008 config
# comment, research/setup_screen.json, research/backlog.jsonl configs_tried)
TRIES = {"exhaustion_short": 855_600, "heat_fade_short": 19_200, "heat_fade_long": 19_200, "orb20_a": 15,
         "intraday_momentum": 15, **{f"MF{i}": 8_012 for i in range(1, 6)}, **{f"NS{i}": 7_374 for i in range(1, 6)}}
TRY_SRC = {"exhaustion_short": "setups2 swarm", "heat_fade_short": "heat study", "heat_fade_long": "heat study",
           "orb20_a": "setup screen (15 setups)", "intraday_momentum": "setup screen (15 setups)"}


def _load(path: Path, name: str):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def setups() -> list[dict]:
    cfg = yaml.safe_load((ROOT / "config/default.yaml").read_text())["strategies"]
    out = []
    for name, p in cfg.items():
        if not p.get("enabled"):
            continue
        kind = p.get("type") or "bt"
        short = name.split("-")[0]
        base = {"setup": name, "group": "live original" if not re.match(r"^(MF|NS)\d", name) else "live probation",
                "tries": TRIES.get(short, TRIES.get(name)), "tries_src": TRY_SRC.get(name, "lineage scan")}
        if kind == "lab":
            out.append({**base, "kind": "lab", "path": ROOT / p["module"], "min_adv": float(p.get("min_adv", 0)),
                        "window": tuple(p.get("window") or (950, 1500))})
        elif kind == "heat":
            out.append({**base, "kind": "heat", "path": ROOT / p["formula"], "min_adv": float(p.get("min_adv", 0)),
                        "window": tuple(p.get("window") or (950, 1500)), "sides": p.get("sides", "both")})
        else:
            out.append({**base, "kind": "bt"})
    bl = {e.get("lab_module"): e for e in map(json.loads, (ROOT / "research/backlog.jsonl").read_text().splitlines()) if e.get("lab_module")}
    for lm, e in bl.items():
        p = ROOT / lm
        txt = p.read_text()
        mn = re.search(r"min_adv (\d+)", txt)
        w = re.search(r"window \[(\d+), (\d+)\]", txt)
        out.append({"setup": p.stem.split("-")[0] + " " + e["id"], "group": "backlog RW (lab_module)", "kind": "lab", "path": p,
                    "min_adv": float(mn.group(1)) if mn else 0.0, "window": (int(w.group(1)), int(w.group(2))) if w else (950, 1500),
                    "tries": e.get("configs_tried"), "tries_src": "backlog configs_tried"})
    for p in sorted((ROOT / "research/bdi/videos").glob("VID*.py")):
        out.append({"setup": p.stem.split("-")[0], "group": "BDI video", "kind": "vid", "path": p, "tries": 692_484,
                    "tries_src": "video digests Vol I+II"})
    return out


def scan(sts: list[dict]) -> pd.DataFrame:
    mods = {}
    for s in sts:
        if s["kind"] in ("lab", "heat"):
            m = _load(s["path"], "m_" + re.sub(r"\W", "_", s["setup"]))
            s["side"] = getattr(m, "SIDE", None) if s["kind"] == "lab" else s["sides"]
            s["geom"] = getattr(m, "GEOM", "t1s1") if s["kind"] == "lab" else "t1s1"
            mods[s["setup"]] = m
    rows, t0 = [], time.time()
    for mo in months():
        df = load_month(mo)
        tod, adv = df["tod"].to_numpy(), df["adv20"].fillna(0).to_numpy()
        for s in sts:
            if s["kind"] not in ("lab", "heat"):
                continue
            m = mods[s["setup"]]
            lo, hi = s["window"]
            base = (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (adv >= s["min_adv"])
            with np.errstate(invalid="ignore"):
                if s["kind"] == "lab":
                    legs = [(np.asarray(m.mask(df), bool) & base, s["side"], s["geom"])]
                else:
                    sc = np.asarray(m.score(df), float)
                    legs = []
                    if s["sides"] in ("both", "long") and getattr(m, "LONG_AT", None) is not None:
                        legs.append((base & (sc >= m.LONG_AT), "long", "t1s1"))
                    if s["sides"] in ("both", "short") and getattr(m, "SHORT_AT", None) is not None:
                        legs.append((base & (sc <= m.SHORT_AT), "short", "t1s1"))
            for mk, side, geom in legs:
                tr = G.lab_trades(df, mk, side, geom)
                tr["setup"] = s["setup"]
                rows.append(tr)
        print(f"{mo}: {len(df)} rows scanned ({time.time() - t0:.0f}s)", flush=True)
        del df
    x = pd.concat(rows, ignore_index=True)
    x["symbol"] = x["symbol"].astype(str)
    x.to_parquet(TRADES, index=False)
    return x


def bt_trades() -> pd.DataFrame:
    p = DATA / "bt_trades.parquet"
    if not p.exists():
        return pd.DataFrame(columns=["date", "symbol", "tod", "r", "setup"])
    b = pd.read_parquet(p)
    et = pd.to_datetime(b["entry_time"])
    b = b[et.dt.hour * 100 + et.dt.minute >= 950]          # live takes no entries before 09:50 (as the screen)
    return pd.DataFrame({"date": pd.to_datetime(b["date"]).dt.date, "symbol": b["symbol"].astype(str),
                         "tod": (et.dt.hour * 100 + et.dt.minute).to_numpy(), "r": b["r_multiple"].astype(float),
                         "setup": b["strategy"]})


def evaluate(sts, trades, reg) -> pd.DataFrame:
    rows = []
    for s in sts:
        base = {"setup": s["setup"], "group": s["group"], "kind": s["kind"], "side": s.get("side"), "geom": s.get("geom"),
                "min_adv": s.get("min_adv"), "window": s.get("window"), "tries": s.get("tries"), "tries_src": s.get("tries_src")}
        if s["kind"] == "vid":
            rows.append({**base, "verdict": "not scored", "failed_gates": "structural exit (GEOM None) and extra 1-minute "
                         "features: LabStrategy cannot run it"})
            continue
        tr = trades[trades["setup"] == s["setup"]]
        if s["kind"] == "bt" and not len(tr):
            rows.append({**base, "verdict": "not scored", "failed_gates": "backtester run missing"})
            continue
        o = G.summary(tr)
        rs = G.regime_split(tr, reg)
        wf = G.walk_forward(tr, months=sorted(set(pd.PeriodIndex(pd.to_datetime(list(reg.index)), freq="M").astype(str))),
                            exclude_months=LOCKED_MONTHS)
        dsr = G.deflated_sharpe(tr.groupby("date")["r"].sum().to_numpy(), s.get("tries") or 1)
        v, fails = G.verdict(o, rs, wf, s.get("tries") or 1)
        un = G.summary(tr[pd.to_datetime(tr["date"]) < pd.Timestamp(UNSEEN_BEFORE)]) if len(tr) else {"n": 0}
        q = G.per_quarter(tr)
        rows.append({**base, "n": o.get("n", 0), "days": o.get("days"), "per_day": round(o["n"] / o["days"], 2) if o.get("days") else None,
                     "win_rate": o.get("win_rate"), "exp_r": o.get("exp_r"), "t": o.get("t"), "t_required": G.t_required(s.get("tries") or 1),
                     "ex_best_day": o.get("ex_best_day"), "green_days": o.get("green_days"),
                     "up_n": rs["up"].get("n", 0), "up_exp": rs["up"].get("exp_r"), "up_t": rs["up"].get("t"),
                     "flat_n": rs["flat"].get("n", 0), "flat_exp": rs["flat"].get("exp_r"), "flat_t": rs["flat"].get("t"),
                     "down_n": rs["down"].get("n", 0), "down_exp": rs["down"].get("exp_r"), "down_t": rs["down"].get("t"),
                     "wf_folds": wf["n_folds"], "wf_share_pos": wf["share_positive"],
                     "wf_trailing_on_exp": wf["trailing_on"].get("exp_r"), "dsr": dsr.get("dsr"),
                     "unseen_n": un.get("n", 0), "unseen_exp": un.get("exp_r"), "unseen_t": un.get("t"),
                     "per_quarter": json.dumps({k: v["exp_r"] for k, v in q.items()}),
                     "per_quarter_n": json.dumps({k: v["n"] for k, v in q.items()}),
                     "verdict": v, "failed_gates": "; ".join(fails)})
    return pd.DataFrame(rows)


def report(res: pd.DataFrame, reg: pd.DataFrame, trades: pd.DataFrame) -> str:
    cuts = reg.attrs.get("cuts", (np.nan, np.nan))
    sc = res[res["verdict"] != "not scored"]
    cnt = res["verdict"].value_counts().to_dict()
    L = ["# Re-score on the 2-year history (rule 19)", "",
         "*Educational only - not financial advice. Lab and backtest results only; nothing here is a live result.*", "",
         f"**Setups scored: {len(sc)}** of {len(res)} listed (not scored: {len(res) - len(sc)}, the 8 BDI video modules, whose "
         "structural exit and extra 1-minute features LabStrategy cannot run). Each setup is a fixed rule: nothing was "
         "fitted on this history, so the configurations tried on it are the "
         f"{len(sc)} setups themselves; the lineages' own search sizes set each t bar.", "",
         f"Verdicts: keep {cnt.get('keep', 0)}, rework {cnt.get('rework', 0)}, retire {cnt.get('retire', 0)}, not scored {cnt.get('not scored', 0)}.", "",
         "## Data and method",
         f"- History: {min(reg.index)} .. {max(reg.index)}, {len(reg)} sessions outside the locked block, 1,226 lab symbols (today's list: "
         "survivorship bias - names delisted or no longer liquid are missing). The rule-19 locked block 2024-11-01..2025-02-28 is excluded.",
         "- Lab setups: module mask on the setups2-pipeline frames, the YAML window, point-in-time 20-day ADV >= the setup's min_adv, "
         "first qualifying bar per symbol-day, R = 0.25 x daily ATR, exit by 15:55, production costs (1c + 1 bps per side, the exit "
         "side free on target fills, +2c on stops).",
         "- orb20_a and intraday_momentum: the production backtester (as research/setup_screen.py), entries from 09:50.",
         f"- Regimes: universe median open-to-close per session, terciles over the open history: down <= {cuts[0]:.3f}%, up >= {cuts[1]:.3f}% "
         f"({(reg.regime == 'up').sum()} up / {(reg.regime == 'flat').sum()} flat / {(reg.regime == 'down').sum()} down sessions).",
         f"- Gates (mcf/research/gates.py): exp > 0; day-clustered t >= max(1.5, sqrt(2 ln N)) with N = configurations tried in the lineage; "
         f"exp > 0 in up AND down sessions (n >= {G.REGIME_MIN_N} each); walk-forward (3-month train, 1-month test, step 1) positive "
         f"share >= {G.WF_MIN_SHARE} over folds with n >= {G.FOLD_MIN_N}.",
         f"- 'Unseen' = sessions before {UNSEEN_BEFORE} (outside the locked block): data no MCF study had loaded before rule 19. "
         "Sessions from 2026-03-10 on include every lineage's train/valid and the two old holdouts, so they are in-sample for these setups.", "",
         "## Results (failures included)", "",
         "| Setup | Group | Side/geom | n | /day | win | exp R | t | t req | up exp (n) | flat exp | down exp (n) | WF +share | unseen exp (n, t) | Verdict | Failed gates |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    order = {"keep": 0, "rework": 1, "retire": 2, "not scored": 3}
    f = lambda v, d=3: "–" if v is None or (isinstance(v, float) and not np.isfinite(v)) else (f"{v:+.{d}f}" if isinstance(v, float) else str(v))
    for _, r in res.assign(o=res["verdict"].map(order)).sort_values(["o", "group", "setup"]).iterrows():
        if r["verdict"] == "not scored":
            L.append(f"| {r.setup} | {r.group} | short/tx | – | – | – | – | – | – | – | – | – | – | – | not scored | {r.failed_gates} |")
            continue
        L.append(f"| {r.setup} | {r.group} | {r.side}/{r.geom or 'bt'} | {int(r.n)} | {r.per_day} | {r.win_rate} | {f(r.exp_r)} | {r.t} | "
                 f"{r.t_required} | {f(r.up_exp)} ({int(r.up_n)}) | {f(r.flat_exp)} | {f(r.down_exp)} ({int(r.down_n)}) | {r.wf_share_pos} | "
                 f"{f(r.unseen_exp)} ({int(r.unseen_n)}, {r.unseen_t}) | **{r.verdict}** | {r.failed_gates} |")
    L += ["", "## Per-quarter expectancy (R after costs)", ""]
    qs = sorted({q for s in sc["per_quarter"] for q in json.loads(s)})
    L.append("| Setup | " + " | ".join(qs) + " |")
    L.append("|---|" + "---|" * len(qs))
    for _, r in sc.sort_values("setup").iterrows():
        d, n = json.loads(r.per_quarter), json.loads(r.per_quarter_n)
        L.append(f"| {r.setup} | " + " | ".join(f"{d[q]:+.3f} ({n[q]})" if q in d else "–" for q in qs) + " |")
    L += ["", "Files: `research/history2y/rescore.csv` (all columns incl. deflated Sharpe and the trailing-on walk-forward variant), "
          "trades in `research/history2y/data/` (git-ignored)."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-scan", action="store_true")
    a = ap.parse_args()
    sts = setups()
    for s in sts:
        if s["kind"] in ("lab", "heat"):
            m = _load(s["path"], "m_" + re.sub(r"\W", "_", s["setup"]))
            s["side"] = getattr(m, "SIDE", None) if s["kind"] == "lab" else s["sides"]
            s["geom"] = getattr(m, "GEOM", "t1s1") if s["kind"] == "lab" else "t1s1"
    lab = pd.read_parquet(TRADES) if a.skip_scan and TRADES.exists() else scan(sts)
    lab["date"] = pd.to_datetime(lab["date"]).dt.date
    trades = pd.concat([lab, bt_trades()], ignore_index=True)
    reg = regimes()
    trades = trades[trades["date"].isin(set(reg.index))]
    res = evaluate(sts, trades, reg)
    res.to_csv(Path(__file__).parent / "rescore.csv", index=False)
    (Path(__file__).parent / "RESCORE.md").write_text(report(res, reg, trades))
    pd.set_option("display.width", 250)
    print(res[["setup", "n", "exp_r", "t", "t_required", "up_exp", "down_exp", "wf_share_pos", "unseen_exp", "verdict"]].to_string())
