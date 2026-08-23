import pandas as pd
import numpy as np

from data_store import get_history


# ============================================================
# LOAD HISTORICAL DATA
# ============================================================

def load_history(
    expiry=None,
    strike=None
):
    """
    Load historical option-chain snapshots
    from SQLite database.
    """

    df = get_history(
        expiry=expiry,
        strike=strike
    )

    if df.empty:
        return df

    df["fetch_time"] = pd.to_datetime(
        df["fetch_time"],
        errors="coerce"
    )

    df["strike"] = pd.to_numeric(
        df["strike"],
        errors="coerce"
    )

    df = df.sort_values(
        ["fetch_time", "strike"]
    ).reset_index(drop=True)

    return df


# ============================================================
# SNAPSHOT SUMMARY
# ============================================================

def get_snapshot_summary(
    expiry=None
):
    """
    Return one row per historical snapshot.
    """

    df = load_history(
        expiry=expiry
    )

    if df.empty:
        return pd.DataFrame()

    summary = (
        df.groupby(
            "fetch_time",
            as_index=False
        )
        .agg(
            spot_price=(
                "spot_price",
                "first"
            ),
            pcr=(
                "pcr",
                "mean"
            ),
            total_ce_oi=(
                "ce_oi",
                "sum"
            ),
            total_pe_oi=(
                "pe_oi",
                "sum"
            ),
            total_ce_volume=(
                "ce_volume",
                "sum"
            ),
            total_pe_volume=(
                "pe_volume",
                "sum"
            )
        )
    )

    summary["oi_pcr"] = np.where(
        summary["total_ce_oi"] != 0,
        summary["total_pe_oi"]
        / summary["total_ce_oi"],
        np.nan
    )

    summary["spot_change"] = (
        summary["spot_price"].diff()
    )

    summary["spot_change_pct"] = (
        summary["spot_price"]
        .pct_change()
        * 100
    )

    summary["ce_oi_change"] = (
        summary["total_ce_oi"].diff()
    )

    summary["pe_oi_change"] = (
        summary["total_pe_oi"].diff()
    )

    return summary


# ============================================================
# STRIKE HISTORY
# ============================================================

def get_strike_history(
    strike,
    expiry=None
):
    """
    Historical movement for one strike.
    """

    df = load_history(
        expiry=expiry,
        strike=strike
    )

    if df.empty:
        return df

    columns = [
        "fetch_time",
        "expiry",
        "strike",
        "spot_price",

        "ce_ltp",
        "ce_volume",
        "ce_oi",
        "ce_prev_oi",
        "ce_oi_change",
        "ce_iv",
        "ce_delta",
        "ce_gamma",
        "ce_theta",
        "ce_vega",
        "ce_pop",

        "pe_ltp",
        "pe_volume",
        "pe_oi",
        "pe_prev_oi",
        "pe_oi_change",
        "pe_iv",
        "pe_delta",
        "pe_gamma",
        "pe_theta",
        "pe_vega",
        "pe_pop"
    ]

    available = [
        col
        for col in columns
        if col in df.columns
    ]

    result = df[
        available
    ].copy()

    result = result.sort_values(
        "fetch_time"
    )

    return result


# ============================================================
# GREEK HISTORY
# ============================================================

def get_greek_history(
    strike,
    option_type="CE",
    expiry=None
):
    """
    Return historical Greeks for a strike.
    """

    df = get_strike_history(
        strike=strike,
        expiry=expiry
    )

    if df.empty:
        return df

    option_type = option_type.upper()

    if option_type not in ["CE", "PE"]:
        raise ValueError(
            "option_type must be CE or PE"
        )

    prefix = option_type.lower()

    columns = [
        "fetch_time",
        "strike",
        f"{prefix}_iv",
        f"{prefix}_delta",
        f"{prefix}_gamma",
        f"{prefix}_theta",
        f"{prefix}_vega",
        f"{prefix}_pop"
    ]

    available = [
        col
        for col in columns
        if col in df.columns
    ]

    return df[
        available
    ].copy()


# ============================================================
# OPTION PRICE HISTORY
# ============================================================

def get_price_history(
    strike,
    expiry=None
):
    """
    Historical CE/PE price movement.
    """

    df = get_strike_history(
        strike=strike,
        expiry=expiry
    )

    if df.empty:
        return df

    result = df[
        [
            "fetch_time",
            "spot_price",
            "ce_ltp",
            "pe_ltp"
        ]
    ].copy()

    result["ce_change"] = (
        result["ce_ltp"].diff()
    )

    result["pe_change"] = (
        result["pe_ltp"].diff()
    )

    result["ce_change_pct"] = (
        result["ce_ltp"]
        .pct_change()
        * 100
    )

    result["pe_change_pct"] = (
        result["pe_ltp"]
        .pct_change()
        * 100
    )

    return result


# ============================================================
# OI HISTORY
# ============================================================

def get_oi_history(
    strike,
    expiry=None
):
    """
    Historical CE/PE OI and OI change.
    """

    df = get_strike_history(
        strike=strike,
        expiry=expiry
    )

    if df.empty:
        return df

    result = df[
        [
            "fetch_time",
            "spot_price",
            "ce_oi",
            "ce_oi_change",
            "pe_oi",
            "pe_oi_change"
        ]
    ].copy()

    result["ce_oi_delta"] = (
        result["ce_oi"].diff()
    )

    result["pe_oi_delta"] = (
        result["pe_oi"].diff()
    )

    return result


