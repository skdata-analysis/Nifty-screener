import numpy as np
import pandas as pd


# ============================================================
# NIFTY CANDLESTICK PATTERN ENGINE
# ============================================================

def _safe_float(value):
    try:
        if pd.isna(value):
            return np.nan
        return float(value)
    except Exception:
        return np.nan


def _body(df):
    return (df["close"] - df["open"]).abs()


def _range(df):
    return df["high"] - df["low"]


def _upper_wick(df):
    return df["high"] - df[["open", "close"]].max(axis=1)


def _lower_wick(df):
    return df[["open", "close"]].min(axis=1) - df["low"]


def _bullish(df):
    return df["close"] > df["open"]


def _bearish(df):
    return df["close"] < df["open"]


# ============================================================
# INDIVIDUAL PATTERNS
# ============================================================

def detect_doji(df):
    """
    Doji:
    Open and close are very close relative to candle range.
    """

    candle_range = _range(df)
    body = _body(df)

    return (
        candle_range > 0
    ) & (
        body <= candle_range * 0.10
    )


def detect_hammer(df):
    """
    Hammer:
    Small body near upper part of candle
    with long lower wick.
    """

    body = _body(df)
    candle_range = _range(df)
    lower = _lower_wick(df)
    upper = _upper_wick(df)

    return (
        (candle_range > 0)
        & (lower >= body * 2)
        & (upper <= body * 0.75)
        & (body <= candle_range * 0.40)
    )


def detect_shooting_star(df):
    """
    Shooting Star:
    Small body with long upper wick.
    """

    body = _body(df)
    candle_range = _range(df)
    lower = _lower_wick(df)
    upper = _upper_wick(df)

    return (
        (candle_range > 0)
        & (upper >= body * 2)
        & (lower <= body * 0.75)
        & (body <= candle_range * 0.40)
    )


def detect_bullish_engulfing(df):
    """
    Bullish Engulfing:
    Current candle bullish and body engulfs
    previous bearish body.
    """

    if len(df) == 0:
        return pd.Series(dtype=bool)

    previous_open = df["open"].shift(1)
    previous_close = df["close"].shift(1)

    previous_bearish = previous_close < previous_open
    current_bullish = df["close"] > df["open"]

    current_body_low = df[["open", "close"]].min(axis=1)
    current_body_high = df[["open", "close"]].max(axis=1)

    previous_body_low = pd.concat(
        [previous_open, previous_close],
        axis=1
    ).min(axis=1)

    previous_body_high = pd.concat(
        [previous_open, previous_close],
        axis=1
    ).max(axis=1)

    return (
        previous_bearish
        & current_bullish
        & (current_body_low <= previous_body_low)
        & (current_body_high >= previous_body_high)
    )


def detect_bearish_engulfing(df):
    """
    Bearish Engulfing:
    Current candle bearish and body engulfs
    previous bullish body.
    """

    if len(df) == 0:
        return pd.Series(dtype=bool)

    previous_open = df["open"].shift(1)
    previous_close = df["close"].shift(1)

    previous_bullish = previous_close > previous_open
    current_bearish = df["close"] < df["open"]

    current_body_low = df[["open", "close"]].min(axis=1)
    current_body_high = df[["open", "close"]].max(axis=1)

    previous_body_low = pd.concat(
        [previous_open, previous_close],
        axis=1
    ).min(axis=1)

    previous_body_high = pd.concat(
        [previous_open, previous_close],
        axis=1
    ).max(axis=1)

    return (
        previous_bullish
        & current_bearish
        & (current_body_low <= previous_body_low)
        & (current_body_high >= previous_body_high)
    )


def detect_inside_bar(df):
    """
    Inside Bar:
    Current candle remains completely inside
    previous candle.
    """

    previous_high = df["high"].shift(1)
    previous_low = df["low"].shift(1)

    return (
        (df["high"] <= previous_high)
        & (df["low"] >= previous_low)
    )


