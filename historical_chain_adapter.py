import pandas as pd
import numpy as np


def safe_float(value):

    try:

        if value is None or pd.isna(value):
            return np.nan

        return float(value)

    except Exception:

        return np.nan


def convert_historical_snapshot(df):
    """
    Convert historical option rows into the same
    CE/PE structure expected by backtest_engine.py.

    Input:

        timestamp
        strike
        option_type
        open
        high
        low
        close
        volume
        open_interest

    Output:

        strike
        ce_ltp
        pe_ltp
        ce_volume
        pe_volume
        ce_oi
        pe_oi
    """

    if df is None or df.empty:

        return pd.DataFrame()

    data = df.copy()

    # --------------------------------------------------------
    # CLEAN COLUMN NAMES
    # --------------------------------------------------------

    data.columns = [
        str(col).strip().lower()
        for col in data.columns
    ]

    # --------------------------------------------------------
    # STRIKE
    # --------------------------------------------------------

    data["strike"] = pd.to_numeric(
        data["strike"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # OPTION TYPE
    # --------------------------------------------------------

    data["option_type"] = (
        data["option_type"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    data["close"] = pd.to_numeric(
        data["close"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # VOLUME
    # --------------------------------------------------------

    if "volume" in data.columns:

        data["volume"] = pd.to_numeric(
            data["volume"],
            errors="coerce"
        )

    else:

        data["volume"] = np.nan

    # --------------------------------------------------------
    # OPEN INTEREST
    # --------------------------------------------------------

    if "open_interest" in data.columns:

        data["open_interest"] = pd.to_numeric(
            data["open_interest"],
            errors="coerce"
        )

    else:

        data["open_interest"] = np.nan

    # --------------------------------------------------------
    # CALLS
    # --------------------------------------------------------

    ce = data[
        data["option_type"] == "CE"
    ].copy()

    ce = ce[
        [
            "strike",
            "close",
            "volume",
            "open_interest"
        ]
    ]

    ce = ce.rename(
        columns={
            "close": "ce_ltp",
            "volume": "ce_volume",
            "open_interest": "ce_oi"
        }
    )

    # --------------------------------------------------------
    # PUTS
    # --------------------------------------------------------

    pe = data[
        data["option_type"] == "PE"
    ].copy()

    pe = pe[
        [
            "strike",
            "close",
            "volume",
            "open_interest"
        ]
    ]

    pe = pe.rename(
        columns={
            "close": "pe_ltp",
            "volume": "pe_volume",
            "open_interest": "pe_oi"
        }
    )

    # --------------------------------------------------------
    # MERGE CE + PE
    # --------------------------------------------------------

    result = pd.merge(
        ce,
        pe,
        on="strike",
        how="outer"
    )

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    result = result.sort_values(
        "strike"
    )

    result = result.reset_index(
        drop=True
    )

    return result
