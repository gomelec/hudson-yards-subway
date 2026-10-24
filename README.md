# Subway Opening in the Process of Urban Revival: Hudson Yards, New York City

**How does a new subway station change who commutes into a redeveloping neighbourhood?**

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Data](https://img.shields.io/badge/data-PLUTO%20%7C%20LODES%202009%E2%80%932020-555)
![Status](https://img.shields.io/badge/status-replication%20package-2e7d32)

Fedor Shafranov — final assignment, Housing course, LMU Munich (July 2025).
Paper: [`Writing/main.pdf`](Writing/main.pdf) (LaTeX rebuild) · as submitted:
[`Writing/original/Fedor_Shafranov_Housing.pdf`](Writing/original/Fedor_Shafranov_Housing.pdf)

---

## The fact

Hudson Yards on Manhattan's Far West Side was mostly rail yards and vacant land until a large,
privately led redevelopment started in 2012. In September 2015 the **34 St–Hudson Yards** station
(7 line) opened — the last case of a new NYC subway station built into an essentially new neighbourhood.

1. **Construction accelerates after the opening.** Built floor area in the Hudson Yards census tract
   rises from about 2.1 million m² in 2015 to 3.1 million m² in 2016 and 3.5 million m² in 2020;
   office space doubles (Panel A).
2. **Commuters come from farther away.** In every distance bin except the closest (< 1 km), the
   number of Hudson Yards commuters per 1,000 workers in a home tract is higher after 2015 than before;
   in the closest bin it falls (Panel B).

![Figure 1](empirics/results/figures/fig1_combined.png)

*Figure 1. Panel A: total, commercial and office floor area in census tract 99 (Manhattan), PLUTO,
square metres; dashed line = subway opening. Panel B: average number of workers commuting to the Hudson
Yards tracts per 1,000 workers living in a NYC census tract, by distance between the home tract and the
Hudson Yards tract; 2009–2014 vs. 2015–2020, shaded areas are 95 % confidence intervals of the mean.*

## Data

| Source | Years | Unit | Used for |
|---|---|---|---|
| [PLUTO](https://www.nyc.gov/site/planning/data-maps/open-data/dwn-pluto-mappluto.page), NYC Department of City Planning (archived releases 09v2 … 20v8) | 2009–2020 | tax lot → census tract | Panel A: floor area by use |
| [LODES 8](https://lehd.ces.census.gov/data/#lodes) origin–destination, NY, main file, all primary jobs (JT01), U.S. Census Bureau | 2009–2020 | census block pair → tract pair | Panel B: commuters by home tract |
| [2020 cartographic-boundary census tracts](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.2020.html), NY, 1:500k, U.S. Census Bureau | 2020 | tract polygons | Panel B: distance to Hudson Yards |

Every cleaning and construction decision is listed in [`data/README.md`](data/README.md).
**Raw data (~2.3 GB compressed) are not included**; `master.py` downloads them into `data/raw/`
(see [`data/raw/README.md`](data/raw/README.md)).

## Reproduce

Requirements: [uv](https://docs.astral.sh/uv/) (installs Python 3.13 and the packages from `uv.lock`).

```bash
uv sync                                 # Python environment
uv run python master.py                 # download raw data, clean, build, draw Figure 1
uv run python master.py --check         # ... and compare with the original output and the frozen baseline
```

Other options: `--list` (show steps), `--stage cleaning` / `--only panel_b` / `--from processing`
(partial runs), `--link-from DIR` (use raw files you already have instead of downloading),
`--set-baseline` (freeze current outputs). Each step writes a log to `logs/`.
A full run takes about 1 minute plus download time on a laptop.

### Pipeline

| Stage | Script | Output |
|---|---|---|
| collection | `data/scripts/collection/download_raw.py` | `data/raw/{pluto,lodes,tracts}/` (checksums: `raw_manifest.csv`) |
| cleaning | `data/scripts/cleaning/clean_pluto.py` | `data/clean/pluto/pluto_agg_MN_all_years.csv` — Manhattan tract × year |
| cleaning | `data/scripts/cleaning/clean_lodes.py` | `data/clean/lodes/hudson_commuters.csv`, `total_workers.csv` |
| processing | `data/scripts/processing/build_commute_distance.py` | `data/processed/commute_distance.csv` — shares and distances |
| empirics | `empirics/scripts/01_panel_a_construction.py` | Figure 1A + `empirics/results/tables/panel_a_built_area.csv` |
| empirics | `empirics/scripts/02_panel_b_commuters.py` | Figure 1B + `empirics/results/tables/panel_b_commuters_by_distance.csv` |
| empirics | `empirics/scripts/03_figure1_combined.py` | Figure 1 (`empirics/results/figures/fig1_combined.png/.pdf`) |
| writing | `Writing/scripts/build_paper.py` | `Writing/main.pdf` (skipped without LaTeX) |
| check | `data/scripts/checks/check_replication.py` | compares outputs with `archive/legacy_outputs/` and `archive/baseline/` |

Paths and constants (years, tract codes, distance bins) are set once in [`config.py`](config.py).

### Replication status

The scripts are a one-to-one translation of the original Jupyter notebooks (kept in
[`archive/original_notebooks/`](archive/original_notebooks/)); no method was changed.

- **Panel A** — the cleaned PLUTO tract panel is identical, cell by cell, to the file the original
  notebook saved (3,479 tract-years; `archive/legacy_outputs/`), and the figure matches the submitted one.
- **Panel B** — the six distance-bin means for both periods reproduce the submitted figure
  (e.g. < 1 km: 8.12 before vs. 6.85 after; 1–3 km: 3.71 vs. 4.38).

All outputs are frozen in `archive/baseline/`; `master.py --check` reports any change.

## Repository structure

```
master.py, config.py          run everything / shared settings
data/raw/                     raw downloads (not in git)
data/scripts/                 collection, cleaning, processing, checks
data/clean/, data/processed/  generated data (not in git)
empirics/scripts/             figure scripts
empirics/results/             figures and the tables behind them
Writing/                      the paper (LaTeX) and the submitted PDF
archive/                      original notebooks, legacy output, frozen baseline
```

## Citation

Shafranov, F. (2025). *Subway Opening in the Process of Urban Revival.* Final assignment, Housing,
LMU Munich. Replication package, https://github.com/gomelec/hudson-yards-subway.
