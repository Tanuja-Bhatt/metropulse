import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# =============================================================================
# METROPULSE — SHARED CHART STYLING
# =============================================================================

TEXT_COLOR = "#172033"
MUTED_TEXT = "#526078"
GRID_COLOR = "#D9DEE8"
ACCENT_COLOR = "#18A999"
ACCENT_BLUE = "#5B9FE3"
CARD_BACKGROUND = "#FFFFFF"


def apply_chart_style(
    fig,
    *,
    title=None,
    x_title=None,
    y_title=None,
    height=500,
):
    """
    Apply one consistent visual system to every MetroPulse Plotly chart.

    Main purpose:
    - Make axis titles visible
    - Make tick labels visible
    - Make chart titles visible
    - Improve gridline contrast
    - Keep charts consistent across all dashboard pages
    """

    fig.update_layout(
        title=dict(
            text=title if title else None,
            font=dict(
                color=TEXT_COLOR,
                size=18,
                family="Arial",
            ),
            x=0,
            xanchor="left",
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=CARD_BACKGROUND,

        font=dict(
            color=TEXT_COLOR,
            size=13,
            family="Arial",
        ),

        height=height,

        margin=dict(
            l=75,
            r=35,
            t=70,
            b=75,
        ),

        hoverlabel=dict(
            bgcolor="#172033",
            font=dict(
                color="#FFFFFF",
                size=13,
            ),
        ),

        legend=dict(
            font=dict(
                color=TEXT_COLOR,
                size=12,
            ),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor=GRID_COLOR,
            borderwidth=1,
        ),
    )

    # -------------------------------------------------------------------------
    # X AXIS
    # -------------------------------------------------------------------------

    fig.update_xaxes(
        title=dict(
            text=x_title,
            font=dict(
                color=TEXT_COLOR,
                size=14,
            ),
            standoff=12,
        ),
        tickfont=dict(
            color=TEXT_COLOR,
            size=12,
        ),
        showgrid=True,
        gridcolor=GRID_COLOR,
        gridwidth=1,
        zeroline=False,
        linecolor="#AEB7C7",
        linewidth=1,
        ticks="outside",
        tickcolor="#AEB7C7",
    )

    # -------------------------------------------------------------------------
    # Y AXIS
    # -------------------------------------------------------------------------

    fig.update_yaxes(
        title=dict(
            text=y_title,
            font=dict(
                color=TEXT_COLOR,
                size=14,
            ),
            standoff=12,
        ),
        tickfont=dict(
            color=TEXT_COLOR,
            size=12,
        ),
        showgrid=True,
        gridcolor=GRID_COLOR,
        gridwidth=1,
        zeroline=False,
        linecolor="#AEB7C7",
        linewidth=1,
        ticks="outside",
        tickcolor="#AEB7C7",
    )

    return fig


# =============================================================================
# TEMPORAL DEMAND
# =============================================================================

def hourly_demand_chart(df):
    """
    Hourly taxi demand over time.
    """

    data = df.copy()

    if "calendar_date" in data.columns:
        data["calendar_date"] = pd.to_datetime(
            data["calendar_date"],
            errors="coerce",
        )

    # Identify the hourly timestamp column.
    if "hourly_timestamp" in data.columns:
        x_column = "hourly_timestamp"
    elif "datetime" in data.columns:
        x_column = "datetime"
    elif "timestamp" in data.columns:
        x_column = "timestamp"
    elif "calendar_date" in data.columns and "hour_of_day" in data.columns:
        data["hourly_timestamp"] = (
            data["calendar_date"]
            + pd.to_timedelta(
                data["hour_of_day"],
                unit="h",
            )
        )
        x_column = "hourly_timestamp"
    else:
        raise ValueError(
            "Temporal dataset must contain an hourly timestamp "
            "or calendar_date + hour_of_day."
        )

    fig = px.line(
        data,
        x=x_column,
        y="taxi_trip_count",
        title="Hourly Taxi Demand",
    )

    fig.update_traces(
        line=dict(
            color=ACCENT_BLUE,
            width=2,
        ),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Taxi Trips: %{y:,.0f}"
            "<extra></extra>"
        ),
    )

    return apply_chart_style(
        fig,
        title="Hourly Taxi Demand",
        x_title="Time",
        y_title="Taxi Trips",
        height=500,
    )


