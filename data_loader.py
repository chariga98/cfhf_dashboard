"""
data_loader.py
===============
Everything related to getting data INTO the app: reading the Excel
workbook and building the simulated farmer GPS points used on the map.

All loading functions are wrapped in `st.cache_data`, so the (fairly slow)
Excel read only happens once per session, not on every filter click.
"""

import numpy as np
import pandas as pd
import streamlit as st

import config


@st.cache_data(show_spinner="Loading CFHF workbook...")
def load_all_sheets(data_file: str = str(config.DATA_FILE)) -> dict[str, pd.DataFrame]:
    """
    Read every sheet listed in config.SHEETS from the Excel workbook.

    Returns
    -------
    dict[str, pd.DataFrame]
        Keyed the same way as config.SHEETS, e.g. data["soil_health"].

    Raises
    ------
    FileNotFoundError
        If the workbook isn't where config.DATA_FILE expects it. app.py
        turns this into a friendly on-screen message rather than a crash.
    """
    if not config.DATA_FILE.exists():
        raise FileNotFoundError(
            f"Could not find the data workbook at: {config.DATA_FILE}\n"
            f"Place 'CFHF.Data.Stacked.xlsx' inside the 'Data' folder next "
            f"to app.py, or update DATA_FILE in config.py."
        )

    data = {}
    for key, sheet_name in config.SHEETS.items():
        try:
            data[key] = pd.read_excel(data_file, sheet_name=sheet_name)
        except ValueError:
            # Sheet not present in this workbook version - skip gracefully
            # instead of crashing the whole dashboard. The chart for this
            # dataset will simply show "No data".
            data[key] = pd.DataFrame()
    return data


@st.cache_data(show_spinner=False)
def build_farmer_locations(identifiers: pd.DataFrame) -> pd.DataFrame:
    """
    Simulate a GPS point for every unique farmer.

    The source data only has a County (not exact coordinates), so each
    farmer is placed near their county's center point with a small random
    offset ("jitter") so points don't all stack on top of each other on
    the map. A fixed random seed makes this reproducible between runs.

    Parameters
    ----------
    identifiers : pd.DataFrame
        Must contain Farmer_ID, County, and Organization columns.

    Returns
    -------
    pd.DataFrame with columns: Farmer_ID, County, Organization, latitude, longitude
    """
    rng = np.random.default_rng(config.RANDOM_SEED)

    unique_farmers = identifiers.drop_duplicates(subset="Farmer_ID").copy()

    county_df = pd.DataFrame(
        [(county, lat, lng) for county, (lat, lng) in config.COUNTY_CENTERS.items()],
        columns=["County", "lat", "lng"],
    )

    located = unique_farmers.merge(county_df, on="County", how="left")

    n = len(located)
    located["latitude"] = located["lat"] + rng.normal(0, config.JITTER_STD_DEV, n)
    located["longitude"] = located["lng"] + rng.normal(0, config.JITTER_STD_DEV, n)

    return located[["Farmer_ID", "County", "Organization", "latitude", "longitude"]]
