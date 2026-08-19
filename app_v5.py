import os
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
from live_optionchain_data import (
    update_option_chain,
    get_available_expiries
)

from data_store import save_snapshot
from streamlit_autorefresh import st_autorefresh
from market_structure import calculate_market_structure
from datetime import datetime
from market_structure import calculate_market_structure
from strategy_ui import render_strategy_tab

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NIFTY Master Screener",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ---------- GLOBAL ---------- */

    .stApp {
        background: #0b0e13;
        color: #f5f7fa;
    }

    .main .block-container {
        max-width: 1500px;
        padding-top: 18px;
        padding-left: 24px;
        padding-right: 24px;
        padding-bottom: 10px;
    }

    header[data-testid="stHeader"] {
        background: #0b0e13;
    }

    /* ---------- TOP HEADER ---------- */

    .top-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 4px 14px 4px;
        border-bottom: 1px solid #272b33;
        margin-bottom: 8px;
    }

    .brand {
        font-size: 25px;
        font-weight: 800;
        letter-spacing: -0.5px;
    }

    .status {
        color: #00e59a;
        font-weight: 700;
        font-size: 14px;
    }

    .status-detail {
        color: #7f8795;
        font-size: 13px;
        margin-left: 10px;
    }

    /* ---------- METRIC CARDS ---------- */

    .metric-card {
        background: #11151c;
        border: 1px solid #292e38;
        border-radius: 10px;
        padding: 13px 16px;
        min-height: 84px;
    }

    .metric-label {
        color: #8f98a8;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }

    .metric-value {
        color: #f4f6f8;
        font-size: 25px;
        font-weight: 750;
        margin-top: 4px;
    }

    .metric-sub {
        color: #7f8795;
        font-size: 11px;
        margin-top: 2px;
    }

    /* ---------- LEVEL CARDS ---------- */

    .level-card {
        background: #11151c;
        border: 1px solid #292e38;
        border-radius: 10px;
        padding: 11px 14px;
        height: 78px;
    }

    .level-title {
        color: #8f98a8;
        font-size: 11px;
        text-transform: uppercase;
    }

    .level-value {
        font-size: 21px;
        font-weight: 750;
        margin-top: 5px;
    }

    .resistance {
        color: #ff5c67;
    }

    .support {
        color: #00e59a;
    }

    /* ---------- SECTION TITLE ---------- */

    .section-title {
        font-size: 21px;
        font-weight: 750;
        margin-top: 8px;
        margin-bottom: 8px;
    }

    .small-title {
        font-size: 15px;
        font-weight: 700;
        margin-bottom: 6px;
    }

    /* ---------- SIGNAL ---------- */

    .signal-card {
        background: #11151c;
        border: 1px solid #292e38;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }

    .signal-label {
        color: #8f98a8;
        font-size: 12px;
    }

    .signal-value {
        font-size: 24px;
        font-weight: 800;
        margin-top: 4px;
    }

    .bullish {
        color: #00e59a;
    }

    .bearish {
        color: #ff5c67;
    }

    .neutral {
        color: #f1c75b;
    }

    /* ---------- DATA QUALITY ---------- */

    .data-ready {
        color: #00e59a;
        font-weight: 700;
    }

    .data-warning {
        color: #f1c75b;
        font-weight: 700;
    }

    /* ---------- TABLE ---------- */

    div[data-testid="stDataFrame"] {
        border: 1px solid #292e38;
        border-radius: 8px;
    }

    /* ---------- BUTTON ---------- */

    .stButton button {
        border-radius: 8px;
        border: 1px solid #383e49;
        background: #171b23;
        color: #f5f7fa;
    }

    .stButton button:hover {
        border-color: #ff4654;
        color: #ffffff;
    }

    /* ---------- SELECTBOX ---------- */

    div[data-baseweb="select"] > div {
        background: #151921;
        border-color: #303641;
    }

    /* ---------- TABS ---------- */

    button[data-baseweb="tab"] {
        font-weight: 650;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #ff4654;
    }

    /* ---------- REMOVE EXCESSIVE GAP ---------- */

    div.block-container > div {
        gap: 0.7rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# FILE PATH
# ============================================================

CSV_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "nifty_option_chain.csv"
)
# ============================================================
# DATA LOADER
# ============================================================

@st.cache_data(ttl=30)
def load_data(path):

    if not os.path.exists(path):
        return pd.DataFrame()

    df = pd.read_csv(path)

    # Remove accidental unnamed columns
    df = df.loc[
        :,
        ~df.columns.astype(str).str.startswith("Unnamed")
    ]

    # Convert important numeric columns
    numeric_columns = [
        "strike",
        "spot_price",

        "ce_ltp",
        "ce_volume",
        "ce_oi",
        "ce_prev_oi",
        "ce_oi_change",
        "ce_iv",

        "pe_ltp",
        "pe_volume",
        "pe_oi",
        "pe_prev_oi",
        "pe_oi_change",
        "pe_iv",

        "ce_delta",
        "ce_gamma",
        "ce_theta",
        "ce_vega",

        "pe_delta",
        "pe_gamma",
        "pe_theta",
        "pe_vega"
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    if "strike" in df.columns:
        df = df.sort_values("strike")

    df = df.reset_index(drop=True)
    return df
# ============================================================
# SAFE NUMERIC HELPERS
# ============================================================

def safe_number(value, default=0):

    try:
        if pd.isna(value):
            return default

        return float(value)

    except Exception:
        return default


def safe_sum_column(df, column):

    """
    IMPORTANT:
    This function receives a COLUMN NAME as a string.

    It fixes the previous error:

        TypeError: unhashable type: 'Series'

    Previous code effectively did:

        safe_sum(df["ce_oi"])

    and then checked:

        if series not in df.columns

    A pandas Series cannot be used like that.

    Now we pass:

        safe_sum_column(df, "ce_oi")
    """

    if column not in df.columns:
        return 0

    return pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0).sum()


def format_number(value):

    if value is None or pd.isna(value):
        return "-"

    value = float(value)

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"

    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"

    return f"{value:,.0f}"


def format_price(value):

    if value is None or pd.isna(value):
        return "-"

    return f"{float(value):,.2f}"


def format_integer(value):

    if value is None or pd.isna(value):
        return "-"

    return f"{float(value):,.0f}"


# ============================================================
# CALCULATIONS
# ============================================================

def calculate_metrics(df):

    if df.empty:
        return {}

    spot = safe_number(
        df["spot_price"].dropna().iloc[0]
        if "spot_price" in df.columns
        and not df["spot_price"].dropna().empty
        else 0
    )

    strikes = sorted(
        df["strike"].dropna().unique()
    )

    if not strikes:
        return {}

    # --------------------------------------------------------
    # ATM
    # --------------------------------------------------------

    atm = min(
        strikes,
        key=lambda x: abs(x - spot)
    )

    # --------------------------------------------------------
    # ATM RANGE
    # --------------------------------------------------------

    atm_index = strikes.index(atm)

    lower = max(0, atm_index - 10)
    upper = min(len(strikes), atm_index + 11)

    atm_range_strikes = strikes[lower:upper]

    atm_df = df[
        df["strike"].isin(atm_range_strikes)
    ].copy()

    # --------------------------------------------------------
    # TOTAL OI
    # --------------------------------------------------------

    total_ce_oi = safe_sum_column(
        df,
        "ce_oi"
    )

    total_pe_oi = safe_sum_column(
        df,
        "pe_oi"
    )

    overall_pcr = (
        total_pe_oi / total_ce_oi
        if total_ce_oi != 0
        else np.nan
    )

    # --------------------------------------------------------
    # ATM PCR
    # --------------------------------------------------------

    atm_ce_oi = safe_sum_column(
        atm_df,
        "ce_oi"
    )

    atm_pe_oi = safe_sum_column(
        atm_df,
        "pe_oi"
    )

    atm_pcr = (
        atm_pe_oi / atm_ce_oi
        if atm_ce_oi != 0
        else np.nan
    )

    # --------------------------------------------------------
    # MAX CE OI
    # --------------------------------------------------------

    max_ce_oi = None
    max_ce_oi_strike = None

    if "ce_oi" in df.columns:

        temp = df.dropna(
            subset=["ce_oi"]
        )

        if not temp.empty:

            row = temp.loc[
                temp["ce_oi"].idxmax()
            ]

            max_ce_oi = row["ce_oi"]
            max_ce_oi_strike = row["strike"]

    # --------------------------------------------------------
    # MAX PE OI
    # --------------------------------------------------------

    max_pe_oi = None
    max_pe_oi_strike = None

    if "pe_oi" in df.columns:

        temp = df.dropna(
            subset=["pe_oi"]
        )

        if not temp.empty:

            row = temp.loc[
                temp["pe_oi"].idxmax()
            ]

            max_pe_oi = row["pe_oi"]
            max_pe_oi_strike = row["strike"]

    # --------------------------------------------------------
    # MAX CE ΔOI
    # --------------------------------------------------------

    max_ce_change = None
    max_ce_change_strike = None

    if "ce_oi_change" in df.columns:

        temp = df.dropna(
            subset=["ce_oi_change"]
        )

        if not temp.empty:

            row = temp.loc[
                temp["ce_oi_change"].idxmax()
            ]

            max_ce_change = row["ce_oi_change"]
            max_ce_change_strike = row["strike"]

    # --------------------------------------------------------
    # MAX PE ΔOI
    # --------------------------------------------------------

    max_pe_change = None
    max_pe_change_strike = None

    if "pe_oi_change" in df.columns:

        temp = df.dropna(
            subset=["pe_oi_change"]
        )

        if not temp.empty:

            row = temp.loc[
                temp["pe_oi_change"].idxmax()
            ]

            max_pe_change = row["pe_oi_change"]
            max_pe_change_strike = row["strike"]

    # --------------------------------------------------------
    # SUPPORT / RESISTANCE
    # --------------------------------------------------------

    resistance = max_ce_oi_strike
    support = max_pe_oi_strike

    # --------------------------------------------------------
    # PCR BIAS
    # --------------------------------------------------------

    if pd.isna(overall_pcr):

        pcr_bias = "NEUTRAL"

    elif overall_pcr >= 1.15:

        pcr_bias = "BULLISH"

    elif overall_pcr <= 0.85:

        pcr_bias = "BEARISH"

    else:

        pcr_bias = "NEUTRAL"

    # --------------------------------------------------------
    # OI CHANGE SCORE
    # --------------------------------------------------------

    total_ce_change = safe_sum_column(
        df,
        "ce_oi_change"
    )

    total_pe_change = safe_sum_column(
        df,
        "pe_oi_change"
    )

    oi_score = 0

    if total_pe_change > total_ce_change:
        oi_score += 1

    elif total_ce_change > total_pe_change:
        oi_score -= 1

    # --------------------------------------------------------
    # FINAL SIGNAL SCORE
    # --------------------------------------------------------

    score = 0

    # PCR
    if not pd.isna(overall_pcr):

        if overall_pcr >= 1.15:
            score += 1

        elif overall_pcr <= 0.85:
            score -= 1

    # OI change
    score += oi_score

    if score >= 2:

        market_bias = "BULLISH"

    elif score <= -2:

        market_bias = "BEARISH"

    else:

        market_bias = "NEUTRAL"

    # --------------------------------------------------------
    # IV DATA QUALITY
    # --------------------------------------------------------

    ce_iv_valid = 0
    pe_iv_valid = 0

    if "ce_iv" in df.columns:

        ce_iv_valid = int(
            (
                pd.to_numeric(
                    df["ce_iv"],
                    errors="coerce"
                ) > 0
            ).sum()
        )

    if "pe_iv" in df.columns:

        pe_iv_valid = int(
            (
                pd.to_numeric(
                    df["pe_iv"],
                    errors="coerce"
                ) > 0
            ).sum()
        )

    return {
        "spot": spot,
        "atm": atm,
        "strikes": strikes,
        "atm_df": atm_df,

        "total_ce_oi": total_ce_oi,
        "total_pe_oi": total_pe_oi,

        "overall_pcr": overall_pcr,
        "atm_pcr": atm_pcr,

        "max_ce_oi": max_ce_oi,
        "max_ce_oi_strike": max_ce_oi_strike,

        "max_pe_oi": max_pe_oi,
        "max_pe_oi_strike": max_pe_oi_strike,

        "max_ce_change": max_ce_change,
        "max_ce_change_strike": max_ce_change_strike,

        "max_pe_change": max_pe_change,
        "max_pe_change_strike": max_pe_change_strike,

        "support": support,
        "resistance": resistance,

        "total_ce_change": total_ce_change,
        "total_pe_change": total_pe_change,

        "oi_score": oi_score,
        "score": score,

        "pcr_bias": pcr_bias,
        "market_bias": market_bias,

        "ce_iv_valid": ce_iv_valid,
        "pe_iv_valid": pe_iv_valid
    }


# ============================================================
# CHART HELPERS
# ============================================================

def prepare_chart_data(df, atm, range_count=10):

    if df.empty:
        return df

    strikes = sorted(
        df["strike"].dropna().unique()
    )

    if not strikes:
        return df

    atm_index = min(
        range(len(strikes)),
        key=lambda i: abs(strikes[i] - atm)
    )

    lower = max(
        0,
        atm_index - range_count
    )

    upper = min(
        len(strikes),
        atm_index + range_count + 1
    )

    selected = strikes[lower:upper]

    return df[
        df["strike"].isin(selected)
    ].copy()


def oi_chart(df, atm):

    data = prepare_chart_data(
        df,
        atm,
        10
    )

    if data.empty:
        return None

    chart_df = data[
        ["strike", "ce_oi", "pe_oi"]
    ].copy()

    chart_df = chart_df.melt(
        id_vars=["strike"],
        value_vars=["ce_oi", "pe_oi"],
        var_name="Type",
        value_name="OI"
    )

    chart_df["Type"] = chart_df["Type"].map(
        {
            "ce_oi": "CE OI",
            "pe_oi": "PE OI"
        }
    )

    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "strike:O",
                title="Strike"
            ),
            y=alt.Y(
                "OI:Q",
                title="OI"
            ),
            color=alt.Color(
                "Type:N",
                scale=alt.Scale(
                    domain=[
                        "CE OI",
                        "PE OI"
                    ],
                    range=[
                        "#ff4654",
                        "#00d995"
                    ]
                )
            ),
            tooltip=[
                "strike",
                "Type",
                alt.Tooltip(
                    "OI:Q",
                    format=","
                )
            ]
        )
        .properties(
            height=250
        )
    )

    return chart


