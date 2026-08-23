import numpy as np
import pandas as pd


# ============================================================
# VALIDATION
# ============================================================

def validate_ohlcv(df):

    required = [
        "open",
        "high",
        "low",
        "close"
    ]

    missing = [
        col for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing OHLC columns: {missing}"
        )

    return True


# ============================================================
# CANDLE FEATURES
# ============================================================

def add_candle_features(df):

    data = df.copy()

    validate_ohlcv(data)

    data["body"] = (
        data["close"] - data["open"]
    ).abs()

    data["range"] = (
        data["high"] - data["low"]
    )

    data["upper_wick"] = (
        data["high"]
        - data[["open", "close"]].max(axis=1)
    )

    data["lower_wick"] = (
        data[["open", "close"]].min(axis=1)
        - data["low"]
    )

    data["bullish_candle"] = (
        data["close"] > data["open"]
    )

    data["bearish_candle"] = (
        data["close"] < data["open"]
    )

    data["body_ratio"] = np.where(
        data["range"] > 0,
        data["body"] / data["range"],
        0
    )

    return data


# ============================================================
# CANDLE PATTERN ENGINE
# ============================================================

def detect_candle_patterns(df):

    data = add_candle_features(df)

    data["pattern"] = ""

    # --------------------------------------------------------
    # HAMMER
    # --------------------------------------------------------

    hammer = (
        (data["lower_wick"] >= data["body"] * 2)
        &
        (data["upper_wick"] <= data["body"] * 0.5)
        &
        (data["body_ratio"] <= 0.45)
    )

    data.loc[
        hammer,
        "pattern"
    ] = "HAMMER"

    # --------------------------------------------------------
    # SHOOTING STAR
    # --------------------------------------------------------

    shooting_star = (
        (data["upper_wick"] >= data["body"] * 2)
        &
        (data["lower_wick"] <= data["body"] * 0.5)
        &
        (data["body_ratio"] <= 0.45)
    )

    data.loc[
        shooting_star,
        "pattern"
    ] = "SHOOTING STAR"

    # --------------------------------------------------------
    # DOJI
    # --------------------------------------------------------

    doji = (
        data["body_ratio"] <= 0.10
    )

    data.loc[
        doji,
        "pattern"
    ] = "DOJI"

    # --------------------------------------------------------
    # PREVIOUS CANDLE
    # --------------------------------------------------------

    previous_open = data["open"].shift(1)
    previous_close = data["close"].shift(1)

    # --------------------------------------------------------
    # BULLISH ENGULFING
    # --------------------------------------------------------

    bullish_engulfing = (
        (previous_close < previous_open)
        &
        (data["close"] > data["open"])
        &
        (data["open"] <= previous_close)
        &
        (data["close"] >= previous_open)
    )

    data.loc[
        bullish_engulfing,
        "pattern"
    ] = "BULLISH ENGULFING"

    # --------------------------------------------------------
    # BEARISH ENGULFING
    # --------------------------------------------------------

    bearish_engulfing = (
        (previous_close > previous_open)
        &
        (data["close"] < data["open"])
        &
        (data["open"] >= previous_close)
        &
        (data["close"] <= previous_open)
    )

    data.loc[
        bearish_engulfing,
        "pattern"
    ] = "BEARISH ENGULFING"

    return data


# ============================================================
# VOLUME ENGINE
# ============================================================

def analyze_volume(
    df,
    period=20
):

    data = df.copy()

    if "volume" not in data.columns:

        data["volume_ma"] = np.nan
        data["volume_ratio"] = np.nan
        data["volume_signal"] = "NO VOLUME DATA"

        return data

    data["volume"] = pd.to_numeric(
        data["volume"],
        errors="coerce"
    )

    data["volume_ma"] = (
        data["volume"]
        .rolling(period)
        .mean()
    )

    data["volume_ratio"] = np.where(
        data["volume_ma"] > 0,
        data["volume"] / data["volume_ma"],
        np.nan
    )

    data["volume_signal"] = np.select(
        [
            data["volume_ratio"] >= 2.0,
            data["volume_ratio"] >= 1.5,
            data["volume_ratio"] >= 1.2
        ],
        [
            "EXTREME VOLUME",
            "HIGH VOLUME",
            "ABOVE AVERAGE"
        ],
        default="NORMAL"
    )

    return data


# ============================================================
# SWING DETECTION
# ============================================================

def detect_swings(
    df,
    window=3
):

    data = df.copy()

    data["swing_high"] = False
    data["swing_low"] = False

    if len(data) < (
        window * 2 + 1
    ):
        return data

    for i in range(
        window,
        len(data) - window
    ):

        current_high = data[
            "high"
        ].iloc[i]

        current_low = data[
            "low"
        ].iloc[i]

        left_highs = data[
            "high"
        ].iloc[
            i - window:i
        ]

        right_highs = data[
            "high"
        ].iloc[
            i + 1:i + window + 1
        ]

        left_lows = data[
            "low"
        ].iloc[
            i - window:i
        ]

        right_lows = data[
            "low"
        ].iloc[
            i + 1:i + window + 1
        ]

        if (
            current_high >= left_highs.max()
            and
            current_high >= right_highs.max()
        ):

            data.loc[
                data.index[i],
                "swing_high"
            ] = True

        if (
            current_low <= left_lows.min()
            and
            current_low <= right_lows.min()
        ):

            data.loc[
                data.index[i],
                "swing_low"
            ] = True

    return data


