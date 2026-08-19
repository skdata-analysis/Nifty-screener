import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================
# NIFTY MASTER SCREENER - V4
# One-screen trading dashboard + top navigation
# ============================================================

st.set_page_config(
    page_title="NIFTY Master Screener",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# GLOBAL CSS
# -----------------------------
st.markdown(
    """
    <style>
        /* Main application */
        .stApp {
            background: #0b0e13;
        }

        .block-container {
            padding-top: 0.65rem;
            padding-left: 1.25rem;
            padding-right: 1.25rem;
            padding-bottom: 0.6rem;
            max-width: 100%;
        }

        /* Hide Streamlit chrome that is not useful for terminal UI */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Compact headings */
        h1, h2, h3 {
            margin-top: 0 !important;
        }

        /* Metric cards */
        div[data-testid="stMetric"] {
            background: #11151c;
            border: 1px solid #252b35;
            border-radius: 10px;
            padding: 10px 12px;
        }

        div[data-testid="stMetricLabel"] {
            color: #8f98a8;
            font-size: 0.78rem;
        }

        div[data-testid="stMetricValue"] {
            color: #f3f5f7;
            font-size: 1.55rem;
        }

        /* Tables */
        div[data-testid="stDataFrame"] {
            border: 1px solid #252b35;
            border-radius: 8px;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 8px;
            border: 1px solid #3a414d;
            background: #171b23;
            color: #f2f4f7;
            font-weight: 600;
        }

        .stButton > button:hover {
            border-color: #7f8ea3;
            color: white;
        }

        /* Select boxes */
        div[data-baseweb="select"] > div {
            background: #11151c;
            border-color: #2c333e;
        }

        /* Section labels */
        .section-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #e9edf2;
            margin: 0.25rem 0 0.45rem 0;
        }

        .subtle {
            color: #7f8998;
            font-size: 0.75rem;
        }

        .positive {
            color: #00d084;
            font-weight: 700;
        }

        .negative {
            color: #ff4d5f;
            font-weight: 700;
        }

        .neutral {
            color: #f0b90b;
            font-weight: 700;
        }

        .terminal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.15rem 0 0.5rem 0;
        }

        .brand {
            font-size: 1.25rem;
            font-weight: 800;
            color: #f5f7fa;
        }

        .live-dot {
            color: #00d084;
            font-weight: 700;
        }

        /* Reduce chart padding */
        div[data-testid="stVegaLiteChart"] {
            background: #0f1319;
            border: 1px solid #252b35;
            border-radius: 8px;
            padding: 3px;
        }

        /* Mobile */
        @media (max-width: 900px) {
            .block-container {
                padding-left: 0.55rem;
                padding-right: 0.55rem;
            }

            .brand {
                font-size: 1rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# DATA
# ============================================================

DATA_PATH = Path("data/nifty_option_chain.csv")


@st.cache_data(ttl=10)
def load_data():
    if not DATA_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(DATA_PATH)

    # Numeric columns
    numeric_cols = [
        "strike", "spot_price", "pcr",
        "ce_ltp", "ce_volume", "ce_oi", "ce_prev_oi", "ce_oi_change",
        "ce_iv", "ce_delta", "ce_gamma", "ce_theta", "ce_vega", "ce_pop",
        "ce_bid", "ce_bid_qty", "ce_ask", "ce_ask_qty",
        "pe_ltp", "pe_volume", "pe_oi", "pe_prev_oi", "pe_oi_change",
        "pe_iv", "pe_delta", "pe_gamma", "pe_theta", "pe_vega", "pe_pop",
        "pe_bid", "pe_bid_qty", "pe_ask", "pe_ask_qty",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "strike" in df.columns:
        df = df.sort_values("strike").reset_index(drop=True)

    return df


df = load_data()

if df.empty:
    st.error(
        "Option-chain CSV not found. Run `python optionchain_datafram.py` first."
    )
    st.stop()

# ============================================================
# HELPERS
# ============================================================

def fmt_num(value, decimals=0):
    if pd.isna(value):
        return "—"
    if decimals == 0:
        return f"{value:,.0f}"
    return f"{value:,.{decimals}f}"

def safe_sum(series):
    if series is None:
        return 0

    return pd.to_numeric(series, errors="coerce").fillna(0).sum()



def get_bias(pcr):
    if pd.isna(pcr):
        return "N/A"
    if pcr >= 1.20:
        return "BULLISH"
    if pcr <= 0.80:
        return "BEARISH"
    return "NEUTRAL"


def get_buildup(price_change, oi_change):
    if pd.isna(price_change) or pd.isna(oi_change):
        return "N/A"

    if price_change > 0 and oi_change > 0:
        return "LONG BUILDUP"
    if price_change < 0 and oi_change > 0:
        return "SHORT BUILDUP"
    if price_change > 0 and oi_change < 0:
        return "SHORT COVERING"
    if price_change < 0 and oi_change < 0:
        return "LONG UNWINDING"
    return "NEUTRAL"


# ============================================================
# CORE VALUES
# ============================================================

spot = df["spot_price"].dropna().iloc[0] if "spot_price" in df.columns and df["spot_price"].notna().any() else np.nan
strikes = sorted(df["strike"].dropna().unique())

if not strikes:
    st.error("No strike data found in CSV.")
    st.stop()

atm = min(strikes, key=lambda x: abs(x - spot)) if not pd.isna(spot) else strikes[len(strikes) // 2]

expiry = (
    str(df["expiry"].dropna().iloc[0])
    if "expiry" in df.columns and df["expiry"].notna().any()
    else "—"
)

total_ce_oi = safe_sum(df["ce_oi"])
total_pe_oi = safe_sum(df["pe_oi"])
overall_pcr = total_pe_oi / total_ce_oi if total_ce_oi else np.nan

# Max OI
max_ce_row = df.loc[df["ce_oi"].idxmax()] if "ce_oi" in df.columns and df["ce_oi"].notna().any() else None
max_pe_row = df.loc[df["pe_oi"].idxmax()] if "pe_oi" in df.columns and df["pe_oi"].notna().any() else None

# Max absolute positive OI change
max_ce_change_row = (
    df.loc[df["ce_oi_change"].idxmax()]
    if "ce_oi_change" in df.columns and df["ce_oi_change"].notna().any()
    else None
)
max_pe_change_row = (
    df.loc[df["pe_oi_change"].idxmax()]
    if "pe_oi_change" in df.columns and df["pe_oi_change"].notna().any()
    else None
)

bias = get_bias(overall_pcr)

# ============================================================
# HEADER
# ============================================================

st.markdown(
    f"""
    <div class="terminal-header">
        <div class="brand">📊 NIFTY MASTER SCREENER</div>
        <div>
            <span class="live-dot">● DATA READY</span>
            &nbsp;&nbsp;
            <span class="subtle">Upstox • {len(df)} strikes</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# TOP NAVIGATION
# ============================================================

tab_dashboard, tab_chain, tab_oi, tab_volume, tab_iv, tab_pcr, tab_signals = st.tabs(
    ["DASHBOARD", "OPTION CHAIN", "OI", "VOLUME", "IV", "PCR", "SIGNALS"]
)

# ============================================================
# DASHBOARD
# ============================================================

with tab_dashboard:

    # Controls row
    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 1.0])

    with c1:
        strike_range = st.selectbox(
            "STRIKE RANGE",
            ["ATM ± 5", "ATM ± 10", "ATM ± 15", "ATM ± 20", "ALL"],
            index=0,
            key="dashboard_range",
        )

    with c2:
        st.metric("NIFTY SPOT", fmt_num(spot, 2))

    with c3:
        st.metric("ATM STRIKE", fmt_num(atm))

    with c4:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Market summary
    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        st.metric("EXPIRY", expiry)

    with m2:
        st.metric("PCR", fmt_num(overall_pcr, 3))

    with m3:
        st.metric(
            "MAX CE OI",
            fmt_num(max_ce_row["ce_oi"]) if max_ce_row is not None else "—",
            f"Strike {fmt_num(max_ce_row['strike'])}" if max_ce_row is not None else None,
        )

    with m4:
        st.metric(
            "MAX PE OI",
            fmt_num(max_pe_row["pe_oi"]) if max_pe_row is not None else "—",
            f"Strike {fmt_num(max_pe_row['strike'])}" if max_pe_row is not None else None,
        )

    with m5:
        st.metric("MARKET BIAS", bias)

    # Determine selected strikes
    if strike_range == "ALL":
        selected_strikes = strikes
    else:
        n = int(strike_range.split("±")[1].strip())
        atm_index = strikes.index(atm)
        selected_strikes = strikes[
            max(0, atm_index - n): min(len(strikes), atm_index + n + 1)
        ]

    view = df[df["strike"].isin(selected_strikes)].copy()

    # Option chain
    st.markdown('<div class="section-title">OPTION CHAIN</div>', unsafe_allow_html=True)

    display_cols = [
        "ce_oi", "ce_oi_change", "ce_volume", "ce_iv", "ce_ltp",
        "strike",
        "pe_ltp", "pe_iv", "pe_volume", "pe_oi_change", "pe_oi"
    ]

    display_cols = [c for c in display_cols if c in view.columns]
    chain = view[display_cols].copy()

    rename_map = {
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
        "pe_oi": "PE OI",
    }

    chain = chain.rename(columns=rename_map)

    # Formatting
    format_dict = {}
    for col in chain.columns:
        if col in ["CE OI", "CE ΔOI", "CE Volume", "PE Volume", "PE ΔOI", "PE OI"]:
            format_dict[col] = "{:,.0f}"
        elif col in ["CE IV", "PE IV"]:
            format_dict[col] = "{:.2f}"
        elif col in ["CE LTP", "PE LTP"]:
            format_dict[col] = "{:.2f}"
        elif col == "STRIKE":
            format_dict[col] = "{:,.0f}"

    st.dataframe(
        chain.style.format(format_dict),
        use_container_width=True,
        height=330,
    )

    # Mini analytics
    a1, a2 = st.columns(2)

    with a1:
        st.markdown('<div class="section-title">OI DISTRIBUTION</div>', unsafe_allow_html=True)
        oi_chart = view[["strike", "ce_oi", "pe_oi"]].copy()
        oi_chart = oi_chart.set_index("strike")
        oi_chart.columns = ["CE OI", "PE OI"]
        st.bar_chart(oi_chart, height=190)

    with a2:
        st.markdown('<div class="section-title">ΔOI DISTRIBUTION</div>', unsafe_allow_html=True)
        doi_chart = view[["strike", "ce_oi_change", "pe_oi_change"]].copy()
        doi_chart = doi_chart.set_index("strike")
        doi_chart.columns = ["CE ΔOI", "PE ΔOI"]
        st.bar_chart(doi_chart, height=190)

    # Bottom key levels
    b1, b2, b3, b4 = st.columns(4)

    with b1:
        st.metric(
            "MAX CE ΔOI",
            fmt_num(max_ce_change_row["ce_oi_change"]) if max_ce_change_row is not None else "—",
            f"Strike {fmt_num(max_ce_change_row['strike'])}" if max_ce_change_row is not None else None,
        )

    with b2:
        st.metric(
            "MAX PE ΔOI",
            fmt_num(max_pe_change_row["pe_oi_change"]) if max_pe_change_row is not None else "—",
            f"Strike {fmt_num(max_pe_change_row['strike'])}" if max_pe_change_row is not None else None,
        )

    with b3:
        st.metric(
            "SUPPORT",
            fmt_num(max_pe_row["strike"]) if max_pe_row is not None else "—",
        )

    with b4:
        st.metric(
            "RESISTANCE",
            fmt_num(max_ce_row["strike"]) if max_ce_row is not None else "—",
        )

    st.caption(
        f"● Data source: Upstox CSV  •  Rows: {len(df)}  •  "
        f"ATM: {fmt_num(atm)}  •  Dashboard range: {strike_range}"
    )


