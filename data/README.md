# Data construction: decisions log

Every cleaning and construction decision in the pipeline, by dataset, with the script where it happens.
Tags: **[original]** = decision taken in the original notebooks (carried over unchanged);
**[refactor]** = change in *how* the code does it, with identical results;
**[open]** = known issue, not resolved (candidates for the robustness analysis).

---

## 1. PLUTO — `data/scripts/cleaning/clean_pluto.py` → `data/clean/pluto/pluto_agg_MN_all_years.csv`

One row per Manhattan census tract × year, 2009–2020 (3,479 rows, 378 tracts).

| # | Decision | Tag |
|---|---|---|
| L1 | One archived PLUTO release per year: 09v2, 10v2, 11v2, 12v2, 13v2, 14v2, 15v1, 16v2, 17v1.1, 18v2.1, 19v2, 20v8 (`config.PLUTO_RELEASES`). | [original] |
| L1a | The Manhattan file is read directly from the release zip instead of from a hand-extracted copy; only the columns used are read. Output identical to the original notebook (checked by `check_replication.py`). | [refactor] |
| L2 | 2018–2020 releases are citywide; keep `borough == "MN"`. | [original] |
| L3 | Tract code normalised to 6 digits: left-pad to 4, then right-pad to 6 (`"99"` → `"009900"`, `"9901"` → `"009901"`). | [original] |
| L4 | 11-digit GEOID = `36` (NY) + `061` (New York County) + 6-digit tract. | [original] |
| L5 | 2009–2010 use the 2000 census tract variable (`Tract2000`), 2011–2020 the 2010 one (`Tract2010`). | [original] |
| L6 | Floor areas (lot, building, commercial, residential, office, retail, garage, storage, factory, other), number of buildings, floors and units, and assessed values summed over tax lots in a tract. | [original] |
| L7 | Hudson Yards = tract 009900. PLUTO has no split into 99.01–99.03. | [original] |
| L-open-1 | Tract boundaries change between the 2000 and 2010 censuses (L5); tract 99 is used for both without a crosswalk. | [open] |
| L-open-2 | PLUTO records the *stock* of floor area as assessed by the Department of Finance; a building enters when it is assessed, not when construction starts or ends. | [open] |

## 2. LODES — `data/scripts/cleaning/clean_lodes.py` → `data/clean/lodes/`

| # | Decision | Tag |
|---|---|---|
| C1 | LODES 8 origin–destination "main" file for NY (home and work block in NY), job type JT01 (primary jobs), variable `S000` (all jobs). | [original] |
| C2 | Tract = first 11 digits of the 15-digit 2020 census block code. | [original] |
| C3 | Hudson Yards commuters = jobs with work tract in {36061009901, 36061009902, 36061009903, 36061009900}, summed by home tract × work tract. 009900 does not exist in 2020 geography and has no flows. | [original] |
| C4 | Total workers of a home tract = all its jobs, any NY work location. | [original] |
| C1a | Each yearly file is read once with only `w_geocode`, `h_geocode`, `S000`; geocodes read as text. | [refactor] |
| C-open-1 | Out-of-state commuters (NJ, CT) are not in the NY main file. | [open] |
| C-open-2 | LODES reports the job's establishment location; firms reporting all jobs at one address (e.g. a headquarters) can create spikes, e.g. tract 99.02 jumps from 5,860 jobs (2017) to 27,294 (2018) and back to 15,084 (2019). | [open] |
| C-open-3 | LODES counts jobs held at the start of the second quarter (reference date April 1); the station opened 13 September 2015, so LODES 2015 is pre-opening. | [open] |

## 3. Commuting and distance — `data/scripts/processing/build_commute_distance.py` → `data/processed/commute_distance.csv`

One row per NYC home tract × Hudson Yards destination tract × year (home tracts with no Hudson Yards
commuters in a year keep one row with missing values).

| # | Decision | Tag |
|---|---|---|
| D1 | Home tracts: 2020 cartographic-boundary tracts (`cb_2020_36_tract_500k`) in Bronx, Kings, New York, Queens, Richmond counties — the file and filter of `pygris.tracts(state="NY", cb=True, county=[…], year=2020)`. | [original] |
| D1a | The shapefile is downloaded once into `data/raw/tracts/` and read with geopandas instead of being fetched by pygris at run time. | [refactor] |
| D2 | Commuters per 1,000 = 1000 × Hudson Yards commuters / total workers of the home tract (C3/C4). | [original] |
| D3 | Distance = shortest distance between the home-tract polygon and the destination-tract polygon, in EPSG:2263 (feet) × 0.0003048, rounded to 0.01 km. | [original] |
| D4 | Home tracts without Hudson Yards commuters have missing share and distance and drop out of the Panel B means. | [original] |
| D5 | Periods: 2009–2014 = "Before 2015", 2015–2020 = "After 2015 (inclusive)". | [original] |
| D6 | Distance bins [0,1), [1,3), [3,5), [5,7), [7,10), [10,∞) km. | [original] |
| D-open-1 | D3 is an edge-to-edge distance: all adjacent tracts get 0 km; a centroid distance would be the usual alternative. | [open] |
| D-open-2 | D4 conditions on positive flows; as commuting spreads, more low-share tracts enter the sample, which changes the composition of each bin. | [open] |
| D-open-3 | Each home tract enters up to three times per year (one row per destination tract 99.01–99.03), so the means weight tract × destination pairs, not home tracts. | [open] |
| D-open-4 | Confidence intervals treat the pooled tract-year observations as independent. | [open] |

## 4. Figure — `empirics/scripts/`

| # | Decision | Tag |
|---|---|---|
| F1 | Panel A: total (`bldgarea`), commercial (`comarea`) and office (`officearea`) floor area of tract 009900, × 0.092903 to m². | [original] |
| F2 | Panel B: mean of D2 by period × distance bin; 95 % CI = 1.96 × sd / √n. | [original] |
| F3 | The combined figure is drawn as one matplotlib figure (the original was assembled from the two panel images). | [refactor] |

---

## Change log

| Date | Change |
|---|---|
| 2026-10-24 | Notebooks converted into the scripted pipeline (`master.py`); no change in methods. PLUTO output verified identical to the original. |
