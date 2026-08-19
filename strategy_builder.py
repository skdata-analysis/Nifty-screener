import pandas as pd


STRATEGIES = [
    "LONG STRADDLE",
    "SHORT STRADDLE",
    "LONG STRANGLE",
    "SHORT STRANGLE",
    "BULL CALL SPREAD",
    "BEAR PUT SPREAD",
    "IRON CONDOR",
]


def get_atm_strike(df):
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

    spot = float(spot_values.iloc[0])

    return float(
        min(
            strikes,
            key=lambda x: abs(float(x) - spot)
        )
    )


def build_strategy_legs(
    strategy,
    selections,
    quantity
):
    """
    Build normalized strategy legs.

    Every leg contains:

        strike
        option_type
        action
        quantity
    """

    quantity = int(quantity)

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    strategy = strategy.upper().strip()

    # --------------------------------------------------------
    # STRADDLE
    # --------------------------------------------------------

    if strategy in [
        "LONG STRADDLE",
        "SHORT STRADDLE",
    ]:

        strike = float(
            selections["strike"]
        )

        action = (
            "BUY"
            if strategy == "LONG STRADDLE"
            else "SELL"
        )

        return [
            {
                "strike": strike,
                "option_type": "CE",
                "action": action,
                "quantity": quantity,
            },
            {
                "strike": strike,
                "option_type": "PE",
                "action": action,
                "quantity": quantity,
            },
        ]

    # --------------------------------------------------------
    # STRANGLE
    # --------------------------------------------------------

    if strategy in [
        "LONG STRANGLE",
        "SHORT STRANGLE",
    ]:

        put_strike = float(
            selections["put_strike"]
        )

        call_strike = float(
            selections["call_strike"]
        )

        action = (
            "BUY"
            if strategy == "LONG STRANGLE"
            else "SELL"
        )

        return [
            {
                "strike": put_strike,
                "option_type": "PE",
                "action": action,
                "quantity": quantity,
            },
            {
                "strike": call_strike,
                "option_type": "CE",
                "action": action,
                "quantity": quantity,
            },
        ]

    # --------------------------------------------------------
    # BULL CALL SPREAD
    # --------------------------------------------------------

    if strategy == "BULL CALL SPREAD":

        buy_strike = float(
            selections["buy_strike"]
        )

        sell_strike = float(
            selections["sell_strike"]
        )

        return [
            {
                "strike": buy_strike,
                "option_type": "CE",
                "action": "BUY",
                "quantity": quantity,
            },
            {
                "strike": sell_strike,
                "option_type": "CE",
                "action": "SELL",
                "quantity": quantity,
            },
        ]

    # --------------------------------------------------------
    # BEAR PUT SPREAD
    # --------------------------------------------------------

    if strategy == "BEAR PUT SPREAD":

        buy_strike = float(
            selections["buy_strike"]
        )

        sell_strike = float(
            selections["sell_strike"]
        )

        return [
            {
                "strike": buy_strike,
                "option_type": "PE",
                "action": "BUY",
                "quantity": quantity,
            },
            {
                "strike": sell_strike,
                "option_type": "PE",
                "action": "SELL",
                "quantity": quantity,
            },
        ]

    # --------------------------------------------------------
    # IRON CONDOR
    # --------------------------------------------------------

    if strategy == "IRON CONDOR":

        put_buy_strike = float(
            selections["put_buy_strike"]
        )

        put_sell_strike = float(
            selections["put_sell_strike"]
        )

        call_sell_strike = float(
            selections["call_sell_strike"]
        )

        call_buy_strike = float(
            selections["call_buy_strike"]
        )

        return [
            {
                "strike": put_buy_strike,
                "option_type": "PE",
                "action": "BUY",
                "quantity": quantity,
            },
            {
                "strike": put_sell_strike,
                "option_type": "PE",
                "action": "SELL",
                "quantity": quantity,
            },
            {
                "strike": call_sell_strike,
                "option_type": "CE",
                "action": "SELL",
                "quantity": quantity,
            },
            {
                "strike": call_buy_strike,
                "option_type": "CE",
                "action": "BUY",
                "quantity": quantity,
            },
        ]

    raise ValueError(
        f"Unsupported strategy: {strategy}"
    )