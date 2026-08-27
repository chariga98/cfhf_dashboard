# CFHF: AE Farmers Trainings Dashboard (Python)

A Python/Streamlit rewrite of the original R/Shiny dashboard. Same filters,
same charts, same "Download Farmer Details" export - now in a small set of
plain, commented Python files.

## Project layout

```
cfhf_dashboard/
├── app.py              # Run this. UI + wiring only - kept short on purpose.
├── config.py            # ALL paths, column names, colors, and chart definitions.
├── data_loader.py        # Reads the Excel workbook, builds farmer map points.
├── chart_utils.py        # Reusable chart-building functions.
├── requirements.txt
├── README.md
└── Data/
    └── CFHF.Data.Stacked.xlsx   <- put your workbook here (see below)
```

**Where does the data go?** Put your `CFHF.Data.Stacked.xlsx` workbook
inside the `Data/` folder, using that exact file name. If you'd rather keep
it somewhere else (a shared drive, a different name, etc.), open
`config.py` and change the `DATA_FILE` line near the top - that's the only
place a file path is set in the whole project.

## Setup (one time)

```bash
# 1. (recommended) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt
```

## Run the dashboard

```bash
streamlit run app.py
```

This opens the dashboard in your browser (usually `http://localhost:8501`).
Stop it anytime with `Ctrl+C` in the terminal.

## How the code is organized

- **`config.py`** - the file to edit for almost any maintenance task:
  moving the data file, renaming a column, changing an organization's map
  color, or adding/removing/reordering a chart on a tab. Every chart is
  described as one line in the `CHART_SPECS` dictionary rather than as a
  hand-written function, so adding a new chart doesn't require touching
  `app.py` at all.
- **`data_loader.py`** - loads every sheet from the Excel workbook once
  (cached, so filtering doesn't re-read the file) and simulates a GPS
  point per farmer for the map, since the source data only has counties,
  not coordinates.
- **`chart_utils.py`** - small functions that turn a filtered dataset into
  a bar / pie / doughnut / scatter chart. These are the Python equivalent
  of the `make_vertical_bar()` / `make_pie_chart()` etc. helpers from the
  original R app.
- **`app.py`** - reads the sidebar filters, narrows the data down step by
  step (Assessment Round → Workshop Round → Organization → County →
  Sub-County → Cluster → Farmer, exactly like the original cascading
  filters), then draws the Overview tab (KPI counters + map) and the five
  "Day" tabs by looping over `config.CHART_SPECS`.

## Notes on things that changed from the R version

- **Framework**: Shiny → Streamlit. Streamlit reruns the whole script on
  each interaction, which is what replaces the R app's `observe()` /
  `updateSelectInput()` blocks for the cascading filters - so the filter
  logic is actually simpler here.
- **Charts**: `ggplot2` + `plotly::ggplotly()` → `plotly.express` directly.
- **Map**: `leaflet` → `plotly.express.scatter_map` (falls back
  automatically to `scatter_mapbox` on older Plotly versions). No API key
  or token is required either way.
- **Excel export**: `writexl` → `pandas.ExcelWriter` with the `xlsxwriter`
  engine, built in memory and served through a Streamlit download button.

## Troubleshooting

- **"Could not find the data workbook..."** - the app couldn't find the
  Excel file. Double check it's named `CFHF.Data.Stacked.xlsx` and sits
  inside the `Data/` folder, or update `DATA_FILE` in `config.py`.
- **A chart shows "No data"** - that sheet/column either has no rows for
  the current filter selection, or the column name in your workbook
  doesn't match what's in `config.py`. Check the `CHART_SPECS` and
  `SHEETS` entries for that chart.
