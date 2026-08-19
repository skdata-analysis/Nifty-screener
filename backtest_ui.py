# ============================================================
# BACKTEST UI
# Professional strategy backtesting interface
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np

from payoff_analysis import (
    attach_entry_premiums,
    build_payoff_dataframe,
    calculate_payoff_summary,
)

from backtest_data import (
    get_historical_expiries,
    get_historical_dates,
    load_historical_snapshots,
)

from backtest_runner import (
    run_single_backtest,
    run_multi_trade_backtest,
)

from strategy_builder import (
    STRATEGIES,
    build_strategy_legs,
)


# ============================================================
# HELPERS
# ============================================================

def get_atm_strike(df):
    """
    Calculate ATM strike from spot price and available strikes.
    """

    if df is None or df.empty:
        return None

    if "spot_price" not in df.columns:
        return None

    if "strike" not in df.columns:
        return None

    spot_values = pd.to_numeric(
        df["spot_price"],
        errors="coerce"
    ).dropna()

    strikes = pd.to_numeric(
        df["strike"],
        errors="coerce"
    ).dropna().unique()

    if spot_values.empty or len(strikes) == 0:
        return None

    spot = float(
        spot_values.iloc[0]
    )

    return float(
        min(
            strikes,
            key=lambda x: abs(
                float(x) - spot
            )
        )
    )


def format_money(value):
    """
    Format P&L values safely.
    """

    try:
        value = float(value)

        if np.isnan(value):
            return "₹0.00"

        return f"₹{value:,.2f}"

    except Exception:
        return "₹0.00"


def format_number(value):
    """
    Format numeric values safely.
    """

    try:
        value = float(value)

        if np.isnan(value):
            return "0.00"

        return f"{value:,.2f}"

    except Exception:
        return "0.00"


def format_profit_factor(value):
    """
    Format profit factor including infinity.
    """

    try:

        value = float(value)

        if np.isinf(value):
            return "∞"

        if np.isnan(value):
            return "0.00"

        return f"{value:.2f}"

    except Exception:
        return "0.00"


def get_available_strikes(df):
    """
    Return sorted valid strikes.
    """

    if df is None or df.empty:
        return []

    if "strike" not in df.columns:
        return []

    strikes = pd.to_numeric(
        df["strike"],
        errors="coerce"
    ).dropna().unique()

    return sorted(
        [float(x) for x in strikes]
    )


def get_snapshot_times_from_data(
    snapshots
):
    """
    Return clean timestamp list.
    """

    times = []

    for snapshot in snapshots:

        timestamp = snapshot.get(
            "timestamp"
        )

        if timestamp is None:
            continue

        parsed = pd.to_datetime(
            timestamp,
            errors="coerce"
        )

        if not pd.isna(parsed):
            times.append(parsed)

    return times


def get_spot_price(df):
    """
    Return spot price from snapshot.
    """

    if (
        df is None
        or df.empty
        or "spot_price" not in df.columns
    ):
        return None

    values = pd.to_numeric(
        df["spot_price"],
        errors="coerce"
    ).dropna()

    if values.empty:
        return None

    return float(
        values.iloc[0]
    )


def get_pcr(df):
    """
    Return PCR if available.
    """

    if (
        df is None
        or df.empty
        or "pcr" not in df.columns
    ):
        return None

    values = pd.to_numeric(
        df["pcr"],
        errors="coerce"
    ).dropna()

    if values.empty:
        return None

    return float(
        values.iloc[0]
    )


# ============================================================
# STRATEGY PARAMETER UI
# ============================================================

