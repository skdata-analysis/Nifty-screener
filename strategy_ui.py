import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

from strategy_engine import (
    calculate_strategy_payoff,
    long_straddle,
    short_straddle,
    long_strangle,
    short_strangle,
    bull_call_spread,
    bear_put_spread,
    iron_condor,
)


# ============================================================
# HELPERS
# ============================================================

def _safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _get_premium(df, strike, option_type):
    """
    Get current option premium from option-chain dataframe.
    """

    column = "ce_ltp" if option_type == "CE" else "pe_ltp"

    if column not in df.columns:
        return 0.0

    rows = df[df["strike"] == strike]

    if rows.empty:
        return 0.0

    return _safe_float(rows[column].iloc[0])
def _validate_strategy(strategy, selections):
    """
    Validate strike relationships for option strategies.
    """

    if strategy in [
        "LONG STRADDLE",
        "SHORT STRADDLE"
    ]:
        return True, ""

    if strategy in [
        "LONG STRANGLE",
        "SHORT STRANGLE"
    ]:

        ce_strike = selections["ce_strike"]
        pe_strike = selections["pe_strike"]

        if pe_strike >= ce_strike:
            return (
                False,
                "For a strangle, PUT strike must be below CALL strike."
            )

        return True, ""

    if strategy == "BULL CALL SPREAD":

        buy_strike = selections["buy_strike"]
        sell_strike = selections["sell_strike"]

        if buy_strike >= sell_strike:
            return (
                False,
                "Bull Call Spread requires BUY CE strike < SELL CE strike."
            )

        return True, ""

    if strategy == "BEAR PUT SPREAD":

        buy_strike = selections["buy_strike"]
        sell_strike = selections["sell_strike"]

        if buy_strike <= sell_strike:
            return (
                False,
                "Bear Put Spread requires BUY PE strike > SELL PE strike."
            )

        return True, ""

    if strategy == "IRON CONDOR":

        put_buy = selections["put_buy_strike"]
        put_sell = selections["put_sell_strike"]
        call_sell = selections["call_sell_strike"]
        call_buy = selections["call_buy_strike"]

        if not (
            put_buy
            < put_sell
            < call_sell
            < call_buy
        ):
            return (
                False,
                "Iron Condor requires PUT BUY < PUT SELL < CALL SELL < CALL BUY."
            )

        return True, ""

    return True, ""



def _calculate_breakevens(payoff_df):
    """
    Detect approximate breakeven points where strategy
    P&L crosses zero.
    """

    if payoff_df.empty:
        return []

    prices = payoff_df["underlying_price"].values
    pnl = payoff_df["strategy_pnl"].values

    breakevens = []

    for i in range(len(pnl) - 1):

        p1 = pnl[i]
        p2 = pnl[i + 1]

        if p1 == 0:
            breakevens.append(prices[i])

        elif p1 * p2 < 0:

            x1 = prices[i]
            x2 = prices[i + 1]

            # Linear interpolation
            try:
                breakeven = (
                    x1
                    + (0 - p1)
                    * (x2 - x1)
                    / (p2 - p1)
                )

                breakevens.append(breakeven)

            except Exception:
                pass

    # Remove duplicates
    output = []

    for value in breakevens:
        if not output or abs(value - output[-1]) > 0.01:
            output.append(value)

    return output


