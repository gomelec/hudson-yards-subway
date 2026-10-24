# Archive

| Folder | Content |
|---|---|
| `original_notebooks/` | The Jupyter notebooks as written for the course (July 2025), with hard-coded Windows paths. `Pluto/` and `LODES Data/distance graph in matplotlib.ipynb` produced the submitted figure and were translated into the scripts of the pipeline; `LODES Data/Data check.ipynb` and the other notebooks are exploration (single-tract time series, maps, Detroit, amenities). Kept for reference; not run by `master.py`. |
| `legacy_outputs/` | `pluto_agg_MN_all_years.csv` — the only intermediate file the original notebooks saved; `check_replication.py` compares the new PLUTO output with it. |
| `baseline/` | Frozen copies of the pipeline outputs (`master.py --set-baseline`); `master.py --check` reports any change. |
