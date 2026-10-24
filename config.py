"""
config.py — paths and constants shared by every script in the pipeline.

Every script adds the project root to sys.path and does `import config`, so the
replication runs from any working directory and nothing is hard-coded twice.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# --- folders -----------------------------------------------------------------
RAW = ROOT / "data" / "raw"                  # as downloaded, never modified (git-ignored)
RAW_PLUTO = RAW / "pluto"
RAW_LODES = RAW / "lodes"
RAW_TRACTS = RAW / "tracts"
CLEAN = ROOT / "data" / "clean"              # one cleaned file per source
PROCESSED = ROOT / "data" / "processed"      # analysis files built from several sources
RESULTS = ROOT / "empirics" / "results"
FIGURES = RESULTS / "figures"
TABLES = RESULTS / "tables"
BASELINE = ROOT / "archive" / "baseline"     # frozen outputs for check_replication.py

# --- sample ------------------------------------------------------------------
YEARS = list(range(2009, 2021))              # 2009-2020, as in the submitted paper
SUBWAY_YEAR = 2015                           # 34 St-Hudson Yards station opened 13 Sep 2015

# Hudson Yards = Manhattan census tract 99.
#  - PLUTO (2010 tract definitions) has one tract, 009900.
#  - LODES 8 uses 2020 blocks, where tract 99 is split into 99.01, 99.02, 99.03.
#    009900 is kept in the list as in the original notebook (it has no flows in LODES 8).
HY_TRACT_PLUTO = "36061009900"
HY_TRACTS_LODES = ["36061009903", "36061009902", "36061009901", "36061009900"]

# Home tracts in Panel B: the five NYC counties (pygris county names -> FIPS).
NYC_COUNTIES = {"005": "Bronx County", "047": "Kings County", "061": "New York County",
                "081": "Queens County", "085": "Richmond County"}

# Panel B distance bins (km, left-closed), exactly as in the original notebook.
DIST_EDGES = [0, 1, 3, 5, 7, 10, float("inf")]
DIST_LABELS = ["<1 km", "1–3 km", "3–5 km", "5–7 km", "7–10 km", ">10 km"]

SQFT_TO_SQM = 0.092903
FEET_TO_KM = 0.0003048
CRS_FEET = 2263                              # NAD83 / New York Long Island (ftUS)

# --- raw files ---------------------------------------------------------------
# PLUTO: one archived DCP release per year. (zip in data/raw/pluto, Manhattan member, tract column)
# 2009-2017 releases are split by borough; 2018-2020 are citywide and filtered to borough == "MN".
PLUTO_RELEASES = {
    2009: ("nyc_pluto_09v2.zip",          "MN09v2.txt",                   "Tract2000"),
    2010: ("nyc_pluto_10v2.zip",          "mn10v2.txt",                   "Tract2000"),
    2011: ("nyc_pluto_11v2.zip",          "mn11v2.txt",                   "Tract2010"),
    2012: ("nyc_pluto_12v2.zip",          "mn12v2.txt",                   "Tract2010"),
    2013: ("nyc_pluto_13v2.zip",          "MN.csv",                       "Tract2010"),
    2014: ("nyc_pluto_14v2.zip",          "MN.csv",                       "Tract2010"),
    2015: ("nyc_pluto_15v1.zip",          "Mn.csv",                       "Tract2010"),
    2016: ("nyc_pluto_16v2.zip",          "BORO_zip_files_csv/MN.csv",    "Tract2010"),
    2017: ("nyc_pluto_17v1_1.zip",        "PLUTO17v1.1/MN2017V11.csv",    "Tract2010"),
    2018: ("nyc_pluto_18v2_1_csv.zip",    "pluto_18v2_1.csv",             "tract2010"),
    2019: ("nyc_pluto_19v2_csv.zip",      "pluto_19v2.csv",               "tract2010"),
    2020: ("nyc_pluto_20v8_arc_csv.zip",  "pluto_20v8.csv",               "tract2010"),
}
# Variables summed to the tract level (original notebook, cell "Pluto_agg").
PLUTO_VARS = ["LotArea", "BldgArea", "ComArea", "ResArea", "OfficeArea", "RetailArea",
              "GarageArea", "StrgeArea", "FactryArea", "OtherArea", "NumBldgs", "NumFloors",
              "UnitsRes", "UnitsTotal", "AssessLand", "AssessTot"]

# LODES 8 origin-destination, main file (home and work in NY), JT01 = primary jobs.
LODES_FILE = "ny_od_main_JT01_{year}.csv.gz"
LODES_URL = "https://lehd.ces.census.gov/data/lodes/LODES8/ny/od/ny_od_main_JT01_{year}.csv.gz"

# 2020 cartographic-boundary tracts for NY — the file pygris.tracts(state="NY", cb=True, year=2020) fetches.
TRACTS_FILE = "cb_2020_36_tract_500k.zip"
TRACTS_URL = "https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_36_tract_500k.zip"


def lodes_path(year: int) -> Path:
    """LODES file for a year; accepts the uncompressed .csv as well (same content)."""
    gz = RAW_LODES / LODES_FILE.format(year=year)
    return gz if gz.exists() else gz.with_suffix("")
