"""
clean_pluto.py — Manhattan PLUTO 2009-2020 aggregated to census tract x year.

Origin: notebooks `Pluto/Translate pluto txt to csv.ipynb` and `Pluto/Graph buildings.ipynb`
(identical cleaning code in both). The logic is unchanged; only file handling differs:
the Manhattan file is read straight from each archived DCP zip instead of from an
extracted copy, and only the columns that are used are read (sums are unaffected).

Steps (decision numbers refer to data/README.md):
  L1  one PLUTO release per year 2009-2020 (PLUTO_RELEASES in config.py)
  L2  2018-2020 releases are citywide -> keep borough == "MN"
  L3  tract code normalised to 6 digits: left-pad to 4, right-pad to 6
      ("99" -> "0099" -> "009900"; "99.01" is stored as "9901" -> "009901")
  L4  11-digit tract GEOID = "36" + "061" + 6-digit tract
  L5  2009-2010 use the 2000 tract variable (Tract2000), 2011-2020 the 2010 one (Tract2010)
  L6  floor areas, building and unit counts and assessed values summed over tax lots

Input : data/raw/pluto/nyc_pluto_*.zip
Output: data/clean/pluto/pluto_agg_MN_all_years.csv   (one row per tract x year)
"""
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import config  # noqa: E402

OUT = config.CLEAN / "pluto" / "pluto_agg_MN_all_years.csv"


def normalize_tract6(val):
    """L3 — original notebook function, unchanged."""
    if pd.isna(val):
        return None
    val = val.strip().zfill(4)  # at least 4 digits
    return val.ljust(6, "0")    # pad right side to 6 digits


def full_tract(df, tract_col, borough_num="061"):
    """L4 — original notebook function, unchanged (Manhattan = county 061)."""
    df["full_tract"] = np.where(
        df[tract_col].notna(),
        "36" + borough_num + df[tract_col].astype(str).str.zfill(6),
        np.nan,
    )
    return df


def read_release(year):
    zip_name, member, tract_col = config.PLUTO_RELEASES[year]
    path = config.RAW_PLUTO / zip_name
    with zipfile.ZipFile(path) as z:
        # case-insensitive member lookup (e.g. 15v1 ships "Mn.csv")
        names = {n.lower(): n for n in z.namelist()}
        with z.open(names[member.lower()]) as f:
            header = pd.read_csv(f, nrows=0).columns
        citywide = "borough" in header and tract_col.islower()
        wanted = {c.lower() for c in config.PLUTO_VARS} | {tract_col.lower(), "borough"}
        usecols = [c for c in header if c.lower() in wanted]
        with z.open(names[member.lower()]) as f:
            df = pd.read_csv(f, usecols=usecols, dtype={tract_col: str}, low_memory=False)
    if citywide:                                                   # L2
        df = df[df["borough"] == "MN"].copy()
    print(f"{year}: {zip_name}/{member}: {len(df):,} Manhattan tax lots")
    return df, tract_col


def main():
    frames = []
    for year in config.YEARS:
        df, tract_col = read_release(year)
        df[tract_col] = df[tract_col].apply(normalize_tract6)          # L3
        df = full_tract(df, tract_col)                                  # L4, L5
        df["year"] = year
        df.columns = [c if c in ("full_tract", "year") else c.lower() for c in df.columns]
        agg = (df.groupby(["full_tract", "year"])[[c.lower() for c in config.PLUTO_VARS]]
                 .agg("sum").reset_index())                             # L6
        frames.append(agg)

    out = pd.concat(frames).sort_values(by=["full_tract", "year"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"\nwrote {OUT.relative_to(config.ROOT)}: {len(out):,} tract-years, "
          f"{out['full_tract'].nunique()} tracts")
    hy = out[out["full_tract"] == config.HY_TRACT_PLUTO][["year", "bldgarea", "comarea", "officearea"]]
    print(f"\nHudson Yards tract {config.HY_TRACT_PLUTO} (sq ft):\n{hy.to_string(index=False)}")


if __name__ == "__main__":
    main()
