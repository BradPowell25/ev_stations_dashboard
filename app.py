import streamlit as st
import pydeck as pdk
import json
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Cost title
st.markdown(
    """
    <h1 style='text-align: center; font-size: 30px; margin-bottom: 24px;'>
    Cost Calculator
    </h1>
    """,
    unsafe_allow_html=True
)

# Define car brands and avg efficiencies
ev_car_brands = {
    "Tesla Model 3": 4.1,
    "Nissan Leaf": 3.6,
    "Chevrolet Bolt": 3.8,
    "Hyundai Kona Electric": 4.0,
    "Ford Mustang Mach-E": 3.5,
    "Audi e-tron": 2.6,
    "BMW i3": 3.4,
    "Other EV": 3.5,
}

gas_car_brands = {
    "Toyota Corolla": 32,
    "Honda Civic": 33,
    "Ford F-150": 20,
    "Chevrolet Silverado": 21,
    "BMW 3 Series": 27,
    "Audi A4": 28,
    "Other Gas Car": 25,
}

electricity_cost_per_kwh = 0.13  # Average cost (USD)
gas_price_per_gallon = 3.50  # Average cost (USD)

# Gas car inputs
col3, col4 = st.columns(2)
with col3:
    selected_gas_car = st.selectbox("Select Your Gas Car:", list(gas_car_brands.keys()), index=0)
with col4:
    gas_miles_per_week = st.number_input(
        "Miles Driven Per Week:",
        min_value=0,
        max_value=2000,
        value=250, 
        step=10,
    )

# Gas costs
gas_efficiency = gas_car_brands[selected_gas_car] 
gallons_needed = gas_miles_per_week / gas_efficiency  
gas_weekly_cost = gallons_needed * gas_price_per_gallon 
gas_monthly_cost = gas_weekly_cost * 4  
gas_yearly_cost = gas_weekly_cost * 52 

# EV car inputs
col1, col2 = st.columns(2)
with col1:
    selected_ev_car = st.selectbox("Select Your EV:", list(ev_car_brands.keys()), index=0)

# EV costs
ev_efficiency = ev_car_brands[selected_ev_car]  
ev_kwh_needed = gas_miles_per_week / ev_efficiency  
ev_weekly_cost = ev_kwh_needed * electricity_cost_per_kwh
ev_monthly_cost = ev_weekly_cost * 4 
ev_yearly_cost = ev_weekly_cost * 52 

# Comparison title
st.markdown(
    """
    <h1 style='text-align: center; font-size: 20px; margin-bottom: 24px;'>
    Cost Comparison
    </h1>
    """,
    unsafe_allow_html=True
)