# ============================================================
# ATM STRIKE
# ============================================================

def get_atm_strike(
    expiry=None
):
    """
    Determine the latest ATM strike from
    the historical database.
    """

    df = load_history(
        expiry=expiry
    )

    if df.empty:
        return None

    latest_time = df[
        "fetch_time"
    ].max()

    latest = df[
        df["fetch_time"] == latest_time
    ].copy()

    if latest.empty:
        return None

    spot = latest[
        "spot_price"
    ].dropna()

    if spot.empty:
        return None

    spot_price = float(
        spot.iloc[0]
    )

    strikes = (
        latest["strike"]
        .dropna()
        .unique()
    )

    if len(strikes) == 0:
        return None

    return float(
        min(
            strikes,
            key=lambda x:
                abs(x - spot_price)
        )
    )


# ============================================================
# ATM HISTORY
# ============================================================

def get_atm_history(
    expiry=None
):
    """
    Historical ATM option data.
    """

    df = load_history(
        expiry=expiry
    )

    if df.empty:
        return df

    rows = []

    for fetch_time, group in df.groupby(
        "fetch_time"
    ):

        group = group.dropna(
            subset=[
                "spot_price",
                "strike"
            ]
        )

        if group.empty:
            continue

        spot = float(
            group["spot_price"].iloc[0]
        )

        atm_idx = (
            (group["strike"] - spot)
            .abs()
            .idxmin()
        )

        row = group.loc[
            atm_idx
        ].copy()

        rows.append(row)

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(
        rows
    )

    return result.sort_values(
        "fetch_time"
    ).reset_index(drop=True)


# ============================================================
# OI BUILDUP CLASSIFICATION
# ============================================================

def classify_oi_buildup(
    price_change,
    oi_change
):
    """
    Basic price + OI interpretation.

    Price ↑ + OI ↑ = Long buildup
    Price ↓ + OI ↑ = Short buildup
    Price ↑ + OI ↓ = Short covering
    Price ↓ + OI ↓ = Long unwinding
    """

    if pd.isna(price_change) or pd.isna(
        oi_change
    ):
        return "N/A"

    if price_change > 0 and oi_change > 0:
        return "LONG BUILDUP"

    if price_change < 0 and oi_change > 0:
        return "SHORT BUILDUP"

    if price_change > 0 and oi_change < 0:
        return "SHORT COVERING"

    if price_change < 0 and oi_change < 0:
        return "LONG UNWINDING"

    return "NEUTRAL"


# ============================================================
# STRIKE OI ANALYSIS
# ============================================================

def get_oi_buildup_analysis(
    strike,
    expiry=None
):
    """
    Combine price movement, OI movement and
    buildup classification.
    """

    price = get_price_history(
        strike=strike,
        expiry=expiry
    )

    oi = get_oi_history(
        strike=strike,
        expiry=expiry
    )

    if price.empty or oi.empty:
        return pd.DataFrame()

    result = price[
        [
            "fetch_time",
            "spot_price",
            "ce_ltp",
            "pe_ltp"
        ]
    ].copy()

    result["ce_oi"] = oi[
        "ce_oi"
    ].values

    result["pe_oi"] = oi[
        "pe_oi"
    ].values

    result["ce_oi_change"] = oi[
        "ce_oi_delta"
    ].values

    result["pe_oi_change"] = oi[
        "pe_oi_delta"
    ].values

    result["ce_structure"] = [
        classify_oi_buildup(
            p,
            o
        )
        for p, o in zip(
            result["ce_ltp"].diff(),
            result["ce_oi_change"]
        )
    ]

    result["pe_structure"] = [
        classify_oi_buildup(
            p,
            o
        )
        for p, o in zip(
            result["pe_ltp"].diff(),
            result["pe_oi_change"]
        )
    ]

    return result


# ============================================================
# DATABASE HEALTH
# ============================================================

def get_data_health():

    df = load_history()

    if df.empty:
        return {
            "rows": 0,
            "snapshots": 0,
            "latest_fetch": None,
            "expiries": 0
        }

    return {
        "rows": len(df),
        "snapshots": df[
            "fetch_time"
        ].nunique(),

        "latest_fetch": df[
            "fetch_time"
        ].max(),

        "expiries": df[
            "expiry"
        ].nunique()
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n==============================")
    print("HISTORICAL ANALYTICS TEST")
    print("==============================")

    health = get_data_health()

    print("\nDatabase health:")
    print(health)

    df = load_history()

    print("\nHistorical rows:")
    print(len(df))

    print("\nHistorical columns:")
    print(len(df.columns))

    if not df.empty:

        expiry = df[
            "expiry"
        ].dropna().iloc[-1]

        print(
            "\nTesting expiry:",
            expiry
        )

        atm = get_atm_strike(
            expiry=expiry
        )

        print(
            "ATM strike:",
            atm
        )

        if atm is not None:

            greek = get_greek_history(
                strike=atm,
                option_type="CE",
                expiry=expiry
            )

            print(
                "\nCE Greek history:"
            )

            print(
                greek.tail(5).to_string(
                    index=False
                )
            )

            oi = get_oi_history(
                strike=atm,
                expiry=expiry
            )

            print(
                "\nOI history:"
            )

            print(
                oi.tail(5).to_string(
                    index=False
                )
            )

    print(
        "\nAnalytics engine test complete."
    )