"""
app.py
======
CFHF: AE Farmers Trainings Dashboard (Python / Streamlit version)

This is the ONLY file you run: `streamlit run app.py`

WHAT THIS FILE DOES, TOP TO BOTTOM
-----------------------------------
1. Load the workbook (data_loader.py) and simulate farmer GPS points.
2. Draw the sidebar's cascading filters (Round -> Workshop -> Org ->
   County -> Sub-County -> Cluster -> Farmer) and apply them.
3. Draw the "Overview" tab: KPI counters + the Kenya map.
4. Draw the "Day 1" - "Day 5" tabs: every chart listed in
   config.CHART_SPECS, laid out automatically.
5. Provide the "Download Farmer Details" button in the sidebar.

All dataset locations, chart titles, and column names live in config.py.
All chart-drawing logic lives in chart_utils.py. This file is just the
"wiring" between them, so it stays short and easy to follow.
"""

import io

import pandas as pd
import plotly.express as px
import streamlit as st

import chart_utils
import config
from data_loader import build_farmer_locations, load_all_sheets

# ---------------------------------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CFHF: AE Farmers Trainings Dashboard",
    layout="wide",
)
st.title("CFHF: AE Farmers Trainings Dashboard")


# ---------------------------------------------------------------------------
# 1. LOAD DATA
# ---------------------------------------------------------------------------
try:
    data = load_all_sheets()
except FileNotFoundError as err:
    st.error(str(err))
    st.stop()

identifiers = data["identifiers"]
farmer_locations = build_farmer_locations(identifiers)


# ---------------------------------------------------------------------------
# 2. SIDEBAR: CASCADING FILTERS
# ---------------------------------------------------------------------------
# Each filter narrows down `working_df`, and the NEXT filter's dropdown
# options are built from whatever survives the filters applied so far -
# exactly like the chained observe() blocks in the original R app.
st.sidebar.header("Filters")

working_df = identifiers.copy()
selections = {}

for label, column in config.FILTER_FIELDS:
    if column not in working_df.columns:
        continue

    options = ["All"] + sorted(working_df[column].dropna().unique().tolist())
    choice = st.sidebar.selectbox(label, options, key=f"filter_{column}")
    selections[column] = choice

    if choice != "All":
        working_df = working_df[working_df[column] == choice]

filtered_ids = working_df  # final filtered Identifiers table, used everywhere below
total_farmers = filtered_ids["Farmer_ID"].nunique()


