import os
from textwrap import dedent
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
from nifty_chart_engine import (
    prepare_chart_data as prepare_nifty_chart_data,
    get_multi_timeframe_signal,
    classify_multi_timeframe_regime,
)
from nifty_price_action import run_price_action_engine
from nifty_pattern_engine import run_pattern_engine

from live_optionchain_data import (
    update_option_chain,
    get_available_expiries
)

from data_store import save_snapshot
from historical_analytics import (
    load_history,
    get_strike_history,
    get_greek_history,
    get_price_history,
    get_oi_history,
    get_oi_buildup_analysis,
    get_atm_strike,
)
from streamlit_autorefresh import st_autorefresh
from market_structure import calculate_market_structure
from datetime import datetime

from strategy_ui import render_strategy_tab
from backtest_ui import render_backtest_page



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
# CUSTOM CSS — INSTITUTIONAL TERMINAL DESIGN SYSTEM
# PHASE 1
# ============================================================
st.markdown(
    """
    <style>

/* =========================================================
   PHASE 1C — DASHBOARD TERMINAL PANELS
   ========================================================= */

.dashboard-panel {
    background: var(--bg-panel);

    border: 1px solid var(--border);

    border-radius: var(--radius-md);

    padding: 11px 12px;

    box-shadow: var(--shadow-panel);

    margin-bottom: 8px;
}

.dashboard-panel-header {
    display: flex;

    align-items: center;
    justify-content: space-between;

    padding-bottom: 7px;

    margin-bottom: 8px;

    border-bottom: 1px solid var(--border-soft);
}

.dashboard-panel-title {
    color: var(--text-primary);

    font-size: 10px;

    font-weight: 900;

    letter-spacing: 0.8px;

    text-transform: uppercase;
}

.dashboard-panel-meta {
    color: var(--text-muted);

    font-size: 8px;

    font-weight: 700;

    letter-spacing: 0.5px;
}


/* ---------------------------------------------------------
   DASHBOARD SNAPSHOT GRID
   --------------------------------------------------------- */

.dashboard-grid {
    display: grid;

    grid-template-columns:
        repeat(5, minmax(0, 1fr));

    gap: 7px;
}

.dashboard-stat {
    background: var(--bg-panel-2);

    border: 1px solid var(--border-soft);

    border-radius: var(--radius-sm);

    padding: 9px 10px;

    min-height: 59px;
}

.dashboard-stat-label {
    color: var(--text-muted);

    font-size: 8px;

    font-weight: 800;

    letter-spacing: 0.7px;

    text-transform: uppercase;
}

.dashboard-stat-value {
    color: var(--text-primary);

    font-size: 17px;

    font-weight: 850;

    margin-top: 5px;

    line-height: 1;
}


/* ---------------------------------------------------------
   MARKET STRUCTURE GRID
   --------------------------------------------------------- */

.structure-grid {
    display: grid;

    grid-template-columns:
        repeat(4, minmax(0, 1fr));

    gap: 7px;
}

.structure-item {
    background: var(--bg-panel-2);

    border:
        1px solid var(--border-soft);

    border-radius: var(--radius-sm);

    padding: 9px 10px;
}

.structure-label {
    color: var(--text-muted);

    font-size: 8px;

    font-weight: 800;

    letter-spacing: 0.65px;

    text-transform: uppercase;
}

.structure-value {
    color: var(--text-primary);

    font-size: 17px;

    font-weight: 850;

    margin-top: 5px;
}


/* ---------------------------------------------------------
   REGIME PANEL
   --------------------------------------------------------- */

.regime-panel {
    background:
        linear-gradient(
            135deg,
            #10161d,
            #0d1218
        );

    border:
        1px solid var(--border);

    border-radius: var(--radius-md);

    padding: 11px 12px;

    box-shadow: var(--shadow-panel);
}

.regime-grid {
    display: grid;

    grid-template-columns:
        1.45fr
        repeat(4, 0.8fr)
        1fr;

    gap: 8px;

    align-items: center;
}

.regime-cell {
    min-height: 38px;
}

.regime-label {
    color: var(--text-muted);

    font-size: 7px;

    font-weight: 800;

    letter-spacing: 0.7px;

    text-transform: uppercase;

    margin-bottom: 5px;
}

.regime-value {
    color: var(--text-primary);

    font-size: 12px;

    font-weight: 900;

    line-height: 1.1;
}

.regime-main {
    font-size: 17px;

    color: var(--green);
}

.regime-score {
    color: var(--green);

    font-size: 16px;

    font-weight: 900;
}

.regime-footer {
    display: flex;

    justify-content: space-between;

    align-items: center;

    margin-top: 8px;

    padding-top: 7px;

    border-top:
        1px solid var(--border-soft);

    color: var(--text-muted);

    font-size: 8px;
}

.regime-footer strong {
    color: var(--text-primary);
}


/* ---------------------------------------------------------
   MOBILE SAFETY
   --------------------------------------------------------- */

@media (max-width: 900px) {

    .dashboard-grid {
        grid-template-columns:
            repeat(2, minmax(0, 1fr));
    }

    .structure-grid {
        grid-template-columns:
            repeat(2, minmax(0, 1fr));
    }

    .regime-grid {
        grid-template-columns:
            repeat(2, minmax(0, 1fr));
    }
}

    /* =========================================================
       01. DESIGN TOKENS
    ========================================================= */

    :root {
        --bg-main: #080b10;
        --bg-panel: #0d1117;
        --bg-panel-2: #10151c;
        --bg-elevated: #141a22;
        --bg-input: #111720;

        --border: #202832;
        --border-soft: #181f28;
        --border-bright: #2b3542;

        --text-primary: #edf2f7;
        --text-secondary: #9aa5b3;
        --text-muted: #687483;
        --text-dim: #4f5a67;

        --green: #00d99a;
        --green-soft: #123d32;

        --red: #ff4d5d;
        --red-soft: #411c23;

        --amber: #f2c45c;
        --amber-soft: #40351a;

        --blue: #5ca8ff;
        --blue-soft: #172d46;

        --radius-sm: 5px;
        --radius-md: 7px;
        --radius-lg: 9px;

        --shadow-panel:
            0 1px 0 rgba(255,255,255,0.025),
            0 8px 24px rgba(0,0,0,0.18);
    }

    /* =========================================================
       02. APPLICATION BACKGROUND
       ========================================================= */

    .stApp {
        background:
            radial-gradient(
                circle at 50% -20%,
                rgba(40,55,75,0.12),
                transparent 45%
            ),
            var(--bg-main);

        color: var(--text-primary);
    }

    html,
    body,
    [class*="css"] {
        font-family:
            Inter,
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;
    }


    /* =========================================================
       03. MAIN CONTAINER
       ========================================================= */

    .main .block-container {
        max-width: 1600px;

        padding-top: 12px;
        padding-left: 18px;
        padding-right: 18px;
        padding-bottom: 14px;
    }

    div.block-container > div {
        gap: 0.55rem;
    }


    /* =========================================================
       04. STREAMLIT HEADER
       ========================================================= */

    header[data-testid="stHeader"] {
        background: var(--bg-main);
        height: 34px;
    }

    header[data-testid="stHeader"] > div {
        background: transparent;
    }


    /* =========================================================
       05. GLOBAL TEXT
       ========================================================= */

    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        letter-spacing: -0.2px;
    }

    p {
        color: var(--text-secondary);
    }

    .stCaption,
    [data-testid="stCaptionContainer"] {
        color: var(--text-muted) !important;
    }


    /* =========================================================
       06. TERMINAL TOP HEADER
       ========================================================= */

    .top-header {
        display: flex;
        align-items: center;
        justify-content: space-between;

        min-height: 44px;

        padding:
            2px 2px 10px 2px;

        margin-bottom: 9px;

        border-bottom:
            1px solid var(--border);
    }

    .brand {
        color: var(--text-primary);

        font-size: 20px;
        font-weight: 800;

        letter-spacing: 0.2px;
        line-height: 1;
    }

    .status {
        color: var(--green);

        font-size: 11px;
        font-weight: 800;

        letter-spacing: 0.8px;
        text-transform: uppercase;
    }

    .status-detail {
        color: var(--text-muted);

        font-size: 10px;

        margin-left: 9px;
    }
    /* =========================================================
   06B. GLOBAL TERMINAL HEADER
   ========================================================= */

.terminal-header {
    display: flex;

    align-items: center;
    justify-content: space-between;

    min-height: 52px;

    padding:
        6px 4px 9px 4px;

    margin-bottom: 7px;

    border-bottom:
        1px solid var(--border);

    background:
        linear-gradient(
            180deg,
            rgba(255,255,255,0.012),
            transparent
        );
}


/* ---------- BRAND ---------- */

.terminal-brand {
    display: flex;

    align-items: center;

    gap: 9px;

    min-width: 245px;
}

.terminal-logo {
    width: 27px;
    height: 27px;

    display: flex;

    align-items: center;
    justify-content: center;

    background: #111a20;

    border:
        1px solid #2a3b43;

    border-radius: 5px;

    color: var(--green);

    font-size: 13px;
    font-weight: 900;

    letter-spacing: 0;
}

.terminal-title {
    color: var(--text-primary);

    font-size: 13px;
    font-weight: 900;

    letter-spacing: 1px;
}

.terminal-subtitle {
    color: var(--text-dim);

    font-size: 7px;
    font-weight: 800;

    letter-spacing: 1px;

    margin-top: 3px;
}


/* ---------- MARKET STRIP ---------- */

.terminal-market-strip {
    display: flex;

    align-items: center;

    gap: 0;

    margin-left: auto;
}

.terminal-market-item {
    min-width: 72px;

    padding:
        0 12px;

    border-left:
        1px solid var(--border);
}

.terminal-market-item.primary {
    min-width: 108px;
}

.terminal-market-label {
    color: var(--text-muted);

    font-size: 7px;
    font-weight: 800;

    letter-spacing: 0.8px;

    text-transform: uppercase;

    margin-bottom: 3px;
}

.terminal-market-value {
    color: var(--text-primary);

    font-size: 13px;
    font-weight: 850;

    line-height: 1;
}

.terminal-market-value.compact {
    font-size: 10px;
}

.terminal-bull {
    color: var(--green) !important;
}

.terminal-bear {
    color: var(--red) !important;
}

.terminal-neutral {
    color: var(--amber) !important;
}


/* ---------- LIVE STATUS ---------- */

.terminal-live {
    display: flex;

    align-items: center;

    gap: 6px;

    padding-left: 13px;

    margin-left: 3px;

    border-left:
        1px solid var(--border);
}

.terminal-live-dot {
    color: var(--green);

    font-size: 8px;

    animation:
        terminal-pulse 1.8s infinite;
}

.terminal-live-text {
    color: var(--green);

    font-size: 8px;
    font-weight: 900;

    letter-spacing: 0.8px;
}

.terminal-time {
    color: var(--text-dim);

    font-size: 8px;

    margin-top: 2px;
}


@keyframes terminal-pulse {

    0%, 100% {
        opacity: 1;
    }

    50% {
        opacity: 0.35;
    }
}

    /* =========================================================
       07. UNIVERSAL TERMINAL PANEL
       ========================================================= */

    .terminal-panel {
        background: var(--bg-panel);

        border:
            1px solid var(--border);

        border-radius: var(--radius-md);

        box-shadow: var(--shadow-panel);

        padding: 12px;
    }

    .terminal-panel-flat {
        background: var(--bg-panel);

        border:
            1px solid var(--border);

        border-radius: var(--radius-md);

        padding: 10px 12px;
    }


    /* =========================================================
       08. METRIC CARDS
       ========================================================= */

    .metric-card {
        background: var(--bg-panel);

        border:
            1px solid var(--border);

        border-radius: var(--radius-md);

        padding: 10px 13px;

        min-height: 74px;

        box-shadow: var(--shadow-panel);

        transition:
            border-color 0.15s ease,
            background 0.15s ease;
    }

    .metric-card:hover {
        background: var(--bg-panel-2);
        border-color: var(--border-bright);
    }

    .metric-label {
        color: var(--text-muted);

        font-size: 9px;
        font-weight: 800;

        letter-spacing: 0.85px;
        text-transform: uppercase;
    }

    .metric-value {
        color: var(--text-primary);

        font-size: 22px;
        font-weight: 800;

        line-height: 1.1;

        margin-top: 5px;
    }

    .metric-sub {
        color: var(--text-muted);

        font-size: 9px;

        margin-top: 4px;
    }


    /* =========================================================
       09. LEVEL CARDS
       ========================================================= */

    .level-card {
        background: var(--bg-panel);

        border:
            1px solid var(--border);

        border-radius: var(--radius-md);

        padding: 9px 12px;

        min-height: 68px;
    }

    .level-title {
        color: var(--text-muted);

        font-size: 9px;
        font-weight: 800;

        letter-spacing: 0.75px;
        text-transform: uppercase;
    }

    .level-value {
        color: var(--text-primary);

        font-size: 19px;
        font-weight: 800;

        margin-top: 5px;
    }

    .support {
        color: var(--green) !important;
    }

    .resistance {
        color: var(--red) !important;
    }


    /* =========================================================
       10. SECTION HEADERS
       ========================================================= */

    .section-title {
        color: var(--text-primary);

        font-size: 13px;
        font-weight: 800;

        letter-spacing: 0.65px;
        text-transform: uppercase;

        margin-top: 8px;
        margin-bottom: 8px;

        padding-left: 8px;

        border-left:
            2px solid var(--border-bright);
    }

    .small-title {
        color: var(--text-secondary);

        font-size: 10px;
        font-weight: 800;

        letter-spacing: 0.7px;
        text-transform: uppercase;

        margin-bottom: 6px;
    }


    /* =========================================================
       11. SIGNAL CARDS
       ========================================================= */

    .signal-card {
        background: var(--bg-panel);

        border:
            1px solid var(--border);

        border-radius: var(--radius-md);

        padding: 12px;

        text-align: center;
    }

    .signal-label {
        color: var(--text-muted);

        font-size: 9px;
        font-weight: 800;

        letter-spacing: 0.7px;
        text-transform: uppercase;
    }

    .signal-value {
        color: var(--text-primary);

        font-size: 21px;
        font-weight: 850;

        margin-top: 4px;
    }

    .bullish {
        color: var(--green) !important;
    }

    .bearish {
        color: var(--red) !important;
    }

    .neutral {
        color: var(--amber) !important;
    }


    /* =========================================================
       12. STATUS STATES
       ========================================================= */

    .data-ready {
        color: var(--green) !important;
        font-weight: 800;
    }

    .data-warning {
        color: var(--amber) !important;
        font-weight: 800;
    }

    .status-live {
        color: var(--green);

        font-size: 9px;
        font-weight: 800;

        letter-spacing: 0.7px;
        text-transform: uppercase;
    }

    .status-live::before {
        content: "●";

        margin-right: 5px;
    }


    /* =========================================================
       13. STREAMLIT METRIC OVERRIDE
       ========================================================= */

    [data-testid="stMetric"] {
        background: var(--bg-panel);

        border:
            1px solid var(--border);

        border-radius: var(--radius-md);

        padding: 10px 12px;

        box-shadow: var(--shadow-panel);
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-muted) !important;

        font-size: 9px !important;
        font-weight: 800 !important;

        letter-spacing: 0.7px;
        text-transform: uppercase;
    }

    [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;

        font-size: 21px !important;
        font-weight: 800 !important;
    }


    /* =========================================================
       14. BUTTONS
       ========================================================= */

    .stButton > button {
        min-height: 34px;

        background: var(--bg-elevated);

        color: var(--text-primary);

        border:
            1px solid var(--border-bright);

        border-radius: var(--radius-md);

        font-size: 10px;
        font-weight: 800;

        letter-spacing: 0.45px;

        transition:
            background 0.15s ease,
            border-color 0.15s ease,
            transform 0.1s ease;
    }

    .stButton > button:hover {
        background: #19212b;

        border-color: #526174;

        color: #ffffff;
    }

    .stButton > button:active {
        transform: translateY(1px);
    }


    /* =========================================================
       15. INPUTS / SELECTBOXES
       ========================================================= */

    div[data-baseweb="select"] > div {
        background: var(--bg-input) !important;

        border:
            1px solid var(--border-bright) !important;

        border-radius: var(--radius-md) !important;

        min-height: 34px;
    }

    div[data-baseweb="select"] span {
        color: var(--text-primary) !important;

        font-size: 11px;
    }

    div[data-baseweb="input"] > div {
        background: var(--bg-input) !important;

        border:
            1px solid var(--border-bright) !important;

        border-radius: var(--radius-md) !important;
    }

    input {
        color: var(--text-primary) !important;
        font-size: 11px !important;
    }

    textarea {
        background: var(--bg-input) !important;
        color: var(--text-primary) !important;
    }


    /* =========================================================
       16. INPUT LABELS
       ========================================================= */

    [data-testid="stWidgetLabel"] label {
        color: var(--text-muted) !important;

        font-size: 9px !important;
        font-weight: 800 !important;

        letter-spacing: 0.7px;

        text-transform: uppercase;
    }


    /* =========================================================
       17. DATA TABLES
       ========================================================= */

    div[data-testid="stDataFrame"] {
        border:
            1px solid var(--border);

        border-radius: var(--radius-md);

        overflow: hidden;

        background: var(--bg-panel);

        box-shadow: var(--shadow-panel);
    }

    div[data-testid="stDataFrame"] * {
        font-size: 10px;
    }


    /* =========================================================
   18. TERMINAL NAVIGATION
   ========================================================= */

div[data-testid="stTabs"] {
    margin-top: 2px;
    margin-bottom: 10px;
}

div[data-baseweb="tab-list"] {
    display: flex !important;

    gap: 0 !important;

    background: #0b0f15;

    border-bottom:
        1px solid var(--border);

    padding:
        0 2px;

    overflow-x: auto !important;
    overflow-y: hidden !important;

    scrollbar-width: none;
}

div[data-baseweb="tab-list"]::-webkit-scrollbar {
    display: none;
}

button[data-baseweb="tab"] {
    flex: 0 0 auto;

    color: #758191 !important;

    background: transparent !important;

    border: 0 !important;

    padding:
        9px 11px 8px 11px !important;

    margin: 0 !important;

    min-height: 34px !important;

    font-size: 9px !important;

    font-weight: 800 !important;

    letter-spacing: 0.65px !important;

    text-transform: uppercase;

    transition:
        color 0.15s ease,
        background 0.15s ease;
}

button[data-baseweb="tab"]:hover {
    color: var(--text-primary) !important;

    background:
        rgba(255,255,255,0.025) !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--text-primary) !important;

    background:
        rgba(255,255,255,0.025) !important;
}

button[data-baseweb="tab"][aria-selected="true"]::after {
    content: "";

    position: absolute;

    bottom: 0;
    left: 10px;
    right: 10px;

    height: 2px;

    background: var(--green);

    border-radius:
        2px 2px 0 0;
}

div[data-baseweb="tab-highlight"] {
    display: none !important;
}

    /* =========================================================
       19. DIVIDERS
       ========================================================= */

    hr {
        border: 0;

        border-top:
            1px solid var(--border);

        margin:
            8px 0;
    }


    /* =========================================================
       20. ALERTS / INFO BOXES
       ========================================================= */

    div[data-testid="stAlert"] {
        background: var(--bg-panel);

        border:
            1px solid var(--border);

        border-radius: var(--radius-md);

        color: var(--text-secondary);

        font-size: 10px;
    }


    /* =========================================================
       21. EXPANDERS
       ========================================================= */

    div[data-testid="stExpander"] {
        background: var(--bg-panel);

        border:
            1px solid var(--border);

        border-radius: var(--radius-md);
    }


    /* =========================================================
       22. SCROLLBARS
       ========================================================= */

    ::-webkit-scrollbar {
        width: 7px;
        height: 7px;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg-main);
    }

    ::-webkit-scrollbar-thumb {
        background: #29333f;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #3b4857;
    }


    /* =========================================================
       23. REMOVE UNNECESSARY STREAMLIT DECORATION
       ========================================================= */

    [data-testid="stToolbar"] {
        visibility: hidden;
    }

    #MainMenu {
        visibility: hidden;
    }


    /* =========================================================
       24. COMPACT VERTICAL RHYTHM
       ========================================================= */

    [data-testid="stVerticalBlock"] {
        gap: 0.45rem;
    }

    [data-testid="stHorizontalBlock"] {
        gap: 0.55rem;
    }


    /* =========================================================
       25. MOBILE / SMALL SCREEN SAFETY
       ========================================================= */

    @media (max-width: 900px) {

        .main .block-container {
            padding-left: 10px;
            padding-right: 10px;
        }

        .metric-value {
            font-size: 18px;
        }

        .section-title {
            font-size: 11px;
        }
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
        "ce_pop",
        "ce_rho",

        "pe_delta",
        "pe_gamma",
        "pe_theta",
        "pe_vega",
        "pe_pop",
        "pe_rho"
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
# OPTION GREEKS ANALYTICS ENGINE
# ============================================================

GREEK_COLUMNS = [
    "delta",
    "gamma",
    "theta",
    "vega",
    "rho",
]

OPTION_METRIC_COLUMNS = [
    "iv",
    "pop",
    "delta",
    "gamma",
    "theta",
    "vega",
    "rho",
]


def ensure_greek_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a numeric-safe copy with expected Greek columns present."""
    out = df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()

    required = []
    for side in ("ce", "pe"):
        for metric in OPTION_METRIC_COLUMNS:
            required.append(f"{side}_{metric}")

    for column in required:
        if column not in out.columns:
            out[column] = np.nan
        out[column] = pd.to_numeric(out[column], errors="coerce")

    return out


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator is None or not np.isfinite(denominator) or abs(denominator) < 1e-12:
        return np.nan
    return float(numerator / denominator)


def _sum_product(df: pd.DataFrame, left: str, right: str, absolute: bool = False) -> float:
    if left not in df.columns or right not in df.columns:
        return 0.0
    values = pd.to_numeric(df[left], errors="coerce").fillna(0)
    weight = pd.to_numeric(df[right], errors="coerce").fillna(0)
    product = values * weight
    if absolute:
        product = product.abs()
    return float(product.sum())


def get_atm_row(df: pd.DataFrame, atm: float) -> pd.Series | None:
    if df.empty or "strike" not in df.columns:
        return None

    work = df.copy()
    work["strike"] = pd.to_numeric(work["strike"], errors="coerce")
    work = work.dropna(subset=["strike"])
    if work.empty:
        return None

    idx = (work["strike"] - float(atm)).abs().idxmin()
    return work.loc[idx]


def greek_summary(df: pd.DataFrame, atm: float, range_count: int = 10) -> dict:
    """Build ATM, ratio and raw OI-weighted Greek metrics.

    The exposure values are deliberately labelled as raw OI-weighted values.
    They are NOT presented as dealer GEX/DEX because option-side positioning
    sign assumptions are required for a true dealer-exposure convention.
    """
    work = ensure_greek_columns(df)
    atm_row = get_atm_row(work, atm)

    if atm_row is None:
        return {
            "atm": atm,
            "atm_row": None,
            "valid": False,
        }

    # ATM values
    result = {
        "atm": float(atm),
        "atm_row": atm_row,
        "valid": True,
    }

    for side in ("ce", "pe"):
        for metric in OPTION_METRIC_COLUMNS:
            result[f"atm_{side}_{metric}"] = atm_row.get(f"{side}_{metric}", np.nan)

    # ATM ratios
    result["atm_iv_ratio"] = _safe_ratio(
        result["atm_ce_iv"], result["atm_pe_iv"]
    )
    result["atm_premium_ratio"] = _safe_ratio(
        float(atm_row.get("ce_ltp", np.nan)),
        float(atm_row.get("pe_ltp", np.nan)),
    )

    # ATM ± range
    if "strike" in work.columns:
        strikes = sorted(pd.to_numeric(work["strike"], errors="coerce").dropna().unique())
        if strikes:
            atm_index = min(range(len(strikes)), key=lambda i: abs(strikes[i] - float(atm)))
            lo = max(0, atm_index - int(range_count))
            hi = min(len(strikes), atm_index + int(range_count) + 1)
            range_df = work[work["strike"].isin(strikes[lo:hi])].copy()
        else:
            range_df = work.iloc[0:0].copy()
    else:
        range_df = work.iloc[0:0].copy()

    # Standard market ratios
    ce_oi = pd.to_numeric(range_df.get("ce_oi", 0), errors="coerce").fillna(0).sum()
    pe_oi = pd.to_numeric(range_df.get("pe_oi", 0), errors="coerce").fillna(0).sum()
    ce_volume = pd.to_numeric(range_df.get("ce_volume", 0), errors="coerce").fillna(0).sum()
    pe_volume = pd.to_numeric(range_df.get("pe_volume", 0), errors="coerce").fillna(0).sum()

    result["range_oi_pcr"] = _safe_ratio(pe_oi, ce_oi)
    result["range_volume_pcr"] = _safe_ratio(pe_volume, ce_volume)

    # Greek/OI ratios. Absolute weighting avoids cancellation between strikes.
    for metric in GREEK_COLUMNS:
        if metric == "rho":
            # Rho is optional in the current stored chain.
            pass
        ce_exp = _sum_product(range_df, f"ce_{metric}", "ce_oi", absolute=True)
        pe_exp = _sum_product(range_df, f"pe_{metric}", "pe_oi", absolute=True)
        result[f"{metric}_oi_ratio"] = _safe_ratio(ce_exp, pe_exp)
        result[f"ce_{metric}_oi_weighted"] = _sum_product(range_df, f"ce_{metric}", "ce_oi")
        result[f"pe_{metric}_oi_weighted"] = _sum_product(range_df, f"pe_{metric}", "pe_oi")
        result[f"net_{metric}_oi_weighted"] = (
            result[f"ce_{metric}_oi_weighted"] + result[f"pe_{metric}_oi_weighted"]
        )

    # IV ratio across the selected range.
    ce_iv = pd.to_numeric(range_df.get("ce_iv", 0), errors="coerce").replace(0, np.nan)
    pe_iv = pd.to_numeric(range_df.get("pe_iv", 0), errors="coerce").replace(0, np.nan)
    result["range_ce_iv_mean"] = float(ce_iv.mean()) if ce_iv.notna().any() else np.nan
    result["range_pe_iv_mean"] = float(pe_iv.mean()) if pe_iv.notna().any() else np.nan
    result["range_iv_ratio"] = _safe_ratio(
        result["range_ce_iv_mean"], result["range_pe_iv_mean"]
    )

    # Data quality counts.
    for side in ("ce", "pe"):
        for metric in OPTION_METRIC_COLUMNS:
            col = f"{side}_{metric}"
            result[f"{col}_valid"] = int(
                pd.to_numeric(work[col], errors="coerce").notna().sum()
            )

    return result

# ============================================================
# STEP 10 — GREEK CONTROL / INTELLIGENCE ENGINE
# ============================================================

def greek_control_summary(
    df,
    atm,
    range_count=10
):
    """
    Compact Greek intelligence layer.

    Uses the existing Greek columns already produced by
    ensure_greek_columns() / greek_summary().
    """

    result = {
        "valid": False,

        "atm_delta": np.nan,
        "atm_gamma": np.nan,
        "atm_theta": np.nan,
        "atm_vega": np.nan,

        "ce_delta": np.nan,
        "pe_delta": np.nan,
        "ce_gamma": np.nan,
        "pe_gamma": np.nan,
        "ce_theta": np.nan,
        "pe_theta": np.nan,
        "ce_vega": np.nan,
        "pe_vega": np.nan,

        "net_delta": np.nan,
        "net_gamma": np.nan,
        "net_theta": np.nan,
        "net_vega": np.nan,

        "delta_bias": "NEUTRAL",
        "gamma_regime": "NEUTRAL",
        "theta_regime": "NEUTRAL",
        "vega_regime": "NEUTRAL",

        "gamma_concentration_strike": np.nan,
        "delta_concentration_strike": np.nan,
        "vega_concentration_strike": np.nan,

        "gamma_exposure": 0.0,
        "delta_exposure": 0.0,
        "theta_exposure": 0.0,
        "vega_exposure": 0.0,
    }

    try:

        work = ensure_greek_columns(df).copy()

    except Exception:

        return result

    if work.empty:
        return result

    if "strike" not in work.columns:
        return result

    # --------------------------------------------------------
    # NUMERIC NORMALIZATION
    # --------------------------------------------------------

    numeric_columns = [
        "strike",

        "ce_delta",
        "pe_delta",

        "ce_gamma",
        "pe_gamma",

        "ce_theta",
        "pe_theta",

        "ce_vega",
        "pe_vega",

        "ce_oi",
        "pe_oi"
    ]

    for column in numeric_columns:

        if column in work.columns:

            work[column] = pd.to_numeric(
                work[column],
                errors="coerce"
            )

    work = work.dropna(
        subset=["strike"]
    )

    if work.empty:
        return result

    # --------------------------------------------------------
    # FIND ATM
    # --------------------------------------------------------

    try:

        atm_index = (
            work["strike"]
            - float(atm)
        ).abs().idxmin()

        atm_row = work.loc[
            atm_index
        ]

    except Exception:

        atm_row = None

    if atm_row is None:
        return result

    # --------------------------------------------------------
    # ATM GREEKS
    # --------------------------------------------------------

    ce_delta = atm_row.get(
        "ce_delta",
        np.nan
    )

    pe_delta = atm_row.get(
        "pe_delta",
        np.nan
    )

    ce_gamma = atm_row.get(
        "ce_gamma",
        np.nan
    )

    pe_gamma = atm_row.get(
        "pe_gamma",
        np.nan
    )

    ce_theta = atm_row.get(
        "ce_theta",
        np.nan
    )

    pe_theta = atm_row.get(
        "pe_theta",
        np.nan
    )

    ce_vega = atm_row.get(
        "ce_vega",
        np.nan
    )

    pe_vega = atm_row.get(
        "pe_vega",
        np.nan
    )

    # --------------------------------------------------------
    # ATM NET VALUES
    # --------------------------------------------------------

    atm_delta = (
        safe_number(ce_delta, 0)
        + safe_number(pe_delta, 0)
    )

    atm_gamma = (
        safe_number(ce_gamma, 0)
        + safe_number(pe_gamma, 0)
    )

    atm_theta = (
        safe_number(ce_theta, 0)
        + safe_number(pe_theta, 0)
    )

    atm_vega = (
        safe_number(ce_vega, 0)
        + safe_number(pe_vega, 0)
    )

    # --------------------------------------------------------
    # SELECT ATM RANGE
    # --------------------------------------------------------

    strikes = sorted(
        pd.to_numeric(
            work["strike"],
            errors="coerce"
        )
        .dropna()
        .unique()
    )

    if not strikes:
        return result

    atm_position = min(
        range(len(strikes)),
        key=lambda i:
            abs(
                strikes[i]
                - float(atm)
            )
    )

    lo = max(
        0,
        atm_position
        - int(range_count)
    )

    hi = min(
        len(strikes),
        atm_position
        + int(range_count)
        + 1
    )

    selected_strikes = strikes[
        lo:hi
    ]

    range_df = work[
        work["strike"].isin(
            selected_strikes
        )
    ].copy()

    # --------------------------------------------------------
    # OI-WEIGHTED GREEK EXPOSURE
    # --------------------------------------------------------

    def weighted_exposure(
        metric
    ):

        ce_metric = pd.to_numeric(
            range_df.get(
                f"ce_{metric}",
                0
            ),
            errors="coerce"
        ).fillna(0)

        pe_metric = pd.to_numeric(
            range_df.get(
                f"pe_{metric}",
                0
            ),
            errors="coerce"
        ).fillna(0)

        ce_oi = pd.to_numeric(
            range_df.get(
                "ce_oi",
                0
            ),
            errors="coerce"
        ).fillna(0)

        pe_oi = pd.to_numeric(
            range_df.get(
                "pe_oi",
                0
            ),
            errors="coerce"
        ).fillna(0)

        ce_exp = (
            ce_metric
            * ce_oi
        ).sum()

        pe_exp = (
            pe_metric
            * pe_oi
        ).sum()

        return (
            float(ce_exp),
            float(pe_exp)
        )

    ce_delta_exp, pe_delta_exp = (
        weighted_exposure("delta")
    )

    ce_gamma_exp, pe_gamma_exp = (
        weighted_exposure("gamma")
    )

    ce_theta_exp, pe_theta_exp = (
        weighted_exposure("theta")
    )

    ce_vega_exp, pe_vega_exp = (
        weighted_exposure("vega")
    )

    net_delta = (
        ce_delta_exp
        + pe_delta_exp
    )

    net_gamma = (
        ce_gamma_exp
        + pe_gamma_exp
    )

    net_theta = (
        ce_theta_exp
        + pe_theta_exp
    )

    net_vega = (
        ce_vega_exp
        + pe_vega_exp
    )

    # --------------------------------------------------------
    # CONCENTRATION STRIKES
    # --------------------------------------------------------

    range_df["gamma_abs"] = (
        pd.to_numeric(
            range_df["ce_gamma"],
            errors="coerce"
        ).abs().fillna(0)
        +
        pd.to_numeric(
            range_df["pe_gamma"],
            errors="coerce"
        ).abs().fillna(0)
    )

    range_df["delta_abs"] = (
        pd.to_numeric(
            range_df["ce_delta"],
            errors="coerce"
        ).abs().fillna(0)
        +
        pd.to_numeric(
            range_df["pe_delta"],
            errors="coerce"
        ).abs().fillna(0)
    )

    range_df["vega_abs"] = (
        pd.to_numeric(
            range_df["ce_vega"],
            errors="coerce"
        ).abs().fillna(0)
        +
        pd.to_numeric(
            range_df["pe_vega"],
            errors="coerce"
        ).abs().fillna(0)
    )

    def max_strike(column):

        try:

            return float(
                range_df.loc[
                    range_df[column].idxmax(),
                    "strike"
                ]
            )

        except Exception:

            return np.nan

    gamma_concentration_strike = (
        max_strike("gamma_abs")
    )

    delta_concentration_strike = (
        max_strike("delta_abs")
    )

    vega_concentration_strike = (
        max_strike("vega_abs")
    )

    # --------------------------------------------------------
    # DELTA BIAS
    # --------------------------------------------------------

    if net_delta > 0:

        delta_bias = "POSITIVE DELTA"

    elif net_delta < 0:

        delta_bias = "NEGATIVE DELTA"

    else:

        delta_bias = "DELTA NEUTRAL"

    # --------------------------------------------------------
    # GAMMA REGIME
    # --------------------------------------------------------

    if net_gamma > 0:

        gamma_regime = "POSITIVE GAMMA"

    elif net_gamma < 0:

        gamma_regime = "NEGATIVE GAMMA"

    else:

        gamma_regime = "GAMMA NEUTRAL"

    # --------------------------------------------------------
    # THETA REGIME
    # --------------------------------------------------------

    if net_theta < 0:

        theta_regime = "NEGATIVE THETA"

    elif net_theta > 0:

        theta_regime = "POSITIVE THETA"

    else:

        theta_regime = "THETA NEUTRAL"

    # --------------------------------------------------------
    # VEGA REGIME
    # --------------------------------------------------------

    if net_vega > 0:

        vega_regime = "POSITIVE VEGA"

    elif net_vega < 0:

        vega_regime = "NEGATIVE VEGA"

    else:

        vega_regime = "VEGA NEUTRAL"

    result.update({

        "valid": True,

        "atm_delta": atm_delta,
        "atm_gamma": atm_gamma,
        "atm_theta": atm_theta,
        "atm_vega": atm_vega,

        "ce_delta": ce_delta,
        "pe_delta": pe_delta,

        "ce_gamma": ce_gamma,
        "pe_gamma": pe_gamma,

        "ce_theta": ce_theta,
        "pe_theta": pe_theta,

        "ce_vega": ce_vega,
        "pe_vega": pe_vega,

        "net_delta": net_delta,
        "net_gamma": net_gamma,
        "net_theta": net_theta,
        "net_vega": net_vega,

        "delta_bias": delta_bias,
        "gamma_regime": gamma_regime,
        "theta_regime": theta_regime,
        "vega_regime": vega_regime,

        "gamma_concentration_strike":
            gamma_concentration_strike,

        "delta_concentration_strike":
            delta_concentration_strike,

        "vega_concentration_strike":
            vega_concentration_strike,

        "gamma_exposure":
            net_gamma,

        "delta_exposure":
            net_delta,

        "theta_exposure":
            net_theta,

        "vega_exposure":
            net_vega
    })

    return result
# ============================================================
# STEP 11 — GREEK VISUAL ANALYTICS ENGINE
# ============================================================

def build_greek_heatmap(
    df,
    atm,
    range_count=10,
    side="NET"
):
    """
    Greek matrix heatmap across strikes.

    Side:
        CE
        PE
        NET

    NET = CE + PE

    Values remain raw for tooltips while the heatmap
    uses a row-wise normalized scale so Delta, Gamma,
    Theta and Vega can be visually compared.
    """

    try:

        work = ensure_greek_columns(
            df
        ).copy()

    except Exception:

        return None

    if work.empty:
        return None

    if "strike" not in work.columns:
        return None

    # --------------------------------------------------------
    # NORMALIZE NUMERIC COLUMNS
    # --------------------------------------------------------

    greek_metrics = [
        "Delta",
        "Gamma",
        "Theta",
        "Vega"
    ]

    metric_map = {
        "Delta": "delta",
        "Gamma": "gamma",
        "Theta": "theta",
        "Vega": "vega"
    }

    for metric_key in metric_map.values():

        for option_side in [
            "ce",
            "pe"
        ]:

            column = (
                f"{option_side}_{metric_key}"
            )

            if column in work.columns:

                work[column] = pd.to_numeric(
                    work[column],
                    errors="coerce"
                ).fillna(0)

    work["strike"] = pd.to_numeric(
        work["strike"],
        errors="coerce"
    )

    work = work.dropna(
        subset=["strike"]
    )

    if work.empty:
        return None

    # --------------------------------------------------------
    # ATM RANGE
    # --------------------------------------------------------

    strikes = sorted(
        work["strike"]
        .unique()
        .tolist()
    )

    if not strikes:
        return None

    atm_index = min(
        range(len(strikes)),
        key=lambda i:
            abs(
                strikes[i]
                - float(atm)
            )
    )

    lo = max(
        0,
        atm_index
        - int(range_count)
    )

    hi = min(
        len(strikes),
        atm_index
        + int(range_count)
        + 1
    )

    selected_strikes = strikes[
        lo:hi
    ]

    work = work[
        work["strike"].isin(
            selected_strikes
        )
    ].copy()

    if work.empty:
        return None

    # --------------------------------------------------------
    # BUILD LONG DATASET
    # --------------------------------------------------------

    rows = []

    for metric in greek_metrics:

        metric_key = metric_map[
            metric
        ]

        ce_col = f"ce_{metric_key}"
        pe_col = f"pe_{metric_key}"

        if (
            ce_col not in work.columns
            or pe_col not in work.columns
        ):
            continue

        for _, row in work.iterrows():

            strike = row["strike"]

            ce_value = safe_number(
                row.get(
                    ce_col,
                    0
                ),
                0
            )

            pe_value = safe_number(
                row.get(
                    pe_col,
                    0
                ),
                0
            )

            if side == "CE":

                value = ce_value

            elif side == "PE":

                value = pe_value

            else:

                value = (
                    ce_value
                    + pe_value
                )

            rows.append(
                {
                    "Metric": metric,
                    "Strike": strike,
                    "Value": value
                }
            )

    if not rows:
        return None

    heat_df = pd.DataFrame(
        rows
    )

    # --------------------------------------------------------
    # ROW-WISE NORMALIZATION
    # --------------------------------------------------------

    def normalize_row(
        group
    ):

        values = (
            pd.to_numeric(
                group["Value"],
                errors="coerce"
            )
            .fillna(0)
        )

        max_abs = float(
            values.abs().max()
        )

        if max_abs == 0:

            group["Intensity"] = 0.0

        else:

            group["Intensity"] = (
                values
                / max_abs
            )

        return group

    heat_df = (
        heat_df
        .groupby(
            "Metric",
            group_keys=False
        )
        .apply(
            normalize_row
        )
        .reset_index(
            drop=True
        )
    )

    # --------------------------------------------------------
    # HEATMAP
    # --------------------------------------------------------

    chart = (
        alt.Chart(
            heat_df
        )
        .mark_rect(
            cornerRadius=4,
            stroke="#202631",
            strokeWidth=1
        )
        .encode(

            x=alt.X(
                "Strike:O",
                title="STRIKE",
                sort=selected_strikes,
                axis=alt.Axis(
                    labelAngle=0
                )
            ),

            y=alt.Y(
                "Metric:N",
                title=None,
                sort=[
                    "Delta",
                    "Gamma",
                    "Theta",
                    "Vega"
                ]
            ),

            color=alt.Color(
                "Intensity:Q",
                scale=alt.Scale(
                    domain=[
                        -1,
                        0,
                        1
                    ],
                    range=[
                        "#ff4654",
                        "#11151c",
                        "#00d995"
                    ]
                ),
                legend=alt.Legend(
                    title="RELATIVE INTENSITY"
                )
            ),

            tooltip=[
                alt.Tooltip(
                    "Strike:Q",
                    title="Strike",
                    format=",.0f"
                ),
                alt.Tooltip(
                    "Metric:N",
                    title="Greek"
                ),
                alt.Tooltip(
                    "Value:Q",
                    title="Raw Value",
                    format=",.6f"
                ),
                alt.Tooltip(
                    "Intensity:Q",
                    title="Relative",
                    format=".2f"
                )
            ]
        )
        .properties(
            height=250
        )
        .interactive()
    )

    return chart
# ============================================================
# GREEK CONCENTRATION ENGINE
# ============================================================

def greek_concentration_summary(
    df,
    atm,
    range_count=10
):
    """
    Finds the strike where each Greek has the
    highest combined CE + PE absolute concentration.
    """

    result = {
        "valid": False,

        "delta_strike": np.nan,
        "gamma_strike": np.nan,
        "theta_strike": np.nan,
        "vega_strike": np.nan,

        "delta_value": np.nan,
        "gamma_value": np.nan,
        "theta_value": np.nan,
        "vega_value": np.nan
    }

    try:

        work = ensure_greek_columns(
            df
        ).copy()

    except Exception:

        return result

    if work.empty:
        return result

    if "strike" not in work.columns:
        return result

    work["strike"] = pd.to_numeric(
        work["strike"],
        errors="coerce"
    )

    work = work.dropna(
        subset=["strike"]
    )

    if work.empty:
        return result

    # --------------------------------------------------------
    # ATM RANGE
    # --------------------------------------------------------

    strikes = sorted(
        work["strike"]
        .unique()
        .tolist()
    )

    if not strikes:
        return result

    atm_index = min(
        range(len(strikes)),
        key=lambda i:
            abs(
                strikes[i]
                - float(atm)
            )
    )

    lo = max(
        0,
        atm_index
        - int(range_count)
    )

    hi = min(
        len(strikes),
        atm_index
        + int(range_count)
        + 1
    )

    work = work[
        work["strike"].isin(
            strikes[lo:hi]
        )
    ].copy()

    # --------------------------------------------------------
    # EACH GREEK
    # --------------------------------------------------------

    for greek in [
        "delta",
        "gamma",
        "theta",
        "vega"
    ]:

        ce_col = f"ce_{greek}"
        pe_col = f"pe_{greek}"

        if (
            ce_col not in work.columns
            or pe_col not in work.columns
        ):
            continue

        ce = pd.to_numeric(
            work[ce_col],
            errors="coerce"
        ).fillna(0)

        pe = pd.to_numeric(
            work[pe_col],
            errors="coerce"
        ).fillna(0)

        work[
            f"{greek}_combined"
        ] = (
            ce.abs()
            + pe.abs()
        )

        try:

            index = work[
                f"{greek}_combined"
            ].idxmax()

            result[
                f"{greek}_strike"
            ] = float(
                work.loc[
                    index,
                    "strike"
                ]
            )

            result[
                f"{greek}_value"
            ] = float(
                work.loc[
                    index,
                    f"{greek}_combined"
                ]
            )

        except Exception:

            pass

    result["valid"] = True

    return result
def greek_by_strike_chart(
    df: pd.DataFrame,
    atm: float,
    metric: str = "Delta",
    side: str = "CE + PE",
    range_count: int = 10,
    height: int = 360,
):
    """Return a responsive Greek-by-strike Altair chart."""
    work = ensure_greek_columns(df)
    if work.empty or "strike" not in work.columns:
        return None

    metric_key = str(metric).strip().lower()
    if metric_key not in OPTION_METRIC_COLUMNS:
        metric_key = "delta"

    if metric_key in {"iv", "pop"}:
        # These are not Greeks but are useful in the same analytical view.
        y_title = metric_key.upper()
    else:
        y_title = metric_key.capitalize()

    strikes = sorted(pd.to_numeric(work["strike"], errors="coerce").dropna().unique())
    if not strikes:
        return None

    atm_index = min(range(len(strikes)), key=lambda i: abs(strikes[i] - float(atm)))
    lo = max(0, atm_index - int(range_count))
    hi = min(len(strikes), atm_index + int(range_count) + 1)
    selected = strikes[lo:hi]

    chart_df = work[work["strike"].isin(selected)][["strike", f"ce_{metric_key}", f"pe_{metric_key}"]].copy()
    chart_df = chart_df.melt(
        id_vars=["strike"],
        value_vars=[f"ce_{metric_key}", f"pe_{metric_key}"],
        var_name="Side",
        value_name="Value",
    )
    chart_df["Side"] = chart_df["Side"].map(
        {f"ce_{metric_key}": "CE", f"pe_{metric_key}": "PE"}
    )
    chart_df = chart_df.dropna(subset=["Value"])

    if side in {"CE", "PE"}:
        chart_df = chart_df[chart_df["Side"] == side]

    if chart_df.empty:
        return None

    colors = ["#ff4654", "#00d995"]
    domain = ["CE", "PE"]

    chart = (
        alt.Chart(chart_df)
        .mark_line(point=True, strokeWidth=2)
        .encode(
            x=alt.X("strike:O", title="STRIKE", sort=selected),
            y=alt.Y("Value:Q", title=y_title, scale=alt.Scale(zero=False)),
            color=alt.Color(
                "Side:N",
                scale=alt.Scale(domain=domain, range=colors),
                legend=alt.Legend(title="SIDE"),
            ),
            tooltip=[
                alt.Tooltip("strike:Q", title="Strike", format=",.0f"),
                alt.Tooltip("Side:N", title="Side"),
                alt.Tooltip("Value:Q", title=y_title, format=",.4f"),
            ],
        )
        .properties(height=height)
        .interactive()
    )
    return chart


def greek_exposure_chart(
    df: pd.DataFrame,
    atm: float,
    metric: str = "Delta OI",
    range_count: int = 10,
    height: int = 320,
):
    """Grouped CE/PE raw OI-weighted Greek exposure by strike."""
    work = ensure_greek_columns(df)
    if work.empty or "strike" not in work.columns:
        return None

    metric_map = {
        "Delta OI": "delta",
        "Gamma OI": "gamma",
        "Theta OI": "theta",
        "Vega OI": "vega",
        "Rho OI": "rho",
    }
    metric_key = metric_map.get(metric, "delta")
    ce_col = f"ce_{metric_key}"
    pe_col = f"pe_{metric_key}"

    if ce_col not in work.columns or pe_col not in work.columns:
        return None

    strikes = sorted(pd.to_numeric(work["strike"], errors="coerce").dropna().unique())
    if not strikes:
        return None
    atm_index = min(range(len(strikes)), key=lambda i: abs(strikes[i] - float(atm)))
    lo = max(0, atm_index - int(range_count))
    hi = min(len(strikes), atm_index + int(range_count) + 1)
    selected = strikes[lo:hi]

    chart_df = work[work["strike"].isin(selected)][
        ["strike", ce_col, pe_col, "ce_oi", "pe_oi"]
    ].copy()
    chart_df["CE"] = (
        pd.to_numeric(chart_df[ce_col], errors="coerce").fillna(0)
        * pd.to_numeric(chart_df["ce_oi"], errors="coerce").fillna(0)
    )
    chart_df["PE"] = (
        pd.to_numeric(chart_df[pe_col], errors="coerce").fillna(0)
        * pd.to_numeric(chart_df["pe_oi"], errors="coerce").fillna(0)
    )
    chart_df = chart_df[["strike", "CE", "PE"]].melt(
        id_vars=["strike"], var_name="Side", value_name="Exposure"
    )

    return (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("strike:O", title="STRIKE", sort=selected),
            xOffset=alt.XOffset("Side:N"),
            y=alt.Y("Exposure:Q", title=f"RAW {metric.upper()}", scale=alt.Scale(zero=False)),
            color=alt.Color(
                "Side:N",
                scale=alt.Scale(domain=["CE", "PE"], range=["#ff4654", "#00d995"]),
                legend=alt.Legend(title="SIDE"),
            ),
            tooltip=[
                alt.Tooltip("strike:Q", title="Strike", format=",.0f"),
                alt.Tooltip("Side:N", title="Side"),
                alt.Tooltip("Exposure:Q", title="Raw OI-weighted", format=",.2f"),
            ],
        )
        .properties(height=height)
        .interactive()
    )


