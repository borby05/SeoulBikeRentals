import calendar
import math

import numpy as np
import pandas as pd
import streamlit as st

import style
import data
import charts

style.setup("Predict")
style.banner("Predict", "Estimate the rentals of one hour from the day and the weather")

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]  # 0 to 6
MONTHS = list(calendar.month_name)[1:]                                                      # January to December


@st.cache_data
def get_data():
    return data.load_all()


@st.cache_resource
def get_model():
    return data.load_model()


df = get_data()
metrics = data.load_metrics()
model = get_model()


def limits(column, step):
    """Lowest and highest value of one column in the data, rounded outward to the slider step."""
    low = math.floor(df[column].min() / step) * step
    high = math.ceil(df[column].max() / step) * step
    return float(low), float(high)


# ---------- Inputs ----------
inputs, result = st.columns([1, 1])

with inputs:
    st.subheader("When")
    col1, col2 = st.columns(2)
    with col1:
        hour = st.selectbox("Hour of the day", range(24), index=18, format_func=lambda h: f"{h:02d}:00")
        weekday_name = st.selectbox("Weekday", WEEKDAYS, index=2)
    with col2:
        month_name = st.selectbox("Month", MONTHS, index=5)
        holiday = st.checkbox("Public holiday")

    st.subheader("Weather")
    t_low, t_high = limits("temperature", 1)
    temperature = st.slider("Temperature (°C)", t_low, t_high, float(round(df["temperature"].median())), 0.5, format="%.1f")
    humidity = st.slider("Humidity (%)", 0, 100, int(df["humidity"].median()))
    w_low, w_high = limits("wind_speed", 0.5)
    wind_speed = st.slider("Wind speed (m/s)", w_low, w_high, round(float(df["wind_speed"].median()), 1), 0.1, format="%.1f")
    r_low, r_high = limits("rainfall", 1)
    rainfall = st.slider("Rainfall (mm)", r_low, r_high, 0.0, 0.5, format="%.1f")
    s_low, s_high = limits("snowfall", 1)
    snowfall = st.slider("Snowfall (cm)", s_low, s_high, 0.0, 0.1, format="%.1f")

# ---------- Prediction ----------
base = {
    "month": MONTHS.index(month_name) + 1,
    "weekday": WEEKDAYS.index(weekday_name),
    "holiday_flag": int(holiday),
    "temperature": temperature,
    "humidity": humidity,
    "wind_speed": wind_speed,
    "rainfall": rainfall,
    "snowfall": snowfall,
}
# One call predicts all 24 hours with the same day and weather. The chosen hour is one of them.
frame = pd.DataFrame([{**base, "hour": h} for h in range(24)])[metrics["features"]]
curve = np.maximum(model.predict(frame), 0)
value = float(curve[hour])

with result:
    st.subheader("Estimate")
    style.number_card("Predicted rentals", f"{value:,.0f}",
                      f"{weekday_name}, {month_name}, {hour:02d}:00", colour=style.AMBER, hero=True)
    style.number_card("Typical miss", f"about {metrics['mae']:,.0f}",
                      "rentals per hour, measured on the test months", colour=style.CORAL)
    style.notice(
        f"This model has an average error of about {metrics['mae']:,.0f} rentals per hour "
        f"and predicts about {abs(metrics['mean_error']):,.0f} rentals too low on average. "
        f"It was trained on {metrics['train_period']} and tested on {metrics['test_period']}, "
        f"so other months carry more uncertainty. Use the result as planning guidance."
    )
    rush = metrics["rush_hour_mean_error"].get(f"{hour:02d}:00")
    if rush is not None:
        style.notice(f"At {hour:02d}:00 the model ran about {abs(rush):,.0f} rentals too low "
                     f"on average in the test months.")

# ---------- Curve ----------
with st.container(border=True):
    charts.show(charts.predict_curve(curve, hour, "Predicted rentals across the day, weather held at your inputs"))

# ---------- Model notes ----------
with st.expander("Model notes"):
    base_mae = metrics["baseline_mae"]
    best = min(base_mae.values())
    improvement = (best - metrics["mae"]) / best * 100
    st.markdown(
        f"""
**Model:** {metrics['model']}. Trained on {metrics['train_period']}. Tested on {metrics['test_period']} ({metrics['test_rows']:,} hours).

**Inputs:** {", ".join(metrics['features'])}.

**Error on the test months**
- MAE: {metrics['mae']:,.1f} rentals per hour. This is the typical size of a miss.
- RMSE: {metrics['rmse']:,.1f}. R2: {metrics['r2']:.2f}.
- Mean error: {metrics['mean_error']:,.1f}. A negative value means the model predicts low.

**Simple baselines, MAE**
- Overall mean: {base_mae['overall_mean']:,.1f}
- Hour of day mean: {base_mae['hour_mean']:,.1f}
- Hour and weekend mean: {base_mae['hour_weekend_mean']:,.1f}
- The model is {improvement:.0f}% below the strongest baseline.

**Rush hours:** mean error of {metrics['rush_hour_mean_error']['08:00']:,.1f} at 08:00 and {metrics['rush_hour_mean_error']['18:00']:,.1f} at 18:00.

**Limits**
- The test months cover autumn only.
- The data covers one year.
- The test months never appear in the training months, so the month input is untested on unseen months.
- The public holiday box uses the same flag the model learned from.
"""
    )
