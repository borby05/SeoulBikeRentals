# Seoul Bike Rentals

A year of hourly bike rental records, analysed month by month, compared side by side and used to estimate the demand of one hour. Demand means completed rentals. The project holds a data cleaning pipeline, a 2017 and a 2018 analysis, a prediction model and a Streamlit app.

**Live app:** https://YOUR-APP-NAME.streamlit.app

## What the project answers

- How much did demand rise and fall across the year, and which days stand out?
- How do months, seasons, hours, weekdays, weather and holidays shape demand?
- How far apart are any two months?
- How much demand should we expect in one hour, and how far off can that estimate be?

## The app

The Streamlit app has four pages.

| Page | What it does |
|---|---|
| Home | Headline figures, a year and month filter, and the main chart by month or season |
| Explore | Filters by year, month, day type and hours. Shows daily, monthly and hourly charts |
| Compare | Sets any two months side by side with six measures and a daily line for each |
| Predict | Estimates the demand of one hour from the day and the weather, with the typical error shown |

Every estimate on the Predict page carries the model's error and its limits.

## Model results

The model is a gradient boosting regressor. It trains on December 2017 to September 2018 and is scored on October and November 2018, two months it never saw.

| Measure | Value |
|---|---|
| MAE | 220.9 rentals per hour |
| RMSE | 291.8 |
| R2 | 0.73 |
| Mean error | -187.3 (the model predicts low) |
| Best baseline MAE | 272.9 (hour and weekend mean) |

The model predicts low most at the rush hours: 515.4 rentals low at 08:00 and 479.1 low at 18:00. The test covers autumn only and the data holds one year, so treat each estimate as planning guidance. The model report holds the full comparison, checks and limits.

## Clone and run

You need Git and Python 3.11 or higher.

**1. Clone the repository**

```
git clone https://github.com/borby05/SeoulBikeRentals.git
cd SeoulBikeRentals
```

**2. Create a virtual environment and install the libraries**

Windows (PowerShell):

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS or Linux:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**3. Start the app**

Run this from the repository root, not from the app folder.

```
streamlit run app/Home.py
```

The app opens at http://localhost:8501. It reads the cleaned data and the saved model from the repository, so nothing else needs to run first.

## Repository layout

```
SeoulBikeRentals/
  app/                 Streamlit app
    Home.py            Landing page and entry point
    pages/             Explore, Compare and Predict pages
    data.py            Loads the data and the model for the app
    charts.py          All charts
    style.py           Colours, styling and top navigation
    assets/logo.svg    Logo
  data/
    raw/               Source file, SeoulBikeData.csv
    clean/             Cleaned hourly table and the closed hours list
  models/
    gradient_boosting.joblib   Trained model
    metrics.json               Scores, features and rush-hour errors
  notebooks/           Cleaning, 2017 and 2018 analysis, audit and modelling notebooks
  src/                 clean.py, analysis.py and the modelling code
  .streamlit/          Theme and navigation settings
  requirements.txt     Pinned library versions
```

## Data notes

- Source: hourly records from 1 December 2017 to 30 November 2018, 8,760 rows. 8,465 are open hours.
- December 2017 is the only month of 2017.
- Closed days stay as gaps. They never count as zero.
- 6 October 2018 is a partial day with 17 open hours.
- Weekdays are coded 0 for Monday to 6 for Sunday.
- The model learned from the source holiday flag. The 2018 report uses a verified holiday list, which marks more dates.

## Reproduce the model

Run the modelling notebook from the top. Its final cell writes `models/gradient_boosting.joblib` and `models/metrics.json`. The time split trains on December 2017 to 30 September 2018 and tests on October and November 2018. The model settings are `max_iter=300`, `learning_rate=0.05` and `random_state=42`.

## Known limits

- One year of data. Each season appears once.
- The test covers October and November only.
- The model predicts low at 08:00 and 18:00.
- Weather values come from the user, not from a forecast.

## Libraries

streamlit 1.51.0, pandas 2.3.3, numpy 2.3.5, scikit-learn 1.7.2, joblib 1.5.2, plotly 6.5.0.
