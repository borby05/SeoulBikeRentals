from pathlib import Path

import pandas as pd

from src.clean import CLEAN_FILE, load_clean

CLEAN_DIR = Path("../data/clean")

# --------------------------------------------------------------------------------

def load_operating_rows(clean_file: str | Path = CLEAN_FILE) -> pd.DataFrame:
    """
    Load the cleaned dataset, retain only rows where functioning_day is Yes,
    sort the observations chronologically by date and hour, and reset the index.
    """
    df = load_clean(CLEAN_DIR / clean_file)         # the clean file only contians the file name

    df = (
        df[df["functioning_day"] == "Yes"]
        .sort_values(by=["date", "hour"])
        .reset_index(drop=True)
    )

    return df


def time_split(
    df: pd.DataFrame,
    cutoff_date: str | pd.Timestamp
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the operating data chronologically.

    Training data contains observations on or before the cutoff date.
    Test data contains observations strictly after the cutoff date.
    Both returned DataFrames have reset indices.
    """
    cutoff = pd.Timestamp(cutoff_date)

    train = (
        df.loc[df["date"] <= cutoff]
        .reset_index(drop=True)
    )

    test = (
        df.loc[df["date"] > cutoff]
        .reset_index(drop=True)
    )

    return train, test