def filter_by_farmer(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows for farmers who survived the sidebar filters."""
    if df.empty or "Farmer_ID" not in df.columns:
        return df
    return df[df["Farmer_ID"].isin(filtered_ids["Farmer_ID"])]


# ---------------------------------------------------------------------------
# 3. SIDEBAR: DOWNLOAD FARMER DETAILS
# ---------------------------------------------------------------------------
def build_farmer_details_workbook() -> bytes:
    """
    Build an in-memory Excel workbook with:
      - Farmer Details : one row per farmer, with location + group info
      - QA Log         : simple data-quality summary
      - Problem Records: any duplicate/missing-ID rows (only if present)
    Mirrors the downloadHandler() in the original app.R.
    """
    details = (
        identifiers.drop_duplicates(subset="Farmer_ID")[
            ["Farmer_ID", "Farmer Name", "Workshop.Round", "Organization",
             "County", "Sub.County", "Cluster"]
        ]
        .merge(farmer_locations[["Farmer_ID", "latitude", "longitude"]],
                on="Farmer_ID", how="left")
    )

    # --- data quality checks ---
    duplicates = details[details.duplicated(subset="Farmer_ID", keep=False)]
    missing_ids = details[details["Farmer_ID"].isna() |
                           (details["Farmer_ID"].astype(str).str.strip() == "")]

    qa_log = pd.DataFrame({
        "Check": ["Total unique farmers", "Duplicate Farmer IDs found",
                  "Records with missing Farmer ID"],
        "Result": [len(details), len(duplicates), len(missing_ids)],
        "Status": ["INFO",
                   "PASS" if len(duplicates) == 0 else "FAIL",
                   "PASS" if len(missing_ids) == 0 else "FAIL"],
    })

    # --- apply the current sidebar filters, then tidy column names ---
    details_filtered = (
        details[details["Farmer_ID"].isin(filtered_ids["Farmer_ID"])]
        .rename(columns={
            "Farmer_ID": "Farmer ID",
            "Workshop.Round": "Workshop Round",
            "Sub.County": "Sub County",
            "latitude": "Latitude",
            "longitude": "Longitude",
        })
        .sort_values("Farmer ID")
    )

    # --- write everything to an in-memory .xlsx file ---
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        details_filtered.to_excel(writer, sheet_name="Farmer Details", index=False)
        qa_log.to_excel(writer, sheet_name="QA Log", index=False)
        if not duplicates.empty or not missing_ids.empty:
            problems = pd.concat([
                duplicates.assign(Issue="Duplicate ID"),
                missing_ids.assign(Issue="Missing ID"),
            ], ignore_index=True)
            problems.to_excel(writer, sheet_name="Problem Records", index=False)
    return buffer.getvalue()


st.sidebar.divider()
st.sidebar.download_button(
    label="Download Farmer Details",
    data=build_farmer_details_workbook(),
    file_name="Farmer Details.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    width="stretch",
)


# ---------------------------------------------------------------------------
# 4. MAIN TABS
# ---------------------------------------------------------------------------
tab_names = ["Overview"] + list(config.CHART_SPECS.keys())
tabs = st.tabs(tab_names)


# --- Overview tab: KPIs + map -------------------------------------------
with tabs[0]:
    kpi_cols = st.columns(6)
    kpi_values = [
        ("Farmers", filtered_ids["Farmer_ID"].nunique()),
        ("Workshops", filtered_ids["Workshop.Round"].nunique()),
        ("Organizations", filtered_ids["Organization"].nunique()),
        ("Counties", filtered_ids["County"].nunique()),
        ("Sub Counties", filtered_ids["Sub.County"].nunique()),
        ("Farmer Groups", filtered_ids["Cluster"].nunique()),
    ]
    for col, (label, value) in zip(kpi_cols, kpi_values):
        col.metric(label, value)

    st.subheader("Farmer Distribution Map")
    map_data = farmer_locations[
        farmer_locations["Farmer_ID"].isin(filtered_ids["Farmer_ID"])
    ]

    if map_data.empty:
        st.info("No farmers match the current filters.")
    else:
        color_map = {
            org: config.ORG_COLORS.get(org, config.DEFAULT_MARKER_COLOR)
            for org in map_data["Organization"].dropna().unique()
        }
        map_kwargs = dict(
            data_frame=map_data,
            lat="latitude", lon="longitude",
            color="Organization",
            color_discrete_map=color_map,
            hover_name="County",
            hover_data={"Organization": True, "latitude": False, "longitude": False},
            zoom=5.5, height=600,
        )
        # plotly >= 6 renamed scatter_mapbox -> scatter_map (no Mapbox token
        # required either way); support both so this runs on any recent
        # plotly version without the user needing to pin a specific one.
        if hasattr(px, "scatter_map"):
            fig_map = px.scatter_map(**map_kwargs)
            fig_map.update_layout(map_style="open-street-map")
        else:
            fig_map = px.scatter_mapbox(**map_kwargs)
            fig_map.update_layout(mapbox_style="open-street-map")

        fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        st.plotly_chart(fig_map, width="stretch")


# --- Day 1-5 tabs: charts driven entirely by config.CHART_SPECS ---------
CHART_FUNCTIONS = {
    "vertical": chart_utils.make_vertical_bar,
    "horizontal": chart_utils.make_horizontal_bar,
    "pie": lambda data, title, resp, tot: chart_utils.make_pie_chart(data, title, resp, tot, doughnut=False),
    "doughnut": lambda data, title, resp, tot: chart_utils.make_pie_chart(data, title, resp, tot, doughnut=True),
}

for tab, tab_name in zip(tabs[1:], config.CHART_SPECS.keys()):
    with tab:
        specs = config.CHART_SPECS[tab_name]
        i = 0
        while i < len(specs):
            # Group consecutive charts into a row based on their declared
            # widths (out of 12), so e.g. three width=4 charts share a row.
            row_specs, row_width = [], 0
            while i < len(specs) and row_width + specs[i]["width"] <= 12:
                row_specs.append(specs[i])
                row_width += specs[i]["width"]
                i += 1

            columns = st.columns([spec["width"] for spec in row_specs])
            for col, spec in zip(columns, row_specs):
                with col:
                    df = filter_by_farmer(data.get(spec["sheet"], pd.DataFrame()))
                    responded = df["Farmer_ID"].nunique() if "Farmer_ID" in df.columns else 0

                    if spec["kind"] == "scatter":
                        fig = chart_utils.make_scatter_plot(
                            df, spec["column"], spec["title"], responded, total_farmers
                        )
                    else:
                        counted = chart_utils.category_count(df, spec["column"])
                        fig = CHART_FUNCTIONS[spec["kind"]](
                            counted, spec["title"], responded, total_farmers
                        )
                    st.plotly_chart(fig, width="stretch")
