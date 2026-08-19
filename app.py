import streamlit as st
import pandas as pd
import plotly.graph_objects as go


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NIFTY Option Chain Screener",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #0b0e13;
    color: #f5f5f5;
}

.block-container {
    padding-top: 1.2rem;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
    max-width: 100%;
}

.main-title {
    font-size: 32px;
    font-weight: 700;
}

.subtitle {
    color: #8d96a5;
    font-size: 14px;
    margin-bottom: 20px;
}

.metric-card {
    background-color: #12161d;
    border: 1px solid #252b35;
    border-radius: 8px;
    padding: 15px;
    min-height: 105px;
}

.metric-label {
    color: #8d96a5;
    font-size: 13px;
}

.metric-value {
    color: #f5f5f5;
    font-size: 24px;
    font-weight: 700;
    margin-top: 7px;
}

.analysis-card {
    background-color: #12161d;
    border: 1px solid #252b35;
    border-radius: 8px;
    padding: 18px;
    min-height: 115px;
}

.analysis-label {
    color: #8d96a5;
    font-size: 13px;
}

.analysis-value {
    font-size: 22px;
    font-weight: 700;
    margin-top: 8px;
}

.section-title {
    font-size: 22px;
    font-weight: 650;
    margin-top: 15px;
    margin-bottom: 10px;
}

.bullish {
    color: #00d084;
}

.bearish {
    color: #ff4d4d;
}

.neutral {
    color: #f5c451;
}

section[data-testid="stSidebar"] {
    background-color: #0f1319;
    border-right: 1px solid #252b35;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    df = pd.read_csv(
        "data/nifty_option_chain.csv"
    )

    return df


df = load_data()


# ============================================================
# CLEAN DATA
# ============================================================

numeric_columns = [
    "strike",
    "spot_price",

    "ce_ltp",
    "ce_close",
    "ce_volume",
    "ce_oi",
    "ce_oi_change",
    "ce_iv",

    "pe_ltp",
    "pe_close",
    "pe_volume",
    "pe_oi",
    "pe_oi_change",
    "pe_iv"
]

for col in numeric_columns:

    if col in df.columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )


df = (
    df
    .sort_values("strike")
    .reset_index(drop=True)
)


# ============================================================
# MARKET DATA
# ============================================================

spot = float(
    df["spot_price"].iloc[0]
)

expiry = str(
    df["expiry"].iloc[0]
)


# ============================================================
# ATM
# ============================================================

strikes = sorted(
    df["strike"].dropna().unique()
)

atm = min(
    strikes,
    key=lambda x: abs(x - spot)
)


# ============================================================
# PCR
# ============================================================

total_ce_oi = (
    df["ce_oi"]
    .fillna(0)
    .sum()
)

total_pe_oi = (
    df["pe_oi"]
    .fillna(0)
    .sum()
)

pcr = (
    total_pe_oi / total_ce_oi
    if total_ce_oi != 0
    else 0
)


# ============================================================
# STRIKE-WISE PCR
# ============================================================

df["strike_pcr"] = (
    df["pe_oi"].fillna(0)
    /
    df["ce_oi"].replace(0, pd.NA)
)

df["strike_pcr"] = (
    df["strike_pcr"]
    .fillna(0)
)


# ============================================================
# OPTION PRICE CHANGE
# ============================================================

df["ce_price_change"] = (
    df["ce_ltp"].fillna(0)
    -
    df["ce_close"].fillna(0)
)

df["pe_price_change"] = (
    df["pe_ltp"].fillna(0)
    -
    df["pe_close"].fillna(0)
)


# ============================================================
# BUILDUP CLASSIFICATION
# ============================================================

def buildup_signal(price_change, oi_change):

    if pd.isna(price_change) or pd.isna(oi_change):

        return "No Data"

    if price_change > 0 and oi_change > 0:

        return "Long Buildup"

    elif price_change < 0 and oi_change > 0:

        return "Short Buildup"

    elif price_change > 0 and oi_change < 0:

        return "Short Covering"

    elif price_change < 0 and oi_change < 0:

        return "Long Unwinding"

    return "Neutral"


df["ce_signal"] = df.apply(
    lambda row: buildup_signal(
        row["ce_price_change"],
        row["ce_oi_change"]
    ),
    axis=1
)

df["pe_signal"] = df.apply(
    lambda row: buildup_signal(
        row["pe_price_change"],
        row["pe_oi_change"]
    ),
    axis=1
)


