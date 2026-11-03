import pandas as pd

# Weeks run Friday to Thursday in this project.
WEEK_ORDER = [
    "Friday", "Saturday", "Sunday", "Monday",
    "Tuesday", "Wednesday", "Thursday",
]
WEEKEND_NAMES = {"Saturday", "Sunday"}
ROLLING_WINDOW_DAYS = 7
ROLLING_MIN_DAYS = 4

# Verified public holidays: 25 December 2017 and the 2018 dates (January to November).
# Source: holidays-calendar.net. The raw holiday flag in the dataset is not used.
HOLIDAYS = {
    pd.Timestamp(day)
    for day in [
        "2017-12-25",
        "2018-01-01",
        "2018-02-15", "2018-02-16", "2018-02-17",    # Seollal
        "2018-03-01",
        "2018-05-05", "2018-05-07",                  # Children's Day and its substitute
        "2018-05-22",
        "2018-06-06",
        "2018-06-13",                                # local election day
        "2018-08-15",
        "2018-09-23", "2018-09-24", "2018-09-25",    # Chuseok
        "2018-09-26",                                # Chuseok substitute
        "2018-10-03",
        "2018-10-09",
    ]
}

# (label, first hour, last hour), both ends included.
TIME_BLOCKS = [
    ("Night (0-5)", 0, 5),
    ("Morning (6-9)", 6, 9),
    ("Midday (10-15)", 10, 15),
    ("Evening (16-20)", 16, 20),
    ("Late (21-23)", 21, 23),
]

# Season mapping across all 11 months
SEASON_BY_MONTH = {
    1: "Winter",
    2: "Winter",
    3: "Spring",
    4: "Spring",
    5: "Spring",
    6: "Summer",
    7: "Summer",
    8: "Summer",
    9: "Autumn",
    10: "Autumn",
    11: "Autumn"
}

SEASON_ORDER = ["Winter", "Spring", "Summer", "Autumn"]

ALL_YEAR_LABEL = "All year"
WEATHER_FACTORS = ["temperature", "humidity", "rainfall", "snowfall"]
PERCENT = 100

WINTER_NAME = "Winter"


def daily_totals(df: pd.DataFrame) -> pd.Series:
    """Return the total rentals for each date."""

    return df.groupby("date")["rented_bike_count"].sum()


def hour_profile(df: pd.DataFrame) -> pd.Series:
    """Return the mean rentals for each hour of the day."""

    return df.groupby("hour")["rented_bike_count"].mean()


def add_day_type(table: pd.DataFrame) -> pd.DataFrame:
    """Label each row as Weekday, Weekend or Holiday. Needs date and day_name."""

    out = table.copy()
    out["day_type"] = "Weekday"
    out.loc[out["day_name"].isin(WEEKEND_NAMES), "day_type"] = "Weekend"
    out.loc[out["date"].isin(HOLIDAYS), "day_type"] = "Holiday"
    return out


def daily_table(df: pd.DataFrame) -> pd.DataFrame:
    """One row per date with day name, week number, day type and total rentals."""

    daily = (
        df.groupby(["date", "day_name", "week_number"], as_index=False)
        ["rented_bike_count"]
        .sum()
        .rename(columns={"rented_bike_count": "daily_rentals"})
        .sort_values("date")
        .reset_index(drop=True)
    )
    return add_day_type(daily)


def weekly_summary(daily: pd.DataFrame) -> pd.DataFrame:
    """One row per week. Mean daily rentals keeps partial weeks comparable."""

    weekly = (
        daily.groupby("week_number")
        .agg(
            start_date=("date", "min"),
            end_date=("date", "max"),
            days=("date", "nunique"),
            total_rentals=("daily_rentals", "sum"),
            mean_daily_rentals=("daily_rentals", "mean"),
        )
        .reset_index()
        .sort_values("week_number")
        .reset_index(drop=True)
    )
    weekly["is_partial"] = weekly["days"] < 7
    weekly["change_vs_prev_pct"] = weekly["mean_daily_rentals"].pct_change() * 100
    return weekly