def hourly_profile_chart(df):
    """
    Average taxi demand by hour of day.
    """

    data = df.copy()

    if "hour_of_day" not in data.columns:
        raise ValueError(
            "Temporal dataset must contain 'hour_of_day'."
        )

    grouped = (
        data
        .groupby("hour_of_day", as_index=False)
        ["taxi_trip_count"]
        .mean()
        .sort_values("hour_of_day")
    )

    fig = px.line(
        grouped,
        x="hour_of_day",
        y="taxi_trip_count",
        markers=True,
        title="Average Demand by Hour",
    )

    fig.update_traces(
        line=dict(
            color=ACCENT_COLOR,
            width=3,
        ),
        marker=dict(
            size=7,
            color=ACCENT_COLOR,
        ),
        hovertemplate=(
            "Hour: %{x}:00<br>"
            "Average Taxi Trips: %{y:,.0f}"
            "<extra></extra>"
        ),
    )

    fig.update_xaxes(
        dtick=1,
        tickmode="linear",
    )

    return apply_chart_style(
        fig,
        title="Average Demand by Hour",
        x_title="Hour of Day",
        y_title="Average Taxi Trips",
        height=500,
    )


# =============================================================================
# GEOGRAPHIC PERFORMANCE
# =============================================================================

def geographic_activity_chart(df, top_n=15):
    """
    Top taxi zones ranked by total activity.
    """

    data = df.copy()

    # Resolve the zone-name collision created by the spatial join.
    if "zone_y" in data.columns:
        zone_column = "zone_y"
    elif "zone" in data.columns:
        zone_column = "zone"
    elif "zone_x" in data.columns:
        zone_column = "zone_x"
    else:
        zone_column = None

    if zone_column is None:
        raise ValueError(
            "Geographic dataset does not contain a zone-name column."
        )

    if "total_zone_activity" not in data.columns:
        raise ValueError(
            "Geographic dataset does not contain "
            "'total_zone_activity'."
        )

    plot_df = (
        data[
            [
                zone_column,
                "total_zone_activity",
            ]
        ]
        .dropna(subset=[zone_column])
        .sort_values(
            "total_zone_activity",
            ascending=False,
        )
        .head(top_n)
        .sort_values(
            "total_zone_activity",
            ascending=True,
        )
    )

    plot_df = plot_df.rename(
        columns={
            zone_column: "zone",
        }
    )

    fig = px.bar(
        plot_df,
        x="total_zone_activity",
        y="zone",
        orientation="h",
        title=f"Top {top_n} Zones by Activity",
    )

    fig.update_traces(
        marker_color=ACCENT_BLUE,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Trips: %{x:,.0f}"
            "<extra></extra>"
        ),
    )

    return apply_chart_style(
        fig,
        title=f"Top {top_n} Zones by Activity",
        x_title="Trips",
        y_title="Pickup Zone",
        height=max(500, top_n * 32),
    )


# =============================================================================
# FARES & PAYMENTS
# =============================================================================

def payment_revenue_chart(df):
    """
    Revenue by canonical payment type.
    """

    data = df.copy()

    required = {
        "payment_type_label",
        "total_amount",
    }

    missing = required - set(data.columns)

    if missing:
        raise ValueError(
            f"Payment dataset is missing required columns: {sorted(missing)}"
        )

    # Safety guard against duplicate canonical labels.
    data = (
        data
        .groupby(
            "payment_type_label",
            as_index=False,
        )
        ["total_amount"]
        .sum()
        .sort_values(
            "total_amount",
            ascending=False,
        )
    )

    fig = px.bar(
        data,
        x="payment_type_label",
        y="total_amount",
        title="Revenue by Payment Type",
    )

    fig.update_traces(
        marker_color=ACCENT_BLUE,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Revenue: $%{y:,.2f}"
            "<extra></extra>"
        ),
    )

    return apply_chart_style(
        fig,
        title="Revenue by Payment Type",
        x_title="Payment Type",
        y_title="Total Amount ($)",
        height=500,
    )


# =============================================================================
# WEATHER & TRANSIT
# =============================================================================

def weather_demand_chart(df):
    """
    Average taxi demand by precipitation category.
    """

    data = df.copy()

    required = {
        "precipitation_category",
        "category_avg_taxi_trips",
    }

    missing = required - set(data.columns)

    if missing:
        raise ValueError(
            "Weather dataset is missing required columns: "
            f"{sorted(missing)}"
        )

    # Preserve a sensible weather ordering.
    category_order = [
        "Dry",
        "Light Rain",
        "Moderate Rain",
        "Heavy Rain",
    ]

    data["precipitation_category"] = pd.Categorical(
        data["precipitation_category"],
        categories=category_order,
        ordered=True,
    )

    data = data.sort_values("precipitation_category")

    fig = px.bar(
        data,
        x="precipitation_category",
        y="category_avg_taxi_trips",
        title="Average Taxi Demand by Precipitation",
    )

    fig.update_traces(
        marker_color=ACCENT_BLUE,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Average Taxi Trips: %{y:,.0f}"
            "<extra></extra>"
        ),
    )

    return apply_chart_style(
        fig,
        title="Average Taxi Demand by Precipitation",
        x_title="Precipitation",
        y_title="Average Taxi Trips",
        height=500,
    )