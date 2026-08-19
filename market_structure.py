import pandas as pd


# ============================================================
# MARKET STRUCTURE ENGINE
# ============================================================

def calculate_market_structure(df):

    if df is None or df.empty:
        return {}

    data = df.copy()

    # --------------------------------------------------------
    # SPOT
    # --------------------------------------------------------

    spot = data["spot_price"].dropna().iloc[0]

    # --------------------------------------------------------
    # ATM
    # --------------------------------------------------------

    atm_index = (
        data["strike"] - spot
    ).abs().idxmin()

    atm_strike = data.loc[
        atm_index,
        "strike"
    ]

    # --------------------------------------------------------
    # MAX CE OI
    # --------------------------------------------------------

    max_ce_oi_idx = data[
        "ce_oi"
    ].idxmax()

    max_ce_oi_strike = data.loc[
        max_ce_oi_idx,
        "strike"
    ]

    max_ce_oi = data.loc[
        max_ce_oi_idx,
        "ce_oi"
    ]

    # --------------------------------------------------------
    # MAX PE OI
    # --------------------------------------------------------

    max_pe_oi_idx = data[
        "pe_oi"
    ].idxmax()

    max_pe_oi_strike = data.loc[
        max_pe_oi_idx,
        "strike"
    ]

    max_pe_oi = data.loc[
        max_pe_oi_idx,
        "pe_oi"
    ]

    # --------------------------------------------------------
    # MAX CE OI CHANGE
    # --------------------------------------------------------

    max_ce_change_idx = data[
        "ce_oi_change"
    ].idxmax()

    max_ce_change_strike = data.loc[
        max_ce_change_idx,
        "strike"
    ]

    max_ce_oi_change = data.loc[
        max_ce_change_idx,
        "ce_oi_change"
    ]

    # --------------------------------------------------------
    # MAX PE OI CHANGE
    # --------------------------------------------------------

    max_pe_change_idx = data[
        "pe_oi_change"
    ].idxmax()

    max_pe_change_strike = data.loc[
        max_pe_change_idx,
        "strike"
    ]

    max_pe_oi_change = data.loc[
        max_pe_change_idx,
        "pe_oi_change"
    ]

    # --------------------------------------------------------
    # TOTAL OI
    # --------------------------------------------------------

    total_ce_oi = (
        data["ce_oi"]
        .fillna(0)
        .sum()
    )

    total_pe_oi = (
        data["pe_oi"]
        .fillna(0)
        .sum()
    )

    # --------------------------------------------------------
    # PCR
    # --------------------------------------------------------

    if total_ce_oi != 0:

        overall_pcr = (
            total_pe_oi
            / total_ce_oi
        )

    else:

        overall_pcr = None

    # --------------------------------------------------------
    # OI IMBALANCE
    # --------------------------------------------------------

    total_oi = (
        total_ce_oi
        + total_pe_oi
    )

    if total_oi != 0:

        oi_imbalance = (
            total_pe_oi
            - total_ce_oi
        ) / total_oi

    else:

        oi_imbalance = 0

    # --------------------------------------------------------
    # MARKET BIAS
    # --------------------------------------------------------

    if overall_pcr is None:

        bias = "NEUTRAL"

    elif overall_pcr > 1.10:

        bias = "BULLISH"

    elif overall_pcr < 0.90:

        bias = "BEARISH"

    else:

        bias = "NEUTRAL"

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {

        "spot": spot,

        "atm_strike": atm_strike,

        "max_ce_oi_strike":
            max_ce_oi_strike,

        "max_ce_oi":
            max_ce_oi,

        "max_pe_oi_strike":
            max_pe_oi_strike,

        "max_pe_oi":
            max_pe_oi,

        "max_ce_change_strike":
            max_ce_change_strike,

        "max_ce_oi_change":
            max_ce_oi_change,

        "max_pe_change_strike":
            max_pe_change_strike,

        "max_pe_oi_change":
            max_pe_oi_change,

        "total_ce_oi":
            total_ce_oi,

        "total_pe_oi":
            total_pe_oi,

        "overall_pcr":
            overall_pcr,

        "oi_imbalance":
            oi_imbalance,

        "bias":
            bias,
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    import os

    BASE_DIR = os.path.dirname(
        os.path.abspath(__file__)
    )

    CSV_PATH = os.path.join(
        BASE_DIR,
        "data",
        "nifty_option_chain.csv"
    )

    df = pd.read_csv(
        CSV_PATH
    )

    result = calculate_market_structure(
        df
    )

    print()
    print("==============================")
    print("MARKET STRUCTURE")
    print("==============================")

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )
        