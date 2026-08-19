import pandas as pd


# ============================================================
# STRATEGY LEG
# ============================================================

def create_leg(
    option_type,
    strike,
    premium,
    quantity=1,
    action="BUY"
):
    return {
        "option_type": option_type,
        "strike": float(strike),
        "premium": float(premium),
        "quantity": int(quantity),
        "action": action.upper()
    }


# ============================================================
# LEG PAYOFF
# ============================================================

def calculate_leg_payoff(
    leg,
    prices
):

    prices = pd.Series(prices)

    strike = leg["strike"]
    premium = leg["premium"]
    quantity = leg["quantity"]
    action = leg["action"]
    option_type = leg["option_type"]

    # --------------------------------------------
    # OPTION INTRINSIC VALUE
    # --------------------------------------------

    if option_type == "CE":

        intrinsic = (
            prices - strike
        ).clip(lower=0)

    elif option_type == "PE":

        intrinsic = (
            strike - prices
        ).clip(lower=0)

    else:

        raise ValueError(
            "option_type must be CE or PE"
        )

    # --------------------------------------------
    # BUY / SELL
    # --------------------------------------------

    if action == "BUY":

        payoff = (
            intrinsic - premium
        ) * quantity

    elif action == "SELL":

        payoff = (
            premium - intrinsic
        ) * quantity

    else:

        raise ValueError(
            "action must be BUY or SELL"
        )

    return payoff


# ============================================================
# STRATEGY PAYOFF
# ============================================================

def calculate_strategy_payoff(
    legs,
    price_range
):

    prices = pd.Series(
        price_range,
        name="underlying_price"
    )

    result = pd.DataFrame({
        "underlying_price": prices
    })

    result["strategy_pnl"] = 0.0

    for leg in legs:

        leg_payoff = calculate_leg_payoff(
            leg,
            prices
        )

        result["strategy_pnl"] += (
            leg_payoff.values
        )

    return result


# ============================================================
# STRADDLE
# ============================================================

def long_straddle(
    strike,
    ce_premium,
    pe_premium,
    quantity=1
):

    return [

        create_leg(
            "CE",
            strike,
            ce_premium,
            quantity,
            "BUY"
        ),

        create_leg(
            "PE",
            strike,
            pe_premium,
            quantity,
            "BUY"
        )
    ]


# ============================================================
# SHORT STRADDLE
# ============================================================

def short_straddle(
    strike,
    ce_premium,
    pe_premium,
    quantity=1
):

    return [

        create_leg(
            "CE",
            strike,
            ce_premium,
            quantity,
            "SELL"
        ),

        create_leg(
            "PE",
            strike,
            pe_premium,
            quantity,
            "SELL"
        )
    ]


# ============================================================
# LONG STRANGLE
# ============================================================

def long_strangle(
    ce_strike,
    pe_strike,
    ce_premium,
    pe_premium,
    quantity=1
):

    return [

        create_leg(
            "CE",
            ce_strike,
            ce_premium,
            quantity,
            "BUY"
        ),

        create_leg(
            "PE",
            pe_strike,
            pe_premium,
            quantity,
            "BUY"
        )
    ]


# ============================================================
# SHORT STRANGLE
# ============================================================

def short_strangle(
    ce_strike,
    pe_strike,
    ce_premium,
    pe_premium,
    quantity=1
):

    return [

        create_leg(
            "CE",
            ce_strike,
            ce_premium,
            quantity,
            "SELL"
        ),

        create_leg(
            "PE",
            pe_strike,
            pe_premium,
            quantity,
            "SELL"
        )
    ]


# ============================================================
# BULL CALL SPREAD
# ============================================================

def bull_call_spread(
    buy_strike,
    sell_strike,
    buy_premium,
    sell_premium,
    quantity=1
):

    return [

        create_leg(
            "CE",
            buy_strike,
            buy_premium,
            quantity,
            "BUY"
        ),

        create_leg(
            "CE",
            sell_strike,
            sell_premium,
            quantity,
            "SELL"
        )
    ]


# ============================================================
# BEAR PUT SPREAD
# ============================================================

def bear_put_spread(
    buy_strike,
    sell_strike,
    buy_premium,
    sell_premium,
    quantity=1
):

    return [

        create_leg(
            "PE",
            buy_strike,
            buy_premium,
            quantity,
            "BUY"
        ),

        create_leg(
            "PE",
            sell_strike,
            sell_premium,
            quantity,
            "SELL"
        )
    ]


# ============================================================
# IRON CONDOR
# ============================================================

def iron_condor(
    put_buy_strike,
    put_sell_strike,
    call_sell_strike,
    call_buy_strike,
    put_buy_premium,
    put_sell_premium,
    call_sell_premium,
    call_buy_premium,
    quantity=1
):

    return [

        create_leg(
            "PE",
            put_buy_strike,
            put_buy_premium,
            quantity,
            "BUY"
        ),

        create_leg(
            "PE",
            put_sell_strike,
            put_sell_premium,
            quantity,
            "SELL"
        ),

        create_leg(
            "CE",
            call_sell_strike,
            call_sell_premium,
            quantity,
            "SELL"
        ),

        create_leg(
            "CE",
            call_buy_strike,
            call_buy_premium,
            quantity,
            "BUY"
        )
    ]
    