col5, col_arrow, col6 = st.columns([2, 1, 2])
with col5:
    st.markdown(
        f"""
        <div style='border: 2px solid #FF5722; border-radius: 10px; padding: 10px; text-align: center;'>
        <b>Gas Weekly Cost:</b> ${gas_weekly_cost:.2f}<br>
        <b>Gas Monthly Cost:</b> ${gas_monthly_cost:.2f}<br>
        <b>Gas Yearly Cost:</b> ${gas_yearly_cost:.2f}
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_arrow:
    st.markdown(
        f"""
        <div style='text-align: center; font-size: 50px;'>
        &#x27A1;
        </div>
        """,
        unsafe_allow_html=True,
    )
with col6:
    st.markdown(
        f"""
        <div style='border: 2px solid #4CAF50; border-radius: 10px; padding: 10px; text-align: center;'>
        <b>EV Weekly Cost:</b> ${ev_weekly_cost:.2f}<br>
        <b>EV Monthly Cost:</b> ${ev_monthly_cost:.2f}<br>
        <b>EV Yearly Cost:</b> ${ev_yearly_cost:.2f}
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br><br>", unsafe_allow_html=True)
# Stations title
st.markdown(
    """
    <h1 style='text-align: center; font-size: 30px; margin-bottom: 24px;'>
    Electric Vehicle (EV) Charging Stations in the United States
    </h1>
    """,
    unsafe_allow_html=True
)

# TopoJSON data
with open('counties.json') as f:
    topojson_data = json.load(f)

# Population data
population_df = pd.read_csv('population.csv')
population_df = population_df.rename(columns={"lat": "Latitude", "lng": "Longitude", "population": "Population"})

# Stations data and preprocessing
file_name = 'ev_stations.csv'  
df = pd.read_csv(file_name)
df['ZIP'] = df['ZIP'].astype(str)

relevant_columns = [
    'Station Name', 'Street Address', 'City', 'State', 'ZIP',
    'Latitude', 'Longitude', 'EV Connector Types', 'Access Days Time',
    'Open Date', 'Facility Type', 'Access Code',
    'EV Pricing', 'Station Phone'
]

filtered_df = df[relevant_columns]
filtered_df = filtered_df.dropna(subset=['Open Date'])

# Fill missing values
filtered_df['Station Name'] = filtered_df['Station Name'].fillna('Unknown Station')
filtered_df['City'] = filtered_df['City'].fillna('Unknown City')
filtered_df['State'] = filtered_df['State'].fillna('Unknown State')
filtered_df['Facility Type'] = filtered_df['Facility Type'].fillna('Unknown Facility')
filtered_df['Station Phone'] = filtered_df['Station Phone'].fillna("Unknown Number")
filtered_df['EV Pricing'] = filtered_df['EV Pricing'].fillna("Unknown Pricing")
filtered_df['EV Connector Types'] = filtered_df['EV Connector Types'].fillna('Unknown Connector')
filtered_df['Access Days Time'] = filtered_df['Access Days Time'].fillna('Unknown Hours')

filtered_df['Open Date'] = pd.to_datetime(filtered_df['Open Date'], errors='coerce')
stations_df = filtered_df

# Heatmap checkbox
show_heatmap = st.checkbox("Population Heatmap", value=False)

# City, State
stations_df['City_State'] = stations_df['City'].str.lower().\
                            apply(lambda x: x.title()) + ', ' + stations_df['State']
city_names = sorted(stations_df['City_State'].unique())

def get_city_coordinates(city_name):
    city_data = stations_df[stations_df['City_State'].str.contains(city_name)]
    if not city_data.empty:
        lat, lon = city_data.iloc[0][['Latitude', 'Longitude']]
        return lat, lon
    else:
        return None, None

# Generate cumulative station counts over time
def generate_station_count_data(df):
    cumulative_counts = df.groupby('Open Date').size().cumsum().reset_index(name='Station Count')
    cumulative_counts['Open Date'] = cumulative_counts['Open Date'].dt.date
    cumulative_counts.columns = ['Date', 'Station Count']
    return cumulative_counts

# Sidebar and filters
# Date slider
st.sidebar.markdown("**Date Range (available stations between dates):**")
min_date = stations_df['Open Date'].min().date()
max_date = stations_df['Open Date'].max().date()
selected_date_range = st.sidebar.slider(
    "",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, min_date),
    format="MM-DD-YYYY"
)

# Change dates back to Timestamp
selected_start_date = pd.to_datetime(selected_date_range[0])
selected_end_date = pd.to_datetime(selected_date_range[1])

# City filter
st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.markdown("**City (Please remove location coordinates):**")
city_names.insert(0, "")
city_name = st.sidebar.selectbox("", city_names)
if city_name == "":  # No city selected
    city_name = None
else: 
    st.sidebar.success(f"Zoomed in on {city_name}")
    
# Access filter
st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.markdown("**Access:**")
access_type = stations_df['Access Code'].dropna().unique()
selected_access_types = st.sidebar.multiselect("", options=access_type, default=access_type)

# User location filter
st.sidebar.markdown("<br>", unsafe_allow_html=True) 
st.sidebar.markdown("**Enter Location (Please select no city):**")
user_lat = st.sidebar.number_input("Latitude", value=None, format="%.6f")
lat_dir = st.sidebar.selectbox("Latitude Direction", ["N", "S"], index=0)
user_lon = st.sidebar.number_input("Longitude", value=None, format="%.6f")
lon_dir = st.sidebar.selectbox("Longitude Direction", ["E", "W"], index=1)

user_coordinates = None
if user_lat is not None and user_lon is not None: # User entered coordinates
    if lat_dir == "S":
        user_lat = -abs(user_lat)
    if lon_dir == "W":
        user_lon = -abs(user_lon)
    
    user_coordinates = (user_lat, user_lon)
    city_name = None # Reset to default
    st.sidebar.success(f"Zoomed in on Location")

# Filter stations based on date range, city, and access
filtered_stations = stations_df[
        (stations_df["Open Date"] >= selected_start_date) & 
        (stations_df["Open Date"] <= selected_end_date)]