def render_strategy_parameters(
    strategy,
    available_strikes,
    atm_strike
):
    """
    Render strategy-specific strike controls.

    Returns:
        selections dictionary
    """

    if not available_strikes:
        st.error(
            "No valid option strikes available."
        )
        return None

    atm_index = min(
        range(
            len(available_strikes)
        ),
        key=lambda i: abs(
            available_strikes[i]
            - atm_strike
        )
    ) if atm_strike is not None else 0

    # ========================================================
    # STRADDLE
    # ========================================================

    if strategy in [
        "LONG STRADDLE",
        "SHORT STRADDLE",
    ]:

        strike = st.selectbox(
            "ATM STRIKE",
            available_strikes,
            index=atm_index,
            key="bt_straddle_strike"
        )

        return {
            "strike": float(strike)
        }

    # ========================================================
    # STRANGLE
    # ========================================================

    if strategy in [
        "LONG STRANGLE",
        "SHORT STRANGLE",
    ]:

        left, right = st.columns(2)

        put_default = max(
            0,
            atm_index - 2
        )

        call_default = min(
            len(available_strikes) - 1,
            atm_index + 2
        )

        with left:

            put_strike = st.selectbox(
                "PUT STRIKE",
                available_strikes,
                index=put_default,
                key="bt_put_strike"
            )

        with right:

            call_strike = st.selectbox(
                "CALL STRIKE",
                available_strikes,
                index=call_default,
                key="bt_call_strike"
            )

        if put_strike >= call_strike:

            st.error(
                "PUT STRIKE must be below CALL STRIKE."
            )

            return None

        return {
            "put_strike": float(
                put_strike
            ),
            "call_strike": float(
                call_strike
            ),
        }

    # ========================================================
    # BULL CALL / BEAR PUT SPREAD
    # ========================================================

    if strategy in [
        "BULL CALL SPREAD",
        "BEAR PUT SPREAD",
    ]:

        left, right = st.columns(2)

        buy_default = max(
            0,
            atm_index - 1
        )

        sell_default = min(
            len(available_strikes) - 1,
            atm_index + 1
        )

        with left:

            buy_strike = st.selectbox(
                "BUY STRIKE",
                available_strikes,
                index=buy_default,
                key="bt_buy_strike"
            )

        with right:

            sell_strike = st.selectbox(
                "SELL STRIKE",
                available_strikes,
                index=sell_default,
                key="bt_sell_strike"
            )

        if strategy == "BULL CALL SPREAD":

            if buy_strike >= sell_strike:

                st.error(
                    "For Bull Call Spread, "
                    "BUY STRIKE must be below SELL STRIKE."
                )

                return None

        else:

            if buy_strike <= sell_strike:

                st.error(
                    "For Bear Put Spread, "
                    "BUY STRIKE must be above SELL STRIKE."
                )

                return None

        return {
            "buy_strike": float(
                buy_strike
            ),
            "sell_strike": float(
                sell_strike
            ),
        }

    # ========================================================
    # IRON CONDOR
    # ========================================================

    if strategy == "IRON CONDOR":

        c1, c2, c3, c4 = st.columns(4)

        put_buy_default = max(
            0,
            atm_index - 4
        )

        put_sell_default = max(
            0,
            atm_index - 2
        )

        call_sell_default = min(
            len(available_strikes) - 1,
            atm_index + 2
        )

        call_buy_default = min(
            len(available_strikes) - 1,
            atm_index + 4
        )

        with c1:

            put_buy_strike = st.selectbox(
                "PUT BUY",
                available_strikes,
                index=put_buy_default,
                key="bt_ic_put_buy"
            )

        with c2:

            put_sell_strike = st.selectbox(
                "PUT SELL",
                available_strikes,
                index=put_sell_default,
                key="bt_ic_put_sell"
            )

        with c3:

            call_sell_strike = st.selectbox(
                "CALL SELL",
                available_strikes,
                index=call_sell_default,
                key="bt_ic_call_sell"
            )

        with c4:

            call_buy_strike = st.selectbox(
                "CALL BUY",
                available_strikes,
                index=call_buy_default,
                key="bt_ic_call_buy"
            )

        if not (
            put_buy_strike
            < put_sell_strike
            < call_sell_strike
            < call_buy_strike
        ):

            st.error(
                "Iron Condor strikes must satisfy: "
                "PUT BUY < PUT SELL < CALL SELL < CALL BUY."
            )

            return None

        return {
            "put_buy_strike": float(
                put_buy_strike
            ),
            "put_sell_strike": float(
                put_sell_strike
            ),
            "call_sell_strike": float(
                call_sell_strike
            ),
            "call_buy_strike": float(
                call_buy_strike
            ),
        }

    st.error(
        f"Unsupported strategy: {strategy}"
    )

    return None


