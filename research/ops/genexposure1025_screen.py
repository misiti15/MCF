"""GEN exposure 2026-10-25: the generator's own screen code (mcf.research.generator) on recent open months, per day.

    python research/ops/genexposure1025_screen.py OUT.csv [months...]      (default 2026-08 2026-09 2026-10; 'all' = every open month)

For every GEN setup with a `gen.spec` in config/account_gen.yaml: the screen's signals (first qualifying 5-minute bar
per symbol-day inside the window, adv20 >= the spec floor, finite R - exactly screen.evaluate) per session, plus the
same signals that also pass the live universe's daily-ATR filter (atr_d / close >= 1%, universe.min_atr_pct) - the
only live universe filter the screen panel does not apply (earnings blackout and the $20M floor it does apply).
Writes one row per (setup, date): n_screen, n_atr_ok. The 2-year per_day each setup carries is the same count averaged
over all ~480 open sessions. Research only; nothing here trades. Educational only - not financial advice.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import yaml

from mcf.research.arena import data as AD
from mcf.research.generator.apply import spec_from_cfg
from mcf.research.generator.data import Panel, _blackout, build_month
from mcf.research.generator.screen import first_rows, spec_mask_idx


def main(out: str, months: list[str]) -> None:
    if months == ["all"]:
        months = list(AD.months("all"))
    lib = AD._lib()
    st = yaml.safe_load(open("config/account_gen.yaml"))["strategies"]
    specs = {n: spec_from_cfg(v) for n, v in st.items() if isinstance(v, dict) and (v.get("gen") or {}).get("spec")}
    rows, n_days = [], 0
    for m in months:      # first rows per symbol-day never cross a month: one month's panel at a time (memory)
        x = build_month(m)
        # atr% per panel row: the frame's atr_d / close, aligned like build_month's universe rows
        df = lib.load_month(m, columns=["symbol", "date", "tod", "close", "atr_d", "adv20"])
        df = df[df["adv20"].to_numpy(float) >= 20e6].reset_index(drop=True)
        df["symbol"] = df["symbol"].astype(str)
        tod = df["tod"].to_numpy()
        uni = (tod >= 950) & (tod <= 1500) & ~_blackout(df["symbol"].to_numpy(), df["date"].to_numpy())
        a = (df["atr_d"].to_numpy(float) / df["close"].to_numpy(float) * 100)[uni]
        assert len(a) == len(x["tod"]), (m, len(a), len(x["tod"]))
        del df
        P = Panel([x], [m])
        atr_ok = a >= 1.0
        n_days += P.n_days
        for name, sp in specs.items():
            idx = first_rows(P.sd, spec_mask_idx(P, sp))
            r = P.a[f"r_{sp.side}_{sp.geom}"][idx].astype(np.float64)
            idx = idx[np.isfinite(r)]
            c = pd.DataFrame({"date": P.days[P.day[idx]], "ok": atr_ok[idx]}).groupby("date").agg(
                n_screen=("ok", "size"), n_atr_ok=("ok", "sum")).reindex(sorted(P.days), fill_value=0)
            pdy = (st[name].get("gen") or {}).get("screen", {}).get("per_day")
            rows += [{"setup": name, "date": d, "n_screen": int(q.n_screen), "n_atr_ok": int(q.n_atr_ok),
                      "per_day_2y": pdy} for d, q in c.iterrows()]
        print(f"{m}: {len(a)} rows, {P.n_days} sessions", flush=True)
        del P, x
    pd.DataFrame(rows).to_csv(out, index=False)
    print("wrote", out, len(rows), "rows; sessions", n_days)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:] or ["2026-08", "2026-09", "2026-10"])   # "all" = every open month