if city_name:
    filtered_stations = filtered_stations[filtered_stations['City_State'] == city_name]
filtered_stations = filtered_stations[filtered_stations['Access Code'].isin(selected_access_types)]

# Initial map view for the US
default_view_state = pdk.ViewState(
    longitude=-100.0,
    latitude=40.0,
    zoom=3.0,
    pitch=0,
)

# Update map view based on user input
if city_name:
    lat, lon = get_city_coordinates(city_name)
    if lat and lon:
        map_view_state = pdk.ViewState(
            longitude=lon,
            latitude=lat,
            zoom=10,
            pitch=0,
        )
elif user_coordinates:
    user_lat, user_lon = user_coordinates
    map_view_state = pdk.ViewState(
        longitude=user_lon,
        latitude=user_lat,
        zoom=12,
        pitch=0,
    )
else:
    map_view_state = default_view_state

# GeoJsonLayer for TopoJSON map
counties_layer = pdk.Layer(
    "GeoJsonLayer",
    topojson_data,
    get_fill_color=[255, 0, 0, 140],
    pickable=True,
    auto_highlight=True,
)

#Station Info
tooltip = {
    "html": "<b>Station Name:</b> {Station Name}<br>"
            "<b>Address:</b> {Street Address}, {City}, {State}, {ZIP}<br>"
            "<b>Hours:</b> {Access Days Time}<br>"
            "<b>Pricing:</b> {EV Pricing}<br>"
            "<b>Phone Number:</b> {Station Phone}<br>"
            "<b>Facility:</b> {Facility Type}<br>",
    "style": {"backgroundColor": "steelblue", "color": "white"}
}

# Tesla station or not 
def get_fill_color(ev_type):
    return [255, 0, 0] if "TESLA" in ev_type else [0, 255, 0]

# ScatterplotLayer for EV stations
def get_filtered_layer():
    return pdk.Layer(
        "ScatterplotLayer",
        filtered_stations, 
        get_position=["Longitude", "Latitude"],
        get_fill_color="fill_color", 
        get_radius=30,
        pickable=True,
        auto_highlight=True
    )
filtered_stations["fill_color"] = filtered_stations['EV Connector Types'].apply(get_fill_color)

# Population Heat Map
heatmap_layer = pdk.Layer(
    "HeatmapLayer",
    population_df,
    get_position=["Longitude", "Latitude"],
    get_weight="Population",  
    aggregation="MEAN", 
    opacity=0.3, 
    radius_pixels=30
)

stations_layer = get_filtered_layer()
if show_heatmap:
    layers = [counties_layer, stations_layer, heatmap_layer]
else: 
    layers = [counties_layer, stations_layer]

# Display map with layers
st.pydeck_chart(
    pdk.Deck(
        layers=layers,
        initial_view_state=map_view_state,
        map_style="dark",
        tooltip = tooltip
    )
)

# Legend for Tesla station or not
st.markdown(
    """
    <style>
    .legend {
        position: relative;
        bottom: 510px;
        left: 775px;
        background-color: white;
        padding: 10px;
        border: 2px solid #ddd;
        border-radius: 5px;
        font-size: 12px;
        max-width: 100px;
    }
    .legend div {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
    }
    .legend-color {
        width: 15px;
        height: 15px;
        margin-right: 5px;
        border-radius: 50%;
    }
    .red {
        background-color: red;
    }
    .green {
        background-color: green;
    }
    </style>
    <div class="legend">
        <div><div class="legend-color red"></div>Tesla</div>
        <div><div class="legend-color green"></div>Other</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Stations growth chart for filtered data
filtered_station_count = generate_station_count_data(filtered_stations)
trace_name = "United States" if city_name is None else f"{city_name}"
fig = make_subplots()
fig.add_trace(go.Scatter(x=filtered_station_count['Date'], y=filtered_station_count['Station Count'],
                         mode='lines', name=trace_name, line=dict(color='green')))
                    
fig.update_layout(
    title="Growth of EV Charging Stations",
    title_x=0.5,
    title_xanchor='center',
    xaxis_title="Date",
    yaxis_title="Number of Stations",
    xaxis=dict(tickformat="%m-%d-%Y"),
    height=500,
    showlegend=True,
)

# Display line chart
st.plotly_chart(fig)