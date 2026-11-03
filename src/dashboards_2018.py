"""Dashboards for the 2018 analysis of the Seoul bike rental project.

One function per business question, as in dashboards.py. The 2017 dashboards
stay untouched because the 2017 report is signed off. This file reuses the
palette and the drawing helpers from dashboards.py. The helpers start with an
underscore. A shared chart_style module will replace these imports once the
2018 report ships.
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Patch

from src.analysis import SEASON_BY_MONTH, SEASON_ORDER
from src.clean import UNITS
from src.dashboards import (
    BLUE,
    ORANGE,
    AQUA,
    BLUE_LIGHT,
    SURFACE,
    INK,
    INK2,
    MUTED,
    DAY_TYPE_COLOURS,
    _style,
    _kpi_strip,
    _finish,
    _bar_labels,
)

TOP_N = 5                       # days shown in the best and weakest panel
DAY_TYPE_ORDER = ["Weekday", "Weekend", "Holiday"]
MONTH_LABEL_LENGTH = 3          # Jan, Feb, Mar


def _month_axis(ax) -> None:
    """One tick per month with the month name. January reads Jan, not the year."""

    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))


# ---------------------------------------------------------------- Question 1
def dashboard_volume(
    tiles: dict,
    daily: pd.DataFrame,
    full_calendar: pd.Series,
    rolling_avg: pd.Series,
    save_path=None,
):
    """Question 1: total volume, mean per day, extremes and day types for 2018.

    tiles is the dict from headline_figures. daily is the table from
    daily_table. full_calendar and rolling_avg are indexed by every calendar
    date, with closed dates empty, so the lines break at the closures.
    """

    _style()
    fig = plt.figure(figsize=(14, 11))
    gs = GridSpec(3, 2, height_ratios=[0.45, 2.1, 1.7], hspace=0.45,
                  wspace=0.28, top=0.92, bottom=0.06)

    # Headline tiles
    _kpi_strip(
        fig.add_subplot(gs[0, :]),
        [
            ("Total rentals", f"{tiles['total_rentals']:,}",
             f"{tiles['open_dates']} open dates"),
            ("Mean per day", f"{tiles['mean_per_day']:,.0f}", "rentals"),
            ("Busiest day", f"{tiles['busiest_rentals']:,}",
             f"{tiles['busiest_day_name'][:3]} {tiles['busiest_date']:%b %d}"),
            ("Quietest day", f"{tiles['quietest_rentals']:,}",
             f"{tiles['quietest_day_name'][:3]} {tiles['quietest_date']:%b %d}"),
        ],
    )

    # Panel 1: daily line, 7-day average and the mean. Gaps mark closed dates.
    closed_dates = int(full_calendar.isna().sum())
    ax = fig.add_subplot(gs[1, :])
    ax.plot(full_calendar.index, full_calendar.values, color=BLUE, lw=1.1,
            alpha=0.4, label="Daily rentals")
    ax.plot(rolling_avg.index, rolling_avg.values, color=ORANGE, lw=2.4,
            label="7-day average")
    last_date = rolling_avg.last_valid_index()
    ax.text(last_date, rolling_avg[last_date], "  7-day average",
            color=INK, fontsize=9, va="center")

    ax.axhline(tiles["mean_per_day"], color=MUTED, ls="--", lw=1.2)
    ax.text(full_calendar.index[0], tiles["mean_per_day"],
            f" Mean per day {tiles['mean_per_day']:,.0f}",
            color=INK2, fontsize=9, va="bottom")

    ax.set_ylim(0, tiles["busiest_rentals"] * 1.15)
    for key, dx, dy, align, vert in [
        ("busiest", -10, 0, "right", "center"),
        ("quietest", 10, 4, "left", "bottom"),
    ]:
        date = tiles[f"{key}_date"]
        value = tiles[f"{key}_rentals"]
        ax.scatter([date], [value], s=55, color=INK, edgecolor=SURFACE,
                   linewidth=1.5, zorder=5)
        ax.annotate(f"{key.capitalize()} {value:,}", (date, value),
                    xytext=(dx, dy), textcoords="offset points", fontsize=9,
                    color=INK, ha=align, va=vert)

    ax.legend(frameon=False, loc="upper left", fontsize=9)
    ax.set_title(f"Daily rentals (gaps mark the {closed_dates} closed dates)")
    ax.set_ylabel("Rentals per day")
    ax.margins(x=0.08)
    _month_axis(ax)

    # Panel 2: best and weakest days
    ax = fig.add_subplot(gs[2, 0])
    best = daily.nlargest(TOP_N, "daily_rentals")
    worst = daily.nsmallest(TOP_N, "daily_rentals")
    ranked = pd.concat([best.assign(group=f"Top {TOP_N}"),
                        worst.assign(group=f"Bottom {TOP_N}")])
    ranked = ranked.sort_values("daily_rentals")
    names = [f"{d:%b %d} ({n[:3]})" for d, n in
             zip(ranked["date"], ranked["day_name"])]
    colours = [BLUE if g.startswith("Top") else ORANGE for g in ranked["group"]]
    bars = ax.barh(names, ranked["daily_rentals"], color=colours,
                   height=0.65, edgecolor=SURFACE, linewidth=2)
    _bar_labels(ax, bars, horizontal=True)
    ax.set_xlim(0, ranked["daily_rentals"].max() * 1.15)
    ax.set_title("Five best and five weakest days")
    ax.set_xlabel("Rentals")
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[Patch(color=BLUE, label=f"Top {TOP_N}"),
                       Patch(color=ORANGE, label=f"Bottom {TOP_N}")],
              frameon=False, loc="lower right", fontsize=9)

    # Panel 3: mean rentals per day by day type
    ax = fig.add_subplot(gs[2, 1])
    stats = (daily.groupby("day_type")["daily_rentals"]
             .agg(["mean", "count"])
             .reindex(DAY_TYPE_ORDER).dropna())
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

    start = full_calendar.index.min()
    end = full_calendar.index.max()
    _finish(fig, "Question 1: How did daily rentals move in 2018?",
            f"Daily totals, extremes and day types, {start:%d %b} to {end:%d %b %Y}",
            save_path)
    return fig


# ---------------------------------------------------------------- Question 2
def dashboard_months(monthly: pd.DataFrame, highlights: dict, save_path=None):
    """Question 2: mean rentals per day by month, the monthly change and the weather.

    monthly is the table from monthly_summary. highlights is the dict from
    monthly_highlights. The lowest month and the biggest rise month are shaded
    in the weather panels so the reader can read the weather for each.
    """

    _style()
    fig = plt.figure(figsize=(14, 13))
    gs = GridSpec(4, 3, height_ratios=[0.45, 1.9, 1.5, 1.3], hspace=0.55,
                  wspace=0.28, top=0.92, bottom=0.05)

    labels = monthly["month_name"].str[:MONTH_LABEL_LENGTH].tolist()
    positions = range(len(monthly))
    rise_month = highlights["biggest_monthly_rise"]
    low_month = highlights["lowest_month"]

    # Headline tiles
    _kpi_strip(
        fig.add_subplot(gs[0, :]),
        [
            ("Highest month", f"{highlights['highest_mean']:,.0f}",
             f"{highlights['highest_month']}, rentals per day"),
            ("Lowest month", f"{highlights['lowest_mean']:,.0f}",
             f"{low_month}, rentals per day"),
            ("Biggest rise", f"{highlights['biggest_rise_pct']:+.0f}%",
             f"{rise_month}, against the month before"),
        ],
    )

    # Panel 1: mean rentals per day for each month
    ax = fig.add_subplot(gs[1, :])
    bars = ax.bar(positions, monthly["mean_daily_rentals"], color=BLUE,
                  width=0.62, edgecolor=SURFACE, linewidth=2)
    _bar_labels(ax, bars)
    month_ticks = [f"{label}\n{int(dates)} dates"
                   for label, dates in zip(labels, monthly["open_dates"])]
    ax.set_xticks(list(positions), month_ticks)
    ax.set_ylim(0, monthly["mean_daily_rentals"].max() * 1.15)
    ax.set_title("Mean rentals per day by month (open dates under each month)")
    ax.set_ylabel("Rentals per day")
    ax.grid(axis="x", visible=False)

    # Panel 2: change against the month before
    ax = fig.add_subplot(gs[2, :])
    change = monthly["change_vs_prev_pct"]
    colours = [BLUE if value >= 0 else ORANGE for value in change.fillna(0)]
    bars = ax.bar(positions, change.fillna(0), color=colours, width=0.62,
                  edgecolor=SURFACE, linewidth=2)
    for bar, value, name in zip(bars, change, monthly["month_name"]):
        if pd.isna(value):
            ax.text(bar.get_x() + bar.get_width() / 2, 2, "no month before",
                    ha="center", va="bottom", fontsize=8.5, color=INK2)
            continue
        offset = 3 if value >= 0 else -3
        ax.text(bar.get_x() + bar.get_width() / 2, value + offset,
                f"{value:+.1f}%" + ("\nbiggest rise" if name == rise_month else ""),
                ha="center", va="bottom" if value >= 0 else "top",
                fontsize=9, color=INK)
    ax.axhline(0, color=INK2, lw=1)
    ax.set_xticks(list(positions), labels)
    ax.set_ylim(change.min() * 2.0, change.max() * 1.3)
    ax.set_title("Change in mean rentals per day against the month before")
    ax.set_ylabel("Change (%)")
    ax.grid(axis="x", visible=False)

    # Panel 3: weather by month. Each measure has its own axis.
    weather = [
        ("mean_temperature", f"Mean temperature ({UNITS['temperature']})", "line"),
        ("mean_daily_rainfall", f"Mean daily rainfall ({UNITS['rainfall']})", "bar"),
        ("mean_daily_snowfall", f"Mean daily snowfall ({UNITS['snowfall']})", "bar"),
    ]
    shaded = {low_month: "Low", rise_month: "Rise"}
    for col, (column, title, kind) in enumerate(weather):
        ax = fig.add_subplot(gs[3, col])
        for name, role in shaded.items():
            index = monthly.index[monthly["month_name"] == name][0]
            ax.axvspan(index - 0.5, index + 0.5, color=MUTED, alpha=0.18, lw=0)
            if col == 0:
                ax.text(index, 1.02, role, transform=ax.get_xaxis_transform(),
                        ha="center", va="bottom", fontsize=8.5, color=INK2)
        if kind == "line":
            ax.plot(list(positions), monthly[column], color=AQUA, lw=2,
                    marker="o", ms=5, mfc=AQUA, mec=SURFACE, mew=1.2)
            ax.axhline(0, color=INK2, lw=0.8)
        else:
            ax.bar(list(positions), monthly[column], color=AQUA, width=0.6,
                   edgecolor=SURFACE, linewidth=1.5)
        ax.set_xticks(list(positions), [label[0] for label in labels])
        ax.set_title(title, fontsize=10.5, pad=16 if col == 0 else 6)
        ax.grid(axis="x", visible=False)

    _finish(fig, "Question 2: Which months rose most, and which were lowest?",
            "Mean rentals per day by month with the weather beside each month "
            "(shaded: Low is the lowest month, Rise is the biggest rise)", save_path)
    return fig


# ---------------------------------------------------------------- Question 3
def dashboard_seasons(
    seasons: pd.DataFrame,
    season_stats: dict,
    daily: pd.DataFrame,
    save_path=None,
):
    """Question 3: mean rentals per day by season, the gaps and the spread.

    seasons is the table from season_summary. season_stats is the dict from
    season_highlights. daily is the table from daily_table. The box plot reads
    the spread of every open date inside each season.
    """

    _style()
    fig = plt.figure(figsize=(14, 12))
    gs = GridSpec(3, 2, height_ratios=[0.45, 1.8, 2.1], hspace=0.5,
                  wspace=0.25, top=0.92, bottom=0.06)

    leader = season_stats["leading_season"]
    weakest = season_stats["weakest_season"]
    gaps = season_stats["season_gaps"]
    positions = list(range(len(seasons)))
    names = seasons["season"].tolist()

    # Headline tiles
    _kpi_strip(
        fig.add_subplot(gs[0, :]),
        [
            ("Leading season", f"{season_stats['leading_mean']:,.0f}",
             f"{leader}, rentals per day"),
            ("Weakest season", f"{season_stats['weakest_mean']:,.0f}",
             f"{weakest}, rentals per day"),
            ("Gap to the leader", f"{gaps[weakest]['gap_pct']:.0f}%",
             f"{weakest} below {leader}"),
        ],
    )

    # Panel 1: mean rentals per day by season, with the gap to the leader
    ax = fig.add_subplot(gs[1, 0])
    means = seasons["mean_daily_rentals"]
    bars = ax.bar(positions, means, color=BLUE, width=0.6,
                  edgecolor=SURFACE, linewidth=2)
    for bar, name, mean in zip(bars, names, means):
        note = "leader" if name == leader else f"-{gaps[name]['gap_pct']:.0f}% vs {leader}"
        ax.text(bar.get_x() + bar.get_width() / 2, mean,
                f"{mean:,.0f}\n{note}", ha="center", va="bottom",
                fontsize=9, color=INK)
    ax.set_xticks(positions, [f"{n}\n{int(d)} dates" for n, d in
                              zip(names, seasons["open_dates"])])
    ax.set_ylim(0, means.max() * 1.22)
    ax.set_title("Mean rentals per day by season")
    ax.set_ylabel("Rentals per day")
    ax.grid(axis="x", visible=False)

    # Panel 2: spread as a share of the mean
    ax = fig.add_subplot(gs[1, 1])
    spread = seasons["spread_pct"]
    colours = [ORANGE if value == spread.max() else AQUA for value in spread]
    bars = ax.bar(positions, spread, color=colours, width=0.6,
                  edgecolor=SURFACE, linewidth=2)
    _bar_labels(ax, bars, fmt="{:.0f}%")
    ax.set_xticks(positions, names)
    ax.set_ylim(0, spread.max() * 1.2)
    ax.set_title("Spread: standard deviation as % of the mean")
    ax.set_ylabel("Spread (%)")
    ax.grid(axis="x", visible=False)

    # Panel 3: every open date inside each season
    ax = fig.add_subplot(gs[2, :])
    table = daily.copy()
    table["season"] = table["date"].dt.month.map(SEASON_BY_MONTH)
    groups = [table.loc[table["season"] == n, "daily_rentals"] for n in SEASON_ORDER]
    ax.boxplot(groups, positions=positions, widths=0.45, patch_artist=True,
               boxprops={"facecolor": AQUA, "alpha": 0.35, "edgecolor": AQUA},
               medianprops={"color": INK, "linewidth": 1.8},
               whiskerprops={"color": MUTED}, capprops={"color": MUTED},
               flierprops={"marker": "o", "markersize": 4, "markerfacecolor": MUTED,
                           "markeredgecolor": SURFACE})
    ax.scatter(positions, seasons["mean_daily_rentals"], marker="D", s=60,
               color=ORANGE, edgecolor=SURFACE, linewidth=1.2, zorder=5,
               label="Mean")
    for pos, low, high in zip(positions, seasons["lowest_day"],
                              seasons["highest_day"]):
        ax.text(pos + 0.27, low, f"low {low:,.0f}", fontsize=8.5, color=INK2,
                va="center")
        ax.text(pos + 0.27, high, f"high {high:,.0f}", fontsize=8.5, color=INK2,
                va="center")
    ax.set_xticks(positions, names)
    ax.set_xlim(-0.6, len(seasons) - 0.3)
    ax.set_ylim(0, seasons["highest_day"].max() * 1.1)
    ax.set_title("Daily rentals inside each season (line is the median, box is the middle half of days)")
    ax.set_ylabel("Rentals per day")
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, loc="upper left", fontsize=9)

    _finish(fig, "Question 3: Which season leads, and how steady is each?",
            "Mean rentals per day by season, the gap to the leader and the spread "
            "of daily rentals, 2018 (winter holds January and February only)",
            save_path)
    return fig


# ---------------------------------------------------------------- Question 4
SEASON_COLOURS = {"Winter": BLUE_LIGHT, "Spring": AQUA, "Summer": ORANGE, "Autumn": INK2}
BLOCK_COLOURS = [MUTED, BLUE_LIGHT, BLUE, ORANGE, INK2]    # night to late
MORNING_PEAK_GROUPS = ["Weekday"]    # weekends and holidays have no morning peak


def _hour_axis(ax) -> None:
    """One tick every two hours, labelled 0 to 22."""

    ax.set_xticks(range(0, 24, 2))
    ax.set_xlim(-0.5, 23.5)
    ax.set_xlabel("Hour of day")


def dashboard_hours(
    season_profiles: pd.DataFrame,
    day_type_profiles: pd.DataFrame,
    peaks: pd.DataFrame,
    season_shares: pd.DataFrame,
    save_path=None,
):
    """Question 4: the shape of the day by season and by day type.

    season_profiles and day_type_profiles are hours down the side and groups
    across the top. peaks is the table from hour_peaks. season_shares holds the
    percent of rentals in each time block, one row per season.
    """

    _style()
    fig = plt.figure(figsize=(14, 12))
    gs = GridSpec(3, 2, height_ratios=[0.45, 2.0, 1.5], hspace=0.5,
                  wspace=0.22, top=0.92, bottom=0.06)

    # Headline tiles
    _kpi_strip(
        fig.add_subplot(gs[0, :]),
        [
            ("Weekday evening peak", f"{peaks.loc['Weekday', 'evening_mean']:,.0f}",
             f"{peaks.loc['Weekday', 'evening_hour']}:00, rentals per hour"),
            ("Weekend peak", f"{peaks.loc['Weekend', 'evening_mean']:,.0f}",
             f"{peaks.loc['Weekend', 'evening_hour']}:00, rentals per hour"),
            ("Holiday peak", f"{peaks.loc['Holiday', 'evening_mean']:,.0f}",
             f"{peaks.loc['Holiday', 'evening_hour']}:00, rentals per hour"),
        ],
    )

    # Panel 1: hourly profile for each season
    ax = fig.add_subplot(gs[1, 0])
    for season in season_profiles.columns:
        ax.plot(season_profiles.index, season_profiles[season], lw=2.2,
                color=SEASON_COLOURS[season], label=season)
    for hour in (8, 18):
        ax.axvline(hour, color=MUTED, ls="--", lw=1)
        ax.text(hour, 1.01, f"{hour}:00", transform=ax.get_xaxis_transform(),
                ha="center", va="bottom", fontsize=8.5, color=INK2)
    ax.set_title("Mean rentals per hour by season", pad=18)
    ax.set_ylabel("Rentals per hour")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    _hour_axis(ax)

    # Panel 2: hourly profile for each day type, with the peaks marked
    ax = fig.add_subplot(gs[1, 1])
    for day_type in day_type_profiles.columns:
        colour = DAY_TYPE_COLOURS[day_type]
        ax.plot(day_type_profiles.index, day_type_profiles[day_type], lw=2.2,
                color=colour, label=day_type)
        marks = [("evening_hour", "evening_mean")]
        if day_type in MORNING_PEAK_GROUPS:
            marks.append(("morning_hour", "morning_mean"))
        for hour_col, mean_col in marks:
            hour, value = peaks.loc[day_type, hour_col], peaks.loc[day_type, mean_col]
            ax.scatter([hour], [value], s=45, color=colour, edgecolor=SURFACE,
                       linewidth=1.3, zorder=5)
            if day_type in MORNING_PEAK_GROUPS:    # weekend and holiday values sit in the tiles
                ax.annotate(f"{hour}:00  {value:,.0f}", (hour, value),
                            xytext=(0, 8), textcoords="offset points",
                            ha="center", fontsize=8.5, color=INK)
    ax.set_title("Mean rentals per hour by day type", pad=18)
    ax.set_ylabel("Rentals per hour")
    ax.set_ylim(0, day_type_profiles.max().max() * 1.15)
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    _hour_axis(ax)

    # Panel 3: where each season's rentals fall in the day
    ax = fig.add_subplot(gs[2, :])
    blocks = list(season_shares.columns)
    seasons = list(season_shares.index)[::-1]
    left = [0.0] * len(seasons)
    for block, colour in zip(blocks, BLOCK_COLOURS):
        values = season_shares.loc[seasons, block].tolist()
        bars = ax.barh(seasons, values, left=left, color=colour, height=0.62,
                       edgecolor=SURFACE, linewidth=2, label=block)
        for bar, value, start in zip(bars, values, left):
            ax.text(start + value / 2, bar.get_y() + bar.get_height() / 2,
                    f"{value:.0f}%", ha="center", va="center", fontsize=9,
                    color="white", fontweight="bold")
        left = [a + b for a, b in zip(left, values)]
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of the season's rentals (%)")
    ax.set_title("Share of rentals by time block and season", pad=22)
    ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0),
              ncol=len(blocks), fontsize=9, handlelength=1.2)

    _finish(fig, "Question 4: What does a typical day look like?",
            "Hourly rentals by season and day type, and the share of rentals in "
            "each time block, 2018", save_path)
    return fig


# ---------------------------------------------------------------- Question 5
def dashboard_weekdays(
    weekday_table: pd.DataFrame,
    lowest_counts: pd.Series,
    weekly: pd.DataFrame,
    weekly_marks: pd.DataFrame,
    save_path=None,
):
    """Question 5: weekday means, how often each weekday is lowest, and the weeks.

    weekday_table is from weekday_comparison. lowest_counts is from
    lowest_day_by_week. weekly is from weekly_summary. weekly_marks is from
    weekly_highlights. Partial weeks show as hollow markers.
    """

    _style()
    fig = plt.figure(figsize=(14, 12))
    gs = GridSpec(3, 2, height_ratios=[0.45, 1.9, 1.7], hspace=0.55,
                  wspace=0.25, top=0.92, bottom=0.06)

    names = weekday_table["weekday"].tolist()
    positions = list(range(len(names)))
    means = weekday_table["mean_daily_rentals"]
    best = weekday_table.loc[means.idxmax()]
    lowest = weekday_table.loc[means.idxmin()]
    complete_weeks = int(lowest_counts.sum())
    lowest_hits = int(lowest_counts[lowest["weekday"]])

    # Headline tiles
    _kpi_strip(
        fig.add_subplot(gs[0, :]),
        [
            ("Best weekday", f"{best['mean_daily_rentals']:,.0f}",
             f"{best['weekday']}, rentals per day"),
            ("Weakest weekday", f"{lowest['mean_daily_rentals']:,.0f}",
             f"{lowest['weekday']}, {lowest['gap_to_best_pct']:.1f}% below {best['weekday']}"),
            (f"{lowest['weekday']} is the lowest day", f"{lowest_hits} of {complete_weeks}",
             "complete weeks"),
        ],
    )

    # Panel 1: mean rentals per day by weekday, with and without holidays
    ax = fig.add_subplot(gs[1, 0])
    colours = [ORANGE if name == lowest["weekday"] else BLUE for name in names]
    bars = ax.bar(positions, means, color=colours, width=0.76,
                  edgecolor=SURFACE, linewidth=2, label="All open dates")
    for bar, mean in zip(bars, means):    # labels sit inside the bars, clear of the markers
        ax.text(bar.get_x() + bar.get_width() / 2, mean * 0.45, f"{mean:,.0f}",
                ha="center", va="center", fontsize=8.5, color="white", fontweight="bold")
    ax.scatter(positions, weekday_table["mean_excluding_holidays"], marker="D",
               s=42, color=INK, edgecolor=SURFACE, linewidth=1.1, zorder=5,
               label="Without holidays")
    ax.set_xticks(positions, [f"{n[:3]}\n{int(d)} dates" for n, d in
                              zip(names, weekday_table["open_dates"])])
    ax.set_ylim(0, means.max() * 1.22)
    ax.set_title("Mean rentals per day by weekday")
    ax.set_ylabel("Rentals per day")
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, loc="upper right", fontsize=9, ncol=2)

    # Panel 2: how often each weekday is the lowest day of a complete week
    ax = fig.add_subplot(gs[1, 1])
    counts = lowest_counts.reindex(names)
    colours = [ORANGE if name == lowest["weekday"] else BLUE for name in names]
    bars = ax.bar(positions, counts, color=colours, width=0.62,
                  edgecolor=SURFACE, linewidth=2)
    _bar_labels(ax, bars)
    even_share = complete_weeks / len(names)
    ax.axhline(even_share, color=MUTED, ls="--", lw=1.2)
    ax.annotate(f"equal chance {even_share:.1f}", (-0.4, even_share),
                xytext=(0, 16), textcoords="offset points",
                ha="left", va="bottom", fontsize=8.5, color=INK2)
    ax.set_xticks(positions, [n[:3] for n in names])
    ax.set_ylim(0, counts.max() * 1.22)
    ax.set_title(f"Weeks in which each weekday is the lowest ({complete_weeks} complete weeks)")
    ax.set_ylabel("Weeks")
    ax.grid(axis="x", visible=False)

    # Panel 3: mean rentals per day for every week
    ax = fig.add_subplot(gs[2, :])
    ax.plot(weekly["start_date"], weekly["mean_daily_rentals"], color=BLUE,
            lw=1.6, alpha=0.55)
    full = weekly.loc[~weekly["is_partial"]]
    part = weekly.loc[weekly["is_partial"]]
    ax.scatter(full["start_date"], full["mean_daily_rentals"], s=34, color=BLUE,
               edgecolor=SURFACE, linewidth=1, zorder=4, label="Complete week")
    ax.scatter(part["start_date"], part["mean_daily_rentals"], s=40,
               facecolor=SURFACE, edgecolor=BLUE, linewidth=1.5, zorder=4,
               label="Partial week")
    for _, mark in weekly_marks.iterrows():
        ax.scatter([mark["start_date"]], [mark["mean_daily_rentals"]], s=70,
                   color=ORANGE, edgecolor=SURFACE, linewidth=1.3, zorder=5)
        above = mark["highlight"] == "Highest"
        ax.annotate(
            f"{mark['highlight']} week {int(mark['week_number'])}: "
            f"{mark['mean_daily_rentals']:,.0f}",
            (mark["start_date"], mark["mean_daily_rentals"]),
            xytext=(0, 10 if above else 55), textcoords="offset points",
            ha="center", va="bottom", fontsize=9, color=INK,
            arrowprops=None if above else {"arrowstyle": "-", "color": MUTED, "lw": 0.9})
    ax.set_ylim(0, weekly["mean_daily_rentals"].max() * 1.18)
    ax.set_title("Mean rentals per day by week (weeks run Friday to Thursday)")
    ax.set_ylabel("Rentals per day")
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    _month_axis(ax)

    _finish(fig, "Question 5: Does the Sunday weakness repeat?",
            "Mean rentals per day by weekday, how often each weekday is lowest, "
            "and the weekly path, 2018", save_path)
    return fig


# ---------------------------------------------------------------- Question 6
FACTOR_LABELS = {
    "temperature_r": "Temperature",
    "humidity_r": "Humidity",
    "rainfall_r": "Rainfall",
    "snowfall_r": "Snowfall",
}
STRONG_R = 0.5                  # |r| at or above this shows in white text on the heat map


def dashboard_weather(
    table: pd.DataFrame,
    correlations: pd.DataFrame,
    rain: pd.DataFrame,
    save_path=None,
):
    """Question 6: how weather moves daily rentals inside each season.

    table is from weather_daily_table. correlations is from season_correlations.
    rain is from rain_effect. A blank cell on the heat map means the factor
    never changed inside that season, so r does not exist.
    """

    _style()
    fig = plt.figure(figsize=(14, 12))
    gs = GridSpec(3, 2, height_ratios=[0.45, 2.2, 1.9], hspace=0.5,
                  wspace=0.25, top=0.92, bottom=0.06)

    by_name = correlations.set_index("season")
    gaps = rain.set_index("season")["gap_pct"]

    # Headline tiles
    _kpi_strip(
        fig.add_subplot(gs[0, :]),
        [
            ("Temperature r, all year", f"{by_name.loc['All year', 'temperature_r']:+.2f}",
             "seasons mixed together"),
            ("Temperature r, Summer", f"{by_name.loc['Summer', 'temperature_r']:+.2f}",
             "inside one season"),
            ("Rain day gap, Spring", f"{gaps['Spring']:.0f}%", "against dry days"),
            ("Rain day gap, Winter", f"{gaps['Winter']:.0f}%", "against dry days"),
        ],
    )

    # Panel 1: every open date, rentals against temperature
    ax = fig.add_subplot(gs[1, 0])
    for season in SEASON_ORDER:
        group = table[table["season"] == season]
        ax.scatter(group["temperature"], group["daily_rentals"], s=22, alpha=0.75,
                   color=SEASON_COLOURS[season], edgecolor=SURFACE, linewidth=0.5,
                   label=f"{season} (r {by_name.loc[season, 'temperature_r']:+.2f})")
    ax.set_xlabel(f"Mean temperature ({UNITS['temperature']})")
    ax.set_ylabel("Rentals per day")
    ax.set_title("Daily rentals against temperature, one dot per open date")
    ax.legend(frameon=False, fontsize=9, loc="upper left")

    # Panel 2: heat map of r, season by factor
    ax = fig.add_subplot(gs[1, 1])
    rows = SEASON_ORDER + ["All year"]
    columns = list(FACTOR_LABELS)
    values = by_name.loc[rows, columns].to_numpy(dtype=float)
    image = ax.imshow(values, cmap="RdBu", vmin=-1, vmax=1, aspect="auto")
    for i in range(len(rows)):
        for j in range(len(columns)):
            value = values[i, j]
            if pd.isna(value):
                text, colour = "constant", MUTED
            else:
                text = f"{value:+.2f}"
                colour = "white" if abs(value) >= STRONG_R else INK
            ax.text(j, i, text, ha="center", va="center", fontsize=11,
                    color=colour)
    ax.set_xticks(range(len(columns)), list(FACTOR_LABELS.values()))
    ax.set_yticks(range(len(rows)), [f"{r} ({int(by_name.loc[r, 'open_dates'])})"
                                     for r in rows])
    ax.grid(False)
    ax.set_title("Pearson r with daily rentals (open dates in brackets)")
    fig.colorbar(image, ax=ax, fraction=0.04, pad=0.02)

    # Panel 3: mean rentals on dry and rain days
    ax = fig.add_subplot(gs[2, :])
    positions = range(len(rain))
    width = 0.36
    dry = ax.bar([p - width / 2 for p in positions], rain["dry_mean"], width,
                 color=BLUE, edgecolor=SURFACE, linewidth=2, label="Dry days")
    wet = ax.bar([p + width / 2 for p in positions], rain["rain_mean"], width,
                 color=ORANGE, edgecolor=SURFACE, linewidth=2, label="Rain days")
    _bar_labels(ax, dry)
    _bar_labels(ax, wet)
    for p, (dates_dry, dates_wet, gap) in enumerate(
        zip(rain["dry_dates"], rain["rain_dates"], rain["gap_pct"])
    ):
        ax.text(p, -0.17, f"{dates_dry} dry, {dates_wet} rain dates\ngap {gap:.0f}%",
                ha="center", va="top", fontsize=9, color=INK2,
                transform=ax.get_xaxis_transform())
    ax.set_xticks(list(positions), rain["season"])
    ax.tick_params(axis="x", pad=2)
    ax.set_ylim(0, rain[["dry_mean", "rain_mean"]].to_numpy().max() * 1.15)
    ax.set_ylabel("Rentals per day")
    ax.set_title("Mean rentals per day, dry days against rain days")
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, loc="upper left", fontsize=9)

    _finish(fig, "Question 6: Does weather move demand inside each season?",
            "Correlation and rain effect by season, 2018. Association only, "
            "not cause", save_path)
    return fig


# ---------------------------------------------------------------- Question 7
GAP_BELOW = ORANGE
GAP_ABOVE = BLUE
PERIOD_ORDER = ["December 2017", "January 2018", "February 2018"]
PERIOD_COLOURS = {"December 2017": ORANGE, "January 2018": BLUE_LIGHT,
                  "February 2018": BLUE}


def dashboard_holidays(
    peers: pd.DataFrame,
    day_types: pd.DataFrame,
    closed: pd.DataFrame,
    winter: pd.DataFrame,
    daily_2017: pd.DataFrame,
    daily_2018: pd.DataFrame,
    gap: dict,
    save_path=None,
):
    """Question 7: holidays, closed dates and Winter 2018 against December 2017.

    peers is from holiday_vs_peers. day_types is from day_type_summary. closed
    is from closed_dates_table. winter is from winter_comparison. daily_2017 and
    daily_2018 are daily tables. gap is the dict from winter_gap.
    """

    _style()
    fig = plt.figure(figsize=(14, 13))
    gs = GridSpec(3, 2, height_ratios=[0.45, 2.2, 1.9], hspace=0.5,
                  wspace=0.28, top=0.92, bottom=0.06)

    below = int((peers["gap_pct"] < 0).sum())

    # Headline tiles
    _kpi_strip(
        fig.add_subplot(gs[0, :]),
        [
            ("Holidays below peers", f"{below} of {len(peers)}",
             "same month, same weekday type"),
            ("Mean holiday gap", f"{peers['gap_pct'].mean():.0f}%", "against peers"),
            ("Closed dates", f"{len(closed)}", f"{int(closed['is_holiday'].sum())} on a holiday"),
            ("Winter 2018 vs Dec 2017", f"{gap['gap_pct']:.0f}%",
             f"{gap['gap_rentals']:,.0f} rentals per day"),
        ],
    )

    # Panel 1: each holiday against its peers
    ax = fig.add_subplot(gs[1, 0])
    ordered = peers.sort_values("date", ascending=False).reset_index(drop=True)
    colours = [GAP_BELOW if value < 0 else GAP_ABOVE for value in ordered["gap_pct"]]
    bars = ax.barh(range(len(ordered)), ordered["gap_pct"], color=colours,
                   edgecolor=SURFACE, linewidth=1.5, height=0.75)
    for bar, value in zip(bars, ordered["gap_pct"]):
        ax.text(value + (1.2 if value >= 0 else -1.2), bar.get_y() + bar.get_height() / 2,
                f"{value:+.0f}%", va="center", ha="left" if value >= 0 else "right",
                fontsize=9, color=INK)
    ax.set_yticks(range(len(ordered)),
                  [f"{d:%d %b} {n[:3]}" for d, n in zip(ordered["date"], ordered["day_name"])])
    ax.axvline(0, color=INK2, linewidth=1)
    ax.set_xlim(-75, 40)
    ax.set_xlabel("Holiday rentals against the mean of ordinary dates (%)")
    ax.set_title("Each holiday against peers in its own month")
    ax.grid(axis="y", visible=False)

    # Panel 2: day types
    ax = fig.add_subplot(gs[1, 1])
    positions = range(len(day_types))
    bars = ax.bar(positions, day_types["mean_daily_rentals"],
                  color=[DAY_TYPE_COLOURS[n] for n in day_types["day_type"]],
                  width=0.6, edgecolor=SURFACE, linewidth=2)
    _bar_labels(ax, bars)
    ax.set_xticks(list(positions), [f"{n}\n{int(d)} dates" for n, d in
                                    zip(day_types["day_type"], day_types["open_dates"])])
    ax.set_ylim(0, day_types["mean_daily_rentals"].max() * 1.15)
    ax.set_ylabel("Rentals per day")
    ax.set_title("Mean rentals per day by day type (seasons mixed)")
    ax.grid(axis="x", visible=False)

    # Panel 3: closed dates by month
    ax = fig.add_subplot(gs[2, 0])
    months = list(range(1, 12))
    counts = closed.groupby("month").size().reindex(months, fill_value=0)
    bars = ax.bar(months, counts, color=BLUE, width=0.65, edgecolor=SURFACE, linewidth=2)
    for bar, value in zip(bars, counts):
        if value:
            ax.text(bar.get_x() + bar.get_width() / 2, value, f"{value}",
                    ha="center", va="bottom", fontsize=9, color=INK)
    ax.set_xticks(months, [pd.Timestamp(2018, m, 1).strftime("%b") for m in months])
    ax.set_ylim(0, max(counts.max() + 1, 1) * 1.2)
    ax.set_ylabel("Closed dates")
    ax.set_title(f"Closed dates by month ({len(closed)} in total)")
    ax.grid(axis="x", visible=False)

    # Panel 4: winter against December 2017, every open date
    ax = fig.add_subplot(gs[2, 1])
    series = {
        "December 2017": daily_2017["daily_rentals"],
        "January 2018": daily_2018.loc[daily_2018["date"].dt.month == 1, "daily_rentals"],
        "February 2018": daily_2018.loc[daily_2018["date"].dt.month == 2, "daily_rentals"],
    }
    means = winter.set_index("period")["mean_daily_rentals"]
    for i, name in enumerate(PERIOD_ORDER):
        values = series[name]
        offsets = (pd.Series(range(len(values))) % 7 - 3) * 0.045
        ax.scatter(i + offsets, values, s=22, alpha=0.8, color=PERIOD_COLOURS[name],
                   edgecolor=SURFACE, linewidth=0.5)
        ax.hlines(means[name], i - 0.3, i + 0.3, color=INK, linewidth=2)
        ax.text(i + 0.33, means[name], f"mean {means[name]:,.0f}", va="center",
                fontsize=9, color=INK)
    ax.set_xticks(range(len(PERIOD_ORDER)),
                  [f"{n}\n{len(series[n])} dates" for n in PERIOD_ORDER])
    ax.set_xlim(-0.5, len(PERIOD_ORDER) - 0.1)
    ax.set_ylabel("Rentals per day")
    ax.set_title("Winter 2018 against December 2017, every open date")
    ax.grid(axis="x", visible=False)

    _finish(fig, "Question 7: Holidays, closed dates and the winter comparison",
            "Holiday effect against same-month peers, closed dates, and Winter 2018 "
            "(January and February) against December 2017", save_path)
    return fig
