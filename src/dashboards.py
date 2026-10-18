"""Dashboards for the Seoul bike rental project.

One function per business question. Each function draws one figure with a
headline strip, several panels, direct labels and a saved PNG. Colours follow
a validated three-slot palette. No chart uses two y-axes.
"""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Patch

from src.analysis import WEEK_ORDER

# Palette (light mode). Slots 1 to 3 pass all-pairs checks.
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
BLUE_LIGHT = "#86b6ef"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

SEQ = LinearSegmentedColormap.from_list(
    "seq_blue", ["#cde2fb", "#86b6ef", "#2a78d6", "#184f95", "#0d366b"]
)

DAY_TYPE_COLOURS = {"Weekday": BLUE, "Weekend": ORANGE, "Holiday": AQUA}


def _style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "font.family": "sans-serif",
            "font.size": 10,
            "text.color": INK,
            "axes.labelcolor": INK2,
            "axes.edgecolor": AXIS,
            "xtick.color": INK2,
            "ytick.color": INK2,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "axes.axisbelow": True,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.titlecolor": INK,
        }
    )


def _kpi_strip(ax, items) -> None:
    """Draw headline numbers. items = [(label, value, note), ...]."""

    ax.axis("off")
    n = len(items)
    for i, (label, value, note) in enumerate(items):
        x = (i + 0.5) / n
        ax.text(x, 0.74, label, ha="center", va="center", fontsize=10,
                color=INK2, transform=ax.transAxes)
        ax.text(x, 0.40, value, ha="center", va="center", fontsize=22,
                fontweight="bold", color=INK, transform=ax.transAxes)
        ax.text(x, 0.08, note, ha="center", va="center", fontsize=9,
                color=MUTED, transform=ax.transAxes)


def _date_axis(ax, dates=None) -> None:
    """Short date labels. Every 3 days for a month, automatic for longer spans."""

    span = 0
    if dates is not None and len(dates) > 1:
        span = (dates.max() - dates.min()).days
    if 0 < span <= 70:
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    else:
        locator = mdates.AutoDateLocator(minticks=5, maxticks=10)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))


def _finish(fig, title: str, subtitle: str, save_path) -> None:
    fig.suptitle(title, x=0.01, y=0.995, ha="left", fontsize=18,
                 fontweight="bold", color=INK)
    fig.text(0.01, 0.962, subtitle, ha="left", fontsize=11, color=INK2)
    if save_path is not None:
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.show()


def _bar_labels(ax, bars, fmt="{:,.0f}", pad=0.01, horizontal=False) -> None:
    for bar in bars:
        if horizontal:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height() / 2,
                    " " + fmt.format(width), va="center", ha="left",
                    fontsize=9, color=INK)
        else:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height,
                    fmt.format(height), va="bottom", ha="center",
                    fontsize=9, color=INK)