# ============================================================
# DISPLAY METRICS
# ============================================================

def display_metrics(metrics):

    total_pnl = metrics.get(
        "total_pnl",
        0
    )

    win_rate = metrics.get(
        "win_rate",
        0
    )

    profit_factor = metrics.get(
        "profit_factor",
        0
    )

    max_drawdown = metrics.get(
        "max_drawdown",
        0
    )

    total_trades = metrics.get(
        "total_trades",
        0
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:

        st.metric(
            "TOTAL P&L",
            format_money(
                total_pnl
            )
        )

    with c2:

        st.metric(
            "WIN RATE",
            f"{format_number(win_rate)}%"
        )

    with c3:

        st.metric(
            "PROFIT FACTOR",
            format_profit_factor(
                profit_factor
            )
        )

    with c4:

        st.metric(
            "MAX DRAWDOWN",
            format_money(
                max_drawdown
            )
        )

    with c5:

        st.metric(
            "TRADES",
            int(total_trades)
        )


# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_results(
    results,
    trade=None
):

    if results is None:
        return

    if not isinstance(
        results,
        pd.DataFrame
    ):
        return

    if results.empty:

        st.warning(
            "No valid trades were generated."
        )

        return

    # ========================================================
    # EQUITY CURVE
    # ========================================================

    st.markdown(
        '<div class="section-title">EQUITY CURVE</div>',
        unsafe_allow_html=True
    )

    chart_df = results.copy()

    if "cumulative_pnl" in chart_df.columns:

        chart_df["Trade"] = range(
            1,
            len(chart_df) + 1
        )

        chart_df = chart_df.set_index(
            "Trade"
        )

        st.line_chart(
            chart_df["cumulative_pnl"],
            height=220,
            use_container_width=True
        )

    # ========================================================
    # TRADE HISTORY
    # ========================================================

    st.markdown(
        '<div class="section-title">TRADE HISTORY</div>',
        unsafe_allow_html=True
    )

    columns = [
        "entry_time",
        "exit_time",
        "strategy_pnl",
        "cumulative_pnl",
        "result",
    ]

    available_columns = [
        col
        for col in columns
        if col in results.columns
    ]

    display_df = results[
        available_columns
    ].copy()

    if "strategy_pnl" in display_df.columns:

        display_df["strategy_pnl"] = (
            pd.to_numeric(
                display_df["strategy_pnl"],
                errors="coerce"
            )
            .round(2)
        )

    if "cumulative_pnl" in display_df.columns:

        display_df["cumulative_pnl"] = (
            pd.to_numeric(
                display_df["cumulative_pnl"],
                errors="coerce"
            )
            .round(2)
        )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=220
    )

    # ========================================================
    # SINGLE TRADE LEG DETAILS
    # ========================================================

    if trade is not None:

        st.markdown(
            '<div class="section-title">LEG DETAILS</div>',
            unsafe_allow_html=True
        )

        leg_rows = []

        for leg in trade.get(
            "legs",
            []
        ):

            leg_rows.append(
                {
                    "STRIKE":
                        leg.get("strike"),

                    "TYPE":
                        leg.get("option_type"),

                    "ACTION":
                        leg.get("action"),

                    "QTY":
                        leg.get("quantity"),

                    "ENTRY":
                        leg.get(
                            "entry_premium"
                        ),

                    "EXIT":
                        leg.get(
                            "exit_premium"
                        ),

                    "P&L":
                        leg.get(
                            "pnl"
                        ),
                }
            )

        if leg_rows:

            leg_df = pd.DataFrame(
                leg_rows
            )

            st.dataframe(
                leg_df,
                use_container_width=True,
                hide_index=True,
                height=180
            )


# ============================================================
# BACKTEST PAGE
# ============================================================

