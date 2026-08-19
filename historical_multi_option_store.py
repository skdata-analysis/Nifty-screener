import os
import pandas as pd

from expired_options import (
    get_expired_option_contracts,
    find_option_contract,
    get_expired_option_history
)


# ============================================================
# SETTINGS
# ============================================================

EXPIRY = "2026-08-11"

FROM_DATE = "2026-08-03"
TO_DATE = "2026-08-11"

INTERVAL = "5minute"


# Contracts required for our strategy
CONTRACTS = [
    {
        "strike": 21600,
        "option_type": "PE"
    },
    {
        "strike": 24400,
        "option_type": "CE"
    }
]


# ============================================================
# PATH
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
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("DOWNLOADING COMPLETE OPTION HISTORY")
    print("=" * 60)

    print("Expiry:", EXPIRY)
    print("From:", FROM_DATE)
    print("To:", TO_DATE)
    print("Interval:", INTERVAL)

    # --------------------------------------------------------
    # Get expired contracts
    # --------------------------------------------------------

    contracts = get_expired_option_contracts(
        expiry_date=EXPIRY
    )

    print()
    print("Contracts received:", len(contracts))

    # --------------------------------------------------------
    # Download each required contract
    # --------------------------------------------------------

    for contract_info in CONTRACTS:

        strike = contract_info["strike"]
        option_type = contract_info["option_type"]

        print()
        print("-" * 60)
        print(
            f"Downloading {strike} {option_type}"
        )
        print("-" * 60)

        contract = find_option_contract(
            contracts=contracts,
            strike_price=strike,
            option_type=option_type
        )

        if not contract:

            print(
                f"ERROR: Contract not found "
                f"{strike} {option_type}"
            )

            continue

        instrument_key = contract[
            "instrument_key"
        ]

        trading_symbol = contract[
            "trading_symbol"
        ]

        lot_size = contract[
            "lot_size"
        ]

        print("Instrument:", trading_symbol)
        print("Instrument Key:", instrument_key)
        print("Lot Size:", lot_size)

        # ----------------------------------------------------
        # Historical data
        # ----------------------------------------------------

        df = get_expired_option_history(
            instrument_key=instrument_key,
            from_date=FROM_DATE,
            to_date=TO_DATE,
            interval=INTERVAL
        )

        if df is None or df.empty:

            print(
                "WARNING: No historical data received."
            )

            continue

        # ----------------------------------------------------
        # Standard columns
        # ----------------------------------------------------

        df["expiry"] = EXPIRY
        df["strike"] = strike
        df["option_type"] = option_type
        df["instrument_key"] = instrument_key
        df["trading_symbol"] = trading_symbol
        df["lot_size"] = lot_size

        # ----------------------------------------------------
        # Sort
        # ----------------------------------------------------

        if "timestamp" in df.columns:

            df["timestamp"] = pd.to_datetime(
                df["timestamp"]
            )

            df = df.sort_values(
                "timestamp"
            )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        filename = (
            f"NIFTY_{EXPIRY}_"
            f"{strike}_"
            f"{option_type}_"
            f"{INTERVAL}.csv"
        )

        filepath = os.path.join(
            HISTORICAL_DIR,
            filename
        )

        df.to_csv(
            filepath,
            index=False
        )

        print()
        print("Saved:", filepath)
        print("Rows:", len(df))

    print()
    print("=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
    
    