# ============================================================
# VOLUME / OI
# ============================================================

df["ce_volume_oi"] = (
    df["ce_volume"].fillna(0)
    /
    df["ce_oi"].replace(0, pd.NA)
)

df["pe_volume_oi"] = (
    df["pe_volume"].fillna(0)
    /
    df["pe_oi"].replace(0, pd.NA)
)

df["ce_volume_oi"] = df["ce_volume_oi"].fillna(0)
df["pe_volume_oi"] = df["pe_volume_oi"].fillna(0)


# ============================================================
# SUPPORT / RESISTANCE
# ============================================================

max_ce_oi_row = df.loc[
    df["ce_oi"].idxmax()
]

max_pe_oi_row = df.loc[
    df["pe_oi"].idxmax()
]

resistance = max_ce_oi_row["strike"]
support = max_pe_oi_row["strike"]


max_ce_change_row = df.loc[
    df["ce_oi_change"].idxmax()
]

max_pe_change_row = df.loc[
    df["pe_oi_change"].idxmax()
]


# ============================================================
# MARKET BIAS
# ============================================================

if pcr >= 1.20:

    market_bias = "Bullish"
    bias_class = "bullish"

elif pcr <= 0.80:

    market_bias = "Bearish"
    bias_class = "bearish"

else:

    market_bias = "Neutral"
    bias_class = "neutral"


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    "## 📊 NIFTY SCREENER"
)

st.sidebar.markdown(
    "### Strike Range"
)

strike_range = st.sidebar.selectbox(
    "Display strikes",
    [
        "ATM ± 5",
        "ATM ± 10",
        "ATM ± 15",
        "ATM ± 20",
        "All Strikes"
    ],
    index=1
)


st.sidebar.markdown("---")

st.sidebar.markdown(
    "### Analysis"
)

analysis_mode = st.sidebar.selectbox(
    "Select analysis",
    [
        "Overview",
        "OI Analysis",
        "ΔOI Analysis",
        "Volume Analysis",
        "PCR Analysis"
    ]
)


st.sidebar.markdown("---")

if st.sidebar.button(
    "🔄 Refresh Data",
    width="stretch"
):

    st.cache_data.clear()

    st.rerun()


st.sidebar.markdown("---")

st.sidebar.markdown(
    "### Current Market"
)

st.sidebar.write(
    f"**Spot:** {spot:,.2f}"
)

st.sidebar.write(
    f"**ATM:** {atm:,.0f}"
)

st.sidebar.write(
    f"**Expiry:** {expiry}"
)

st.sidebar.write(
    f"**PCR:** {pcr:.3f}"
)

st.sidebar.write(
    f"**Bias:** {market_bias}"
)


# ============================================================
# FILTER STRIKES
# ============================================================

atm_index = min(
    range(len(strikes)),
    key=lambda i: abs(strikes[i] - atm)
)

range_map = {
    "ATM ± 5": 5,
    "ATM ± 10": 10,
    "ATM ± 15": 15,
    "ATM ± 20": 20
}

if strike_range == "All Strikes":

    selected_strikes = strikes

else:

    n = range_map[strike_range]

    lower = max(
        0,
        atm_index - n
    )

    upper = min(
        len(strikes),
        atm_index + n + 1
    )

    selected_strikes = strikes[
        lower:upper
    ]


display_df = df[
    df["strike"].isin(selected_strikes)
].copy()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">NIFTY Option Chain Screener</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Upstox Option Chain • Analysis Terminal</div>',
    unsafe_allow_html=True
)


# ============================================================
# TOP METRICS
# ============================================================

c1, c2, c3, c4, c5 = st.columns(5)


with c1:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">NIFTY SPOT</div>
            <div class="metric-value">
                {spot:,.2f}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with c2:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">ATM STRIKE</div>
            <div class="metric-value">
                {atm:,.0f}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with c3:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">EXPIRY</div>
            <div class="metric-value">
                {expiry}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with c4:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">PCR</div>
            <div class="metric-value">
                {pcr:.3f}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with c5:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">MARKET BIAS</div>
            <div class="metric-value {bias_class}">
                {market_bias}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.markdown("---")


# ============================================================
# SUPPORT / RESISTANCE
# ============================================================

st.markdown(
    '<div class="section-title">Market Structure</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "OI Support",
        f"{support:,.0f}",
        f"PE OI {max_pe_oi_row['pe_oi']:,.0f}"
    )