def detect_bullish_breakout(df):
    """
    Breakout:
    Current close breaks previous candle high.
    """

    previous_high = df["high"].shift(1)

    return df["close"] > previous_high


def detect_bearish_breakdown(df):
    """
    Breakdown:
    Current close breaks previous candle low.
    """

    previous_low = df["low"].shift(1)

    return df["close"] < previous_low


# ============================================================
# MORNING / EVENING STAR
# ============================================================

def detect_morning_star(df):

    if len(df) < 3:
        return pd.Series(False, index=df.index)

    c1_open = df["open"].shift(2)
    c1_close = df["close"].shift(2)

    c2_open = df["open"].shift(1)
    c2_close = df["close"].shift(1)

    c3_open = df["open"]
    c3_close = df["close"]

    c1_body = (c1_close - c1_open).abs()
    c2_body = (c2_close - c2_open).abs()

    c1_bearish = c1_close < c1_open
    c3_bullish = c3_close > c3_open

    c3_midpoint = (c1_open + c1_close) / 2

    return (
        c1_bearish
        & (c2_body < c1_body * 0.5)
        & c3_bullish
        & (c3_close > c3_midpoint)
    )


def detect_evening_star(df):

    if len(df) < 3:
        return pd.Series(False, index=df.index)

    c1_open = df["open"].shift(2)
    c1_close = df["close"].shift(2)

    c2_open = df["open"].shift(1)
    c2_close = df["close"].shift(1)

    c3_open = df["open"]
    c3_close = df["close"]

    c1_body = (c1_close - c1_open).abs()
    c2_body = (c2_close - c2_open).abs()

    c1_bullish = c1_close > c1_open
    c3_bearish = c3_close < c3_open

    c3_midpoint = (c1_open + c1_close) / 2

    return (
        c1_bullish
        & (c2_body < c1_body * 0.5)
        & c3_bearish
        & (c3_close < c3_midpoint)
    )


# ============================================================
# PATTERN NAME
# ============================================================

def get_primary_pattern(row):
    """
    Assign one primary pattern.
    Priority is given to stronger reversal patterns.
    """

    bullish_patterns = [
        "BULLISH ENGULFING",
        "MORNING STAR",
        "HAMMER"
    ]

    bearish_patterns = [
        "BEARISH ENGULFING",
        "EVENING STAR",
        "SHOOTING STAR"
    ]

    for pattern in bullish_patterns:
        if bool(row.get(pattern, False)):
            return pattern

    for pattern in bearish_patterns:
        if bool(row.get(pattern, False)):
            return pattern

    if bool(row.get("INSIDE BAR", False)):
        return "INSIDE BAR"

    if bool(row.get("DOJI", False)):
        return "DOJI"

    if bool(row.get("BULLISH BREAKOUT", False)):
        return "BULLISH BREAKOUT"

    if bool(row.get("BEARISH BREAKDOWN", False)):
        return "BEARISH BREAKDOWN"

    return "NONE"


# ============================================================
# MAIN ENGINE
# ============================================================