def change_chart(df, atm):

    data = prepare_chart_data(
        df,
        atm,
        10
    )

    if data.empty:
        return None

    chart_df = data[
        [
            "strike",
            "ce_oi_change",
            "pe_oi_change"
        ]
    ].copy()

    chart_df = chart_df.melt(
        id_vars=["strike"],
        value_vars=[
            "ce_oi_change",
            "pe_oi_change"
        ],
        var_name="Type",
        value_name="Change"
    )

    chart_df["Type"] = chart_df["Type"].map(
        {
            "ce_oi_change": "CE ΔOI",
            "pe_oi_change": "PE ΔOI"
        }
    )

    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "strike:O",
                title="Strike"
            ),
            y=alt.Y(
                "Change:Q",
                title="ΔOI"
            ),
            color=alt.Color(
                "Type:N",
                scale=alt.Scale(
                    domain=[
                        "CE ΔOI",
                        "PE ΔOI"
                    ],
                    range=[
                        "#ff4654",
                        "#00d995"
                    ]
                )
            ),
            tooltip=[
                "strike",
                "Type",
                alt.Tooltip(
                    "Change:Q",
                    format=","
                )
            ]
        )
        .properties(
            height=250
        )
    )

    return chart


def volume_chart(df, atm):

    data = prepare_chart_data(
        df,
        atm,
        10
    )

    chart_df = data[
        [
            "strike",
            "ce_volume",
            "pe_volume"
        ]
    ].copy()

    chart_df = chart_df.melt(
        id_vars=["strike"],
        value_vars=[
            "ce_volume",
            "pe_volume"
        ],
        var_name="Type",
        value_name="Volume"
    )

    chart_df["Type"] = chart_df["Type"].map(
        {
            "ce_volume": "CE Volume",
            "pe_volume": "PE Volume"
        }
    )

    return (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "strike:O",
                title="Strike"
            ),
            y=alt.Y(
                "Volume:Q",
                title="Volume"
            ),
            color=alt.Color(
                "Type:N",
                scale=alt.Scale(
                    domain=[
                        "CE Volume",
                        "PE Volume"
                    ],
                    range=[
                        "#ff4654",
                        "#00d995"
                    ]
                )
            ),
            tooltip=[
                "strike",
                "Type",
                alt.Tooltip(
                    "Volume:Q",
                    format=","
                )
            ]
        )
        .properties(
            height=320
        )
    )


