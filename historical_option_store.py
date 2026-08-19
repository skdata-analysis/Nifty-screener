import os
import pandas as pd

from expired_options import (
    get_expired_option_contracts,
    find_option_contract,
    get_expired_option_history
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

HISTORICAL_DIR = os.path.join(
    BASE_DIR,
    "data",
    "historical",
    "options"
)

os.makedirs(
    HISTORICAL_DIR,
    exist_ok=True
)


# ============================================================
# SAVE HISTORICAL OPTION DATA
# ============================================================

def save_option_history(
    expiry_date,
    strike,
    option_type,
    from_date,
    to_date,
    interval="5minute"
):

    option_type = option_type.upper()

    print("\n========================================")
    print("HISTORICAL OPTION DATA")
    print("========================================")

    print("Expiry:", expiry_date)
    print("Strike:", strike)
    print("Option:", option_type)
    print("From:", from_date)
    print("To:", to_date)
    print("Interval:", interval)

    # --------------------------------------------------------
    # GET EXPIRED CONTRACTS
    # --------------------------------------------------------

    contracts = get_expired_option_contracts(
        expiry_date=expiry_date
    )

    print(
        "Contracts received:",
        len(contracts)
    )

    # --------------------------------------------------------
    # FIND CONTRACT
    # --------------------------------------------------------

    contract = find_option_contract(
        contracts=contracts,
        strike=strike,
        option_type=option_type
    )

    if contract is None:

        raise RuntimeError(
            f"Unable to find {option_type} "
            f"contract for strike {strike}"
        )

    instrument_key = contract[
        "instrument_key"
    ]

    print(
        "Instrument:",
        contract.get("trading_symbol")
    )

    print(
        "Instrument Key:",
        instrument_key
    )

    print(
        "Lot Size:",
        contract.get("lot_size")
    )

    # --------------------------------------------------------
    # DOWNLOAD HISTORY
    # --------------------------------------------------------

    df = get_expired_option_history(
        expired_instrument_key=instrument_key,
        interval=interval,
        from_date=from_date,
        to_date=to_date
    )

    if df.empty:

        raise RuntimeError(
            "No historical candles returned."
        )

    # --------------------------------------------------------
    # ADD CONTRACT INFORMATION
    # --------------------------------------------------------

    df["expiry"] = expiry_date
    df["strike"] = float(strike)
    df["option_type"] = option_type
    df["instrument_key"] = instrument_key
    df["trading_symbol"] = contract.get(
        "trading_symbol"
    )
    df["lot_size"] = contract.get(
        "lot_size"
    )

    # --------------------------------------------------------
    # FILE NAME
    # --------------------------------------------------------

    filename = (
        f"NIFTY_"
        f"{expiry_date}_"
        f"{int(strike)}_"
        f"{option_type}_"
        f"{interval}.csv"
    )

    filepath = os.path.join(
        HISTORICAL_DIR,
        filename
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    df.to_csv(
        filepath,
        index=False
    )

    print(
        "\nHistorical data saved:"
    )

    print(filepath)

    print(
        "Rows:",
        len(df)
    )

    print(
        "Columns:",
        list(df.columns)
    )

    return df


# ============================================================
# LOAD SAVED HISTORY
# ============================================================

def load_option_history(
    expiry_date,
    strike,
    option_type,
    interval="5minute"
):

    filename = (
        f"NIFTY_"
        f"{expiry_date}_"
        f"{int(strike)}_"
        f"{option_type.upper()}_"
        f"{interval}.csv"
    )

    filepath = os.path.join(
        HISTORICAL_DIR,
        filename
    )

    if not os.path.exists(filepath):

        return pd.DataFrame()

    return pd.read_csv(
        filepath,
        parse_dates=["timestamp"]
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n========================================"
    )

    print(
        "TESTING HISTORICAL OPTION STORAGE"
    )

    print(
        "========================================"
    )

    # --------------------------------------------------------
    # TEST PARAMETERS
    # --------------------------------------------------------

    expiry = "2026-08-11"

    strike = 21600

    option_type = "PE"

    from_date = "2026-08-03"

    to_date = "2026-08-11"

    interval = "5minute"

    # --------------------------------------------------------
    # DOWNLOAD + SAVE
    # --------------------------------------------------------

    df = save_option_history(

        expiry_date=expiry,

        strike=strike,

        option_type=option_type,

        from_date=from_date,

        to_date=to_date,

        interval=interval
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print(
        "\n========================================"
    )

    print(
        "SUCCESS"
    )

    print(
        "========================================"
    )

    print(
        df.head()
    )

    print(
        "\nLast rows:"
    )

    print(
        df.tail()
    )
    