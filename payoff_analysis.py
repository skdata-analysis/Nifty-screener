# ============================================================
# STRATEGY PAYOFF ANALYSIS
# ============================================================

import numpy as np
import pandas as pd


# ============================================================
# OPTION PAYOFF
# ============================================================

def option_payoff(
    spot,
    strike,
    option_type,
    action,
    premium,
):
    """
    Calculate expiry P&L for one option leg.
    """

    spot = np.asarray(
        spot,
        dtype=float
    )

    strike = float(strike)
    premium = float(premium)

    option_type = str(
        option_type
    ).upper()

    action = str(
        action
    ).upper()

    if option_type == "CE":

        intrinsic = np.maximum(
            spot - strike,
            0
        )

    elif option_type == "PE":

        intrinsic = np.maximum(
            strike - spot,
            0
        )

    else:

        raise ValueError(
            f"Invalid option type: {option_type}"
        )

    if action == "BUY":

        return intrinsic - premium

    if action == "SELL":

        return premium - intrinsic

    raise ValueError(
        f"Invalid action: {action}"
    )


# ============================================================
# STRATEGY PAYOFF
# ============================================================

def calculate_strategy_payoff(
    legs,
    spot_prices,
    multiplier=1,
):
    """
    Calculate total strategy expiry payoff.

    legs must contain:

        strike
        option_type
        action
        entry_premium
        quantity
    """

    spot_prices = np.asarray(
        spot_prices,
        dtype=float
    )

    total = np.zeros_like(
        spot_prices,
        dtype=float
    )

    for leg in legs:

        premium = leg.get(
            "entry_premium"
        )

        if premium is None:

            raise ValueError(
                "entry_premium missing "
                "from strategy leg."
            )

        quantity = int(
            leg.get(
                "quantity",
                1
            )
        )

        leg_pnl = option_payoff(
            spot=spot_prices,
            strike=float(
                leg["strike"]
            ),
            option_type=leg[
                "option_type"
            ],
            action=leg[
                "action"
            ],
            premium=float(
                premium
            ),
        )

        total += (
            leg_pnl
            * quantity
            * multiplier
        )

    return total


# ============================================================
# BREAKEVEN DETECTION
# ============================================================

def find_breakevens(
    spot_prices,
    pnl_values,
):
    """
    Find approximate breakeven points
    using sign changes.
    """

    spots = np.asarray(
        spot_prices,
        dtype=float
    )

    pnl = np.asarray(
        pnl_values,
        dtype=float
    )

    breakevens = []

    for i in range(
        len(spots) - 1
    ):

        p1 = pnl[i]
        p2 = pnl[i + 1]

        if p1 == 0:

            breakevens.append(
                spots[i]
            )

        elif p1 * p2 < 0:

            x1 = spots[i]
            x2 = spots[i + 1]

            # Linear interpolation
            x = (
                x1
                + (
                    -p1
                    / (p2 - p1)
                )
                * (x2 - x1)
            )

            breakevens.append(
                x
            )

    if len(pnl) > 0 and pnl[-1] == 0:

        breakevens.append(
            spots[-1]
        )

    # Remove near duplicates
    unique = []

    for value in breakevens:

        if not any(
            abs(value - x) < 0.01
            for x in unique
        ):

            unique.append(
                float(value)
            )

    return unique


# ============================================================
# PAYOFF SUMMARY
# ============================================================

def calculate_payoff_summary(
    spot_prices,
    pnl_values,
):
    """
    Return payoff statistics.
    """

    spots = np.asarray(
        spot_prices,
        dtype=float
    )

    pnl = np.asarray(
        pnl_values,
        dtype=float
    )

    if len(spots) == 0:

        return {
            "max_profit": 0,
            "max_loss": 0,
            "breakevens": [],
        }

    max_profit = float(
        np.max(pnl)
    )

    max_loss = float(
        np.min(pnl)
    )

    breakevens = find_breakevens(
        spots,
        pnl
    )

    return {
        "max_profit": max_profit,
        "max_loss": max_loss,
        "breakevens": breakevens,
    }


# ============================================================
# BUILD PAYOFF DATAFRAME
# ============================================================

def build_payoff_dataframe(
    legs,
    center_price,
    points=100,
    step=50,
):
    """
    Create NIFTY expiry payoff curve
    around the current/entry spot.
    """

    center_price = float(
        center_price
    )

    lower = max(
        1,
        center_price
        - points * step
    )

    upper = (
        center_price
        + points * step
    )

    spot_prices = np.arange(
        lower,
        upper + step,
        step
    )

    pnl = calculate_strategy_payoff(
        legs=legs,
        spot_prices=spot_prices,
    )

    df = pd.DataFrame(
        {
            "NIFTY": spot_prices,
            "P&L": pnl,
        }
    )

    return df


# ============================================================
# ENRICH LEGS WITH ENTRY PREMIUM
# ============================================================

def attach_entry_premiums(
    legs,
    snapshot_df,
):
    """
    Add entry_premium to normalized
    strategy legs using historical option-chain data.
    """

    if (
        snapshot_df is None
        or snapshot_df.empty
    ):

        raise ValueError(
            "Entry snapshot is empty."
        )

    if "strike" not in snapshot_df.columns:

        raise ValueError(
            "Strike column not found."
        )

    result = []

    for leg in legs:

        strike = float(
            leg["strike"]
        )

        option_type = str(
            leg["option_type"]
        ).upper()

        if option_type == "CE":

            premium_column = "ce_ltp"

        elif option_type == "PE":

            premium_column = "pe_ltp"

        else:

            raise ValueError(
                f"Invalid option type: {option_type}"
            )

        if premium_column not in snapshot_df.columns:

            raise ValueError(
                f"{premium_column} not found."
            )

        strikes = pd.to_numeric(
            snapshot_df["strike"],
            errors="coerce"
        )

        rows = snapshot_df[
            strikes == strike
        ]

        if rows.empty:

            raise ValueError(
                f"Strike {strike} not found."
            )

        premium = pd.to_numeric(
            rows[premium_column],
            errors="coerce"
        ).iloc[0]

        if pd.isna(premium):

            raise ValueError(
                f"Premium unavailable for "
                f"{option_type} {strike}."
            )

        new_leg = dict(
            leg
        )

        new_leg[
            "entry_premium"
        ] = float(premium)

        result.append(
            new_leg
        )

    return result