# ============================================================
# SUPPORT / RESISTANCE
# ============================================================

def calculate_support_resistance(
    df,
    lookback=50
):

    if df.empty:

        return {
            "support": np.nan,
            "resistance": np.nan
        }

    data = df.tail(
        lookback
    ).copy()

    swings = detect_swings(
        data,
        window=3
    )

    swing_highs = swings.loc[
        swings["swing_high"],
        "high"
    ]

    swing_lows = swings.loc[
        swings["swing_low"],
        "low"
    ]

    if not swing_highs.empty:

        resistance = float(
            swing_highs.iloc[-1]
        )

    else:

        resistance = float(
            data["high"].max()
        )

    if not swing_lows.empty:

        support = float(
            swing_lows.iloc[-1]
        )

    else:

        support = float(
            data["low"].min()
        )

    return {
        "support": support,
        "resistance": resistance
    }


# ============================================================
# TREND ENGINE
# ============================================================

def determine_trend(df):

    if df.empty:
        return "UNKNOWN"

    latest = df.iloc[-1]

    close = latest["close"]

    ema9 = latest.get(
        "ema_9",
        np.nan
    )

    ema20 = latest.get(
        "ema_20",
        np.nan
    )

    ema50 = latest.get(
        "ema_50",
        np.nan
    )

    if (
        pd.notna(ema9)
        and
        pd.notna(ema20)
        and
        pd.notna(ema50)
    ):

        if (
            close > ema9
            and
            ema9 > ema20
            and
            ema20 > ema50
        ):
            return "STRONG BULLISH"

        if (
            close < ema9
            and
            ema9 < ema20
            and
            ema20 < ema50
        ):
            return "STRONG BEARISH"

        if close > ema20:
            return "BULLISH"

        if close < ema20:
            return "BEARISH"

    return "NEUTRAL"


# ============================================================
# BREAKOUT / BREAKDOWN
# ============================================================

def detect_breakout(
    df,
    support,
    resistance,
    buffer=0.001
):

    if df.empty:
        return "NONE"

    latest = df.iloc[-1]

    close = float(
        latest["close"]
    )

    high = float(
        latest["high"]
    )

    low = float(
        latest["low"]
    )

    if pd.notna(resistance):

        resistance_level = (
            resistance
            * (1 + buffer)
        )

        if (
            close > resistance_level
            or
            high > resistance_level
        ):

            return "BULLISH BREAKOUT"

    if pd.notna(support):

        support_level = (
            support
            * (1 - buffer)
        )

        if (
            close < support_level
            or
            low < support_level
        ):

            return "BEARISH BREAKDOWN"

    return "NONE"


# ============================================================
# MASTER EVENT ENGINE
# ============================================================

def detect_price_action_event(
    df,
    support,
    resistance
):

    if df.empty:
        return "NO DATA"

    latest = df.iloc[-1]

    pattern = str(
        latest.get(
            "pattern",
            ""
        )
    )

    volume_signal = str(
        latest.get(
            "volume_signal",
            "NORMAL"
        )
    )

    breakout = detect_breakout(
        df,
        support,
        resistance
    )

    # --------------------------------------------------------
    # BREAKOUT + VOLUME
    # --------------------------------------------------------

    if breakout == "BULLISH BREAKOUT":

        if volume_signal in [
            "HIGH VOLUME",
            "EXTREME VOLUME"
        ]:

            return "BULLISH BREAKOUT + VOLUME"

        return "BULLISH BREAKOUT"

    if breakout == "BEARISH BREAKDOWN":

        if volume_signal in [
            "HIGH VOLUME",
            "EXTREME VOLUME"
        ]:

            return "BEARISH BREAKDOWN + VOLUME"

        return "BEARISH BREAKDOWN"

    # --------------------------------------------------------
    # REVERSAL PATTERNS
    # --------------------------------------------------------

    if pattern == "BULLISH ENGULFING":

        return "BULLISH ENGULFING"

    if pattern == "BEARISH ENGULFING":

        return "BEARISH ENGULFING"

    if pattern == "HAMMER":

        return "HAMMER REVERSAL"

    if pattern == "SHOOTING STAR":

        return "SHOOTING STAR REVERSAL"

    return "NO MAJOR EVENT"


# ============================================================
# MASTER ENGINE
# ============================================================

def run_price_action_engine(
    df
):

    if df.empty:

        return {
            "data": df,
            "trend": "UNKNOWN",
            "event": "NO DATA",
            "support": np.nan,
            "resistance": np.nan,
            "volume_signal": "NO DATA"
        }

    data = df.copy()

    # Candle patterns
    data = detect_candle_patterns(
        data
    )

    # Volume
    data = analyze_volume(
        data
    )

    # Swings
    data = detect_swings(
        data
    )

    # Levels
    levels = calculate_support_resistance(
        data
    )

    support = levels[
        "support"
    ]

    resistance = levels[
        "resistance"
    ]

    # Trend
    trend = determine_trend(
        data
    )

    # Event
    event = detect_price_action_event(
        data,
        support,
        resistance
    )

    latest_volume = str(
        data.iloc[-1].get(
            "volume_signal",
            "NO DATA"
        )
    )

    return {
        "data": data,
        "trend": trend,
        "event": event,
        "support": support,
        "resistance": resistance,
        "volume_signal": latest_volume
    }