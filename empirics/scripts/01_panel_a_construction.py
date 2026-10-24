"""
01_panel_a_construction.py — Figure 1, Panel A: built area in Hudson Yards, 2009-2020.

Origin: notebook `Pluto/Graph buildings.ipynb` (cells 16-19), logic unchanged.
Total, commercial and office floor area of the Hudson Yards tract (PLUTO tract 009900),
converted from square feet to square metres.

Input : data/clean/pluto/pluto_agg_MN_all_years.csv
Output: empirics/results/tables/panel_a_built_area.csv
        empirics/results/figures/fig1_panel_a.png / .pdf
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config  # noqa: E402
from figure_style import draw_panel_a, save  # noqa: E402

AREA_COLS = ["lotarea", "bldgarea", "comarea", "resarea", "officearea",
             "retailarea", "garagearea", "strgearea", "factryarea", "otherarea"]


def convert_sqft_to_sqm(df, area_columns, suffix="_sqm"):
    for col in area_columns:
        df[f"{col}{suffix}"] = df[col] * config.SQFT_TO_SQM
    return df


def main():
    pluto = pd.read_csv(config.CLEAN / "pluto" / "pluto_agg_MN_all_years.csv", dtype={"full_tract": str})
    pluto = convert_sqft_to_sqm(pluto, AREA_COLS)
    sqm_cols = ["bldgarea_sqm", "comarea_sqm", "officearea_sqm"]
    data = (pluto[pluto["full_tract"] == config.HY_TRACT_PLUTO]
            .groupby("year")[sqm_cols].sum().reset_index())

    config.TABLES.mkdir(parents=True, exist_ok=True)
    data.to_csv(config.TABLES / "panel_a_built_area.csv", index=False)
    print(data.round(0).to_string(index=False))

    fig, ax = plt.subplots(figsize=(10, 5))
    draw_panel_a(ax, data)
    fig.tight_layout()
    save(fig, "fig1_panel_a")


if __name__ == "__main__":
    main()