def iv_chart(df, atm):

    data = prepare_chart_data(
        df,
        atm,
        10
    )

    chart_df = data[
        ["strike", "ce_iv", "pe_iv"]
    ].copy()

    # Treat zero IV as missing
    chart_df["ce_iv"] = chart_df["ce_iv"].replace(
        0,
        np.nan
    )

    chart_df["pe_iv"] = chart_df["pe_iv"].replace(
        0,
        np.nan
    )

    chart_df = chart_df.melt(
        id_vars=["strike"],
        value_vars=[
            "ce_iv",
            "pe_iv"
        ],
        var_name="Type",
        value_name="IV"
    )

    chart_df["Type"] = chart_df["Type"].map(
        {
            "ce_iv": "CE IV",
            "pe_iv": "PE IV"
        }
    )

    chart_df = chart_df.dropna(
        subset=["IV"]
    )

    if chart_df.empty:
        return None

    return (
        alt.Chart(chart_df)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "strike:O",
                title="Strike"
            ),
            y=alt.Y(
                "IV:Q",
                title="IV"
            ),
            color=alt.Color(
                "Type:N",
                scale=alt.Scale(
                    domain=[
                        "CE IV",
                        "PE IV"
                    ],
                    range=[
                        "#ff4654",
                        "#00d995"
                    ]
                )
            ),
            tooltip=[
                "strike",
                "Type",
                alt.Tooltip(
                    "IV:Q",
                    format=".2f"
                )
            ]
        )
        .properties(
            height=320
        )
    )