# ============================================================
# OPTION CHAIN TAB
# ============================================================

with tab_chain:
    st.subheader("Full Option Chain")

    n_chain = st.selectbox(
        "Display",
        ["ATM ± 10", "ATM ± 20", "ALL"],
        key="chain_range",
    )

    if n_chain == "ALL":
        chain_df = df.copy()
    else:
        n = int(n_chain.split("±")[1].strip())
        atm_index = strikes.index(atm)
        selected = strikes[
            max(0, atm_index - n): min(len(strikes), atm_index + n + 1)
        ]
        chain_df = df[df["strike"].isin(selected)].copy()

    cols = [
        "ce_oi", "ce_oi_change", "ce_volume", "ce_iv", "ce_ltp",
        "strike",
        "pe_ltp", "pe_iv", "pe_volume", "pe_oi_change", "pe_oi"
    ]
    cols = [c for c in cols if c in chain_df.columns]

    full_chain = chain_df[cols].rename(columns=rename_map)

    fmt = {}
    for col in full_chain.columns:
        if col in ["CE OI", "CE ΔOI", "CE Volume", "PE Volume", "PE ΔOI", "PE OI"]:
            fmt[col] = "{:,.0f}"
        elif col in ["CE IV", "PE IV", "CE LTP", "PE LTP"]:
            fmt[col] = "{:.2f}"
        elif col == "STRIKE":
            fmt[col] = "{:,.0f}"

    st.dataframe(full_chain.style.format(fmt), use_container_width=True, height=620)


