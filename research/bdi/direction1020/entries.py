"""(Copied unchanged from bdi1019/entries.py for direction1020.) History entries for the setups that traded live in Primary / Testing 1 over 2026-10-06..10-19 (PLAN.md), in their
current config form, on the history2y 5-min lab frames (open months only; lib.load_month refuses the locked block).
Method of research/history2y/rescore.py (gates.lab_trades: first bar per symbol-day, production costs, tod entry costs).
Writes <scratch>/entries.parquet and setups_used.csv. Usage: python entries.py <scratch>. Educational only - not financial advice."""
import importlib.util
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path("/home/user/MCF")
OUT = Path(__file__).resolve().parent
S = Path(sys.argv[1])
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
from lib import DATA, load_month, months  # noqa: E402
from mcf.research import gates as G  # noqa: E402

LOCK = ("2024-11-01", "2025-02-28")
EXCLUDE = {"intraday_momentum"}          # trades index ETFs: the veto is definitional


def live_setups():
    names = {}
    for br, acct in (("mcf-data", "primary"), ("mcf-data-testing", "testing1")):
        db = S / f"{br}.db"
        if not db.exists():
            db.write_bytes(subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:journal.db"], capture_output=True, check=True).stdout)
        t = pd.read_sql("select date, strategy from trades", sqlite3.connect(db))
        ds = sorted(t.date.unique())[-10:]
        for k, n in t[t.date.isin(ds)].strategy.value_counts().items():
            names.setdefault(k, {})[acct] = int(n)
    return names


def spec(name):
    d = yaml.safe_load((ROOT / "config/default.yaml").read_text())["strategies"]
    t = yaml.safe_load((ROOT / "config/account_testing.yaml").read_text())["strategies"]
    p = {**d.get(name, {}), **t.get(name, {})}
    en = bool(t.get(name, {}).get("enabled") or d.get(name, {}).get("enabled"))
    return p, en


def load(path, nm):
    sys.path.insert(0, str(path.parent))
    sp = importlib.util.spec_from_file_location(nm, path); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return m


if __name__ == "__main__":
    live = live_setups()
    sts, skipped = [], []
    for name, acc in sorted(live.items()):
        p, en = spec(name)
        kind = p.get("type")
        if name in EXCLUDE or name.startswith("IDX"):
            skipped.append((name, "index ETF setup (excluded by plan)")); continue
        if not en:
            skipped.append((name, "not enabled in current config (replaced by its -FD version or retired)")); continue
        if kind == "lab":
            m = load(ROOT / p["module"], "m_" + re.sub(r"\W", "_", name))
            if getattr(m, "GEOM", "t1s1") not in ("t1s1", "t05s1", "t1s05"):
                skipped.append((name, f"structural exit GEOM {m.GEOM}: no frame outcome")); continue
            sts.append(dict(setup=name, kind="lab", m=m, side=m.SIDE, geom=getattr(m, "GEOM", "t1s1"), acc=acc,
                            min_adv=float(p.get("min_adv", 0)), window=tuple(p.get("window") or (950, 1500))))
        elif kind == "heat":
            m = load(ROOT / p["formula"], "m_" + re.sub(r"\W", "_", name))
            sts.append(dict(setup=name, kind="heat", m=m, side=p.get("sides"), geom="t1s1", acc=acc,
                            min_adv=float(p.get("min_adv", 0)), window=tuple(p.get("window") or (950, 1500))))
        elif name == "orb20_a":
            sts.append(dict(setup=name, kind="bt", side="both", geom="bt", acc=acc))
        else:
            skipped.append((name, f"no history harness (type {kind})"))
    rows = []
    for mo in months():
        df = load_month(mo)
        ds_ = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        assert not ((ds_ >= LOCK[0]) & (ds_ <= LOCK[1])).any(), "locked block present"
        tod, adv = df["tod"].to_numpy(), df["adv20"].fillna(0).to_numpy()
        for s in sts:
            if s["kind"] == "bt":
                continue
            lo, hi = s["window"]
            base = (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (adv >= s["min_adv"])
            m = s["m"]
            with np.errstate(invalid="ignore"):
                if s["kind"] == "lab":
                    legs = [(np.asarray(m.mask(df), bool) & base, s["side"], s["geom"])]
                else:
                    sc = np.asarray(m.score(df), float); legs = []
                    if s["side"] in ("both", "long") and getattr(m, "LONG_AT", None) is not None:
                        legs.append((base & (sc >= m.LONG_AT), "long", "t1s1"))
                    if s["side"] in ("both", "short") and getattr(m, "SHORT_AT", None) is not None:
                        legs.append((base & (sc <= m.SHORT_AT), "short", "t1s1"))
            for mk, side, geom in legs:
                tr = G.lab_trades(df, mk, side, geom)
                tr["setup"], tr["side"] = s["setup"], side
                rows.append(tr)
        print(mo, len(df), sum(len(r) for r in rows), flush=True)
        del df
    b = pd.read_parquet(DATA / "bt_trades.parquet")
    b = b[b.strategy == "orb20_a"]
    et = pd.to_datetime(b["entry_time"], utc=True).dt.tz_convert("America/New_York")
    tod = (et.dt.hour * 100 + et.dt.minute).to_numpy()
    # bt entry_time is the stop-entry fill minute; the decision bar is the 5-min bar CLOSE at or before it (frame tod =
    # bar close time), so every index value used is known at the fill
    bar = pd.Series(et).dt.floor("5min")
    o = pd.DataFrame({"date": pd.to_datetime(b["date"]).dt.date, "symbol": b.symbol.astype(str),
                      "tod": (bar.dt.hour * 100 + bar.dt.minute).to_numpy(), "r": b.r_multiple.astype(float).to_numpy(),
                      "setup": "orb20_a", "side": np.where(b.side.to_numpy() > 0, "long", "short")})
    o = o[tod >= 950]
    rows.append(o)
    E = pd.concat(rows, ignore_index=True)
    E["symbol"] = E.symbol.astype(str); E["date"] = E.date.astype(str)
    assert not ((E.date >= LOCK[0]) & (E.date <= LOCK[1])).any(), "locked block present"
    E = E[E.date <= "2026-10-07"]
    E.to_parquet(S / "entries.parquet", index=False)
    U = pd.DataFrame([dict(setup=s["setup"], kind=s["kind"], side=s["side"], geom=s["geom"], window=s.get("window"),
                           min_adv=s.get("min_adv"), live_primary=s["acc"].get("primary", 0), live_testing1=s["acc"].get("testing1", 0),
                           hist_n=int((E.setup == s["setup"]).sum())) for s in sts])
    U = pd.concat([U, pd.DataFrame([dict(setup=n, kind="skipped: " + why) for n, why in skipped])], ignore_index=True)
    U.to_csv(OUT / "setups_used.csv", index=False)
    print(U.to_string())