def historical_greek_chart(history_df: pd.DataFrame, option_type: str, metric: str, height: int = 300):
    """Create a safe historical Greek chart from get_greek_history output."""
    if not isinstance(history_df, pd.DataFrame) or history_df.empty:
        return None

    prefix = str(option_type).lower()
    metric_key = str(metric).lower()
    column = f"{prefix}_{metric_key}"
    if column not in history_df.columns or "fetch_time" not in history_df.columns:
        return None

    chart_df = history_df[["fetch_time", column]].copy()
    chart_df["fetch_time"] = pd.to_datetime(chart_df["fetch_time"], errors="coerce")
    chart_df["value"] = pd.to_numeric(chart_df[column], errors="coerce")
    chart_df = chart_df.dropna(subset=["fetch_time", "value"])
    if chart_df.empty:
        return None

    return (
        alt.Chart(chart_df)
        .mark_line(point=True, strokeWidth=2)
        .encode(
            x=alt.X("fetch_time:T", title="TIME"),
            y=alt.Y("value:Q", title=metric.upper(), scale=alt.Scale(zero=False)),
            tooltip=[
                alt.Tooltip("fetch_time:T", title="Time"),
                alt.Tooltip("value:Q", title=metric.upper(), format=",.4f"),
            ],
        )
        .properties(height=height)
        .interactive()
    )
# ============================================================
# GAMMA BLAST ENGINE
# ============================================================

def calculate_gamma_blast(df: pd.DataFrame, atm: float, range_count: int = 15):
    """
    Gamma Blast / Gamma Pressure engine.

    IMPORTANT:
    This is an analytical gamma-pressure proxy based on
    Gamma × OI. It is NOT dealer GEX because the dataset
    does not contain dealer/client positioning information.

    Convention used for the pressure proxy:
        CE gamma pressure = +Gamma × CE OI
        PE gamma pressure = -Gamma × PE OI

    The resulting imbalance is useful for identifying
    gamma concentration and pressure zones.
    """

    if not isinstance(df, pd.DataFrame) or df.empty:
        return {
            "valid": False,
            "message": "No option-chain data available."
        }

    work = ensure_greek_columns(df).copy()

    if "strike" not in work.columns:
        return {
            "valid": False,
            "message": "Strike column unavailable."
        }

    work["strike"] = pd.to_numeric(
        work["strike"],
        errors="coerce"
    )

    work = work.dropna(
        subset=["strike"]
    )

    if work.empty:
        return {
            "valid": False,
            "message": "No valid strikes available."
        }

    # --------------------------------------------------------
    # Numeric safety
    # --------------------------------------------------------

    for col in [
        "ce_gamma",
        "pe_gamma",
        "ce_oi",
        "pe_oi"
    ]:

        if col not in work.columns:
            work[col] = 0.0

        work[col] = pd.to_numeric(
            work[col],
            errors="coerce"
        ).fillna(0.0)

    # --------------------------------------------------------
    # Select ATM range
    # --------------------------------------------------------

    strikes = sorted(
        work["strike"].unique()
    )

    if not strikes:
        return {
            "valid": False,
            "message": "No strikes available."
        }

    atm_index = min(
        range(len(strikes)),
        key=lambda i: abs(
            strikes[i] - float(atm)
        )
    )

    lower = max(
        0,
        atm_index - int(range_count)
    )

    upper = min(
        len(strikes),
        atm_index + int(range_count) + 1
    )

    selected_strikes = strikes[
        lower:upper
    ]

    work = work[
        work["strike"].isin(
            selected_strikes
        )
    ].copy()

    # --------------------------------------------------------
    # GAMMA PRESSURE
    # --------------------------------------------------------

    work["CE_GAMMA_PRESSURE"] = (
        work["ce_gamma"]
        * work["ce_oi"]
    )

    work["PE_GAMMA_PRESSURE"] = (
        work["pe_gamma"]
        * work["pe_oi"]
    )

    # Proxy directional convention
    work["NET_GAMMA_PRESSURE"] = (
        work["CE_GAMMA_PRESSURE"]
        - work["PE_GAMMA_PRESSURE"]
    )

    work["ABS_GAMMA_PRESSURE"] = (
        work["CE_GAMMA_PRESSURE"].abs()
        +
        work["PE_GAMMA_PRESSURE"].abs()
    )

    # --------------------------------------------------------
    # TOTALS
    # --------------------------------------------------------

    ce_gamma_pressure = float(
        work["CE_GAMMA_PRESSURE"].sum()
    )

    pe_gamma_pressure = float(
        work["PE_GAMMA_PRESSURE"].sum()
    )

    net_gamma_pressure = float(
        work["NET_GAMMA_PRESSURE"].sum()
    )

    total_gamma_pressure = float(
        work["ABS_GAMMA_PRESSURE"].sum()
    )

    gamma_imbalance = (
        net_gamma_pressure
        / total_gamma_pressure
        if total_gamma_pressure > 0
        else np.nan
    )

    # --------------------------------------------------------
    # GAMMA WALL
    # --------------------------------------------------------

    if not work.empty:

        wall_idx = (
            work["ABS_GAMMA_PRESSURE"]
            .idxmax()
        )

        gamma_wall_strike = float(
            work.loc[
                wall_idx,
                "strike"
            ]
        )

        gamma_wall_value = float(
            work.loc[
                wall_idx,
                "ABS_GAMMA_PRESSURE"
            ]
        )

    else:

        gamma_wall_strike = np.nan
        gamma_wall_value = np.nan

    # --------------------------------------------------------
    # ATM GAMMA
    # --------------------------------------------------------

    atm_idx = (
        (work["strike"] - float(atm))
        .abs()
        .idxmin()
    )

    atm_row = work.loc[
        atm_idx
    ]

    atm_ce_gamma = float(
        atm_row["ce_gamma"]
    )

    atm_pe_gamma = float(
        atm_row["pe_gamma"]
    )

    atm_net_gamma = (
        float(
            atm_row["CE_GAMMA_PRESSURE"]
        )
        -
        float(
            atm_row["PE_GAMMA_PRESSURE"]
        )
    )

    # --------------------------------------------------------
    # BLAST SCORE
    # --------------------------------------------------------

    blast_score = (
        abs(gamma_imbalance)
        * 100
        if np.isfinite(gamma_imbalance)
        else 0
    )

    if blast_score >= 60:

        blast_strength = "EXTREME"

    elif blast_score >= 40:

        blast_strength = "STRONG"

    elif blast_score >= 20:

        blast_strength = "MODERATE"

    else:

        blast_strength = "WEAK"

    # --------------------------------------------------------
    # PRESSURE CLASSIFICATION
    # --------------------------------------------------------

    if net_gamma_pressure > 0:

        pressure = "LONG GAMMA PRESSURE"

    elif net_gamma_pressure < 0:

        pressure = "SHORT GAMMA PRESSURE"

    else:

        pressure = "GAMMA NEUTRAL"

    # --------------------------------------------------------
    # ATM DISTANCE TO WALL
    # --------------------------------------------------------

    wall_distance = (
        gamma_wall_strike - float(atm)
        if np.isfinite(gamma_wall_strike)
        else np.nan
    )

    return {
        "valid": True,

        "data": work,

        "atm": float(atm),

        "ce_gamma_pressure":
            ce_gamma_pressure,

        "pe_gamma_pressure":
            pe_gamma_pressure,

        "net_gamma_pressure":
            net_gamma_pressure,

        "total_gamma_pressure":
            total_gamma_pressure,

        "gamma_imbalance":
            gamma_imbalance,

        "blast_score":
            blast_score,

        "blast_strength":
            blast_strength,

        "pressure":
            pressure,

        "gamma_wall_strike":
            gamma_wall_strike,

        "gamma_wall_value":
            gamma_wall_value,

        "wall_distance":
            wall_distance,

        "atm_ce_gamma":
            atm_ce_gamma,

        "atm_pe_gamma":
            atm_pe_gamma,

        "atm_net_gamma":
            atm_net_gamma,
    }


# ============================================================
# GAMMA FLIP / GAMMA WALL ENGINE
# ============================================================

def calculate_gamma_structure(
    gamma_result,
    spot,
    atm
):
    """
    Detect gamma wall, gamma flip and gamma regime.

    Gamma flip:
        First strike where cumulative net gamma pressure
        changes sign.

    This is a pressure-proxy calculation and is NOT dealer GEX.
    """

    if not gamma_result:
        return {
            "valid": False
        }

    if not gamma_result.get(
        "valid",
        False
    ):
        return {
            "valid": False
        }

    data = gamma_result.get(
        "data"
    )

    if not isinstance(
        data,
        pd.DataFrame
    ):
        return {
            "valid": False
        }

    if data.empty:
        return {
            "valid": False
        }

    work = data.copy()

    required = [
        "strike",
        "NET_GAMMA_PRESSURE"
    ]

    for col in required:

        if col not in work.columns:
            return {
                "valid": False
            }

    work["strike"] = pd.to_numeric(
        work["strike"],
        errors="coerce"
    )

    work["NET_GAMMA_PRESSURE"] = pd.to_numeric(
        work["NET_GAMMA_PRESSURE"],
        errors="coerce"
    )

    work = work.dropna(
        subset=[
            "strike",
            "NET_GAMMA_PRESSURE"
        ]
    )

    work = (
        work
        .sort_values("strike")
        .reset_index(drop=True)
    )

    if work.empty:
        return {
            "valid": False
        }

    work["CUMULATIVE_GAMMA"] = (
        work["NET_GAMMA_PRESSURE"].cumsum()
    )

    flip_strikes = []

    for index in range(1, len(work)):
        previous_value = work.loc[
            index - 1,
            "CUMULATIVE_GAMMA"
        ]
        current_value = work.loc[
            index,
            "CUMULATIVE_GAMMA"
        ]

        if (
            previous_value < 0 <= current_value
            or previous_value > 0 >= current_value
        ):
            flip_strikes.append(
                float(work.loc[index, "strike"])
            )

    gamma_flip = (
        min(
            flip_strikes,
            key=lambda strike: abs(strike - float(spot))
        )
        if flip_strikes
        else np.nan
    )

    if np.isfinite(gamma_flip):
        if float(spot) > gamma_flip:
            regime = "POSITIVE GAMMA ZONE"
        elif float(spot) < gamma_flip:
            regime = "NEGATIVE GAMMA ZONE"
        else:
            regime = "AT GAMMA FLIP"
    else:
        atm_index = min(
            range(len(work)),
            key=lambda index: abs(
                float(work.loc[index, "strike"]) - float(atm)
            )
        )
        atm_cumulative = work.loc[
            atm_index,
            "CUMULATIVE_GAMMA"
        ]
        regime = (
            "POSITIVE GAMMA ZONE"
            if atm_cumulative > 0
            else "NEGATIVE GAMMA ZONE"
            if atm_cumulative < 0
            else "GAMMA NEUTRAL"
        )

    wall_index = work["NET_GAMMA_PRESSURE"].abs().idxmax()
    gamma_wall = float(work.loc[wall_index, "strike"])
    wall_pressure = float(
        work.loc[wall_index, "NET_GAMMA_PRESSURE"]
    )

    above = work[work["strike"] > float(spot)]
    below = work[work["strike"] < float(spot)]

    wall_above = (
        float(above.loc[above["NET_GAMMA_PRESSURE"].abs().idxmax(), "strike"])
        if not above.empty
        else np.nan
    )
    wall_below = (
        float(below.loc[below["NET_GAMMA_PRESSURE"].abs().idxmax(), "strike"])
        if not below.empty
        else np.nan
    )

    flip_distance = (
        gamma_flip - float(spot)
        if np.isfinite(gamma_flip)
        else np.nan
    )
    distance_from_flip = abs(flip_distance)
    if not np.isfinite(gamma_flip):
        blast_zone = "GAMMA UNDEFINED"
    elif distance_from_flip <= 50:
        blast_zone = "GAMMA FLIP ZONE"
    elif distance_from_flip <= 100:
        blast_zone = "GAMMA TRANSITION"
    else:
        blast_zone = "GAMMA TREND ZONE"

    return {
        "valid": True,
        "data": work,
        "gamma_flip": gamma_flip,
        "gamma_wall": gamma_wall,
        "wall_pressure": wall_pressure,
        "wall_distance": gamma_wall - float(spot),
        "flip_distance": flip_distance,
        "wall_above": wall_above,
        "wall_below": wall_below,
        "regime": regime,
        "blast_zone": blast_zone,
    }

# ============================================================
# BUILD AGGREGATED GAMMA HISTORY
# ============================================================

def build_gamma_history_snapshot(
    history_df
):
    """
    Convert historical option-chain records into
    aggregated gamma-pressure snapshots.

    Expected historical fields may include:
        fetch_time
        strike
        ce_gamma
        pe_gamma
        ce_oi
        pe_oi

    Returns:
        fetch_time
        gamma_pressure
    """

    if not isinstance(
        history_df,
        pd.DataFrame
    ):
        return pd.DataFrame()

    if history_df.empty:
        return pd.DataFrame()

    work = history_df.copy()

    required = [
        "fetch_time",
        "ce_gamma",
        "pe_gamma",
        "ce_oi",
        "pe_oi"
    ]

    missing = [
        col
        for col in required
        if col not in work.columns
    ]

    if missing:
        return pd.DataFrame()

    work["fetch_time"] = pd.to_datetime(
        work["fetch_time"],
        errors="coerce"
    )

    for col in required[1:]:

        work[col] = pd.to_numeric(
            work[col],
            errors="coerce"
        ).fillna(0)

    work = work.dropna(
        subset=[
            "fetch_time"
        ]
    )

    if work.empty:
        return pd.DataFrame()
    
    # ============================================================
# GAMMA BLAST COMPOSITE SCORE
# ============================================================

def calculate_gamma_blast_score(
    gamma_blast,
    gamma_structure,
    gamma_acceleration=None,
    greek_metrics=None,
    spot=None,
    atm=None
):
    """
    Composite 0-100 Gamma Blast score.

    Components:
        30% Gamma pressure
        20% Gamma wall concentration
        20% Gamma flip proximity
        15% Gamma acceleration
        10% OI pressure
         5% IV pressure

    Missing components are automatically removed from the
    denominator so the score does not pretend unavailable
    data exists.

    This is an analytical score, NOT an automatic order signal.
    """

    result = {
        "valid": False,
        "score": 0.0,
        "direction": "NEUTRAL",
        "state": "LOW",
        "components": {},
        "available_weight": 0.0,
    }

    if not gamma_blast:
        return result

    if not gamma_blast.get(
        "valid",
        False
    ):
        return result
    
    # ============================================================
# STEP 8 — GAMMA + PRICE ACTION FUSION ENGINE
# ============================================================