# ============================================================
# OPTION CHAIN TABLE
# ============================================================

def make_option_table(df, atm, range_count):

    data = prepare_chart_data(
        df,
        atm,
        range_count
    )

    columns = [
        "ce_oi",
        "ce_oi_change",
        "ce_volume",
        "ce_iv",
        "ce_ltp",
        "strike",
        "pe_ltp",
        "pe_iv",
        "pe_volume",
        "pe_oi_change",
        "pe_oi"
    ]

    columns = [
        c for c in columns
        if c in data.columns
    ]

    table = data[columns].copy()

    rename = {
        "ce_oi": "CE OI",
        "ce_oi_change": "CE ΔOI",
        "ce_volume": "CE Volume",
        "ce_iv": "CE IV",
        "ce_ltp": "CE LTP",

        "strike": "STRIKE",

        "pe_ltp": "PE LTP",
        "pe_iv": "PE IV",
        "pe_volume": "PE Volume",
        "pe_oi_change": "PE ΔOI",
        "pe_oi": "PE OI"
    }

    table = table.rename(
        columns=rename
    )

    return table


def style_option_table(table, atm):

    def highlight_atm(row):

        styles = [
            ""
            for _ in row
        ]

        if "STRIKE" in row.index:

            try:

                if float(row["STRIKE"]) == float(atm):

                    styles = [
                        "background-color: #202633; font-weight: 700;"
                        for _ in row
                    ]

            except Exception:
                pass

        return styles

    styled = table.style.apply(
        highlight_atm,
        axis=1
    )

    if "CE ΔOI" in table.columns:

        styled = styled.map(
            lambda x:
                "color: #00e59a; font-weight: 700;"
                if pd.notna(x) and x > 0
                else (
                    "color: #ff4654; font-weight: 700;"
                    if pd.notna(x) and x < 0
                    else ""
                ),
            subset=["CE ΔOI"]
        )

    if "PE ΔOI" in table.columns:

        styled = styled.map(
            lambda x:
                "color: #00e59a; font-weight: 700;"
                if pd.notna(x) and x > 0
                else (
                    "color: #ff4654; font-weight: 700;"
                    if pd.notna(x) and x < 0
                    else ""
                ),
            subset=["PE ΔOI"]
        )

    return styled


# ============================================================
# SIGNAL ENGINE
# ============================================================