# ============================================================
# OI TAB
# ============================================================

with tab_oi:
    st.subheader("Open Interest Analysis")

    c1, c2 = st.columns(2)

    with c1:
        oi = df[["strike", "ce_oi", "pe_oi"]].copy().set_index("strike")
        oi.columns = ["CE OI", "PE OI"]
        st.bar_chart(oi, height=400)

    with c2:
        doi = df[["strike", "ce_oi_change", "pe_oi_change"]].copy().set_index("strike")
        doi.columns = ["CE ΔOI", "PE ΔOI"]
        st.bar_chart(doi, height=400)

    o1, o2, o3, o4 = st.columns(4)
    with o1:
        st.metric("TOTAL CE OI", fmt_num(total_ce_oi))
    with o2:
        st.metric("TOTAL PE OI", fmt_num(total_pe_oi))
    with o3:
        st.metric("MAX CE OI STRIKE", fmt_num(max_ce_row["strike"]) if max_ce_row is not None else "—")
    with o4:
        st.metric("MAX PE OI STRIKE", fmt_num(max_pe_row["strike"]) if max_pe_row is not None else "—")


# ============================================================
# VOLUME TAB
# ============================================================

with tab_volume:
    st.subheader("Volume Analysis")

    volume = df[["strike", "ce_volume", "pe_volume"]].copy().set_index("strike")
    volume.columns = ["CE Volume", "PE Volume"]

    st.bar_chart(volume, height=450)

    v1, v2 = st.columns(2)
    with v1:
        st.metric("TOTAL CE VOLUME", fmt_num(safe_sum(df["ce_volume"])))
    with v2:
        st.metric("TOTAL PE VOLUME", fmt_num(safe_sum(df["pe_volume"])))


