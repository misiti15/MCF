"""gates1021: the live setups of Primary / Testing 1 / Testing 2 (docs/live/assignments.json) with their merged
account configs, and which of them the frame scan can cover. Writes setups_used.csv. Educational only - not
financial advice."""
from __future__ import annotations

import json

import pandas as pd

from common import HERE, ROOT, account_cfg, load_mod

FRAME_GEOMS = {"t1s1", "t05s1", "t1s05"}


def live_setups() -> pd.DataFrame:
    asg = json.loads((ROOT / "docs" / "live" / "assignments.json").read_text())["accounts"]
    rows = []
    for acct in ("primary", "testing", "testing2"):
        cfg = account_cfg(acct)
        st = cfg.get("strategies") or {}
        for name in asg[acct]:
            p = dict(st.get(name) or {})
            typ = p.get("type", "classic")
            row = {"account": acct, "setup": name, "type": typ, "module": p.get("module"),
                   "window": tuple(p.get("window") or (950, 1500)), "min_adv": float(p.get("min_adv", 0) or 0),
                   "refire": bool(p.get("refire", (cfg.get("live") or {}).get("lab_refire", False))),
                   "cooldown": int(p.get("refire_cooldown", (cfg.get("live") or {}).get("lab_refire_cooldown", 1))),
                   "context": json.dumps(p.get("context")), "symbols": json.dumps(p.get("symbols")),
                   "enabled": bool(p.get("enabled", True)), "geom": p.get("geom"), "side": None, "covered": False,
                   "why_not": ""}
            if typ != "lab":
                row["why_not"] = f"type {typ} (not a lab mask)"
            else:
                m = load_mod(name, p["module"])
                row["side"] = m.SIDE
                g = p.get("geom") or getattr(m, "GEOM", "t1s1")
                row["geom"] = g
                if g not in FRAME_GEOMS:
                    row["why_not"] = f"geom {g} (no frame outcome)"
                elif "RW6G1" in name:
                    row["why_not"] = "needs the 1-minute VWAP-band guard"
                elif "/cwt/" in p["module"] or "reddit1012liq" in p["module"]:
                    row["why_not"] = "needs 09:35-09:45 head rows (opening-range logic)"
                elif p.get("symbols"):
                    row["why_not"] = "index/ETF allow-list setup"
                else:
                    row["covered"] = True
            rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = live_setups()
    df.to_csv(HERE / "setups_used.csv", index=False)
    print(df[["account", "setup", "type", "geom", "side", "refire", "covered", "why_not"]].to_string())
