"""REPS2 shared loader: live and shadow records of every account journal on the mcf-data* branches (read-only, `git show`).

live_trades()   closed trades of the live run (kind 'paper'), R after costs (mcf.costs.cost_r = pnl_adj / risk, LR8)
shadow()        closed shadow trades + shadow signals with their mode ('of_live' = a live setup's twin, 'only' = a setup
                that cannot trade live in that account; mcf/execution/shadow.py), R after costs (fill profile B)
Educational only - not financial advice."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf.costs import cost_r                                   # noqa: E402
from mcf.research.shadow_calib import BRANCHES, RESOURCE, family_of     # noqa: E402,F401

COLS = ["account", "strategy", "date", "r", "side"]


def _mode(x) -> str:
    try:
        v = json.loads(x) if x else {}
        return str(v.get("mode", "of_live")) if isinstance(v, dict) else "of_live"
    except (TypeError, ValueError):
        return "of_live"


@lru_cache(maxsize=1)
def load() -> dict:
    """{'live': trades, 'shadow': trades (+ mode), 'shadow_sig': entered shadow signals (+ mode)} over every account."""
    live, sh, sig = [], [], []
    for acct, br in BRANCHES.items():
        try:
            raw = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:journal.db"], capture_output=True,
                                 check=True).stdout
        except subprocess.CalledProcessError:
            continue
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            f.write(raw)
            f.flush()
            con = sqlite3.connect(f.name)
            runs = pd.read_sql("SELECT id, kind FROM runs", con)
            for kind in ("paper", "shadow"):
                ids = runs.loc[runs.kind == kind, "id"].tolist()
                if not ids:
                    continue
                rid = int(min(ids))
                t = pd.read_sql("SELECT * FROM trades WHERE run_id=? AND exit_time IS NOT NULL", con, params=[rid])
                if len(t):
                    t["r"] = cost_r(t).astype(float)
                    t["account"] = acct
                    if "side" not in t:
                        t["side"] = 0
                if kind == "paper":
                    if len(t):
                        live.append(t[COLS])
                    continue
                s = pd.read_sql("SELECT day, strategy, symbol, side, status, info, broker_order_id FROM signals "
                                "WHERE run_id=? AND status='shadow_entered'", con, params=[rid])
                s["mode"] = [_mode(x) for x in s["info"]]
                s["account"] = acct
                sig.append(s.drop(columns=["info"]))
                if len(t):
                    om = dict(zip(s["broker_order_id"].astype(str), s["mode"]))
                    t["mode"] = [om.get(str(o), "of_live") for o in t.get("broker_order_id", pd.Series(index=t.index))]
                    sh.append(t[COLS + ["mode"]])
            con.close()
    cat = lambda x, c: pd.concat(x, ignore_index=True) if x else pd.DataFrame(columns=c)  # noqa: E731
    out = {"live": cat(live, COLS), "shadow": cat(sh, COLS + ["mode"]),
           "shadow_sig": cat(sig, ["day", "strategy", "symbol", "side", "status", "broker_order_id", "mode", "account"])}
    for k in out:
        d = out[k]
        if "date" in d:
            d["date"] = d["date"].astype(str).str[:10]
    return out


def _cat(status: str, reason: str) -> str:
    r = str(reason or "")
    if status in ("submitted", "dry_run"):
        return "entered"
    if status == "rejected":
        return "broker"
    if any(r.startswith(x) for x in RESOURCE):
        return "resource"
    if "shortable" in r or "ETB" in r or "borrow" in r:
        return "borrow"
    if r.startswith(("spread", "cost filter", "size <", "quote")):
        return "quote_cost"
    return "other"


@lru_cache(maxsize=1)
def live_signals() -> pd.DataFrame:
    """Live-run signal counts per account x setup x day x category (entered / resource / quote_cost / borrow / broker /
    other), from every account journal."""
    out = []
    for acct, br in BRANCHES.items():
        try:
            raw = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:journal.db"], capture_output=True,
                                 check=True).stdout
        except subprocess.CalledProcessError:
            continue
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            f.write(raw)
            f.flush()
            con = sqlite3.connect(f.name)
            g = pd.read_sql("SELECT day, strategy, status, reason, count(*) AS n FROM signals WHERE run_id=(SELECT "
                            "min(id) FROM runs WHERE kind='paper') GROUP BY 1,2,3,4", con)
            con.close()
        g["cat"] = [_cat(a, b) for a, b in zip(g["status"], g["reason"])]
        g["account"] = acct
        out.append(g.groupby(["account", "strategy", "day", "cat"], as_index=False)["n"].sum())
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=["account", "strategy", "day", "cat", "n"])


def assignments() -> dict:
    return json.loads((ROOT / "docs" / "live" / "assignments.json").read_text())