with c2:

    st.metric(
        "OI Resistance",
        f"{resistance:,.0f}",
        f"CE OI {max_ce_oi_row['ce_oi']:,.0f}"
    )


with c3:

    st.metric(
        "Max CE ΔOI",
        f"{max_ce_change_row['strike']:,.0f}",
        f"{max_ce_change_row['ce_oi_change']:,.0f}"
    )


with c4:

    st.metric(
        "Max PE ΔOI",
        f"{max_pe_change_row['strike']:,.0f}",
        f"{max_pe_change_row['pe_oi_change']:,.0f}"
    )


st.markdown("---")


# ============================================================
# OPTION CHAIN
# ============================================================

st.markdown(
    '<div class="section-title">Option Chain</div>',
    unsafe_allow_html=True
)


chain = display_df[
    [
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
].copy()


chain.columns = [
    "CE OI",
    "CE ΔOI",
    "CE Volume",
    "CE IV",
    "CE LTP",

    "STRIKE",

    "PE LTP",
    "PE IV",
    "PE Volume",
    "PE ΔOI",
    "PE OI"
]


format_dict = {

    "CE OI": "{:,.0f}",
    "CE ΔOI": "{:,.0f}",
    "CE Volume": "{:,.0f}",
    "CE IV": "{:.2f}",
    "CE LTP": "{:.2f}",

    "STRIKE": "{:,.0f}",

    "PE LTP": "{:.2f}",
    "PE IV": "{:.2f}",
    "PE Volume": "{:,.0f}",
    "PE ΔOI": "{:,.0f}",
    "PE OI": "{:,.0f}"
}


def color_delta(value):

    if pd.isna(value):

        return ""

    if value > 0:

        return (
            "color: #00d084;"
            "font-weight: 700;"
        )

    if value < 0:

        return (
            "color: #ff4d4d;"
            "font-weight: 700;"
        )

    return ""


def highlight_atm(row):

    if row["STRIKE"] == atm:

        return [
            "background-color: #263238;"
            "font-weight: 700;"
        ] * len(row)

    return [""] * len(row)


styled = (
    chain
    .style
    .format(format_dict)
    .map(
        color_delta,
        subset=[
            "CE ΔOI",
            "PE ΔOI"
        ]
    )
    .apply(
        highlight_atm,
        axis=1
    )
)


st.dataframe(
    styled,
    width="stretch",
    height=580,
    hide_index=True
)


st.markdown("---")


# ============================================================
# ANALYSIS SECTION
# ============================================================

if analysis_mode == "Overview":

    st.markdown(
        '<div class="section-title">Analysis Overview</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Total CE OI",
            f"{total_ce_oi:,.0f}"
        )

    with c2:

        st.metric(
            "Total PE OI",
            f"{total_pe_oi:,.0f}"
        )

    with c3:

        st.metric(
            "Strike PCR",
            f"{display_df['strike_pcr'].mean():.3f}"
        )


# ============================================================
# OI ANALYSIS
# ============================================================

elif analysis_mode == "OI Analysis":

    st.markdown(
        '<div class="section-title">OI Analysis</div>',
        unsafe_allow_html=True
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=display_df["strike"],
            y=display_df["ce_oi"],
            name="CE OI"
        )
    )

    fig.add_trace(
        go.Bar(
            x=display_df["strike"],
            y=display_df["pe_oi"],
            name="PE OI"
        )
    )

    fig.add_vline(
        x=atm,
        line_dash="dash",
        annotation_text="ATM"
    )

    fig.update_layout(
        template="plotly_dark",
        title="Call OI vs Put OI",
        xaxis_title="Strike",
        yaxis_title="Open Interest",
        barmode="group",
        height=500
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )


# ============================================================
# ΔOI ANALYSIS
# ============================================================