def weekday_summary(daily: pd.DataFrame) -> pd.DataFrame:
    """One row per weekday in Friday to Thursday order."""

    summary = (
        daily.groupby("day_name")
        .agg(
            days=("date", "nunique"),
            mean_daily_rentals=("daily_rentals", "mean"),
            min_rentals=("daily_rentals", "min"),
            max_rentals=("daily_rentals", "max"),
        )
        .reindex(WEEK_ORDER)
        .dropna(how="all")
        .reset_index()
    )
    return summary


def week_weekday_matrix(daily: pd.DataFrame) -> pd.DataFrame:
    """Weeks down the side, weekdays across the top, daily rentals inside."""

    matrix = daily.pivot_table(
        index="week_number",
        columns="day_name",
        values="daily_rentals",
        aggfunc="sum",
    )
    return matrix.reindex(columns=[d for d in WEEK_ORDER if d in matrix.columns])


def hour_profile_by_day_type(df: pd.DataFrame) -> pd.DataFrame:
    """Mean rentals per hour, one column for each day type."""

    dates = add_day_type(df[["date", "day_name"]].drop_duplicates())
    merged = df.merge(dates[["date", "day_type"]], on="date")
    return (
        merged.groupby(["day_type", "hour"])["rented_bike_count"]
        .mean()
        .unstack("day_type")
    )


