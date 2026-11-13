import streamlit as st
import style

style.setup("Style test")
style.banner("Seoul Bike Rentals", "Rental demand across December 2017 to November 2018")

col1, col2, col3 = st.columns(3)
with col1:
    style.number_card("Peak month", "June", "29,896 rentals per day")
with col2:
    style.number_card("Lowest month", "January", "4,839 rentals per day")
with col3:
    style.number_card("Model error", "221", "Test months: Oct and Nov 2018", accent=True)

style.notice("2017 contains December only. Select 2018 to view monthly and seasonal patterns.")