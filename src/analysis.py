import pandas as pd

# Weeks run Friday to Thursday in this project.
WEEK_ORDER = [
    "Friday", "Saturday", "Sunday", "Monday",
    "Tuesday", "Wednesday", "Thursday",
]
WEEKEND_NAMES = {"Saturday", "Sunday"}

# Verified against official sources: only 25 December 2017 is a public holiday.
HOLIDAYS = {pd.Timestamp("2017-12-25")}

# (label, first hour, last hour), both ends included.
TIME_BLOCKS = [
    ("Night (0-5)", 0, 5),
    ("Morning (6-9)", 6, 9),
    ("Midday (10-15)", 10, 15),
    ("Evening (16-20)", 16, 20),
    ("Late (21-23)", 21, 23),
]


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