def get_signal_for_row(row):

    ce_change = safe_number(
        row.get("ce_oi_change"),
        0
    )

    pe_change = safe_number(
        row.get("pe_oi_change"),
        0
    )

    # Basic rule-based interpretation
    if pe_change > 0 and ce_change < 0:
        return "PUT BUILDUP"

    if ce_change > 0 and pe_change < 0:
        return "CALL BUILDUP"

    if pe_change < 0 and ce_change < 0:
        return "UNWINDING"

    if pe_change > 0 and ce_change > 0:
        return "BOTH BUILDUP"

    return "NEUTRAL"


def create_signal_table(df, atm):

    data = prepare_chart_data(
        df,
        atm,
        10
    ).copy()

    data["SIGNAL"] = data.apply(
        get_signal_for_row,
        axis=1
    )

    output = data[
        [
            "strike",
            "ce_oi_change",
            "pe_oi_change",
            "SIGNAL"
        ]
    ].copy()

    output.columns = [
        "STRIKE",
        "CE ΔOI",
        "PE ΔOI",
        "SIGNAL"
    ]

    return output


# ============================================================
# LOAD DATA
# ============================================================

df = load_data(CSV_PATH)
# ============================================================
# MARKET STRUCTURE ENGINE
# ============================================================

market_structure = calculate_market_structure(df)
# ============================================================
# MARKET STRUCTURE HEADER
# ============================================================

st.markdown("### NIFTY 50 MARKET STRUCTURE")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "NIFTY SPOT",
        f"{market_structure['spot']:,.2f}"
    )

with col2:
    st.metric(
        "ATM",
        f"{market_structure['atm_strike']:,.0f}"
    )

with col3:
    st.metric(
        "PCR",
        f"{market_structure['overall_pcr']:.3f}"
    )

with col4:
    st.metric(
        "CE RESISTANCE",
        f"{market_structure['max_ce_oi_strike']:,.0f}"
    )

with col5:
    st.metric(
        "PE SUPPORT",
        f"{market_structure['max_pe_oi_strike']:,.0f}"
    )
    col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "MAX CE ΔOI",
        f"{market_structure['max_ce_change_strike']:,.0f}"
    )

with col2:
    st.metric(
        "MAX PE ΔOI",
        f"{market_structure['max_pe_change_strike']:,.0f}"
    )

with col3:
    st.metric(
        "OI IMBALANCE",
        f"{market_structure['oi_imbalance'] * 100:.2f}%"
    )

with col4:
    st.metric(
        "MARKET BIAS",
        market_structure["bias"]
    )

if df.empty:
    st.error("Option-chain CSV not found.")
    st.info("Make sure this file exists: data/nifty_option_chain.csv")
    st.stop()

metrics = calculate_metrics(df)

if not metrics:
    st.error("Unable to calculate market metrics.")
    st.stop()

spot = metrics["spot"]
atm = metrics["atm"]
last_updated = datetime.now().strftime("%H:%M:%S")


expiry = "-"

if "expiry" in df.columns:

    expiry_values = (
        df["expiry"]
        .dropna()
        .astype(str)
        .unique()
    )

    if len(expiry_values) > 0:
        expiry = expiry_values[0]


# ============================================================
# HEADER
# ============================================================

if df.empty:

    st.error(
        "Option-chain CSV not found."
    )

    st.info(
        "Make sure this file exists: "
        "data/nifty_option_chain.csv"
    )

    st.stop()


metrics = calculate_metrics(df)

if not metrics:

    st.error(
        "Unable to calculate market metrics."
    )

    st.stop()


spot = metrics["spot"]
atm = metrics["atm"]


expiry = "-"

if "expiry" in df.columns:

    expiry_values = (
        df["expiry"]
        .dropna()
        .astype(str)
        .unique()
    )

    if len(expiry_values) > 0:
        expiry = expiry_values[0]


# ============================================================
# HEADER HTML
# ============================================================

header_col1, header_col2 = st.columns([6, 2])

with header_col1:
    st.markdown(
        "<div style='font-size:25px; font-weight:800; letter-spacing:-0.5px; color:#f5f7fa; margin-bottom:6px;'>📊 NIFTY MASTER SCREENER</div>",
        unsafe_allow_html=True
    )