# ============================================================
# IV TAB
# ============================================================

with tab_iv:
    st.subheader("Implied Volatility")

    iv = df[["strike", "ce_iv", "pe_iv"]].copy().set_index("strike")
    iv.columns = ["CE IV", "PE IV"]

    st.line_chart(iv, height=450)

    i1, i2 = st.columns(2)
    with i1:
        st.metric(
            "ATM CE IV",
            fmt_num(
                df.loc[df["strike"] == atm, "ce_iv"].iloc[0], 2
            ) if not df.loc[df["strike"] == atm, "ce_iv"].empty else "—",
        )
    with i2:
        st.metric(
            "ATM PE IV",
            fmt_num(
                df.loc[df["strike"] == atm, "pe_iv"].iloc[0], 2
            ) if not df.loc[df["strike"] == atm, "pe_iv"].empty else "—",
        )


# ============================================================
# PCR TAB
# ============================================================

with tab_pcr:
    st.subheader("PCR Analysis")

    pcr_df = df[["strike", "ce_oi", "pe_oi"]].copy()
    pcr_df["PCR"] = np.where(
        pcr_df["ce_oi"] != 0,
        pcr_df["pe_oi"] / pcr_df["ce_oi"],
        np.nan,
    )
    pcr_df = pcr_df.set_index("strike")

    st.line_chart(pcr_df[["PCR"]], height=450)

    p1, p2, p3 = st.columns(3)
    with p1:
        st.metric("OVERALL PCR", fmt_num(overall_pcr, 3))
    with p2:
        atm_row = df[df["strike"].isin(
            strikes[max(0, strikes.index(atm)-5): min(len(strikes), strikes.index(atm)+6)]
        )]
        atm_ce = safe_sum(atm_row["ce_oi"])
        atm_pe = safe_sum(atm_row["pe_oi"])
        atm_pcr = atm_pe / atm_ce if atm_ce else np.nan
        st.metric("ATM ± 5 PCR", fmt_num(atm_pcr, 3))
    with p3:
        st.metric("BIAS", bias)


# ============================================================
# SIGNALS TAB
# ============================================================

with tab_signals:
    st.subheader("Strike-Level Signal Scanner")

    signal_df = df[["strike", "ce_ltp", "ce_oi_change", "pe_ltp", "pe_oi_change"]].copy()

    # Current implementation uses ΔOI + LTP direction relative to previous close.
    # This is deliberately kept simple until historical snapshots are stored.
    signal_df["CE OI Change"] = signal_df["ce_oi_change"]
    signal_df["PE OI Change"] = signal_df["pe_oi_change"]

    def oi_signal(ce_change, pe_change):
        if pd.isna(ce_change) and pd.isna(pe_change):
            return "N/A"
        if ce_change > 0 and pe_change > 0:
            return "BOTH OI BUILDUP"
        if ce_change > 0 and pe_change < 0:
            return "CE OI BUILDUP"
        if ce_change < 0 and pe_change > 0:
            return "PE OI BUILDUP"
        if ce_change < 0 and pe_change < 0:
            return "OI UNWINDING"
        return "NEUTRAL"

    signal_df["SIGNAL"] = signal_df.apply(
        lambda r: oi_signal(r["ce_oi_change"], r["pe_oi_change"]),
        axis=1,
    )

    signal_view = signal_df[
        ["strike", "CE OI Change", "PE OI Change", "SIGNAL"]
    ].rename(columns={"strike": "STRIKE"})

    st.dataframe(
        signal_view.style.format({
            "CE OI Change": "{:,.0f}",
            "PE OI Change": "{:,.0f}",
            "STRIKE": "{:,.0f}",
        }),
        use_container_width=True,
        height=600,
    )

    st.info(
        "Signal engine V4 is intentionally based on OI structure only. "
        "Do not treat it as a buy/sell recommendation yet. "
        "Historical price snapshots will be added before full buildup classification."
    )
