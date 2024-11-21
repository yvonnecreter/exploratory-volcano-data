# Imports
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as subplots
from urllib.request import urlopen
import json
from copy import deepcopy


# Load & Cache Data
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, index_col=0)
    return df


df_raw = load_data(path="volcano_ds_pop.csv")
df_org = deepcopy(df_raw)
df = df_org

with open("countries.geojson", "r") as file:
    geojson = json.load(file)

# Add title
st.title("Volcano Data Exploration")
st.text("Activity around the globe")

# Weight Danger Levels of volcano attributes:
# Quick, probably not scientifically accurate weighting of the severity of volcano attributes
status_danger_map = {
    "Holocene": 0.1,  # Minor recent activity
    "Historical": 0.2,  # Documented eruptions but not recently active
    "Tephrochronology": 0.3,  # Dating of ash layers, indicates potential but low immediate danger
    "Radiocarbon": 0.4,  # Indicates activity in the more distant past
    "Uncertain": 0.5,  # Unknown activity, medium risk due to uncertainty
    "Fumarolic": 0.6,  # Fumaroles suggest ongoing volcanic activity, moderate danger
    "Anthropology": 0.4,  # Likely represents historical human interaction, not immediate danger
    "Hydration Rind": 0.7,  # Indicates ancient eruptions, potential for reactivation
    "Varve Count": 0.3,  # Annual sediment layers, suggests distant past activity
    "Pleistocene-Fumarol": 0.9,  # Combined term, indicating significant activity in the past, high danger
    "Hot Springs": 0.7,  # Hot springs indicate geothermal activity, moderate danger
    "Dendrochronology": 0.2,  # Tree rings might indicate past eruptions but low current danger
    "Seismicity": 0.9,  # Active seismic activity, high danger
    "Ar/Ar": 0.5,  # Argon dating, indicates geological age, moderate danger
    "Hydrophonic": 0.8,  # Submarine activity, potential for tsunamis, high danger
    "Pleistocene": 0.7,  # Ancient eruptions, moderate potential for reactivation
}
df["Status_Id"] = df.Status.map(status_danger_map)
df["Status_Id"] = df.Status.map(status_danger_map)

lastknown_danger_map = {
    "Unknown": 0,
    "P": 0.25,
    "Q": 0.5,
    "U": 0.75,
    "D1": 0.875,
    "D2": 0.9375,
    "D3": 0.96875,
    "D4": 0.984375,
    "D5": 0.99609375,
    "D6": 0.998046875,
    "D7": 0.9990234375,
    "U1": 0.99951171875,
    "U7": 0.9990234375,
}
df["LastKnown_Id"] = df["Last Known"].map(lastknown_danger_map)
df["Weighted_Danger_Level"] = 0.7 * df["Status_Id"] + 0.3 * df["LastKnown_Id"]
moderate_danger_threshold = 0.5
high_danger_threshold = 0.7

st.sidebar.subheader("Advanced Filter Settings")

# Filter Options
# Create a checkbox Show dataframe to display/hide your dataset.
checkbox_df = st.sidebar.checkbox("Show dataset")
#     * Add a dropdown that lets users select based on some feature of your dataset (e.g. age of the dog owner).
left_column, right_column = st.columns([1, 1])
#     * Add “All” option to this dropdown.

# Sort by Type
volcano_types = ["All"] + sorted(pd.unique(df.Type))
volcano_type = left_column.selectbox("Type of volcano:", volcano_types)

# Sort by Status
volcano_status = ["All"] + sorted(pd.unique(df.Status))
volcano_state = right_column.selectbox("Volcano Status:", volcano_status)


# Sort by Population
pop_min = df_org["Population (2020)"].min()
pop_max = df_org["Population (2020)"].max()
popul_min, popul_max = st.sidebar.slider("Population in 2020", value=(pop_min, pop_max))
elv_min = df_org["Elev"].min()
elv_max = df_org["Elev"].max()
elev_min, elev_max = st.sidebar.slider("Elevation", value=(elv_min, elv_max))
dang_min, dang_max = st.sidebar.slider("Weighted Danger Level", value=(0.0, 1.0))

# Selection Handler
df = df_org
if volcano_type != "All":
    df = df[df.Type == volcano_type]
if volcano_state != "All":
    df = df[df.Status == volcano_state]
df = df[(df["Population (2020)"] >= popul_min) & (df["Population (2020)"] <= popul_max)]
df = df[(df["Elev"] >= elev_min) & (df["Elev"] <= elev_max)]
df = df[
    (df["Weighted_Danger_Level"] >= dang_min)
    & (df["Weighted_Danger_Level"] <= dang_max)
]

# Show Dataframe
if checkbox_df:
    st.text("My dataset:")
    st.dataframe(data=df_raw)

# Create a Plotly choropleth map, which visualizes the geospatial features and some interesting information from your dataset.
# Plot volcanoes with weighted colors on map
displ_option = st.radio("Map", ["Elevation", "Danger Levels"])
displ_map = {"Elevation": "Elev", "Danger Levels": "Weighted_Danger_Level"}
displ_color_map = {"Elevation": "Blues", "Danger Levels": "Thermal"}
df["Elev_Normalised"] = (df.Elev - df.Elev.min()) / (df.Elev.max() - df.Elev.min())

