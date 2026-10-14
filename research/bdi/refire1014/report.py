"""refire1014 step 2: first-of-day vs refire (cooldown 1 / 3 / 6 decision bars) per setup, the extras (2nd+ signals)
on their own, the pre-declared verdict (NOTES.md 1.4) and the expected extra trades/day per account.
Educational only - not financial advice.

    python research/bdi/refire1014/report.py      # reads $RF_SCR/hits.parquet -> results.csv, summary.json, table.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))
from scan import ACCOUNTS, SCR  # noqa: E402

from mcf.research import gates  # noqa: E402
from mcf.strategies.setups import refire_select  # noqa: E402

CDS = (1, 3, 6)
MIN_N = 30
DESIGN_OFF = ("MF1-945-flowsell-vwapup", "MF2-open-rsimidhi-flowsell", "MF3-open-flowsell-rsi5hi",
              "MF4-h40-open-flowsell", "CWT09-", "LIQ-", "CWT12-coil-")


def design_off(name: str) -> bool:
    # the Primary MF1-MF4 (open windows) only; their -FD versions are full-day by design
    return any(name == d or (d.endswith("-") and name.startswith(d)) for d in DESIGN_OFF)


def chains(g: pd.DataFrame, cd: int | None) -> tuple[np.ndarray, np.ndarray]:
    """Row positions of the emitted signals and a first-of-day flag. cd None = first hit of the day (dropped when
    untradeable, as LabStrategy with refire off)."""
    key = g["symbol"].to_numpy().astype(object) + "|" + g["date"].astype(str).to_numpy().astype(object)
    bar = g["bar"].to_numpy(int)
    ok = np.isfinite(g["r"].to_numpy(float))
    starts = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    ends = np.r_[starts[1:], len(g)]
    pos, first = [], []
    for a, b in zip(starts, ends):
        if cd is None:
            if ok[a]:
                pos.append(a); first.append(True)
            continue
        okb = {int(bar[i]): bool(ok[i]) for i in range(a, b)}
        posb = {int(bar[i]): i for i in range(a, b)}
        # the same chain as LabStrategy (refire_select on decision-bar numbers, untradeable bars dropped first)
        out = [posb[x] for x in refire_select([int(v) for v in bar[a:b]], cd, valid=lambda x: okb[x])]
        pos += out
        first += ([True] + [False] * (len(out) - 1)) if out else []
    return np.array(pos, int), np.array(first, bool)


def stats(g, pos, sessions):
    if not len(pos):
        return {"n": 0}
    t = pd.DataFrame({"date": g["date"].to_numpy()[pos], "r": g["r"].to_numpy(float)[pos]})
    s = gates.summary(t)
    s["per_day"] = round(len(pos) / sessions, 3)
    return s


def main():
    sts = json.load(open(SCR / "setups.json"))
    hits = pd.read_parquet(SCR / "hits.parquet").sort_values(["key", "symbol", "date", "bar"], kind="mergesort")
    sessions = int(hits["date"].nunique())
    rows = []
    for s in sts:
        g = hits[hits["key"] == s["key"]].reset_index(drop=True)
        row = {"setup": s["name"], "accounts": "/".join(s["accounts"]), "side": s["side"], "geom": s["geom"],
               "window": f"{s['window'][0]}-{s['window'][1]}", "qual_bars": len(g),
               "design_off": design_off(s["name"])}
        p0, _ = chains(g, None)
        st0 = stats(g, p0, sessions)
        row.update({f"first_{k}": st0.get(k) for k in ("n", "per_day", "exp_r", "t")})
        for cd in CDS:
            p, f = chains(g, cd)
            a, x = stats(g, p, sessions), stats(g, p[~f], sessions)
            fr = stats(g, p[f], sessions)
            row.update({f"cd{cd}_{k}": a.get(k) for k in ("n", "per_day", "exp_r", "t")})
            row.update({f"cd{cd}_x_{k}": x.get(k) for k in ("n", "per_day", "exp_r", "t", "ex_best_day")})
            row[f"cd{cd}_f_exp"] = fr.get("exp_r")
        rows.append(row)
    res = pd.DataFrame(rows)

    def verdict(r):
        ben = [cd for cd in CDS if (r[f"cd{cd}_x_n"] or 0) >= MIN_N and r[f"cd{cd}_x_exp_r"] is not None
               and r[f"cd{cd}_x_exp_r"] > 0 and r[f"cd{cd}_x_exp_r"] >= r[f"cd{cd}_f_exp"]]
        pos = [cd for cd in CDS if (r[f"cd{cd}_x_n"] or 0) and r[f"cd{cd}_x_exp_r"] is not None and r[f"cd{cd}_x_exp_r"] > 0]
        cls = "benefit" if ben else ("neutral" if pos else ("worse" if max(r[f"cd{cd}_x_n"] or 0 for cd in CDS) >= MIN_N
                                                            else ("neutral" if max(r[f"cd{cd}_x_n"] or 0 for cd in CDS) else "no-extras")))
        rec = min(ben) if ben and not r["design_off"] else None
        return pd.Series({"class": cls, "recommend_cd": rec, "refire": rec is not None})

    res = pd.concat([res, res.apply(verdict, axis=1)], axis=1)
    res.to_csv(HERE / "results.csv", index=False)
    acct = {}
    for a in ACCOUNTS:
        sub = res[res["accounts"].str.contains(a + "($|/)", regex=True)]
        rec = sub[sub["refire"]]
        extra = sum(r[f"cd{int(r['recommend_cd'])}_x_per_day"] for _, r in rec.iterrows())
        acct[a] = {"setups": int(len(sub)), "recommended_on": int(len(rec)),
                   "extra_per_day_recommended": round(float(extra), 2),
                   "first_per_day": round(float(sub["first_per_day"].sum()), 2),
                   "extra_per_day_if_all_cd1": round(float(sub["cd1_x_per_day"].fillna(0).sum()), 2)}
    summ = {"sessions": sessions, "unique_setups": len(res), "configurations": 4 * len(res),
            "classes": res["class"].value_counts().to_dict(),
            "classes_excl_design_off": res[~res["design_off"]]["class"].value_counts().to_dict(),
            "design_off": int(res["design_off"].sum()), "recommended_on": int(res["refire"].sum()), "accounts": acct}
    json.dump(summ, open(HERE / "summary.json", "w"), indent=1)
    print(json.dumps(summ, indent=1))

    def f(v, d=3):
        return "-" if v is None or (isinstance(v, float) and np.isnan(v)) else (f"{v:+.{d}f}" if isinstance(v, float) else str(v))

    lines = ["| setup | acct | geom | win | first n/day, exp, t | cd1 extras n/day, exp, t | cd3 extras | cd6 extras | "
             "cd1 all exp, t | class | refire |", "|" + "---|" * 11]
    ab = {"Primary": "P", "Testing": "T1", "Testing 2": "T2"}
    for _, r in res.iterrows():
        def x(cd):
            return f"{f(r[f'cd{cd}_x_per_day'], 2)}, {f(r[f'cd{cd}_x_exp_r'])}, {f(r[f'cd{cd}_x_t'], 2)}"
        rf = "off (design)" if r["design_off"] else (f"on cd{int(r['recommend_cd'])}" if r["refire"] else "off")
        lines.append(f"| {r['setup']} | {'/'.join(ab[a] for a in r['accounts'].split('/'))} | {r['geom']} | {r['window']} | "
                     f"{f(r['first_per_day'], 2)}, {f(r['first_exp_r'])}, {f(r['first_t'], 2)} | {x(1)} | {x(3)} | {x(6)} | "
                     f"{f(r['cd1_exp_r'])}, {f(r['cd1_t'], 2)} | {r['class']} | {rf} |")
    (HERE / "table.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
