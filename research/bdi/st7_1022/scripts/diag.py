"""st7_1022 Part 0 (normal variance) + Part 1 (diagnosis of P0, descriptive, not counted). Writes diag.csv, days.csv.
Educational only - not financial advice."""
import numpy as np
import pandas as pd
from core import load, first_per_symday, p0_cond, exit_r
from sc import HERE, summ

cand, part, pc, pp = load()
i0 = first_per_symday(cand, p0_cond(cand))
c = cand.loc[i0].copy()
c["r"] = exit_r(cand, pc, "t1s1", i0)
part["r"] = exit_r(part, pp, "t1s1")
ctrl = part.groupby("cid")["r"].mean()
c["ctrl"] = c["cid"].map(ctrl)
c.to_parquet(HERE.parent / "st7_1022" / "p0.parquet") if False else None
t = c["tod"]
c["todb"] = np.select([t < 1045, t == 1045, t < 1200, t < 1335], ["09:50-10:40", "10:45 bar", "10:50-11:55", "12:00-13:30"], "13:35-15:00")
c["gapb"] = pd.cut(c["gap"], [-99, -1, 1, 3, 999], labels=["gap<=-1", "-1..1", "1..3", "gap>3"]).astype(str)
c["rs"] = c["fromOpen"] - c["spy_fo"]
c["rsb"] = pd.cut(c["rs"], [-99, -4, -3, -2, 99], labels=["RS<-4", "-4..-3", "-3..-2", "RS>=-2"]).astype(str)
c["fob"] = pd.cut(c["fromOpen"], [-99, -4, -2, -1], labels=["fo<-4", "-4..-2", "-2..-1"]).astype(str)
c["rsib"] = pd.cut(c["rsi"], [0, 20, 25, 30.0001], labels=["rsi<20", "20-25", "25-30"]).astype(str)
c["drop"] = c["prsi"] - c["rsi"]
c["dropb"] = pd.cut(c["drop"], [0, 25, 35, 100], labels=["drop<25", "25-35", "drop>35"]).astype(str)
c["spyv"] = np.where(c["spy_vwap"] > 0, "SPY>VWAP", "SPY<VWAP")
c["qqqv"] = np.where(c["qqq_vwap"] > 0, "QQQ>VWAP", "QQQ<VWAP")
c["spyfo"] = np.where(c["spy_fo"] > 0, "SPY up from open", "SPY down from open")
c["brd"] = np.where(c["d2"] > 0, "breadth rising", np.where(c["d2"] <= 0, "breadth falling", "breadth n/a (<10:00)"))
c["brl"] = pd.cut(c["breadth"], [0, 0.4, 0.6, 1], labels=["breadth<0.4", "0.4-0.6", ">0.6"]).astype(str)
c["bpb"] = pd.cut(c["buyPressure"], [0, 0.1, 0.25, 1], labels=["bp 0-0.1", "0.1-0.25", ">0.25"]).astype(str)
c["vrb"] = pd.cut(c["volumeRatio"], [0, 1, 2, 999], labels=["vol<1", "1-2", "vol>2"]).astype(str)
c["atrp"] = c["atr_d"] / c["close"] * 100
c["atrb"] = pd.cut(c["atrp"], [0, 3, 5, 999], labels=["ATR%<3", "3-5", ">5"]).astype(str)
nb = c.groupby(["date", "tod"])["symbol"].transform("size")
c["samebar"] = np.select([nb == 1, nb == 2], ["1 in bar", "2 in bar"], "3+ in bar")
c = c.sort_values(["date", "tod", "symbol"])
c["k_day"] = c.groupby("date").cumcount() + 1
c["kday"] = np.select([c.k_day == 1, c.k_day <= 3, c.k_day <= 6], ["#1", "#2-3", "#4-6"], "#7+")
c["cohort"] = np.where(c["tod"] == 1045, "10:45 bar", "other bars")
rows = []
for var in ["regime", "regime2", "todb", "cohort", "gapb", "rsb", "fob", "rsib", "dropb", "spyv", "qqqv", "spyfo", "brd", "brl",
            "bpb", "vrb", "atrb", "samebar", "kday"]:
    for lev, g in c.groupby(var):
        row = {"split_by": var, "level": lev}
        for sp in ("train", "valid", "all"):
            x = g if sp == "all" else g[g["split"] == sp]
            if not len(x):
                continue
            s = summ(x["r"], x["date"])
            row.update({f"n_{sp}": s["n"], f"avg_{sp}": s["exp_r"], f"tot_{sp}": round(x["r"].sum(), 1), f"t_{sp}": s["t"],
                        f"rand_{sp}": round(x["ctrl"].mean(), 4)})
        if var not in ("regime", "regime2"):
            for reg in ("Bull", "Bear", "Choppy", "Quiet"):
                x = g[g["regime"] == reg]
                row[f"{reg}_n"], row[f"{reg}_avg"] = len(x), round(x["r"].mean(), 3) if len(x) else None
        rows.append(row)
d = pd.DataFrame(rows)
d.to_csv(HERE / "diag.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print(d[["split_by", "level", "n_train", "avg_train", "n_valid", "avg_valid", "n_all", "avg_all", "t_all", "rand_all",
         "Bull_avg", "Bear_avg", "Choppy_avg", "Quiet_avg"]].to_string())
# cohort x regime x split
print(c.pivot_table(index=["cohort", "split"], columns="regime", values="r", aggfunc=["mean", "size"]).round(3).to_string())
print(c.pivot_table(index=["spyv", "split"], columns="regime", values="r", aggfunc=["mean", "size"]).round(3).to_string())
# Part 0: day totals
day = c.groupby("date").agg(r=("r", "sum"), n=("r", "size"), regime=("regime", "first"), regime2=("regime2", "first"),
                            o2c=("o2c", "first"), split=("split", "first"))
day.to_csv(HERE / "days.csv")
LIVE = -2.4683   # 10-21 live ST7-FD day total R (journal: -1.063 -1.030 +0.282 -0.369 -0.269)
for nm, g in [("all traded days", day), ("Choppy days", day[day.regime == "Choppy"]),
              ("Choppy-up days", day[day.regime2 == "Choppy-up"]), ("Bull days", day[day.regime == "Bull"]),
              ("train", day[day.split == "train"]), ("valid", day[day.split == "valid"])]:
    print(f"{nm}: {len(g)} days, share with day total <= {LIVE:.2f}R: {(g.r <= LIVE).mean():.1%} ({(g.r <= LIVE).sum()}), "
          f"median day {g.r.median():+.2f}R, mean {g.r.mean():+.2f}R")
bad = (day.r <= LIVE).to_numpy()
print("P(bad | prev traded day bad)", round(bad[1:][bad[:-1]].mean(), 3), "base", round(bad.mean(), 3))
# 5-trade days specifically
g5 = day[day.n >= 5]
print("days with >=5 trades:", len(g5), "share <= live:", round((g5.r <= LIVE).mean(), 3))
c.to_parquet("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/st7/p0.parquet")
