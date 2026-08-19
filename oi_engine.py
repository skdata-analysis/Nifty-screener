import pandas as pd


# ============================================================
# OI CLASSIFICATION
# ============================================================

def classify_oi(price_change, oi_change):

    if pd.isna(price_change) or pd.isna(oi_change):
        return "UNKNOWN"

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
# PREPARE OI DATA
# ============================================================

def prepare_oi_analysis(df):

    data = df.copy()

    # --------------------------------------------------------
    # CE PRICE CHANGE
    # --------------------------------------------------------

    if "ce_ltp" in data.columns:

        data["ce_price_change"] = (
            data["ce_ltp"]
            .diff()
        )

    else:

        data["ce_price_change"] = None


    # --------------------------------------------------------
    # PE PRICE CHANGE
    # --------------------------------------------------------

    if "pe_ltp" in data.columns:

        data["pe_price_change"] = (
            data["pe_ltp"]
            .diff()
        )

    else:

        data["pe_price_change"] = None


    # --------------------------------------------------------
    # CE OI SIGNAL
    # --------------------------------------------------------

    data["ce_oi_signal"] = data.apply(
        lambda row: classify_oi(
            row["ce_price_change"],
            row["ce_oi_change"]
        ),
        axis=1
    )


    # --------------------------------------------------------
    # PE OI SIGNAL
    # --------------------------------------------------------

    data["pe_oi_signal"] = data.apply(
        lambda row: classify_oi(
            row["pe_price_change"],
            row["pe_oi_change"]
        ),
        axis=1
    )


    return data


# ============================================================
# MAX OI
# ============================================================

def get_max_oi(df):

    result = {}

    if "ce_oi" in df.columns:

        ce_idx = df["ce_oi"].idxmax()

        result["max_ce_strike"] = (
            df.loc[ce_idx, "strike"]
        )

        result["max_ce_oi"] = (
            df.loc[ce_idx, "ce_oi"]
        )


    if "pe_oi" in df.columns:

        pe_idx = df["pe_oi"].idxmax()

        result["max_pe_strike"] = (
            df.loc[pe_idx, "strike"]
        )

        result["max_pe_oi"] = (
            df.loc[pe_idx, "pe_oi"]
        )


    return result


# ============================================================
# MAX OI CHANGE
# ============================================================

def get_max_oi_change(df):

    result = {}

    if "ce_oi_change" in df.columns:

        ce_idx = df["ce_oi_change"].idxmax()

        result["max_ce_change_strike"] = (
            df.loc[ce_idx, "strike"]
        )

        result["max_ce_oi_change"] = (
            df.loc[ce_idx, "ce_oi_change"]
        )


    if "pe_oi_change" in df.columns:

        pe_idx = df["pe_oi_change"].idxmax()

        result["max_pe_change_strike"] = (
            df.loc[pe_idx, "strike"]
        )

        result["max_pe_oi_change"] = (
            df.loc[pe_idx, "pe_oi_change"]
        )
    return result  
