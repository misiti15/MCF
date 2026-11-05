"""Intraday marked-to-market R curve of one account and day (owner 2026-11-05, intraday tracker).

    python -m mcf.report.intraday --date 2026-11-05 --account primary [--step 1] [--state-dir DIR] [--out PATH]

Sources, in order (the one used is printed and written into the CSV / chart):
  snapshots  the runner's per-poll "mtm" snapshots in the poll log (polls/<date>/*.jsonl.gz, mcf.execution.runner
             mtm_snapshot): realized R (reconciled) + the open lots' unrealized R at each poll, long/short counts, net
             notional, SPY/QQQ/IWM % from the open when the runner had their bars.
  journal    past days without snapshots: the journal's closed trades of the day (entry / exit times and prices, initial
             stop, booked R) marked to market on cached 1-minute bars (data/replay/1Min store, then data/cache_hist/1Min);
             a trade without cached bars counts 0 while open and its booked R from the exit minute
             ("journal+bars" / "journal (no bars: realized only)").
State is read from --state-dir (a folder holding polls/ and journal.db) or, by default, from the account's state branch
(origin/mcf-data*, via `git show`, read-only). Writes research/intraday/<date>/<account>.{png,csv} unless --out is given
(a path ending in .png/.csv, or a folder). Unrealized marks carry no costs; realized R is as the journal books it.
The BDI swing autopsy uses these curves when present (docs/BDI_CHARTER.md). Educational only - not financial advice."""
from __future__ import annotations

import argparse
import gzip
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

NY = "America/New_York"
ROOT = Path(__file__).resolve().parents[2]
BRANCH = {"primary": "mcf-data", "testing": "mcf-data-testing", "testing1": "mcf-data-testing",
          "testing2": "mcf-data-testing2", "explore1": "mcf-data-explore1", "livelab": "mcf-data-livelab",
          "graveyard": "mcf-data-graveyard", "gen": "mcf-data-gen", "longhold": "mcf-data-longhold",
          "hunch": "mcf-data-hunch", "borrow": "mcf-data-borrow"}
DISCLAIMER = "Educational only — not financial advice"
INDEX = ("SPY", "QQQ", "IWM")


# ---------------------------------------------------------------------------------------------- reading state
def _git(*args, binary=False):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=True,
                          text=not binary).stdout


def load_state(account: str, day: str, state_dir: str | None = None) -> tuple[list[dict], str | None]:
    """(poll records of the day, path of a readable journal.db or None)."""
    from ..execution.runner import read_poll_log

    if state_dir:
        sd = Path(state_dir)
        recs = read_poll_log(str(sd / "polls"), day) if (sd / "polls" / day).exists() else []
        j = sd / "journal.db"
        return recs, str(j) if j.exists() else None
    br = f"origin/{BRANCH.get(account.lower(), account)}"
    recs: list[dict] = []
    try:
        names = _git("ls-tree", "--name-only", f"{br}:polls/{day}").split()
    except subprocess.CalledProcessError:
        names = []
    for n in sorted(x for x in names if x.endswith(".jsonl.gz")):
        raw = gzip.decompress(_git("show", f"{br}:polls/{day}/{n}", binary=True)).decode()
        recs += [json.loads(line) for line in raw.splitlines() if line.strip()]
    jpath = None
    try:
        blob = _git("show", f"{br}:journal.db", binary=True)
        fd, jpath = tempfile.mkstemp(suffix=".db")
        with os.fdopen(fd, "wb") as f:
            f.write(blob)
    except subprocess.CalledProcessError:
        pass
    return sorted(recs, key=lambda r: r["t"]), jpath


def _grid(day: str, step: int) -> pd.DatetimeIndex:
    return pd.date_range(pd.Timestamp(f"{day} 09:30", tz=NY), pd.Timestamp(f"{day} 16:00", tz=NY), freq=f"{step}min")


