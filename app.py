import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Set up the Streamlit page
st.set_page_config(page_title="Flood Monitoring Dashboard", layout="wide")
st.title("🌊 Flood Monitoring Dashboard")

# Fetch all measurement stations
def get_stations():
    url = "https://environment.data.gov.uk/flood-monitoring/id/stations"
    response = requests.get(url).json()
    return response.get("items", [])

stations = get_stations()
station_options = {station["notation"]: station["label"] for station in stations}

# Select station
selected_station = st.selectbox(
    "Select a Station", 
    options=[""] + list(station_options.keys()), 
    format_func=lambda x: "Choose a station" if x == "" else station_options.get(x, x)
)

# Fetch available measures for the selected station
def get_measures(station_id):
    url = f"https://environment.data.gov.uk/flood-monitoring/id/stations/{station_id}/measures"
    response = requests.get(url).json()
    return response.get("items", [])

if selected_station:
    measures = get_measures(selected_station)
    measure_options = {measure["notation"]: f"{measure['label']} ({measure['unitName']})" for measure in measures}
    selected_measure = st.selectbox("Select a Measure", options=[""] + list(measure_options.keys()), format_func=lambda x: measure_options.get(x, "Choose a measure"))

    # Fetch readings for the selected measure in the last 24 hours
    def get_readings(measure_id):
        since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        url = f"https://environment.data.gov.uk/flood-monitoring/id/measures/{measure_id}/readings?_sorted&since={since}"
        response = requests.get(url).json()
        readings = response.get("items", [])
        return [{"Time": datetime.fromisoformat(r["dateTime"][:-1]).strftime('%Y-%m-%d %H:%M:%S'), "Value": r["value"]} for r in readings]

    if selected_measure:
        readings_data = get_readings(selected_measure)
        if readings_data:
            df = pd.DataFrame(readings_data)

            # Display line chart
            fig = px.line(df, x="Time", y="Value", title="Readings Over the Last 24 Hours", markers=True)
            st.plotly_chart(fig, use_container_width=True)

            # Display table
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No readings available for the selected measure.")