def render_backtest_page():

    st.markdown(
        """
        <div class="section-title">
            BACKTEST ENGINE
        </div>
        """,
        unsafe_allow_html=True
    )

    # ========================================================
    # HISTORICAL EXPIRIES
    # ========================================================

    expiries = get_historical_expiries()

    if not expiries:

        st.warning(
            "No historical option-chain data available."
        )

        return

    # ========================================================
    # TOP CONTROLS
    # ========================================================

    c1, c2, c3, c4 = st.columns(4)

    # --------------------------------------------------------
    # EXPIRY
    # --------------------------------------------------------

    with c1:

        expiry = st.selectbox(
            "EXPIRY",
            expiries,
            key="bt_expiry"
        )

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    dates = get_historical_dates(
        expiry=expiry
    )

    if not dates:

        st.warning(
            "No historical dates available "
            "for selected expiry."
        )

        return

    with c2:

        selected_date = st.selectbox(
            "TRADING DATE",
            dates,
            key="bt_date"
        )

    # --------------------------------------------------------
    # STRATEGY
    # --------------------------------------------------------

    with c3:

        strategy = st.selectbox(
            "STRATEGY",
            STRATEGIES,
            key="bt_strategy"
        )

    # --------------------------------------------------------
    # QUANTITY
    # --------------------------------------------------------

    with c4:

        quantity = st.number_input(
            "QUANTITY",
            min_value=1,
            value=75,
            step=75,
            key="bt_quantity"
        )

    # ========================================================
    # LOAD SNAPSHOTS
    # ========================================================

    try:

        snapshots = load_historical_snapshots(
            expiry=expiry,
            start_date=selected_date,
            end_date=selected_date,
        )

    except Exception as e:

        st.error(
            f"Unable to load historical data: {e}"
        )

        return

    if not snapshots:

        st.warning(
            "No historical snapshots found."
        )

        return

    # ========================================================
    # DATA STATUS
    # ========================================================

    first_df = snapshots[0].get(
        "data"
    )

    last_df = snapshots[-1].get(
        "data"
    )

    atm_strike = get_atm_strike(
        first_df
    )

    spot_price = get_spot_price(
        first_df
    )

    pcr = get_pcr(
        first_df
    )

    times = get_snapshot_times_from_data(
        snapshots
    )

    s1, s2, s3, s4 = st.columns(4)

    with s1:

        st.metric(
            "SNAPSHOTS",
            len(snapshots)
        )

    with s2:

        if spot_price is not None:

            st.metric(
                "SPOT",
                f"{spot_price:,.2f}"
            )

        else:

            st.metric(
                "SPOT",
                "—"
            )

    with s3:

        if atm_strike is not None:

            st.metric(
                "ATM",
                f"{atm_strike:,.0f}"
            )

        else:

            st.metric(
                "ATM",
                "—"
            )

    with s4:

        if pcr is not None:

            st.metric(
                "PCR",
                f"{pcr:.3f}"
            )

        else:

            st.metric(
                "PCR",
                "—"
            )

    # ========================================================
    # STRIKE DATA
    # ========================================================

    available_strikes = get_available_strikes(
        first_df
    )

    if not available_strikes:

        st.error(
            "No valid strikes found."
        )

        return

    # ========================================================
    # STRATEGY PARAMETERS
    # ========================================================

    st.markdown(
        '<div class="section-title">STRATEGY PARAMETERS</div>',
        unsafe_allow_html=True
    )

    selections = render_strategy_parameters(
        strategy=strategy,
        available_strikes=available_strikes,
        atm_strike=atm_strike
    )

    if selections is None:

        return

    # ========================================================
    # BUILD STRATEGY LEGS
    # ========================================================

    try:

        legs = build_strategy_legs(
            strategy,
            selections,
            quantity
        )

    except Exception as e:

        st.error(
            f"Unable to build strategy: {e}"
        )

        return

    if not legs:

        st.error(
            "No strategy legs were generated."
        )

        return

    # ========================================================
    # SHOW LEGS
    # ========================================================

    leg_preview = pd.DataFrame(
        legs
    )

    if not leg_preview.empty:

        st.dataframe(
            leg_preview[
                [
                    "strike",
                    "option_type",
                    "action",
                    "quantity",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            height=150
        )

    # ========================================================
    # BACKTEST MODE
    # ========================================================

    st.markdown(
        '<div class="section-title">BACKTEST MODE</div>',
        unsafe_allow_html=True
    )

    mode = st.radio(
        "MODE",
        [
            "SINGLE TRADE",
            "MULTI TRADE",
        ],
        horizontal=True,
        key="bt_mode"
    )

    # ========================================================
    # SINGLE TRADE TIME CONTROLS
    # ========================================================

    entry_time = None
    exit_time = None

    if mode == "SINGLE TRADE":

        if len(times) < 2:

            st.warning(
                "At least two snapshots are required "
                "for a backtest."
            )

            return

        time_strings = [
            pd.to_datetime(
                t
            ).strftime(
                "%H:%M:%S"
            )
            for t in times
        ]

        tc1, tc2 = st.columns(2)

        with tc1:

            entry_label = st.selectbox(
                "ENTRY TIME",
                time_strings[:-1],
                index=0,
                key="bt_entry_time"
            )

        entry_position = (
            time_strings.index(
                entry_label
            )
        )

        exit_options = (
            time_strings[
                entry_position + 1:
            ]
        )

        if not exit_options:

            st.warning(
                "No exit snapshot available "
                "after selected entry."
            )

            return

        with tc2:

            exit_label = st.selectbox(
                "EXIT TIME",
                exit_options,
                index=len(
                    exit_options
                ) - 1,
                key="bt_exit_time"
            )

        entry_time = times[
            entry_position
        ]

        exit_time = times[
            time_strings.index(
                exit_label
            )
        ]

    # ========================================================
    # MULTI TRADE CONTROLS
    # ========================================================

    entry_step = 1
    holding_steps = 1

    if mode == "MULTI TRADE":

        mc1, mc2 = st.columns(2)

        with mc1:

            entry_step = st.number_input(
                "ENTRY STEP",
                min_value=1,
                value=1,
                step=1,
                key="bt_entry_step"
            )

        with mc2:

            holding_steps = st.number_input(
                "HOLDING SNAPSHOTS",
                min_value=1,
                value=1,
                step=1,
                key="bt_holding_steps"
            )

        estimated_trades = max(
            0,
            (
                len(snapshots)
                - int(holding_steps)
                + int(entry_step)
                - 1
            )
            // int(entry_step)
        )

        st.caption(
            f"Estimated trade opportunities: "
            f"{estimated_trades}"
        )

    # ========================================================
    # RUN BACKTEST
    # ========================================================

    st.markdown("")

    run_button = st.button(
        "▶ RUN BACKTEST",
        use_container_width=True,
        key="run_backtest"
    )

    if not run_button:

        return

    # ========================================================
    # EXECUTE
    # ========================================================

    try:

        # ----------------------------------------------------
        # SINGLE TRADE
        # ----------------------------------------------------

        if mode == "SINGLE TRADE":

            output = run_single_backtest(
                expiry=expiry,
                trade_date=selected_date,
                entry_time=entry_time,
                exit_time=exit_time,
                legs=legs,
            )

            results = output.get(
                "results"
            )

            metrics = output.get(
                "metrics",
                {}
            )

            trade = output.get(
                "trade"
            )

        # ----------------------------------------------------
        # MULTI TRADE
        # ----------------------------------------------------

        else:

            output = run_multi_trade_backtest(
                snapshots=snapshots,
                legs=legs,
                entry_step=int(
                    entry_step
                ),
                holding_steps=int(
                    holding_steps
                ),
            )

            results = output.get(
                "results"
            )

            metrics = output.get(
                "metrics",
                {}
            )

            trade = None

        # ====================================================
        # RESULT CHECK
        # ====================================================

        if not metrics:

            st.warning(
                "Backtest completed, but no valid "
                "trade results were generated."
            )

            return

        # ====================================================
        # SUCCESS
        # ====================================================

        st.success(
            "Backtest completed successfully."
        )

        # ====================================================
        # PERFORMANCE
        # ========================================================

        st.markdown(
            '<div class="section-title">PERFORMANCE</div>',
            unsafe_allow_html=True
        )

        display_metrics(
            metrics
        )

        # ====================================================
        # RESULTS
        # ========================================================

        display_results(
            results,
            trade=trade
        )

    except Exception as e:

        st.error(
            f"Backtest failed: {e}"
        )