elif analysis_mode == "ΔOI Analysis":

    st.markdown(
        '<div class="section-title">ΔOI Analysis</div>',
        unsafe_allow_html=True
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=display_df["strike"],
            y=display_df["ce_oi_change"],
            name="CE ΔOI"
        )
    )

    fig.add_trace(
        go.Bar(
            x=display_df["strike"],
            y=display_df["pe_oi_change"],
            name="PE ΔOI"
        )
    )

    fig.add_hline(y=0)

    fig.add_vline(
        x=atm,
        line_dash="dash",
        annotation_text="ATM"
    )

    fig.update_layout(
        template="plotly_dark",
        title="Call ΔOI vs Put ΔOI",
        xaxis_title="Strike",
        yaxis_title="Change in OI",
        barmode="group",
        height=500
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

    # ----------------------------------------
    # SIGNAL TABLE
    # ----------------------------------------

    signal_df = display_df[
        [
            "strike",
            "ce_ltp",
            "ce_price_change",
            "ce_oi_change",
            "ce_signal",
            "pe_ltp",
            "pe_price_change",
            "pe_oi_change",
            "pe_signal"
        ]
    ].copy()

    signal_df.columns = [
        "Strike",
        "CE LTP",
        "CE Price Chg",
        "CE ΔOI",
        "CE Signal",
        "PE LTP",
        "PE Price Chg",
        "PE ΔOI",
        "PE Signal"
    ]

    st.dataframe(
        signal_df,
        width="stretch",
        hide_index=True
    )


# ============================================================
# VOLUME ANALYSIS
# ============================================================

elif analysis_mode == "Volume Analysis":

    st.markdown(
        '<div class="section-title">Volume Analysis</div>',
        unsafe_allow_html=True
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=display_df["strike"],
            y=display_df["ce_volume"],
            name="CE Volume"
        )
    )

    fig.add_trace(
        go.Bar(
            x=display_df["strike"],
            y=display_df["pe_volume"],
            name="PE Volume"
        )
    )

    fig.add_vline(
        x=atm,
        line_dash="dash",
        annotation_text="ATM"
    )

    fig.update_layout(
        template="plotly_dark",
        title="Call Volume vs Put Volume",
        xaxis_title="Strike",
        yaxis_title="Volume",
        barmode="group",
        height=500
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

    # ----------------------------------------
    # TOP VOLUME
    # ----------------------------------------

    max_ce_volume = display_df.loc[
        display_df["ce_volume"].idxmax()
    ]

    max_pe_volume = display_df.loc[
        display_df["pe_volume"].idxmax()
    ]

    c1, c2 = st.columns(2)

    with c1:

        st.metric(
            "Highest CE Volume",
            f"{max_ce_volume['strike']:,.0f}",
            f"{max_ce_volume['ce_volume']:,.0f}"
        )

    with c2:

        st.metric(
            "Highest PE Volume",
            f"{max_pe_volume['strike']:,.0f}",
            f"{max_pe_volume['pe_volume']:,.0f}"
        )


# ============================================================
# PCR ANALYSIS
# ============================================================

elif analysis_mode == "PCR Analysis":

    st.markdown(
        '<div class="section-title">PCR Analysis</div>',
        unsafe_allow_html=True
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=display_df["strike"],
            y=display_df["strike_pcr"],
            mode="lines+markers",
            name="Strike PCR"
        )
    )

    fig.add_hline(
        y=1,
        line_dash="dash",
        annotation_text="PCR 1.0"
    )

    fig.add_vline(
        x=atm,
        line_dash="dash",
        annotation_text="ATM"
    )

    fig.update_layout(
        template="plotly_dark",
        title="Strike-wise Put/Call OI Ratio",
        xaxis_title="Strike",
        yaxis_title="PE OI / CE OI",
        height=500
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

    pcr_table = display_df[
        [
            "strike",
            "ce_oi",
            "pe_oi",
            "strike_pcr"
        ]
    ].copy()

    pcr_table.columns = [
        "Strike",
        "CE OI",
        "PE OI",
        "PCR"
    ]

    st.dataframe(
        pcr_table,
        width="stretch",
        hide_index=True
    )


# ============================================================
# SIGNAL SUMMARY
# ============================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">Quick Market Summary</div>',
    unsafe_allow_html=True
)

summary_col1, summary_col2, summary_col3 = st.columns(3)


with summary_col1:

    st.markdown(
        f"""
        <div class="analysis-card">
            <div class="analysis-label">
                OI SUPPORT
            </div>
            <div class="analysis-value bullish">
                {support:,.0f}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with summary_col2:

    st.markdown(
        f"""
        <div class="analysis-card">
            <div class="analysis-label">
                OI RESISTANCE
            </div>
            <div class="analysis-value bearish">
                {resistance:,.0f}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with summary_col3:

    st.markdown(
        f"""
        <div class="analysis-card">
            <div class="analysis-label">
                PCR BIAS
            </div>
            <div class="analysis-value {bias_class}">
                {market_bias}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    