def calculate_gamma_price_fusion(
    gamma_score,
    price_snapshot=None,
    gamma_structure=None
):
    """
    Step 8 Market Regime Fusion Engine.

    Combines:
        55% Gamma Intelligence
        45% Price Action Intelligence

    Output:
        - directional score
        - confidence
        - market regime
        - alignment
        - risk state

    This is an analytical regime engine.
    It is NOT an automatic trading/order signal.
    """

    result = {
        "valid": False,
        "fusion_score": 0.0,
        "gamma_score": 0.0,
        "price_score": 0.0,
        "direction": "NEUTRAL",
        "regime": "NO DATA",
        "confidence": 0.0,
        "alignment": "NO DATA",
        "risk": "UNKNOWN",
        "trend": "UNKNOWN",
        "pattern": "NEUTRAL",
        "supertrend": "NEUTRAL",
        "price_signal": "NEUTRAL",
    }

    # --------------------------------------------------------
    # SAFE HELPERS
    # --------------------------------------------------------

    def signed_bias(value):
        """
        Convert text signal into directional score.
        Returns -100 to +100.
        """

        if value is None:
            return 0.0

        text = str(value).upper().strip()

        bullish_words = [
            "BULL",
            "BUY",
            "LONG",
            "UPTREND",
            "UP",
            "POSITIVE",
            "BREAKOUT",
            "CALL",
            "BULLISH"
        ]

        bearish_words = [
            "BEAR",
            "SELL",
            "SHORT",
            "DOWNTREND",
            "DOWN",
            "NEGATIVE",
            "BREAKDOWN",
            "PUT",
            "BEARISH"
        ]

        bull = any(word in text for word in bullish_words)
        bear = any(word in text for word in bearish_words)

        if bull and not bear:
            return 100.0

        if bear and not bull:
            return -100.0

        return 0.0

    def clamp(value, low=-100.0, high=100.0):

        try:
            value = float(value)
        except Exception:
            return 0.0

        if not np.isfinite(value):
            return 0.0

        return max(low, min(high, value))

    # --------------------------------------------------------
    # GAMMA SIDE
    # --------------------------------------------------------

    if isinstance(gamma_score, dict):

        gamma_magnitude = gamma_score.get(
            "score",
            0.0
        )

        gamma_direction = gamma_score.get(
            "direction",
            "NEUTRAL"
        )

        try:
            gamma_magnitude = float(
                gamma_magnitude
            )
        except Exception:
            gamma_magnitude = 0.0

        gamma_magnitude = max(
            0.0,
            min(100.0, gamma_magnitude)
        )

        gamma_direction_score = signed_bias(
            gamma_direction
        )

        gamma_signed_score = (
            gamma_magnitude
            * (
                1
                if gamma_direction_score > 0
                else -1
                if gamma_direction_score < 0
                else 0
            )
        )

    else:

        gamma_magnitude = 0.0
        gamma_signed_score = 0.0

    # --------------------------------------------------------
    # PRICE ACTION SIDE
    # --------------------------------------------------------

    price_components = []

    if isinstance(price_snapshot, dict):

        trend = price_snapshot.get(
            "trend",
            "UNKNOWN"
        )

        pattern = price_snapshot.get(
            "pattern_bias",
            "NEUTRAL"
        )

        supertrend = price_snapshot.get(
            "supertrend_signal",
            "NEUTRAL"
        )

        price_signal = price_snapshot.get(
            "signal",
            "NEUTRAL"
        )

        # Main trend — 30%
        trend_score = signed_bias(trend)

        # Pattern — 25%
        pattern_score = signed_bias(pattern)

        # Supertrend — 20%
        supertrend_score = signed_bias(
            supertrend
        )

        # Multi-factor signal — 25%
        signal_score_text = signed_bias(
            price_signal
        )

        # Numeric signal score, when available
        numeric_signal_score = price_snapshot.get(
            "signal_score",
            0
        )

        try:
            numeric_signal_score = float(
                numeric_signal_score
            )
        except Exception:
            numeric_signal_score = 0.0

        if np.isfinite(numeric_signal_score):

            # Normalize common +/-100 or +/-10 style scores
            if abs(numeric_signal_score) <= 10:
                numeric_signal_score *= 10

            numeric_signal_score = clamp(
                numeric_signal_score
            )

            if abs(numeric_signal_score) > abs(
                signal_score_text
            ):
                signal_score_text = numeric_signal_score

        price_score = (
            trend_score * 0.30
            + pattern_score * 0.25
            + supertrend_score * 0.20
            + signal_score_text * 0.25
        )

        price_components = [
            trend_score,
            pattern_score,
            supertrend_score,
            signal_score_text
        ]

    else:

        trend = "UNKNOWN"
        pattern = "NEUTRAL"
        supertrend = "NEUTRAL"
        price_signal = "NEUTRAL"

        price_score = 0.0

    price_score = clamp(
        price_score
    )

    # --------------------------------------------------------
    # FINAL FUSION
    # --------------------------------------------------------

    fusion_score = (
        gamma_signed_score * 0.55
        + price_score * 0.45
    )

    fusion_score = clamp(
        fusion_score
    )

    # --------------------------------------------------------
    # DIRECTION
    # --------------------------------------------------------

    if fusion_score >= 60:

        direction = "STRONG BULLISH"

    elif fusion_score >= 25:

        direction = "BULLISH"

    elif fusion_score <= -60:

        direction = "STRONG BEARISH"

    elif fusion_score <= -25:

        direction = "BEARISH"

    else:

        direction = "NEUTRAL"

    # --------------------------------------------------------
    # GAMMA / PRICE ALIGNMENT
    # --------------------------------------------------------

    gamma_sign = np.sign(
        gamma_signed_score
    )

    price_sign = np.sign(
        price_score
    )

    if (
        gamma_sign != 0
        and price_sign != 0
        and gamma_sign == price_sign
    ):

        alignment = "ALIGNED"

    elif (
        gamma_sign != 0
        and price_sign != 0
        and gamma_sign != price_sign
    ):

        alignment = "CONFLICT"

    else:

        alignment = "PARTIAL"

    # --------------------------------------------------------
    # MARKET REGIME
    # --------------------------------------------------------

    abs_fusion = abs(
        fusion_score
    )

    if alignment == "CONFLICT":

        regime = "TRANSITION"

    elif abs_fusion >= 70:

        regime = "EXPANSION"

    elif abs_fusion >= 40:

        regime = "TREND"

    else:

        regime = "RANGE"

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    gamma_confidence = gamma_magnitude

    price_confidence = abs(
        price_score
    )

    confidence = (
        gamma_confidence * 0.55
        + price_confidence * 0.45
    )

    if alignment == "CONFLICT":

        confidence *= 0.70

    confidence = max(
        0.0,
        min(100.0, confidence)
    )

    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    if alignment == "CONFLICT":

        risk = "HIGH"

    elif confidence >= 75:

        risk = "CONTROLLED"

    elif confidence >= 50:

        risk = "MODERATE"

    else:

        risk = "ELEVATED"

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    result.update({

        "valid": True,

        "fusion_score": float(
            fusion_score
        ),

        "gamma_score": float(
            gamma_signed_score
        ),

        "price_score": float(
            price_score
        ),

        "direction": direction,

        "regime": regime,

        "confidence": float(
            confidence
        ),

        "alignment": alignment,

        "risk": risk,

        "trend": trend,

        "pattern": pattern,

        "supertrend": supertrend,

        "price_signal": price_signal,

        "gamma_structure": (
            gamma_structure
            if isinstance(
                gamma_structure,
                dict
            )
            else {}
        )

    })

    return result
    # ============================================================
# GAMMA BLAST VELOCITY ENGINE
# ============================================================

def calculate_gamma_blast_velocity(
    current_score,
    previous_score=None
):
    """
    Measures the change in Gamma Blast Score between
    consecutive application snapshots.

    Uses score movement rather than pretending that
    snapshot frequency itself represents market velocity.
    """

    result = {
        "valid": False,
        "current_score": np.nan,
        "previous_score": np.nan,
        "score_change": np.nan,
        "velocity_pct": np.nan,
        "state": "STABLE",
        "severity": "LOW",
    }

    try:
        current_score = float(
            current_score
        )
    except Exception:
        return result

    if not np.isfinite(
        current_score
    ):
        return result

    result["current_score"] = (
        current_score
    )

    if previous_score is None:
        return result

    try:
        previous_score = float(
            previous_score
        )
    except Exception:
        return result

    if not np.isfinite(
        previous_score
    ):
        return result

    score_change = (
        current_score
        - previous_score
    )

    # Percentage change relative to previous score.
    if abs(previous_score) > 0.01:

        velocity_pct = (
            score_change
            /
            abs(previous_score)
        ) * 100

    else:

        velocity_pct = np.nan
    
    
    # ============================================================
# GAMMA BLAST SNAPSHOT TRACKER
# ============================================================

def update_gamma_blast_snapshot(
    score,
    max_history=100
):
    """
    Keeps a lightweight in-session history of Gamma Blast
    scores.

    This avoids changing the existing persistent database
    until we deliberately integrate Gamma Blast into the
    historical storage layer.
    """

    if "gamma_blast_history" not in st.session_state:

        st.session_state[
            "gamma_blast_history"
        ] = []

    history = (
        st.session_state[
            "gamma_blast_history"
        ]
    )

    try:

        score = float(score)

    except Exception:

        return pd.DataFrame()

    if not np.isfinite(score):

        return pd.DataFrame()

    now = pd.Timestamp.now()

    history.append(
        {
            "timestamp": now,
            "score": score,
        }
    )

    # Prevent uncontrolled session growth.
    if len(history) > max_history:

        st.session_state[
            "gamma_blast_history"
        ] = history[
            -max_history:
        ]

    return pd.DataFrame(
        st.session_state[
            "gamma_blast_history"
        ]
    )
    
    # ============================================================
# GAMMA BLAST SCORE HISTORY CHART
# ============================================================

def gamma_blast_history_chart(
    history_df,
    height=260
):

    return None

# GAMMA PRESSURE HEATMAP
# ============================================================

def build_gamma_pressure_heatmap(
    gamma_df,
    spot=None,
    gamma_wall=None,
    gamma_flip=None
):
    """
    Build a strike-level gamma pressure heatmap.

    Uses the already calculated gamma dataframe.
    """

    if not isinstance(
        gamma_df,
        pd.DataFrame
    ):
        return None

    if gamma_df.empty:
        return None

    work = gamma_df.copy()

    required = [
        "strike",
        "NET_GAMMA_PRESSURE"
    ]

    if not all(
        col in work.columns
        for col in required
    ):
        return None

    work["strike"] = pd.to_numeric(
        work["strike"],
        errors="coerce"
    )

    work["NET_GAMMA_PRESSURE"] = pd.to_numeric(
        work["NET_GAMMA_PRESSURE"],
        errors="coerce"
    )

    work = work.dropna(
        subset=[
            "strike",
            "NET_GAMMA_PRESSURE"
        ]
    )

    if work.empty:
        return None

    # --------------------------------------------------------
    # LIMIT TO RELEVANT STRIKES
    # --------------------------------------------------------

    if spot is not None:

        try:

            spot = float(spot)

            work = work[
                abs(
                    work["strike"]
                    - spot
                ) <= 500
            ]

        except Exception:

            pass

    # --------------------------------------------------------
    # PRESSURE
    # --------------------------------------------------------

    work["ABS_GAMMA"] = (
        work[
            "NET_GAMMA_PRESSURE"
        ]
        .abs()
    )

    # --------------------------------------------------------
    # NORMALIZED PRESSURE
    # --------------------------------------------------------

    max_pressure = (
        work["ABS_GAMMA"]
        .max()
    )

    if max_pressure > 0:

        work["PRESSURE_PCT"] = (
            work["ABS_GAMMA"]
            /
            max_pressure
            * 100
        )

    else:

        work["PRESSURE_PCT"] = 0

    # --------------------------------------------------------
    # LABEL
    # --------------------------------------------------------

    work["ZONE"] = np.where(
        work[
            "NET_GAMMA_PRESSURE"
        ] >= 0,
        "POSITIVE",
        "NEGATIVE"
    )

    # --------------------------------------------------------
    # BASE HEATMAP
    # --------------------------------------------------------

    heatmap = (
        alt.Chart(work)
        .mark_rect(
            cornerRadius=3
        )
        .encode(

            x=alt.X(
                "strike:O",
                title="STRIKE",
                sort="ascending"
            ),

            y=alt.Y(
                "ZONE:N",
                title=None
            ),

            color=alt.Color(
                "NET_GAMMA_PRESSURE:Q",
                title="NET GAMMA"
            ),

            tooltip=[
                alt.Tooltip(
                    "strike:Q",
                    title="Strike"
                ),

                alt.Tooltip(
                    "NET_GAMMA_PRESSURE:Q",
                    title="Net Gamma",
                    format=".2f"
                ),

                alt.Tooltip(
                    "PRESSURE_PCT:Q",
                    title="Pressure %",
                    format=".1f"
                ),

                alt.Tooltip(
                    "ZONE:N",
                    title="Zone"
                ),
            ]
        )
    )

    layers = [
        heatmap
    ]

    # --------------------------------------------------------
    # SPOT LINE
    # --------------------------------------------------------

    if spot is not None:

        spot_df = pd.DataFrame(
            {
                "spot": [spot]
            }
        )

        spot_line = (
            alt.Chart(spot_df)
            .mark_rule(
                strokeWidth=2
            )
            .encode(
                x=alt.X(
                    "spot:Q"
                )
            )
        )

        layers.append(
            spot_line
        )

    # --------------------------------------------------------
    # GAMMA WALL
    # --------------------------------------------------------

    if (
        gamma_wall is not None
        and np.isfinite(
            gamma_wall
        )
    ):

        wall_df = pd.DataFrame(
            {
                "wall": [
                    float(gamma_wall)
                ]
            }
        )

        wall_line = (
            alt.Chart(wall_df)
            .mark_rule(
                strokeWidth=2,
                strokeDash=[
                    6,
                    4
                ]
            )
            .encode(
                x=alt.X(
                    "wall:Q"
                )
            )
        )

        layers.append(
            wall_line
        )

    # --------------------------------------------------------
    # GAMMA FLIP
    # --------------------------------------------------------

    if (
        gamma_flip is not None
        and np.isfinite(
            gamma_flip
        )
    ):

        flip_df = pd.DataFrame(
            {
                "flip": [
                    float(gamma_flip)
                ]
            }
        )

        flip_line = (
            alt.Chart(flip_df)
            .mark_rule(
                strokeWidth=2,
                strokeDash=[
                    3,
                    3
                ]
            )
            .encode(
                x=alt.X(
                    "flip:Q"
                )
            )
        )

        layers.append(
            flip_line
        )

    return (
        alt.layer(
            *layers
        )
        .properties(
            height=220
        )
        .interactive()
    )

    if not isinstance(
        history_df,
        pd.DataFrame
    ):
        return None

    if history_df.empty:
        return None

    required = [
        "timestamp",
        "score"
    ]

    if not all(
        col in history_df.columns
        for col in required
    ):
        return None

    chart_df = history_df.copy()

    chart_df["timestamp"] = pd.to_datetime(
        chart_df["timestamp"],
        errors="coerce"
    )

    chart_df["score"] = pd.to_numeric(
        chart_df["score"],
        errors="coerce"
    )

    chart_df = chart_df.dropna(
        subset=[
            "timestamp",
            "score"
        ]
    )

    if chart_df.empty:
        return None

    score_line = (
        alt.Chart(chart_df)
        .mark_line(
            point=True,
            strokeWidth=2
        )
        .encode(
            x=alt.X(
                "timestamp:T",
                title="TIME"
            ),

            y=alt.Y(
                "score:Q",
                title="BLAST SCORE",
                scale=alt.Scale(
                    domain=[0, 100]
                )
            ),

            tooltip=[
                alt.Tooltip(
                    "timestamp:T",
                    title="Time"
                ),

                alt.Tooltip(
                    "score:Q",
                    title="Score",
                    format=".1f"
                ),
            ]
        )
    )
    # ============================================================
# GAMMA WALL RADAR
# ============================================================

def build_gamma_wall_radar(
    gamma_df,
    spot,
    gamma_wall=None,
    gamma_flip=None,
    strikes_each_side=4
):
    """
    Build a compact Gamma Wall Radar around spot.

    Shows the strongest gamma-pressure strikes above
    and below the current NIFTY spot.
    """

    if not isinstance(
        gamma_df,
        pd.DataFrame
    ):
        return pd.DataFrame()

    if gamma_df.empty:
        return pd.DataFrame()

    required = [
        "strike",
        "NET_GAMMA_PRESSURE"
    ]

    if not all(
        col in gamma_df.columns
        for col in required
    ):
        return pd.DataFrame()

    work = gamma_df.copy()

    work["strike"] = pd.to_numeric(
        work["strike"],
        errors="coerce"
    )

    work["NET_GAMMA_PRESSURE"] = pd.to_numeric(
        work["NET_GAMMA_PRESSURE"],
        errors="coerce"
    )

    work = work.dropna(
        subset=[
            "strike",
            "NET_GAMMA_PRESSURE"
        ]
    )

    if work.empty:
        return pd.DataFrame()

    spot = float(spot)

    work["ABS_PRESSURE"] = (
        work[
            "NET_GAMMA_PRESSURE"
        ]
        .abs()
    )

    # --------------------------------------------------------
    # ABOVE SPOT
    # --------------------------------------------------------

    above = (
        work[
            work["strike"] >= spot
        ]
        .sort_values(
            "ABS_PRESSURE",
            ascending=False
        )
        .head(
            strikes_each_side
        )
    )

    # --------------------------------------------------------
    # BELOW SPOT
    # --------------------------------------------------------

    below = (
        work[
            work["strike"] < spot
        ]
        .sort_values(
            "ABS_PRESSURE",
            ascending=False
        )
        .head(
            strikes_each_side
        )
    )

    radar = pd.concat(
        [
            above,
            below
        ],
        ignore_index=True
    )

    if radar.empty:
        return pd.DataFrame()

    radar["DISTANCE"] = (
        radar["strike"]
        - spot
    )

    radar["DIRECTION"] = np.where(
        radar["DISTANCE"] > 0,
        "RESISTANCE",
        "SUPPORT"
    )

    radar["WALL"] = (
        radar["strike"]
        == gamma_wall
    )

    radar["FLIP"] = (
        radar["strike"]
        == gamma_flip
    )

    radar = (
        radar
        .sort_values(
            "strike",
            ascending=False
        )
        .reset_index(drop=True)
    )

    return radar
    # --------------------------------------------------------
    # SCORE THRESHOLD
    # --------------------------------------------------------

    threshold_df = pd.DataFrame(
        {
            "score": [65]
        }
    )

    threshold = (
        alt.Chart(threshold_df)
        .mark_rule(
            strokeDash=[
                5,
                5
            ]
        )
        .encode(
            y=alt.Y(
                "score:Q"
            )
        )
    )

    return (
        score_line
        +
        threshold
    ).properties(
        height=height
    ).interactive()

    # --------------------------------------------------------
    # CLASSIFY SCORE MOVEMENT
    # --------------------------------------------------------

    if score_change >= 20:

        state = "BLAST ACCELERATION"
        severity = "EXTREME"

    elif score_change >= 10:

        state = "BLAST BUILDING"
        severity = "HIGH"

    elif score_change >= 3:

        state = "BUILDING"
        severity = "MODERATE"

    elif score_change <= -20:

        state = "BLAST UNWIND"
        severity = "EXTREME"

    elif score_change <= -10:

        state = "BLAST UNWINDING"
        severity = "HIGH"

    elif score_change <= -3:

        state = "COOLING"
        severity = "MODERATE"

    else:

        state = "STABLE"
        severity = "LOW"

    result.update({

        "valid": True,

        "previous_score":
            previous_score,

        "score_change":
            score_change,

        "velocity_pct":
            velocity_pct,

        "state":
            state,

        "severity":
            severity,
    })

    return result

    # --------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------

    def clamp(value, low=0.0, high=100.0):

        try:

            value = float(value)

        except Exception:

            return np.nan

        if not np.isfinite(value):

            return np.nan

        return max(
            low,
            min(
                high,
                value
            )
        )

    def add_component(
        name,
        score,
        weight
    ):

        score = clamp(score)

        if not np.isfinite(score):

            return

        components[name] = {
            "score": score,
            "weight": float(weight),
        }

    components = {}

    # ========================================================
    # 1. GAMMA PRESSURE — 30%
    # ========================================================

    imbalance = gamma_blast.get(
        "gamma_imbalance"
    )

    pressure_score = np.nan

    if (
        imbalance is not None
        and np.isfinite(
            imbalance
        )
    ):

        # Absolute pressure intensity.
        #
        # 0.00 = balanced
        # 1.00 = extreme imbalance

        pressure_score = (
            abs(
                float(imbalance)
            )
            * 100
        )

    add_component(
        "GAMMA PRESSURE",
        pressure_score,
        30
    )

    # ========================================================
    # 2. GAMMA WALL — 20%
    # ========================================================

    wall_score = np.nan

    wall_distance = np.nan

    if gamma_structure:

        wall_distance = gamma_structure.get(
            "wall_distance"
        )

    if (
        wall_distance is not None
        and np.isfinite(
            wall_distance
        )
    ):

        distance = abs(
            float(wall_distance)
        )

        # Near wall = stronger signal.
        #
        # 0 points  -> 100
        # 50 points -> 75
        # 100       -> 50
        # 200+      -> 0

        wall_score = max(
            0,
            100
            -
            (
                distance
                / 2
                * 1
            )
        )

    add_component(
        "GAMMA WALL",
        wall_score,
        20
    )

    # ========================================================
    # 3. GAMMA FLIP PROXIMITY — 20%
    # ========================================================

    flip_score = np.nan

    flip_distance = np.nan

    if gamma_structure:

        flip_distance = gamma_structure.get(
            "flip_distance"
        )

    if (
        flip_distance is not None
        and np.isfinite(
            flip_distance
        )
    ):

        distance = abs(
            float(flip_distance)
        )

        flip_score = max(
            0,
            100
            -
            (
                distance
                / 2
            )
        )

    add_component(
        "GAMMA FLIP",
        flip_score,
        20
    )

    # ========================================================
    # 4. GAMMA ACCELERATION — 15%
    # ========================================================

    acceleration_score = np.nan

    if gamma_acceleration:

        acceleration_score = (
            gamma_acceleration.get(
                "score"
            )
        )

    add_component(
        "GAMMA ACCELERATION",
        acceleration_score,
        15
    )

    # ========================================================
    # 5. OI PRESSURE — 10%
    # ========================================================

    oi_score = np.nan

    if greek_metrics:

        pcr = greek_metrics.get(
            "range_oi_pcr"
        )

        if (
            pcr is not None
            and np.isfinite(
                pcr
            )
        ):

            # Distance from PCR 1.
            #
            # This is intentionally a pressure
            # component, not a bullish/bearish
            # assumption by itself.

            oi_score = min(
                100,
                abs(
                    float(pcr) - 1
                )
                * 100
            )

    add_component(
        "OI PRESSURE",
        oi_score,
        10
    )

    # ========================================================
    # 6. IV PRESSURE — 5%
    # ========================================================

    iv_score = np.nan

    if greek_metrics:

        iv_ratio = greek_metrics.get(
            "range_iv_ratio"
        )

        if (
            iv_ratio is not None
            and np.isfinite(
                iv_ratio
            )
        ):

            iv_score = min(
                100,
                abs(
                    float(iv_ratio) - 1
                )
                * 100
            )

    add_component(
        "IV PRESSURE",
        iv_score,
        5
    )

    # ========================================================
    # WEIGHTED SCORE
    # ========================================================

    weighted_sum = 0.0
    available_weight = 0.0

    for item in components.values():

        weighted_sum += (
            item["score"]
            *
            item["weight"]
        )

        available_weight += (
            item["weight"]
        )

    if available_weight <= 0:

        return result

    score = (
        weighted_sum
        /
        available_weight
    )

    score = clamp(
        score
    )

    # ========================================================
    # DIRECTION
    # ========================================================

    net_gamma = gamma_blast.get(
        "net_gamma_pressure"
    )

    direction = "NEUTRAL"

    if (
        net_gamma is not None
        and np.isfinite(
            net_gamma
        )
    ):

        if float(net_gamma) > 0:

            direction = "BULLISH PRESSURE"

        elif float(net_gamma) < 0:

            direction = "BEARISH PRESSURE"

    # ========================================================
    # SCORE STATE
    # ========================================================

    if score >= 80:

        state = "EXTREME"

    elif score >= 65:

        state = "HIGH"

    elif score >= 45:

        state = "MODERATE"

    elif score >= 25:

        state = "LOW"

    else:

        state = "QUIET"

    # ========================================================
    # FINAL
    # ========================================================

    result = {

        "valid": True,

        "score": float(
            score
        ),

        "direction": direction,

        "state": state,

        "components": components,

        "available_weight":
            available_weight,

    }

    return result

    # --------------------------------------------------------
    # GAMMA PRESSURE
    # --------------------------------------------------------

    work["gamma_pressure"] = (
        (
            work["ce_gamma"]
            *
            work["ce_oi"]
        ).abs()
        +
        (
            work["pe_gamma"]
            *
            work["pe_oi"]
        ).abs()
    )

    snapshot = (
        work
        .groupby(
            "fetch_time",
            as_index=False
        )[
            "gamma_pressure"
        ]
        .sum()
        .sort_values(
            "fetch_time"
        )
        .reset_index(drop=True)
    )

    return snapshot    
# ============================================================
# GAMMA ACCELERATION / MIGRATION ENGINE
# ============================================================

def calculate_gamma_acceleration(
    current_gamma,
    history_df=None,
    spot=None,
    atm=None
):
    """
    Compare current gamma pressure with historical snapshots.

    This detects:
        - Gamma build
        - Gamma unwind
        - Gamma acceleration
        - Gamma wall migration

    This remains a gamma-pressure proxy and is NOT dealer GEX.
    """

    result = {
        "valid": False,
        "state": "GAMMA STABLE",
        "score": 0.0,
        "current_total": np.nan,
        "previous_total": np.nan,
        "change_pct": np.nan,
        "wall_change": np.nan,
        "wall_migration": "STABLE",
    }

    if not current_gamma:
        return result

    if not current_gamma.get(
        "valid",
        False
    ):
        return result

    current_total = float(
        current_gamma.get(
            "total_gamma_pressure",
            0
        )
    )

    current_wall = float(
        current_gamma.get(
            "gamma_wall_strike",
            np.nan
        )
    )

    result["current_total"] = current_total

    if (
        history_df is None
        or not isinstance(
            history_df,
            pd.DataFrame
        )
        or history_df.empty
    ):
        return result

    hist = history_df.copy()

    # --------------------------------------------------------
    # FIND GAMMA-LIKE COLUMN
    # --------------------------------------------------------

    gamma_candidates = [
        "gamma_pressure",
        "net_gamma_pressure",
        "gamma",
        "gamma_oi",
        "net_gamma_oi_weighted"
    ]

    gamma_col = None

    for col in gamma_candidates:

        if col in hist.columns:

            gamma_col = col
            break

    # --------------------------------------------------------
    # FIND WALL COLUMN
    # --------------------------------------------------------

    wall_candidates = [
        "gamma_wall",
        "gamma_wall_strike",
        "wall_strike"
    ]

    wall_col = None

    for col in wall_candidates:

        if col in hist.columns:

            wall_col = col
            break

    # --------------------------------------------------------
    # CURRENT SNAPSHOT FALLBACK
    # --------------------------------------------------------

    # If the stored history does not contain a dedicated
    # gamma-pressure series, compare against the raw Greek
    # history when available.

    if gamma_col is None:

        if (
            "ce_gamma" in hist.columns
            and "pe_gamma" in hist.columns
            and "ce_oi" in hist.columns
            and "pe_oi" in hist.columns
        ):

            ce = (
                pd.to_numeric(
                    hist["ce_gamma"],
                    errors="coerce"
                ).fillna(0)
                *
                pd.to_numeric(
                    hist["ce_oi"],
                    errors="coerce"
                ).fillna(0)
            )

            pe = (
                pd.to_numeric(
                    hist["pe_gamma"],
                    errors="coerce"
                ).fillna(0)
                *
                pd.to_numeric(
                    hist["pe_oi"],
                    errors="coerce"
                ).fillna(0)
            )

            hist["__gamma_pressure"] = (
                ce.abs() + pe.abs()
            )

            gamma_col = "__gamma_pressure"

    if gamma_col is None:
        return result

    hist[gamma_col] = pd.to_numeric(
        hist[gamma_col],
        errors="coerce"
    )

    hist = hist.dropna(
        subset=[gamma_col]
    )

    if hist.empty:
        return result

    # --------------------------------------------------------
    # HISTORICAL GAMMA
    # --------------------------------------------------------

    historical_values = (
        hist[gamma_col]
        .abs()
        .astype(float)
    )

    previous_total = float(
        historical_values.iloc[-1]
    )

    result["previous_total"] = previous_total

    # --------------------------------------------------------
    # GAMMA CHANGE
    # --------------------------------------------------------

    if previous_total > 0:

        change_pct = (
            (
                current_total
                - previous_total
            )
            / previous_total
        ) * 100

    else:

        change_pct = np.nan

    result["change_pct"] = change_pct

    # --------------------------------------------------------
    # WALL MIGRATION
    # --------------------------------------------------------

    if wall_col is not None:

        historical_walls = pd.to_numeric(
            hist[wall_col],
            errors="coerce"
        ).dropna()

        if not historical_walls.empty:

            previous_wall = float(
                historical_walls.iloc[-1]
            )

            if np.isfinite(
                current_wall
            ):

                wall_change = (
                    current_wall
                    - previous_wall
                )

                result[
                    "wall_change"
                ] = wall_change

                if wall_change > 0:

                    result[
                        "wall_migration"
                    ] = "MOVED UP"

                elif wall_change < 0:

                    result[
                        "wall_migration"
                    ] = "MOVED DOWN"

                else:

                    result[
                        "wall_migration"
                    ] = "STABLE"

    # --------------------------------------------------------
    # BUILD / UNWIND
    # --------------------------------------------------------

    if not np.isfinite(
        change_pct
    ):

        state = "GAMMA STABLE"

    elif change_pct >= 20:

        state = "GAMMA ACCELERATION"

    elif change_pct >= 5:

        state = "GAMMA BUILDING"

    elif change_pct <= -20:

        state = "GAMMA BLAST RISK"

    elif change_pct <= -5:

        state = "GAMMA UNWINDING"

    else:

        state = "GAMMA STABLE"

    # --------------------------------------------------------
    # ACCELERATION SCORE
    # --------------------------------------------------------

    if np.isfinite(
        change_pct
    ):

        score = min(
            100,
            abs(change_pct) * 2
        )

    else:

        score = 0.0

    result["score"] = float(
        score
    )

    result["state"] = state
    result["valid"] = True

    return result

    # --------------------------------------------------------
    # CUMULATIVE GAMMA
    # --------------------------------------------------------

    work["CUMULATIVE_GAMMA"] = (
        work["NET_GAMMA_PRESSURE"]
        .cumsum()
    )

    # --------------------------------------------------------
    # GAMMA FLIP DETECTION
    # --------------------------------------------------------

    flip_strikes = []

    for i in range(
        1,
        len(work)
    ):

        previous_value = float(
            work.loc[
                i - 1,
                "CUMULATIVE_GAMMA"
            ]
        )

        current_value = float(
            work.loc[
                i,
                "CUMULATIVE_GAMMA"
            ]
        )

        if (
            previous_value < 0
            and current_value >= 0
        ) or (
            previous_value > 0
            and current_value <= 0
        ):

            flip_strikes.append(
                float(
                    work.loc[
                        i,
                        "strike"
                    ]
                )
            )

    # --------------------------------------------------------
    # SELECT NEAREST GAMMA FLIP TO SPOT
    # --------------------------------------------------------

    if flip_strikes:

        gamma_flip = min(
            flip_strikes,
            key=lambda x:
                abs(
                    x - float(spot)
                )
        )

    else:

        gamma_flip = np.nan

    # --------------------------------------------------------
    # GAMMA REGIME
    # --------------------------------------------------------

    if np.isfinite(
        gamma_flip
    ):

        if float(spot) > gamma_flip:

            regime = "POSITIVE GAMMA ZONE"

        elif float(spot) < gamma_flip:

            regime = "NEGATIVE GAMMA ZONE"

        else:

            regime = "AT GAMMA FLIP"

    else:

        # fallback to cumulative gamma at ATM
        atm_idx = min(
            range(len(work)),
            key=lambda i:
                abs(
                    float(
                        work.loc[i, "strike"]
                    ) - float(atm)
                )
        )

        atm_cumulative = float(
            work.loc[
                atm_idx,
                "CUMULATIVE_GAMMA"
            ]
        )

        if atm_cumulative > 0:

            regime = "POSITIVE GAMMA ZONE"

        elif atm_cumulative < 0:

            regime = "NEGATIVE GAMMA ZONE"

        else:

            regime = "GAMMA NEUTRAL"

    # --------------------------------------------------------
    # GAMMA WALL
    # --------------------------------------------------------

    wall_idx = (
        work[
            "NET_GAMMA_PRESSURE"
        ]
        .abs()
        .idxmax()
    )

    gamma_wall = float(
        work.loc[
            wall_idx,
            "strike"
        ]
    )

    wall_pressure = float(
        work.loc[
            wall_idx,
            "NET_GAMMA_PRESSURE"
        ]
    )

    # --------------------------------------------------------
    # DISTANCES
    # --------------------------------------------------------

    wall_distance = (
        gamma_wall
        - float(spot)
    )

    if np.isfinite(
        gamma_flip
    ):

        flip_distance = (
            gamma_flip
            - float(spot)
        )

    else:

        flip_distance = np.nan

    # --------------------------------------------------------
    # NEAREST GAMMA WALL ABOVE / BELOW
    # --------------------------------------------------------

    above = work[
        work["strike"]
        > float(spot)
    ].copy()

    below = work[
        work["strike"]
        < float(spot)
    ].copy()

    if not above.empty:

        above_idx = (
            above[
                "NET_GAMMA_PRESSURE"
            ]
            .abs()
            .idxmax()
        )

        wall_above = float(
            above.loc[
                above_idx,
                "strike"
            ]
        )

    else:

        wall_above = np.nan

    if not below.empty:

        below_idx = (
            below[
                "NET_GAMMA_PRESSURE"
            ]
            .abs()
            .idxmax()
        )

        wall_below = float(
            below.loc[
                below_idx,
                "strike"
            ]
        )

    else:

        wall_below = np.nan

    # --------------------------------------------------------
    # BLAST ZONE
    # --------------------------------------------------------

    if np.isfinite(
        gamma_flip
    ):

        distance_from_flip = abs(
            float(spot)
            - gamma_flip
        )

        if distance_from_flip <= 50:

            blast_zone = "GAMMA FLIP ZONE"

        elif distance_from_flip <= 100:

            blast_zone = "GAMMA TRANSITION"

        else:

            blast_zone = "GAMMA TREND ZONE"

    else:

        blast_zone = "GAMMA UNDEFINED"

    return {

        "valid": True,

        "data": work,

        "gamma_flip":
            gamma_flip,

        "gamma_wall":
            gamma_wall,

        "wall_pressure":
            wall_pressure,

        "wall_distance":
            wall_distance,

        "flip_distance":
            flip_distance,

        "wall_above":
            wall_above,

        "wall_below":
            wall_below,

        "regime":
            regime,

        "blast_zone":
            blast_zone
    }