with header_col2:

    st.markdown(
        """
        <div style="
            text-align:right;
            color:#00e59a;
            font-weight:700;
            font-size:14px;
            margin-top:8px;
        ">
            ● LIVE DATA
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div style="
            text-align:right;
            color:#7f8795;
            font-size:13px;
            margin-top:2px;
        ">
            Upstox • {len(df)} strikes
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div style="
            text-align:right;
            color:#7f8795;
            font-size:12px;
            margin-top:2px;
        ">
            Updated: {last_updated}
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# EXPIRY + AUTO REFRESH + MANUAL REFRESH
# ============================================================

@st.cache_data(ttl=300)
def load_expiries():
    return get_available_expiries()


available_expiries = load_expiries()


# ------------------------------------------------------------
# SELECTED EXPIRY
# ------------------------------------------------------------

if "selected_expiry" not in st.session_state:

    st.session_state.selected_expiry = (
        available_expiries[0]
    )


# ------------------------------------------------------------
# AUTO REFRESH OPTIONS
# ------------------------------------------------------------

refresh_options = {
    "OFF": 0,
    "15 sec": 15,
    "30 sec": 30,
    "1 min": 60,
    "5 min": 300
}


# ------------------------------------------------------------
# CONTROL ROW
# ------------------------------------------------------------

refresh_col1, refresh_col2, refresh_col3 = st.columns(
    [5, 3, 1]
)


# ------------------------------------------------------------
# EXPIRY
# ------------------------------------------------------------

with refresh_col1:

    selected_expiry = st.selectbox(
        "EXPIRY",
        available_expiries,
        index=available_expiries.index(
            st.session_state.selected_expiry
        ),
        key="expiry_selector"
    )

    st.session_state.selected_expiry = selected_expiry


# ------------------------------------------------------------
# AUTO REFRESH SELECTOR
# ------------------------------------------------------------

with refresh_col2:

    auto_refresh_label = st.selectbox(
        "AUTO REFRESH",
        list(refresh_options.keys()),
        index=0,
        key="auto_refresh_selector"
    )

    refresh_seconds = refresh_options[
        auto_refresh_label
    ]


# ------------------------------------------------------------
# MANUAL REFRESH BUTTON
# ------------------------------------------------------------

with refresh_col3:

    st.write("")

    if st.button(
        "↻",
        width="stretch"
    ):

        try:

            fresh_df = update_option_chain(
                expiry_date=selected_expiry
            )

            save_snapshot(
                fresh_df
            )

            load_data.clear()

            st.success(
                f"Data refreshed • "
                f"Expiry: {selected_expiry}"
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Refresh failed: {e}"
            )


# ============================================================
# AUTO REFRESH ENGINE
# ============================================================

if refresh_seconds > 0:

    refresh_count = st_autorefresh(
        interval=refresh_seconds * 1000,
        key="nifty_auto_refresh"
    )

    if refresh_count > 0:

        try:

            fresh_df = update_option_chain(
                expiry_date=selected_expiry
            )

            save_snapshot(
                fresh_df
            )

            load_data.clear()

        except Exception as e:

            st.error(
                f"Auto refresh failed: {e}"
            )
            
# ============================================================
# TAB 1 — DASHBOARD
# ============================================================
# ============================================================
# NAVIGATION
# ============================================================

tabs = st.tabs(
    [
        "DASHBOARD",
        "OPTION CHAIN",
        "OI ANALYSIS",
        "VOLUME",
        "IV",
        "PCR",
        "SIGNALS",
        "STRATEGY",
    ]
)
with tabs[0]:

    # --------------------------------------------------------
    # MARKET CARDS
    # --------------------------------------------------------

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            "NIFTY SPOT",
            format_price(spot)
        )

    with c2:
        st.metric(
            "ATM",
            format_integer(atm)
        )

    with c3:
        st.metric(
            "EXPIRY",
            expiry
        )

    with c4:
        st.metric(
            "OVERALL PCR",
            f"{metrics['overall_pcr']:.3f}"
        )

    with c5:
        bias = metrics["market_bias"]
        st.metric(
            "MARKET BIAS",
            bias,
            f"Score: {metrics['score']}"
        )

    st.write("")

    # --------------------------------------------------------
    # LEVELS
    # --------------------------------------------------------

    l1, l2, l3, l4 = st.columns(4)

    with l1:
        st.markdown(
            f"**MAX CE OI**\n\n<span style='color:#ff5c67; font-size:21px; font-weight:750;'>{format_integer(metrics['max_ce_oi_strike'])}</span>",
            unsafe_allow_html=True
        )

    with l2:
        st.markdown(
            f"**MAX PE OI**\n\n<span style='color:#00e59a; font-size:21px; font-weight:750;'>{format_integer(metrics['max_pe_oi_strike'])}</span>",
            unsafe_allow_html=True
        )

    with l3:
        st.markdown(
            f"**MAX CE ΔOI**\n\n<span style='font-size:21px; font-weight:750;'>{format_integer(metrics['max_ce_change_strike'])}</span>",
            unsafe_allow_html=True
        )

    with l4:
        st.markdown(
            f"**MAX PE ΔOI**\n\n<span style='font-size:21px; font-weight:750;'>{format_integer(metrics['max_pe_change_strike'])}</span>",
            unsafe_allow_html=True
        )

    st.write("")

    # --------------------------------------------------------
    # DASHBOARD CHARTS
    # --------------------------------------------------------

    st.markdown("## Market Structure")

    chart1, chart2 = st.columns(2)

    with chart1:

        st.markdown("### OI Distribution — ATM ± 10")

        chart = oi_chart(
            df,
            atm
        )

        if chart:
            st.altair_chart(
                chart,
                width="stretch"
            )

    with chart2:

        st.markdown("### OI Change — ATM ± 10")

        chart = change_chart(
            df,
            atm
        )

        if chart:
            st.altair_chart(
                chart,
                width="stretch"
            )


# ============================================================
# TAB 2 — OPTION CHAIN
# ============================================================

with tabs[1]:

    st.markdown(
        '<div class="section-title">Option Chain</div>',
        unsafe_allow_html=True
    )

    range_choice = st.selectbox(
        "Display",
        [
            "ATM ± 5",
            "ATM ± 10",
            "ATM ± 15",
            "ATM ± 20",
            "ALL"
        ],
        index=1
    )

    if range_choice == "ATM ± 5":
        range_count = 5

    elif range_choice == "ATM ± 10":
        range_count = 10

    elif range_choice == "ATM ± 15":
        range_count = 15

    elif range_choice == "ATM ± 20":
        range_count = 20

    else:
        range_count = len(
            df["strike"].unique()
        )

    option_table = make_option_table(
        df,
        atm,
        range_count
    )

    styled_table = style_option_table(
        option_table,
        atm
    )

    st.dataframe(
        styled_table,
        width="stretch",
        height=570,
        hide_index=False
    )


# ============================================================
# TAB 3 — OI
# ============================================================

with tabs[2]:

    st.markdown(
        '<div class="section-title">OI Analysis</div>',
        unsafe_allow_html=True
    )

    a, b, c, d = st.columns(4)

    with a:
        st.metric(
            "Total CE OI",
            format_number(
                metrics["total_ce_oi"]
            )
        )

    with b:
        st.metric(
            "Total PE OI",
            format_number(
                metrics["total_pe_oi"]
            )
        )

    with c:
        st.metric(
            "MAX CE OI",
            format_integer(
                metrics["max_ce_oi_strike"]
            )
        )

    with d:
        st.metric(
            "MAX PE OI",
            format_integer(
                metrics["max_pe_oi_strike"]
            )
        )

    chart = oi_chart(
        df,
        atm
    )

    if chart:

        st.altair_chart(
            chart,
            width="stretch"
        )

    st.markdown(
        f"""
        <div class="level-card">
            <span class="support">
                SUPPORT: {format_integer(metrics["support"])}
            </span>
            &nbsp;&nbsp;&nbsp;
            <span class="resistance">
                RESISTANCE: {format_integer(metrics["resistance"])}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# TAB 4 — VOLUME
# ============================================================

with tabs[3]:

    st.markdown(
        '<div class="section-title">Volume Analysis</div>',
        unsafe_allow_html=True
    )

    total_ce_volume = safe_sum_column(
        df,
        "ce_volume"
    )

    total_pe_volume = safe_sum_column(
        df,
        "pe_volume"
    )

    a, b = st.columns(2)

    with a:

        st.metric(
            "Total CE Volume",
            format_number(
                total_ce_volume
            )
        )

    with b:

        st.metric(
            "Total PE Volume",
            format_number(
                total_pe_volume
            )
        )

    chart = volume_chart(
        df,
        atm
    )

    if chart:

        st.altair_chart(
            chart,
            width="stretch"
        )


# ============================================================
# TAB 5 — IV
# ============================================================

with tabs[4]:

    st.markdown(
        '<div class="section-title">IV Analysis</div>',
        unsafe_allow_html=True
    )

    # Replace zero with NaN
    iv_df = df.copy()

    if "ce_iv" in iv_df.columns:

        iv_df["ce_iv"] = (
            iv_df["ce_iv"]
            .replace(0, np.nan)
        )

    if "pe_iv" in iv_df.columns:

        iv_df["pe_iv"] = (
            iv_df["pe_iv"]
            .replace(0, np.nan)
        )

    atm_row = iv_df[
        iv_df["strike"] == atm
    ]

    atm_ce_iv = np.nan
    atm_pe_iv = np.nan

    if not atm_row.empty:

        if "ce_iv" in atm_row.columns:

            atm_ce_iv = atm_row[
                "ce_iv"
            ].iloc[0]

        if "pe_iv" in atm_row.columns:

            atm_pe_iv = atm_row[
                "pe_iv"
            ].iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "ATM CE IV",
            "-"
            if pd.isna(atm_ce_iv)
            else f"{atm_ce_iv:.2f}"
        )

    with c2:

        st.metric(
            "ATM PE IV",
            "-"
            if pd.isna(atm_pe_iv)
            else f"{atm_pe_iv:.2f}"
        )

    with c3:

        st.metric(
            "CE IV Valid",
            f'{metrics["ce_iv_valid"]}/{len(df)}'
        )

    with c4:

        st.metric(
            "PE IV Valid",
            f'{metrics["pe_iv_valid"]}/{len(df)}'
        )

    chart = iv_chart(
        iv_df,
        atm
    )

    if chart:

        st.altair_chart(
            chart,
            width="stretch"
        )

    else:

        st.warning(
            "No valid IV values available for the selected strikes."
        )


