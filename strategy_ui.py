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
from strategy_engine import calculate_strategy_metrics


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
    Robust live premium lookup.

    Supports common CE/PE LTP column names.
    """

    if df is None or df.empty:
        return 0.0

    # --------------------------------------------------------
    # STRIKE COLUMN
    # --------------------------------------------------------

    strike_col = None

    for col in [
        "strike",
        "strike_price",
        "strikePrice",
        "STRIKE",
    ]:
        if col in df.columns:
            strike_col = col
            break

    if strike_col is None:
        return 0.0

    temp = df.copy()

    temp[strike_col] = pd.to_numeric(
        temp[strike_col],
        errors="coerce"
    )

    rows = temp[
        temp[strike_col] == float(strike)
    ]

    if rows.empty:
        return 0.0

    # --------------------------------------------------------
    # PREMIUM COLUMN
    # --------------------------------------------------------

    if option_type == "CE":

        candidates = [
            "ce_ltp",
            "CE_LTP",
            "ce_last_price",
            "CE_LAST_PRICE",
            "call_ltp",
            "call_price",
        ]

    else:

        candidates = [
            "pe_ltp",
            "PE_LTP",
            "pe_last_price",
            "PE_LAST_PRICE",
            "put_ltp",
            "put_price",
        ]

    premium_col = None

    for col in candidates:

        if col in rows.columns:
            premium_col = col
            break

    if premium_col is None:
        return 0.0

    return _safe_float(
        rows[premium_col].iloc[0]
    )
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
    # ============================================================
    # LIVE MARKET HEADER
    # ============================================================

    st.markdown("### LIVE MARKET")

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric(
            "NIFTY",
            f"{spot:,.2f}"
            if spot is not None
            else "-"
        )

    with m2:
        st.metric(
            "ATM",
            f"{atm:,.0f}"
            if atm is not None
            else "-"
        )

    with m3:
        st.metric(
            "EXPIRY",
            expiry
            if expiry is not None
            else "-"
        )
    with m4:

        st.metric(
            "ATM DISTANCE",
            f"{abs(float(spot) - float(atm)):,.0f}"
            if spot is not None and atm is not None
            else "-"
        )


# ============================================================
# OPTION CHAIN VALIDATION
# ============================================================

    if df is None or df.empty:

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


    if len(strikes) == 0:

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
        st.warning("Unable to calculate strategy payoff.")
        return

    # --------------------------------------------------------
    # RISK METRICS
    # --------------------------------------------------------

    risk = calculate_strategy_metrics(
        legs,
        price_range
    )

    net_premium = risk["net_premium"]
    risk_max_profit = risk["max_profit"]
    risk_max_loss = risk["max_loss"]
    risk_breakevens = risk["breakevens"]

    payoff_max_profit = payoff_df["strategy_pnl"].max()
    payoff_max_loss = payoff_df["strategy_pnl"].min()
    breakevens = _calculate_breakevens(payoff_df)

    # --------------------------------------------------------
    # STRATEGY SUMMARY
    # --------------------------------------------------------

    st.markdown("### Strategy Summary")

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric(
            "MAX PROFIT",
            (
                "UNLIMITED"
                if strategy in ["LONG STRADDLE", "LONG STRANGLE"]
                else f"₹{payoff_max_profit:,.2f}"
            )
        )

    with m2:
        st.metric(
            "MAX LOSS",
            (
                "UNLIMITED"
                if strategy in ["SHORT STRADDLE", "SHORT STRANGLE"]
                else f"₹{payoff_max_loss:,.2f}"
            )
        )

    with m3:
        st.metric(
            "BREAKEVEN",
            (
                " / ".join(f"{x:,.2f}" for x in breakevens[:2])
                if breakevens
                else "-"
            )
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
    # STRATEGY RISK
    # --------------------------------------------------------

    st.markdown("### Strategy Risk")

    r1, r2, r3, r4 = st.columns(4)

    with r1:
        st.metric("NET PREMIUM", f"₹{net_premium:,.2f}")

    with r2:
        st.metric(
            "MAX PROFIT",
            (
                "UNLIMITED"
                if np.isinf(risk_max_profit)
                else f"₹{risk_max_profit:,.2f}"
            )
        )

    with r3:
        st.metric(
            "MAX LOSS",
            (
                "UNLIMITED"
                if np.isinf(risk_max_loss)
                else f"₹{risk_max_loss:,.2f}"
            )
        )

    with r4:
        st.metric(
            "BREAKEVEN",
            (
                " / ".join(f"{x:,.0f}" for x in risk_breakevens)
                if risk_breakevens
                else "-"
            )
        )

    # --------------------------------------------------------
    # STRATEGY LEGS
    # --------------------------------------------------------

    st.markdown("### Strategy Legs")

    legs_df = pd.DataFrame(legs)[
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
        height=170,
        hide_index=True
    )

    # --------------------------------------------------------
    # PAYOFF CHART
    # --------------------------------------------------------

    st.markdown("### Expiry Payoff")

    chart = _strategy_chart(payoff_df, spot)

    if chart:
        st.altair_chart(
            chart,
            width="stretch",
            height=360
        )
    # ============================================================
    # PREMIUM VALIDATION
    # ============================================================

    invalid_legs = [
        leg
        for leg in legs
        if float(leg.get("premium", 0)) <= 0
    ]

    if invalid_legs:

        st.warning(
            "Live premium could not be found for one or more "
            "strategy legs. Check the option-chain columns."
        )

        st.dataframe(
            pd.DataFrame(legs),
            width="stretch",
            hide_index=True
        )

        return
    # --------------------------------------------------------
    # P&L TABLE
    # --------------------------------------------------------

    st.markdown("### Strategy P&L")

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
        height=190,
        hide_index=True
    )
