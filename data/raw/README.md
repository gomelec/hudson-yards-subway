# Raw data — as downloaded, never modified

Not in git (≈2.3 GB compressed). `uv run python master.py --stage collection` downloads everything;
files that are already present are skipped and each new file is checked against the MD5 of the copy used
for the paper (`data/scripts/collection/raw_manifest.csv`; a mismatch is a warning, e.g. after a re-release).
If you already have the files, `uv run python master.py --stage collection --link-from DIR` symlinks them.

| Folder | File(s) | Source | Used by |
|---|---|---|---|
| `pluto/` | `nyc_pluto_09v2.zip`, `_10v2`, `_11v2`, `_12v2`, `_13v2`, `_14v2`, `_15v1`, `_16v2`, `_17v1_1`, `_18v2_1_csv`, `_19v2_csv`, `_20v8_arc_csv` | NYC Department of City Planning, PLUTO archive ("Bytes of the Big Apple" archive, PLUTO). Downloaded July 2025. | `clean_pluto.py` (Manhattan file in each zip) |
| `lodes/` | `ny_od_main_JT01_2009.csv.gz` … `_2020.csv.gz` | U.S. Census Bureau, LEHD Origin-Destination Employment Statistics, LODES 8, https://lehd.ces.census.gov/data/lodes/LODES8/ny/od/. Downloaded 2023–2025 (the uncompressed .csv is accepted too). | `clean_lodes.py` |
| `tracts/` | `cb_2020_36_tract_500k.zip` | U.S. Census Bureau, 2020 cartographic boundary files, census tracts, New York, 1:500,000, https://www2.census.gov/geo/tiger/GENZ2020/shp/ (the file `pygris.tracts(state="NY", cb=True, year=2020)` uses) | `build_commute_distance.py` |

**Manual download.** If an automatic download fails (the DCP archive has moved several times), download
the file in a browser and put it, unchanged, into the folder above:
PLUTO archive — https://www.nyc.gov/site/planning/data-maps/open-data/bytes-archive.page (section PLUTO);
LODES and tracts — the URLs in the table.
