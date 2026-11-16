import io, subprocess, pandas as pd
R = "/home/user/MCF"
def git(*a): return subprocess.run(["git", "-C", R, *a], capture_output=True, text=True, check=True).stdout
snaps = []
for br in ("mcf-data", "mcf-data-testing", "mcf-data-testing2"):
    for h in git("log", "--format=%H", f"origin/{br}", "--", "universe.csv").split():
        try: snaps.append(pd.read_csv(io.StringIO(git("show", f"{h}:universe.csv")), usecols=["symbol", "shortable", "easy_to_borrow", "built_at"]))
        except Exception as e: pass
U = pd.concat(snaps).drop_duplicates(["symbol", "built_at"])
U["day"] = pd.to_datetime(U.built_at, utc=True).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
U["ok"] = (U.shortable.astype(bool) & U.easy_to_borrow.astype(bool)).astype(float)
DF = U.groupby(["day", "symbol"]).ok.mean().reset_index()
print(DF.day.nunique(), DF.day.min(), DF.day.max())
DF.groupby("symbol").ok.mean().rename("rate").to_frame().to_parquet("etb_rate.parquet")
