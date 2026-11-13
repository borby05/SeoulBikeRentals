import streamlit as st

import style
import data
import charts
import analysis  # works because data.py adds the src folder to the path

style.setup("Seoul Bike Rentals")
style.banner("Seoul Bike Rentals", "Explore a year of rental demand, compare any two months and estimate the next hour.")


@st.cache_data
def get_data():
    return data.load_all()


df = get_data()
metrics = data.load_metrics()

# ---------- Filter bar ----------
col_year, col_month = st.columns(2)
with col_year:
    year_choice = st.selectbox("Year", ["All years", 2017, 2018])
year = None if year_choice == "All years" else year_choice

with col_month:
    month_choice = st.selectbox("Month", ["All months"] + data.month_labels(data.pick(df, year=year)))
months = None if month_choice == "All months" else [month_choice]

view = data.pick(df, year=year, months=months)

if year == 2017:
    style.notice("2017 contains December only. Select 2018 to view monthly and seasonal patterns.")

# ---------- Numbers ----------
daily = analysis.daily_table(view)
figures = analysis.headline_figures(daily)
busiest_hour = int(analysis.hour_profile(view).idxmax())

if months is None:
    monthly = data.monthly_table(view)
    top = monthly.loc[monthly["mean_daily_rentals"].idxmax()]
    low = monthly.loc[monthly["mean_daily_rentals"].idxmin()]
    peak = ("Peak month", top["month_label"], f"{top['mean_daily_rentals']:,.0f} rentals per day")
    lowest = ("Lowest month", low["month_label"], f"{low['mean_daily_rentals']:,.0f} rentals per day")
else:
    peak = ("Busiest day", figures["busiest_date"].strftime("%d %b %Y"),
            f"{figures['busiest_rentals']:,} rentals")
    lowest = ("Quietest day", figures["quietest_date"].strftime("%d %b %Y"),
              f"{figures['quietest_rentals']:,} rentals")

# ---------- Cards ----------
row1 = st.columns(3)
with row1[0]:
    style.number_card("Total rentals", f"{figures['total_rentals']:,}",
                      f"{figures['open_dates']} open days", colour=style.TEAL)
with row1[1]:
    style.number_card("Average per day", f"{figures['mean_per_day']:,.0f}",
                      "rentals per open day", colour=style.BLUE)
with row1[2]:
    style.number_card("Busiest hour", f"{busiest_hour:02d}:00",
                      "highest average rentals", colour=style.GREEN)

row2 = st.columns(3)
with row2[0]:
    style.number_card(*peak, colour=style.AMBER)
with row2[1]:
    style.number_card(*lowest, colour=style.CORAL)
with row2[2]:
    baseline = metrics["baseline_mae"]["hour_weekend_mean"]
    style.number_card(
        "Model error (MAE)",
        f"{metrics['mae']:,.0f}",
        f"Best baseline: {baseline:,.0f}. Tested on Oct and Nov 2018",
        hero=True,
    )

# ---------- Main chart ----------
st.subheader("Rental demand")
with st.container(border=True):
    if months is None:
        view_by = st.radio("View by", ["Month", "Season"], horizontal=True)
        if view_by == "Month":
            charts.show(charts.monthly_chart(monthly))
        else:
            seasons = analysis.season_summary(daily).dropna(subset=["mean_daily_rentals"])
            if seasons.empty:
                style.notice("Seasons need 2018 data. Select 2018 or All years.")
            else:
                charts.show(charts.season_chart(seasons))
    else:
        charts.show(charts.daily_line(data.month_series(daily), month_choice))

# ---------- Navigation ----------
st.subheader("Go further")
nav = st.columns(3)
with nav[0]:
    style.nav_card("Explore", "Filter by year, month, day type and hour. Follow one month day by day.")
    st.page_link("pages/1_Explore.py", label="Open Explore")
with nav[1]:
    style.nav_card("Compare", "Set any two months side by side and see who led, and by how much.")
    st.page_link("pages/2_Compare.py", label="Open Compare")
with nav[2]:
    style.nav_card("Predict", "Enter the day and the weather. Get an estimate for one hour.")
    st.page_link("pages/3_Predict.py", label="Open Predict")

# ---------- Footer ----------
closed, partial = data.closed_and_partial(daily, view)
st.caption(
    f"Data: Seoul Bike Rentals hourly records. In this view, {closed} closed day(s) appear as gaps "
    f"and never as zero, and {partial} day(s) hold only part of the 24 hours. "
    f"Model figures come from the test months October and November 2018."
)
