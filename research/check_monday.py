"""Outcome-free readiness check for Monday's four scores (Builder). Verifies inputs exist, plans + scorers are committed,
selftests pass. Reads no result. Educational only - not financial advice."""
import subprocess, sys
from pathlib import Path
G = Path("/home/user/guild/research"); M = Path("/home/user/MCF"); SC = Path("/tmp/claude-0/-home-user-MCF/14615c23-3a58-5ec1-a24c-76299e68a66c/scratchpad")
ok = True
def chk(name, cond, fix=""):
    global ok; ok &= bool(cond); print(f"[{'ok' if cond else 'MISSING'}] {name}" + ("" if cond else f"  -> {fix}"))
chk("momside daily closes", (G / "momside/data/daily_closes.parquet").exists(), "python momside/momside.py --fetch (outside market hours)")
chk("full-day trade lists", (G / "momside/data/trades_full.parquet").exists(), "python momside/build_full.py")
chk("sizestop dividends + splits", (G / "sizestop/data/cash_div.parquet").exists() and (G / "sizestop/data/splits.parquet").exists(), "python sizestop/fetch_div.py")
chk("GEN hold lists", any((SC / "hold/bt").glob("sig_*.parquet")), "python bereplay/bt_hold.py (see roles/builder_log.md)")
chk("bt_lab1104 lists", any((M / "research/history2y/data/bt_lab1104").glob("sig_*.parquet")), "research/data/rebuild.sh")
chk("1-min cache (SPY present)", (M / "data/cache_hist/1Min/SPY.parquet").exists(), "research/data/rebuild.sh")
for d in ("momside", "sizestop", "dipturn"):
    st = subprocess.run(["git", "-C", str(G), "status", "--porcelain", f"{d}/PLAN.md", f"{d}/{d}.py"], capture_output=True, text=True).stdout
    chk(f"{d} plan + scorer committed", not st.strip(), "commit before scoring")
for cmd in (["python", "momside/momside.py", "--selftest"], ["python", "sizestop/sizestop.py", "--selftest"],
            ["python", "dipturn/dipturn.py", "--selftest"], ["python", "builder_blockguard.py"], ["python", "guild_read.py"]):
    r = subprocess.run(cmd, cwd=G, capture_output=True, text=True, timeout=900)
    chk("selftest " + cmd[1], r.returncode == 0 and "ok" in r.stdout, (r.stderr or r.stdout)[-200:])
r = subprocess.run(["python", "-c", "import ast;ast.parse(open('fwdcal/mirror.py').read())"], cwd=G, capture_output=True, text=True)
chk("fwdcal mirror.py parses", r.returncode == 0)
print("READY" if ok else "NOT READY", "- Educational only - not financial advice.")
sys.exit(0 if ok else 1)
