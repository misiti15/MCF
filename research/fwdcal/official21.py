"""OFFICIAL rule 21 on frozen FWDCAL books (Lead 11-17 19:00; owner RULE21-DB 11-17): adapts mirror books
(out/books/<variant>/<day>/<acct>.json) to MCF research/replay_cal/score.py's run layout and calls its main() unchanged
(decision-bar match from the client order id, LR8 R on each side's own fills, gap + never-optimistic guards, fresh
sessions after params_v2 fit_until). A read of frozen books, not a re-score: no replay is re-run.
    python official21.py --dates 2026-11-16..2026-11-17 --variant qm0 --out out/official21_fresh2
Educational only - not financial advice."""
import argparse, gzip, json, subprocess, sys, tempfile
from pathlib import Path
import pandas as pd
MCF = Path("/home/user/MCF"); sys.path.insert(0, str(MCF / "research" / "replay_cal")); sys.path.insert(0, str(MCF))
import score as S  # noqa: E402
ACC = ["primary", "testing", "testing2", "explore1", "livelab", "graveyard", "gen", "testingd", "testinge", "testingf"]
BR = {a: ("mcf-data" if a == "primary" else f"mcf-data-{a}") for a in ACC}
NAME = {"primary": "Primary", "testing": "On Deck", "testing2": "Testing A", "explore1": "Testing B", "livelab": "Testing C",
        "graveyard": "Graveyard", "gen": "Generator", "testingd": "Testing D", "testinge": "Testing E", "testingf": "Testing F"}
ap = argparse.ArgumentParser(); ap.add_argument("--dates"); ap.add_argument("--variant", default="qm0"); ap.add_argument("--out"); ap.add_argument("--accounts", default=",".join(ACC))
a = ap.parse_args(); lo, hi = a.dates.split("..")
tmp = Path(tempfile.mkdtemp(prefix="off21_")); run, live = tmp / "run", tmp / "live"; live.mkdir(parents=True)
for acc, br in BR.items():
    (live / f"{br}.db").write_bytes(subprocess.run(["git", "-C", str(MCF), "show", f"origin/{br}:journal.db"], capture_output=True, check=True).stdout)
n = 0
for f in sorted((Path(__file__).parent / "out" / "books" / a.variant).glob("*/*.json")):
    r = json.loads(f.read_text())
    if r.get("skipped") or not (lo <= r["day"] <= hi):
        continue
    d = run / r["acc"] / r["day"]; d.mkdir(parents=True, exist_ok=True)
    t = pd.DataFrame(r["trades"])
    if len(t):
        t["broker_order_id"] = t.meta.str.extract(r'"coid": "([^"]+)"')[0]
        assert t.broker_order_id.notna().all(), f"coid missing {f}"
    s = pd.DataFrame(r["signals"]);  s["info"] = "{}"
    t.to_csv(d / "trades.csv.gz", index=False); s.to_csv(d / "signals.csv.gz", index=False)
    (d / "stats.json").write_text("{}"); n += 1
print(f"books adapted: {n} (account-days) from {a.variant}, {lo}..{hi}")
S.BRANCH_DB.update(BR)
acc = a.accounts.split(",")
GROUPS = {"all": acc, "ex_graveyard": [x for x in acc if x != "graveyard"],
          "arena_ondeck": [x for x in acc if x not in ("graveyard", "primary")]}   # Skeptic 11-18 01:50, Lead-adopted wording
lines = []
for g, aa in GROUPS.items():
    o = Path(a.out) / ("" if g == "all" else g); print(f"== OFFICIAL rule 21, group {g}: {','.join(aa)}")
    S.main(["--run", str(run), "--dates", a.dates, "--accounts", ",".join(aa), "--live-dir", str(live), "--out", str(o)])
    sc = json.loads((o / "scorecard.json").read_text())
    if g == "all":
        for x in sc["accounts"]:
            r = x["rule21"]; f = [k for k in ("match_ok", "gap_ok", "no_optimism", "fresh") if not r[k]]
            lines.append(f"{NAME[x['account']]:10s} match {r['match']:.3f} gap_m {r['gap_matched']:+.4f} gap_all {r['gap_all']:+.4f} "
                         f"{'PASS' if r['pass'] else 'FAIL ' + ','.join(f)}")
        nf = sum(not v for v in sc["rule21"]["per_account"].values())
        lines.append(f"per-account FAIL in {nf} of {len(acc)}")
    r = sc["pooled"]["rule21"]; f = [k for k in ("match_ok", "gap_ok", "no_optimism", "fresh") if not r[k]]
    lines.append(f"pooled {g:13s} match {r['match']:.3f} gap_m {r['gap_matched']:+.4f} gap_all {r['gap_all']:+.4f} "
                 f"{'PASS' if r['pass'] else 'FAIL ' + ','.join(f)}")
txt = "\n".join(lines) + ("\nOFFICIAL rule 21 (owner RULE21-DB, decision-bar match; MCF research/replay_cal/score.py rule21() unchanged, on "
       f"frozen books {a.variant} {a.dates}; a read, not a re-score). Educational only - not financial advice.")
(Path(a.out) / "OFFICIAL.txt").write_text(txt + "\n"); print(txt)
