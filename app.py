import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import pydeck as pdk

st.set_page_config(page_title="Flood Monitoring Dashboard", layout="wide")
st.title("Flood Monitoring Dashboard")

refresh_rate = 15  
refresh_seconds = refresh_rate * 60 

# Function to fetch stations
@st.cache_data(ttl=refresh_seconds)
def get_stations():
    url = "https://environment.data.gov.uk/flood-monitoring/id/stations"
    try:
        response = requests.get(url).json()
        return response.get("items", [])
    except Exception as e:
        st.error(f"Failed to fetch stations: {e}")
        return []

stations = get_stations()
station_options = {station["notation"]: station["label"] for station in stations}

selected_station = st.selectbox(
    "Select a Station", 
    options=[""] + list(station_options.keys()), 
    format_func=lambda x: "Choose a station" if x == "" else station_options.get(x, x)
)

if selected_station:
    # Function to fetch readings for the last 24 hours
    @st.cache_data(ttl=refresh_seconds)
    def get_readings(station_id):
        since = (datetime.now() - timedelta(days=1)).isoformat() + 'Z'
        url = f"https://environment.data.gov.uk/flood-monitoring/id/stations/{station_id}/readings?_sorted&since={since}"
        try:
            response = requests.get(url).json()
            readings = response.get("items", [])
            return [{"Time (yyyy-MM-dd HH:mm:ss)": datetime.fromisoformat(r["dateTime"][:-1]).strftime('%Y-%m-%d %H:%M:%S'), "Reading": r["value"]} for r in readings]
        except Exception as e:
            st.error(f"Failed to fetch readings: {e}")
            return []

    readings_data = get_readings(selected_station)
    
    if readings_data:
        df = pd.DataFrame(readings_data)

        # Line chart
        fig = px.line(df, x="Time (yyyy-MM-dd HH:mm:ss)", y="Reading", title="Readings Over the Last 24 Hours", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        # Table
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No readings available for the selected station.")

    if stations and selected_station:
        st.subheader(f"📍 Location of {station_options[selected_station]}")

        station_map_data = pd.DataFrame([
            {"lat": s["lat"], "lon": s["long"], "label": s["label"], "notation": s["notation"]}
            for s in stations if "lat" in s and "long" in s
        ])

        selected_station_data = station_map_data[station_map_data["notation"] == selected_station]

        if not selected_station_data.empty:
            default_lat, default_lon = selected_station_data.iloc[0]["lat"], selected_station_data.iloc[0]["lon"]
        else:
            default_lat, default_lon = station_map_data["lat"].mean(), station_map_data["lon"].mean()

        selected_station_layer = pdk.Layer(
            "ScatterplotLayer",
            data=selected_station_data,
            get_position="[lon, lat]",
            get_color="[255, 0, 0, 200]", 
            get_radius=3000,
            pickable=True,
            tooltip=True
        )

        other_stations_data = station_map_data[station_map_data["notation"] != selected_station]
        other_stations_layer = pdk.Layer(
            "ScatterplotLayer",
            data=other_stations_data,
            get_position="[lon, lat]",
            get_color="[0, 0, 255, 100]",
            get_radius=1000,
            pickable=False
        )

        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/outdoors-v11", 
            initial_view_state=pdk.ViewState(
                latitude=default_lat,
                longitude=default_lon,
                zoom=8, 
                pitch=50
            ),
            layers=[other_stations_layer, selected_station_layer],
        ))

        st.write(f"📌 Highlighted in **Red**: {station_options[selected_station]}. The blue markers respresent the other flood stations.")

        st.write(f"🔄 Auto-refreshing dashboard in {refresh_rate} minutes:")
        progress_bar = st.progress(0)

        for i in range(refresh_seconds):
            time.sleep(1)
            progress_bar.progress((i + 1) / refresh_seconds)

        st.rerun()