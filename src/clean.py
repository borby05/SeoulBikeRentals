import pandas as pd
from pathlib import Path

# =================
# CONSTANT VARIABLE
# =================
UNITS = {
    "temperature": "°C",            # the degree symbol was lost in the file.
    "humidity": "%",
    "wind_speed": "m/s",
    "visibility": "10m",            # one unit equals 10 m, as in the raw header
    "dew_point_temperature": "°C",  # same as temperature
    "solar_radiation": "MJ/m2",
    "rainfall": "mm",
    "snowfall": "cm",
}                                   # feeds axis labels in the reports and the dashboard
WEEK_INCREMENT = 1                  # increases the week index by 1 
DATE_FORMAT = "%d/%m/%Y"            # parsing the date column format
WEEK_ANCHOR = pd.Timestamp("2017-12-01")            # start of the week
DAYS_IN_WEEK = 7
WEEKEND_DAYS = [5, 6]               # Saturday and Sunday
WEEK_START_DAY = 4                  # Friday
CLOSED_LABEL = "No"                 # value in functioning_day that marks a closed hour
EXPECTED_ROWS = 8760                # no of rows in the raw file
HOURS_PER_DAY = 24
MIN_HOUR = 0
MAX_HOUR = 23
MIN_RENTALS = 0
MIN_HUMIDITY = 0
MAX_HUMIDITY = 100
CLEAN_FILE = "clean.csv"            # open hours, saved in data/clean/
CLOSED_FILE = "closed_hours.csv"    # closed hours, saved in data/clean/
assert WEEK_ANCHOR.weekday() == WEEK_START_DAY      # Start day of the week = 4 (Friday)


def load_raw(file_path: str | Path) -> pd.DataFrame:
    """Read the raw bike CSV into a DataFrame."""
    if not Path(file_path).is_file():
        raise FileNotFoundError(f"No file found: {Path(file_path).resolve()}")
    return pd.read_csv(file_path, encoding="utf-8")


def standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with lowercase, underscore-separated column names and no units."""
    df_copy = df.copy()
    df_copy.columns = (
        df_copy.columns
        .str.replace(r"\s*\([^)]*\)", "", regex=True)
        .str.lower()
        .str.strip()
        .str.replace(r"\s+", "_", regex=True)
    )
    return df_copy


def parse_date_column(df: pd.DataFrame, date_col: str = "date", fmt: str = DATE_FORMAT) -> pd.DataFrame:
    """Return a copy of df with the date column parsed to datetime using fmt."""
    df_copy = df.copy()
    df_copy[date_col] = pd.to_datetime(df_copy[date_col], format=fmt)
    return df_copy


def add_calendar_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Return a copy of df with year, month, weekday, day_name, is_weekend, week_position and week_number columns added."""
    df_copy = df.copy()
    df_copy["year"] = df_copy[date_col].dt.year
    df_copy["month"] = df_copy[date_col].dt.month
    df_copy["weekday"] = df_copy[date_col].dt.dayofweek
    df_copy["day_name"] = df_copy[date_col].dt.day_name()
    df_copy["is_weekend"] = df_copy["weekday"].isin(WEEKEND_DAYS)
    df_copy["week_position"] = (df_copy["weekday"] - WEEK_START_DAY) % DAYS_IN_WEEK

    days_since_anchor = (df_copy[date_col] - WEEK_ANCHOR).dt.days
    df_copy["week_number"] = days_since_anchor // DAYS_IN_WEEK + WEEK_INCREMENT
    return df_copy


def validate(df: pd.DataFrame) -> None:
    """Raise AssertionError if df breaks any rule in the validation table."""
    # Check 1: row count
    row_count = len(df)
    assert row_count == EXPECTED_ROWS, (
        f"Row count is {row_count}, expected {EXPECTED_ROWS}"
    )

    # Check 2: every date holds a full day of hours
    rows_per_date = df.groupby("date").size()
    bad_dates = rows_per_date[rows_per_date != HOURS_PER_DAY]
    assert bad_dates.empty, (
        f"{len(bad_dates)} dates do not hold {HOURS_PER_DAY} rows: {bad_dates.to_dict()}"
    )

    # Check 3: each date and hour pair appears once
    duplicate_pairs = df.duplicated(subset=["date", "hour"]).sum()
    assert duplicate_pairs == 0, (
        f"Found {duplicate_pairs} duplicated date and hour pairs"
    )

    # Check 4: hour runs from MIN_HOUR to MAX_HOUR with HOURS_PER_DAY distinct values
    min_hour = df["hour"].min()
    max_hour = df["hour"].max()
    unique_hours = df["hour"].nunique()
    assert min_hour == MIN_HOUR, (
        f"Smallest hour is {min_hour}, expected {MIN_HOUR}"
    )
    assert max_hour == MAX_HOUR, (
        f"Largest hour is {max_hour}, expected {MAX_HOUR}"
    )
    assert unique_hours == HOURS_PER_DAY, (
        f"Found {unique_hours} distinct hours, expected {HOURS_PER_DAY}"
    )

    # Check 5: rentals are never negative
    min_rentals = df["rented_bike_count"].min()
    assert min_rentals >= MIN_RENTALS, (
        f"Smallest rental count is {min_rentals}, expected at least {MIN_RENTALS}"
    )

    # Check 6: humidity stays between MIN_HUMIDITY and MAX_HUMIDITY
    min_humidity = df["humidity"].min()
    max_humidity = df["humidity"].max()
    assert min_humidity >= MIN_HUMIDITY, (
        f"Smallest humidity is {min_humidity}, expected at least {MIN_HUMIDITY}"
    )
    assert max_humidity <= MAX_HUMIDITY, (
        f"Largest humidity is {max_humidity}, expected at most {MAX_HUMIDITY}"
    )

    # Check 7: no missing values anywhere
    missing_values = df.isna().sum().sum()
    assert missing_values == 0, (
        f"Found {missing_values} missing values"
    )


def split_closed(df: pd.DataFrame, flag_col: str = "functioning_day") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return open-hour and closed-hour copies of df, split on flag_col."""
    is_closed = df[flag_col] == CLOSED_LABEL
    open_df = df[~is_closed]
    closed_df = df[is_closed]
    return open_df.copy(), closed_df.copy()


def save_clean(open_df: pd.DataFrame, closed_df: pd.DataFrame, out_dir: str | Path) -> None:
    """Write open_df and closed_df as CSV files inside out_dir."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    open_df.to_csv(out_path / CLEAN_FILE, index=False)
    closed_df.to_csv(out_path / CLOSED_FILE, index=False)


def load_clean(file_path: str | Path) -> pd.DataFrame:
    """Read a saved clean CSV and restore the date column as dates."""
    return pd.read_csv(file_path, parse_dates=["date"])