def gamma_blast_chart(
    gamma_result,
    height=380
):

    if not gamma_result:
        return None

    if not gamma_result.get(
        "valid",
        False
    ):
        return None

    data = gamma_result.get(
        "data"
    )

    if not isinstance(
        data,
        pd.DataFrame
    ):
        return None

    if data.empty:
        return None

    chart_df = data[
        [
            "strike",
            "CE_GAMMA_PRESSURE",
            "PE_GAMMA_PRESSURE",
            "NET_GAMMA_PRESSURE"
        ]
    ].copy()

    chart_df = chart_df.melt(
        id_vars=["strike"],
        value_vars=[
            "CE_GAMMA_PRESSURE",
            "PE_GAMMA_PRESSURE",
            "NET_GAMMA_PRESSURE"
        ],
        var_name="TYPE",
        value_name="GAMMA"
    )

    chart_df["TYPE"] = chart_df[
        "TYPE"
    ].map({

        "CE_GAMMA_PRESSURE":
            "CE GAMMA",

        "PE_GAMMA_PRESSURE":
            "PE GAMMA",

        "NET_GAMMA_PRESSURE":
            "NET GAMMA",

    })

    return (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(

            x=alt.X(
                "strike:O",
                title="STRIKE"
            ),

            y=alt.Y(
                "GAMMA:Q",
                title="GAMMA PRESSURE",
                scale=alt.Scale(
                    zero=True
                )
            ),

            color=alt.Color(
                "TYPE:N",
                scale=alt.Scale(
                    domain=[
                        "CE GAMMA",
                        "PE GAMMA",
                        "NET GAMMA"
                    ],
                    range=[
                        "#ff4654",
                        "#00d995",
                        "#f1c75b"
                    ]
                ),
                legend=alt.Legend(
                    title="GAMMA"
                )
            ),

            tooltip=[
                alt.Tooltip(
                    "strike:Q",
                    title="Strike",
                    format=",.0f"
                ),

                alt.Tooltip(
                    "TYPE:N",
                    title="Type"
                ),

                alt.Tooltip(
                    "GAMMA:Q",
                    title="Gamma",
                    format=",.4f"
                ),
            ],
        )
        .properties(
            height=height
        )
        .interactive()
    )
# ============================================================
# STEP 12 — HISTORICAL GREEK INTELLIGENCE ENGINE
# ============================================================

def historical_greek_intelligence(
    history_df
):
    """
    Converts historical Greek snapshots into
    momentum / acceleration / regime information.

    Expected columns:
        timestamp
        delta
        gamma
        theta
        vega

    The function is intentionally tolerant of
    alternate historical column names.
    """

    result = {
        "valid": False,
        "data": pd.DataFrame(),

        "delta": {},
        "gamma": {},
        "theta": {},
        "vega": {}
    }

    if history_df is None:
        return result

    if not isinstance(
        history_df,
        pd.DataFrame
    ):
        return result

    if history_df.empty:
        return result

    work = history_df.copy()

    # --------------------------------------------------------
    # TIMESTAMP
    # --------------------------------------------------------

    timestamp_candidates = [
        "timestamp",
        "time",
        "datetime",
        "date"
    ]

    timestamp_column = None

    for column in timestamp_candidates:

        if column in work.columns:

            timestamp_column = column
            break

    if timestamp_column is not None:

        work["timestamp"] = pd.to_datetime(
            work[timestamp_column],
            errors="coerce"
        )

    else:

        work["timestamp"] = pd.NaT

    # --------------------------------------------------------
    # COLUMN DISCOVERY
    # --------------------------------------------------------

    greek_aliases = {

        "delta": [
            "delta",
            "atm_delta",
            "net_delta"
        ],

        "gamma": [
            "gamma",
            "atm_gamma",
            "net_gamma"
        ],

        "theta": [
            "theta",
            "atm_theta",
            "net_theta"
        ],

        "vega": [
            "vega",
            "atm_vega",
            "net_vega"
        ]
    }

    resolved = {}

    for greek, aliases in greek_aliases.items():

        for alias in aliases:

            if alias in work.columns:

                resolved[
                    greek
                ] = alias

                break

    # --------------------------------------------------------
    # REQUIRE AT LEAST ONE GREEK
    # --------------------------------------------------------

    if not resolved:
        return result

    # --------------------------------------------------------
    # NORMALIZE
    # --------------------------------------------------------

    for greek, column in resolved.items():

        work[greek] = pd.to_numeric(
            work[column],
            errors="coerce"
        )

    work = work.sort_values(
        "timestamp"
    )

    # --------------------------------------------------------
    # INTELLIGENCE CALCULATION
    # --------------------------------------------------------

    for greek in [
        "delta",
        "gamma",
        "theta",
        "vega"
    ]:

        if greek not in work.columns:
            continue

        series = (
            pd.to_numeric(
                work[greek],
                errors="coerce"
            )
            .dropna()
        )

        if series.empty:
            continue

        current = float(
            series.iloc[-1]
        )

        previous = (
            float(series.iloc[-2])
            if len(series) >= 2
            else current
        )

        previous_2 = (
            float(series.iloc[-3])
            if len(series) >= 3
            else previous
        )

        change = (
            current
            - previous
        )

        acceleration = (
            current
            - 2 * previous
            + previous_2
        )

        # ----------------------------------------------------
        # PERCENT CHANGE
        # ----------------------------------------------------

        if abs(previous) > 1e-12:

            pct_change = (
                change
                / abs(previous)
            ) * 100

        else:

            pct_change = 0.0

        # ----------------------------------------------------
        # MOMENTUM
        # ----------------------------------------------------

        if change > 0:

            momentum = "RISING"

        elif change < 0:

            momentum = "FALLING"

        else:

            momentum = "FLAT"

        # ----------------------------------------------------
        # ACCELERATION
        # ----------------------------------------------------

        if acceleration > 0:

            acceleration_state = "ACCELERATING"

        elif acceleration < 0:

            acceleration_state = "DECELERATING"

        else:

            acceleration_state = "STABLE"

        # ----------------------------------------------------
        # REGIME
        # ----------------------------------------------------

        if (
            change > 0
            and acceleration > 0
        ):

            regime = "EXPANDING"

        elif (
            change > 0
            and acceleration <= 0
        ):

            regime = "RISING"

        elif (
            change < 0
            and acceleration < 0
        ):

            regime = "CONTRACTING"

        elif (
            change < 0
            and acceleration >= 0
        ):

            regime = "FALLING"

        else:

            regime = "STABLE"

        result[
            greek
        ] = {

            "current": current,

            "previous": previous,

            "change": change,

            "pct_change": pct_change,

            "acceleration": acceleration,

            "momentum": momentum,

            "acceleration_state":
                acceleration_state,

            "regime": regime
        }

    # --------------------------------------------------------
    # CLEAN HISTORY DATA
    # --------------------------------------------------------

    history_columns = [
        "timestamp"
    ]

    for greek in [
        "delta",
        "gamma",
        "theta",
        "vega"
    ]:

        if greek in work.columns:

            history_columns.append(
                greek
            )

    history = work[
        history_columns
    ].copy()

    result["data"] = history

    result["valid"] = (
        len(history) > 0
    )

    return result

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
# ============================================================
# MULTI-TIMEFRAME REGIME PANEL
# ============================================================

def render_mtf_regime_panel():

    try:

        mtf = get_multi_timeframe_signal()

        regime = classify_multi_timeframe_regime(mtf)

    except Exception as e:

        st.error(f"MTF engine error: {e}")
        return

    overall_signal = mtf.get(
        "overall_signal",
        "NO DATA"
    )

    overall_score = mtf.get(
        "overall_score",
        0
    )

    alignment = mtf.get(
        "alignment",
        "NO DATA"
    )

    regime_name = regime.get(
        "regime",
        "NO DATA"
    )

    bias = regime.get(
        "bias",
        "NEUTRAL"
    )

    risk = regime.get(
        "risk",
        "UNKNOWN"
    )

    description = regime.get(
        "description",
        ""
    )

    # --------------------------------------------------------
    # SIGNAL COLOR
    # --------------------------------------------------------

    if "BUY" in overall_signal:

        signal_color = "#00e59a"

    elif "SELL" in overall_signal:

        signal_color = "#ff5c67"

    else:

        signal_color = "#f1c75b"

    # --------------------------------------------------------
    # REGIME COLOR
    # --------------------------------------------------------

    if "BULLISH" in regime_name:

        regime_color = "#00e59a"

    elif "BEARISH" in regime_name:

        regime_color = "#ff5c67"

    else:

        regime_color = "#f1c75b"

    # --------------------------------------------------------
    # RISK COLOR
    # --------------------------------------------------------

    if risk == "LOWER":

        risk_color = "#00e59a"

    elif risk == "HIGHER":

        risk_color = "#ff5c67"

    else:

        risk_color = "#f1c75b"

    # ========================================================
    # HEADER
    # ========================================================

    st.html(
        dedent(f"""
        <div style="
            background:#11151c;
            border:1px solid #292e38;
            border-radius:10px;
            padding:10px 14px;
            margin-top:6px;
            margin-bottom:8px;
        ">

        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
        ">

            <div>
                <div style="
                    color:#8f98a8;
                    font-size:10px;
                    font-weight:800;
                    letter-spacing:1px;
                ">
                    MULTI-TIMEFRAME MARKET REGIME
                </div>

                <div style="
                    color:{regime_color};
                    font-size:20px;
                    font-weight:900;
                    margin-top:3px;
                ">
                    {regime_name}
                </div>

                <div style="
                    color:#8f98a8;
                    font-size:11px;
                    margin-top:2px;
                ">
                    {description}
                </div>
            </div>

            <div style="
                text-align:right;
                min-width:130px;
            ">

                <div style="
                    color:#8f98a8;
                    font-size:10px;
                    font-weight:700;
                ">
                    OVERALL SIGNAL
                </div>

                <div style="
                    color:{signal_color};
                    font-size:18px;
                    font-weight:900;
                ">
                    {overall_signal}
                </div>

                <div style="
                    color:#f5f7fa;
                    font-size:11px;
                ">
                    SCORE {overall_score:+.2f}
                </div>

            </div>

        </div>

        </div>
        """),
    )

    # ========================================================
    # TIMEFRAME DATA
    # ========================================================

    results = mtf.get(
        "timeframes",
        {}
    )

    timeframe_order = [
        ("1D", "HIGHER TF"),
        ("1H", "MEDIUM TF"),
        ("15m", "INTRADAY"),
        ("5m", "FAST")
    ]

    cols = st.columns(
        6,
        gap="small"
    )

    # --------------------------------------------------------
    # TIMEFRAME CARDS
    # --------------------------------------------------------

    for col, (tf, label) in zip(
        cols[:4],
        timeframe_order
    ):

        data = results.get(
            tf,
            {}
        )

        signal = data.get(
            "signal",
            "NO DATA"
        )

        score = data.get(
            "score",
            0
        )

        price = data.get(
            "price"
        )

        supertrend = data.get(
            "supertrend",
            "NO DATA"
        )

        adx_strength = data.get(
            "adx_strength",
            "NO DATA"
        )

        if "BUY" in signal:

            color = "#00e59a"

        elif "SELL" in signal:

            color = "#ff5c67"

        else:

            color = "#f1c75b"

        price_text = (
            "-"
            if price is None
            else f"{price:,.2f}"
        )

        st.html(
            dedent(f"""
            <div style="
                background:#11151c;
                border:1px solid #292e38;
                border-radius:8px;
                padding:8px 10px;
                min-height:82px;
            ">

                <div style="
                    color:#737d8d;
                    font-size:9px;
                    font-weight:800;
                    letter-spacing:.7px;
                ">
                    {label}
                </div>

                <div style="
                    color:#f5f7fa;
                    font-size:11px;
                    margin-top:2px;
                ">
                    {tf}
                </div>

                <div style="
                    color:{color};
                    font-size:15px;
                    font-weight:900;
                    margin-top:3px;
                ">
                    {signal}
                </div>

                <div style="
                    color:#8f98a8;
                    font-size:9px;
                    margin-top:2px;
                ">
                    SCORE {score:+.1f}
                    &nbsp; | &nbsp;
                    ST {supertrend}
                </div>

            </div>
            """),
        )

    # ========================================================
    # SCORE / ALIGNMENT / RISK
    # ========================================================

    with cols[4]:

        st.metric(
            "MTF SCORE",
            f"{overall_score:+.2f}"
        )

    with cols[5]:

        st.html(
            dedent(f"""
            <div style="
                background:#11151c;
                border:1px solid #292e38;
                border-radius:8px;
                padding:8px 10px;
                min-height:82px;
            ">

                <div style="
                    color:#737d8d;
                    font-size:9px;
                    font-weight:800;
                ">
                    ALIGNMENT
                </div>

                <div style="
                    color:{regime_color};
                    font-size:13px;
                    font-weight:900;
                    margin-top:6px;
                ">
                    {alignment}
                </div>

                <div style="
                    color:{risk_color};
                    font-size:10px;
                    font-weight:800;
                    margin-top:5px;
                ">
                    RISK: {risk}
                </div>

            </div>
            """),
        )
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
            xOffset=alt.XOffset("Type:N"),
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
            xOffset=alt.XOffset("Type:N"),
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
            xOffset=alt.XOffset("Type:N"),
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
# ============================================================
# STEP 9 — ADVANCED OPTION CHAIN INTELLIGENCE ENGINE
# ============================================================

def calculate_option_chain_intelligence(df, atm):
    """
    Advanced strike-level intelligence layer.

    Uses:
        OI
        OI Change
        Volume
        IV
        LTP

    This is a market-structure analytics layer.
    It is NOT dealer positioning / guaranteed trade prediction.
    """

    result = {
        "valid": False,

        "call_wall": np.nan,
        "put_wall": np.nan,

        "call_oi": 0.0,
        "put_oi": 0.0,

        "call_oi_change": 0.0,
        "put_oi_change": 0.0,

        "call_volume": 0.0,
        "put_volume": 0.0,

        "max_call_volume_strike": np.nan,
        "max_put_volume_strike": np.nan,

        "max_call_oi_change_strike": np.nan,
        "max_put_oi_change_strike": np.nan,

        "call_iv_max_strike": np.nan,
        "put_iv_max_strike": np.nan,

        "pcr": np.nan,

        "structure": "NEUTRAL",
        "bias": "NEUTRAL",
        "strength": 0.0,

        "atm": atm,
        "atm_row": None
    }

    if not isinstance(df, pd.DataFrame):
        return result

    if df.empty:
        return result

    required = [
        "strike",
        "ce_oi",
        "pe_oi"
    ]

    if not all(
        column in df.columns
        for column in required
    ):
        return result

    work = df.copy()

    # --------------------------------------------------------
    # NUMERIC NORMALIZATION
    # --------------------------------------------------------

    numeric_columns = [
        "strike",
        "ce_oi",
        "pe_oi",
        "ce_oi_change",
        "pe_oi_change",
        "ce_volume",
        "pe_volume",
        "ce_iv",
        "pe_iv",
        "ce_ltp",
        "pe_ltp"
    ]

    for column in numeric_columns:

        if column in work.columns:

            work[column] = pd.to_numeric(
                work[column],
                errors="coerce"
            )

    work = work.dropna(
        subset=["strike"]
    )

    if work.empty:
        return result

    # --------------------------------------------------------
    # OPTIONAL COLUMNS
    # --------------------------------------------------------

    for column in [
        "ce_oi_change",
        "pe_oi_change",
        "ce_volume",
        "pe_volume",
        "ce_iv",
        "pe_iv",
        "ce_ltp",
        "pe_ltp"
    ]:

        if column not in work.columns:

            work[column] = 0.0

    # --------------------------------------------------------
    # TOTAL STRUCTURE
    # --------------------------------------------------------

    call_oi = work["ce_oi"].fillna(0).sum()
    put_oi = work["pe_oi"].fillna(0).sum()

    call_oi_change = (
        work["ce_oi_change"]
        .fillna(0)
        .sum()
    )

    put_oi_change = (
        work["pe_oi_change"]
        .fillna(0)
        .sum()
    )

    call_volume = (
        work["ce_volume"]
        .fillna(0)
        .sum()
    )

    put_volume = (
        work["pe_volume"]
        .fillna(0)
        .sum()
    )

    # --------------------------------------------------------
    # PCR
    # --------------------------------------------------------

    if call_oi > 0:

        pcr = (
            put_oi
            / call_oi
        )

    else:

        pcr = np.nan

    # --------------------------------------------------------
    # OI WALLS
    # --------------------------------------------------------

    try:

        call_wall = float(
            work.loc[
                work["ce_oi"].idxmax(),
                "strike"
            ]
        )

    except Exception:

        call_wall = np.nan

    try:

        put_wall = float(
            work.loc[
                work["pe_oi"].idxmax(),
                "strike"
            ]
        )

    except Exception:

        put_wall = np.nan

    # --------------------------------------------------------
    # VOLUME CONCENTRATION
    # --------------------------------------------------------

    try:

        max_call_volume_strike = float(
            work.loc[
                work["ce_volume"].idxmax(),
                "strike"
            ]
        )

    except Exception:

        max_call_volume_strike = np.nan

    try:

        max_put_volume_strike = float(
            work.loc[
                work["pe_volume"].idxmax(),
                "strike"
            ]
        )

    except Exception:

        max_put_volume_strike = np.nan

    # --------------------------------------------------------
    # OI CHANGE CONCENTRATION
    # --------------------------------------------------------

    try:

        max_call_oi_change_strike = float(
            work.loc[
                work["ce_oi_change"].idxmax(),
                "strike"
            ]
        )

    except Exception:

        max_call_oi_change_strike = np.nan

    try:

        max_put_oi_change_strike = float(
            work.loc[
                work["pe_oi_change"].idxmax(),
                "strike"
            ]
        )

    except Exception:

        max_put_oi_change_strike = np.nan

    # --------------------------------------------------------
    # IV CONCENTRATION
    # --------------------------------------------------------

    try:

        call_iv_max_strike = float(
            work.loc[
                work["ce_iv"].idxmax(),
                "strike"
            ]
        )

    except Exception:

        call_iv_max_strike = np.nan

    try:

        put_iv_max_strike = float(
            work.loc[
                work["pe_iv"].idxmax(),
                "strike"
            ]
        )

    except Exception:

        put_iv_max_strike = np.nan

    # --------------------------------------------------------
    # STRUCTURE BIAS
    # --------------------------------------------------------

    # Positive PUT ΔOI relative to CALL ΔOI
    # is treated as stronger put-side buildup.
    #
    # Positive CALL ΔOI relative to PUT ΔOI
    # is treated as stronger call-side buildup.
    #
    # This is a rule-based interpretation.

    oi_change_diff = (
        put_oi_change
        - call_oi_change
    )

    volume_diff = (
        put_volume
        - call_volume
    )

    pcr_score = 0.0

    if np.isfinite(pcr):

        if pcr >= 1.20:

            pcr_score = 1.0

        elif pcr >= 1.05:

            pcr_score = 0.5

        elif pcr <= 0.80:

            pcr_score = -1.0

        elif pcr <= 0.95:

            pcr_score = -0.5

    oi_score = 0.0

    if (
        put_oi_change > 0
        and call_oi_change < 0
    ):

        oi_score = 1.0

    elif (
        call_oi_change > 0
        and put_oi_change < 0
    ):

        oi_score = -1.0

    elif (
        put_oi_change > call_oi_change
    ):

        oi_score = 0.5

    elif (
        call_oi_change > put_oi_change
    ):

        oi_score = -0.5

    volume_score = 0.0

    if put_volume > call_volume * 1.20:

        volume_score = 0.5

    elif call_volume > put_volume * 1.20:

        volume_score = -0.5

    composite = (
        pcr_score * 0.35
        + oi_score * 0.45
        + volume_score * 0.20
    )

    # --------------------------------------------------------
    # CLASSIFICATION
    # --------------------------------------------------------

    if composite >= 0.60:

        bias = "BULLISH"
        structure = "PUT DOMINANT"

    elif composite >= 0.20:

        bias = "MILD BULLISH"
        structure = "PUT LEAN"

    elif composite <= -0.60:

        bias = "BEARISH"
        structure = "CALL DOMINANT"

    elif composite <= -0.20:

        bias = "MILD BEARISH"
        structure = "CALL LEAN"

    else:

        bias = "NEUTRAL"
        structure = "BALANCED"

    strength = min(
        100.0,
        abs(composite) * 100.0
    )

    # --------------------------------------------------------
    # ATM ROW
    # --------------------------------------------------------

    atm_row = None

    try:

        atm_index = (
            work["strike"]
            - float(atm)
        ).abs().idxmin()

        atm_row = work.loc[
            atm_index
        ].to_dict()

    except Exception:

        atm_row = None

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    result.update({

        "valid": True,

        "call_wall": call_wall,
        "put_wall": put_wall,

        "call_oi": float(call_oi),
        "put_oi": float(put_oi),

        "call_oi_change": float(
            call_oi_change
        ),

        "put_oi_change": float(
            put_oi_change
        ),

        "call_volume": float(
            call_volume
        ),

        "put_volume": float(
            put_volume
        ),

        "max_call_volume_strike":
            max_call_volume_strike,

        "max_put_volume_strike":
            max_put_volume_strike,

        "max_call_oi_change_strike":
            max_call_oi_change_strike,

        "max_put_oi_change_strike":
            max_put_oi_change_strike,

        "call_iv_max_strike":
            call_iv_max_strike,

        "put_iv_max_strike":
            put_iv_max_strike,

        "pcr": pcr,

        "structure": structure,

        "bias": bias,

        "strength": float(
            strength
        ),

        "atm_row": atm_row

    })

    return result