# ============================================================
# TAB 6 — PCR
# ============================================================

with tabs[5]:

    st.markdown(
        '<div class="section-title">PCR Analysis</div>',
        unsafe_allow_html=True
    )

    p1, p2, p3 = st.columns(3)

    with p1:

        st.metric(
            "Overall PCR",
            f'{metrics["overall_pcr"]:.3f}'
        )

    with p2:

        st.metric(
            "ATM ± 10 PCR",
            f'{metrics["atm_pcr"]:.3f}'
        )

    with p3:

        st.metric(
            "PCR Bias",
            metrics["pcr_bias"]
        )

    # --------------------------------------------------------
    # PCR BY STRIKE
    # --------------------------------------------------------

    pcr_df = prepare_chart_data(
        df,
        atm,
        10
    ).copy()

    pcr_df["PCR"] = np.where(
        pcr_df["ce_oi"] > 0,
        pcr_df["pe_oi"] / pcr_df["ce_oi"],
        np.nan
    )

    pcr_df = pcr_df.dropna(
        subset=["PCR"]
    )

    # Avoid extreme ratios from tiny CE OI
    pcr_df = pcr_df[
        pcr_df["PCR"] <= 5
    ]

    if not pcr_df.empty:

        chart = (
            alt.Chart(pcr_df)
            .mark_line(
                point=True
            )
            .encode(
                x=alt.X(
                    "strike:O",
                    title="Strike"
                ),
                y=alt.Y(
                    "PCR:Q",
                    title="PCR",
                    scale=alt.Scale(
                        domain=[
                            0,
                            max(
                                2,
                                float(
                                    pcr_df["PCR"].max()
                                )
                            )
                        ]
                    )
                ),
                tooltip=[
                    "strike",
                    alt.Tooltip(
                        "PCR:Q",
                        format=".3f"
                    )
                ]
            )
            .properties(
                height=400
            )
        )

        st.altair_chart(
            chart,
            width="stretch"
        )

    st.info(
        "PCR chart is restricted to ATM ± 10 and "
        "extreme ratios above 5 are excluded to avoid "
        "far-OTM distortion."
    )


