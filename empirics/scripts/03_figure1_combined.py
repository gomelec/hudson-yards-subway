"""
03_figure1_combined.py — Figure 1 of the paper: Panel A above Panel B.

The original combined figure (project/Figures/Combined_Panels_A_B.png) was assembled from the two
panel images by hand; here it is drawn in one matplotlib figure from the saved panel tables.

Input : empirics/results/tables/panel_a_built_area.csv, panel_b_commuters_by_distance.csv
Output: empirics/results/figures/fig1_combined.png / .pdf
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config  # noqa: E402
from figure_style import draw_panel_a, draw_panel_b, save  # noqa: E402


def main():
    a = pd.read_csv(config.TABLES / "panel_a_built_area.csv")
    b = pd.read_csv(config.TABLES / "panel_b_commuters_by_distance.csv")
    fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(10, 10))
    draw_panel_a(ax_a, a)
    draw_panel_b(ax_b, b)
    fig.tight_layout()
    save(fig, "fig1_combined")


if __name__ == "__main__":
    main()