def date_hour_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Dates down the side, hours across the top, rentals inside."""

    return df.pivot_table(
        index="date", columns="hour", values="rented_bike_count", aggfunc="sum"
    )


def time_block_share(df: pd.DataFrame) -> pd.Series:
    """Percent of all rentals that fall in each time block."""

    totals = pd.Series(
        {
            name: df.loc[df["hour"].between(low, high), "rented_bike_count"].sum()
            for name, low, high in TIME_BLOCKS
        }
    )
    return totals / totals.sum() * 100


def peak_hours(profile: pd.Series) -> dict:
    """Morning peak (6 to 11), evening peak (16 to 21) and the quietest hour."""

    morning = profile.loc[6:11]
    evening = profile.loc[16:21]
    return {
        "morning_hour": int(morning.idxmax()),
        "morning_mean": float(morning.max()),
        "evening_hour": int(evening.idxmax()),
        "evening_mean": float(evening.max()),
        "overall_hour": int(profile.idxmax()),
        "trough_hour": int(profile.idxmin()),
        "trough_mean": float(profile.min()),
    }


def find_column(df: pd.DataFrame, include: str, exclude: tuple = ()):
    """Return the first column whose lower-case name holds `include`.

    The cleaned file may name weather columns in different ways, so this
    finds them by keyword instead of by exact name.
    """

    for col in df.columns:
        name = str(col).lower()
        if include in name and not any(word in name for word in exclude):
            return col
    return None


def daily_weather(df: pd.DataFrame) -> pd.DataFrame:
    """Daily temperature, humidity, rainfall and snowfall. Empty if none found."""

    spec = {
        "temperature": ("temp", ("dew",), "mean"),
        "humidity": ("humid", (), "mean"),
        "rainfall": ("rain", (), "sum"),
        "snowfall": ("snow", (), "sum"),
    }
    agg = {}
    for label, (keyword, excluded, how) in spec.items():
        col = find_column(df, keyword, excluded)
        if col is not None:
            agg[label] = (col, how)
    if not agg:
        return pd.DataFrame()
    return df.groupby("date").agg(**agg).reset_index()


def headline_figures(daily: pd.DataFrame) -> dict:
    """Return total, mean per open date, busiest and quietest dates. Use before any reindex."""

    total_rentals = int(daily["daily_rentals"].sum())
    open_dates = len(daily)

    # idxmax and idxmin return row labels. daily_table resets the index,
    # so the labels match .loc.
    busiest = daily["daily_rentals"].idxmax()
    quietest = daily["daily_rentals"].idxmin()
    return {
        "total_rentals": total_rentals,
        "open_dates": open_dates,
        "mean_per_day": float(total_rentals / open_dates),
        "busiest_date": daily.loc[busiest, "date"],
        "busiest_day_name": str(daily.loc[busiest, "day_name"]),
        "busiest_rentals": int(daily.loc[busiest, "daily_rentals"]),
        "quietest_date": daily.loc[quietest, "date"],
        "quietest_day_name": str(daily.loc[quietest, "day_name"]),
        "quietest_rentals": int(daily.loc[quietest, "daily_rentals"]),
    }


def to_full_calendar(daily_rentals: pd.Series, start, end) -> pd.Series:
    """Reindex daily rentals (indexed by date) onto every calendar date from start to end.

    Closed dates stay empty (NaN). They are never filled with zero.
    """

    calendar = pd.date_range(start=start, end=end, freq="D")
    return daily_rentals.reindex(calendar)


def rolling_average(daily_rentals: pd.Series) -> pd.Series:
    """Centred rolling mean over calendar days, empty on every closed date.

    Needs ROLLING_MIN_DAYS days with data inside the window. The result is
    masked so the line breaks at closures instead of crossing them.
    """

    average = daily_rentals.rolling(
        f"{ROLLING_WINDOW_DAYS}D",
        center=True,
        min_periods=ROLLING_MIN_DAYS,
    ).mean()
    return average.where(daily_rentals.notna())


def monthly_summary(daily: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    """Summarise monthly rentals and weather across open dates."""
    daily_data = daily.copy()
    weather_data = weather.copy()

    daily_data["month"] = daily_data["date"].dt.month

    monthly = (
        daily_data.groupby("month")
        .agg(
            open_dates=("date", "nunique"),
            total_rentals=("daily_rentals", "sum"),
            mean_daily_rentals=("daily_rentals", "mean")
        )
        .reset_index()
    )

    month_name = (
        daily_data["date"]
        .dt.month_name()
        .groupby(daily_data["date"].dt.month)
        .first()
    )
    monthly["month_name"] = monthly["month"].map(month_name)

    monthly["change_vs_prev_pct"] = (
        monthly["mean_daily_rentals"]
        .pct_change(periods=1)
        .mul(100)
    )

    weather_data["month"] = weather_data["date"].dt.month

    monthly_weather = (
        weather_data.groupby("month")
        .agg(
            mean_temperature=("temperature", "mean"),
            mean_daily_rainfall=("rainfall", "mean"),
            mean_daily_snowfall=("snowfall", "mean")
        )
        .reset_index()
    )

    monthly = monthly.merge(
        monthly_weather,
        on="month",
        how="left"
    )

    return monthly[
        [
            "month",
            "month_name",
            "open_dates",
            "total_rentals",
            "mean_daily_rentals",
            "change_vs_prev_pct",
            "mean_temperature",
            "mean_daily_rainfall",
            "mean_daily_snowfall"
        ]
    ]


def monthly_highlights(monthly: pd.DataFrame) -> dict:
    """Return the largest monthly rise and the lowest and highest rentals means."""
    valid_changes = monthly.dropna(
        subset=["change_vs_prev_pct"]
        )
    biggest_rise = valid_changes.loc[
        valid_changes["change_vs_prev_pct"].idxmax()
    ]

    lowest = monthly.loc[monthly["mean_daily_rentals"].idxmin()]
    highest = monthly.loc[monthly["mean_daily_rentals"].idxmax()]

    return {
        "biggest_monthly_rise": biggest_rise["month_name"],
        "biggest_rise_pct": float(biggest_rise["change_vs_prev_pct"]),
        "lowest_month": lowest["month_name"],
        "lowest_mean": float(lowest["mean_daily_rentals"]),
        "highest_month": highest["month_name"],
        "highest_mean": float(highest["mean_daily_rentals"])
    }


def season_summary(daily: pd.DataFrame) -> pd.DataFrame:
    """Return the seasonal summary of each season in the dataframe."""
    daily = daily.copy()
    daily["season"] = daily["date"].dt.month.map(SEASON_BY_MONTH)

    summary = (
        daily.groupby("season")["daily_rentals"]
        .agg(
            open_dates="count",
            total_rentals="sum",
            mean_daily_rentals="mean",
            median_daily_rentals="median",
            lowest_day="min",
            highest_day="max",
            std_daily_rentals="std",
        )
        .reindex(SEASON_ORDER)
        .rename_axis("season")
        .reset_index()
    )

    summary["spread_pct"] = (
        summary["std_daily_rentals"]
        / summary["mean_daily_rentals"]
        * 100
    )

    return summary


def season_highlights(seasons: pd.DataFrame) -> dict:
    """Return the seasonal highlights across all seasons."""
    leader = seasons.loc[seasons["mean_daily_rentals"].idxmax()]
    weakest = seasons.loc[seasons["mean_daily_rentals"].idxmin()]

    season_gaps = {}

    for _, season in seasons.iterrows():
        if season["season"] != leader["season"]:
            gap = float(leader["mean_daily_rentals"] - season["mean_daily_rentals"])

            season_gaps[season["season"]] = {
                "gap_rentals": gap,
                "gap_pct": float(gap / leader["mean_daily_rentals"] * 100)
            }

    return {
        "leading_season": leader["season"],
        "leading_mean": float(leader["mean_daily_rentals"]),
        "weakest_season": weakest["season"],
        "weakest_mean": float(weakest["mean_daily_rentals"]),
        "season_gaps": season_gaps,
    }


def hour_profile_by_season(df: pd.DataFrame) -> pd.DataFrame:
    """Return the seasonal hourly profile of the dataset."""

    df = df.copy()
    df["season"] = df["month"].map(SEASON_BY_MONTH)

    return (
        df.groupby(["season", "hour"])["rented_bike_count"]
        .mean()
        .unstack("season")
        .reindex(index=range(24), columns=SEASON_ORDER)
    )


def hour_peaks(profiles: pd.DataFrame) -> pd.DataFrame:
    """Return the peak and quietest hour across the morning and evening."""

    rows = []

    for group in profiles.columns:
        peaks = peak_hours(profiles[group])

        rows.append({
            "group": group,
            "morning_hour": peaks["morning_hour"],
            "morning_mean": peaks["morning_mean"],
            "evening_hour": peaks["evening_hour"],
            "evening_mean": peaks["evening_mean"],
            "quietest_hour": profiles[group].idxmin(),
        })

    return pd.DataFrame(rows).set_index("group")


def weekday_comparison(daily: pd.DataFrame) -> pd.DataFrame:
    """Compare mean daily rentals by weekday, including and excluding holidays."""

    all_dates = weekday_summary(daily).copy()

    non_holidays = daily.loc[~daily["date"].isin(HOLIDAYS)]

    holiday_adjusted = (
        non_holidays.groupby("day_name")["daily_rentals"]
        .mean()
        .reindex(WEEK_ORDER)
    )

    all_dates["mean_excluding_holidays"] = (
        all_dates["day_name"].map(holiday_adjusted)
    )

    best_mean = all_dates["mean_daily_rentals"].max()

    all_dates["gap_to_best_pct"] = (
        (best_mean - all_dates["mean_daily_rentals"])
        / best_mean
        * 100
    )

    return all_dates[
        [
            "day_name",
            "days",
            "mean_daily_rentals",
            "mean_excluding_holidays",
            "gap_to_best_pct",
        ]
    ].rename(
        columns={
            "day_name": "weekday",
            "days": "open_dates",
        }
    ).reset_index(drop=True)


def lowest_day_by_week(daily: pd.DataFrame) -> pd.Series:
    """Count the lowest weekday in each complete week."""

    matrix = week_weekday_matrix(daily)
    complete_weeks = weekly_summary(daily).query(
        "days == 7"
    )["week_number"]

    complete_matrix = matrix.loc[
        matrix.index.isin(complete_weeks), WEEK_ORDER
    ]

    lowest_days = complete_matrix.idxmin(axis=1)

    return (
        lowest_days.value_counts()
        .reindex(WEEK_ORDER, fill_value=0)
        .rename("lowest_week_count")
    )


def weekly_highlights(weekly: pd.DataFrame) -> pd.DataFrame:
    """Return the highest and weakest complete weeks."""

    complete = weekly.loc[~weekly["is_partial"]].copy()

    highest = complete.loc[
        complete["mean_daily_rentals"].idxmax()
    ].copy()

    weakest = complete.loc[
        complete["mean_daily_rentals"].idxmin()
    ].copy()

    highlights = pd.DataFrame(
        [
            {
                "highlight": "Highest",
                "week_number": int(highest["week_number"]),
                "start_date": highest["start_date"],
                "end_date": highest["end_date"],
                "mean_daily_rentals": highest["mean_daily_rentals"],
            },
            {
                "highlight": "Weakest",
                "week_number": int(weakest["week_number"]),
                "start_date": weakest["start_date"],
                "end_date": weakest["end_date"],
                "mean_daily_rentals": weakest["mean_daily_rentals"],
            },
        ]
    )

    return highlights


def weather_daily_table(daily: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    """Return one row per open date with rentals, weather, season and a rain flag."""

    table = daily.merge(weather, on="date", how="inner", validate="one_to_one")
    table["season"] = table["date"].dt.month.map(SEASON_BY_MONTH)
    table["is_rain_day"] = table["rainfall"] > 0
    return table


def _correlation(rentals: pd.Series, factor: pd.Series) -> float:
    """Return Pearson r, or NaN when the factor never changes."""

    if factor.nunique() < 2:
        return float("nan")
    return float(rentals.corr(factor))


def season_correlations(table: pd.DataFrame) -> pd.DataFrame:
    """Return Pearson r between daily rentals and each weather factor, by season and all year."""

    groups = [(season, table[table["season"] == season]) for season in SEASON_ORDER]
    groups.append((ALL_YEAR_LABEL, table))

    rows = []
    for name, group in groups:
        row = {"season": name, "open_dates": len(group)}
        for factor in WEATHER_FACTORS:
            row[f"{factor}_r"] = _correlation(group["daily_rentals"], group[factor])
        rows.append(row)
    return pd.DataFrame(rows)


def season_weather_means(table: pd.DataFrame) -> pd.DataFrame:
    """Return the mean of each weather factor and the mean rentals per season."""

    return (
        table.groupby("season")[["daily_rentals"] + WEATHER_FACTORS]
        .mean()
        .reindex(SEASON_ORDER)
        .reset_index()
    )


def rain_effect(table: pd.DataFrame) -> pd.DataFrame:
    """Return mean rentals on dry and rain days for each season, with the gap."""

    rows = []
    for season in SEASON_ORDER:
        group = table[table["season"] == season]
        dry = group.loc[~group["is_rain_day"], "daily_rentals"]
        wet = group.loc[group["is_rain_day"], "daily_rentals"]
        rows.append({
            "season": season,
            "dry_dates": len(dry),
            "rain_dates": len(wet),
            "dry_mean": dry.mean(),
            "rain_mean": wet.mean(),
        })
    effect = pd.DataFrame(rows)
    effect["gap_rentals"] = effect["rain_mean"] - effect["dry_mean"]
    effect["gap_pct"] = effect["gap_rentals"] / effect["dry_mean"] * PERCENT
    return effect


def holiday_vs_peers(daily: pd.DataFrame) -> pd.DataFrame:
    """Compare each holiday with ordinary dates of the same month and the same weekday type."""

    table = daily.copy()
    table["is_weekend"] = table["day_name"].isin(WEEKEND_NAMES)
    table["month"] = table["date"].dt.month
    ordinary = table[table["day_type"] != "Holiday"]

    rows = []
    for _, holiday in table[table["day_type"] == "Holiday"].iterrows():
        peers = ordinary[
            (ordinary["month"] == holiday["month"])
            & (ordinary["is_weekend"] == holiday["is_weekend"])
        ]["daily_rentals"]
        peer_mean = peers.mean()
        rows.append({
            "date": holiday["date"],
            "day_name": holiday["day_name"],
            "holiday_rentals": holiday["daily_rentals"],
            "peer_dates": len(peers),
            "peer_mean": peer_mean,
            "gap_pct": (holiday["daily_rentals"] - peer_mean) / peer_mean * PERCENT,
        })
    return pd.DataFrame(rows)


def day_type_summary(daily: pd.DataFrame) -> pd.DataFrame:
    """Return open dates, mean and median rentals per day type."""

    return (
        daily.groupby("day_type")["daily_rentals"]
        .agg(open_dates="count", mean_daily_rentals="mean", median_daily_rentals="median")
        .reindex(["Weekday", "Weekend", "Holiday"])
        .reset_index()
    )


def closed_dates_table(full_calendar: pd.Series) -> pd.DataFrame:
    """List each calendar date with no rentals, with its weekday, month and holiday flag."""

    closed = full_calendar.index[full_calendar.isna()]
    table = pd.DataFrame({"date": closed})
    table["day_name"] = table["date"].dt.day_name()
    table["month"] = table["date"].dt.month
    table["is_holiday"] = table["date"].isin(HOLIDAYS)
    return table


def partial_dates(df: pd.DataFrame, hours_per_day: int = 24) -> pd.DataFrame:
    """Return open dates with fewer than a full day of open hours."""

    hours = df.groupby("date").size().rename("open_hours").reset_index()
    return hours[hours["open_hours"] < hours_per_day].reset_index(drop=True)


def winter_comparison(
    daily_2017: pd.DataFrame,
    weather_2017: pd.DataFrame,
    daily_2018: pd.DataFrame,
    weather_2018: pd.DataFrame,
) -> pd.DataFrame:
    """Compare December 2017, January 2018, February 2018 and Winter 2018 on a per-day basis."""

    first = weather_daily_table(daily_2017, weather_2017)
    second = weather_daily_table(daily_2018, weather_2018)
    second = second[second["season"] == WINTER_NAME]

    periods = {
        "December 2017": first,
        "January 2018": second[second["date"].dt.month == 1],
        "February 2018": second[second["date"].dt.month == 2],
        "Winter 2018": second,
    }

    rows = []
    for name, group in periods.items():
        rentals = group["daily_rentals"]
        rows.append({
            "period": name,
            "open_dates": len(group),
            "mean_daily_rentals": rentals.mean(),
            "median_daily_rentals": rentals.median(),
            "lowest_day": rentals.min(),
            "highest_day": rentals.max(),
            "std_daily_rentals": rentals.std(),
            "mean_temperature": group["temperature"].mean(),
            "mean_daily_rainfall": group["rainfall"].mean(),
            "mean_daily_snowfall": group["snowfall"].mean(),
            "holiday_dates": int((group["day_type"] == "Holiday").sum()),
        })
    return pd.DataFrame(rows)


def sunday_gap(daily: pd.DataFrame) -> dict:
    """Return Sunday mean, period mean, Sunday dates and the Sunday gap in percent."""

    sundays = daily.loc[daily["day_name"] == "Sunday", "daily_rentals"]
    period_mean = daily["daily_rentals"].mean()
    return {
        "sunday_dates": len(sundays),
        "sunday_mean": sundays.mean(),
        "period_mean": period_mean,
        "gap_pct": (sundays.mean() - period_mean) / period_mean * PERCENT,
    }


def winter_gap(comparison: pd.DataFrame) -> dict:
    """Return the gap of Winter 2018 below December 2017 with its standard error and t value."""

    first = comparison.set_index("period").loc["December 2017"]
    second = comparison.set_index("period").loc["Winter 2018"]
    gap = second["mean_daily_rentals"] - first["mean_daily_rentals"]
    standard_error = (
        first["std_daily_rentals"] ** 2 / first["open_dates"]
        + second["std_daily_rentals"] ** 2 / second["open_dates"]
    ) ** 0.5
    return {
        "gap_rentals": gap,
        "gap_pct": gap / first["mean_daily_rentals"] * PERCENT,
        "standard_error": standard_error,
        "t_value": gap / standard_error,
    }