def make_option_table(df, atm, range_count, table_view="MARKET DATA"):

    data = ensure_greek_columns(
        prepare_chart_data(
            df,
            atm,
            range_count
        )
    )

    market_columns = [
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

    greek_columns = [
        "ce_iv",
        "ce_delta",
        "ce_gamma",
        "ce_theta",
        "ce_vega",
        "ce_pop",
        "strike",
        "pe_pop",
        "pe_vega",
        "pe_theta",
        "pe_gamma",
        "pe_delta",
        "pe_iv"
    ]

    full_columns = [
        "ce_ltp",
        "ce_oi",
        "ce_oi_change",
        "ce_volume",
        "ce_iv",
        "ce_delta",
        "ce_gamma",
        "ce_theta",
        "ce_vega",
        "ce_pop",
        "strike",
        "pe_pop",
        "pe_vega",
        "pe_theta",
        "pe_gamma",
        "pe_delta",
        "pe_iv",
        "pe_volume",
        "pe_oi_change",
        "pe_oi",
        "pe_ltp"
    ]

    if table_view == "GREEKS":
        columns = greek_columns
    elif table_view == "FULL ANALYTICS":
        columns = full_columns
    else:
        columns = market_columns

    columns = [
        column
        for column in columns
        if column in data.columns
    ]

    table = data[columns].copy()

    rename = {
        "ce_oi": "CE OI",
        "ce_oi_change": "CE ΔOI",
        "ce_volume": "CE Volume",
        "ce_iv": "CE IV",
        "ce_ltp": "CE LTP",
        "ce_delta": "CE Delta",
        "ce_gamma": "CE Gamma",
        "ce_theta": "CE Theta",
        "ce_vega": "CE Vega",
        "ce_pop": "CE POP",
        "ce_rho": "CE Rho",

        "strike": "STRIKE",

        "pe_ltp": "PE LTP",
        "pe_iv": "PE IV",
        "pe_volume": "PE Volume",
        "pe_oi_change": "PE ΔOI",
        "pe_oi": "PE OI",
        "pe_delta": "PE Delta",
        "pe_gamma": "PE Gamma",
        "pe_theta": "PE Theta",
        "pe_vega": "PE Vega",
        "pe_pop": "PE POP",
        "pe_rho": "PE Rho"
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

# --------------------------------------------------------
# MULTI-TIMEFRAME SIGNAL ENGINE
# --------------------------------------------------------

try:

    mtf_result = get_multi_timeframe_signal()

    mtf_regime = classify_multi_timeframe_regime(
        mtf_result
    )

except Exception as e:

    st.error(
        f"Multi-timeframe engine error: {e}"
    )

    mtf_result = {
        "overall_score": 0,
        "overall_signal": "NO DATA",
        "higher_tf": "NO DATA",
        "medium_tf": "NO DATA",
        "intraday_tf": "NO DATA",
        "fast_tf": "NO DATA",
        "alignment": "NO DATA",
        "bullish_count": 0,
        "bearish_count": 0,
        "neutral_count": 0,
    }

    mtf_regime = {
        "regime": "NO DATA",
        "bias": "NEUTRAL",
        "description": "No MTF data available.",
        "risk": "UNKNOWN",
    }
# --------------------------------------------------------
# MTF MARKET REGIME PANEL
# --------------------------------------------------------

regime_name = mtf_regime.get(
    "regime",
    "NO DATA"
)

regime_bias = mtf_regime.get(
    "bias",
    "NEUTRAL"
)

regime_risk = mtf_regime.get(
    "risk",
    "UNKNOWN"
)

overall_signal = mtf_result.get(
    "overall_signal",
    "NO DATA"
)

overall_score = mtf_result.get(
    "overall_score",
    0
)

alignment = mtf_result.get(
    "alignment",
    "NO DATA"
)

bullish_count = mtf_result.get(
    "bullish_count",
    0
)

bearish_count = mtf_result.get(
    "bearish_count",
    0
)

neutral_count = mtf_result.get(
    "neutral_count",
    0
)

regime_color = {
    "BULLISH": "#00e59a",
    "SHORT-TERM BULLISH": "#00e59a",
    "BEARISH": "#ff5c67",
    "SHORT-TERM BEARISH": "#ff5c67",
    "NEUTRAL": "#f1c75b",
}.get(
    regime_bias,
    "#f1c75b"
)

signal_color = {
    "STRONG BUY": "#00e59a",
    "BUY": "#00e59a",
    "WEAK BUY": "#65d6a4",
    "STRONG SELL": "#ff5c67",
    "SELL": "#ff5c67",
    "WEAK SELL": "#ff8a8a",
    "NEUTRAL": "#f1c75b",
}.get(
    overall_signal,
    "#f1c75b"
)

st.html(
    dedent(f"""
    <div style="
        background:#11151c;
        border:1px solid #292e38;
        border-radius:10px;
        padding:12px 14px;
        margin-bottom:10px;
    ">

        <div style="
            color:#8f98a8;
            font-size:11px;
            font-weight:800;
            letter-spacing:0.8px;
            margin-bottom:10px;
        ">
            NIFTY MARKET REGIME
        </div>

        <div style="
            display:grid;
            grid-template-columns:
                1.5fr 1fr 1fr 1fr 1fr 1.4fr;
            gap:8px;
        ">

            <div>
                <div style="
                    color:#737c8c;
                    font-size:10px;
                    font-weight:700;
                ">
                    REGIME
                </div>

                <div style="
                    color:{regime_color};
                    font-size:17px;
                    font-weight:800;
                    margin-top:3px;
                ">
                    {regime_name}
                </div>
            </div>

            <div>
                <div style="
                    color:#737c8c;
                    font-size:10px;
                    font-weight:700;
                ">
                    1D
                </div>

                <div style="
                    color:#f5f7fa;
                    font-size:14px;
                    font-weight:800;
                    margin-top:5px;
                ">
                    {mtf_result.get("higher_tf", "NO DATA")}
                </div>
            </div>

            <div>
                <div style="
                    color:#737c8c;
                    font-size:10px;
                    font-weight:700;
                ">
                    1H
                </div>

                <div style="
                    color:#f5f7fa;
                    font-size:14px;
                    font-weight:800;
                    margin-top:5px;
                ">
                    {mtf_result.get("medium_tf", "NO DATA")}
                </div>
            </div>

            <div>
                <div style="
                    color:#737c8c;
                    font-size:10px;
                    font-weight:700;
                ">
                    15M
                </div>

                <div style="
                    color:#f5f7fa;
                    font-size:14px;
                    font-weight:800;
                    margin-top:5px;
                ">
                    {mtf_result.get("intraday_tf", "NO DATA")}
                </div>
            </div>

            <div>
                <div style="
                    color:#737c8c;
                    font-size:10px;
                    font-weight:700;
                ">
                    5M
                </div>

                <div style="
                    color:#f5f7fa;
                    font-size:14px;
                    font-weight:800;
                    margin-top:5px;
                ">
                    {mtf_result.get("fast_tf", "NO DATA")}
                </div>
            </div>

            <div>
                <div style="
                    color:#737c8c;
                    font-size:10px;
                    font-weight:700;
                ">
                    MTF SCORE
                </div>

                <div style="
                    color:{signal_color};
                    font-size:17px;
                    font-weight:800;
                    margin-top:3px;
                ">
                    {overall_score:+.2f}
                    <span style="
                        font-size:11px;
                        margin-left:5px;
                    ">
                        {overall_signal}
                    </span>
                </div>
            </div>

        </div>

        <div style="
            border-top:1px solid #252a33;
            margin-top:10px;
            padding-top:8px;
            display:flex;
            justify-content:space-between;
            color:#8f98a8;
            font-size:11px;
        ">

            <span>
                ALIGNMENT:
                <b style="color:#f5f7fa;">
                    {alignment}
                </b>
            </span>

            <span>
                BULL:
                <b style="color:#00e59a;">
                    {bullish_count}
                </b>
                &nbsp;&nbsp;

                BEAR:
                <b style="color:#ff5c67;">
                    {bearish_count}
                </b>
                &nbsp;&nbsp;

                NEUTRAL:
                <b style="color:#f1c75b;">
                    {neutral_count}
                </b>
            </span>

            <span>
                BIAS:
                <b style="color:{regime_color};">
                    {regime_bias}
                </b>
                &nbsp;&nbsp;|&nbsp;&nbsp;

                RISK:
                <b style="color:#f5f7fa;">
                    {regime_risk}
                </b>
            </span>

        </div>

    </div>
    """),
)
# ============================================================
# LOAD DATA
# ============================================================

df = load_data(CSV_PATH)

if not df.empty:
    df = ensure_greek_columns(df)

if df.empty:
    st.error("Option-chain CSV not found.")
    st.info("Make sure this file exists: data/nifty_option_chain.csv")
    st.stop()

# ============================================================
# MARKET STRUCTURE ENGINE
# ============================================================

market_structure = calculate_market_structure(df)
# ============================================================
# MARKET STRUCTURE HEADER
# ============================================================

st.html(
    """
    <div class="dashboard-panel-header" style="margin-top:2px;">

        <div class="dashboard-panel-title">
            MARKET STRUCTURE
        </div>

        <div class="dashboard-panel-meta">
            NIFTY 50 • LIVE MARKET MAP
        </div>

    </div>
    """
)

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
# GLOBAL TERMINAL HEADER
# ============================================================

bias = metrics.get(
    "market_bias",
    "NEUTRAL"
)

pcr = metrics.get(
    "overall_pcr",
    np.nan
)

score = metrics.get(
    "score",
    0
)

support_level = metrics.get(
    "support",
    None
)

resistance_level = metrics.get(
    "resistance",
    None
)

if bias == "BULLISH":
    bias_class = "terminal-bull"
elif bias == "BEARISH":
    bias_class = "terminal-bear"
else:
    bias_class = "terminal-neutral"


st.html(
    f"""
    <div class="terminal-header">

        <div class="terminal-brand">
            <div class="terminal-logo">
                N
            </div>

            <div>
                <div class="terminal-title">
                    NIFTY TERMINAL
                </div>

                <div class="terminal-subtitle">
                    OPTIONS • ALGO • MARKET INTELLIGENCE
                </div>
            </div>
        </div>


        <div class="terminal-market-strip">

            <div class="terminal-market-item primary">
                <div class="terminal-market-label">
                    NIFTY 50
                </div>

                <div class="terminal-market-value">
                    {spot:,.2f}
                </div>
            </div>


            <div class="terminal-market-item">
                <div class="terminal-market-label">
                    ATM
                </div>

                <div class="terminal-market-value">
                    {atm:,.0f}
                </div>
            </div>


            <div class="terminal-market-item">
                <div class="terminal-market-label">
                    PCR
                </div>

                <div class="terminal-market-value">
                    {pcr:.3f}
                </div>
            </div>


            <div class="terminal-market-item">
                <div class="terminal-market-label">
                    EXPIRY
                </div>

                <div class="terminal-market-value compact">
                    {expiry}
                </div>
            </div>


            <div class="terminal-market-item">
                <div class="terminal-market-label">
                    BIAS
                </div>

                <div class="terminal-market-value {bias_class}">
                    {bias}
                </div>
            </div>


            <div class="terminal-live">

                <div class="terminal-live-dot">
                    ●
                </div>

                <div>
                    <div class="terminal-live-text">
                        LIVE
                    </div>

                    <div class="terminal-time">
                        {datetime.now().strftime("%H:%M:%S")}
                    </div>
                </div>

            </div>

        </div>

    </div>
    """
)
# ============================================================
# TAB 1 — DASHBOARD
# ============================================================
# ============================================================
# NAVIGATION
# ============================================================

tabs = st.tabs(
    [
        "DASH",
        "CHAIN",
        "OI",
        "VOL",
        "IV",
        "GREEKS",
        "PCR",
        "SIGNALS",
        "STRATEGY",
        "BACKTEST",
        "HISTORY",
        "CHART",
        "FUSION",
    ]
)

if True:



    # ============================================================
    # EXPIRY + AUTO REFRESH + MANUAL REFRESH
    # ============================================================

    @st.cache_data(ttl=300)
    def load_expiries():
        return get_available_expiries()


    available_expiries = load_expiries()

    if not available_expiries:
        st.error(
            "No NIFTY option expiries are available from the Upstox data source."
        )
        st.stop()


    # ------------------------------------------------------------
    # SELECTED EXPIRY
    # ------------------------------------------------------------

    if (
        "selected_expiry" not in st.session_state
        or st.session_state.selected_expiry not in available_expiries
    ):

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


# Close Dashboard-only header/control scope before the global auto-refresh engine.

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
            
with tabs[0]:
    pass

    # --------------------------------------------------------
    # MARKET CARDS
        # --------------------------------------------------------

        # --------------------------------------------------------
# MARKET SNAPSHOT
# --------------------------------------------------------

dashboard_bias = metrics["market_bias"]
dashboard_score = metrics["score"]

if dashboard_bias == "BULLISH":
    dashboard_bias_class = "bullish"
elif dashboard_bias == "BEARISH":
    dashboard_bias_class = "bearish"
else:
    dashboard_bias_class = "neutral"

st.html(
    f"""
    <div class="dashboard-panel">

        <div class="dashboard-panel-header">

            <div class="dashboard-panel-title">
                MARKET SNAPSHOT
            </div>

            <div class="dashboard-panel-meta">
                NIFTY 50 • LIVE
            </div>

        </div>


        <div class="dashboard-grid">

            <div class="dashboard-stat">

                <div class="dashboard-stat-label">
                    NIFTY SPOT
                </div>

                <div class="dashboard-stat-value">
                    {format_price(spot)}
                </div>

            </div>


            <div class="dashboard-stat">

                <div class="dashboard-stat-label">
                    ATM
                </div>

                <div class="dashboard-stat-value">
                    {format_integer(atm)}
                </div>

            </div>


            <div class="dashboard-stat">

                <div class="dashboard-stat-label">
                    EXPIRY
                </div>

                <div class="dashboard-stat-value"
                     style="font-size:14px;">

                    {expiry}

                </div>

            </div>


            <div class="dashboard-stat">

                <div class="dashboard-stat-label">
                    OVERALL PCR
                </div>

                <div class="dashboard-stat-value">
                    {metrics["overall_pcr"]:.3f}
                </div>

            </div>


            <div class="dashboard-stat">

                <div class="dashboard-stat-label">
                    MARKET BIAS
                </div>

                <div class="dashboard-stat-value {dashboard_bias_class}">
                    {dashboard_bias}
                </div>

                <div style="
                    color:#687483;
                    font-size:8px;
                    margin-top:4px;
                ">
                    SCORE: {dashboard_score}
                </div>

            </div>

        </div>

    </div>
    """
)
st.write("")

# --------------------------------------------------------
# OI STRUCTURE
# --------------------------------------------------------

st.html(
    f"""
    <div class="dashboard-panel">

        <div class="dashboard-panel-header">

            <div class="dashboard-panel-title">
                OI STRUCTURE
            </div>

            <div class="dashboard-panel-meta">
                KEY STRIKE LEVELS
            </div>

        </div>


        <div class="structure-grid">

            <div class="structure-item">

                <div class="structure-label">
                    MAX CE OI
                </div>

                <div class="structure-value resistance">
                    {format_integer(metrics["max_ce_oi_strike"])}
                </div>

            </div>


            <div class="structure-item">

                <div class="structure-label">
                    MAX PE OI
                </div>

                <div class="structure-value support">
                    {format_integer(metrics["max_pe_oi_strike"])}
                </div>

            </div>


            <div class="structure-item">

                <div class="structure-label">
                    MAX CE ΔOI
                </div>

                <div class="structure-value">
                    {format_integer(metrics["max_ce_change_strike"])}
                </div>

            </div>


            <div class="structure-item">

                <div class="structure-label">
                    MAX PE ΔOI
                </div>

                <div class="structure-value">
                    {format_integer(metrics["max_pe_change_strike"])}
                </div>

            </div>

        </div>

    </div>
    """
)       
# ============================================================
# TAB 2 — OPTION CHAIN
# ============================================================

with tabs[1]:

    # --------------------------------------------------------
    # MARKET STRUCTURE CHARTS
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

    st.markdown(
        '<div class="section-title">Option Chain</div>',
        unsafe_allow_html=True
    )

    option_control1, option_control2 = st.columns([1, 1])

    with option_control1:
        range_choice = st.selectbox(
            "DISPLAY RANGE",
            [
                "ATM ± 5",
                "ATM ± 10",
                "ATM ± 15",
                "ATM ± 20",
                "ALL"
            ],
            index=1,
            key="option_chain_range"
        )

    with option_control2:
        table_view = st.selectbox(
            "DATA VIEW",
            [
                "MARKET DATA",
                "GREEKS",
                "FULL ANALYTICS"
            ],
            index=0,
            key="option_chain_data_view"
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
    # ========================================================
    # STEP 9 — OPTION CHAIN INTELLIGENCE PANEL
    # ========================================================

    chain_intel = calculate_option_chain_intelligence(
        df,
        atm
    )

    if chain_intel.get(
        "valid",
        False
    ):

        call_wall = chain_intel.get(
            "call_wall",
            np.nan
        )

        put_wall = chain_intel.get(
            "put_wall",
            np.nan
        )

        chain_pcr = chain_intel.get(
            "pcr",
            np.nan
        )

        chain_bias = chain_intel.get(
            "bias",
            "NEUTRAL"
        )

        chain_structure = chain_intel.get(
            "structure",
            "BALANCED"
        )

        chain_strength = chain_intel.get(
            "strength",
            0
        )

        # ----------------------------------------------------
        # BIAS COLOR
        # ----------------------------------------------------

        if "BULLISH" in chain_bias:

            chain_bias_color = "#00e59a"

        elif "BEARISH" in chain_bias:

            chain_bias_color = "#ff4654"

        else:

            chain_bias_color = "#f1c75b"

        # ----------------------------------------------------
        # TOP STRUCTURE BAR
        # ----------------------------------------------------

        st.html(
            dedent(
                f"""
                <div style="
                    margin-top:10px;
                    margin-bottom:10px;
                    padding:13px 16px;
                    background:#10151c;
                    border:1px solid #292e38;
                    border-radius:10px;
                ">

                    <div style="
                        display:flex;
                        align-items:center;
                        justify-content:space-between;
                    ">

                        <div>

                            <div style="
                                color:#737d8d;
                                font-size:9px;
                                font-weight:900;
                                letter-spacing:1.3px;
                            ">
                                OPTION CHAIN INTELLIGENCE
                            </div>

                            <div style="
                                color:#f5f7fa;
                                font-size:17px;
                                font-weight:900;
                                margin-top:4px;
                            ">
                                {chain_structure}
                            </div>

                        </div>

                        <div style="
                            text-align:right;
                        ">

                            <div style="
                                color:{chain_bias_color};
                                font-size:16px;
                                font-weight:950;
                            ">
                                {chain_bias}
                            </div>

                            <div style="
                                color:#737d8d;
                                font-size:10px;
                                margin-top:3px;
                            ">
                                STRUCTURE STRENGTH
                                {chain_strength:.0f}%
                            </div>

                        </div>

                    </div>

                </div>
                """
            )
        )

        # ----------------------------------------------------
        # STRUCTURE CARDS
        # ----------------------------------------------------

        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            CALL WALL
                        </div>

                        <div class="metric-value"
                             style="font-size:20px;">
                            {format_integer(call_wall)}
                        </div>

                        <div class="metric-sub">
                            Highest CE OI
                        </div>

                    </div>
                    """
                )
            )

        with c2:

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            PUT WALL
                        </div>

                        <div class="metric-value"
                             style="font-size:20px;">
                            {format_integer(put_wall)}
                        </div>

                        <div class="metric-sub">
                            Highest PE OI
                        </div>

                    </div>
                    """
                )
            )

        with c3:

            pcr_display = (
                f"{chain_pcr:.2f}"
                if np.isfinite(chain_pcr)
                else "—"
            )

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            OI PCR
                        </div>

                        <div class="metric-value"
                             style="font-size:20px;">
                            {pcr_display}
                        </div>

                        <div class="metric-sub">
                            PE OI / CE OI
                        </div>

                    </div>
                    """
                )
            )

        with c4:

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            ATM
                        </div>

                        <div class="metric-value"
                             style="font-size:20px;">
                            {format_integer(atm)}
                        </div>

                        <div class="metric-sub">
                            Reference strike
                        </div>

                    </div>
                    """
                )
            )

        with c5:

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            BIAS
                        </div>

                        <div style="
                            color:{chain_bias_color};
                            font-size:16px;
                            font-weight:950;
                            margin-top:9px;
                        ">
                            {chain_bias}
                        </div>

                        <div class="metric-sub">
                            OI + volume structure
                        </div>

                    </div>
                    """
                )
            )

        # ----------------------------------------------------
        # CONCENTRATION PANEL
        # ----------------------------------------------------

        st.markdown(
            "#### Strike Concentration"
        )

        q1, q2, q3, q4 = st.columns(4)

        with q1:

            st.html(
                dedent(
                    f"""
                    <div style="
                        background:#11151c;
                        border:1px solid #292e38;
                        border-radius:9px;
                        padding:11px 13px;
                    ">

                        <div class="metric-label">
                            CE VOLUME PEAK
                        </div>

                        <div class="metric-value"
                             style="font-size:17px;">
                            {
                                format_integer(
                                    chain_intel.get(
                                        "max_call_volume_strike",
                                        np.nan
                                    )
                                )
                            }
                        </div>

                    </div>
                    """
                )
            )

        with q2:

            st.html(
                dedent(
                    f"""
                    <div style="
                        background:#11151c;
                        border:1px solid #292e38;
                        border-radius:9px;
                        padding:11px 13px;
                    ">

                        <div class="metric-label">
                            PE VOLUME PEAK
                        </div>

                        <div class="metric-value"
                             style="font-size:17px;">
                            {
                                format_integer(
                                    chain_intel.get(
                                        "max_put_volume_strike",
                                        np.nan
                                    )
                                )
                            }
                        </div>

                    </div>
                    """
                )
            )

        with q3:

            st.html(
                dedent(
                    f"""
                    <div style="
                        background:#11151c;
                        border:1px solid #292e38;
                        border-radius:9px;
                        padding:11px 13px;
                    ">

                        <div class="metric-label">
                            CE ΔOI PEAK
                        </div>

                        <div class="metric-value"
                             style="font-size:17px;">
                            {
                                format_integer(
                                    chain_intel.get(
                                        "max_call_oi_change_strike",
                                        np.nan
                                    )
                                )
                            }
                        </div>

                    </div>
                    """
                )
            )

        with q4:

            st.html(
                dedent(
                    f"""
                    <div style="
                        background:#11151c;
                        border:1px solid #292e38;
                        border-radius:9px;
                        padding:11px 13px;
                    ">

                        <div class="metric-label">
                            PE ΔOI PEAK
                        </div>

                        <div class="metric-value"
                             style="font-size:17px;">
                            {
                                format_integer(
                                    chain_intel.get(
                                        "max_put_oi_change_strike",
                                        np.nan
                                    )
                                )
                            }
                        </div>

                    </div>
                    """
                )
            )

    option_table = make_option_table(
        df,
        atm,
        range_count,
        table_view=table_view
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
        # ========================================================
    # STEP 9 — ATM BATTLEFIELD
    # ========================================================

    try:

        atm_data = prepare_chart_data(
            df,
            atm,
            2
        ).copy()

        if not atm_data.empty:

            atm_data["DISTANCE"] = (
                atm_data["strike"]
                - float(atm)
            )

            atm_data["ABS_DISTANCE"] = (
                atm_data["DISTANCE"]
                .abs()
            )

            atm_data = atm_data.sort_values(
                "ABS_DISTANCE"
            ).head(5)

            # ------------------------------------------------
            # BUILD DISPLAY
            # ------------------------------------------------

            battlefield_rows = []

            for _, row in atm_data.iterrows():

                strike_value = row.get(
                    "strike",
                    np.nan
                )

                ce_oi_change = safe_number(
                    row.get(
                        "ce_oi_change",
                        0
                    ),
                    0
                )

                pe_oi_change = safe_number(
                    row.get(
                        "pe_oi_change",
                        0
                    ),
                    0
                )

                ce_volume = safe_number(
                    row.get(
                        "ce_volume",
                        0
                    ),
                    0
                )

                pe_volume = safe_number(
                    row.get(
                        "pe_volume",
                        0
                    ),
                    0
                )

                if (
                    pe_oi_change > 0
                    and ce_oi_change < 0
                ):

                    structure_signal = (
                        "PUT BUILDUP"
                    )

                elif (
                    ce_oi_change > 0
                    and pe_oi_change < 0
                ):

                    structure_signal = (
                        "CALL BUILDUP"
                    )

                elif (
                    pe_oi_change < 0
                    and ce_oi_change < 0
                ):

                    structure_signal = (
                        "UNWINDING"
                    )

                elif (
                    pe_oi_change > 0
                    and ce_oi_change > 0
                ):

                    structure_signal = (
                        "BOTH BUILDUP"
                    )

                else:

                    structure_signal = (
                        "NEUTRAL"
                    )

                battlefield_rows.append({

                    "STRIKE":
                        format_integer(
                            strike_value
                        ),

                    "DISTANCE":
                        f"{strike_value - atm:+.0f}",

                    "CE ΔOI":
                        format_number(
                            ce_oi_change
                        ),

                    "PE ΔOI":
                        format_number(
                            pe_oi_change
                        ),

                    "CE VOL":
                        format_number(
                            ce_volume
                        ),

                    "PE VOL":
                        format_number(
                            pe_volume
                        ),

                    "STRUCTURE":
                        structure_signal
                })

            battlefield_df = pd.DataFrame(
                battlefield_rows
            )

            st.markdown(
                "#### ATM Battlefield"
            )

            st.dataframe(
                battlefield_df,
                width="stretch",
                height=225,
                hide_index=True
            )

    except Exception as e:

        st.caption(
            f"ATM battlefield unavailable: {e}"
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
        dedent(f"""
        <div class="level-card">
            <span class="support">
                SUPPORT: {format_integer(metrics["support"])}
            </span>
            &nbsp;&nbsp;&nbsp;
            <span class="resistance">
                RESISTANCE: {format_integer(metrics["resistance"])}
            </span>
        </div>
        """),
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
# TAB 6 — GREEKS
# ============================================================

with tabs[5]:

    st.markdown(
        '<div class="section-title">Option Greeks & Analytics</div>',
        unsafe_allow_html=True
    )

    greek_df = ensure_greek_columns(df)
    
    greek_metrics = greek_summary(
        greek_df,
        atm,
        range_count=10
    )
    
        # ========================================================
    # STEP 10 — GREEK CONTROL PANEL
    # ========================================================

    greek_control = greek_control_summary(
        greek_df,
        atm,
        range_count=10
    )

    # --------------------------------------------------------
    # HELPER
    # --------------------------------------------------------

    def greek_display(
        value,
        decimals=4
    ):

        try:

            if value is None:
                return "—"

            if pd.isna(value):
                return "—"

            return f"{float(value):,.{decimals}f}"

        except Exception:

            return "—"

    # --------------------------------------------------------
    # TOP STATUS BAR
    # --------------------------------------------------------

    if greek_control.get(
        "valid",
        False
    ):

        st.html(
            dedent(
                f"""
                <div style="
                    margin-top:10px;
                    margin-bottom:12px;
                    padding:14px 16px;
                    background:#10151c;
                    border:1px solid #292e38;
                    border-radius:10px;
                ">

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                    ">

                        <div>

                            <div style="
                                color:#737d8d;
                                font-size:9px;
                                font-weight:900;
                                letter-spacing:1.3px;
                            ">
                                GREEK CONTROL PANEL
                            </div>

                            <div style="
                                color:#f5f7fa;
                                font-size:18px;
                                font-weight:900;
                                margin-top:4px;
                            ">
                                ATM + OI-WEIGHTED GREEK STRUCTURE
                            </div>

                        </div>

                        <div style="
                            text-align:right;
                        ">

                            <div style="
                                color:#8f98a8;
                                font-size:9px;
                                font-weight:800;
                                letter-spacing:.8px;
                            ">
                                GAMMA REGIME
                            </div>

                            <div style="
                                color:#00e59a;
                                font-size:14px;
                                font-weight:950;
                                margin-top:3px;
                            ">
                                {greek_control.get("gamma_regime", "—")}
                            </div>

                        </div>

                    </div>

                </div>
                """
            )
        )

        # ----------------------------------------------------
        # PRIMARY GREEK CARDS
        # ----------------------------------------------------

        g1, g2, g3, g4, g5 = st.columns(5)

        with g1:

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            ATM DELTA
                        </div>

                        <div class="metric-value"
                             style="font-size:20px;">
                            {
                                greek_display(
                                    greek_control.get(
                                        "atm_delta"
                                    ),
                                    4
                                )
                            }
                        </div>

                        <div class="metric-sub">
                            CE + PE
                        </div>

                    </div>
                    """
                )
            )

        with g2:

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            ATM GAMMA
                        </div>

                        <div class="metric-value"
                             style="font-size:20px;">
                            {
                                greek_display(
                                    greek_control.get(
                                        "atm_gamma"
                                    ),
                                    6
                                )
                            }
                        </div>

                        <div class="metric-sub">
                            CE + PE
                        </div>

                    </div>
                    """
                )
            )

        with g3:

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            ATM THETA
                        </div>

                        <div class="metric-value"
                             style="font-size:20px;">
                            {
                                greek_display(
                                    greek_control.get(
                                        "atm_theta"
                                    ),
                                    4
                                )
                            }
                        </div>

                        <div class="metric-sub">
                            CE + PE
                        </div>

                    </div>
                    """
                )
            )

        with g4:

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            ATM VEGA
                        </div>

                        <div class="metric-value"
                             style="font-size:20px;">
                            {
                                greek_display(
                                    greek_control.get(
                                        "atm_vega"
                                    ),
                                    4
                                )
                            }
                        </div>

                        <div class="metric-sub">
                            CE + PE
                        </div>

                    </div>
                    """
                )
            )

        with g5:

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            ATM STRIKE
                        </div>

                        <div class="metric-value"
                             style="font-size:20px;">
                            {format_integer(atm)}
                        </div>

                        <div class="metric-sub">
                            Nearest live strike
                        </div>

                    </div>
                    """
                )
            )

        # ----------------------------------------------------
        # EXPOSURE CARDS
        # ----------------------------------------------------

        st.markdown(
            "#### OI-Weighted Greek Exposure"
        )

        e1, e2, e3, e4 = st.columns(4)

        with e1:

            st.metric(
                "NET DELTA",
                greek_display(
                    greek_control.get(
                        "net_delta"
                    ),
                    2
                )
            )

        with e2:

            st.metric(
                "NET GAMMA",
                greek_display(
                    greek_control.get(
                        "net_gamma"
                    ),
                    2
                )
            )

        with e3:

            st.metric(
                "NET THETA",
                greek_display(
                    greek_control.get(
                        "net_theta"
                    ),
                    2
                )
            )

        with e4:

            st.metric(
                "NET VEGA",
                greek_display(
                    greek_control.get(
                        "net_vega"
                    ),
                    2
                )
            )

        # ----------------------------------------------------
        # REGIME STRIP
        # ----------------------------------------------------

        r1, r2, r3, r4 = st.columns(4)

        regime_items = [
            (
                r1,
                "DELTA",
                greek_control.get(
                    "delta_bias",
                    "—"
                )
            ),
            (
                r2,
                "GAMMA",
                greek_control.get(
                    "gamma_regime",
                    "—"
                )
            ),
            (
                r3,
                "THETA",
                greek_control.get(
                    "theta_regime",
                    "—"
                )
            ),
            (
                r4,
                "VEGA",
                greek_control.get(
                    "vega_regime",
                    "—"
                )
            )
        ]

        for container, label, value in regime_items:

            with container:

                st.html(
                    dedent(
                        f"""
                        <div style="
                            background:#11151c;
                            border:1px solid #292e38;
                            border-radius:8px;
                            padding:9px 12px;
                            text-align:center;
                        ">

                            <div style="
                                color:#737d8d;
                                font-size:8px;
                                font-weight:900;
                                letter-spacing:1px;
                            ">
                                {label}
                            </div>

                            <div style="
                                color:#dfe5ec;
                                font-size:11px;
                                font-weight:900;
                                margin-top:4px;
                            ">
                                {value}
                            </div>

                        </div>
                        """
                    )
                )
    

    # --------------------------------------------------------
    # DATA STATUS
    # --------------------------------------------------------

    greek_valid_total = 0
    greek_expected_total = len(greek_df) * 8

    for column in [
        "ce_delta", "ce_gamma", "ce_theta", "ce_vega",
        "pe_delta", "pe_gamma", "pe_theta", "pe_vega"
    ]:
        greek_valid_total += int(
            pd.to_numeric(
                greek_df[column],
                errors="coerce"
            ).notna().sum()
        )

    if greek_valid_total == 0:
        st.warning(
            "No live Greek values are available in the current option-chain data. "
            "The Greek analytics will populate automatically when the Upstox snapshot "
            "contains Delta, Gamma, Theta and Vega."
        )
    else:
        st.caption(
            f"Greek data quality: {greek_valid_total}/{greek_expected_total} "
            "core Greek fields valid • ATM values are taken from the nearest strike."
        )

    # --------------------------------------------------------
    # ATM GREEK CARDS
    # --------------------------------------------------------

    def greek_card_value(value, decimals=4):
        try:
            if value is None or pd.isna(value):
                return "—"
            return f"{float(value):,.{decimals}f}"
        except Exception:
            return "—"

    def ratio_card_value(value):
        try:
            if value is None or pd.isna(value):
                return "—"
            return f"{float(value):.3f}"
        except Exception:
            return "—"

    row1 = st.columns(5)

    with row1[0]:
        st.metric(
            "ATM CE DELTA",
            greek_card_value(greek_metrics.get("atm_ce_delta"))
        )

    with row1[1]:
        st.metric(
            "ATM PE DELTA",
            greek_card_value(greek_metrics.get("atm_pe_delta"))
        )

    with row1[2]:
        st.metric(
            "ATM CE GAMMA",
            greek_card_value(greek_metrics.get("atm_ce_gamma"), 6)
        )

    with row1[3]:
        st.metric(
            "ATM PE GAMMA",
            greek_card_value(greek_metrics.get("atm_pe_gamma"), 6)
        )

    with row1[4]:
        ce_iv = greek_metrics.get("atm_ce_iv")
        pe_iv = greek_metrics.get("atm_pe_iv")
        iv_text = (
            f"CE {greek_card_value(ce_iv, 2)} | "
            f"PE {greek_card_value(pe_iv, 2)}"
        )
        st.metric("ATM IV", iv_text)

    row2 = st.columns(5)

    with row2[0]:
        st.metric(
            "ATM CE THETA",
            greek_card_value(greek_metrics.get("atm_ce_theta"), 2)
        )

    with row2[1]:
        st.metric(
            "ATM PE THETA",
            greek_card_value(greek_metrics.get("atm_pe_theta"), 2)
        )

    with row2[2]:
        st.metric(
            "ATM CE VEGA",
            greek_card_value(greek_metrics.get("atm_ce_vega"), 3)
        )

    with row2[3]:
        st.metric(
            "ATM PE VEGA",
            greek_card_value(greek_metrics.get("atm_pe_vega"), 3)
        )

    with row2[4]:
        ce_pop = greek_metrics.get("atm_ce_pop")
        pe_pop = greek_metrics.get("atm_pe_pop")
        pop_text = (
            f"CE {greek_card_value(ce_pop, 2)} | "
            f"PE {greek_card_value(pe_pop, 2)}"
        )
        st.metric("ATM POP", pop_text)

    # --------------------------------------------------------
    # RATIOS
    # --------------------------------------------------------

    st.markdown("### Greek & Options Ratios")

    ratio_row1 = st.columns(4)

    ratio_definitions = [
        ("OI PCR", greek_metrics.get("range_oi_pcr")),
        ("VOLUME PCR", greek_metrics.get("range_volume_pcr")),
        ("ATM IV RATIO", greek_metrics.get("atm_iv_ratio")),
        ("ATM PREMIUM RATIO", greek_metrics.get("atm_premium_ratio")),
    ]

    for col, (label, value) in zip(ratio_row1, ratio_definitions):
        with col:
            st.metric(label, ratio_card_value(value))

    ratio_row2 = st.columns(4)

    greek_ratio_definitions = [
        ("DELTA OI RATIO", greek_metrics.get("delta_oi_ratio")),
        ("GAMMA OI RATIO", greek_metrics.get("gamma_oi_ratio")),
        ("THETA OI RATIO", greek_metrics.get("theta_oi_ratio")),
        ("VEGA OI RATIO", greek_metrics.get("vega_oi_ratio")),
    ]

    for col, (label, value) in zip(ratio_row2, greek_ratio_definitions):
        with col:
            st.metric(label, ratio_card_value(value))

    st.caption(
        "Greek OI ratios compare absolute CE Greek×OI to absolute PE Greek×OI "
        "over ATM ± 10 strikes. They are analytical ratios, not dealer-position estimates."
    )

    # --------------------------------------------------------
    # GREEK BY STRIKE
    # --------------------------------------------------------

    st.markdown("### Greek Curve by Strike")

    chart_control1, chart_control2, chart_control3 = st.columns([1, 1, 1])

    with chart_control1:
        greek_chart_metric = st.selectbox(
            "METRIC",
            [
                "Delta",
                "Gamma",
                "Theta",
                "Vega",
                "IV",
                "POP",
                "Rho",
            ],
            index=0,
            key="live_greek_chart_metric"
        )

    with chart_control2:
        greek_chart_side = st.selectbox(
            "SIDE",
            [
                "CE + PE",
                "CE",
                "PE"
            ],
            index=0,
            key="live_greek_chart_side"
        )

    with chart_control3:
        greek_chart_range = st.selectbox(
            "STRIKE RANGE",
            [
                5,
                10,
                15,
                20
            ],
            index=1,
            key="live_greek_chart_range"
        )

    greek_chart = greek_by_strike_chart(
        greek_df,
        atm,
        metric=greek_chart_metric,
        side=greek_chart_side,
        range_count=greek_chart_range,
        height=360
    )

    if greek_chart is not None:
        st.altair_chart(
            greek_chart,
            width="stretch"
        )
    else:
        st.info(
            f"No valid {greek_chart_metric} data is available for the selected strikes."
        )

    # --------------------------------------------------------
    # OI-WEIGHTED GREEK EXPOSURE
    # --------------------------------------------------------

    st.markdown("### OI-Weighted Greek Exposure")

    exposure_control1, exposure_control2 = st.columns([1, 3])

    with exposure_control1:
        exposure_metric = st.selectbox(
            "EXPOSURE",
            [
                "Delta OI",
                "Gamma OI",
                "Theta OI",
                "Vega OI",
                "Rho OI",
            ],
            index=0,
            key="greek_exposure_metric"
        )

    exposure_chart = greek_exposure_chart(
        greek_df,
        atm,
        metric=exposure_metric,
        range_count=10,
        height=320
    )

    if exposure_chart is not None:
        st.altair_chart(
            exposure_chart,
            width="stretch"
        )
    else:
        st.info(
            f"No {exposure_metric} data is available in the current snapshot."
        )

    st.caption(
        "Exposure shown here is raw Greek × OI by strike. It is intentionally not labelled "
        "as dealer GEX/DEX because a dealer-position sign convention is not present in the data."
    )

    # --------------------------------------------------------
    # RAW GREEK EXPOSURE SUMMARY
    # --------------------------------------------------------

    exposure_row = st.columns(4)

    exposure_cards = [
        ("RAW DELTA OI", greek_metrics.get("net_delta_oi_weighted")),
        ("RAW GAMMA OI", greek_metrics.get("net_gamma_oi_weighted")),
        ("RAW THETA OI", greek_metrics.get("net_theta_oi_weighted")),
        ("RAW VEGA OI", greek_metrics.get("net_vega_oi_weighted")),
    ]

    for col, (label, value) in zip(exposure_row, exposure_cards):
        with col:
            if value is None or pd.isna(value):
                display_value = "—"
            else:
                display_value = format_number(value)
            st.metric(label, display_value)
