from combo import *
S3 = pd.read_parquet(O2 + "sim3.parquet").drop(columns=["A_r", "A_why", "A_xt", "A_drift"], errors="ignore")
c3 = c.merge(S3, on="key", how="inner")
E = ["S15", "S20", "S15T06", "S15T04", "S20T06", "S12T04", "S15MH60", "S12BE4", "SLOD", "SLODT06"]
base = dict(gate=both(c1, g3))
if __name__ == "__main__":
    rows = [row("K-b (S12) on sim3 pool", trades(c3, **base, exitc="S12"))]
    for e in E: rows.append(row(f"C1+G3 + {e}", trades(c3, **base, exitc=e)))
    rows.append(row("WB4 + S15 alone", trades(c3, exitc="S15")))
    rows.append(row("WB4 + S20 alone", trades(c3, exitc="S20")))
    D = pd.DataFrame(rows); D.to_csv(O2 + "exp3.csv", index=False)
    pd.set_option("display.width", 260)
    print(D[["name", "train_avg", "valid_avg", "replay_n", "replay_avg", "replay_wo_best", "replay_worst_day", "2y_n", "2y_avg", "2y_wo_best", "2y_worst_day", "2y_win", "up", "flat", "down"]].round(3).to_string())