def _strategy_chart(payoff_df, spot):
    """
    Create strategy payoff chart.
    """

    if payoff_df.empty:
        return None

    base = (
        alt.Chart(payoff_df)
        .mark_line(
            strokeWidth=3
        )
        .encode(
            x=alt.X(
                "underlying_price:Q",
                title="NIFTY Price"
            ),
            y=alt.Y(
                "strategy_pnl:Q",
                title="P&L"
            ),
            tooltip=[
                alt.Tooltip(
                    "underlying_price:Q",
                    title="NIFTY",
                    format=",.0f"
                ),
                alt.Tooltip(
                    "strategy_pnl:Q",
                    title="P&L",
                    format=",.2f"
                )
            ]
        )
    )

    zero_line = (
        alt.Chart(
            pd.DataFrame(
                {"strategy_pnl": [0]}
            )
        )
        .mark_rule(
            strokeDash=[5, 5]
        )
        .encode(
            y="strategy_pnl:Q"
        )
    )

    spot_line = (
        alt.Chart(
            pd.DataFrame(
                {"spot": [spot]}
            )
        )
        .mark_rule(
            strokeDash=[3, 3]
        )
        .encode(
            x=alt.X(
                "spot:Q"
            )
        )
    )

    return (
        (base + zero_line + spot_line)
        .properties(
            height=430
        )
        .interactive()
    )


# ============================================================
# STRATEGY BUILDER
# ============================================================

def _build_strategy(
    strategy,
    strike_values,
    df,
    quantity,
    selections
):

    if strategy == "LONG STRADDLE":

        strike = selections["strike"]

        ce_premium = _get_premium(
            df,
            strike,
            "CE"
        )

        pe_premium = _get_premium(
            df,
            strike,
            "PE"
        )

        legs = long_straddle(
            strike,
            ce_premium,
            pe_premium,
            quantity
        )

    elif strategy == "SHORT STRADDLE":

        strike = selections["strike"]

        ce_premium = _get_premium(
            df,
            strike,
            "CE"
        )

        pe_premium = _get_premium(
            df,
            strike,
            "PE"
        )

        legs = short_straddle(
            strike,
            ce_premium,
            pe_premium,
            quantity
        )

    elif strategy == "LONG STRANGLE":

        ce_strike = selections["ce_strike"]
        pe_strike = selections["pe_strike"]

        ce_premium = _get_premium(
            df,
            ce_strike,
            "CE"
        )

        pe_premium = _get_premium(
            df,
            pe_strike,
            "PE"
        )

        legs = long_strangle(
            ce_strike,
            pe_strike,
            ce_premium,
            pe_premium,
            quantity
        )

    elif strategy == "SHORT STRANGLE":

        ce_strike = selections["ce_strike"]
        pe_strike = selections["pe_strike"]

        ce_premium = _get_premium(
            df,
            ce_strike,
            "CE"
        )

        pe_premium = _get_premium(
            df,
            pe_strike,
            "PE"
        )

        legs = short_strangle(
            ce_strike,
            pe_strike,
            ce_premium,
            pe_premium,
            quantity
        )

    elif strategy == "BULL CALL SPREAD":

        buy_strike = selections["buy_strike"]
        sell_strike = selections["sell_strike"]

        buy_premium = _get_premium(
            df,
            buy_strike,
            "CE"
        )

        sell_premium = _get_premium(
            df,
            sell_strike,
            "CE"
        )

        legs = bull_call_spread(
            buy_strike,
            sell_strike,
            buy_premium,
            sell_premium,
            quantity
        )

    elif strategy == "BEAR PUT SPREAD":

        buy_strike = selections["buy_strike"]
        sell_strike = selections["sell_strike"]

        buy_premium = _get_premium(
            df,
            buy_strike,
            "PE"
        )

        sell_premium = _get_premium(
            df,
            sell_strike,
            "PE"
        )

        legs = bear_put_spread(
            buy_strike,
            sell_strike,
            buy_premium,
            sell_premium,
            quantity
        )

    elif strategy == "IRON CONDOR":

        put_buy_strike = selections["put_buy_strike"]
        put_sell_strike = selections["put_sell_strike"]
        call_sell_strike = selections["call_sell_strike"]
        call_buy_strike = selections["call_buy_strike"]

        put_buy_premium = _get_premium(
            df,
            put_buy_strike,
            "PE"
        )

        put_sell_premium = _get_premium(
            df,
            put_sell_strike,
            "PE"
        )

        call_sell_premium = _get_premium(
            df,
            call_sell_strike,
            "CE"
        )

        call_buy_premium = _get_premium(
            df,
            call_buy_strike,
            "CE"
        )

        legs = iron_condor(
            put_buy_strike,
            put_sell_strike,
            call_sell_strike,
            call_buy_strike,
            put_buy_premium,
            put_sell_premium,
            call_sell_premium,
            call_buy_premium,
            quantity
        )

    else:

        legs = []

    return legs


