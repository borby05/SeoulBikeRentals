import json
import sys
from pathlib import Path

import pandas as pd

# The app folder sits next to src. One path line lets every page import your functions.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import analysis
import clean

CLEAN_FILE = ROOT / "data" / "clean" / "clean.csv"
METRICS_FILE = ROOT / "models" / "metrics.json"
MODEL_FILE = ROOT / "models" / "gradient_boosting.joblib"


def load_all():
    """Load the clean file and add a label such as 'Jun 2018'."""
    df = clean.load_clean(CLEAN_FILE)
    df["month_label"] = df["date"].dt.strftime("%b %Y")
    return df


def load_metrics():
    """Read the model scores saved by notebook 06."""
    with open(METRICS_FILE) as f:
        return json.load(f)


def month_labels(df):
    """Month labels in calendar order: Dec 2017, then Jan 2018 to Nov 2018."""
    return df.sort_values("date")["month_label"].unique().tolist()


def pick(df, year=None, months=None):
    """Keep one year and the chosen months. None means no filter."""
    out = df
    if year is not None:
        out = out[out["year"] == year]
    if months:
        out = out[out["month_label"].isin(months)]
    return out


def build_tables(df):
    """Daily table and daily weather for any slice of the data."""
    return analysis.daily_table(df), analysis.daily_weather(df)


def monthly_table(df):
    """Monthly summary, one year at a time, so December 2017 never meets November 2018."""
    parts = []
    for year in sorted(df["year"].unique()):
        daily, weather = build_tables(df[df["year"] == year])
        monthly = analysis.monthly_summary(daily, weather)
        monthly["year"] = year
        parts.append(monthly)
    out = pd.concat(parts, ignore_index=True)
    out["month_label"] = out["month_name"].str[:3] + " " + out["year"].astype(str)
    return out


def month_series(daily):
    """Daily rentals of one month on every calendar date. Closed dates stay empty."""
    series = daily.set_index("date")["daily_rentals"]
    start = series.index.min().replace(day=1)
    end = start + pd.offsets.MonthEnd(0)
    return analysis.to_full_calendar(series, start, end)


def long_series(daily):
    """Daily rentals on every calendar date plus the 7-day average. Closed dates stay empty."""
    series = daily.set_index("date")["daily_rentals"]
    full = analysis.to_full_calendar(series, series.index.min(), series.index.max())
    return full, analysis.rolling_average(full)


def load_model():
    """Load the trained gradient boosting model saved by notebook 06."""
    import joblib
    return joblib.load(MODEL_FILE)


def closed_and_partial(daily, view):
    """Count closed dates (gaps in the calendar) and partial dates in the chosen slice."""
    series = daily.set_index("date")["daily_rentals"]
    full = analysis.to_full_calendar(series, series.index.min(), series.index.max())
    return int(full.isna().sum()), len(analysis.partial_dates(view))