def run_pattern_engine(df):

    if df is None or df.empty:
        return {
            "data": pd.DataFrame(),
            "latest_pattern": "NO DATA",
            "pattern_bias": "NEUTRAL",
            "pattern_score": 0
        }

    required_columns = [
        "open",
        "high",
        "low",
        "close"
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing candle columns: "
            + ", ".join(missing)
        )

    data = df.copy()

    # --------------------------------------------------------
    # NUMERIC CLEANUP
    # --------------------------------------------------------

    for column in required_columns:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    data = data.dropna(
        subset=required_columns
    ).reset_index(
        drop=True
    )

    if data.empty:
        return {
            "data": data,
            "latest_pattern": "NO DATA",
            "pattern_bias": "NEUTRAL",
            "pattern_score": 0
        }

    # --------------------------------------------------------
    # PATTERNS
    # --------------------------------------------------------

    data["DOJI"] = detect_doji(data)

    data["HAMMER"] = detect_hammer(data)

    data["SHOOTING STAR"] = detect_shooting_star(data)

    data["BULLISH ENGULFING"] = (
        detect_bullish_engulfing(data)
    )

    data["BEARISH ENGULFING"] = (
        detect_bearish_engulfing(data)
    )

    data["INSIDE BAR"] = (
        detect_inside_bar(data)
    )

    data["MORNING STAR"] = (
        detect_morning_star(data)
    )

    data["EVENING STAR"] = (
        detect_evening_star(data)
    )

    data["BULLISH BREAKOUT"] = (
        detect_bullish_breakout(data)
    )

    data["BEARISH BREAKDOWN"] = (
        detect_bearish_breakdown(data)
    )

    # --------------------------------------------------------
    # PRIMARY PATTERN
    # --------------------------------------------------------

    data["PRIMARY_PATTERN"] = data.apply(
        get_primary_pattern,
        axis=1
    )

    # --------------------------------------------------------
    # PATTERN SCORE
    # --------------------------------------------------------

    data["PATTERN_SCORE"] = 0

    # Strong bullish patterns
    data.loc[
        data["BULLISH ENGULFING"],
        "PATTERN_SCORE"
    ] += 3

    data.loc[
        data["MORNING STAR"],
        "PATTERN_SCORE"
    ] += 3

    data.loc[
        data["HAMMER"],
        "PATTERN_SCORE"
    ] += 2

    data.loc[
        data["BULLISH BREAKOUT"],
        "PATTERN_SCORE"
    ] += 2

    # Strong bearish patterns
    data.loc[
        data["BEARISH ENGULFING"],
        "PATTERN_SCORE"
    ] -= 3

    data.loc[
        data["EVENING STAR"],
        "PATTERN_SCORE"
    ] -= 3

    data.loc[
        data["SHOOTING STAR"],
        "PATTERN_SCORE"
    ] -= 2

    data.loc[
        data["BEARISH BREAKDOWN"],
        "PATTERN_SCORE"
    ] -= 2

    # --------------------------------------------------------
    # PATTERN BIAS
    # --------------------------------------------------------

    data["PATTERN_BIAS"] = np.select(
        [
            data["PATTERN_SCORE"] >= 2,
            data["PATTERN_SCORE"] <= -2
        ],
        [
            "BULLISH",
            "BEARISH"
        ],
        default="NEUTRAL"
    )

    # --------------------------------------------------------
    # LATEST VALUES
    # --------------------------------------------------------

    latest = data.iloc[-1]

    latest_pattern = latest[
        "PRIMARY_PATTERN"
    ]

    latest_bias = latest[
        "PATTERN_BIAS"
    ]

    latest_score = int(
        latest[
            "PATTERN_SCORE"
        ]
    )

    return {
        "data": data,
        "latest_pattern": latest_pattern,
        "pattern_bias": latest_bias,
        "pattern_score": latest_score
    }


# ============================================================
# QUICK TEST
# ============================================================

if __name__ == "__main__":

    test_data = pd.DataFrame(
        {
            "open": [
                100,
                98,
                97,
                96,
                98
            ],
            "high": [
                102,
                100,
                99,
                101,
                103
            ],
            "low": [
                98,
                96,
                95,
                94,
                97
            ],
            "close": [
                99,
                97,
                96,
                100,
                102
            ]
        }
    )

    result = run_pattern_engine(
        test_data
    )

    print(
        result["data"][
            [
                "PRIMARY_PATTERN",
                "PATTERN_SCORE",
                "PATTERN_BIAS"
            ]
        ]
    )

    print(
        "Latest Pattern:",
        result["latest_pattern"]
    )

    print(
        "Pattern Bias:",
        result["pattern_bias"]
    )

    print(
        "Pattern Score:",
        result["pattern_score"]
    )