# ============================================================
# STRATEGY UI
# ============================================================

def render_strategy_tab(df, spot, atm, expiry):
    """
    Main Strategy Analysis interface.
    """

    st.markdown(
        '<div class="section-title">Strategy Analysis</div>',
        unsafe_allow_html=True
    )

    if df.empty:
        st.warning(
            "Option-chain data is not available."
        )
        return

    if "strike" not in df.columns:
        st.error(
            "Strike column is missing from option-chain data."
        )
        return

    strikes = sorted(
        pd.to_numeric(
            df["strike"],
            errors="coerce"
        )
        .dropna()
        .unique()
    )

    if not strikes:
        st.warning(
            "No valid strikes available."
        )
        return

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    h1, h2, h3 = st.columns(3)

    with h1:
        st.metric(
            "NIFTY SPOT",
            f"{spot:,.2f}"
        )

    with h2:
        st.metric(
            "ATM",
            f"{atm:,.0f}"
        )

    with h3:
        st.metric(
            "EXPIRY",
            str(expiry)
        )

    st.write("")

    # --------------------------------------------------------
    # STRATEGY SELECTOR
    # --------------------------------------------------------

    strategy = st.selectbox(
        "STRATEGY",
        [
            "LONG STRADDLE",
            "SHORT STRADDLE",
            "LONG STRANGLE",
            "SHORT STRANGLE",
            "BULL CALL SPREAD",
            "BEAR PUT SPREAD",
            "IRON CONDOR",
        ],
        key="strategy_selector"
    )

    # --------------------------------------------------------
    # QUANTITY
    # --------------------------------------------------------

    # --------------------------------------------------------
    # LOT SIZE
    # --------------------------------------------------------

    lot_size = 75

    lots = st.number_input(
        "LOTS",
        min_value=1,
        value=1,
        step=1,
        key="strategy_lots"
    )

    quantity = int(
        lots * lot_size
    )
    st.caption(
        f"Lot Size: {lot_size} | Quantity: {quantity}"
    )

    selections = {}

    # --------------------------------------------------------
    # STRADDLES
    # --------------------------------------------------------

    if strategy in [
        "LONG STRADDLE",
        "SHORT STRADDLE"
    ]:

        strike = st.selectbox(
            "STRIKE",
            strikes,
            index=(
                strikes.index(atm)
                if atm in strikes
                else len(strikes) // 2
            ),
            key="straddle_strike"
        )

        selections["strike"] = strike

        ce_premium = _get_premium(
            df,
            strike,
            "CE"
        )

        pe_premium = _get_premium(
            df,
            strike,
            "PE"
        )

        c1, c2 = st.columns(2)

        with c1:
            st.metric(
                "CE PREMIUM",
                f"₹{ce_premium:,.2f}"
            )

        with c2:
            st.metric(
                "PE PREMIUM",
                f"₹{pe_premium:,.2f}"
            )

    # --------------------------------------------------------
    # STRANGLES
    # --------------------------------------------------------

    elif strategy in [
        "LONG STRANGLE",
        "SHORT STRANGLE"
    ]:

        c1, c2 = st.columns(2)

        with c1:

            ce_strike = st.selectbox(
                "CALL STRIKE",
                strikes,
                index=(
                    strikes.index(atm)
                    if atm in strikes
                    else len(strikes) // 2
                ),
                key="strangle_ce_strike"
            )

        with c2:

            pe_strike = st.selectbox(
                "PUT STRIKE",
                strikes,
                index=(
                    strikes.index(atm)
                    if atm in strikes
                    else len(strikes) // 2
                ),
                key="strangle_pe_strike"
            )

        selections["ce_strike"] = ce_strike
        selections["pe_strike"] = pe_strike

        ce_premium = _get_premium(
            df,
            ce_strike,
            "CE"
        )

        pe_premium = _get_premium(
            df,
            pe_strike,
            "PE"
        )

        c1, c2 = st.columns(2)

        with c1:
            st.metric(
                "CE PREMIUM",
                f"₹{ce_premium:,.2f}"
            )

        with c2:
            st.metric(
                "PE PREMIUM",
                f"₹{pe_premium:,.2f}"
            )

    # --------------------------------------------------------
    # SPREADS
    # --------------------------------------------------------

    elif strategy in [
        "BULL CALL SPREAD",
        "BEAR PUT SPREAD"
    ]:

        option_type = (
            "CE"
            if strategy == "BULL CALL SPREAD"
            else "PE"
        )

        c1, c2 = st.columns(2)

        with c1:

            buy_strike = st.selectbox(
                "BUY STRIKE",
                strikes,
                index=(
                    strikes.index(atm)
                    if atm in strikes
                    else len(strikes) // 2
                ),
                key="spread_buy_strike"
            )

        with c2:

            sell_strike = st.selectbox(
                "SELL STRIKE",
                strikes,
                index=min(
                    (
                        strikes.index(atm) + 4
                        if atm in strikes
                        else 4
                    ),
                    len(strikes) - 1
                ),
                key="spread_sell_strike"
            )

        selections["buy_strike"] = buy_strike
        selections["sell_strike"] = sell_strike

        buy_premium = _get_premium(
            df,
            buy_strike,
            option_type
        )

        sell_premium = _get_premium(
            df,
            sell_strike,
            option_type
        )

        c1, c2 = st.columns(2)

        with c1:
            st.metric(
                "BUY PREMIUM",
                f"₹{buy_premium:,.2f}"
            )

        with c2:
            st.metric(
                "SELL PREMIUM",
                f"₹{sell_premium:,.2f}"
            )

    # --------------------------------------------------------
    # IRON CONDOR
    # --------------------------------------------------------

    elif strategy == "IRON CONDOR":

        center = (
            strikes.index(atm)
            if atm in strikes
            else len(strikes) // 2
        )

        put_buy_index = max(
            0,
            center - 8
        )

        put_sell_index = max(
            0,
            center - 4
        )

        call_sell_index = min(
            len(strikes) - 1,
            center + 4
        )

        call_buy_index = min(
            len(strikes) - 1,
            center + 8
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            put_buy_strike = st.selectbox(
                "PUT BUY",
                strikes,
                index=put_buy_index,
                key="ic_put_buy"
            )

        with c2:
            put_sell_strike = st.selectbox(
                "PUT SELL",
                strikes,
                index=put_sell_index,
                key="ic_put_sell"
            )

        with c3:
            call_sell_strike = st.selectbox(
                "CALL SELL",
                strikes,
                index=call_sell_index,
                key="ic_call_sell"
            )

        with c4:
            call_buy_strike = st.selectbox(
                "CALL BUY",
                strikes,
                index=call_buy_index,
                key="ic_call_buy"
            )

        selections["put_buy_strike"] = put_buy_strike
        selections["put_sell_strike"] = put_sell_strike
        selections["call_sell_strike"] = call_sell_strike
        selections["call_buy_strike"] = call_buy_strike

    st.write("")

    # --------------------------------------------------------
    # ANALYZE
    # --------------------------------------------------------

    analyze = st.button(
        "⚡ ANALYZE STRATEGY",
        width="stretch",
        key="analyze_strategy"
    )

    if not analyze:
        st.info(
            "Select the strategy parameters and click "
            "ANALYZE STRATEGY."
        )
        return

    # --------------------------------------------------------
    # BUILD LEGS
    # --------------------------------------------------------

    try:

        legs = _build_strategy(
            strategy,
            strikes,
            df,
            quantity,
            selections
        )

    except Exception as e:

        st.error(
            f"Unable to build strategy: {e}"
        )
        return

    if not legs:
        st.error(
            "No strategy legs were created."
        )
        return

    # --------------------------------------------------------
    # PRICE RANGE
    # --------------------------------------------------------

    lower_price = max(
        0,
        spot * 0.90
    )

    upper_price = spot * 1.10

    price_range = np.linspace(
        lower_price,
        upper_price,
        301
    )

    # --------------------------------------------------------
    # PAYOFF
    # --------------------------------------------------------

    payoff_df = calculate_strategy_payoff(
        legs,
        price_range
    )

    if payoff_df.empty:
        st.warning(
            "Unable to calculate strategy payoff."
        )
        return

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    max_profit = payoff_df[
        "strategy_pnl"
    ].max()

    max_loss = payoff_df[
        "strategy_pnl"
    ].min()

    breakevens = _calculate_breakevens(
        payoff_df
    )

    # --------------------------------------------------------
    # STRATEGY SUMMARY
    # --------------------------------------------------------

    st.markdown(
        "### Strategy Summary"
    )

    m1, m2, m3, m4 = st.columns(4)

    with m1:

        st.metric(
            "MAX PROFIT",
            (
                "UNLIMITED"
                if strategy in [
                    "LONG STRADDLE",
                    "LONG STRANGLE"
                ]
                else f"₹{max_profit:,.2f}"
            )
        )

    with m2:

        st.metric(
            "MAX LOSS",
            (
                "UNLIMITED"
                if strategy in [
                    "SHORT STRADDLE",
                    "SHORT STRANGLE"
                ]
                else f"₹{max_loss:,.2f}"
            )
        )

    with m3:

        if breakevens:

            text = " / ".join(
                f"{x:,.2f}"
                for x in breakevens[:2]
            )

        else:

            text = "-"

        st.metric(
            "BREAKEVEN",
            text
        )

    with m4:

        current_index = (
            (payoff_df["underlying_price"] - spot)
            .abs()
            .idxmin()
        )

        current_pnl = payoff_df.loc[
            current_index,
            "strategy_pnl"
        ]

        st.metric(
            "CURRENT P&L",
            f"₹{current_pnl:,.2f}"
        )

    # --------------------------------------------------------
    # LEGS
    # --------------------------------------------------------

    st.markdown(
        "### Strategy Legs"
    )

    legs_df = pd.DataFrame(
        legs
    )

    legs_df = legs_df[
        [
            "action",
            "option_type",
            "strike",
            "premium",
            "quantity"
        ]
    ]

    legs_df.columns = [
        "ACTION",
        "TYPE",
        "STRIKE",
        "PREMIUM",
        "QUANTITY"
    ]

    st.dataframe(
        legs_df,
        width="stretch",
        hide_index=True
    )

    # --------------------------------------------------------
    # PAYOFF CHART
    # --------------------------------------------------------

    st.markdown(
        "### Expiry Payoff"
    )

    chart = _strategy_chart(
        payoff_df,
        spot
    )

    if chart:

        st.altair_chart(
            chart,
            width="stretch"
        )

    # --------------------------------------------------------
    # P&L TABLE
    # --------------------------------------------------------

    st.markdown(
        "### Strategy P&L"
    )

    display_df = payoff_df.copy()

    display_df["underlying_price"] = (
        display_df["underlying_price"]
        .round(0)
        .astype(int)
    )

    display_df["strategy_pnl"] = (
        display_df["strategy_pnl"]
        .round(2)
    )

    st.dataframe(
        display_df,
        width="stretch",
        height=300,
        hide_index=True
    )
    