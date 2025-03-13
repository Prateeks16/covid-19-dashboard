import streamlit as st
import pandas as pd
import plotly.express as px
import pycountry
import numpy as np
from scipy.signal import find_peaks

# Set page config at the very top
st.set_page_config(page_title="COVID-19 Dashboard", layout="wide")

# Load the dataset with caching for performance
@st.cache_data
def load_data():
    return pd.read_csv("P:\\Data science\\Python\\covid dataset\\owid-covid-data.csv", encoding="utf-8", engine="python")

df = load_data()

# Preprocess the data
df['date'] = pd.to_datetime(df['date'], errors="coerce")  # Ensure date is in datetime format
df.fillna(0, inplace=True)

# Function to get country flag URL using pycountry
def get_flag_url(country):
    iso_code_row = df[df['location'] == country]['iso_code']
    if iso_code_row.empty:
        return None  # No flag available
    iso3_code = iso_code_row.values[0]  # Three-letter ISO code
    country_obj = pycountry.countries.get(alpha_3=iso3_code)
    if country_obj:
        return f"https://flagsapi.com/{country_obj.alpha_2}/flat/64.png"
    return None

# Streamlit UI
st.title("📊 COVID-19 Dashboard")

# Disclaimer about data
st.markdown("**📢 Disclaimer:** This data is sourced from 'Our World in Data' and covers the period from the earliest recorded COVID-19 case up to the most recent data available in dataset. Some values may be missing or estimated based on reporting gaps.")

# Sidebar filters with improved layout
st.sidebar.header("Filter Options")
selected_country = st.sidebar.selectbox("Select a country:", df["location"].unique())

graph_style = st.sidebar.selectbox("Select Graph Style:", ["plotly_dark", "ggplot2", "seaborn", "plotly_white", "none"])
graph_template = graph_style if graph_style != "none" else None

# Filter data for the selected country
country_df = df[df["location"] == selected_country]
latest_data = country_df.iloc[-1]

# Global Stats
world_df = df[df["location"] == "World"].iloc[-1]

st.subheader("🌎 Global COVID-19 Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Cases", f"{int(world_df['total_cases']):,}")
col2.metric("Total Deaths", f"{int(world_df['total_deaths']):,}")

# Country Stats with Flag
flag_url = get_flag_url(selected_country)
st.subheader(f"{selected_country}")
if flag_url:
    st.image(flag_url, width=80)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Cases", f"{int(latest_data['total_cases']):,}")
col2.metric("Total Deaths", f"{int(latest_data['total_deaths']):,}")

# Case Fatality Rate (CFR)
cfr = (latest_data['total_deaths'] / latest_data['total_cases']) * 100 if latest_data['total_cases'] > 0 else 0
st.metric("Case Fatality Rate (CFR)", f"{cfr:.2f}%")

# Active Cases vs. Recovered vs. Deaths - Stacked Bar Chart
st.subheader("📊 Active Cases vs. Recovered vs. Deaths")
if 'total_cases' in df.columns and 'total_deaths' in df.columns:
    country_df['recovered'] = country_df['total_cases'] - country_df['total_deaths'] - country_df['new_cases']
    fig_stacked = px.bar(country_df, x='date', y=['new_cases', 'recovered', 'total_deaths'], 
                          labels={'value': 'Cases', 'date': 'Date'},
                          title="Active Cases vs. Recovered vs. Deaths",
                          template=graph_template, barmode='stack')
    st.plotly_chart(fig_stacked, use_container_width=True)

# Wave Detection - Identifying Peaks
st.subheader("📈 COVID-19 Waves (Peaks Detection)")
peaks, _ = find_peaks(country_df['new_cases'], height=1000)  # Adjust height as needed
fig_peaks = px.line(country_df, x='date', y='new_cases', title="Peaks in New Cases", template=graph_template)
fig_peaks.add_scatter(x=country_df.iloc[peaks]['date'], y=country_df.iloc[peaks]['new_cases'], mode='markers', marker=dict(color='red', size=8), name='Peaks')
st.plotly_chart(fig_peaks, use_container_width=True)

# Top 10 Worst-hit Countries Over Time Animation
st.subheader("🌍 Worst-hit Countries Over Time")
fig_animation = px.scatter_geo(df, locations="iso_code", color="total_cases",
                               hover_name="location", size="total_cases",
                               animation_frame=df["date"].astype(str),
                               title="Top 10 Worst-hit Countries Over Time",
                               color_continuous_scale=px.colors.sequential.Plasma,
                               template=graph_template)
st.plotly_chart(fig_animation, use_container_width=True)

# World Map Visualization
st.subheader("🗺️ Global COVID-19 Spread")
fig_world_map = px.choropleth(df[df['date'] == df['date'].max()], locations='iso_code', color='total_cases',
                              hover_name='location', title='COVID-19 Cases Worldwide',
                              color_continuous_scale=px.colors.sequential.Plasma, template=graph_template)
st.plotly_chart(fig_world_map, use_container_width=True, height=800)

# Footer
st.markdown("Data Source: [Our World in Data](https://ourworldindata.org/coronavirus)")