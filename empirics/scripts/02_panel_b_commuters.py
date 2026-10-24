"""
02_panel_b_commuters.py — Figure 1, Panel B: Hudson Yards commuters per 1,000 workers by distance,
before and after the subway opening.

Origin: notebook `LODES Data/distance graph in matplotlib.ipynb` (cell 13), logic unchanged.
For each period and distance bin: mean of commuters per 1,000 workers over all
(home tract x HY destination tract x year) rows, with a 95% interval 1.96 * sd / sqrt(n).

Input : data/processed/commute_distance.csv
Output: empirics/results/tables/panel_b_commuters_by_distance.csv
        empirics/results/figures/fig1_panel_b.png / .pdf
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config  # noqa: E402
from figure_style import draw_panel_b, save  # noqa: E402


def main():
    df = pd.read_csv(config.PROCESSED / "commute_distance.csv")
    df["distance_bin"] = pd.Categorical(df["distance_bin"], categories=config.DIST_LABELS, ordered=True)

    grouped = (df.groupby(["period", "distance_bin"], observed=True)["hudson_workers_per_1000"]
                 .agg(["mean", "std", "count"])
                 .reset_index()
                 .rename(columns={"mean": "avg", "std": "stddev", "count": "n"}))
    grouped["ci95"] = 1.96 * grouped["stddev"] / np.sqrt(grouped["n"])

    config.TABLES.mkdir(parents=True, exist_ok=True)
    grouped.to_csv(config.TABLES / "panel_b_commuters_by_distance.csv", index=False)
    print(grouped.round(3).to_string(index=False))

    fig, ax = plt.subplots(figsize=(10, 5))
    draw_panel_b(ax, grouped)
    fig.tight_layout()
    save(fig, "fig1_panel_b")


if __name__ == "__main__":
    main()
