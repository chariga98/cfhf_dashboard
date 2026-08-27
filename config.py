"""
config.py
=========
Single source of truth for every path, constant, and "what chart goes where"
setting used by the dashboard.

WHY THIS FILE EXISTS
---------------------
The original R/Shiny app mixed file paths, county coordinates, colors, and
chart definitions directly into app.R. That makes the app fragile to
maintain: moving the data file or adding a new chart meant hunting through
600+ lines of UI/server code.

Here, everything that a future maintainer is likely to need to change lives
in ONE place. The rest of the app (data_loader.py, chart_utils.py, app.py)
simply reads from this file and never hard-codes a path, column name, or
color again.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# 1. FILE LOCATIONS
# ---------------------------------------------------------------------------
# Expected project layout:
#
#   cfhf_dashboard/
#   ├── app.py
#   ├── config.py
#   ├── data_loader.py
#   ├── chart_utils.py
#   ├── requirements.txt
#   └── Data/
#       └── CFHF.Data.Stacked.xlsx      <- put your workbook here
#
# If your workbook lives elsewhere, either move/rename it to match the path
# below, or change DATA_FILE to an absolute path (e.g. Path("C:/.../file.xlsx")).

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"
DATA_FILE = DATA_DIR / "CFHF.Data.Stacked.xlsx"

# ---------------------------------------------------------------------------
# 2. RANDOM SEED
# ---------------------------------------------------------------------------
# Farmer GPS points are not in the source data - they are simulated by
# jittering each farmer around their county's center point. The seed keeps
# that jitter identical every time the app runs, so the map doesn't "jump
# around" between sessions.
RANDOM_SEED = 42
JITTER_STD_DEV = 0.08  # degrees of lat/lng "noise" added around a county center

# ---------------------------------------------------------------------------
# 3. WORKBOOK SHEETS
# ---------------------------------------------------------------------------
# Maps a short, code-friendly key -> the exact sheet name inside the Excel
# workbook. Add a new dataset by adding one line here (see SHEET_COLUMN and
# CHART_SPECS below to also make it show up on a tab).
SHEETS = {
    "identifiers": "Identifiers",
    "soil_health": "Soil.Health.Practices",
    "pest_management": "Pest.Management.Practices",
    "nutrition": "Family.Nutrition",
    "value_addition": "IncomeGen.Val.Addition",
    "go_food": "Go-Food",
    "grow_food": "Grow-Food",
    "glow_food": "Glow-Food",
    "value_added_products": "ValueAdditionProducts",
    "sales_record": "Sales.Ravenue.Tracking",
    "livestock_practices": "LivestockPractices",
    "livestock_kept": "Livestock.Kept",
    "feed_materials": "Feed.Materials",
    "livestock_enterprise": "Livestock.Enterprises",
    "agroforestry": "Agroforestry.FoodForest",
    "appropriate_technology": "Appropriate.Technology",
    "soil_water_conservation": "Soil.Water.Conservation",
    "agroforestry_trees": "AgroforestryTreesGrown",
    "fruit_trees": "FruitTrees",
    "fodder_trees": "FodderTrees",
    "firewood_timber_trees": "Firewood.Timber.Trees",
    "tree_management": "Tree.Mgt.Practices",
    "medicinal_plants": "MedicinalPlants",
    "microgarden_types": "MicroGardenType",
    "green_energy_types": "GreenEnergyType",
    "drought_resistant_crops": "DroughtResistantCrops",
    "water_tolerant_crops": "WaterTolerantCrop",
}

# ---------------------------------------------------------------------------
# 4. KENYA COUNTY CENTER POINTS (used to plot farmers on the map)
# ---------------------------------------------------------------------------
COUNTY_CENTERS = {
    "Vihiga":        (0.09, 34.73),
    "Kericho":       (-0.37, 35.29),
    "Homa Bay":      (-0.53, 34.74),
    "Uasin Gishu":   (0.52, 35.27),
    "Kakamega":      (0.28, 34.75),
    "Migori":        (-1.06, 34.47),
    "Kisumu":        (-0.10, 34.75),
    "Siaya":         (0.06, 34.29),
    "Busia":         (0.46, 34.11),
    "Trans Nzoia":   (1.02, 34.95),
    "Nandi":         (0.18, 35.18),
    "Kiambu":        (-1.17, 36.83),
    "Bungoma":       (0.57, 34.71),
}

# Organization -> marker color on the map (falls back to grey if a new
# organization appears in the data that isn't listed here).
ORG_COLORS = {
    "SOFDI": "#FF6B6B",
    "KAPAP": "#4ECDC4",
    "KACE": "#45B7D1",
    "FIPS": "#FFA07A",
    "ANEW": "#98D8C8",
    "IEBC": "#F7DC6F",
    "CEFA": "#BB8FCE",
}
DEFAULT_MARKER_COLOR = "#AAAAAA"

# ---------------------------------------------------------------------------
# 5. CASCADING FILTER COLUMNS (sidebar dropdowns, applied in this order)
# ---------------------------------------------------------------------------
# Each entry is (widget_label, column_name_in_Identifiers_sheet).
FILTER_FIELDS = [
    ("Assessment Round", "Assesment.Round"),
    ("Workshop Round", "Workshop.Round"),
    ("Organization", "Organization"),
    ("County", "County"),
    ("Sub County", "Sub.County"),
    ("Cluster", "Cluster"),
    ("Farmer Name", "Farmer Name"),
]

# ---------------------------------------------------------------------------
# 6. CHART DEFINITIONS, ORGANIZED BY DASHBOARD TAB
# ---------------------------------------------------------------------------
# Each chart is defined once, declaratively, instead of as a hand-written
# render function (as the R app did ~30 times). app.py simply loops over
# this list and draws whatever is listed here. To add/remove/reorder a
# chart on a tab, edit this list - no other code changes needed.
#
# Fields:
#   sheet    : key from SHEETS above (which dataset to pull from)
#   column   : the column in that dataset to summarize/plot
#   title    : chart title shown to the user
#   kind     : "vertical" | "horizontal" | "pie" | "doughnut" | "scatter"
#   width    : how many of 12 grid columns the chart should span (Streamlit
#              layout hint used in app.py)
CHART_SPECS = {
    "Day 1: Soil Health": [
        dict(sheet="soil_health", column="Soil.Health.Practices",
             title="Soil Fertility Management: What Farmers Are Currently Doing",
             kind="vertical", width=12),
    ],
    "Day 2: Pest Management": [
        dict(sheet="pest_management", column="Pest.Management.Practices",
             title="Integrated Pest Management: What Farmers Are Currently Doing",
             kind="vertical", width=12),
    ],
    "Day 3: Nutrition & Value Addition": [
        dict(sheet="nutrition", column="Family.Nutrition.Practices",
             title="Family Nutrition: What Farmers Are Doing",
             kind="vertical", width=12),
        dict(sheet="value_addition", column="Income.ValueAddition.Practices",
             title="Income Generation and Value Addition",
             kind="horizontal", width=12),
        dict(sheet="go_food", column="Go-Foods", title="Go Foods",
             kind="scatter", width=4),
        dict(sheet="grow_food", column="Grow-Foods", title="Grow Foods",
             kind="scatter", width=4),
        dict(sheet="glow_food", column="Glow-Foods", title="Glow Foods",
             kind="scatter", width=4),
        dict(sheet="sales_record", column="Sales.Revenue.Tracking",
             title="Sales Revenue Tracking", kind="doughnut", width=6),
    ],
    "Day 4: Livestock": [
        dict(sheet="livestock_practices", column="Livestock.Practices",
             title="Livestock Production: Current Practices",
             kind="vertical", width=12),
        dict(sheet="livestock_kept", column="Livestock.Kept",
             title="Livestock Kept", kind="vertical", width=6),
        dict(sheet="feed_materials", column="Feed.Materials",
             title="Feed Materials", kind="horizontal", width=6),
        dict(sheet="livestock_enterprise", column="Livestock.Enterprises",
             title="Livestock Enterprises", kind="pie", width=12),
    ],
    "Day 5: Climate & Agroforestry": [
        dict(sheet="agroforestry", column="AgroforestryFoodForest",
             title="Agroforestry and Food Forest: What Farmers Have",
             kind="vertical", width=12),
        dict(sheet="appropriate_technology", column="AppropriateTechnology",
             title="Appropriate Technologies", kind="vertical", width=12),
        dict(sheet="soil_water_conservation", column="Soil.Water.Conservation",
             title="Soil & Water Conservation", kind="horizontal", width=12),
        dict(sheet="agroforestry_trees", column="AgroforestryTrees",
             title="Agroforestry Trees Grown", kind="vertical", width=6),
        dict(sheet="fruit_trees", column="FruitTrees",
             title="Fruit Trees Grown", kind="vertical", width=6),
        dict(sheet="fodder_trees", column="FodderTrees",
             title="Fodder Trees Grown", kind="horizontal", width=6),
        dict(sheet="firewood_timber_trees", column="FirewoodTimberTrees",
             title="Firewood/Timber Trees Grown", kind="vertical", width=6),
        dict(sheet="tree_management", column="TreeManagementPractices",
             title="Tree Management Practices", kind="doughnut", width=6),
        dict(sheet="medicinal_plants", column="MedicinalPlants",
             title="Medicinal Plants", kind="horizontal", width=6),
        dict(sheet="microgarden_types", column="MicrogardenTypes",
             title="Microgarden Types", kind="horizontal", width=6),
        dict(sheet="green_energy_types", column="GreenEnergyTypes",
             title="Green Energy Types", kind="vertical", width=4),
        dict(sheet="drought_resistant_crops", column="DroughtResistantCrops",
             title="Drought Resistant Crops", kind="vertical", width=4),
        dict(sheet="water_tolerant_crops", column="WaterTolerantCrops",
             title="Water Tolerant Crops", kind="vertical", width=4),
    ],
}
