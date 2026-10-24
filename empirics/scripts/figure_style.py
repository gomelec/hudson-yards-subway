"""
figure_style.py — drawing functions for Figure 1, shared by the panel scripts and the combined figure.

Styling copied from the original notebooks (`Pluto/Graph buildings.ipynb`, Panel A;
`LODES Data/distance graph in matplotlib.ipynb`, Panel B).
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # no display needed; must come before pyplot
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config  # noqa: E402

PANEL_A_LABELS = {"bldgarea_sqm": "Total Built Area",
                  "comarea_sqm": "Commercial Area",
                  "officearea_sqm": "Office Space Area"}
PANEL_B_PERIODS = [("Before 2015", "blue", "lightblue"),
                   ("After 2015 (inclusive)", "red", "lightcoral")]


def millions(x, pos):
    return f"{x * 1e-6:.1f}M"


def draw_panel_a(ax, data):
    """data: year + bldgarea_sqm, comarea_sqm, officearea_sqm for the Hudson Yards tract."""
    for col, label in PANEL_A_LABELS.items():
        ax.plot(data["year"], data[col], label=label)
    ax.axvline(x=config.SUBWAY_YEAR, color="#C91441", linestyle="--", linewidth=2)
    ax.text(config.SUBWAY_YEAR + 0.1, ax.get_ylim()[1] * 0.95, "Subway opens (September 2015)", color="#800020")
    ax.set_title("Panel A. Area Built in Hudson Yards", fontsize=14)
    ax.set_xlabel("Year", fontsize=13)
    ax.set_ylabel("Area (sq. meters)", fontsize=13)
    ax.legend(fontsize=11, loc="upper left")
    ax.grid(True)
    ax.yaxis.set_major_formatter(FuncFormatter(millions))


def draw_panel_b(ax, grouped):
    """grouped: period, distance_bin, avg, ci95 (one row per period x bin)."""
    bins = config.DIST_LABELS
    for period, color, ci_color in PANEL_B_PERIODS:
        df = grouped[grouped["period"] == period].set_index("distance_bin").reindex(bins)
        ax.plot(bins, df["avg"], label=period, color=color, marker="o")
        ax.fill_between(bins, df["avg"] - df["ci95"], df["avg"] + df["ci95"],
                        color=ci_color, alpha=0.3, label="_nolegend_")
    ax.set_title("Panel B. Hudson Yards Commuters per 1000 Workers in a Census Tract", fontsize=14)
    ax.set_xlabel("Distance Bin", fontsize=13)
    ax.set_ylabel("Avg. Commuters per 1000", fontsize=13)
    ax.legend(fontsize=11, loc="lower left")
    ax.set_ylim(bottom=0)
    ax.grid(True)


def save(fig, stem):
    config.FIGURES.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(config.FIGURES / f"{stem}.{ext}", dpi=150 if ext == "png" else None, bbox_inches="tight")
    plt.close(fig)
    print(f"saved empirics/results/figures/{stem}.png and .pdf")