with tabs[12]:
    # --------------------------------------------------------
    # GAMMA BLAST
    # --------------------------------------------------------
    
    st.markdown("### ⚡ Gamma Blast")
    
    gamma_blast = calculate_gamma_blast(
        greek_df,
        atm,
        range_count=15
    )
    
    if not gamma_blast.get("valid", False):
    
        st.warning(
            gamma_blast.get(
                "message",
                "Gamma data unavailable."
            )
        )
    
    else:
    
        # ----------------------------------------------------
        # GAMMA BLAST HEADER
        # ----------------------------------------------------
    
        pressure = gamma_blast[
            "pressure"
        ]
    
        blast_strength = gamma_blast[
            "blast_strength"
        ]
    
        blast_score = gamma_blast[
            "blast_score"
        ]
    
        if "LONG" in pressure:
    
            blast_color = "#00e59a"
    
        elif "SHORT" in pressure:
    
            blast_color = "#ff5c67"
    
        else:
    
            blast_color = "#f1c75b"
    
        st.html(
            dedent(
                f"""
                <div style="
                    background:#11151c;
                    border:1px solid #292e38;
                    border-radius:10px;
                    padding:14px 16px;
                    margin-bottom:10px;
                ">
    
                    <div style="
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                    ">
    
                        <div>
    
                            <div style="
                                color:#737d8d;
                                font-size:10px;
                                font-weight:800;
                                letter-spacing:1px;
                            ">
                                GAMMA PRESSURE ENGINE
                            </div>
    
                            <div style="
                                color:{blast_color};
                                font-size:22px;
                                font-weight:900;
                                margin-top:4px;
                            ">
                                {pressure}
                            </div>
    
                        </div>
    
                        <div style="
                            text-align:right;
                        ">
    
                            <div style="
                                color:#737d8d;
                                font-size:10px;
                                font-weight:800;
                            ">
                                BLAST SCORE
                            </div>
    
                            <div style="
                                color:#f5f7fa;
                                font-size:24px;
                                font-weight:900;
                                margin-top:2px;
                            ">
                                {blast_score:.1f}
                            </div>
    
                            <div style="
                                color:{blast_color};
                                font-size:10px;
                                font-weight:800;
                                margin-top:2px;
                            ">
                                {blast_strength}
                            </div>
    
                        </div>
    
                    </div>
    
                </div>
                """
            )
        )
    
        # ----------------------------------------------------
        # GAMMA METRICS
        # ----------------------------------------------------
    
        g1, g2, g3, g4, g5 = st.columns(5)
    
        with g1:
    
            st.metric(
                "CE GAMMA PRESSURE",
                format_number(
                    gamma_blast[
                        "ce_gamma_pressure"
                    ]
                )
            )
    
        with g2:
    
            st.metric(
                "PE GAMMA PRESSURE",
                format_number(
                    gamma_blast[
                        "pe_gamma_pressure"
                    ]
                )
            )
    
        with g3:
    
            st.metric(
                "NET GAMMA",
                format_number(
                    gamma_blast[
                        "net_gamma_pressure"
                    ]
                )
            )
    
        with g4:
    
            wall = gamma_blast[
                "gamma_wall_strike"
            ]
    
            st.metric(
                "GAMMA WALL",
                format_integer(
                    wall
                )
                if np.isfinite(wall)
                else "—"
            )
    
        with g5:
    
            imbalance = gamma_blast[
                "gamma_imbalance"
            ]
    
            st.metric(
                "GAMMA IMBALANCE",
                f"{imbalance:+.3f}"
                if np.isfinite(
                    imbalance
                )
                else "—"
            )
    
        # ----------------------------------------------------
        # GAMMA PRESSURE MAP
        # ----------------------------------------------------
    
        st.markdown(
            "#### Gamma Pressure by Strike"
        )
    
        gamma_chart = gamma_blast_chart(
            gamma_blast,
            height=360
        )
    
        if gamma_chart is not None:
    
            st.altair_chart(
                gamma_chart,
                width="stretch"
            )
    
        else:
    
            st.info(
                "Gamma pressure chart unavailable."
            )
    # --------------------------------------------------------
    # GAMMA WALL RADAR
    # --------------------------------------------------------
    
    st.markdown(
        "#### Gamma Wall Radar"
    )
    
    if (
        "gamma_structure" in globals()
        and gamma_structure.get(
        "valid",
        False
        )
    ):
    
        radar_df = (
            build_gamma_wall_radar(
                gamma_df=
                    gamma_structure[
                        "data"
                    ],
    
                spot=spot,
    
                gamma_wall=
                    gamma_structure[
                        "gamma_wall"
                    ],
    
                gamma_flip=
                    gamma_structure[
                        "gamma_flip"
                    ],
    
                strikes_each_side=4
            )
        )
    
        if not radar_df.empty:
    
            display_radar = (
                radar_df[
                    [
                        "strike",
                        "DISTANCE",
                        "NET_GAMMA_PRESSURE",
                        "DIRECTION",
                        "WALL",
                        "FLIP"
                    ]
                ]
                .copy()
            )
    
            display_radar = (
                display_radar
                .rename(
                    columns={
                        "strike":
                            "STRIKE",
    
                        "DISTANCE":
                            "FROM SPOT",
    
                        "NET_GAMMA_PRESSURE":
                            "NET GAMMA",
    
                        "DIRECTION":
                            "ZONE",
    
                        "WALL":
                            "WALL",
    
                        "FLIP":
                            "FLIP"
                    }
                )
            )
    
            display_radar[
                "STRIKE"
            ] = display_radar[
                "STRIKE"
            ].round(0).astype(int)
    
            display_radar[
                "FROM SPOT"
            ] = display_radar[
                "FROM SPOT"
            ].round(0)
    
            display_radar[
                "NET GAMMA"
            ] = display_radar[
                "NET GAMMA"
            ].round(2)
    
            st.dataframe(
                display_radar,
                width="stretch",
                hide_index=True,
                height=330
            )
    
        else:
    
            st.info(
                "No significant gamma walls "
                "available around spot."
            )
    
    else:
    
        st.info(
            "Gamma Wall Radar is waiting for "
            "valid gamma structure."
        )
    # ----------------------------------------------------
    # GAMMA STRUCTURE
    # ----------------------------------------------------
    
    gamma_structure = calculate_gamma_structure(
        gamma_blast,
        spot=spot,
        atm=atm
    )
    
    if gamma_structure.get(
        "valid",
        False
    ):
    
        gamma_flip = gamma_structure[
            "gamma_flip"
        ]
    
        gamma_wall = gamma_structure[
            "gamma_wall"
        ]
    
        wall_above = gamma_structure[
            "wall_above"
        ]
    
        wall_below = gamma_structure[
            "wall_below"
        ]
    
        regime = gamma_structure[
            "regime"
        ]
    
        blast_zone = gamma_structure[
            "blast_zone"
        ]
        
    # --------------------------------------------------------
    # GAMMA ACCELERATION
    # --------------------------------------------------------
    
    st.markdown(
        "#### Gamma Acceleration"
    )
    
    gamma_acceleration = (
        calculate_gamma_acceleration(
            gamma_blast,
            history_df=None,
            spot=spot,
            atm=atm
        )
    )
    
    a1, a2, a3, a4 = st.columns(4)
    
    with a1:
    
        st.metric(
            "GAMMA STATE",
            gamma_acceleration.get(
                "state",
                "—"
            )
        )
    
    with a2:
    
        change_pct = (
            gamma_acceleration.get(
                "change_pct"
            )
        )
    
        st.metric(
            "GAMMA CHANGE",
            (
                f"{change_pct:+.1f}%"
                if (
                    change_pct is not None
                    and np.isfinite(
                        change_pct
                    )
                )
                else "—"
            )
        )
    
    with a3:
    
        st.metric(
            "WALL MIGRATION",
            gamma_acceleration.get(
                "wall_migration",
                "—"
            )
        )
    
    with a4:
    
        st.metric(
            "ACCELERATION SCORE",
            f"{gamma_acceleration.get('score', 0):.1f}"
        )
    
    st.caption(
        "Acceleration compares aggregated gamma pressure "
        "between snapshots. Historical aggregation becomes "
        "active as sufficient compatible history accumulates."
        
    )
    
    # --------------------------------------------------------
    # GAMMA BLAST SCORE
    # --------------------------------------------------------
    
    st.markdown(
        "#### ⚡ Gamma Blast Score"
    )
    
    gamma_score = calculate_gamma_blast_score(
        gamma_blast=gamma_blast,
        gamma_structure=gamma_structure,
        gamma_acceleration=gamma_acceleration,
        greek_metrics=greek_metrics,
        spot=spot,
        atm=atm
    )
    
    if gamma_score is None:
        gamma_score = {
            "valid": False,
            "score": 0.0,
            "direction": "NEUTRAL",
            "state": "LOW",
            "components": {},
            "available_weight": 0.0,
        }
    
    gamma_velocity = calculate_gamma_blast_velocity(
        gamma_score.get(
            "score",
            0.0
        )
    )
    
    velocity_state = gamma_velocity.get(
        "state",
        "STABLE"
    )
    
    velocity_change = gamma_velocity.get(
        "score_change",
        np.nan
    )
    
    velocity_pct = gamma_velocity.get(
        "velocity_pct",
        np.nan
    )
    
    severity = gamma_velocity.get(
        "severity",
        "LOW"
    )
    
    gamma_score_history = update_gamma_blast_snapshot(
        gamma_score.get(
            "score",
            0.0
        )
    )
    
    final_score = gamma_score.get(
        "score",
        0.0
    )
    
    direction = gamma_score.get(
        "direction",
        "NEUTRAL"
    )
    
    state = gamma_score.get(
        "state",
        "LOW"
    )
    
    if gamma_score.get(
        "valid",
        False
    ):
    
        final_score = gamma_score[
            "score"
        ]
    
        direction = gamma_score[
            "direction"
        ]
    
        state = gamma_score[
            "state"
        ]
    
        gamma_score = calculate_gamma_blast_score(
        gamma_blast=gamma_blast,
        gamma_structure=gamma_structure,
        gamma_acceleration=gamma_acceleration,
        greek_metrics=greek_metrics,
        spot=spot,
        atm=atm
    )
    # --------------------------------------------------------
    # GAMMA BLAST VELOCITY PANEL
    # --------------------------------------------------------
    
    st.markdown(
        "#### ⚡ Blast Velocity"
    )
    
    if gamma_velocity.get(
        "valid",
        False
    ):
    
        velocity_state = (
            gamma_velocity[
                "state"
            ]
        )
    
        velocity_change = (
            gamma_velocity[
                "score_change"
            ]
        )
    
        velocity_pct = (
            gamma_velocity[
                "velocity_pct"
            ]
        )
    
        severity = (
            gamma_velocity[
                "severity"
            ]
        )
        
        # --------------------------------------------------------
    # GAMMA BLAST SCORE HISTORY
    # --------------------------------------------------------
    
    if (
        isinstance(
            gamma_score_history,
            pd.DataFrame
        )
        and len(
            gamma_score_history
        ) >= 2
    ):
    
        st.markdown(
            "#### Gamma Blast Score History"
        )
    
        blast_history_chart = (
            gamma_blast_history_chart(
                gamma_score_history,
                height=260
            )
        )
    
        if blast_history_chart is not None:
    
            st.altair_chart(
                blast_history_chart,
                width="stretch"
            )
    
            st.caption(
                f"{len(gamma_score_history)} "
                "in-session Gamma Blast snapshots • "
                "dashed line = high-risk threshold"
            )
    
        # ----------------------------------------------------
        # COLOR
        # ----------------------------------------------------
    
        if "ACCELERATION" in velocity_state:
    
            velocity_color = "#ff4654"
    
        elif "BUILDING" in velocity_state:
    
            velocity_color = "#f1c75b"
    
        elif "UNWIND" in velocity_state:
    
            velocity_color = "#00d995"
    
        elif "COOLING" in velocity_state:
    
            velocity_color = "#737d8d"
    
        else:
    
            velocity_color = "#737d8d"
    
        v1, v2, v3, v4 = st.columns(4)
    
        with v1:
    
            st.metric(
                "CURRENT SCORE",
                f"{gamma_velocity['current_score']:.1f}"
            )
    
        with v2:
    
            st.metric(
                "PREVIOUS SCORE",
                f"{gamma_velocity['previous_score']:.1f}"
            )
    
        with v3:
    
            st.metric(
                "SCORE Δ",
                f"{velocity_change:+.1f}"
            )
    
        with v4:
    
            st.metric(
                "VELOCITY",
                (
                    f"{velocity_pct:+.1f}%"
                    if np.isfinite(
                        velocity_pct
                    )
                    else "—"
                )
            )
    
        # ----------------------------------------------------
        # STATE BANNER
        # ----------------------------------------------------
    
        st.html(
            dedent(
                f"""
                <div style="
                    margin-top:10px;
                    padding:13px 16px;
                    border-radius:9px;
                    background:#11151c;
                    border:1px solid #292e38;
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                ">
    
                    <div>
    
                        <div style="
                            color:#737d8d;
                            font-size:9px;
                            font-weight:900;
                            letter-spacing:1px;
                        ">
                            GAMMA BLAST VELOCITY
                        </div>
    
                        <div style="
                            color:{velocity_color};
                            font-size:19px;
                            font-weight:900;
                            margin-top:4px;
                        ">
                            {velocity_state}
                        </div>
    
                    </div>
    
                    <div style="
                        text-align:right;
                        color:#737d8d;
                        font-size:10px;
                        font-weight:800;
                    ">
                        SEVERITY<br>
    
                        <span style="
                            color:{velocity_color};
                            font-size:12px;
                        ">
                            {severity}
                        </span>
    
                    </div>
    
                </div>
                """
            )
        )
    
    else:
    
        st.info(
            "Gamma Blast velocity will activate "
            "after the next valid refresh snapshot."
        )
        # ----------------------------------------------------
        # SCORE COLOR
        # ----------------------------------------------------
    
        if final_score >= 80:
    
            score_color = "#ff4654"
    
        elif final_score >= 65:
    
            score_color = "#f1c75b"
    
        elif final_score >= 45:
    
            score_color = "#00d995"
    
        else:
    
            score_color = "#737d8d"
    
        # ----------------------------------------------------
        # MAIN SCORE CARD
        # ----------------------------------------------------
    
        st.html(
            dedent(
                f"""
                <div style="
                    background:#0d1117;
                    border:1px solid #303642;
                    border-radius:12px;
                    padding:18px;
                    margin-top:8px;
                ">
    
                    <div style="
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                    ">
    
                        <div>
    
                            <div style="
                                color:#737d8d;
                                font-size:10px;
                                font-weight:900;
                                letter-spacing:1.2px;
                            ">
                                COMPOSITE GAMMA SIGNAL
                            </div>
    
                            <div style="
                                color:#f5f7fa;
                                font-size:13px;
                                font-weight:700;
                                margin-top:5px;
                            ">
                                GAMMA BLAST SCORE
                            </div>
    
                        </div>
    
                        <div style="
                            text-align:right;
                        ">
    
                            <div style="
                                color:{score_color};
                                font-size:34px;
                                line-height:1;
                                font-weight:950;
                            ">
                                {final_score:.0f}
                                <span style="
                                    font-size:13px;
                                    color:#737d8d;
                                ">
                                    /100
                                </span>
                            </div>
    
                            <div style="
                                color:{score_color};
                                font-size:10px;
                                font-weight:900;
                                margin-top:5px;
                            ">
                                {state}
                            </div>
    
                        </div>
    
                    </div>
    
                    <div style="
                        height:7px;
                        background:#202631;
                        border-radius:8px;
                        overflow:hidden;
                        margin-top:15px;
                    ">
    
                        <div style="
                            width:{final_score:.1f}%;
                            height:100%;
                            background:{score_color};
                            border-radius:8px;
                        "></div>
    
                    </div>
    
                    <div style="
                        display:flex;
                        justify-content:space-between;
                        margin-top:10px;
                    ">
    
                        <span style="
                            color:#737d8d;
                            font-size:10px;
                            font-weight:700;
                        ">
                            DIRECTION
                        </span>
    
                        <span style="
                            color:#f5f7fa;
                            font-size:10px;
                            font-weight:900;
                        ">
                            {direction}
                        </span>
    
                    </div>
    
                </div>
                """
            )
        )
    
        # ----------------------------------------------------
        # COMPONENT BREAKDOWN
        # ----------------------------------------------------
    
        components = gamma_score.get(
            "components",
            {}
        )
    
        if components:
    
            score_rows = []
    
            for name, item in components.items():
    
                score_rows.append(
                    {
                        "COMPONENT":
                            name,
    
                        "SCORE":
                            round(
                                item["score"],
                                1
                            ),
    
                        "WEIGHT":
                            f"{item['weight']:.0f}%",
    
                        "CONTRIBUTION":
                            round(
                                item["score"]
                                *
                                item["weight"]
                                /
                                gamma_score[
                                    "available_weight"
                                ],
                                1
                            ),
                    }
                )
    
            score_df = pd.DataFrame(
                score_rows
            )
    
            st.dataframe(
                score_df,
                width="stretch",
                hide_index=True,
                height=min(
                    280,
                    45
                    +
                    len(score_df)
                    * 35
                )
            )
    
        st.caption(
            "Composite score is an analytical pressure model. "
            "It is not a guaranteed directional prediction and "
            "should not be interpreted as an automatic order signal."
        )
    
    if gamma_structure.get(
        "valid",
        False
    ):
    
        st.info(
            "Gamma Blast score is waiting for valid "
            "Greek-pressure inputs."
        )
    
        # ------------------------------------------------
        # STRUCTURE CARDS
        # ------------------------------------------------
    
        st.markdown(
            "#### Gamma Structure"
        )
    
        gs1, gs2, gs3, gs4, gs5 = st.columns(5)
    
        with gs1:
    
            st.metric(
                "SPOT",
                format_price(
                    spot
                )
            )
    
        with gs2:
    
            st.metric(
                "GAMMA FLIP",
                format_integer(
                    gamma_flip
                )
                if np.isfinite(
                    gamma_flip
                )
                else "—"
            )
    
        with gs3:
    
            st.metric(
                "GAMMA WALL",
                format_integer(
                    gamma_wall
                )
                if np.isfinite(
                    gamma_wall
                )
                else "—"
            )
    
        with gs4:
    
            st.metric(
                "WALL ABOVE",
                format_integer(
                    wall_above
                )
                if np.isfinite(
                    wall_above
                )
                else "—"
            )
    
        with gs5:
    
            st.metric(
                "WALL BELOW",
                format_integer(
                    wall_below
                )
                if np.isfinite(
                    wall_below
                )
                else "—"
            )
    
        # ------------------------------------------------
        # REGIME PANEL
        # ------------------------------------------------
    
        regime_color = "#00e59a"
    
        if "NEGATIVE" in regime:
    
            regime_color = "#ff4654"
    
        elif "FLIP" in regime:
    
            regime_color = "#f1c75b"
    
        st.html(
            dedent(
                f"""
                <div style="
                    display:grid;
                    grid-template-columns:1fr 1fr;
                    gap:10px;
                    margin-top:10px;
                ">
    
                    <div style="
                        background:#11151c;
                        border:1px solid #292e38;
                        border-radius:9px;
                        padding:14px;
                    ">
    
                        <div style="
                            color:#737d8d;
                            font-size:9px;
                            font-weight:800;
                            letter-spacing:1px;
                        ">
                            CURRENT GAMMA REGIME
                        </div>
    
                        <div style="
                            color:{regime_color};
                            font-size:20px;
                            font-weight:900;
                            margin-top:5px;
                        ">
                            {regime}
                        </div>
    
                    </div>
    
                    <div style="
                        background:#11151c;
                        border:1px solid #292e38;
                        border-radius:9px;
                        padding:14px;
                    ">
    
                        <div style="
                            color:#737d8d;
                            font-size:9px;
                            font-weight:800;
                            letter-spacing:1px;
                        ">
                            GAMMA LOCATION
                        </div>
    
                        <div style="
                            color:#f5f7fa;
                            font-size:20px;
                            font-weight:900;
                            margin-top:5px;
                        ">
                            {blast_zone}
                        </div>
    
                    </div>
    
                </div>
                """
            )
        )
    
        # ------------------------------------------------
        # FLIP / WALL DISTANCE
        # ------------------------------------------------
    
        flip_distance = gamma_structure[
            "flip_distance"
        ]
    
        wall_distance = gamma_structure[
            "wall_distance"
        ]
    
        st.caption(
            (
                f"Gamma Flip distance: "
                f"{flip_distance:+.0f} points • "
                f"Gamma Wall distance: "
                f"{wall_distance:+.0f} points"
            )
            if (
                np.isfinite(flip_distance)
                and np.isfinite(wall_distance)
            )
            else
            "Gamma flip/wall distance unavailable."
        )
    
        st.caption(
            "Gamma Flip represents the nearest cumulative "
            "gamma-pressure sign transition within the selected "
            "strike range. It is an analytical proxy, not dealer GEX."
        )
            # ========================================================
        # STEP 10 — GREEK DISTRIBUTION WORKSTATION
        # ========================================================
    
        st.markdown(
            "#### Greek Distribution"
        )
    
        gc1, gc2, gc3 = st.columns(3)
    
        with gc1:
    
            greek_metric_view = st.selectbox(
                "GREEK",
                [
                    "Delta",
                    "Gamma",
                    "Theta",
                    "Vega"
                ],
                index=0,
                key="step10_greek_metric"
            )
    
        with gc2:
    
            greek_side_view = st.selectbox(
                "SIDE",
                [
                    "CE + PE",
                    "CE",
                    "PE"
                ],
                index=0,
                key="step10_greek_side"
            )
    
        with gc3:
    
            greek_range_view = st.selectbox(
                "RANGE",
                [
                    "ATM ± 5",
                    "ATM ± 10",
                    "ATM ± 15",
                    "ATM ± 20"
                ],
                index=1,
                key="step10_greek_range"
            )
    
        greek_range_map = {
            "ATM ± 5": 5,
            "ATM ± 10": 10,
            "ATM ± 15": 15,
            "ATM ± 20": 20
        }
    
        greek_chart_range = greek_range_map.get(
            greek_range_view,
            10
        )
    
        distribution_chart = greek_by_strike_chart(
            greek_df,
            atm,
            metric=greek_metric_view,
            side=greek_side_view,
            range_count=greek_chart_range,
            height=350
        )
    
        if distribution_chart is not None:
    
            st.altair_chart(
                distribution_chart,
                width="stretch"
            )
    
        else:
    
            st.info(
                "No valid Greek distribution data "
                "is available for the selected range."
            )
    
        # ========================================================
        # GREEK EXPOSURE
        # ========================================================
    
        st.markdown(
            "#### Greek Exposure by Strike"
        )
    
        exposure_choice = st.selectbox(
            "EXPOSURE METRIC",
            [
                "Delta OI",
                "Gamma OI",
                "Theta OI",
                "Vega OI"
            ],
            index=1,
            key="step10_exposure_metric"
        )
    
        exposure_chart = greek_exposure_chart(
            greek_df,
            atm,
            metric=exposure_choice,
            range_count=greek_chart_range,
            height=320
        )
    
        if exposure_chart is not None:
    
            st.altair_chart(
                exposure_chart,
                width="stretch"
            )
    
        else:
    
            st.info(
                "No valid exposure data is available "
                "for the selected Greek."
            )
