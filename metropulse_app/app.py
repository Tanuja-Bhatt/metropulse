import sys
from pathlib import Path

# Ensure the project root is available when Streamlit executes this file.
ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px

from html import escape
from pathlib import Path

from metropulse_app.charts import (
    geographic_activity_chart,
    hourly_demand_chart,
    hourly_profile_chart,
    payment_revenue_chart,
    weather_demand_chart,
)

from metropulse_app.formatting import (
    format_currency,
    format_minutes,
    format_number,
    format_percentage,
    format_speed,
)

from metropulse_app.queries import (
    get_data_quality_anomalies,
    get_executive_metrics,
    get_fare_payment_analysis,
    get_geographic_performance,
    get_temporal_demand,
    get_weather_transit_analysis,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ZONE_SHP = (
    PROJECT_ROOT
    / 'data'
    / 'processed'
    / 'zones'
    / 'taxi_zones'
    / 'taxi_zones.shp'
)

# =============================================================================
# PAGE CONFIGURATION + VISUAL SYSTEM
# =============================================================================

st.set_page_config(
    page_title='MetroPulse | NYC Mobility Intelligence',
    page_icon='🚕',
    layout='wide',
    initial_sidebar_state='expanded',
)

st.markdown(
    """
<style>
    :root {
        --mp-navy: #0b1736;
        --mp-navy-2: #13244a;
        --mp-teal: #13b8a6;
        --mp-teal-soft: #e8f8f5;
        --mp-text: #172033;
        --mp-muted: #687386;
        --mp-border: #e4e9f0;
        --mp-surface: #ffffff;
        --mp-bg: #f6f8fb;
    }

    .stApp { background: var(--mp-bg); }
    .block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1500px; }

    [data-testid='stSidebar'] {
        background: #0b1736;
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    [data-testid='stSidebar'] * { color: #eef4ff !important; }
    [data-testid='stSidebar'] .stRadio label {
        padding: 0.45rem 0.65rem;
        border-radius: 0.55rem;
    }
    [data-testid='stSidebar'] .stRadio label:hover {
        background: rgba(255,255,255,0.07);
    }

    .mp-brand {
        padding: 0.4rem 0.25rem 1.25rem 0.25rem;
        border-bottom: 1px solid rgba(255,255,255,0.10);
        margin-bottom: 1.2rem;
    }
    .mp-brand-name { font-size: 1.35rem; font-weight: 800; letter-spacing: -0.02em; }
    .mp-brand-sub { font-size: 0.72rem; color: #aebbd2 !important; margin-top: 0.15rem; }

    .mp-hero {
        background: linear-gradient(135deg, #0b1736 0%, #132b57 68%, #0e5d69 100%);
        border-radius: 1rem;
        padding: 2rem 2.15rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 12px 30px rgba(11,23,54,0.16);
        color: white;
    }
    .mp-eyebrow {
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        color: #72e0d4;
        margin-bottom: 0.45rem;
    }
    .mp-hero-title {
        font-size: 2.5rem;
        line-height: 1.05;
        font-weight: 850;
        letter-spacing: -0.04em;
    }
    .mp-hero-sub {
        max-width: 850px;
        margin-top: 0.7rem;
        color: #d8e2f2;
        font-size: 0.98rem;
        line-height: 1.55;
    }

    .mp-page-eyebrow {
        color: #0a8f82;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }
    .mp-page-title {
        color: var(--mp-text);
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.035em;
        margin-bottom: 0.15rem;
    }
    .mp-page-sub { color: var(--mp-muted); margin-bottom: 1.25rem; }

    .mp-kpi {
        background: var(--mp-surface);
        border: 1px solid var(--mp-border);
        border-radius: 0.85rem;
        padding: 1rem 1.05rem;
        min-height: 105px;
        box-shadow: 0 4px 14px rgba(20,31,56,0.045);
    }
    .mp-kpi-label {
        font-size: 0.69rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #778195;
    }
    .mp-kpi-value {
        font-size: 1.55rem;
        font-weight: 800;
        color: var(--mp-text);
        margin-top: 0.25rem;
        line-height: 1.15;
    }
    .mp-kpi-note {
        font-size: 0.72rem;
        color: var(--mp-muted);
        margin-top: 0.28rem;
    }

    .mp-finding {
        background: linear-gradient(90deg, #eefaf8 0%, #ffffff 100%);
        border: 1px solid #ccece7;
        border-left: 4px solid var(--mp-teal);
        border-radius: 0.8rem;
        padding: 1rem 1.15rem;
        margin: 0.65rem 0 1.35rem 0;
        color: #253044;
        line-height: 1.55;
    }
    .mp-finding-title { font-weight: 800; color: #087d73; margin-bottom: 0.2rem; }

    .mp-section {
        color: var(--mp-text);
        font-size: 1.15rem;
        font-weight: 800;
        letter-spacing: -0.015em;
        margin: 1.25rem 0 0.55rem 0;
    }
    .mp-card {
        background: white;
        border: 1px solid var(--mp-border);
        border-radius: 0.85rem;
        padding: 1rem 1.1rem;
        box-shadow: 0 4px 14px rgba(20,31,56,0.04);
        height: 100%;
    }
    .mp-card-num { color: #0a9d8f; font-size: 0.7rem; font-weight: 850; letter-spacing: 0.1em; }
    .mp-card-title { color: var(--mp-text); font-size: 1rem; font-weight: 800; margin-top: 0.2rem; }
    .mp-card-text { color: var(--mp-muted); font-size: 0.82rem; line-height: 1.5; margin-top: 0.35rem; }

    .mp-evidence {
        background: white;
        border: 1px solid var(--mp-border);
        border-radius: 0.8rem;
        padding: 0.9rem 1rem;
        margin-bottom: 0.7rem;
    }
    .mp-evidence-label { color: #7a8497; font-size: 0.68rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; }
    .mp-evidence-value { color: var(--mp-text); font-size: 1.3rem; font-weight: 800; margin-top: 0.2rem; }

    div[data-testid='stDataFrame'] {
        border: 1px solid var(--mp-border);
        border-radius: 0.7rem;
        overflow: hidden;
    }

    .stButton button, .stDownloadButton button { border-radius: 0.55rem; }
    h1, h2, h3 { color: var(--mp-text); }

    /* Main-content radio controls: keep labels readable on the light canvas. */
    [data-testid='stMainBlockContainer'] div[data-testid='stRadio'] label {
        color: var(--mp-text) !important;
        font-weight: 650 !important;
    }

    [data-testid='stMainBlockContainer'] div[data-testid='stRadio'] p {
        color: #526078 !important;
        font-weight: 700 !important;
    }

    [data-testid='stMainBlockContainer'] div[data-testid='stRadio'] div[role='radiogroup'] {
        gap: 0.35rem 1.1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# =============================================================================
# UI HELPERS
# =============================================================================

def page_header(eyebrow, title, subtitle):
    st.markdown(
        f"""
        <div class='mp-page-eyebrow'>{escape(eyebrow)}</div>
        <div class='mp-page-title'>{escape(title)}</div>
        <div class='mp-page-sub'>{escape(subtitle)}</div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label, value, note=''):
    st.markdown(
        f"""
        <div class='mp-kpi'>
            <div class='mp-kpi-label'>{escape(str(label))}</div>
            <div class='mp-kpi-value'>{escape(str(value))}</div>
            <div class='mp-kpi-note'>{escape(str(note))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def key_finding(text):
    st.markdown(
        f"""
        <div class='mp-finding'>
            <div class='mp-finding-title'>KEY FINDING</div>
            <div>{escape(str(text))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(text):
    st.markdown(f"<div class='mp-section'>{escape(str(text))}</div>", unsafe_allow_html=True)


def recommendation_card(number, title, text):
    st.markdown(
        f"""
        <div class='mp-card'>
            <div class='mp-card-num'>INITIATIVE {number}</div>
            <div class='mp-card-title'>{escape(title)}</div>
            <div class='mp-card-text'>{escape(text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_figure(fig, height=None):
    """Apply the shared dashboard visual system while keeping chart axes readable."""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#ffffff',
        font=dict(
            family='Inter, Segoe UI, Arial, sans-serif',
            color='#253044',
        ),
        margin=dict(
            l=72,
            r=22,
            t=58,
            b=72,
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='left',
            x=0,
            font=dict(
                color='#253044',
                size=12,
            ),
        ),
        hoverlabel=dict(
            bgcolor='#172033',
            font=dict(
                color='white',
                size=12,
            ),
        ),
    )

    # Explicitly set axis title/tick styling. Several Plotly figures inherit
    # very light text from the Streamlit theme, which makes labels disappear
    # against the white plotting surface.
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor='#d8dee8',
        linewidth=1,
        showticklabels=True,
        automargin=True,
        tickfont=dict(
            color='#526078',
            size=11,
        ),
        title_font=dict(
            color='#253044',
            size=12,
        ),
        title_standoff=10,
    )

    fig.update_yaxes(
        gridcolor='#edf0f4',
        zeroline=False,
        showline=False,
        showticklabels=True,
        automargin=True,
        tickfont=dict(
            color='#526078',
            size=11,
        ),
        title_font=dict(
            color='#253044',
            size=12,
        ),
        title_standoff=10,
    )

    if height is not None:
        fig.update_layout(height=height)

    return fig

# =============================================================================
# APPLICATION HEADER + NAVIGATION
# =============================================================================

st.markdown(
    """
    <div class='mp-hero'>
        <div class='mp-eyebrow'>NYC MOBILITY INTELLIGENCE</div>
        <div class='mp-hero-title'>MetroPulse</div>
        <div class='mp-hero-sub'>
            Market-level taxi demand, revenue, geography, weather, transit and data-quality intelligence
            across the April–June 2024 observation period.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """
    <div class='mp-brand'>
        <div class='mp-brand-name'>🚕 MetroPulse</div>
        <div class='mp-brand-sub'>NYC Mobility Intelligence</div>
    </div>
    """,
    unsafe_allow_html=True,
)

page = st.sidebar.radio(
    'Navigate',
    [
        'Executive Overview',
        'Temporal Demand',
        'Geographic Performance',
        'Fares & Payments',
        'Weather & Transit',
        'Data Quality & Anomalies',
    ],
)

# =============================================================================
# DATA LOADERS
# =============================================================================

@st.cache_data
def load_executive():
    return get_executive_metrics()

@st.cache_data
def load_temporal():
    return get_temporal_demand()

@st.cache_data
def load_geography():
    return get_geographic_performance()

@st.cache_data
def load_fares():
    return get_fare_payment_analysis()

@st.cache_data
def load_weather():
    return get_weather_transit_analysis()

@st.cache_data
def load_quality():
    return get_data_quality_anomalies()

@st.cache_data
def load_zone_shapes():
    if not ZONE_SHP.exists():
        raise FileNotFoundError(f'Taxi zone shapefile not found at: {ZONE_SHP}')
    zones = gpd.read_file(ZONE_SHP)
    if zones.crs is None or zones.crs.to_epsg() != 4326:
        zones = zones.to_crs(epsg=4326)
    zones['LocationID'] = pd.to_numeric(zones['LocationID'], errors='coerce')
    return zones

def create_zone_map(geography_df, metric):
    """Create an analytical NYC taxi-zone choropleth.

    The basemap is deliberately secondary. Taxi-zone polygons are colored
    according to the selected metric so the map answers a geographic question:
    where activity/revenue/intensity is concentrated or where observed activity
    is low.

    Geometry is passed only through GeoJSON. The Plotly dataframe contains no
    Shapely Polygon objects, avoiding Streamlit JSON serialization errors.
    """
    import json

    zones = load_zone_shapes().copy()

    # ---------------------------------------------------------
    # Normalize geographic identifiers on the shape side.
    # ---------------------------------------------------------
    zones['LocationID'] = pd.to_numeric(
        zones['LocationID'],
        errors='coerce',
    )

    zones = zones.dropna(subset=['LocationID']).copy()
    zones['LocationID'] = zones['LocationID'].astype(int)
    zones['location_id_str'] = zones['LocationID'].astype(str)

    # ---------------------------------------------------------
    # Normalize geographic identifiers on the mart side.
    # ---------------------------------------------------------
    geo = geography_df.copy()

    geo['location_id'] = pd.to_numeric(
        geo['location_id'],
        errors='coerce',
    )

    geo = geo.dropna(subset=['location_id']).copy()
    geo['location_id'] = geo['location_id'].astype(int)
    geo['location_id_str'] = geo['location_id'].astype(str)

    # One analytical row per location.
    geo = (
        geo.sort_values(
            'total_zone_activity',
            ascending=False,
        )
        .drop_duplicates(
            subset=['location_id'],
            keep='first',
        )
    )

    # ---------------------------------------------------------
    # Resolve the zone-name column.
    # ---------------------------------------------------------
    if 'zone' not in geo.columns:
        if 'zone_y' in geo.columns:
            geo['zone'] = geo['zone_y']
        elif 'zone_x' in geo.columns:
            geo['zone'] = geo['zone_x']

    if 'zone' not in geo.columns:
        geo['zone'] = (
            'Zone '
            + geo['location_id'].astype(str)
        )

    # ---------------------------------------------------------
    # Join analytical data to the taxi-zone polygons.
    # ---------------------------------------------------------
    map_df = zones.merge(
        geo.drop(columns=['geometry'], errors='ignore'),
        on='location_id_str',
        how='left',
        suffixes=('_shape', '_mart'),
    )

    # Prefer the mart zone name when available; otherwise use shape name.
    if 'zone_mart' in map_df.columns:
        map_df['map_zone'] = map_df['zone_mart']
    elif 'zone_shape' in map_df.columns:
        map_df['map_zone'] = map_df['zone_shape']
    elif 'zone' in map_df.columns:
        map_df['map_zone'] = map_df['zone']
    else:
        map_df['map_zone'] = (
            'Zone '
            + map_df['LocationID'].astype(str)
        )

    map_df['map_zone'] = (
        map_df['map_zone']
        .fillna(
            'Zone '
            + map_df['LocationID'].astype(str)
        )
    )

    # ---------------------------------------------------------
    # Metric configuration.
    # ---------------------------------------------------------
    if metric == 'Trip Activity':
        value_column = 'total_zone_activity'
        colorbar_title = 'Taxi Trips'
        color_scale = 'Blues'
        map_title = 'Where Taxi Activity Is Concentrated'

    elif metric == 'Revenue':
        value_column = 'total_zone_revenue'
        colorbar_title = 'Revenue ($)'
        color_scale = 'Blues'
        map_title = 'Where Taxi Revenue Is Concentrated'

    elif metric == 'Revenue per Activity':
        value_column = 'revenue_per_zone_activity'
        colorbar_title = 'Revenue / Activity ($)'
        color_scale = 'Blues'
        map_title = 'Where Activity Generates More Revenue'

    else:
        value_column = 'low_activity_value'
        colorbar_title = 'Low Activity'
        color_scale = 'Reds'
        map_title = 'Where Observed Activity Is Low'

    # ---------------------------------------------------------
    # Build the analytical map value.
    # ---------------------------------------------------------
    if value_column == 'low_activity_value':
        median_activity = pd.to_numeric(
            geo['total_zone_activity'],
            errors='coerce',
        ).median()

        map_df['map_value'] = (
            (
                pd.to_numeric(
                    map_df['total_zone_activity'],
                    errors='coerce',
                ) < median_activity
            )
            &
            (
                pd.to_numeric(
                    map_df['total_zone_activity'],
                    errors='coerce',
                ) > 0
            )
        ).astype(int)

        range_color = (0, 1)

    else:
        map_df[value_column] = pd.to_numeric(
            map_df[value_column],
            errors='coerce',
        ).fillna(0.0)

        # Robust visual scaling: cap only the displayed color range so a
        # handful of extreme zones do not wash out the rest of NYC.
        non_zero = map_df.loc[
            map_df[value_column] > 0,
            value_column,
        ]

        if len(non_zero) > 10:
            lower = float(non_zero.quantile(0.02))
            upper = float(non_zero.quantile(0.98))

            if upper > lower:
                map_df['map_value'] = map_df[value_column].clip(
                    lower=lower,
                    upper=upper,
                )
                range_color = (lower, upper)
            else:
                map_df['map_value'] = map_df[value_column]
                range_color = (
                    float(non_zero.min()),
                    float(non_zero.max()),
                )
        else:
            map_df['map_value'] = map_df[value_column]
            range_color = (
                float(non_zero.min()),
                float(non_zero.max()),
            ) if len(non_zero) else None

    # ---------------------------------------------------------
    # Build GeoJSON with integer-string IDs.
    #
    # This is the critical polygon matching fix:
    # GeoJSON feature.id == plot_df location_id_str
    # ---------------------------------------------------------
    geojson = json.loads(
        zones[['location_id_str', 'geometry']].to_json()
    )

    for feature in geojson['features']:
        feature['id'] = str(
            feature['properties']['location_id_str']
        )

    # ---------------------------------------------------------
    # Plotly dataframe MUST NOT contain geometry.
    # ---------------------------------------------------------
    plot_df = map_df.drop(
        columns=['geometry'],
        errors='ignore',
    ).copy()

    # ---------------------------------------------------------
    # Hover content.
    # ---------------------------------------------------------
    hover_data = {
        'location_id': ':,.0f',
        'total_zone_activity': ':,.0f',
        'total_zone_revenue': '$,.0f',
        'revenue_per_zone_activity': '$,.2f',
        'zone_activity_contribution_pct': ':.2f',
        'zone_revenue_contribution_pct': ':.2f',
        'activity_rank': ':,.0f',
        'revenue_rank': ':,.0f',
        'location_id_str': False,
        'map_value': False,
    }

    hover_data = {
        column: format_spec
        for column, format_spec in hover_data.items()
        if column in plot_df.columns
    }

    # ---------------------------------------------------------
    # Create the choropleth.
    # ---------------------------------------------------------
    fig = px.choropleth_mapbox(
        plot_df,
        geojson=geojson,
        locations='location_id_str',
        featureidkey='id',
        color='map_value',
        hover_name='map_zone',
        hover_data=hover_data,
        color_continuous_scale=color_scale,
        range_color=range_color,
        mapbox_style='carto-positron',
        center={
            'lat': 40.735,
            'lon': -73.94,
        },
        zoom=9.7,
        opacity=0.78,
    )

    # Make taxi-zone boundaries visible.
    fig.update_traces(
        marker_line_width=0.75,
        marker_line_color='rgba(30,45,65,0.65)',
    )

    fig.update_layout(
        height=650,
        margin=dict(
            l=0,
            r=0,
            t=50,
            b=0,
        ),
        title=dict(
            text=map_title,
            x=0,
            xanchor='left',
            font=dict(
                size=19,
                color='#172033',
            ),
        ),
        coloraxis_colorbar=dict(
            title=colorbar_title,
            thickness=15,
            len=0.68,
            title_font=dict(
                color='#172033',
                size=12,
            ),
            tickfont=dict(
                color='#526078',
                size=11,
            ),
        ),
    )

    return fig

# =============================================================================
# EXECUTIVE OVERVIEW
# =============================================================================

if page == 'Executive Overview':
    df = load_executive()
    row = df.iloc[0]

    page_header('DECISION LAYER', 'Executive Overview', 'Market-level view of observed NYC taxi activity and operational demand concentration.')

    cols = st.columns(4)
    with cols[0]: kpi_card('NYC market trips', format_number(row['total_trips']), 'Observed taxi activity')
    with cols[1]: kpi_card('NYC taxi market revenue', format_currency(row['total_amount']), 'Observed charged amount')
    with cols[2]: kpi_card('Amount / trip', format_currency(row['avg_amount_per_trip']), 'Average observed charge')
    with cols[3]: kpi_card('Airport-trip share', format_percentage(row['airport_share_pct']), 'Share of observed trips')

    section_title('Demand Profile')
    cols = st.columns(3)
    with cols[0]: kpi_card('Peak hour', f"{int(row['peak_hour']):02d}:00", 'Highest average hourly demand')
    with cols[1]: kpi_card('Peak-hour share', format_percentage(row['peak_hour_share_pct']), 'Peak hour / total observed trips')
    with cols[2]: kpi_card('Demand CV', format_percentage(row['hourly_demand_cv_pct']), 'Observed hourly volatility')

    key_finding(
        f"Observed taxi demand peaks at {int(row['peak_hour']):02d}:00, with that hour accounting for "
        f"{row['peak_hour_share_pct']:.1f}% of market trips over the assessment period. This is a demand-concentration signal, not evidence of unmet demand because vehicle supply is not observed."
    )

    section_title('Operational Recommendations')
    c1, c2 = st.columns(2)
    with c1:
        recommendation_card('01', 'Airport-focused capacity allocation', 'Test targeted capacity allocation in the 14:00–18:00 airport peak window.')
        with st.expander('4-week experiment design'):
            st.markdown('**Primary experimental metric:** completed airport trips per available vehicle-hour.')
            st.markdown('**Secondary metric:** airport revenue per available vehicle-hour.')
            st.markdown('**Guardrails:** total revenue per available vehicle-hour, non-airport completed trips, wait/rejection/fulfilment measures.')
    with c2:
        recommendation_card('02', 'Multi-hour citywide peak-capacity planning', 'Test capacity planning across the 16:00–20:00 citywide demand window.')
        with st.expander('4-week experiment design'):
            st.markdown('**Primary experimental metric:** completed trips per available vehicle-hour in the 16:00–20:00 window.')
            st.markdown('**Secondary metric:** revenue per available vehicle-hour.')
            st.markdown('**Guardrails:** wait/rejection, utilization, post-20:00 service, total revenue.')

    st.caption('Historical evidence supports these as experimental targets. The dataset does not observe vehicle supply or unmet demand.')

# =============================================================================
# TEMPORAL DEMAND
# =============================================================================

elif page == 'Temporal Demand':

    df = load_temporal().copy()

    # Ensure consistent datetime type
    df["calendar_date"] = pd.to_datetime(df["calendar_date"])

    page_header(
        "TEMPORAL",
        "Temporal Demand",
        "How does taxi demand vary across the observation period and operating hours?"
    )

    # ---------------------------------------------------------
    # FILTERS
    # ---------------------------------------------------------

    data_min_date = df["calendar_date"].min().normalize()
    data_max_date = df["calendar_date"].max().normalize()

    f1, f2 = st.columns([1.5, 1])

    with f1:

        date_preset = st.selectbox(
            "Date window",
            [
                "Full period",
                "Past week",
                "Past month",
                "Past 3 months",
                "Custom",
            ],
            key="temporal_date_preset",
        )

    with f2:

        hour_range = st.slider(
            "Hour of day",
            min_value=0,
            max_value=23,
            value=(0, 23),
            key="temporal_hour_range",
        )

    # ---------------------------------------------------------
    # DATE PRESET
    # ---------------------------------------------------------

    if date_preset == "Full period":

        start_date = data_min_date
        end_date = data_max_date

    elif date_preset == "Past week":

        start_date = max(
            data_min_date,
            data_max_date - pd.Timedelta(days=6),
        )

        end_date = data_max_date

    elif date_preset == "Past month":

        start_date = max(
            data_min_date,
            data_max_date - pd.Timedelta(days=29),
        )

        end_date = data_max_date

    elif date_preset == "Past 3 months":

        start_date = max(
            data_min_date,
            data_max_date - pd.Timedelta(days=89),
        )

        end_date = data_max_date

    else:

        custom_range = st.date_input(
            "Custom date range",
            value=(
                data_min_date.date(),
                data_max_date.date(),
            ),
            min_value=data_min_date.date(),
            max_value=data_max_date.date(),
            key="temporal_custom_range",
        )

        if len(custom_range) == 2:

            start_date = pd.Timestamp(custom_range[0])
            end_date = pd.Timestamp(custom_range[1])

        else:

            start_date = data_min_date
            end_date = data_max_date

    # ---------------------------------------------------------
    # APPLY DATE FILTER
    # ---------------------------------------------------------

    filtered = df[
        (df["calendar_date"] >= start_date)
        &
        (
            df["calendar_date"]
            < end_date + pd.Timedelta(days=1)
        )
    ].copy()

    # ---------------------------------------------------------
    # APPLY HOUR FILTER
    # ---------------------------------------------------------

    start_hour, end_hour = hour_range

    filtered = filtered[
        (filtered["hour_of_day"] >= start_hour)
        &
        (filtered["hour_of_day"] <= end_hour)
    ].copy()

    # ---------------------------------------------------------
    # EMPTY RESULT PROTECTION
    # ---------------------------------------------------------

    if filtered.empty:

        st.warning(
            "No observations match the selected date and hour filters. "
            "Expand the assessment window or hour range."
        )

    else:

        # -----------------------------------------------------
        # FILTER SUMMARY
        # -----------------------------------------------------

        st.caption(
            f"Showing {len(filtered):,} hourly observations "
            f"from {filtered['calendar_date'].min().date()} "
            f"to {filtered['calendar_date'].max().date()}, "
            f"hours {start_hour:02d}:00–{end_hour:02d}:00."
        )

        # Show the actual dataset-relative window
        st.caption(
            f"Date window: {start_date.date()} → {end_date.date()} "
            f"({date_preset})"
        )

        # -----------------------------------------------------
        # KEY FINDING — USE FILTERED DATA
        # -----------------------------------------------------

        hourly_summary = (
            filtered
            .groupby(
                "hour_of_day",
                as_index=False
            )["taxi_trip_count"]
            .mean()
            .sort_values(
                "taxi_trip_count",
                ascending=False
            )
        )

        peak_row = hourly_summary.iloc[0]
        low_row = hourly_summary.iloc[-1]

        peak_hour = int(
            peak_row["hour_of_day"]
        )

        peak_demand = float(
            peak_row["taxi_trip_count"]
        )

        low_hour = int(
            low_row["hour_of_day"]
        )

        low_demand = float(
            low_row["taxi_trip_count"]
        )

        demand_gap_pct = (
            (
                (peak_demand - low_demand)
                / low_demand
            ) * 100
            if low_demand > 0
            else 0
        )

        key_finding(
            f"Within the selected window, average demand peaks around "
            f"{peak_hour:02d}:00 at {peak_demand:,.0f} trips/hour "
            f"and is lowest around {low_hour:02d}:00 at "
            f"{low_demand:,.0f} trips/hour — a "
            f"{demand_gap_pct:.1f}% difference."
        )

        # -----------------------------------------------------
        # CHART 1 — FILTERED DATA
        # -----------------------------------------------------

        section_title(
            "Hourly Taxi Demand Over Time"
        )

        st.plotly_chart(
            style_figure(
                hourly_demand_chart(filtered),
                480,
            ),
            use_container_width=True,
        )

        # -----------------------------------------------------
        # CHART 2 — FILTERED DATA
        # -----------------------------------------------------

        section_title(
            "Average Demand by Hour"
        )

        st.plotly_chart(
            style_figure(
                hourly_profile_chart(filtered),
                450,
            ),
            use_container_width=True,
        )

        # -----------------------------------------------------
        # FILTERED SUMMARY TABLE
        # -----------------------------------------------------

        section_title(
            "Filtered Demand Summary"
        )

        summary = (
            filtered
            .groupby(
                "hour_of_day",
                as_index=False
            )
            .agg(
                avg_trips=(
                    "taxi_trip_count",
                    "mean"
                ),
                total_trips=(
                    "taxi_trip_count",
                    "sum"
                ),
                observations=(
                    "taxi_trip_count",
                    "size"
                ),
            )
            .sort_values(
                "hour_of_day"
            )
        )

        summary["avg_trips"] = (
            summary["avg_trips"]
            .round(0)
        )

        st.dataframe(
            summary,
            use_container_width=True,
            hide_index=True,
        )

# =============================================================================
# GEOGRAPHIC PERFORMANCE
# =============================================================================

elif page == 'Geographic Performance':
    df = load_geography().copy()

    if 'zone' not in df.columns:
        if 'zone_y' in df.columns:
            df['zone'] = df['zone_y']
        elif 'zone_x' in df.columns:
            df['zone'] = df['zone_x']

    page_header(
        'GEOGRAPHY',
        'Geographic Performance',
        'Where is observed taxi activity and revenue concentrated across NYC taxi zones?'
    )

    # ---------------------------------------------------------
    # Geographic filters
    # ---------------------------------------------------------
    filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 1])

    with filter_col1:
        borough_options = ['All'] + sorted(
            df['borough'].dropna().unique().tolist()
        ) if 'borough' in df.columns else ['All']

        selected_borough = st.selectbox(
            'Borough',
            borough_options,
            key='geo_borough_filter',
        )

    with filter_col2:
        service_zone_options = ['All'] + sorted(
            df['service_zone'].dropna().unique().tolist()
        ) if 'service_zone' in df.columns else ['All']

        selected_service_zone = st.selectbox(
            'Service Zone',
            service_zone_options,
            key='geo_service_zone_filter',
        )

    with filter_col3:
        top_n = st.slider(
            'Top zones',
            min_value=5,
            max_value=30,
            value=15,
            key='geo_top_n',
        )

    # ---------------------------------------------------------
    # Apply filters
    # ---------------------------------------------------------
    filtered_geo = df.copy()

    if selected_borough != 'All' and 'borough' in filtered_geo.columns:
        filtered_geo = filtered_geo[
            filtered_geo['borough'] == selected_borough
        ]

    if selected_service_zone != 'All' and 'service_zone' in filtered_geo.columns:
        filtered_geo = filtered_geo[
            filtered_geo['service_zone'] == selected_service_zone
        ]

    if filtered_geo.empty:
        st.warning(
            'No geographic zones match the selected filters. '
            'Choose a broader borough or service-zone selection.'
        )
    else:

        # ---------------------------------------------------------
        # Map metric
        # ---------------------------------------------------------
        c1, c2 = st.columns([1.55, 1])

        with c1:
            st.markdown(
                """
                <div style="
                    font-size:0.78rem;
                    font-weight:800;
                    letter-spacing:0.10em;
                    text-transform:uppercase;
                    color:#526078;
                    margin-bottom:0.25rem;
                ">
                    Map Metric
                </div>
                """,
                unsafe_allow_html=True,
            )

            map_metric = st.radio(
                'Select geographic measure',
                [
                    'Trip Activity',
                    'Revenue',
                    'Revenue per Activity',
                    'Low-Activity Zones',
                ],
                horizontal=True,
                label_visibility='collapsed',
                key='geographic_map_metric',
            )

        # ---------------------------------------------------------
        # KPI calculations on filtered geography
        # ---------------------------------------------------------
        top_activity_zone = filtered_geo.loc[
            filtered_geo['total_zone_activity'].idxmax()
        ]

        top_revenue_zone = filtered_geo.loc[
            filtered_geo['total_zone_revenue'].idxmax()
        ]

        top_10_activity_share = (
            filtered_geo
            .nlargest(
                min(10, len(filtered_geo)),
                'total_zone_activity'
            )['zone_activity_contribution_pct']
            .sum()
        )

        low_activity_count = (
            filtered_geo[
                filtered_geo['below_median_activity_indicator']
            ].shape[0]
        )

        cols = st.columns(4)

        with cols[0]:
            kpi_card(
                'Top activity zone',
                top_activity_zone['zone'],
                f"{top_activity_zone['total_zone_activity']:,.0f} activity"
            )

        with cols[1]:
            kpi_card(
                'Top revenue zone',
                top_revenue_zone['zone'],
                f"{format_currency(top_revenue_zone['total_zone_revenue'])} observed"
            )

        with cols[2]:
            kpi_card(
                'Top 10 activity share',
                f'{top_10_activity_share:.1f}%',
                'Observed zone activity'
            )

        with cols[3]:
            kpi_card(
                'Low-activity screening',
                format_number(low_activity_count),
                'Below-median zones'
            )

        key_finding(
            f"The top observed activity zone in the selected geography is "
            f"{top_activity_zone['zone']}, while "
            f"{top_revenue_zone['zone']} ranks first by revenue. "
            f"Low-activity zones are screening indicators, not proof of inadequate taxi supply."
        )

        # ---------------------------------------------------------
        # Map
        # ---------------------------------------------------------
        section_title({
            'Trip Activity': 'Where Taxi Activity Is Concentrated',
            'Revenue': 'Where Taxi Revenue Is Concentrated',
            'Revenue per Activity': 'Where Activity Generates More Revenue',
            'Low-Activity Zones': 'Where Observed Activity Is Low',
        }[map_metric])

        st.plotly_chart(
            create_zone_map(
                filtered_geo,
                map_metric,
            ),
            use_container_width=True,
        )

        st.caption(
            'Darker polygons indicate higher values for the selected metric. '
            'Hover a zone to inspect observed activity, revenue and ranking. '
            'Revenue per activity is descriptive, not profitability. '
            'Low-activity zones are screening indicators, not proof of inadequate supply.'
        )

        # ---------------------------------------------------------
        # Top zones table
        # ---------------------------------------------------------
        section_title('Top Zones')

        top_df = filtered_geo.nlargest(
            top_n,
            'total_zone_activity'
        )[[
            'location_id',
            'zone',
            'service_zone',
            'total_zone_activity',
            'total_zone_revenue',
            'revenue_per_zone_activity',
            'zone_activity_contribution_pct',
            'zone_revenue_contribution_pct',
            'activity_rank',
            'revenue_rank',
            'activity_segment',
        ]]

        st.dataframe(
            top_df,
            use_container_width=True,
            hide_index=True,
        )

        # ---------------------------------------------------------
        # Low activity table
        # ---------------------------------------------------------
        section_title('Low-Activity Zone Screening')

        low_df = filtered_geo[
            filtered_geo['below_median_activity_indicator']
        ].sort_values(
            'total_zone_activity'
        )[[
            'location_id',
            'zone',
            'service_zone',
            'total_zone_activity',
            'total_zone_revenue',
            'zone_activity_contribution_pct',
            'zone_revenue_contribution_pct',
            'activity_segment',
        ]]

        st.dataframe(
            low_df,
            use_container_width=True,
            hide_index=True,
        )

# =============================================================================
# FARES & PAYMENTS
# =============================================================================

elif page == 'Fares & Payments':
    df = load_fares().copy()

    page_header(
        'ECONOMICS',
        'Fares & Payments',
        'How does observed market revenue vary across payment methods?'
    )

    # ---------------------------------------------------------
    # Payment filter
    # ---------------------------------------------------------
    payment_options = ['All'] + sorted(
        df['payment_type_label']
        .dropna()
        .unique()
        .tolist()
    )

    selected_payment = st.selectbox(
        'Payment Type',
        payment_options,
        key='payment_type_filter',
    )

    filtered = df.copy()

    if selected_payment != 'All':
        filtered = filtered[
            filtered['payment_type_label'] == selected_payment
        ]

    # ---------------------------------------------------------
    # Duplicate canonical-label guard
    # ---------------------------------------------------------
    duplicate_labels = (
        filtered['payment_type_label']
        .duplicated(keep=False)
        .any()
    )

    if duplicate_labels:
        st.error(
            'Payment mart contains duplicate canonical payment labels. '
            'Review the mart before deployment.'
        )

    if filtered.empty:
        st.warning('No payment records match the selected filter.')

    else:
        top_payment = filtered.sort_values(
            'amount_share_pct',
            ascending=False
        ).iloc[0]

        key_finding(
            f"{top_payment['payment_type_label']} represents "
            f"{top_payment['amount_share_pct']:.1f}% of observed NYC taxi "
            f"market revenue in the selected payment view. "
            f"Payment mix is descriptive and should not be interpreted "
            f"as a causal payment effect."
        )

        section_title('Revenue by Payment Type')

        st.plotly_chart(
            style_figure(
                payment_revenue_chart(filtered),
                450,
            ),
            use_container_width=True,
        )

        section_title('Payment Performance')

        display_columns = [
            'payment_type_label',
            'trips',
            'passengers',
            'avg_fare',
            'median_fare',
            'avg_speed_mph',
            'tipping_rate_pct',
            'avg_tip_percentage',
            'trip_share_pct',
            'amount_share_pct',
        ]

        available_columns = [
            c for c in display_columns
            if c in filtered.columns
        ]

        st.dataframe(
            filtered[available_columns],
            use_container_width=True,
            hide_index=True,
        )

# =============================================================================
# WEATHER & TRANSIT
# =============================================================================

elif page == 'Weather & Transit':
    df = load_weather().copy()

    df['calendar_date'] = pd.to_datetime(
        df['calendar_date']
    )

    page_header(
        'CONTEXT',
        'Weather & Transit',
        'Observed taxi outcomes under weather and aggregate transit conditions.'
    )

    # ---------------------------------------------------------
    # Filters
    # ---------------------------------------------------------
    f1, f2 = st.columns([1.2, 1])

    with f1:
        min_date = df['calendar_date'].min().date()
        max_date = df['calendar_date'].max().date()

        weather_date_range = st.date_input(
            'Assessment window',
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key='weather_date_range',
        )

    with f2:
        precipitation_options = ['All'] + sorted(
            df['precipitation_category']
            .dropna()
            .unique()
            .tolist()
        )

        selected_precipitation = st.selectbox(
            'Precipitation category',
            precipitation_options,
            key='precipitation_filter',
        )

    filtered = df.copy()

    if len(weather_date_range) == 2:
        start_date, end_date = weather_date_range

        filtered = filtered[
            (filtered['calendar_date'] >= pd.Timestamp(start_date))
            &
            (
                filtered['calendar_date']
                < pd.Timestamp(end_date) + pd.Timedelta(days=1)
            )
        ]

    if selected_precipitation != 'All':
        filtered = filtered[
            filtered['precipitation_category']
            == selected_precipitation
        ]

    if filtered.empty:
        st.warning(
            'No weather observations match the selected filters.'
        )
    else:

        # ---------------------------------------------------------
        # Evidence base
        # ---------------------------------------------------------
        if 'hours' in filtered.columns:
            evidence = (
                filtered[
                    ['precipitation_category', 'hours']
                ]
                .drop_duplicates()
                .sort_values('hours', ascending=False)
            )
        else:
            evidence = (
                filtered
                .groupby(
                    'precipitation_category',
                    as_index=False
                )
                .size()
                .rename(columns={'size': 'hours'})
            )

        if not evidence.empty:

            evidence_map = dict(
                zip(
                    evidence['precipitation_category'],
                    evidence['hours'],
                )
            )

            light = evidence_map.get('Light Rain')
            dry = evidence_map.get('Dry')
            heavy = evidence_map.get('Heavy Rain')

            caveat = (
                f"Heavy Rain is based on only {int(heavy)} hours"
                if heavy is not None
                else
                'Severe-weather categories have limited observations'
            )

            if light is not None and dry is not None:

                light_rows = filtered[
                    filtered['precipitation_category']
                    == 'Light Rain'
                ]

                dry_rows = filtered[
                    filtered['precipitation_category']
                    == 'Dry'
                ]

                if (
                    not light_rows.empty
                    and not dry_rows.empty
                    and 'category_avg_taxi_trips' in filtered.columns
                ):

                    light_trips = light_rows[
                        'category_avg_taxi_trips'
                    ].iloc[0]

                    dry_trips = dry_rows[
                        'category_avg_taxi_trips'
                    ].iloc[0]

                    if dry_trips not in (None, 0):

                        diff = (
                            light_trips / dry_trips - 1
                        ) * 100

                        key_finding(
                            f"Light-rain hours averaged "
                            f"{diff:.1f}% "
                            f"{'more' if diff >= 0 else 'fewer'} "
                            f"taxi trips than dry hours. "
                            f"{caveat}; severe-weather results "
                            f"should not be over-interpreted."
                        )

            else:
                key_finding(
                    f"Weather categories show different observed "
                    f"taxi outcomes, but {caveat}; treat small-sample "
                    f"categories as directional evidence only."
                )

        # ---------------------------------------------------------
        # Chart
        # ---------------------------------------------------------
        section_title(
            'Average Taxi Demand by Precipitation'
        )

        st.plotly_chart(
            style_figure(
                weather_demand_chart(filtered),
                450,
            ),
            use_container_width=True,
        )

        # ---------------------------------------------------------
        # Evidence base
        # ---------------------------------------------------------
        section_title('Weather Evidence Base')

        ev_cols = (
            st.columns(min(4, len(evidence)))
            if len(evidence)
            else []
        )

        for i, (_, r) in enumerate(evidence.iterrows()):
            with ev_cols[i % len(ev_cols)]:
                kpi_card(
                    r['precipitation_category'],
                    f"n = {int(r['hours']):,}",
                    'Canonical weather hours',
                )

        # ---------------------------------------------------------
        # Outcome table
        # ---------------------------------------------------------
        section_title('Weather / Transit Outcomes')

        display_columns = [
            'precipitation_category',
            'hours',
            'category_avg_taxi_trips',
            'category_avg_taxi_revenue',
            'category_avg_distance_per_trip',
            'category_avg_duration_per_trip',
            'category_avg_amount_per_trip',
            'category_avg_subway_ridership',
            'category_avg_subway_transfers',
        ]

        available_columns = [
            c for c in display_columns
            if c in filtered.columns
        ]

        st.dataframe(
            filtered[available_columns].drop_duplicates(),
            use_container_width=True,
            hide_index=True,
        )

# =============================================================================
# DATA QUALITY & ANOMALIES
# =============================================================================

elif page == 'Data Quality & Anomalies':
    df = load_quality().copy()
    page_header('QUALITY CONTROL', 'Data Quality & Anomalies', 'Rule-level quality flags and their potential analytical impact.')

    issue_flags = df['affected_rows'].sum()
    flagged_revenue = df['affected_revenue'].sum()

    cols = st.columns(3)
    with cols[0]: kpi_card('Quality issues', format_number(len(df)), 'Configured quality rules')
    with cols[1]: kpi_card('Issue flags', format_number(issue_flags), 'Rule-level flags; populations may overlap')
    with cols[2]: kpi_card('Issue-flagged revenue', format_currency(flagged_revenue), 'Rule-level flagged revenue')

    key_finding('Issue Flags are rule-level counts. The same trip can trigger multiple quality rules, so these values must not be interpreted as unique affected trips or unique affected revenue.')

    section_title('Quality Rules')
    st.dataframe(
        df[[
            'issue_id','issue_name','issue_category','affected_rows','affected_pct',
            'affected_revenue','rule','kpi_impact','severity','treatment'
        ]],
        use_container_width=True,
        hide_index=True,
    )