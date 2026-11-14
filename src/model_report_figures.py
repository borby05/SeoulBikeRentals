"""Draws the two charts used in the Seoul Bike Rentals model report.

Run from the repository root:
    python src/model_report_figures.py
The PNG files land in reports/figures.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path("reports/figures")
OUT.mkdir(parents=True, exist_ok=True)

GREEN, LIGHT, GREY, INK = "#196B24", "#A9D3AE", "#9CA3AF", "#1F2937"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False})

# Test scores (October and November 2018), copied from the results tables in notebook 06
MODEL_MAE = {
    "Gradient boosting": 220.9,
    "Random forest": 223.7,
    "Hour and weekend mean": 272.9,
    "Linear regression": 296.0,
    "Hour mean": 298.5,
    "Overall mean": 452.1,
}
BAR_COLOURS = [GREEN, LIGHT, GREY, LIGHT, GREY, GREY]  # model, model, baseline, model, baseline, baseline

MONTH_CHECK = {  # model: (MAE with month, MAE without month)
    "Gradient boosting": (220.9, 254.1),
    "Random forest": (223.7, 262.2),
    "Linear regression": (296.0, 309.5),
}


def figure_1():
    """Horizontal bars: test MAE for every model and baseline."""
    names = list(MODEL_MAE)
    values = list(MODEL_MAE.values())
    ypos = list(range(len(names)))[::-1]  # best model at the top

    fig, ax = plt.subplots(figsize=(8.4, 3.4), dpi=170)
    ax.barh(ypos, values, color=BAR_COLOURS, height=0.62)
    for y, v in zip(ypos, values):
        ax.text(v + 6, y, f"{v:,.1f}", va="center", fontsize=9, color=INK)
    ax.set_yticks(ypos)
    ax.set_yticklabels(names, fontsize=9, color=INK)
    ax.set_xlim(0, 520)
    ax.set_xlabel("MAE, rentals per hour (lower is better)", fontsize=9, color=INK)
    ax.set_title("Test error by model, October and November 2018",
                 fontsize=11, fontweight="bold", color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(OUT / "model_fig1_mae_by_model.png")
    plt.close(fig)


def figure_2():
    """Grouped bars: test MAE with and without the month input."""
    names = list(MONTH_CHECK)
    with_month = [MONTH_CHECK[n][0] for n in names]
    without_month = [MONTH_CHECK[n][1] for n in names]
    x = np.arange(len(names))

    fig, ax = plt.subplots(figsize=(8.4, 3.4), dpi=170)
    bars_a = ax.bar(x - 0.19, with_month, 0.36, color=GREEN, label="With month")
    bars_b = ax.bar(x + 0.19, without_month, 0.36, color=GREY, label="Without month")
    for bars in (bars_a, bars_b):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                    f"{bar.get_height():,.1f}", ha="center", fontsize=9, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=9, color=INK)
    ax.set_ylim(0, 380)
    ax.set_ylabel("MAE, rentals per hour", fontsize=9, color=INK)
    ax.set_title("Test error with and without the month input",
                 fontsize=11, fontweight="bold", color=INK, loc="left")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT / "model_fig2_month_check.png")
    plt.close(fig)


if __name__ == "__main__":
    figure_1()
    figure_2()
    print("Saved to", OUT.resolve())
