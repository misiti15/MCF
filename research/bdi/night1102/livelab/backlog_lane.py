"""livelab: which backlog ideas (status idea / rework, plus near-miss tagged) would enter a live-first lane under the
minimal gate (costs-in backtest not clearly negative, sane trade count, runnable). Heuristic parse of the backlog notes;
every row and its bucket is written to backlog_lane.csv for checking. Educational only - not financial advice."""
import json, re
from pathlib import Path
import pandas as pd
OUT = Path(__file__).parent
rows = [json.loads(l) for l in open("/home/user/MCF/research/backlog.jsonl") if l.strip()]
NEWSETUP = {"setup", "strategy"}
RX_R = re.compile(r"(?<![\w.])([+\-−]?\d*\.\d+)\s?R\b")
RX_N = re.compile(r"\bn\s?=?\s?(\d{2,6})\b")
RX_DAY = re.compile(r"(\d+(?:\.\d+)?)\s?(?:trades)?\s?/\s?day")
BLOCK = re.compile(r"not live-runnable|needs historical news|news api|options|level ?2|order book|premarket data|"
                   r"discretionary|no data|cannot be backtested|not backtestable|retire|review\b|refuted", re.I)
out = []
for r in rows:
    st = r.get("status"); txt = " ".join(str(r.get(k) or "") for k in ("title", "hypothesis", "notes", "test"))
    nm = bool(re.search(r"near[- ]miss", txt, re.I))
    if st not in ("idea", "rework") and not (nm and st == "failed"):
        continue
    cat = r.get("category")
    rs = [float(x.replace("−", "-")) for x in RX_R.findall(r.get("notes") or "")]
    rs = [x for x in rs if abs(x) < 3]
    ns = [int(x) for x in RX_N.findall(r.get("notes") or "")]; dpd = [float(x) for x in RX_DAY.findall(r.get("notes") or "")]
    if r["id"].startswith("top5-"):
        b = "variant of a live setup (top-5 execution tune): twin of its parent, normal backlog path"
    elif cat not in NEWSETUP:
        b = "not a new setup (change to an existing setup / risk / ops / analysis: normal backlog path)"
    elif BLOCK.search(txt):
        b = "blocked: not runnable live / needs data we lack / a review item"
    elif not rs:
        b = "no costs-in backtest number yet (needs module + minimal backtest)"
    else:
        nt = (r.get("notes") or "").replace("\u2212", "-")
        ex = re.findall(r"\bexp(?:ectancy)?\s?([+\-]?\d*\.\d+)\s?R", nt)
        va = re.findall(r"\bvalid\s?([+\-]?\d*\.\d+)\s?R", nt, re.I)
        key = float(ex[0]) if ex else (float(va[-1]) if va else sorted(rs)[len(rs) // 2])
        last = med = key
        n_ok = (max(ns) >= 60 if ns else None); d_ok = (max(dpd) >= 0.3 if dpd else None)
        sane = n_ok or d_ok if (n_ok is not None or d_ok is not None) else None
        if min(last, med) < -0.02:
            b = "fails minimal gate: clearly negative after costs"
        elif sane is False:
            b = "fails minimal gate: too few trades"
        elif sane is None:
            b = "passes R test, trade count not stated (check)"
        else:
            b = "ENTERS lane: not negative after costs, sane count"
    out.append(dict(id=r["id"], status=st, near_miss=nm, category=cat, added=r.get("added"), bucket=b,
                    R_figures=" ".join(f"{x:+.3f}" for x in rs[:6]), n=max(ns) if ns else None,
                    title=(r.get("title") or "")[:110]))
LIVE = {"bdi-rw-nm-ns1-plateau": "NS1 (Primary / T1 -FD)", "bdi-rw-nm-sma50-flush-long": "NS5-sma50-flush-oversold-long-FD (T1)",
        "bdi-rw-nm-ns2-early": "NS2 (Graveyard)", "swarm1017-arena-am-long-gapdown-capitulation": "NM-AR-AM (T2)",
        "swarm1017-AMS-N1-quiet-morning-short": "NM-AMS-N1 (T2)", "swarm1017-arena-pm-gapdn-above-pdh-rvol": "NM-PM-gapdn-above-pdh (T2)",
        "rework-cwt-1017-NM1": "NM1-cwt09 (T2)", "swarm1017-misc-heatlong-pm-strict": "NM-HL-T75-pm-long (T2)"}
for o in out:
    if o["id"] in LIVE and o["bucket"].startswith("ENTERS"):
        o["bucket"] = "passes, but already live as " + LIVE[o["id"]]
d = pd.DataFrame(out); d.to_csv(OUT / "backlog_lane.csv", index=False)
print(len(d)); pd.set_option("display.width", 250); print(d.groupby(["bucket", "status"]).size().unstack(fill_value=0))
print("near-miss tagged:", d.near_miss.sum()); print(d[d.near_miss].bucket.value_counts())