# ---------------------------------------------------------------------------------------------- source 1: snapshots
def curve_from_snapshots(recs: list[dict], day: str, step: int = 1) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(curve on the step grid, events). Events: a lot appearing between two snapshots = entry, disappearing = exit
    (marked at its last uR; its booked R shows in realized R once reconciled)."""
    rows, ev, prev = [], [], {}
    for r in recs:
        m = r.get("mtm")
        if not isinstance(m, dict):
            continue
        ts = pd.Timestamp(f"{day} {r['t']}", tz=NY)
        cur = {(p[0], p[1], p[2], p[3]): p for p in m.get("pos") or []}
        for k, p in cur.items():
            if k not in prev:
                ev.append({"time": ts, "kind": "entry", "symbol": p[0], "setup": p[1], "side": p[2], "r": p[5]})
        for k, p in prev.items():
            if k not in cur:
                ev.append({"time": ts, "kind": "exit", "symbol": p[0], "setup": p[1], "side": p[2], "r": p[5]})
        prev = cur
        idx = m.get("idx") or {}
        rows.append({"time": ts, "realized_r": m.get("rr", 0.0), "unrealized_r": m.get("ur", 0.0),
                     "n_long": m.get("nl", 0), "n_short": m.get("ns", 0), "net_notional": m.get("net"),
                     **{f"{s.lower()}_pct": (idx.get(s) or [None, None])[1] for s in INDEX}})
    if not rows:
        return pd.DataFrame(), pd.DataFrame()
    df = pd.DataFrame(rows).set_index("time").sort_index()
    df = df[~df.index.duplicated(keep="last")]
    g = _grid(day, step)
    out = df.reindex(df.index.union(g)).ffill().reindex(g)
    out = out[out.index >= df.index[0].floor(f"{step}min")]
    out["total_r"] = out["realized_r"] + out["unrealized_r"]
    return out, pd.DataFrame(ev)


# ---------------------------------------------------------------------------------------------- source 2: journal + bars
def _cached_bars(day: str, syms) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    try:
        from ..replay.store import load_day

        out = load_day(day, sorted(syms))
    except Exception:
        out = {}
    bases = [ROOT / "data" / "cache_hist" / "1Min", ROOT / "data" / "cache" / "1Min"]
    try:
        from ..replay.store import HIST

        bases = list(HIST) + bases
    except Exception:
        pass
    try:   # a worktree: the main checkout's caches
        main = Path(_git("rev-parse", "--path-format=absolute", "--git-common-dir").strip()).parent
        bases += [main / "data" / "cache_hist" / "1Min", main / "data" / "cache" / "1Min"]
    except Exception:
        pass
    for s in set(syms) - set(out):
        for base in dict.fromkeys(bases):
            p = base / f"{s}.parquet"
            if not p.exists():
                continue
            try:
                b = pd.read_parquet(p)
                b.index = pd.to_datetime(b.index, utc=True).tz_convert(NY)
                b = b[b.index.normalize() == pd.Timestamp(day, tz=NY)]
                if len(b):
                    out[s] = b
                    break
            except Exception:
                continue
    return out


def journal_trades(jpath: str, day: str) -> pd.DataFrame:
    import sqlite3

    con = sqlite3.connect(f"file:{jpath}?mode=ro", uri=True)
    try:
        t = pd.read_sql("SELECT t.* FROM trades t JOIN runs r ON r.id=t.run_id WHERE r.kind='paper' AND t.date=?",
                        con, params=[day])
    finally:
        con.close()
    return t


def curve_from_journal(trades: pd.DataFrame, day: str, step: int = 1, bars: dict | None = None
                       ) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    g1 = _grid(day, 1)
    if trades is None or trades.empty:
        return pd.DataFrame(), pd.DataFrame(), "journal (no trades)"
    t = trades.copy()
    for c in ("entry_time", "exit_time"):
        t[c] = pd.to_datetime(t[c], utc=True, format="mixed").dt.tz_convert(NY)
    bars = bars if bars is not None else _cached_bars(day, set(t.symbol) | set(INDEX))
    real = pd.Series(0.0, index=g1)
    unr = pd.Series(0.0, index=g1)
    nl = pd.Series(0, index=g1)
    ns = pd.Series(0, index=g1)
    ev, marked = [], 0
    for x in t.itertuples():
        risk = abs(float(x.entry) - float(x.stop)) if pd.notna(x.stop) else 0.0
        side = int(x.side)
        e0 = x.entry_time.floor("1min")
        e1 = x.exit_time.floor("1min") if pd.notna(x.exit_time) else g1[-1]
        openm = (g1 >= e0) & (g1 < e1)
        (nl if side == 1 else ns)[openm] += 1
        real[g1 >= e1] += float(x.r_multiple or 0)
        b = bars.get(x.symbol)
        if b is not None and len(b) and risk > 0:
            c = b["close"].reindex(g1).ffill()
            unr[openm] += (side * (c[openm] - float(x.entry)) / risk).fillna(0.0)
            marked += 1
        ev.append({"time": x.entry_time, "kind": "entry", "symbol": x.symbol, "setup": x.strategy, "side": side, "r": 0.0})
        ev.append({"time": x.exit_time, "kind": "exit", "symbol": x.symbol, "setup": x.strategy, "side": side,
                   "r": float(x.r_multiple or 0)})
    idx = {s: bars.get(s) for s in INDEX}
    df = pd.DataFrame({"realized_r": real, "unrealized_r": unr, "n_long": nl, "n_short": ns, "net_notional": np.nan})
    for s, b in idx.items():
        if b is not None and len(b) and f"{b.index[0]:%H%M}" == "0930":
            df[f"{s.lower()}_pct"] = (b["close"].reindex(g1).ffill() / float(b["open"].iloc[0]) - 1) * 100
        else:
            df[f"{s.lower()}_pct"] = np.nan
    df["total_r"] = df["realized_r"] + df["unrealized_r"]
    df = df.iloc[::step]
    src = ("journal+bars" if marked == len(t) else f"journal+bars ({marked}/{len(t)} trades marked)") if marked \
        else "journal (no bars: realized only)"
    return df, pd.DataFrame(ev), src


# ---------------------------------------------------------------------------------------------- output
def _events_col(curve: pd.DataFrame, ev: pd.DataFrame, step: int) -> pd.Series:
    col = pd.Series("", index=curve.index)
    if ev is None or ev.empty:
        return col
    for e in ev.itertuples():
        k = pd.Timestamp(e.time).floor(f"{step}min")
        if k in col.index:
            tag = f"{'+' if e.kind == 'entry' else '-'}{e.setup}:{e.symbol}:{'L' if e.side == 1 else 'S'}"
            col[k] = f"{col[k]} {tag}".strip()
    return col


def write_outputs(curve, ev, source, day, account, out: str | None = None, step: int = 1) -> tuple[Path, Path]:
    if out and out.endswith((".png", ".csv")):
        base = Path(out).with_suffix("")
    else:
        base = Path(out or ROOT / "research" / "intraday" / day) / account
    base.parent.mkdir(parents=True, exist_ok=True)
    csv, png = base.with_suffix(".csv"), base.with_suffix(".png")
    c = curve.copy()
    c["events"] = _events_col(c, ev, step)
    c["source"] = source
    c.index = c.index.strftime("%H:%M")
    c.index.name = "time"
    with open(csv, "w") as f:
        f.write(f"# {account} {day} intraday R curve; source: {source}; {DISCLAIMER}\n")
        c.round(4).to_csv(f)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    has_idx = any(curve[f"{s.lower()}_pct"].notna().any() for s in INDEX if f"{s.lower()}_pct" in curve)
    fig, axes = plt.subplots(2 if has_idx else 1, 1, figsize=(11, 6.5 if has_idx else 4.5), sharex=True,
                             gridspec_kw={"height_ratios": [3, 1]} if has_idx else None)
    ax = axes[0] if has_idx else axes
    ax.axhline(0, color="#9a9a9a", lw=0.8)
    ax.plot(curve.index, curve["total_r"], color="#2a6fdb", lw=2, label="total R (realized + open)")
    ax.plot(curve.index, curve["realized_r"], color="#7a7a7a", lw=1.2, ls="--", label="realized R")
    if ev is not None and not ev.empty:
        tot = curve["total_r"]
        for kind, mk, col in (("entry", "^", "#1b9e5a"), ("exit", "x", "#c2410c")):
            e = ev[ev.kind == kind]
            if e.empty:
                continue
            ts = pd.to_datetime(e["time"]).dt.floor(f"{step}min")
            y = tot.reindex(ts).to_numpy()
            ax.scatter(ts, y, marker=mk, s=40, color=col, zorder=3, label=f"{kind} ({len(e)})")
        top = ev[ev.kind == "exit"].assign(a=lambda d: d.r.abs().fillna(0)).nlargest(5, "a")
        for e in top.itertuples():   # selective labels: the biggest exits only
            k = pd.Timestamp(e.time).floor(f"{step}min")
            if k in tot.index and pd.notna(tot[k]):
                ax.annotate(f"{e.symbol} {e.r:+.1f}R" if pd.notna(e.r) else str(e.symbol),
                            (k, tot[k]), fontsize=7, color="#333333", xytext=(3, 4), textcoords="offset points")
    last = curve["total_r"].dropna()
    ax.set_ylabel("R")
    ax.set_title(f"{account} {day}: marked-to-market R ({'end ' + format(last.iloc[-1], '+.2f') + 'R' if len(last) else 'n/a'})"
                 f"  source: {source}", fontsize=10)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, loc="upper left")
    if has_idx:
        ax2 = axes[1]
        ax2.axhline(0, color="#9a9a9a", lw=0.8)
        for s, col in zip(INDEX, ("#2a6fdb", "#c2410c", "#7c3aed")):
            k = f"{s.lower()}_pct"
            if k in curve and curve[k].notna().any():
                ax2.plot(curve.index, curve[k], lw=1.4, color=col, label=s)
        ax2.set_ylabel("% from open")
        ax2.grid(alpha=0.25)
        ax2.legend(fontsize=8, loc="upper left", ncol=3)
    (axes[-1] if has_idx else ax).xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=curve.index.tz))
    fig.text(0.99, 0.005, DISCLAIMER, ha="right", fontsize=7, color="#666666")
    fig.tight_layout()
    fig.savefig(png, dpi=110)
    plt.close(fig)
    return png, csv


def build(day: str, account: str = "primary", step: int = 1, state_dir: str | None = None, out: str | None = None,
          bars: dict | None = None, log=print):
    step = max(1, min(5, int(step)))
    recs, jpath = load_state(account, day, state_dir)
    curve, ev = curve_from_snapshots(recs, day, step)
    source = "snapshots"
    if curve.empty:
        if not jpath:
            log(f"{account} {day}: no snapshots and no journal - nothing to chart")
            return None
        curve, ev, source = curve_from_journal(journal_trades(jpath, day), day, step, bars)
        if curve.empty:
            log(f"{account} {day}: no snapshots, {source}")
            return None
    png, csv = write_outputs(curve, ev, source, day, account, out, step)
    log(f"{account} {day}: source {source}; end {curve['total_r'].dropna().iloc[-1]:+.2f}R; wrote {png} and {csv}. "
        f"{DISCLAIMER}")
    return {"png": png, "csv": csv, "source": source, "curve": curve, "events": ev}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True)
    ap.add_argument("--account", default="primary")
    ap.add_argument("--step", type=int, default=1, help="minutes per step, 1-5")
    ap.add_argument("--state-dir", default=None, help="folder with polls/ and journal.db (default: the state branch)")
    ap.add_argument("--out", default=None, help="output .png/.csv path or folder")
    a = ap.parse_args(argv)
    build(a.date, a.account, a.step, a.state_dir, a.out)


if __name__ == "__main__":
    main()
