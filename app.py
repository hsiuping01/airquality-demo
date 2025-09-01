# -*- coding: utf-8 -*-
"""
Created on Sat Aug 23 18:39:15 2025

@author: user
"""
import requests
import matplotlib.pyplot as plt
import streamlit as st

# ──────────────────────────────────────────────
# Streamlit App: Air Quality Checker
# This app fetches real-time air quality data
# from OpenWeatherMap API, given a city name.
# It then displays AQI (Air Quality Index),
# pollutant concentrations, and health advice.
# ──────────────────────────────────────────────

# Page configuration (title, icon, layout)
st.set_page_config(page_title="Air Quality Checker", page_icon="🌫️", layout="centered")
st.title("🌫️ Air Quality Checker")
st.caption("Enter a city name (e.g., Taipei or Paris,FR) to check real-time air quality.")

# API Key is read from Streamlit secrets (stored in .streamlit/secrets.toml)
API_KEY = st.secrets.get("OPENWEATHER_API_KEY", "")

# AQI categories (from OpenWeatherMap documentation)
AQI_TEXT = {
    1: "Good",
    2: "Fair",
    3: "Moderate",
    4: "Poor",
    5: "Very Poor"
}

# Health advice for each AQI category
HEALTH_ADVICE = {
    1: "✅ Air quality is good. Great for outdoor activities.",
    2: "🙂 Acceptable air quality. Minor precautions for sensitive groups.",
    3: "⚠️ Moderate pollution. Consider reducing outdoor exertion.",
    4: "🚫 Unhealthy. Avoid outdoor activities and wear a mask.",
    5: "❗ Very unhealthy. Stay indoors with air purification if possible."
}

# ──────────────────────────────────────────────
# Function: Convert city name to geographic coordinates (lat, lon)
# ──────────────────────────────────────────────
@st.cache_data(ttl=600)  # cache results for 10 minutes
def geocode_city(city_name: str):
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={API_KEY}"
    res = requests.get(url, timeout=10).json()
    if not res:
        return None
    return res[0]["lat"], res[0]["lon"]

# ──────────────────────────────────────────────
# Function: Fetch air quality data for given coordinates
# ──────────────────────────────────────────────
@st.cache_data(ttl=300)  # cache results for 5 minutes
def fetch_air_quality(lat: float, lon: float):
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    res = requests.get(url, timeout=10).json()
    if "list" not in res or not res["list"]:
        return None
    item = res["list"][0]
    return {
        "aqi": item["main"]["aqi"],        # Air Quality Index (1–5)
        "components": item["components"],  # Pollutant concentrations (μg/m³)
        "dt": item.get("dt")               # Timestamp
    }

# ──────────────────────────────────────────────
# Function: Create a bar chart for pollutant concentrations
# ──────────────────────────────────────────────
def plot_components(components: dict):
    keys = [k.upper() for k in components.keys()]
    values = list(components.values())
    fig = plt.figure(figsize=(8, 4.5))
    plt.bar(keys, values, color="skyblue")
    plt.title("Air Pollutant Concentrations (μg/m³)")
    plt.ylabel("Concentration (μg/m³)")
    plt.grid(axis='y', linestyle='--', alpha=0.4)
    plt.tight_layout()
    return fig

# ──────────────────────────────────────────────
# Streamlit UI: Input form
# ──────────────────────────────────────────────
with st.form("aq_form", clear_on_submit=False):
    city_input = st.text_input(
        "City name (add country code if possible, e.g., Tokyo,JP | Paris,FR | Taipei)",
        value="",
        placeholder="e.g., Taipei or Paris,FR"
    )
    submitted = st.form_submit_button("Check Air Quality")

# ──────────────────────────────────────────────
# Handle user input
# ──────────────────────────────────────────────
if submitted:
    # Check if API Key exists
    if not API_KEY:
        st.error("❌ API key not found. Please set OPENWEATHER_API_KEY in .streamlit/secrets.toml")
        st.stop()

    # Check if user entered a city
    if not city_input.strip():
        st.warning("⚠️ Please enter a city name.")
        st.stop()

    # Step 1: Convert city name to coordinates
    with st.spinner("🔎 Looking up city coordinates..."):
        coords = geocode_city(city_input.strip())

    if not coords:
        st.error("❌ City not found. Try again with country code (e.g., Paris,FR).")
        st.stop()

    lat, lon = coords
    st.info(f"📍 Coordinates: ({lat:.5f}, {lon:.5f})")

    # Step 2: Fetch air quality data
    with st.spinner("🌫️ Fetching air quality data..."):
        aq = fetch_air_quality(lat, lon)

    if not aq:
        st.error("❌ Failed to retrieve air quality data.")
        st.stop()

    # Step 3: Display results
    aqi = aq["aqi"]
    components = aq["components"]

    st.subheader("Air Quality Index (AQI)")
    st.write("AQI scale ranges from 1 (Good) to 5 (Very Poor).")
    st.metric(label="AQI Value", value=str(aqi), delta=AQI_TEXT.get(aqi, "Unknown"))
    st.write(HEALTH_ADVICE.get(aqi, "No advice available."))

    st.subheader("Pollutant Concentrations (μg/m³)")
    # Display data as table
    table_data = {k.upper(): f"{v:.2f}" for k, v in components.items()}
    st.table(table_data)

    # Display bar chart
    fig = plot_components(components)
    st.pyplot(fig)
    
st.markdown("---")
st.markdown("📊 **Data Source:** [OpenWeatherMap Air Pollution API](https://openweathermap.org/api/air-pollution)")