fig_scatter = px.scatter_mapbox(
    data_frame=df[
        [
            "Longitude",
            "Latitude",
            "Weighted_Danger_Level",
            "Last Known",
            "Status",
            "Elev",
            "Elev_Normalised",
            "Volcano Name",
            "Country",
        ]
    ].dropna(),
    lon="Longitude",
    lat="Latitude",
    size=(
        "Weighted_Danger_Level"
        if displ_option == "Danger Levels"
        else "Elev_Normalised"
    ),
    size_max=12,
    hover_name="Volcano Name",
    color=displ_map[displ_option],
    mapbox_style="carto-positron",
    hover_data=["Country", "Status", "Last Known"],
    center={"lat": 48.1372, "lon": 11.5758},
    zoom=1,
    color_continuous_scale=displ_color_map[displ_option],
    labels={displ_map[displ_option]: displ_option},
)
fig_scatter.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
st.plotly_chart(fig_scatter)


st.text(
    f"{len(df.Number.unique())}** Volcanoes out of {len(df_raw.Number.unique())} Total\n{len(df.Country.unique())} Countries out of {len(df_raw.Country.unique())} Total,\n{len(df[df.Weighted_Danger_Level>moderate_danger_threshold])} out of which above moderate danger threshold*,\n{len(df[df.Weighted_Danger_Level>high_danger_threshold])} above high danger threshold*."
)

# TODO Radiobutton: Top 10 Countries, Volcano Data
displ_option = st.sidebar.radio("Diagrams", ["World Information", "Volcano Data"])

if displ_option == "World Information":

    # Create a bar chart or a scatter plot for your dataset.
    # Plot volcanoes for all countries
    fig_bar = px.bar(
        data_frame=df,
        x="Country",
        hover_name="Volcano Name",
        color="Last Known",
        labels={"Last Known": "Strength of last known eruption", "count": "Count"},
    )
    st.plotly_chart(fig_bar)

    # Filter for top 10 countries
    volcano_count_df = (
        df.groupby("Country")
        .agg({"Number": "count"})
        .sort_values(by="Number", ascending=False)
    )
    top_countries = volcano_count_df[:10].index.to_list()

    # Plot top 10 countries
    fig = px.bar(
        data_frame=df.sort_values(by="LastKnown_Id").loc[
            df["Country"].isin(top_countries)
        ],
        x="Country",
        color="Last Known",
        hover_name="Volcano Name",
        barmode="stack",
        title="Top 10 countries",
        labels={"Last Known": "Strength of last known eruption", "count": "Count"},
    )
    fig.update_layout(xaxis={"categoryorder": "total descending"})
    st.plotly_chart(fig)
    st.text("* Further explanation here")
else:

    # Volcano Attributes + Danger Level Overview
    st.plotly_chart(
        px.treemap(
            data_frame=df,
            path=["Last Known", "Status", "Type", "Country"],
            hover_name="Volcano Name",
            values="Weighted_Danger_Level",
            color="Weighted_Danger_Level",
            title="Danger Level, Overview",
            color_continuous_scale="thermal",
            labels={"Weighted_Danger_Level": "Danger Level"},
        )
    )

    fig_volcano = subplots.make_subplots(
        4,
        3,
        specs=[
            [{"colspan": 2}, None, None],
            [None, {"colspan": 2}, None],
            [{"colspan": 2}, None, None],
            [None, {"colspan": 2}, None],
        ],
    )

    # * correlation of elevation and last known (filter by color= type) (boxplot)
    for trace in px.scatter(
        data_frame=df.sort_values(by="LastKnown_Id"),
        y="Elev",
        x="Last Known",
        hover_name="Volcano Name",
        opacity=0.2,
        labels={
            "Elev": "Elevation Level",
            "Last Known": "Last Known Eruption Strength",
        },
    ).data:
        fig_volcano.add_trace(
            trace,
            row=1,
            col=1,
        )

    # * correlation of last known and type
    for trace in px.scatter(
        data_frame=df.sort_values(by="LastKnown_Id"),
        y="Type",
        x="Last Known",
        hover_name="Volcano Name",
        opacity=0.2,
        labels={"Type": "Volcano Type", "Last Known": "Last Known Eruption Strength"},
    ).data:
        fig_volcano.add_trace(
            trace,
            row=2,
            col=2,
        )

    # * correlation of population and last known (filter by color = status), order by last known
    for trace in px.scatter(
        data_frame=df,
        y="Population (2020)",
        x="Last Known",
        hover_name="Volcano Name",
        opacity=0.2,
        labels={"Last Known": "Last Known Eruption Strength"},
    ).data:
        fig_volcano.add_trace(
            trace,
            row=3,
            col=1,
        )

    # * correlation of status and type
    for trace in px.scatter(
        data_frame=df,
        y="Status",
        x="Type",
        opacity=0.2,
        hover_name="Volcano Name",
        labels={"Status": "Status of Volcano", "Last Known": "Volcano Type"},
    ).data:
        fig_volcano.add_trace(
            trace,
            row=4,
            col=2,
        )

    fig_volcano.update_layout(height=1600, width=1000, title="Volcano Data, Overview")

    fig_volcano.add_trace(go.Scatter())
    st.plotly_chart(fig_volcano)


# * Add a radio button that lets users choose to display two different options (e.g. male/female or before/after).
# * Optional: Can you make this button work on both of your plots simultaneously?
# Further customize your app as you like (e.g. add a sidebar, split the page into columns, add text, etc.).
# Once you’re satisfied with your app, move on to the deployment stage.


# Ideas
# * Subplots for all volcano info with color selector 'Country'
# * Show Volcano name and number beneath labels on map

# * filter by population to see which volcanos introduce the most risk to humanity
# * put selection filters into a sidebar
# * Show map for * dangerlevel or * elevation (radiobutton)


# Verify Results https://volcano.si.edu/faq/index.cfm?question=countries