# ============================================================
# TAB 7 — SIGNALS
# ============================================================

with tabs[6]:

    st.markdown(
        '<div class="section-title">Signal Scanner</div>',
        unsafe_allow_html=True
    )

    bias = str(metrics["market_bias"]).upper()

    signal_class = {
        "BULLISH": "bullish",
        "BEARISH": "bearish",
        "NEUTRAL": "neutral"
    }.get(bias, "neutral")

    s1, s2, s3 = st.columns(3)

    with s1:

        st.markdown(
            """
            <div style="
                background:#11151c;
                border:1px solid #292e38;
                border-radius:10px;
                padding:18px 16px;
                text-align:center;
                min-height:180px;
            ">
                <div style="color:#8f98a8; font-size:12px; letter-spacing:0.6px; text-transform:uppercase; margin-bottom:18px;">
                    PCR BIAS
                </div>
                <div style="color:#00e59a; font-size:32px; font-weight:800; line-height:1.2;">
                    {pcr_value}
                </div>
            </div>
            """.format(pcr_value=metrics["pcr_bias"]),
            unsafe_allow_html=True
        )

    with s2:

        oi_signal = (
            "BULLISH"
            if metrics["oi_score"] > 0
            else (
                "BEARISH"
                if metrics["oi_score"] < 0
                else "NEUTRAL"
            )
        )

        oi_color = {
            "BULLISH": "#00e59a",
            "BEARISH": "#ff5c67",
            "NEUTRAL": "#f1c75b"
        }.get(oi_signal, "#f1c75b")

        st.markdown(
            """
            <div style="
                background:#11151c;
                border:1px solid #292e38;
                border-radius:10px;
                padding:18px 16px;
                text-align:center;
                min-height:180px;
            ">
                <div style="color:#8f98a8; font-size:12px; letter-spacing:0.6px; text-transform:uppercase; margin-bottom:18px;">
                    OI STRUCTURE
                </div>
                <div style="color:{oi_color}; font-size:32px; font-weight:800; line-height:1.2;">
                    {oi_value}
                </div>
            </div>
            """.format(oi_color=oi_color, oi_value=oi_signal),
            unsafe_allow_html=True
        )

    with s3:

        st.markdown(
            """
            <div style="
                background:#11151c;
                border:1px solid #292e38;
                border-radius:10px;
                padding:18px 16px;
                text-align:center;
                min-height:180px;
            ">
                <div style="color:#8f98a8; font-size:12px; letter-spacing:0.6px; text-transform:uppercase; margin-bottom:18px;">
                    FINAL MARKET BIAS
                </div>
                <div style="color:#00e59a; font-size:32px; font-weight:800; line-height:1.2;">
                    {market_value}
                </div>
                <div style="color:#8f98a8; font-size:12px; letter-spacing:0.6px; margin-top:14px;">
                    Score: {score_value}
                </div>
            </div>
            """.format(
                market_value=bias,
                score_value=metrics["score"]
            ),
            unsafe_allow_html=True
        )

    st.write("")

    # --------------------------------------------------------
    # STRIKE SIGNALS
    # --------------------------------------------------------

    signal_table = create_signal_table(
        df,
        atm
    )

    st.dataframe(
        signal_table,
        width="stretch",
        height=430,
        hide_index=True
    )

    st.caption(
        "Signal engine is rule-based and intended "
        "for analytical screening, not guaranteed "
        "trade prediction."
    )
    # ============================================================
# TAB 8 — STRATEGY ANALYSIS
# ============================================================

with tabs[7]:

    render_strategy_tab(
        df=df,
        spot=spot,
        atm=atm,
        expiry=expiry
    )


# ============================================================
# DATA QUALITY FOOTER
# ============================================================

st.divider()

iv_warning = ""

if metrics["pe_iv_valid"] < len(df):

    iv_warning = (
        f" | PE IV valid: "
        f"{metrics['pe_iv_valid']}/{len(df)}"
    )

st.caption(
    f"Data source: Upstox CSV • "
    f"{len(df)} strikes • "
    f"Spot: {format_price(spot)} • "
    f"ATM: {format_integer(atm)}"
    f"{iv_warning}"
)