with tabs[5]:
    # ========================================================
    # STEP 11 — GREEK VISUAL ANALYTICS WORKSTATION
    # ========================================================

    st.markdown(
        "### Greek Visual Analytics"
    )

    # --------------------------------------------------------
    # CONTROLS
    # --------------------------------------------------------

    ga1, ga2, ga3 = st.columns(
        [1, 1, 1]
    )

    with ga1:

        greek_heat_side = st.selectbox(
            "HEATMAP SIDE",
            [
                "NET",
                "CE",
                "PE"
            ],
            index=0,
            key="step11_heatmap_side"
        )

    with ga2:

        greek_heat_range = st.selectbox(
            "HEATMAP RANGE",
            [
                5,
                10,
                15,
                20
            ],
            index=1,
            key="step11_heatmap_range"
        )


    # --------------------------------------------------------
    # HEATMAP
    # --------------------------------------------------------

    heatmap_chart = build_greek_heatmap(
        greek_df,
        atm,
        range_count=greek_heat_range,
        side=greek_heat_side
    )

    if heatmap_chart is not None:

        

        st.altair_chart(
            heatmap_chart,
            width="stretch"
        )

    else:

        st.info(
            "Greek heatmap is unavailable for "
            "the current snapshot."
        )

    # --------------------------------------------------------
    # CONCENTRATION
    # --------------------------------------------------------

    greek_concentration = (
        greek_concentration_summary(
            greek_df,
            atm,
            range_count=greek_heat_range
        )
    )

    st.markdown(
        "#### Greek Concentration"
    )

    cc1, cc2, cc3, cc4 = st.columns(4)

    concentration_items = [
        (
            cc1,
            "DELTA",
            greek_concentration.get(
                "delta_strike",
                np.nan
            ),
            "Highest |CE| + |PE|"
        ),
        (
            cc2,
            "GAMMA",
            greek_concentration.get(
                "gamma_strike",
                np.nan
            ),
            "Highest |CE| + |PE|"
        ),
        (
            cc3,
            "THETA",
            greek_concentration.get(
                "theta_strike",
                np.nan
            ),
            "Highest |CE| + |PE|"
        ),
        (
            cc4,
            "VEGA",
            greek_concentration.get(
                "vega_strike",
                np.nan
            ),
            "Highest |CE| + |PE|"
        )
    ]

    for container, label, strike, subtitle in concentration_items:

        with container:

            display_strike = (
                format_integer(
                    strike
                )
                if np.isfinite(
                    strike
                )
                else "—"
            )

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            {label} CONCENTRATION
                        </div>

                        <div class="metric-value"
                             style="font-size:20px;">
                            {display_strike}
                        </div>

                        <div class="metric-sub">
                            {subtitle}
                        </div>

                    </div>
                    """
                )
            )

    # --------------------------------------------------------
    # ATM GREEK MATRIX
    # --------------------------------------------------------

    st.markdown(
        "#### ATM Greek Matrix"
    )

    try:

        atm_index = (
            greek_df["strike"]
            - float(atm)
        ).abs().idxmin()

        atm_row = greek_df.loc[
            atm_index
        ]

        matrix_rows = []

        greek_matrix_definition = [
            (
                "DELTA",
                "ce_delta",
                "pe_delta"
            ),
            (
                "GAMMA",
                "ce_gamma",
                "pe_gamma"
            ),
            (
                "THETA",
                "ce_theta",
                "pe_theta"
            ),
            (
                "VEGA",
                "ce_vega",
                "pe_vega"
            )
        ]

        for label, ce_col, pe_col in greek_matrix_definition:

            ce_value = safe_number(
                atm_row.get(
                    ce_col,
                    np.nan
                ),
                np.nan
            )

            pe_value = safe_number(
                atm_row.get(
                    pe_col,
                    np.nan
                ),
                np.nan
            )

            if (
                np.isfinite(ce_value)
                and np.isfinite(pe_value)
            ):

                net_value = (
                    ce_value
                    + pe_value
                )

            else:

                net_value = np.nan

            matrix_rows.append(
                {
                    "GREEK": label,
                    "CE": ce_value,
                    "PE": pe_value,
                    "NET": net_value
                }
            )

        greek_matrix_df = pd.DataFrame(
            matrix_rows
        )

        st.dataframe(
            greek_matrix_df,
            width="stretch",
            hide_index=True,
            height=190
        )

    except Exception as e:

        st.caption(
            f"ATM Greek matrix unavailable: {e}"
        )
        # ========================================================
    # STEP 12 — HISTORICAL GREEK INTELLIGENCE UI
    # ========================================================

    st.markdown(
        "### Historical Greek Intelligence"
    )
    # ========================================================
    # STEP 13 — GREEK SIGNAL FUSION UI
    # ========================================================

    st.markdown(
        "### Greek Signal Fusion"
    )

    historical_intel = historical_greek_intelligence(
        None
    )

    # --------------------------------------------------------
    # SIGNAL ENGINE
    # --------------------------------------------------------

    def greek_signal_fusion(
        historical_intel,
        greek_df=None
    ):
        """Combine available historical Greek changes into one signal."""

        result = {
            "valid": False,
            "score": 0.0,
            "confidence": 0.0,
            "regime": "NEUTRAL",
            "components": {},
            "explanation": "Insufficient Greek information.",
        }

        if not isinstance(historical_intel, dict):
            return result

        weights = {
            "delta": 0.40,
            "gamma": 0.25,
            "theta": 0.15,
            "vega": 0.20,
        }
        components = {}

        for greek, weight in weights.items():
            values = historical_intel.get(greek, {})
            if not isinstance(values, dict) or not values:
                continue

            change = safe_number(
                values.get(
                    "change",
                    values.get("pct_change", 0)
                ),
                0
            )
            signal = 1 if change > 0 else -1 if change < 0 else 0
            components[greek] = {
                "signal": signal,
                "strength": min(abs(change) * 100, 100),
                "weight": weight,
            }

        if not components:
            return result

        total_weight = sum(
            item["weight"]
            for item in components.values()
        )
        score = sum(
            item["signal"] * item["strength"] * item["weight"]
            for item in components.values()
        ) / total_weight
        confidence = sum(
            item["strength"] * item["weight"]
            for item in components.values()
        ) / total_weight

        regime = (
            "BULLISH"
            if score >= 20
            else "BEARISH"
            if score <= -20
            else "NEUTRAL"
        )

        result.update(
            {
                "valid": True,
                "score": float(max(-100, min(100, score))),
                "confidence": float(max(0, min(100, confidence))),
                "regime": regime,
                "components": components,
                "explanation": f"Greek regime: {regime}.",
            }
        )
        return result

    greek_fusion = greek_signal_fusion(
        historical_intel,
        greek_df
    )

    if greek_fusion.get(
        "valid",
        False
    ):

        fusion_score = greek_fusion.get(
            "score",
            0
        )

        fusion_confidence = greek_fusion.get(
            "confidence",
            0
        )

        fusion_regime = greek_fusion.get(
            "regime",
            "NEUTRAL"
        )

        # ====================================================
        # TOP SUMMARY
        # ====================================================

        fs1, fs2, fs3 = st.columns(
            [1, 1, 1]
        )

        with fs1:

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            GREEK SIGNAL SCORE
                        </div>

                        <div class="metric-value"
                             style="font-size:26px;">
                            {fusion_score:+.1f}
                        </div>

                        <div class="metric-sub">
                            RANGE −100 TO +100
                        </div>

                    </div>
                    """
                )
            )

        with fs2:

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            GREEK CONFIDENCE
                        </div>

                        <div class="metric-value"
                             style="font-size:26px;">
                            {fusion_confidence:.0f}%
                        </div>

                        <div class="metric-sub">
                            SIGNAL STRENGTH
                        </div>

                    </div>
                    """
                )
            )

        with fs3:

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            GREEK REGIME
                        </div>

                        <div class="metric-value"
                             style="font-size:22px;">
                            {fusion_regime}
                        </div>

                        <div class="metric-sub">
                            COMBINED GREEK READING
                        </div>

                    </div>
                    """
                )
            )

        # ====================================================
        # COMPONENT MATRIX
        # ====================================================

        st.markdown(
            "#### Greek Signal Matrix"
        )

        component_rows = []

        for greek in [
            "delta",
            "gamma",
            "theta",
            "vega"
        ]:

            data = greek_fusion.get(
                "components",
                {}
            ).get(
                greek,
                {}
            )

            if not data:
                continue

            signal = data.get(
                "signal",
                0
            )

            strength = data.get(
                "strength",
                0
            )

            if signal > 0:

                direction = "BULLISH"

            elif signal < 0:

                direction = "BEARISH"

            else:

                direction = "NEUTRAL"

            component_rows.append(
                {
                    "GREEK":
                        greek.upper(),

                    "DIRECTION":
                        direction,

                    "STRENGTH":
                        f"{strength:.0f}%",

                    "WEIGHT":
                        f"{data.get('weight', 0) * 100:.0f}%"
                }
            )

        if component_rows:

            component_df = pd.DataFrame(
                component_rows
            )

            st.dataframe(
                component_df,
                width="stretch",
                hide_index=True,
                height=185
            )

        # ====================================================
        # INTERPRETATION
        # ====================================================

        st.html(
            dedent(
                f"""
                <div style="
                    margin-top:8px;
                    padding:14px 16px;
                    border:1px solid #252c36;
                    border-radius:10px;
                    background:#0d1117;
                ">

                    <div style="
                        color:#7f8998;
                        font-size:9px;
                        font-weight:900;
                        letter-spacing:1px;
                    ">
                        COMBINED GREEK READING
                    </div>

                    <div style="
                        margin-top:7px;
                        color:#e7ebf0;
                        font-size:13px;
                        font-weight:700;
                    ">
                        {greek_fusion.get(
                            "explanation",
                            "No clear Greek alignment."
                        )}
                    </div>

                </div>
                """
            )
        )

    else:

        st.info(
            "Greek signal fusion requires "
            "multiple historical Greek snapshots."
        )
    # ========================================================
    # STEP 14 — FINAL DERIVATIVES INTELLIGENCE UI
    # ========================================================

    st.markdown(
        "### Derivatives Intelligence"
    )

    pcr = greek_metrics.get(
        "range_oi_pcr",
        np.nan
    )
    max_pain = None

    def derivatives_intelligence_summary(
        greek_fusion=None,
        greek_intel=None,
        gamma_blast=None,
        pcr=None,
        max_pain=None,
        spot=None
    ):
        """Return a safe combined derivatives summary for the dashboard."""

        greek_fusion = (
            greek_fusion
            if isinstance(greek_fusion, dict)
            else {}
        )
        greek_intel = (
            greek_intel
            if isinstance(greek_intel, dict)
            else {}
        )

        greek_score = safe_number(
            greek_fusion.get("score", 0),
            0
        )
        greek_confidence = safe_number(
            greek_fusion.get("confidence", 0),
            0
        )
        pcr_value = safe_number(pcr, np.nan)
        structural_bias = 0.0

        if np.isfinite(pcr_value):
            if pcr_value >= 1.10:
                structural_bias = 20.0
            elif pcr_value >= 1.00:
                structural_bias = 10.0
            elif pcr_value <= 0.90:
                structural_bias = -20.0
            elif pcr_value < 1.00:
                structural_bias = -10.0

        score = max(
            -100.0,
            min(100.0, greek_score * 0.75 + structural_bias * 0.25)
        )
        bias = (
            "BULLISH"
            if score >= 20
            else "BEARISH"
            if score <= -20
            else "NEUTRAL"
        )
        gamma_data = greek_intel.get("gamma", {})
        vega_data = greek_intel.get("vega", {})
        gamma_regime = (
            gamma_data.get("regime", "UNKNOWN")
            if isinstance(gamma_data, dict)
            else "UNKNOWN"
        )
        volatility_regime = "UNKNOWN"
        if isinstance(vega_data, dict):
            volatility_regime = {
                "RISING": "RISING",
                "FALLING": "FALLING",
            }.get(vega_data.get("momentum"), "STABLE")

        return {
            "valid": bool(greek_fusion.get("valid", False)),
            "bias": bias,
            "confidence": float(max(0, min(100, greek_confidence))),
            "greek_score": float(greek_score),
            "gamma_regime": gamma_regime,
            "volatility_regime": volatility_regime,
            "summary": "Derivatives structure is mixed.",
        }

    final_intelligence = (
        derivatives_intelligence_summary(
            greek_fusion=greek_fusion,
            greek_intel=historical_intel,
            pcr=pcr,
            max_pain=max_pain,
            spot=spot
        )
    )

    if final_intelligence.get(
        "valid",
        False
    ):

        # ----------------------------------------------------
        # TOP SUMMARY CARDS
        # ----------------------------------------------------

        di1, di2, di3, di4 = st.columns(4)

        with di1:

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            MARKET BIAS
                        </div>

                        <div class="metric-value"
                             style="font-size:21px;">
                            {final_intelligence["bias"]}
                        </div>

                        <div class="metric-sub">
                            DERIVATIVES STRUCTURE
                        </div>

                    </div>
                    """
                )
            )

        with di2:

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            CONFIDENCE
                        </div>

                        <div class="metric-value"
                             style="font-size:21px;">
                            {final_intelligence["confidence"]:.0f}%
                        </div>

                        <div class="metric-sub">
                            ANALYTICAL CONFIDENCE
                        </div>

                    </div>
                    """
                )
            )

        with di3:

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            GAMMA REGIME
                        </div>

                        <div class="metric-value"
                             style="font-size:18px;">
                            {final_intelligence["gamma_regime"]}
                        </div>

                        <div class="metric-sub">
                            GAMMA STRUCTURE
                        </div>

                    </div>
                    """
                )
            )

        with di4:

            st.html(
                dedent(
                    f"""
                    <div class="metric-card">

                        <div class="metric-label">
                            VOLATILITY
                        </div>

                        <div class="metric-value"
                             style="font-size:18px;">
                            {final_intelligence["volatility_regime"]}
                        </div>

                        <div class="metric-sub">
                            VEGA REGIME
                        </div>

                    </div>
                    """
                )
            )

        # ----------------------------------------------------
        # FINAL READING
        # ----------------------------------------------------

        st.html(
            dedent(
                f"""
                <div style="
                    margin-top:10px;
                    padding:16px 18px;
                    border:1px solid #29313c;
                    border-radius:11px;
                    background:#0c1117;
                ">

                    <div style="
                        color:#7e8999;
                        font-size:9px;
                        font-weight:900;
                        letter-spacing:1px;
                    ">
                        FINAL DERIVATIVES READING
                    </div>

                    <div style="
                        margin-top:8px;
                        color:#edf1f5;
                        font-size:14px;
                        font-weight:800;
                    ">
                        {final_intelligence["summary"]}
                    </div>

                    <div style="
                        margin-top:9px;
                        color:#707b8b;
                        font-size:9px;
                        line-height:1.5;
                    ">
                        Analytical regime summary only.
                        This is not a trading recommendation.
                    </div>

                </div>
                """
            )
        )

    else:

        st.info(
            "Final derivatives intelligence will become "
            "available once sufficient Greek history exists."
        )
    # --------------------------------------------------------
    # PREPARE HISTORY
    # --------------------------------------------------------

    historical_source = None

    # Try the known historical Greek dataframe
    # used by the existing Greek history section.

    for candidate_name in [
        "greek_history_df",
        "historical_greek_df",
        "greek_history",
        "history_df"
    ]:

        candidate = locals().get(
            candidate_name
        )

        if isinstance(
            candidate,
            pd.DataFrame
        ):

            if not candidate.empty:

                historical_source = candidate
                break


    # --------------------------------------------------------
    # FALLBACK — BUILD FROM STORED SNAPSHOTS
    # --------------------------------------------------------

    snapshot_history = None

    if historical_source is None:

        if isinstance(
            snapshot_history,
            pd.DataFrame
        ):

            historical_source = snapshot_history


    # --------------------------------------------------------
    # INTELLIGENCE ENGINE
    # --------------------------------------------------------

    historical_intel = (
        historical_greek_intelligence(
            historical_source
        )
        if historical_source is not None
        else {
            "valid": False,
            "data": pd.DataFrame()
        }
    )


    if historical_intel.get(
        "valid",
        False
    ):

        # ====================================================
        # PRIMARY GREEK MOMENTUM CARDS
        # ====================================================

        h1, h2, h3, h4 = st.columns(4)

        historical_cards = [
            (
                h1,
                "DELTA",
                historical_intel.get(
                    "delta",
                    {}
                )
            ),
            (
                h2,
                "GAMMA",
                historical_intel.get(
                    "gamma",
                    {}
                )
            ),
            (
                h3,
                "THETA",
                historical_intel.get(
                    "theta",
                    {}
                )
            ),
            (
                h4,
                "VEGA",
                historical_intel.get(
                    "vega",
                    {}
                )
            )
        ]

        for container, label, data in historical_cards:

            with container:

                if not data:

                    current_text = "—"
                    change_text = "—"
                    momentum_text = "NO DATA"
                    regime_text = "—"

                else:

                    current_value = data.get(
                        "current",
                        np.nan
                    )

                    change_value = data.get(
                        "pct_change",
                        np.nan
                    )

                    if np.isfinite(
                        current_value
                    ):

                        current_text = (
                            f"{current_value:,.5f}"
                        )

                    else:

                        current_text = "—"

                    if np.isfinite(
                        change_value
                    ):

                        change_text = (
                            f"{change_value:+.2f}%"
                        )

                    else:

                        change_text = "—"

                    momentum_text = data.get(
                        "momentum",
                        "—"
                    )

                    regime_text = data.get(
                        "regime",
                        "—"
                    )

                st.html(
                    dedent(
                        f"""
                        <div class="metric-card">

                            <div class="metric-label">
                                {label}
                            </div>

                            <div class="metric-value"
                                 style="font-size:19px;">
                                {current_text}
                            </div>

                            <div style="
                                margin-top:5px;
                                color:#9aa4b3;
                                font-size:10px;
                                font-weight:800;
                            ">
                                CHANGE&nbsp;&nbsp;
                                {change_text}
                            </div>

                            <div style="
                                margin-top:6px;
                                color:#dfe5ec;
                                font-size:9px;
                                font-weight:900;
                                letter-spacing:.5px;
                            ">
                                {momentum_text}
                                &nbsp;•&nbsp;
                                {regime_text}
                            </div>

                        </div>
                        """
                    )
                )

        # ====================================================
        # REGIME PANEL
        # ====================================================

        st.markdown(
            "#### Greek Regime Monitor"
        )

        rg1, rg2 = st.columns(
            [1, 1]
        )

        # ----------------------------------------------------
        # LEFT — REGIME
        # ----------------------------------------------------

        with rg1:

            regime_rows = []

            for greek in [
                "delta",
                "gamma",
                "theta",
                "vega"
            ]:

                data = historical_intel.get(
                    greek,
                    {}
                )

                if not data:
                    continue

                regime_rows.append(
                    {
                        "GREEK":
                            greek.upper(),

                        "CURRENT":
                            data.get(
                                "current",
                                np.nan
                            ),

                        "CHANGE %":
                            data.get(
                                "pct_change",
                                np.nan
                            ),

                        "MOMENTUM":
                            data.get(
                                "momentum",
                                "—"
                            ),

                        "REGIME":
                            data.get(
                                "regime",
                                "—"
                            )
                    }
                )

            if regime_rows:

                regime_df = pd.DataFrame(
                    regime_rows
                )

                st.dataframe(
                    regime_df,
                    width="stretch",
                    hide_index=True,
                    height=190
                )

        # ----------------------------------------------------
        # RIGHT — CHANGE / ACCELERATION
        # ----------------------------------------------------

        with rg2:

            change_rows = []

            for greek in [
                "delta",
                "gamma",
                "theta",
                "vega"
            ]:

                data = historical_intel.get(
                    greek,
                    {}
                )

                if not data:
                    continue

                change_rows.append(
                    {
                        "GREEK":
                            greek.upper(),

                        "Δ":
                            data.get(
                                "change",
                                np.nan
                            ),

                        "Δ %":
                            data.get(
                                "pct_change",
                                np.nan
                            ),

                        "ACCELERATION":
                            data.get(
                                "acceleration",
                                np.nan
                            ),

                        "STATE":
                            data.get(
                                "acceleration_state",
                                "—"
                            )
                    }
                )

            if change_rows:

                change_df = pd.DataFrame(
                    change_rows
                )

                st.dataframe(
                    change_df,
                    width="stretch",
                    hide_index=True,
                    height=190
                )

        # ====================================================
        # MOMENTUM CHART
        # ====================================================

        history_plot = (
            historical_intel.get(
                "data",
                pd.DataFrame()
            )
        )

        if (
            isinstance(
                history_plot,
                pd.DataFrame
            )
            and not history_plot.empty
        ):

            available_greeks = [
                greek
                for greek in [
                    "delta",
                    "gamma",
                    "theta",
                    "vega"
                ]
                if greek in history_plot.columns
            ]

            if available_greeks:

                selected_historical_greek = (
                    st.selectbox(
                        "HISTORICAL GREEK",
                        available_greeks,
                        index=0,
                        key="step12_historical_greek"
                    )
                )

                plot_df = history_plot[
                    [
                        "timestamp",
                        selected_historical_greek
                    ]
                ].dropna()

                if not plot_df.empty:

                    historical_chart = (
                        alt.Chart(
                            plot_df
                        )
                        .mark_line(
                            strokeWidth=2
                        )
                        .encode(

                            x=alt.X(
                                "timestamp:T",
                                title=None
                            ),

                            y=alt.Y(
                                f"{selected_historical_greek}:Q",
                                title=
                                    selected_historical_greek.upper()
                            ),

                            tooltip=[
                                alt.Tooltip(
                                    "timestamp:T",
                                    title="Time"
                                ),
                                alt.Tooltip(
                                    f"{selected_historical_greek}:Q",
                                    title=
                                        selected_historical_greek.upper(),
                                    format=",.6f"
                                )
                            ]
                        )
                        .properties(
                            height=280
                        )
                        .interactive()
                    )

                    st.altair_chart(
                        historical_chart,
                        width="stretch"
                    )

    else:

        st.info(
            "Historical Greek intelligence will appear "
            "once multiple Greek snapshots are available."
        )
        # ============================================================
# STEP 13 — GREEK SIGNAL FUSION ENGINE
# ============================================================

def greek_signal_fusion(
    historical_intel,
    greek_df=None
):
    """
    Combines Delta, Gamma, Theta and Vega intelligence
    into a single Greek regime / signal assessment.

    Output:
        score       : -100 to +100
        confidence  : 0 to 100
        regime      : BULLISH / BEARISH / NEUTRAL
        components  : per-Greek contribution
        explanation : human-readable interpretation
    """

    result = {
        "valid": False,

        "score": 0.0,
        "confidence": 0.0,

        "regime": "NEUTRAL",

        "components": {},

        "explanation": (
            "Insufficient Greek information."
        )
    }

    if not isinstance(
        historical_intel,
        dict
    ):
        return result

    weights = {
        "delta": 0.40,
        "gamma": 0.25,
        "theta": 0.15,
        "vega": 0.20
    }

    components = {}
    
    # ============================================================
# STEP 14 — FINAL DERIVATIVES INTELLIGENCE ENGINE
# ============================================================

def derivatives_intelligence_summary(
    greek_fusion=None,
    greek_intel=None,
    gamma_blast=None,
    pcr=None,
    max_pain=None,
    spot=None
):
    """
    Final analytical summary combining the Greek,
    Gamma and market-structure layers.

    This is an analytical regime summary only.
    It does NOT generate a BUY / SELL recommendation.
    """

    result = {
        "valid": False,

        "bias": "NEUTRAL",
        "confidence": 0.0,

        "greek_score": 0.0,
        "gamma_regime": "UNKNOWN",
        "volatility_regime": "UNKNOWN",

        "summary": (
            "Insufficient derivatives information."
        )
    }

    # --------------------------------------------------------
    # GREEK SIGNAL
    # --------------------------------------------------------

    if isinstance(
        greek_fusion,
        dict
    ):

        greek_score = safe_number(
            greek_fusion.get(
                "score",
                0
            ),
            0
        )

        greek_confidence = safe_number(
            greek_fusion.get(
                "confidence",
                0
            ),
            0
        )

    else:

        greek_score = 0.0
        greek_confidence = 0.0

    # --------------------------------------------------------
    # GAMMA REGIME
    # --------------------------------------------------------

    gamma_regime = "UNKNOWN"

    if isinstance(
        greek_intel,
        dict
    ):

        gamma_data = greek_intel.get(
            "gamma",
            {}
        )

        if isinstance(
            gamma_data,
            dict
        ):

            gamma_regime = gamma_data.get(
                "regime",
                "UNKNOWN"
            )

    # --------------------------------------------------------
    # VOLATILITY REGIME
    # --------------------------------------------------------

    volatility_regime = "UNKNOWN"

    if isinstance(
        greek_intel,
        dict
    ):

        vega_data = greek_intel.get(
            "vega",
            {}
        )

        if isinstance(
            vega_data,
            dict
        ):

            vega_momentum = vega_data.get(
                "momentum",
                "FLAT"
            )

            if vega_momentum == "RISING":

                volatility_regime = "RISING"

            elif vega_momentum == "FALLING":

                volatility_regime = "FALLING"

            else:

                volatility_regime = "STABLE"

    # --------------------------------------------------------
    # STRUCTURAL BIAS
    # --------------------------------------------------------

    structural_bias = 0.0

    if pcr is not None:

        pcr_value = safe_number(
            pcr,
            np.nan
        )

        if np.isfinite(
            pcr_value
        ):

            if pcr_value >= 1.10:

                structural_bias += 20

            elif pcr_value >= 1.00:

                structural_bias += 10

            elif pcr_value <= 0.90:

                structural_bias -= 20

            elif pcr_value < 1.00:

                structural_bias -= 10

    # --------------------------------------------------------
    # FINAL SCORE
    # --------------------------------------------------------

    final_score = (
        greek_score * 0.75
        + structural_bias * 0.25
    )

    final_score = max(
        -100,
        min(
            100,
            final_score
        )
    )

    # --------------------------------------------------------
    # BIAS
    # --------------------------------------------------------

    if final_score >= 20:

        bias = "BULLISH"

    elif final_score <= -20:

        bias = "BEARISH"

    else:

        bias = "NEUTRAL"

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    confidence = (
        greek_confidence * 0.80
        + min(
            abs(structural_bias) * 5,
            100
        ) * 0.20
    )

    confidence = max(
        0,
        min(
            100,
            confidence
        )
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    summary_parts = []

    if bias == "BULLISH":

        summary_parts.append(
            "Derivatives structure is leaning bullish"
        )

    elif bias == "BEARISH":

        summary_parts.append(
            "Derivatives structure is leaning bearish"
        )

    else:

        summary_parts.append(
            "Derivatives structure is mixed"
        )

    if gamma_regime != "UNKNOWN":

        summary_parts.append(
            f"Gamma is {gamma_regime.lower()}"
        )

    if volatility_regime != "UNKNOWN":

        summary_parts.append(
            f"volatility sensitivity is "
            f"{volatility_regime.lower()}"
        )

    result.update(
        {
            "valid": True,

            "bias": bias,

            "confidence": float(
                confidence
            ),

            "greek_score": float(
                greek_score
            ),

            "gamma_regime":
                gamma_regime,

            "volatility_regime":
                volatility_regime,

            "summary":
                " • ".join(
                    summary_parts
                )
        }
    )

    return result

    # --------------------------------------------------------
    # DELTA
    # --------------------------------------------------------

    delta = historical_intel.get(
        "delta",
        {}
    )

    if delta:

        delta_change = safe_number(
            delta.get(
                "change",
                0
            ),
            0
        )

        if delta_change > 0:

            delta_signal = 1

        elif delta_change < 0:

            delta_signal = -1

        else:

            delta_signal = 0

        components["delta"] = {
            "signal": delta_signal,
            "strength": min(
                abs(delta_change) * 100,
                100
            ),
            "weight": weights["delta"]
        }

    # --------------------------------------------------------
    # GAMMA
    # --------------------------------------------------------

    gamma = historical_intel.get(
        "gamma",
        {}
    )

    if gamma:

        gamma_change = safe_number(
            gamma.get(
                "pct_change",
                0
            ),
            0
        )

        if gamma_change > 0:

            gamma_signal = 1

        elif gamma_change < 0:

            gamma_signal = -1

        else:

            gamma_signal = 0

        components["gamma"] = {
            "signal": gamma_signal,
            "strength": min(
                abs(gamma_change),
                100
            ),
            "weight": weights["gamma"]
        }

    # --------------------------------------------------------
    # THETA
    # --------------------------------------------------------

    theta = historical_intel.get(
        "theta",
        {}
    )

    if theta:

        theta_change = safe_number(
            theta.get(
                "pct_change",
                0
            ),
            0
        )

        # More negative theta = stronger decay.
        # For directional signal, theta alone is neutral.
        theta_signal = 0

        components["theta"] = {
            "signal": theta_signal,
            "strength": min(
                abs(theta_change),
                100
            ),
            "weight": weights["theta"]
        }

    # --------------------------------------------------------
    # VEGA
    # --------------------------------------------------------

    vega = historical_intel.get(
        "vega",
        {}
    )

    if vega:

        vega_change = safe_number(
            vega.get(
                "pct_change",
                0
            ),
            0
        )

        if vega_change > 0:

            vega_signal = 1

        elif vega_change < 0:

            vega_signal = -1

        else:

            vega_signal = 0

        components["vega"] = {
            "signal": vega_signal,
            "strength": min(
                abs(vega_change),
                100
            ),
            "weight": weights["vega"]
        }

    if not components:
        return result

    # --------------------------------------------------------
    # WEIGHTED SCORE
    # --------------------------------------------------------

    weighted_score = 0.0
    total_weight = 0.0
    strength_total = 0.0

    for data in components.values():

        signal = data["signal"]
        strength = data["strength"]
        weight = data["weight"]

        weighted_score += (
            signal
            * strength
            * weight
        )

        total_weight += weight

        strength_total += (
            strength
            * weight
        )

    if total_weight > 0:

        score = (
            weighted_score
            / total_weight
        )

        confidence = (
            strength_total
            / total_weight
        )

    else:

        score = 0.0
        confidence = 0.0

    score = max(
        -100,
        min(
            100,
            score
        )
    )

    confidence = max(
        0,
        min(
            100,
            confidence
        )
    )

    # --------------------------------------------------------
    # REGIME
    # --------------------------------------------------------

    if score >= 20:

        regime = "BULLISH"

    elif score <= -20:

        regime = "BEARISH"

    else:

        regime = "NEUTRAL"

    # --------------------------------------------------------
    # EXPLANATION
    # --------------------------------------------------------

    positive = []
    negative = []

    for greek, data in components.items():

        if data["signal"] > 0:

            positive.append(
                greek.upper()
            )

        elif data["signal"] < 0:

            negative.append(
                greek.upper()
            )

    explanation_parts = []

    if positive:

        explanation_parts.append(
            "Positive "
            + ", ".join(
                positive
            )
        )

    if negative:

        explanation_parts.append(
            "Negative "
            + ", ".join(
                negative
            )
        )

    if not explanation_parts:

        explanation_parts.append(
            "Greek components are mixed or stable"
        )

    explanation = (
        " • ".join(
            explanation_parts
        )
    )

    result.update(
        {
            "valid": True,

            "score": float(
                score
            ),

            "confidence": float(
                confidence
            ),

            "regime": regime,

            "components": components,

            "explanation": explanation
        }
    )

    return result
    # --------------------------------------------------------
    # HISTORICAL GREEK SNAPSHOT CHART
    # --------------------------------------------------------

    st.markdown("### Historical Greek Snapshot")

    hist1, hist2, hist3, hist4 = st.columns(4)

    available_hist_strikes = sorted(
        pd.to_numeric(
            greek_df.get("strike", pd.Series(dtype=float)),
            errors="coerce"
        ).dropna().unique().tolist()
    )

    hist_default_index = 0
    if available_hist_strikes:
        hist_default_index = min(
            range(len(available_hist_strikes)),
            key=lambda i: abs(available_hist_strikes[i] - float(atm))
        )

    with hist1:
        greek_history_strike = st.selectbox(
            "STRIKE",
            available_hist_strikes if available_hist_strikes else [atm],
            index=hist_default_index if available_hist_strikes else 0,
            key="greek_history_strike"
        )

    with hist2:
        greek_history_side = st.selectbox(
            "OPTION",
            ["CE", "PE"],
            index=0,
            key="greek_history_side"
        )

    with hist3:
        greek_history_metric = st.selectbox(
            "METRIC",
            ["IV", "DELTA", "GAMMA", "THETA", "VEGA", "POP"],
            index=0,
            key="greek_history_metric"
        )

    with hist4:
        greek_history_range = st.selectbox(
            "HISTORY",
            ["ALL", "LAST 20", "LAST 50", "LAST 100"],
            index=2,
            key="greek_history_range"
        )

    try:
        greek_history_df = get_greek_history(
            strike=greek_history_strike,
            option_type=greek_history_side,
            expiry=selected_expiry
        )
    except Exception:
        greek_history_df = pd.DataFrame()

    if not greek_history_df.empty and greek_history_range != "ALL":
        history_limit = {
            "LAST 20": 20,
            "LAST 50": 50,
            "LAST 100": 100,
        }.get(greek_history_range, len(greek_history_df))
        greek_history_df = greek_history_df.tail(history_limit).copy()

    history_chart = historical_greek_chart(
        greek_history_df,
        greek_history_side,
        greek_history_metric,
        height=300
    )

    if history_chart is not None:
        st.altair_chart(
            history_chart,
            width="stretch"
        )
    else:
        st.info(
            "No historical Greek snapshots are available for this strike/expiry yet. "
            "Keep refresh enabled or use the manual refresh button to build the series."
        )


# ============================================================
# TAB 7 — PCR
# ============================================================

with tabs[6]:

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

with tabs[7]:

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
            dedent("""
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
            """).format(pcr_value=metrics["pcr_bias"]),
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
            dedent("""
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
            """).format(oi_color=oi_color, oi_value=oi_signal),
            unsafe_allow_html=True
        )

    with s3:

        st.markdown(
            dedent("""
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
            """).format(
                market_value=bias,
                score_value=metrics["score"]
            ),
            unsafe_allow_html=True
        )


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

with tabs[8]:

    render_strategy_tab(
        df=df,
        spot=spot,
        atm=atm,
        expiry=expiry
    )


# ============================================================
# DATA QUALITY FOOTER
# ============================================================

with tabs[1]:

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
# ============================================================
# TAB 9 — BACKTEST
# ============================================================

with tabs[9]:

    render_backtest_page()
    
# ============================================================
# TAB 10 — HISTORICAL ANALYTICS
# ============================================================

with tabs[10]:

    st.markdown(
        '<div class="section-title">Historical Analytics</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # LOAD AVAILABLE HISTORY
    # --------------------------------------------------------

    history_df = load_history()

    if history_df.empty:

        st.warning(
            "No historical option-chain data available."
        )

    else:

        # ----------------------------------------------------
        # CONTROLS
        # ----------------------------------------------------

        control1, control2, control3, control4, control5 = st.columns(5)

        available_expiries = sorted(
            history_df["expiry"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        with control1:

            historical_expiry = st.selectbox(
                "EXPIRY",
                available_expiries,
                index=(
                    available_expiries.index(
                        str(selected_expiry)
                    )
                    if str(selected_expiry)
                    in available_expiries
                    else 0
                ),
                key="historical_expiry"
            )

        expiry_history = history_df[
            history_df["expiry"].astype(str)
            == str(historical_expiry)
        ].copy()

        available_strikes = sorted(
            expiry_history["strike"]
            .dropna()
            .unique()
            .tolist()
        )

        historical_atm = get_atm_strike(
            expiry=historical_expiry
        )

        with control2:

            strike_options = available_strikes

            strike_index = 0

            if (
                historical_atm is not None
                and historical_atm in strike_options
            ):
                strike_index = strike_options.index(
                    historical_atm
                )

            historical_strike = st.selectbox(
                "STRIKE",
                strike_options,
                index=strike_index,
                key="historical_strike"
            )

        with control3:

            option_type = st.selectbox(
                "OPTION",
                [
                    "CE",
                    "PE"
                ],
                key="historical_option"
            )

        with control4:

            metric = st.selectbox(
                "METRIC",
                [
                    "IV",
                    "DELTA",
                    "GAMMA",
                    "THETA",
                    "VEGA",
                    "POP",
                    "LTP",
                    "OI",
                    "OI CHANGE",
                ],
                key="historical_metric"
            )
        with control5:

            history_range = st.selectbox(
                "HISTORY",
                [
                    "ALL",
                    "LAST 20",
                    "LAST 50",
                    "LAST 100"
                ],
                key="historical_range"
            )    

        # ----------------------------------------------------
        # METRIC DATA
        # ----------------------------------------------------

        prefix = option_type.lower()

        if metric in [
            "IV",
            "DELTA",
            "GAMMA",
            "THETA",
            "VEGA",
            "POP"
        ]:

            greek_history = get_greek_history(
                strike=historical_strike,
                option_type=option_type,
                expiry=historical_expiry
            )

            metric_column = (
                f"{prefix}_"
                f"{metric.lower()}"
            )

            chart_df = greek_history[
                [
                    "fetch_time",
                    metric_column
                ]
            ].copy()

            chart_df = chart_df.rename(
                columns={
                    metric_column: "value"
                }
            )

        elif metric == "LTP":

            price_history = get_price_history(
                strike=historical_strike,
                expiry=historical_expiry
            )

            metric_column = (
                f"{prefix}_ltp"
            )

            chart_df = price_history[
                [
                    "fetch_time",
                    metric_column
                ]
            ].copy()

            chart_df = chart_df.rename(
                columns={
                    metric_column: "value"
                }
            )

        elif metric == "OI":

            oi_history = get_oi_history(
                strike=historical_strike,
                expiry=historical_expiry
            )

            metric_column = (
                f"{prefix}_oi"
            )

            chart_df = oi_history[
                [
                    "fetch_time",
                    metric_column
                ]
            ].copy()

            chart_df = chart_df.rename(
                columns={
                    metric_column: "value"
                }
            )

        else:

            oi_history = get_oi_history(
                strike=historical_strike,
                expiry=historical_expiry
            )

            metric_column = (
                f"{prefix}_oi_change"
            )

            chart_df = oi_history[
                [
                    "fetch_time",
                    metric_column
                ]
            ].copy()

            chart_df = chart_df.rename(
                columns={
                    metric_column: "value"
                }
            )

        # ----------------------------------------------------
        # CLEAN DATA
        # ----------------------------------------------------

        chart_df["fetch_time"] = pd.to_datetime(
            chart_df["fetch_time"],
            errors="coerce"
        )

        chart_df["value"] = pd.to_numeric(
            chart_df["value"],
            errors="coerce"
        )

        chart_df = chart_df.dropna(
            subset=[
                "fetch_time",
                "value"
            ]
        )
                # ----------------------------------------------------
        # HISTORY RANGE FILTER
        # ----------------------------------------------------

        if history_range != "ALL":

            range_map = {
                "LAST 20": 20,
                "LAST 50": 50,
                "LAST 100": 100
            }

            limit = range_map.get(
                history_range,
                len(chart_df)
            )

            chart_df = chart_df.tail(
                limit
            ).reset_index(drop=True)

        # ----------------------------------------------------
        # CURRENT VALUE CARDS
        # ----------------------------------------------------

        if not chart_df.empty:

            latest_value = chart_df[
                "value"
            ].iloc[-1]

            previous_value = (
                chart_df["value"].iloc[-2]
                if len(chart_df) > 1
                else np.nan
            )

            change = (
                latest_value - previous_value
                if not pd.isna(previous_value)
                else np.nan
            )

            m1, m2, m3, m4 = st.columns(4)

            with m1:

                st.metric(
                    "STRIKE",
                    format_integer(
                        historical_strike
                    )
                )

            with m2:

                st.metric(
                    f"{option_type} {metric}",
                    f"{latest_value:.4f}"
                )

            with m3:

                if pd.isna(change):

                    st.metric(
                        "CHANGE",
                        "—"
                    )

                else:

                    st.metric(
                        "CHANGE",
                        f"{change:+.4f}"
                    )

            with m4:

                st.metric(
                    "SNAPSHOTS",
                    len(chart_df)
                )
with tabs[1]:
            # --------------------------------------------------------
            # HISTORICAL STRUCTURE
            # --------------------------------------------------------

        price_history = get_price_history(
            strike=historical_strike,
            expiry=historical_expiry
        )

        oi_history = get_oi_history(
            strike=historical_strike,
            expiry=historical_expiry
        )

        structure = get_oi_buildup_analysis(
            strike=historical_strike,
            expiry=historical_expiry
        )

        # --------------------------------------------------------
        # PRICE + OI CARDS
        # --------------------------------------------------------

        if not price_history.empty and not oi_history.empty:

            latest_price = price_history.iloc[-1]
            latest_oi = oi_history.iloc[-1]

            option_ltp = latest_price[
                f"{prefix}_ltp"
            ]

            option_oi = latest_oi[
                f"{prefix}_oi"
            ]

            option_oi_delta = latest_oi[
                f"{prefix}_oi_delta"
            ]

            spot_price = latest_price[
                "spot_price"
            ]

            p1, p2, p3, p4, p5 = st.columns(5)

            with p1:

                st.metric(
                    "NIFTY",
                    f"{spot_price:,.2f}"
                )

            with p2:

                st.metric(
                    f"{option_type} LTP",
                    f"{option_ltp:,.2f}"
                )

            with p3:

                st.metric(
                    f"{option_type} OI",
                    format_number(option_oi)
                )

            with p4:

                st.metric(
                    "SNAPSHOT ΔOI",
                    format_number(option_oi_delta)
                )

            with p5:

                if not structure.empty:

                    latest_structure = structure[
                        f"{prefix}_structure"
                    ].iloc[-1]

                    st.metric(
                        "STRUCTURE",
                        latest_structure
                    )

                else:

                    st.metric(
                        "STRUCTURE",
                        "N/A"
                    )

            # ----------------------------------------------------
            # CHARTS
            # ----------------------------------------------------

            chart_left, chart_right = st.columns(2)

            with chart_left:

                st.markdown(
                    f"### {option_type} Price"
                )

                price_chart_df = price_history[
                    [
                        "fetch_time",
                        f"{prefix}_ltp"
                    ]
                ].copy()

                price_chart_df = price_chart_df.rename(
                    columns={
                        f"{prefix}_ltp": "LTP"
                    }
                )

                price_chart = (
                    alt.Chart(
                        price_chart_df
                    )
                    .mark_line()
                    .encode(
                        x=alt.X(
                            "fetch_time:T",
                            title="TIME"
                        ),
                        y=alt.Y(
                            "LTP:Q",
                            title="PRICE"
                        ),
                        tooltip=[
                            alt.Tooltip(
                                "fetch_time:T",
                                title="Time"
                            ),
                            alt.Tooltip(
                                "LTP:Q",
                                title="LTP",
                                format=".2f"
                            )
                        ]
                    )
                    .properties(
                        height=300
                    )
                )

                st.altair_chart(
                    price_chart,
                    width="stretch"
                )

            with chart_right:

                st.markdown(
                    f"### {option_type} OI"
                )

                oi_chart_df = oi_history[
                    [
                        "fetch_time",
                        f"{prefix}_oi"
                    ]
                ].copy()

                oi_chart_df = oi_chart_df.rename(
                    columns={
                        f"{prefix}_oi": "OI"
                    }
                )

                oi_chart_hist = (
                    alt.Chart(
                        oi_chart_df
                    )
                    .mark_line()
                    .encode(
                        x=alt.X(
                            "fetch_time:T",
                            title="TIME"
                        ),
                        y=alt.Y(
                            "OI:Q",
                            title="OPEN INTEREST"
                        ),
                        tooltip=[
                            alt.Tooltip(
                                "fetch_time:T",
                                title="Time"
                            ),
                            alt.Tooltip(
                                "OI:Q",
                                title="OI",
                                format=",.0f"
                            )
                        ]
                    )
                    .properties(
                        height=300
                    )
                )

                st.altair_chart(
                    oi_chart_hist,
                    width="stretch"
                )

            # ----------------------------------------------------
            # OI BUILDUP TABLE
            # ----------------------------------------------------

            if not structure.empty:

                st.markdown(
                    "### OI Buildup"
                )

                structure_display = structure[
                    [
                        "fetch_time",
                        "ce_ltp",
                        "ce_oi_change",
                        "ce_structure",
                        "pe_ltp",
                        "pe_oi_change",
                        "pe_structure"
                    ]
                ].tail(10).copy()

                structure_display.columns = [
                    "TIME",
                    "CE LTP",
                    "CE ΔOI",
                    "CE STRUCTURE",
                    "PE LTP",
                    "PE ΔOI",
                    "PE STRUCTURE"
                ]

                st.dataframe(
                    structure_display,
                    width="stretch",
                    height=260,
                    hide_index=True
                )

        else:

            st.warning(
                "Historical price/OI data is not available "
                "for this strike."
            )
        # ============================================================
# tab 11 NIFTY CHART
# ============================================================

with tabs[11]:

    st.markdown(
        '<div class="section-title">NIFTY PRICE CHART</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # CONTROLS
    # --------------------------------------------------------

    chart_c1, chart_c2 = st.columns(2)

    with chart_c1:

        chart_interval_label = st.selectbox(
            "TIMEFRAME",
            [
                "1 MINUTE",
                "5 MINUTE",
                "15 MINUTE",
                "30 MINUTE",
                "60 MINUTE"
            ],
            index=1,
            key="nifty_chart_interval"
        )

    with chart_c2:

        chart_days = st.selectbox(
            "HISTORY",
            [
                1,
                3,
                5,
                10
            ],
            index=2,
            key="nifty_chart_days"
        )

    interval_map = {
        "1 MINUTE": "1minute",
        "5 MINUTE": "5minute",
        "15 MINUTE": "15minute",
        "30 MINUTE": "30minute",
        "60 MINUTE": "60minute"
    }

    chart_interval = interval_map[
        chart_interval_label
    ]

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    try:

        chart_df = prepare_nifty_chart_data(
            interval=chart_interval,
            days=chart_days
        )

    except Exception as e:
        st.error(f"NIFTY chart data error: {e}")
        chart_df = pd.DataFrame()

    # --------------------------------------------------------
    # PHASE 1 PRICE ACTION ENGINE
    # --------------------------------------------------------

    try:
        price_action = run_price_action_engine(chart_df)
        chart_df = price_action["data"]

    except Exception as e:
        st.error(f"Price action engine error: {e}")

        price_action = {
            "trend": "UNKNOWN",
            "event": "NO DATA",
            "support": np.nan,
            "resistance": np.nan,
            "volume_signal": "NO DATA"
        }
    # --------------------------------------------------------
    # PHASE 2 CANDLESTICK PATTERN ENGINE
    # --------------------------------------------------------

    try:

        pattern_result = run_pattern_engine(
            chart_df
        )

        chart_df = pattern_result["data"]

    except Exception as e:

        st.error(
            f"Pattern engine error: {e}"
        )

        pattern_result = {
            "latest_pattern": "NO DATA",
            "pattern_bias": "NEUTRAL",
            "pattern_score": 0,
            "data": chart_df
        }
        # --------------------------------------------------------
    # STEP 8 — SAVE PRICE ACTION SNAPSHOT
    # --------------------------------------------------------

    try:

        if not chart_df.empty:

            latest_fusion_row = chart_df.iloc[-1]

            st.session_state[
                "price_action_snapshot"
            ] = {

                "trend": price_action.get(
                    "trend",
                    "UNKNOWN"
                ),

                "support": price_action.get(
                    "support",
                    np.nan
                ),

                "resistance": price_action.get(
                    "resistance",
                    np.nan
                ),

                "volume_signal": price_action.get(
                    "volume_signal",
                    "NO DATA"
                ),

                "pattern_bias": pattern_result.get(
                    "pattern_bias",
                    "NEUTRAL"
                ),

                "pattern_score": pattern_result.get(
                    "pattern_score",
                    0
                ),

                "latest_pattern": pattern_result.get(
                    "latest_pattern",
                    "NO DATA"
                ),

                "supertrend_signal": latest_fusion_row.get(
                    "supertrend_signal",
                    "NEUTRAL"
                ),

                "signal": latest_fusion_row.get(
                    "signal",
                    "NEUTRAL"
                ),

                "signal_score": latest_fusion_row.get(
                    "signal_score",
                    0
                ),

                "adx": latest_fusion_row.get(
                    "adx",
                    np.nan
                ),

                "adx_direction": latest_fusion_row.get(
                    "adx_direction",
                    "NEUTRAL"
                ),

                "adx_strength": latest_fusion_row.get(
                    "adx_strength",
                    "NO DATA"
                ),

                "timestamp": latest_fusion_row.get(
                    "timestamp",
                    pd.Timestamp.now()
                ),

                "timeframe": chart_interval_label,

                "updated": datetime.now().strftime(
                    "%H:%M:%S"
                )
            }

    except Exception as e:

        st.session_state[
            "price_action_snapshot"
        ] = {

            "trend": "UNKNOWN",
            "pattern_bias": "NEUTRAL",
            "pattern_score": 0,
            "supertrend_signal": "NEUTRAL",
            "signal": "NEUTRAL",
            "signal_score": 0,
            "latest_pattern": "NO DATA",
            "timeframe": chart_interval_label,
            "updated": datetime.now().strftime(
                "%H:%M:%S"
            )
        }
    # --------------------------------------------------------
    # CHART
    # --------------------------------------------------------

    if not chart_df.empty:

        latest = chart_df.iloc[-1]

        price = latest["close"]

        previous_close = (
            chart_df["close"].iloc[-2]
            if len(chart_df) > 1
            else price
        )

        change = price - previous_close

        change_pct = (
            (change / previous_close) * 100
            if previous_close != 0
            else 0
        )

        m1, m2, m3, m4 = st.columns(4)

        with m1:

            st.metric(
                "NIFTY",
                f"{price:,.2f}"
            )

        with m2:

            st.metric(
                "CHANGE",
                f"{change:+,.2f}"
            )

        with m3:

            st.metric(
                "CHANGE %",
                f"{change_pct:+.2f}%"
            )

        with m4:

            st.metric(
                "CANDLES",
                len(chart_df)
            )

        # ----------------------------------------------------
        # MARKET INTELLIGENCE
        # ----------------------------------------------------

        latest_row = chart_df.iloc[-1]

        trend_value = price_action.get(
            "trend",
            "UNKNOWN"
        )

        support = price_action.get(
            "support",
            np.nan
        )

        resistance = price_action.get(
            "resistance",
            np.nan
        )

        volume_value = price_action.get(
            "volume_signal",
            "NO DATA"
        )

        adx_value = latest_row.get(
            "adx",
            np.nan
        )

        plus_di_value = latest_row.get(
            "plus_di",
            np.nan
        )

        minus_di_value = latest_row.get(
            "minus_di",
            np.nan
        )

        adx_strength = latest_row.get(
            "adx_strength",
            "NO DATA"
        )

        adx_direction = latest_row.get(
            "adx_direction",
            "NEUTRAL"
        )

        supertrend_value = latest_row.get(
            "supertrend",
            np.nan
        )

        supertrend_signal = latest_row.get(
            "supertrend_signal",
            "NEUTRAL"
        )

        multi_factor_signal = latest_row.get(
            "signal",
            "NEUTRAL"
        )

        signal_score = latest_row.get(
            "signal_score",
            0
        )

        # ----------------------------------------------------
        # INTELLIGENCE ROW 1
        # ----------------------------------------------------

        pa1, pa2, pa3, pa4 = st.columns(4)

        with pa1:

            st.metric(
                "TREND",
                trend_value
            )

        with pa2:

            st.metric(
                "SUPPORT",
                "-"
                if pd.isna(support)
                else f"{support:,.2f}"
            )

        with pa3:

            st.metric(
                "RESISTANCE",
                "-"
                if pd.isna(resistance)
                else f"{resistance:,.2f}"
            )

        with pa4:

            st.metric(
                "VOLUME",
                volume_value
            )

        # ----------------------------------------------------
        # INTELLIGENCE ROW 2
        # ----------------------------------------------------

        ia1, ia2, ia3, ia4 = st.columns(4)

        with ia1:

            st.metric(
                "ADX",
                "-"
                if pd.isna(adx_value)
                else f"{adx_value:.2f}"
            )

        with ia2:

            st.metric(
                "DI DIRECTION",
                adx_direction
            )

        with ia3:

            st.metric(
                "ADX STRENGTH",
                adx_strength
            )

        with ia4:

            st.metric(
                "SUPERTREND",
                supertrend_signal
            )
        # ----------------------------------------------------
        # PRICE ACTION EVENT
        # ----------------------------------------------------

        pattern_name = pattern_result.get(
            "latest_pattern",
            "NO DATA"
        )

        pattern_bias = pattern_result.get(
            "pattern_bias",
            "NEUTRAL"
        )

        pattern_score = pattern_result.get(
            "pattern_score",
            0
        )

        pattern_color = {
            "BULLISH": "#00e59a",
            "BEARISH": "#ff5c67",
            "NEUTRAL": "#f1c75b"
        }.get(
            pattern_bias,
            "#f1c75b"
        )

        # ----------------------------------------------------
        # PATTERN SUMMARY
        # ----------------------------------------------------

        st.html(
            dedent(f"""
            <div style="background:#11151c; border:1px solid #292e38; border-radius:10px; padding:12px 16px; margin-top:8px; margin-bottom:12px;">
            <div style="color:#8f98a8; font-size:11px; font-weight:700; letter-spacing:0.7px;">CANDLESTICK PATTERN</div>
            <div style="color:{pattern_color}; font-size:20px; font-weight:800; margin-top:4px;">{pattern_name}</div>
            <div style="color:#8f98a8; font-size:12px; margin-top:5px;">Bias: <span style="color:{pattern_color}; font-weight:700;">{pattern_bias}</span> &nbsp;&nbsp; | &nbsp;&nbsp; Score: <span style="color:#f5f7fa; font-weight:700;">{pattern_score:+d}</span></div>
            </div>
            """),
        )

        # ----------------------------------------------------
        # CANDLESTICK + PATTERN MARKERS
        # ----------------------------------------------------

        candle = alt.Chart(
            chart_df
        ).encode(
            x=alt.X(
                "timestamp:T",
                title="TIME"
            )
        )

        # ----------------------------------------------------
        # CANDLE WICKS
        # ----------------------------------------------------

        wick = candle.mark_rule().encode(
            y=alt.Y(
                "low:Q",
                title="NIFTY"
            ),
            y2="high:Q"
        )

        # ----------------------------------------------------
        # CANDLE BODIES
        # ----------------------------------------------------

        body = candle.mark_bar().encode(
            y="open:Q",
            y2="close:Q"
        )

        # ----------------------------------------------------
        # EMA 9
        # ----------------------------------------------------

        ema9 = (
            alt.Chart(chart_df)
            .mark_line()
            .encode(
                x="timestamp:T",
                y="ema_9:Q"
            )
        )

        # ----------------------------------------------------
        # EMA 20
        # ----------------------------------------------------

        ema20 = (
            alt.Chart(chart_df)
            .mark_line()
            .encode(
                x="timestamp:T",
                y="ema_20:Q"
            )
        )

        # ----------------------------------------------------
        # EMA 50
        # ----------------------------------------------------

        ema50 = (
            alt.Chart(chart_df)
            .mark_line()
            .encode(
                x="timestamp:T",
                y="ema_50:Q"
            )
        )
        # ----------------------------------------------------
        # SUPERTREND
        # ----------------------------------------------------

        supertrend_chart = (
            alt.Chart(chart_df)
            .mark_line(
                strokeWidth=2
            )
            .encode(
                x=alt.X(
                    "timestamp:T",
                    title="TIME"
                ),
                y=alt.Y(
                    "supertrend:Q",
                    title="NIFTY"
                ),
                tooltip=[
                    alt.Tooltip(
                        "timestamp:T",
                        title="Time"
                    ),
                    alt.Tooltip(
                        "supertrend:Q",
                        title="Supertrend",
                        format=",.2f"
                    ),
                    alt.Tooltip(
                        "supertrend_signal:N",
                        title="Signal"
                    )
                ]
            )
        )

        # ====================================================
        # PATTERN MARKERS
        # ====================================================

        marker_columns = [
            "timestamp",
            "high",
            "low",
            "PRIMARY_PATTERN",
            "PATTERN_BIAS",
            "PATTERN_SCORE"
        ]

        available_marker_columns = [
            col
            for col in marker_columns
            if col in chart_df.columns
        ]

        pattern_markers = chart_df[
            available_marker_columns
        ].copy()

        # ----------------------------------------------------
        # Only show actual detected patterns
        # ----------------------------------------------------

        if "PRIMARY_PATTERN" in pattern_markers.columns:

            pattern_markers = pattern_markers[
                pattern_markers["PRIMARY_PATTERN"]
                .notna()
            ]

            pattern_markers = pattern_markers[
                pattern_markers["PRIMARY_PATTERN"]
                != "NONE"
            ]

        # ----------------------------------------------------
        # Keep chart visually clean
        # Show recent pattern signals only
        # ----------------------------------------------------

        pattern_markers = pattern_markers.tail(
            80
        ).copy()

        # ----------------------------------------------------
        # Marker position
        # ----------------------------------------------------

        if not pattern_markers.empty:

            if "atr" in chart_df.columns:

                atr_values = chart_df[
                    [
                        "timestamp",
                        "atr"
                    ]
                ].copy()

                pattern_markers = pattern_markers.merge(
                    atr_values,
                    on="timestamp",
                    how="left"
                )

                pattern_markers["atr"] = (
                    pd.to_numeric(
                        pattern_markers["atr"],
                        errors="coerce"
                    )
                    .fillna(10)
                )

            else:

                pattern_markers["atr"] = 10

            # ------------------------------------------------
            # Bullish markers
            # ------------------------------------------------

            bullish_marker_data = pattern_markers[
                pattern_markers["PATTERN_BIAS"]
                == "BULLISH"
            ].copy()

            bullish_marker_data["marker_price"] = (
                bullish_marker_data["low"]
                - bullish_marker_data["atr"] * 0.35
            )

            # ------------------------------------------------
            # Bearish markers
            # ------------------------------------------------

            bearish_marker_data = pattern_markers[
                pattern_markers["PATTERN_BIAS"]
                == "BEARISH"
            ].copy()

            bearish_marker_data["marker_price"] = (
                bearish_marker_data["high"]
                + bearish_marker_data["atr"] * 0.35
            )

            # ------------------------------------------------
            # Bullish chart marker
            # ------------------------------------------------

            bullish_markers = (
                alt.Chart(
                    bullish_marker_data
                )
                .mark_point(
                    shape="triangle-up",
                    size=110,
                    filled=True
                )
                .encode(
                    x="timestamp:T",
                    y=alt.Y(
                        "marker_price:Q"
                    ),
                    tooltip=[
                        alt.Tooltip(
                            "timestamp:T",
                            title="Time"
                        ),
                        alt.Tooltip(
                            "PRIMARY_PATTERN:N",
                            title="Pattern"
                        ),
                        alt.Tooltip(
                            "PATTERN_BIAS:N",
                            title="Bias"
                        ),
                        alt.Tooltip(
                            "PATTERN_SCORE:Q",
                            title="Score"
                        )
                    ]
                )
            )

            # ------------------------------------------------
            # Bearish chart marker
            # ------------------------------------------------

            bearish_markers = (
                alt.Chart(
                    bearish_marker_data
                )
                .mark_point(
                    shape="triangle-down",
                    size=110,
                    filled=True
                )
                .encode(
                    x="timestamp:T",
                    y=alt.Y(
                        "marker_price:Q"
                    ),
                    tooltip=[
                        alt.Tooltip(
                            "timestamp:T",
                            title="Time"
                        ),
                        alt.Tooltip(
                            "PRIMARY_PATTERN:N",
                            title="Pattern"
                        ),
                        alt.Tooltip(
                            "PATTERN_BIAS:N",
                            title="Bias"
                        ),
                        alt.Tooltip(
                            "PATTERN_SCORE:Q",
                            title="Score"
                        )
                    ]
                )
            )

        else:

            bullish_markers = alt.Chart(
                pd.DataFrame(
                    columns=[
                        "timestamp",
                        "marker_price"
                    ]
                )
            ).mark_point()

            bearish_markers = alt.Chart(
                pd.DataFrame(
                    columns=[
                        "timestamp",
                        "marker_price"
                    ]
                )
            ).mark_point()

        # ====================================================
        # FINAL CHART
        # ====================================================

        final_chart = (
            wick
            + body
            + ema9
            + ema20
            + ema50
            + bullish_markers
            + bearish_markers
            + supertrend_chart
        ).properties(
            height=500
        )

        st.altair_chart(
            final_chart,
            width="stretch"
        )
        
        # ----------------------------------------------------
        # INDICATOR CARDS
        # ----------------------------------------------------

        i1, i2, i3, i4 = st.columns(4)

        with i1:

            st.metric(
                "EMA 9",
                f"{latest['ema_9']:,.2f}"
            )

        with i2:

            st.metric(
                "EMA 20",
                f"{latest['ema_20']:,.2f}"
            )

        with i3:

            st.metric(
                "ATR",
                f"{latest['atr']:,.2f}"
            )

        with i4:

            st.metric(
                "RSI",
                f"{latest['rsi']:,.2f}"
            )

    else:

        st.warning(
            "No NIFTY historical data available."
        )
    # ============================================================
# STEP 8 — GAMMA + PRICE ACTION FUSION
# ============================================================

with tabs[12]:

    st.markdown(
        '<div class="section-title">Gamma + Price Action Fusion</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Institutional-style market regime engine combining "
        "Gamma pressure, OI/IV structure and NIFTY price action."
    )

    # --------------------------------------------------------
    # LOAD PRICE ACTION SNAPSHOT
    # --------------------------------------------------------

    price_snapshot = st.session_state.get(
        "price_action_snapshot",
        {}
    )

    # --------------------------------------------------------
    # GAMMA ENGINE
    # --------------------------------------------------------

    fusion_greek_metrics = greek_summary(
        df,
        atm,
        range_count=15
    )

    fusion_gamma_blast = calculate_gamma_blast(
        df,
        atm,
        range_count=15
    )

    fusion_gamma_structure = calculate_gamma_structure(
        fusion_gamma_blast,
        spot=spot,
        atm=atm
    )

    fusion_gamma_acceleration = (
        calculate_gamma_acceleration(
            fusion_gamma_blast,
            history_df=None,
            spot=spot,
            atm=atm
        )
    )

    fusion_gamma_score = (
        calculate_gamma_blast_score(
            gamma_blast=fusion_gamma_blast,
            gamma_structure=fusion_gamma_structure,
            gamma_acceleration=fusion_gamma_acceleration,
            greek_metrics=fusion_greek_metrics,
            spot=spot,
            atm=atm
        )
    )

    # --------------------------------------------------------
    # FUSION ENGINE
    # --------------------------------------------------------

    fusion_result = calculate_gamma_price_fusion(
        gamma_score=fusion_gamma_score,
        price_snapshot=price_snapshot,
        gamma_structure=fusion_gamma_structure
    )

    # --------------------------------------------------------
    # SAFE VALUES
    # --------------------------------------------------------

    fusion_score = float(
        fusion_result.get(
            "fusion_score",
            0
        )
    )

    gamma_score_value = float(
        fusion_result.get(
            "gamma_score",
            0
        )
    )

    price_score_value = float(
        fusion_result.get(
            "price_score",
            0
        )
    )

    direction = fusion_result.get(
        "direction",
        "NEUTRAL"
    )

    regime = fusion_result.get(
        "regime",
        "NO DATA"
    )

    confidence = float(
        fusion_result.get(
            "confidence",
            0
        )
    )

    alignment = fusion_result.get(
        "alignment",
        "NO DATA"
    )

    risk = fusion_result.get(
        "risk",
        "UNKNOWN"
    )

    trend = fusion_result.get(
        "trend",
        "UNKNOWN"
    )

    pattern = fusion_result.get(
        "pattern",
        "NEUTRAL"
    )

    supertrend = fusion_result.get(
        "supertrend",
        "NEUTRAL"
    )

    price_signal = fusion_result.get(
        "price_signal",
        "NEUTRAL"
    )

    # --------------------------------------------------------
    # COLOR SYSTEM
    # --------------------------------------------------------

    if fusion_score >= 60:

        fusion_color = "#00e59a"

    elif fusion_score >= 25:

        fusion_color = "#72d9a8"

    elif fusion_score <= -60:

        fusion_color = "#ff4654"

    elif fusion_score <= -25:

        fusion_color = "#ff7b84"

    else:

        fusion_color = "#f1c75b"

    if alignment == "ALIGNED":

        alignment_color = "#00e59a"

    elif alignment == "CONFLICT":

        alignment_color = "#ff4654"

    else:

        alignment_color = "#f1c75b"

    if risk == "CONTROLLED":

        risk_color = "#00e59a"

    elif risk == "HIGH":

        risk_color = "#ff4654"

    else:

        risk_color = "#f1c75b"

    # --------------------------------------------------------
    # COMMAND HEADER
    # --------------------------------------------------------

    st.html(
        dedent(
            f"""
            <div style="
                background:linear-gradient(
                    135deg,
                    #10151d 0%,
                    #0c1118 100%
                );
                border:1px solid #303642;
                border-radius:12px;
                padding:18px 20px;
                margin-top:8px;
                margin-bottom:12px;
            ">

                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    gap:20px;
                ">

                    <div>

                        <div style="
                            color:#737d8d;
                            font-size:10px;
                            font-weight:900;
                            letter-spacing:1.5px;
                        ">
                            MARKET REGIME ENGINE
                        </div>

                        <div style="
                            color:#f5f7fa;
                            font-size:23px;
                            font-weight:900;
                            margin-top:5px;
                        ">
                            GAMMA × PRICE ACTION
                        </div>

                        <div style="
                            color:#737d8d;
                            font-size:11px;
                            margin-top:5px;
                        ">
                            NIFTY {format_price(spot)}
                            &nbsp; • &nbsp;
                            ATM {format_integer(atm)}
                            &nbsp; • &nbsp;
                            EXPIRY {expiry}
                        </div>

                    </div>

                    <div style="
                        text-align:right;
                    ">

                        <div style="
                            color:#737d8d;
                            font-size:9px;
                            font-weight:800;
                            letter-spacing:1px;
                        ">
                            FUSION SCORE
                        </div>

                        <div style="
                            color:{fusion_color};
                            font-size:42px;
                            line-height:1;
                            font-weight:950;
                            margin-top:4px;
                        ">
                            {fusion_score:+.0f}
                        </div>

                        <div style="
                            color:{fusion_color};
                            font-size:11px;
                            font-weight:900;
                            margin-top:5px;
                        ">
                            {direction}
                        </div>

                    </div>

                </div>

                <div style="
                    height:7px;
                    background:#202631;
                    border-radius:8px;
                    overflow:hidden;
                    margin-top:16px;
                ">

                    <div style="
                        width:{min(100, abs(fusion_score)):.1f}%;
                        height:100%;
                        background:{fusion_color};
                        border-radius:8px;
                    "></div>

                </div>

            </div>
            """
        )
    )

    # --------------------------------------------------------
    # CORE REGIME CARDS
    # --------------------------------------------------------

    f1, f2, f3, f4, f5 = st.columns(5)

    with f1:

        st.html(
            dedent(
                f"""
                <div class="metric-card">
                    <div class="metric-label">
                        MARKET REGIME
                    </div>

                    <div style="
                        color:{fusion_color};
                        font-size:19px;
                        font-weight:900;
                        margin-top:8px;
                    ">
                        {regime}
                    </div>
                </div>
                """
            )
        )

    with f2:

        st.html(
            dedent(
                f"""
                <div class="metric-card">
                    <div class="metric-label">
                        CONFIDENCE
                    </div>

                    <div class="metric-value">
                        {confidence:.0f}%
                    </div>

                    <div class="metric-sub">
                        Composite confidence
                    </div>
                </div>
                """
            )
        )

    with f3:

        st.html(
            dedent(
                f"""
                <div class="metric-card">
                    <div class="metric-label">
                        ALIGNMENT
                    </div>

                    <div style="
                        color:{alignment_color};
                        font-size:17px;
                        font-weight:900;
                        margin-top:9px;
                    ">
                        {alignment}
                    </div>
                </div>
                """
            )
        )

    with f4:

        st.html(
            dedent(
                f"""
                <div class="metric-card">
                    <div class="metric-label">
                        RISK
                    </div>

                    <div style="
                        color:{risk_color};
                        font-size:17px;
                        font-weight:900;
                        margin-top:9px;
                    ">
                        {risk}
                    </div>
                </div>
                """
            )
        )

    with f5:

        st.html(
            dedent(
                f"""
                <div class="metric-card">
                    <div class="metric-label">
                        TIMEFRAME
                    </div>

                    <div class="metric-value" style="
                        font-size:17px;
                    ">
                        {price_snapshot.get(
                            "timeframe",
                            "NOT LOADED"
                        )}
                    </div>

                    <div class="metric-sub">
                        Price action source
                    </div>
                </div>
                """
            )
        )

    # --------------------------------------------------------
    # COMPONENT SCOREBOARD
    # --------------------------------------------------------

    st.markdown(
        "### Intelligence Scoreboard"
    )

    s1, s2, s3 = st.columns(3)

    with s1:

        st.html(
            dedent(
                f"""
                <div style="
                    background:#11151c;
                    border:1px solid #292e38;
                    border-radius:10px;
                    padding:15px;
                ">

                    <div style="
                        color:#737d8d;
                        font-size:10px;
                        font-weight:900;
                        letter-spacing:1px;
                    ">
                        GAMMA INTELLIGENCE
                    </div>

                    <div style="
                        color:{'#00e59a'
                        if gamma_score_value > 0
                        else '#ff4654'
                        if gamma_score_value < 0
                        else '#f1c75b'};
                        font-size:28px;
                        font-weight:950;
                        margin-top:6px;
                    ">
                        {gamma_score_value:+.0f}
                    </div>

                    <div style="
                        color:#8f98a8;
                        font-size:11px;
                        margin-top:4px;
                    ">
                        Gamma Blast + OI + IV
                    </div>

                </div>
                """
            )
        )

    with s2:

        st.html(
            dedent(
                f"""
                <div style="
                    background:#11151c;
                    border:1px solid #292e38;
                    border-radius:10px;
                    padding:15px;
                ">

                    <div style="
                        color:#737d8d;
                        font-size:10px;
                        font-weight:900;
                        letter-spacing:1px;
                    ">
                        PRICE ACTION
                    </div>

                    <div style="
                        color:{'#00e59a'
                        if price_score_value > 0
                        else '#ff4654'
                        if price_score_value < 0
                        else '#f1c75b'};
                        font-size:28px;
                        font-weight:950;
                        margin-top:6px;
                    ">
                        {price_score_value:+.0f}
                    </div>

                    <div style="
                        color:#8f98a8;
                        font-size:11px;
                        margin-top:4px;
                    ">
                        Trend + Pattern + Supertrend
                    </div>

                </div>
                """
            )
        )

    with s3:

        st.html(
            dedent(
                f"""
                <div style="
                    background:#11151c;
                    border:1px solid #292e38;
                    border-radius:10px;
                    padding:15px;
                ">

                    <div style="
                        color:#737d8d;
                        font-size:10px;
                        font-weight:900;
                        letter-spacing:1px;
                    ">
                        PRICE SIGNAL
                    </div>

                    <div style="
                        color:#f5f7fa;
                        font-size:18px;
                        font-weight:900;
                        margin-top:11px;
                    ">
                        {price_signal}
                    </div>

                    <div style="
                        color:#8f98a8;
                        font-size:11px;
                        margin-top:5px;
                    ">
                        Trend: {trend}
                    </div>

                </div>
                """
            )
        )

    # --------------------------------------------------------
    # GAMMA STRUCTURE + PRICE ACTION
    # --------------------------------------------------------

    st.markdown(
        "### Regime Structure"
    )

    r1, r2 = st.columns(2)

    with r1:

        gamma_wall_value = (
            fusion_gamma_structure.get(
                "gamma_wall",
                np.nan
            )
            if fusion_gamma_structure.get(
                "valid",
                False
            )
            else np.nan
        )

        gamma_flip_value = (
            fusion_gamma_structure.get(
                "gamma_flip",
                np.nan
            )
            if fusion_gamma_structure.get(
                "valid",
                False
            )
            else np.nan
        )

        wall_above_value = (
            fusion_gamma_structure.get(
                "wall_above",
                np.nan
            )
            if fusion_gamma_structure.get(
                "valid",
                False
            )
            else np.nan
        )

        wall_below_value = (
            fusion_gamma_structure.get(
                "wall_below",
                np.nan
            )
            if fusion_gamma_structure.get(
                "valid",
                False
            )
            else np.nan
        )

        st.html(
            dedent(
                f"""
                <div style="
                    background:#11151c;
                    border:1px solid #292e38;
                    border-radius:10px;
                    padding:15px;
                ">

                    <div style="
                        color:#8f98a8;
                        font-size:10px;
                        font-weight:900;
                        letter-spacing:1px;
                        margin-bottom:12px;
                    ">
                        GAMMA STRUCTURE
                    </div>

                    <div style="
                        display:grid;
                        grid-template-columns:1fr 1fr;
                        gap:10px;
                    ">

                        <div>
                            <div class="metric-label">
                                GAMMA WALL
                            </div>

                            <div class="metric-value"
                                 style="font-size:19px;">
                                {
                                    format_integer(
                                        gamma_wall_value
                                    )
                                }
                            </div>
                        </div>

                        <div>
                            <div class="metric-label">
                                GAMMA FLIP
                            </div>

                            <div class="metric-value"
                                 style="font-size:19px;">
                                {
                                    format_integer(
                                        gamma_flip_value
                                    )
                                }
                            </div>
                        </div>

                        <div>
                            <div class="metric-label">
                                WALL ABOVE
                            </div>

                            <div class="metric-value"
                                 style="font-size:19px;">
                                {
                                    format_integer(
                                        wall_above_value
                                    )
                                }
                            </div>
                        </div>

                        <div>
                            <div class="metric-label">
                                WALL BELOW
                            </div>

                            <div class="metric-value"
                                 style="font-size:19px;">
                                {
                                    format_integer(
                                        wall_below_value
                                    )
                                }
                            </div>
                        </div>

                    </div>

                </div>
                """
            )
        )

    with r2:

        st.html(
            dedent(
                f"""
                <div style="
                    background:#11151c;
                    border:1px solid #292e38;
                    border-radius:10px;
                    padding:15px;
                ">

                    <div style="
                        color:#8f98a8;
                        font-size:10px;
                        font-weight:900;
                        letter-spacing:1px;
                        margin-bottom:12px;
                    ">
                        PRICE ACTION STRUCTURE
                    </div>

                    <div style="
                        display:grid;
                        grid-template-columns:1fr 1fr;
                        gap:10px;
                    ">

                        <div>
                            <div class="metric-label">
                                TREND
                            </div>

                            <div style="
                                color:#f5f7fa;
                                font-size:16px;
                                font-weight:900;
                                margin-top:5px;
                            ">
                                {trend}
                            </div>
                        </div>

                        <div>
                            <div class="metric-label">
                                PATTERN
                            </div>

                            <div style="
                                color:#f5f7fa;
                                font-size:16px;
                                font-weight:900;
                                margin-top:5px;
                            ">
                                {pattern}
                            </div>
                        </div>

                        <div>
                            <div class="metric-label">
                                SUPERTREND
                            </div>

                            <div style="
                                color:#f5f7fa;
                                font-size:16px;
                                font-weight:900;
                                margin-top:5px;
                            ">
                                {supertrend}
                            </div>
                        </div>

                        <div>
                            <div class="metric-label">
                                PATTERN SCORE
                            </div>

                            <div style="
                                color:#f5f7fa;
                                font-size:16px;
                                font-weight:900;
                                margin-top:5px;
                            ">
                                {price_snapshot.get(
                                    "pattern_score",
                                    0
                                )}
                            </div>
                        </div>

                    </div>

                </div>
                """
            )
        )

    # --------------------------------------------------------
    # DECISION COMMAND PANEL
    # --------------------------------------------------------

    st.markdown(
        "### Command Panel"
    )

    if alignment == "ALIGNED":

        command_text = (
            "GAMMA AND PRICE ACTION ARE ALIGNED"
        )

        command_sub = (
            "Directional structure is reinforcing."
        )

    elif alignment == "CONFLICT":

        command_text = (
            "GAMMA / PRICE ACTION CONFLICT"
        )

        command_sub = (
            "Wait for confirmation before treating "
            "the move as a clean regime."
        )

    else:

        command_text = (
            "PARTIAL MARKET CONFIRMATION"
        )

        command_sub = (
            "One major component is not yet decisive."
        )

    st.html(
        dedent(
            f"""
            <div style="
                background:#0d1117;
                border:1px solid {alignment_color};
                border-radius:12px;
                padding:16px 18px;
                margin-top:5px;
            ">

                <div style="
                    color:{alignment_color};
                    font-size:12px;
                    font-weight:950;
                    letter-spacing:1px;
                ">
                    {command_text}
                </div>

                <div style="
                    color:#f5f7fa;
                    font-size:14px;
                    font-weight:700;
                    margin-top:7px;
                ">
                    {direction} • {regime}
                </div>

                <div style="
                    color:#737d8d;
                    font-size:11px;
                    margin-top:5px;
                ">
                    {command_sub}
                </div>

            </div>
            """
        )
    )

    st.caption(
        "Step 8 Fusion is an analytical market-regime layer. "
        "It does not place orders or guarantee directional outcomes."
    )
