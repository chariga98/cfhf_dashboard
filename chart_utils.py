"""
chart_utils.py
===============
Small, reusable chart-building functions - the Python equivalent of the
make_category_count / make_vertical_bar / make_horizontal_bar / make_pie_chart
/ make_scatter_plot helpers in the original app.R.

Each function returns a ready-to-display Plotly figure, so app.py never
has to build a chart "by hand" - it just calls one of these.
"""

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _empty_figure(message: str = "No data") -> go.Figure:
    """A blank placeholder chart, shown when a dataset/column has no data."""
    fig = go.Figure()
    fig.update_layout(
        title=message,
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[{
            "text": message, "xref": "paper", "yref": "paper",
            "showarrow": False, "font": {"size": 16},
        }],
    )
    return fig


def category_count(df: pd.DataFrame, column: str) -> Optional[pd.DataFrame]:
    """
    Tally how many times each unique value in `column` appears.

    Equivalent to R's make_category_count(): drops missing values, counts
    occurrences per category, and sorts from most to least common.
    Returns None if the column doesn't exist in df.
    """
    if column not in df.columns:
        return None

    counts = (
        df[column]
        .dropna()
        .value_counts()
        .rename_axis("Category")
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )
    return counts


def _subtitle(title: str, responded: int, total: int) -> str:
    """Build the '<title><br>Farmers responded: X out of Y' caption."""
    responded = min(responded, total)  # safety check, mirrors the R app
    return f"{title}<br><sup>Farmers responded: {responded} out of {total}</sup>"


def make_vertical_bar(data: Optional[pd.DataFrame], title: str,
                       responded: int, total: int) -> go.Figure:
    """Bar chart with upright bars, categories sorted by count (descending)."""
    if data is None or data.empty:
        return _empty_figure()

    fig = px.bar(
        data, x="Category", y="Count", color="Category",
        title=_subtitle(title, responded, total),
    )
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Count")
    fig.update_xaxes(tickangle=45)
    return fig


def make_horizontal_bar(data: Optional[pd.DataFrame], title: str,
                         responded: int, total: int) -> go.Figure:
    """Bar chart with horizontal bars, categories sorted by count (ascending, so the biggest bar is on top)."""
    if data is None or data.empty:
        return _empty_figure()

    data_sorted = data.sort_values("Count", ascending=True)
    fig = px.bar(
        data_sorted, x="Count", y="Category", color="Category", orientation="h",
        title=_subtitle(title, responded, total),
    )
    fig.update_layout(showlegend=False, xaxis_title="Count", yaxis_title="")
    return fig


def make_pie_chart(data: Optional[pd.DataFrame], title: str,
                    responded: int, total: int, doughnut: bool = False) -> go.Figure:
    """Pie chart; pass doughnut=True for a donut-style hole in the middle."""
    if data is None or data.empty:
        return _empty_figure()

    fig = px.pie(
        data, names="Category", values="Count",
        title=_subtitle(title, responded, total),
        hole=0.5 if doughnut else 0.0,
    )
    return fig


def make_scatter_plot(df: pd.DataFrame, column: str, title: str,
                       responded: int, total: int) -> go.Figure:
    """
    Scatter plot of Farmer_ID vs. a categorical "food type" column.
    Mirrors the Go/Grow/Glow-food scatter charts in the original app.
    """
    if column not in df.columns:
        return _empty_figure()

    data = df[["Farmer_ID", column]].dropna().rename(columns={column: "Food"})
    if data.empty:
        return _empty_figure()

    fig = px.scatter(
        data, x="Food", y="Farmer_ID", color="Food",
        title=_subtitle(title, responded, total),
    )
    fig.update_layout(showlegend=False, xaxis_title="Food Type", yaxis_title="Farmer ID")
    fig.update_xaxes(tickangle=45)
    return fig