# ---------------------------------------------------------------- Question 1
def dashboard_daily(daily: pd.DataFrame, label: str, save_path=None):
    """Daily rentals: trend, extremes and day types."""

    _style()
    fig = plt.figure(figsize=(14, 11))
    gs = GridSpec(3, 2, height_ratios=[0.45, 2.1, 1.7], hspace=0.45,
                  wspace=0.28, top=0.92, bottom=0.06)

    total = int(daily["daily_rentals"].sum())
    mean = daily["daily_rentals"].mean()
    top = daily.loc[daily["daily_rentals"].idxmax()]
    low = daily.loc[daily["daily_rentals"].idxmin()]
    _kpi_strip(
        fig.add_subplot(gs[0, :]),
        [
            ("Total rentals", f"{total:,}", f"{len(daily)} days"),
            ("Mean per day", f"{mean:,.0f}", "rentals"),
            ("Busiest day", f"{top['daily_rentals']:,}",
             f"{top['date']:%a %b %d}"),
            ("Quietest day", f"{low['daily_rentals']:,}",
             f"{low['date']:%a %b %d}"),
        ],
    )

    # Panel 1: daily line with weekends shaded and a rolling mean.
    ax = fig.add_subplot(gs[1, :])
    for d in daily.loc[daily["day_type"] == "Weekend", "date"]:
        ax.axvspan(d - pd.Timedelta(hours=12), d + pd.Timedelta(hours=12),
                   color=MUTED, alpha=0.12, lw=0)
    ax.plot(daily["date"], daily["daily_rentals"], color=BLUE, lw=2,
            marker="o", ms=6, mfc=BLUE, mec=SURFACE, mew=1.5,
            label="Daily rentals")
    rolling = (daily.set_index("date")["daily_rentals"]
               .rolling(7, center=True, min_periods=4).mean())
    ax.plot(rolling.index, rolling.values, color=ORANGE, lw=2,
            label="7-day average")
    ax.text(rolling.index[-1], rolling.iloc[-1], "  7-day average",
            color=INK, fontsize=9, va="center")
    ax.set_ylim(0, daily["daily_rentals"].max() * 1.15)
    for d in daily.loc[daily["day_type"] == "Holiday", "date"]:
        ax.axvline(d, color=INK2, ls="--", lw=1)
        ax.text(d, ax.get_ylim()[1], " Holiday", color=INK2, fontsize=9,
                va="top")
    ax.annotate(f"Busiest {top['daily_rentals']:,}",
                (top["date"], top["daily_rentals"]),
                xytext=(10, 6), textcoords="offset points", fontsize=9,
                color=INK, va="bottom")
    ax.annotate(f"Quietest {low['daily_rentals']:,}",
                (low["date"], low["daily_rentals"]),
                xytext=(-10, -4), textcoords="offset points", fontsize=9,
                color=INK, va="top", ha="right")
    ax.legend(frameon=False, loc="lower left", fontsize=9)
    ax.set_title("Daily rentals (grey bands mark weekends)")
    ax.set_ylabel("Rentals per day")
    ax.margins(x=0.08)
    _date_axis(ax, daily["date"])

    # Panel 2: five best and five weakest days.
    ax = fig.add_subplot(gs[2, 0])
    best = daily.nlargest(5, "daily_rentals")
    worst = daily.nsmallest(5, "daily_rentals")
    ranked = pd.concat([best.assign(group="Top 5"),
                        worst.assign(group="Bottom 5")])
    ranked = ranked.sort_values("daily_rentals")
    names = [f"{d:%b %d} ({n[:3]})" for d, n in
             zip(ranked["date"], ranked["day_name"])]
    colours = [BLUE if g == "Top 5" else ORANGE for g in ranked["group"]]
    bars = ax.barh(names, ranked["daily_rentals"], color=colours,
                   height=0.65, edgecolor=SURFACE, linewidth=2)
    _bar_labels(ax, bars, horizontal=True)
    ax.set_xlim(0, ranked["daily_rentals"].max() * 1.15)
    ax.set_title("Five best and five weakest days")
    ax.set_xlabel("Rentals")
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[Patch(color=BLUE, label="Top 5"),
                       Patch(color=ORANGE, label="Bottom 5")],
              frameon=False, loc="lower right", fontsize=9)

    # Panel 3: mean daily rentals by day type.
    ax = fig.add_subplot(gs[2, 1])
    stats = (daily.groupby("day_type")["daily_rentals"]
             .agg(["mean", "count"])
             .reindex(["Weekday", "Weekend", "Holiday"]).dropna())
    bars = ax.bar(stats.index, stats["mean"],
                  color=[DAY_TYPE_COLOURS[i] for i in stats.index],
                  width=0.55, edgecolor=SURFACE, linewidth=2)
    _bar_labels(ax, bars)
    for bar, n in zip(bars, stats["count"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 0.5,
                f"{int(n)} day{'s' if n != 1 else ''}", ha="center",
                color="white", fontsize=9, fontweight="bold")
    ax.set_title("Mean rentals per day by day type")
    ax.set_ylabel("Rentals per day")
    ax.set_ylim(0, stats["mean"].max() * 1.15)
    ax.grid(axis="x", visible=False)

    _finish(fig, f"Question 1: How did daily rentals move in {label}?",
            "Daily totals, extremes and day types", save_path)
    return fig


# ---------------------------------------------------------------- Question 2
def dashboard_hourly(profile, by_type, shares, matrix, peaks,
                     label: str, save_path=None):
    """Hourly pattern: overall, by day type, by date and by time block."""

    _style()
    fig = plt.figure(figsize=(14, 12))
    gs = GridSpec(3, 2, height_ratios=[0.4, 1.8, 2.0], hspace=0.45,
                  wspace=0.28, top=0.92, bottom=0.05)

    busiest_block = shares.idxmax()
    _kpi_strip(
        fig.add_subplot(gs[0, :]),
        [
            ("Evening peak", f"{peaks['evening_hour']}:00",
             f"{peaks['evening_mean']:,.0f} rentals per hour"),
            ("Morning peak", f"{peaks['morning_hour']}:00",
             f"{peaks['morning_mean']:,.0f} rentals per hour"),
            ("Quietest hour", f"{peaks['trough_hour']}:00",
             f"{peaks['trough_mean']:,.0f} rentals per hour"),
            ("Busiest time block", busiest_block.split(" (")[0],
             f"{shares.max():.0f}% of rentals"),
        ],
    )

    # Panel 1: the typical day.
    ax = fig.add_subplot(gs[1, 0])
    ax.plot(profile.index, profile.values, color=BLUE, lw=2, marker="o",
            ms=6, mfc=BLUE, mec=SURFACE, mew=1.5)
    for hour, value, text in [
        (peaks["morning_hour"], peaks["morning_mean"], "Morning peak"),
        (peaks["evening_hour"], peaks["evening_mean"], "Evening peak"),
    ]:
        ax.annotate(f"{text}\n{hour}:00 · {value:,.0f}", (hour, value),
                    xytext=(0, 14), textcoords="offset points", ha="center",
                    fontsize=9, color=INK,
                    arrowprops=dict(arrowstyle="-", color=MUTED))
    ax.set_title("Typical day: mean rentals per hour")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Rentals per hour")
    ax.set_xticks(range(0, 24, 3))
    ax.set_ylim(0, profile.max() * 1.3)

    # Panel 2: weekday, weekend and holiday profiles.
    ax = fig.add_subplot(gs[1, 1])
    handles = []
    for column in ["Weekday", "Weekend", "Holiday"]:
        if column not in by_type.columns:
            continue
        series = by_type[column]
        style = "--" if column == "Holiday" else "-"
        ax.plot(series.index, series.values, color=DAY_TYPE_COLOURS[column],
                lw=2, ls=style)
        peak_x, peak_y = series.idxmax(), series.max()
        offset = {"Weekday": (8, 0), "Weekend": (0, 10), "Holiday": (0, -20)}
        dx, dy = offset.get(column, (0, 8))
        ax.annotate(column, (peak_x, peak_y), xytext=(dx, dy),
                    textcoords="offset points", fontsize=9, color=INK,
                    ha="left" if dx else "center", va="center")
        handles.append(plt.Line2D([], [], color=DAY_TYPE_COLOURS[column],
                                  lw=2, ls=style, label=column))
    ax.legend(handles=handles, frameon=False, fontsize=9, loc="upper left")
    ax.set_title("Weekday, weekend and holiday profiles")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Rentals per hour")
    ax.set_xticks(range(0, 24, 3))
    ax.set_xlim(0, 23)
    ax.set_ylim(0, by_type.max().max() * 1.1)

    # Panel 3: date by hour heatmap.
    ax = fig.add_subplot(gs[2, 0])
    sns.heatmap(matrix, ax=ax, cmap=SEQ, yticklabels=False,
                cbar_kws={"label": "Rentals", "shrink": 0.8},
                linewidths=0.4, linecolor=SURFACE)
    step = max(len(matrix) // 8, 1)
    ax.set_yticks([i + 0.5 for i in range(0, len(matrix), step)])
    ax.set_yticklabels([f"{d:%b %d}" for d in matrix.index[::step]],
                       rotation=0)
    ax.set_xticks([h + 0.5 for h in range(0, 24, 3)])
    ax.set_xticklabels(range(0, 24, 3), rotation=0)
    ax.set_title("Every day by hour (darker means busier)")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("")
    ax.grid(False)

    # Panel 4: share of rentals by time block.
    ax = fig.add_subplot(gs[2, 1])
    ordered = shares.iloc[::-1]
    bars = ax.barh(ordered.index, ordered.values, color=BLUE, height=0.6,
                   edgecolor=SURFACE, linewidth=2)
    _bar_labels(ax, bars, fmt="{:.0f}%", horizontal=True)
    ax.set_xlim(0, ordered.max() * 1.2)
    ax.set_title("Share of rentals by time block")
    ax.set_xlabel("Percent of all rentals")
    ax.grid(axis="y", visible=False)

    _finish(fig, f"Question 2: What does a typical day look like in {label}?",
            "Hourly pattern, day types and time blocks", save_path)
    return fig


# ---------------------------------------------------------------- Question 3
def dashboard_weekly(daily, weekly, weekday, matrix, label: str,
                     save_path=None):
    """Weeks and weekdays compared."""

    _style()
    fig = plt.figure(figsize=(14, 12))
    gs = GridSpec(3, 2, height_ratios=[0.4, 1.8, 2.0], hspace=0.45,
                  wspace=0.28, top=0.92, bottom=0.05)

    full = weekly[~weekly["is_partial"]]
    pool = full if not full.empty else weekly
    best_week = pool.loc[pool["mean_daily_rentals"].idxmax()]
    weak_week = pool.loc[pool["mean_daily_rentals"].idxmin()]
    best_day = weekday.loc[weekday["mean_daily_rentals"].idxmax()]
    weak_day = weekday.loc[weekday["mean_daily_rentals"].idxmin()]
    _kpi_strip(
        fig.add_subplot(gs[0, :]),
        [
            ("Strongest full week", f"Week {int(best_week['week_number'])}",
             f"{best_week['mean_daily_rentals']:,.0f} per day"),
            ("Weakest full week", f"Week {int(weak_week['week_number'])}",
             f"{weak_week['mean_daily_rentals']:,.0f} per day"),
            ("Strongest weekday", best_day["day_name"],
             f"{best_day['mean_daily_rentals']:,.0f} per day"),
            ("Weakest weekday", weak_day["day_name"],
             f"{weak_day['mean_daily_rentals']:,.0f} per day"),
        ],
    )

    # Panel 1: mean daily rentals per week.
    ax = fig.add_subplot(gs[1, 0])
    colours = [BLUE_LIGHT if p else BLUE for p in weekly["is_partial"]]
    bars = ax.bar([f"Week {w}" for w in weekly["week_number"]],
                  weekly["mean_daily_rentals"], color=colours, width=0.6,
                  edgecolor=SURFACE, linewidth=2)
    _bar_labels(ax, bars)
    for bar, days, partial in zip(bars, weekly["days"], weekly["is_partial"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 0.5,
                f"{days} days" + ("\n(partial)" if partial else ""),
                ha="center", color=INK if partial else "white", fontsize=9,
                fontweight="bold")
    ax.set_title("Mean rentals per day, by week")
    ax.set_ylabel("Rentals per day")
    ax.set_ylim(0, weekly["mean_daily_rentals"].max() * 1.15)
    ax.grid(axis="x", visible=False)
    if len(weekly) > 12:
        ax.tick_params(axis="x", labelrotation=90)

    # Panel 2: mean by weekday with min to max range.
    ax = fig.add_subplot(gs[1, 1])
    x = np.arange(len(weekday))
    bars = ax.bar(x, weekday["mean_daily_rentals"], color=BLUE, width=0.6,
                  edgecolor=SURFACE, linewidth=2)
    ax.vlines(x, weekday["min_rentals"], weekday["max_rentals"],
              color=INK2, lw=1.5)
    for xi, mean_value in zip(x, weekday["mean_daily_rentals"]):
        ax.text(xi + 0.32, mean_value, f"{mean_value:,.0f}", ha="left",
                va="center", fontsize=9, color=INK)
    for xi, n in zip(x, weekday["days"]):
        ax.text(xi, 150, f"n={int(n)}", ha="center", color="white",
                fontsize=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([d[:3] for d in weekday["day_name"]])
    ax.set_title("Mean by weekday (line: lowest to highest day)")
    ax.set_ylabel("Rentals per day")
    ax.set_ylim(0, weekday["max_rentals"].max() * 1.12)
    ax.grid(axis="x", visible=False)

    # Panel 3: week by weekday heatmap.
    ax = fig.add_subplot(gs[2, 0])
    sns.heatmap(matrix, ax=ax, cmap=SEQ, annot=len(matrix) <= 8, fmt=".0f",
                annot_kws={"fontsize": 9}, linewidths=2, linecolor=SURFACE,
                cbar_kws={"label": "Rentals", "shrink": 0.8})
    ax.set_xticklabels([d[:3] for d in matrix.columns], rotation=0)
    ax.set_yticklabels([f"Week {int(w)}" for w in matrix.index], rotation=0)
    ax.set_title("Each week by weekday (darker means busier)")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.grid(False)

    # Panel 4: change from the previous week.
    ax = fig.add_subplot(gs[2, 1])
    change = weekly.dropna(subset=["change_vs_prev_pct"])
    if change.empty:
        ax.axis("off")
    else:
        colours = [BLUE if v >= 0 else ORANGE
                   for v in change["change_vs_prev_pct"]]
        bars = ax.bar([f"Week {w}" for w in change["week_number"]],
                      change["change_vs_prev_pct"], color=colours, width=0.6,
                      edgecolor=SURFACE, linewidth=2)
        for bar, value in zip(bars, change["change_vs_prev_pct"]):
            ax.text(bar.get_x() + bar.get_width() / 2, value,
                    f"{value:+.0f}%", ha="center", fontsize=9, color=INK,
                    va="bottom" if value >= 0 else "top")
        ax.axhline(0, color=AXIS, lw=1)
        ax.set_title("Change in mean daily rentals vs previous week")
        ax.set_ylabel("Percent change")
        ax.margins(y=0.2)
        ax.grid(axis="x", visible=False)
        ax.legend(handles=[Patch(color=BLUE, label="Rise"),
                           Patch(color=ORANGE, label="Fall")],
                  frameon=False, fontsize=9, loc="upper right")

    _finish(fig, f"Question 3: How do weeks and weekdays compare in {label}?",
            "Weeks run Friday to Thursday. The last week may be partial.",
            save_path)
    return fig


# ---------------------------------------------------------------- Question 4
def dashboard_weather(data: pd.DataFrame, label: str, save_path=None):
    """Weather against daily rentals. `data` holds daily_rentals and weather."""

    _style()
    fig = plt.figure(figsize=(14, 13))
    gs = GridSpec(4, 3, height_ratios=[0.4, 1.5, 1.2, 1.9], hspace=0.5,
                  wspace=0.3, top=0.92, bottom=0.05)

    data = data.copy()
    data["weather_day"] = np.select(
        [data["snowfall"] > 0, data["rainfall"] > 0], ["Snow", "Rain"], "Dry"
    )
    corr = data["temperature"].corr(data["daily_rentals"])
    lowest = data.nsmallest(5, "daily_rentals")
    counts = data["weather_day"].value_counts()
    dry_mean = data.loc[data["weather_day"] == "Dry", "daily_rentals"].mean()
    wet_mean = data.loc[data["weather_day"] != "Dry", "daily_rentals"].mean()
    wet_note = ("no wet days" if np.isnan(wet_mean)
                else f"{wet_mean:,.0f} on wet days")
    _kpi_strip(
        fig.add_subplot(gs[0, :]),
        [
            ("Temperature vs rentals (r)", f"{corr:+.2f}", "daily correlation"),
            ("Mean temperature", f"{data['temperature'].mean():.1f}",
             "degrees Celsius"),
            ("Rain or snow days",
             f"{int(counts.get('Rain', 0) + counts.get('Snow', 0))}",
             f"of {len(data)} days"),
            ("Dry day rentals", f"{dry_mean:,.0f}", wet_note),
        ],
    )

    # Panel 1: rentals line with the five weakest days marked.
    ax1 = fig.add_subplot(gs[1, :])
    ax1.plot(data["date"], data["daily_rentals"], color=BLUE, lw=2)
    ax1.scatter(lowest["date"], lowest["daily_rentals"], s=60, color=ORANGE,
                edgecolor=SURFACE, linewidth=1.5, zorder=3,
                label="Five weakest days")
    ax1.legend(frameon=False, loc="lower left", fontsize=9)
    ax1.set_title("Daily rentals")
    ax1.set_ylabel("Rentals per day")
    ax1.set_ylim(bottom=0)
    plt.setp(ax1.get_xticklabels(), visible=False)

    # Panel 2: temperature on its own axis, same dates.
    ax2 = fig.add_subplot(gs[2, :], sharex=ax1)
    ax2.plot(data["date"], data["temperature"], color=INK2, lw=2)
    ax2.axhline(0, color=AXIS, lw=1)
    for d in lowest["date"]:
        ax2.axvline(d, color=ORANGE, lw=1, alpha=0.6)
    ax2.set_title("Mean daily temperature (orange lines mark the five weakest days)")
    ax2.set_ylabel("Degrees Celsius")
    _date_axis(ax2, data["date"])

    # Panel 3: temperature against rentals.
    ax = fig.add_subplot(gs[3, :2])
    ax.scatter(data["temperature"], data["daily_rentals"], s=55, color=BLUE,
               edgecolor=SURFACE, linewidth=1.5, zorder=3)
    slope, intercept = np.polyfit(data["temperature"], data["daily_rentals"], 1)
    xs = np.array([data["temperature"].min(), data["temperature"].max()])
    ax.plot(xs, slope * xs + intercept, color=INK2, lw=1.5, ls="--")
    ax.annotate(f"trend, r = {corr:+.2f}", (xs[1], slope * xs[1] + intercept),
                xytext=(-4, 10), textcoords="offset points", fontsize=9,
                color=INK, ha="right")
    ax.set_title("Warmer days against rentals")
    ax.set_xlabel("Mean daily temperature (degrees Celsius)")
    ax.set_ylabel("Rentals per day")
    ax.margins(x=0.15)

    # Panel 4: mean rentals by weather class.
    ax = fig.add_subplot(gs[3, 2])
    classes = ["Dry", "Rain", "Snow"]
    stats = (data.groupby("weather_day")["daily_rentals"]
             .agg(["mean", "count"]).reindex(classes).dropna())
    colour_map = {"Dry": BLUE, "Rain": ORANGE, "Snow": AQUA}
    bars = ax.bar(stats.index, stats["mean"],
                  color=[colour_map[c] for c in stats.index], width=0.55,
                  edgecolor=SURFACE, linewidth=2)
    _bar_labels(ax, bars)
    for bar, n in zip(bars, stats["count"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 0.5,
                f"{int(n)} day{'s' if n != 1 else ''}", ha="center",
                color="white", fontsize=9, fontweight="bold")
    ax.set_title("Mean rentals by weather")
    ax.set_ylabel("Rentals per day")
    ax.set_ylim(0, stats["mean"].max() * 1.15)
    ax.grid(axis="x", visible=False)

    _finish(fig, f"Question 4: Did weather explain the weak days in {label}?",
            "Temperature, rain and snow against daily rentals", save_path)
    return fig
