"""
build_commute_distance.py — Hudson Yards commuters per 1,000 workers and distance to Hudson Yards,
by NYC home tract, destination tract and year (the data behind Figure 1, Panel B).

Origin: notebook `LODES Data/distance graph in matplotlib.ipynb`, functions
`compute_hudson_share` and `attach_geometries_and_distance` and the cell that pools the years
(logic unchanged). The tract boundaries are read from the Census file that
`pygris.tracts(state="NY", cb=True, county=[five NYC counties], year=2020)` downloads.

Steps (decision numbers refer to data/README.md):
  D1  home tracts = all 2020 cartographic-boundary tracts in the five NYC counties
  D2  commuters per 1,000 = 1000 * hudson_workers / total_workers of the home tract
  D3  distance = shortest distance between the home-tract polygon and the HY destination-tract
      polygon (EPSG:2263, feet -> km, rounded to 2 decimals); adjacent tracts have distance 0
  D4  NYC tracts with no HY commuters in a year keep one row with missing values and drop out
      of the averages in Panel B
  D5  period: "Before 2015" for 2009-2014, "After 2015 (inclusive)" for 2015-2020
  D6  distance bins <1, 1-3, 3-5, 5-7, 7-10, >10 km (left-closed)

Input : data/clean/lodes/hudson_commuters.csv, data/clean/lodes/total_workers.csv,
        data/raw/tracts/cb_2020_36_tract_500k.zip
Output: data/processed/commute_distance.csv
"""
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import config  # noqa: E402

OUT = config.PROCESSED / "commute_distance.csv"


def load_nyc_tracts():
    """D1 — equivalent of pygris.tracts(state='NY', cb=True, county=[...], year=2020)."""
    gdf = gpd.read_file(f"zip://{config.RAW_TRACTS / config.TRACTS_FILE}")
    gdf = gdf[gdf["COUNTYFP"].isin(config.NYC_COUNTIES)].reset_index(drop=True)
    print(f"NYC tracts: {len(gdf):,} (CRS {gdf.crs})")
    return gdf


def compute_hudson_share(hudson_df, total_df):
    """D2 — commuters per 1,000 workers of the home tract."""
    return (hudson_df.merge(total_df, on="h_trct", how="left")
                     .assign(hudson_workers_per_1000=lambda d: 1000 * d["hudson_workers"] / d["total_workers"]))


def attach_geometries_and_distance(stats, ny_tracts, crs_epsg=config.CRS_FEET):
    """D3, D4 — home and work tract geometry, polygon-to-polygon distance in km."""
    home = ny_tracts.merge(stats, left_on="GEOID", right_on="h_trct", how="left")        # all NYC tracts
    w_geom = (ny_tracts[["GEOID", "geometry"]]
              .rename(columns={"GEOID": "w_trct"})
              .rename_geometry("w_geometry"))
    merged = home.merge(pd.DataFrame(w_geom), on="w_trct", how="left")
    merged = merged.to_crs(epsg=crs_epsg)
    w = gpd.GeoSeries(merged["w_geometry"], crs=ny_tracts.crs).to_crs(epsg=crs_epsg)
    merged["tract_distance"] = merged.geometry.distance(w)
    merged["distance_km"] = (merged["tract_distance"] * config.FEET_TO_KM).round(2)
    return merged.drop(columns=["w_geometry"])


def main():
    hudson = pd.read_csv(config.CLEAN / "lodes" / "hudson_commuters.csv", dtype={"h_trct": str, "w_trct": str})
    total = pd.read_csv(config.CLEAN / "lodes" / "total_workers.csv", dtype={"h_trct": str})
    ny_tracts = load_nyc_tracts()

    frames = []
    for year in config.YEARS:
        stats = compute_hudson_share(hudson[hudson["year"] == year].drop(columns="year"),
                                     total[total["year"] == year].drop(columns="year"))
        frames.append(attach_geometries_and_distance(stats, ny_tracts).assign(year=year))
    df = pd.concat(frames, ignore_index=True)

    df["period"] = df["year"].apply(lambda y: "Before 2015" if y < config.SUBWAY_YEAR
                                    else "After 2015 (inclusive)")                      # D5
    df["distance_bin"] = pd.cut(df["distance_km"], bins=config.DIST_EDGES,
                                labels=config.DIST_LABELS, right=False)                  # D6

    keep = ["year", "period", "GEOID", "h_trct", "w_trct", "hudson_workers", "total_workers",
            "hudson_workers_per_1000", "distance_km", "distance_bin"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df[keep].to_csv(OUT, index=False)
    n_flow = df["hudson_workers"].notna().sum()
    print(f"wrote {OUT.relative_to(config.ROOT)}: {len(df):,} rows, {n_flow:,} with HY commuters")
    print(df[df["hudson_workers"].notna()].groupby("year")
            .agg(home_tracts=("GEOID", "nunique"), hy_workers=("hudson_workers", "sum")).to_string())


if __name__ == "__main__":
    main()
