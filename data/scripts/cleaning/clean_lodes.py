"""
clean_lodes.py — LODES 8 NY origin-destination flows aggregated to census tracts, 2009-2020.

Origin: notebook `LODES Data/distance graph in matplotlib.ipynb`, functions
`get_hudson_commuters` and `get_total_workers` (logic unchanged). Each yearly file is read
once and only the three columns that are used are kept.

Steps (decision numbers refer to data/README.md):
  C1  LODES 8 "main" OD file for NY (home and work block both in NY), JT01 = primary jobs,
      S000 = total number of jobs in a block pair
  C2  tract = first 11 digits of the 15-digit 2020 block code
  C3  Hudson Yards commuters: jobs with work tract in HY_TRACTS_LODES, summed by
      (home tract, work tract) — one row per home tract and HY destination tract
  C4  total workers: all jobs summed by home tract (any work location in NY)

Input : data/raw/lodes/ny_od_main_JT01_{2009..2020}.csv.gz (or .csv)
Output: data/clean/lodes/hudson_commuters.csv   year, h_trct, w_trct, hudson_workers
        data/clean/lodes/total_workers.csv      year, h_trct, total_workers
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import config  # noqa: E402

OUT = config.CLEAN / "lodes"


def get_hudson_commuters(df, tracts_hudson):
    """C3 — workers commuting to Hudson Yards, by home and work tract."""
    return (df.query("w_trct in @tracts_hudson")
              .groupby(["h_trct", "w_trct"], as_index=False)
              .agg({"S000": "sum"})
              .rename(columns={"S000": "hudson_workers"}))


def get_total_workers(df):
    """C4 — all workers by home tract."""
    return (df.groupby("h_trct", as_index=False)
              .agg({"S000": "sum"})
              .rename(columns={"S000": "total_workers"}))


def main():
    hudson, total = [], []
    for year in config.YEARS:
        path = config.lodes_path(year)
        df = pd.read_csv(path, usecols=["w_geocode", "h_geocode", "S000"],
                         dtype={"w_geocode": str, "h_geocode": str, "S000": "int64"})
        df["w_trct"] = df["w_geocode"].str.slice(stop=11)                    # C2
        df["h_trct"] = df["h_geocode"].str.slice(stop=11)
        df = df[["w_trct", "h_trct", "S000"]]
        h = get_hudson_commuters(df, config.HY_TRACTS_LODES).assign(year=year)
        t = get_total_workers(df).assign(year=year)
        hudson.append(h)
        total.append(t)
        by_dest = h.groupby("w_trct")["hudson_workers"].sum().to_dict()
        print(f"{year}: {path.name}: {len(df):,} block pairs, {df['S000'].sum():,} jobs; "
              f"HY jobs by tract {by_dest}")
        del df

    OUT.mkdir(parents=True, exist_ok=True)
    hudson = pd.concat(hudson)[["year", "h_trct", "w_trct", "hudson_workers"]]
    total = pd.concat(total)[["year", "h_trct", "total_workers"]]
    hudson.to_csv(OUT / "hudson_commuters.csv", index=False)
    total.to_csv(OUT / "total_workers.csv", index=False)
    print(f"\nwrote data/clean/lodes/hudson_commuters.csv ({len(hudson):,} rows) "
          f"and total_workers.csv ({len(total):,} rows)")


if __name__ == "__main__":
    main()
