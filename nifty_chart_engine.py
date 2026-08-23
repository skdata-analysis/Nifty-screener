import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from historcial_data import get_historical_candles, NIFTY_INSTRUMENT_KEY


# ============================================================
# NIFTY CHART DATA
# ============================================================

# ============================================================
# NIFTY CHART DATA
# ============================================================

def load_nifty_candles(interval="5m", days=5):

    # --------------------------------------------------------
    # STANDARD TIMEFRAME MAP
    # --------------------------------------------------------

    interval_map = {
        "1m":  ("minutes", 1),
        "3m":  ("minutes", 3),
        "5m":  ("minutes", 5),
        "15m": ("minutes", 15),
        "30m": ("minutes", 30),
        "1H":  ("hours", 1),
        "1D":  ("days", 1),

        # Backward compatibility
        "1minute":  ("minutes", 1),
        "5minute":  ("minutes", 5),
        "15minute": ("minutes", 15),
        "30minute": ("minutes", 30),
        "60minute": ("hours", 1),
    }

    if interval not in interval_map:

        raise ValueError(
            "Unsupported interval. "
            "Use 1m, 3m, 5m, 15m, 30m, 1H or 1D."
        )

    unit, interval_value = interval_map[interval]

    # --------------------------------------------------------
    # DATE RANGE
    # --------------------------------------------------------

    today = datetime.now().date()

    df = get_historical_candles(

        instrument_key=NIFTY_INSTRUMENT_KEY,

        unit=unit,

        interval=interval_value,

        to_date=today.strftime("%Y-%m-%d"),

        from_date=(
            today - timedelta(days=days)
        ).strftime("%Y-%m-%d")
    )

    # --------------------------------------------------------
    # EMPTY DATA
    # --------------------------------------------------------

    if df is None or df.empty:

        return pd.DataFrame()

    # --------------------------------------------------------
    # COPY
    # --------------------------------------------------------

    df = df.copy()

    # --------------------------------------------------------
    # TIMESTAMP
    # --------------------------------------------------------

    if "timestamp" in df.columns:

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

    # --------------------------------------------------------
    # NUMERIC COLUMNS
    # --------------------------------------------------------

    for col in [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "oi"
    ]:

        if col in df.columns:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    # --------------------------------------------------------
    # REQUIRED COLUMNS
    # --------------------------------------------------------

    required = [
        "timestamp",
        "open",
        "high",
        "low",
        "close"
    ]

    df = df.dropna(
        subset=[
            c for c in required
            if c in df.columns
        ]
    )

    # --------------------------------------------------------
    # SORT + REMOVE DUPLICATES
    # --------------------------------------------------------

    df = (
        df
        .sort_values("timestamp")
        .drop_duplicates(
            "timestamp"
        )
        .reset_index(drop=True)
    )

    return df

# ============================================================
# BASIC PRICE FEATURES
# ============================================================

def add_price_features(df):
    if df.empty:
        return df
    df = df.copy()
    df["change"] = df["close"].diff()
    df["change_pct"] = df["close"].pct_change() * 100
    df["candle_range"] = df["high"] - df["low"]
    df["body"] = df["close"] - df["open"]
    df["body_abs"] = df["body"].abs()
    df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)
    df["lower_wick"] = df[["open", "close"]].min(axis=1) - df["low"]
    df["body_pct"] = np.where(df["candle_range"] > 0, df["body_abs"] / df["candle_range"] * 100, 0)
    df["bullish_candle"] = df["close"] > df["open"]
    df["bearish_candle"] = df["close"] < df["open"]
    return df


# ============================================================
# INDICATORS
# ============================================================

def add_moving_averages(df, periods=(9, 20, 50, 200)):
    if df.empty:
        return df
    df = df.copy()
    for period in periods:
        df[f"ema_{period}"] = df["close"].ewm(span=period, adjust=False).mean()
    return df


def add_atr(df, period=14):
    if df.empty:
        return df
    df = df.copy()
    prev = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev).abs(),
        (df["low"] - prev).abs()
    ], axis=1).max(axis=1)
    df["true_range"] = tr
    df["atr"] = tr.rolling(period).mean()
    return df


def add_rsi(df, period=14):
    if df.empty:
        return df
    df = df.copy()
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))
    df.loc[(loss == 0) & (gain > 0), "rsi"] = 100
    return df


def add_macd(df, fast=12, slow=26, signal=9):
    if df.empty:
        return df
    df = df.copy()
    fast_ema = df["close"].ewm(span=fast, adjust=False).mean()
    slow_ema = df["close"].ewm(span=slow, adjust=False).mean()
    df["macd"] = fast_ema - slow_ema
    df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    return df


def add_bollinger_bands(df, period=20, std_dev=2.0):
    if df.empty:
        return df
    df = df.copy()
    mid = df["close"].rolling(period).mean()
    std = df["close"].rolling(period).std()
    df["bb_middle"] = mid
    df["bb_upper"] = mid + std_dev * std
    df["bb_lower"] = mid - std_dev * std
    df["bb_width"] = np.where(mid != 0, (df["bb_upper"] - df["bb_lower"]) / mid * 100, np.nan)
    return df


def add_vwap(df):
    """
    Calculate VWAP when meaningful volume is available.

    NIFTY INDEX historical candles may return zero volume.
    In that case VWAP is not statistically meaningful, so
    return NaN instead of generating a misleading value.
    """

    if df.empty:
        return df

    df = df.copy()

    if "volume" not in df.columns:
        df["vwap"] = np.nan
        return df

    volume = pd.to_numeric(
        df["volume"],
        errors="coerce"
    ).fillna(0)

    # --------------------------------------------------------
    # NIFTY INDEX DATA CHECK
    # --------------------------------------------------------

    if volume.sum() <= 0:
        df["vwap"] = np.nan
        return df

    typical_price = (
        df["high"]
        + df["low"]
        + df["close"]
    ) / 3

    cumulative_volume = volume.cumsum()

    cumulative_pv = (
        typical_price * volume
    ).cumsum()

    df["vwap"] = np.where(
        cumulative_volume > 0,
        cumulative_pv / cumulative_volume,
        np.nan
    )

    return df
# ============================================================
# SUPERTREND
# ============================================================

def add_supertrend(df, period=10, multiplier=3.0):

    if df.empty:
        return df

    df = df.copy()

    high = pd.to_numeric(df["high"], errors="coerce")
    low = pd.to_numeric(df["low"], errors="coerce")
    close = pd.to_numeric(df["close"], errors="coerce")

    # --------------------------------------------------------
    # TRUE RANGE
    # --------------------------------------------------------

    previous_close = close.shift(1)

    tr = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    # --------------------------------------------------------
    # ATR
    # --------------------------------------------------------

    atr = tr.rolling(
        window=period,
        min_periods=period,
    ).mean()

    # --------------------------------------------------------
    # BASIC BANDS
    # --------------------------------------------------------

    hl2 = (high + low) / 2

    basic_upper = (
        hl2 + multiplier * atr
    )

    basic_lower = (
        hl2 - multiplier * atr
    )

    # --------------------------------------------------------
    # FINAL BANDS
    # --------------------------------------------------------

    final_upper = pd.Series(
        np.nan,
        index=df.index,
        dtype=float,
    )

    final_lower = pd.Series(
        np.nan,
        index=df.index,
        dtype=float,
    )

    for i in range(len(df)):

        if pd.isna(atr.iloc[i]):
            continue

        if i == 0:

            final_upper.iloc[i] = (
                basic_upper.iloc[i]
            )

            final_lower.iloc[i] = (
                basic_lower.iloc[i]
            )

            continue

        previous_upper = final_upper.iloc[i - 1]
        previous_lower = final_lower.iloc[i - 1]

        if (
            pd.isna(previous_upper)
            or
            basic_upper.iloc[i]
            < previous_upper
            or
            close.iloc[i - 1]
            > previous_upper
        ):

            final_upper.iloc[i] = (
                basic_upper.iloc[i]
            )

        else:

            final_upper.iloc[i] = (
                previous_upper
            )

        if (
            pd.isna(previous_lower)
            or
            basic_lower.iloc[i]
            > previous_lower
            or
            close.iloc[i - 1]
            < previous_lower
        ):

            final_lower.iloc[i] = (
                basic_lower.iloc[i]
            )

        else:

            final_lower.iloc[i] = (
                previous_lower
            )

    # --------------------------------------------------------
    # SUPERTREND
    # --------------------------------------------------------

    supertrend = pd.Series(
        np.nan,
        index=df.index,
        dtype=float,
    )

    direction = pd.Series(
        0,
        index=df.index,
        dtype=int,
    )

    for i in range(len(df)):

        if pd.isna(atr.iloc[i]):
            continue

        # First valid Supertrend candle
        if i == 0 or pd.isna(supertrend.iloc[i - 1]):

            if close.iloc[i] <= final_upper.iloc[i]:

                supertrend.iloc[i] = (
                    final_upper.iloc[i]
                )

                direction.iloc[i] = -1

            else:

                supertrend.iloc[i] = (
                    final_lower.iloc[i]
                )

                direction.iloc[i] = 1

            continue

        previous_st = supertrend.iloc[i - 1]

        previous_direction = (
            direction.iloc[i - 1]
        )

        # ----------------------------------------------------
        # Previous trend bullish
        # ----------------------------------------------------

        if previous_direction == 1:

            if close.iloc[i] < final_lower.iloc[i]:

                supertrend.iloc[i] = (
                    final_upper.iloc[i]
                )

                direction.iloc[i] = -1

            else:

                supertrend.iloc[i] = (
                    final_lower.iloc[i]
                )

                direction.iloc[i] = 1

        # ----------------------------------------------------
        # Previous trend bearish
        # ----------------------------------------------------

        else:

            if close.iloc[i] > final_upper.iloc[i]:

                supertrend.iloc[i] = (
                    final_lower.iloc[i]
                )

                direction.iloc[i] = 1

            else:

                supertrend.iloc[i] = (
                    final_upper.iloc[i]
                )

                direction.iloc[i] = -1

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    df["supertrend"] = supertrend

    df["supertrend_direction"] = direction

    df["supertrend_signal"] = np.select(
        [
            direction == 1,
            direction == -1,
        ],
        [
            "BULLISH",
            "BEARISH",
        ],
        default="NEUTRAL",
    )

    return df


# ============================================================
# ADX + DIRECTIONAL INDEX
# ============================================================

def add_adx(df, period=14):

    if df.empty:
        return df

    df = df.copy()

    high = df["high"]
    low = df["low"]
    close = df["close"]

    previous_high = high.shift(1)
    previous_low = low.shift(1)
    previous_close = close.shift(1)

    # --------------------------------------------------------
    # TRUE RANGE
    # --------------------------------------------------------

    tr = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs()
        ],
        axis=1
    ).max(axis=1)

    # --------------------------------------------------------
    # DIRECTIONAL MOVEMENT
    # --------------------------------------------------------

    up_move = high - previous_high
    down_move = previous_low - low

    plus_dm = np.where(
        (up_move > down_move) &
        (up_move > 0),
        up_move,
        0
    )

    minus_dm = np.where(
        (down_move > up_move) &
        (down_move > 0),
        down_move,
        0
    )

    plus_dm = pd.Series(
        plus_dm,
        index=df.index
    )

    minus_dm = pd.Series(
        minus_dm,
        index=df.index
    )

    # --------------------------------------------------------
    # SMOOTHED VALUES
    # --------------------------------------------------------

    atr = tr.rolling(
        period
    ).mean()

    plus_dm_smoothed = plus_dm.rolling(
        period
    ).mean()

    minus_dm_smoothed = minus_dm.rolling(
        period
    ).mean()

    plus_di = (
        100
        * plus_dm_smoothed
        / atr.replace(0, np.nan)
    )

    minus_di = (
        100
        * minus_dm_smoothed
        / atr.replace(0, np.nan)
    )

    dx = (
        100
        * (plus_di - minus_di).abs()
        / (plus_di + minus_di).replace(
            0,
            np.nan
        )
    )

    adx = dx.rolling(
        period
    ).mean()

    df["plus_di"] = plus_di
    df["minus_di"] = minus_di
    df["adx"] = adx

    # --------------------------------------------------------
    # TREND STRENGTH
    # --------------------------------------------------------

    df["adx_strength"] = np.select(
        [
            adx >= 40,
            adx >= 25,
            adx >= 20
        ],
        [
            "VERY STRONG",
            "STRONG",
            "DEVELOPING"
        ],
        default="WEAK"
    )

    # --------------------------------------------------------
    # DIRECTION
    # --------------------------------------------------------

    df["adx_direction"] = np.select(
        [
            plus_di > minus_di,
            minus_di > plus_di
        ],
        [
            "BULLISH",
            "BEARISH"
        ],
        default="NEUTRAL"
    )

    return df
# ============================================================
# MARKET STRUCTURE
# ============================================================

def add_market_structure(df, lookback=5):
    if df.empty:
        return df
    df = df.copy()
    rh = df["high"].rolling(lookback).max().shift(1)
    rl = df["low"].rolling(lookback).min().shift(1)
    df["structure_high"] = rh
    df["structure_low"] = rl
    df["breakout"] = df["close"] > rh
    df["breakdown"] = df["close"] < rl
    df["higher_high"] = df["high"] > df["high"].shift(1)
    df["higher_low"] = df["low"] > df["low"].shift(1)
    df["lower_high"] = df["high"] < df["high"].shift(1)
    df["lower_low"] = df["low"] < df["low"].shift(1)
    return df


# ============================================================
# REVERSAL PATTERNS
# ============================================================

def add_reversal_patterns(df):
    if df.empty:
        return df
    df = df.copy()
    po, pc = df["open"].shift(1), df["close"].shift(1)
    prev_bull = pc > po
    prev_bear = pc < po

    df["doji"] = (df["candle_range"] > 0) & (df["body_pct"] <= 10)
    df["hammer"] = (
        (df["candle_range"] > 0) &
        (df["lower_wick"] >= df["body_abs"] * 2) &
        (df["upper_wick"] <= df["body_abs"]) &
        (df["body_pct"] <= 45)
    )
    df["shooting_star"] = (
        (df["candle_range"] > 0) &
        (df["upper_wick"] >= df["body_abs"] * 2) &
        (df["lower_wick"] <= df["body_abs"]) &
        (df["body_pct"] <= 45)
    )
    df["bullish_engulfing"] = prev_bear & df["bullish_candle"] & (df["open"] <= pc) & (df["close"] >= po)
    df["bearish_engulfing"] = prev_bull & df["bearish_candle"] & (df["open"] >= pc) & (df["close"] <= po)

    c1o, c1c = df["open"].shift(2), df["close"].shift(2)
    c2o, c2c = df["open"].shift(1), df["close"].shift(1)
    c1body = (c1c - c1o).abs()
    c2body = (c2c - c2o).abs()
    c2small = c2body <= c1body.replace(0, np.nan) * 0.5

    df["morning_star"] = (
        (c1c < c1o) & c2small & df["bullish_candle"] &
        (df["close"] > (c1o + c1c) / 2)
    )
    df["evening_star"] = (
        (c1c > c1o) & c2small & df["bearish_candle"] &
        (df["close"] < (c1o + c1c) / 2)
    )

    df["double_bottom"] = False
    df["double_top"] = False
    tolerance = 0.0025
    prior_low = df["low"].shift(5).rolling(5).min()
    prior_high = df["high"].shift(5).rolling(5).max()
    df.loc[df["low"].notna(), "double_bottom"] = (
        (df["low"] - prior_low).abs() / prior_low.replace(0, np.nan) <= tolerance
    ).fillna(False)
    df.loc[df["high"].notna(), "double_top"] = (
        (df["high"] - prior_high).abs() / prior_high.replace(0, np.nan) <= tolerance
    ).fillna(False)

    df["reversal_pattern"] = ""
    for mask, label in [
        (df["bullish_engulfing"], "BULLISH ENGULFING"),
        (df["bearish_engulfing"], "BEARISH ENGULFING"),
        (df["morning_star"], "MORNING STAR"),
        (df["evening_star"], "EVENING STAR"),
        (df["hammer"], "HAMMER"),
        (df["shooting_star"], "SHOOTING STAR"),
        (df["double_bottom"], "DOUBLE BOTTOM"),
        (df["double_top"], "DOUBLE TOP")
    ]:
        df.loc[mask & (df["reversal_pattern"] == ""), "reversal_pattern"] = label

    return df


# ============================================================
# CONTINUATION PATTERNS
# ============================================================

def add_continuation_patterns(df, lookback=5):
    if df.empty:
        return df
    df = df.copy()
    prior_high = df["high"].rolling(lookback).max().shift(1)
    prior_low = df["low"].rolling(lookback).min().shift(1)
    inside = (df["high"] < df["high"].shift(1)) & (df["low"] > df["low"].shift(1))
    df["inside_bar"] = inside
    df["bullish_continuation"] = inside & df["bullish_candle"] & (df["close"] > prior_high)
    df["bearish_continuation"] = inside & df["bearish_candle"] & (df["close"] < prior_low)
    df["continuation_pattern"] = ""
    df.loc[df["bullish_continuation"], "continuation_pattern"] = "BULLISH INSIDE-BAR BREAKOUT"
    df.loc[df["bearish_continuation"], "continuation_pattern"] = "BEARISH INSIDE-BAR BREAKDOWN"
    return df


# ============================================================
# PRICE ACTION EVENTS
# ============================================================

def add_price_action_events(df, breakout_lookback=20):
    if df.empty:
        return df
    df = df.copy()
    resistance = df["high"].rolling(breakout_lookback).max().shift(1)
    support = df["low"].rolling(breakout_lookback).min().shift(1)
    df["resistance_level"] = resistance
    df["support_level"] = support
    df["resistance_breakout"] = df["close"] > resistance
    df["support_breakdown"] = df["close"] < support

    if "volume" in df.columns:
        vma = df["volume"].rolling(20).mean()
        df["volume_spike"] = df["volume"] > (vma * 1.5)
    else:
        df["volume_spike"] = False

    df["ema20_bull_cross"] = (
        (df["close"] > df["ema_20"]) &
        (df["close"].shift(1) <= df["ema_20"].shift(1))
    ) if "ema_20" in df.columns else False
    df["ema20_bear_cross"] = (
        (df["close"] < df["ema_20"]) &
        (df["close"].shift(1) >= df["ema_20"].shift(1))
    ) if "ema_20" in df.columns else False

    df["vwap_bull_cross"] = (
        (df["close"] > df["vwap"]) &
        (df["close"].shift(1) <= df["vwap"].shift(1))
    ) if "vwap" in df.columns else False
    df["vwap_bear_cross"] = (
        (df["close"] < df["vwap"]) &
        (df["close"].shift(1) >= df["vwap"].shift(1))
    ) if "vwap" in df.columns else False

    df["price_action_event"] = ""
    rules = [
        (df["resistance_breakout"], "RESISTANCE BREAKOUT"),
        (df["support_breakdown"], "SUPPORT BREAKDOWN"),
        (df["bullish_continuation"], "BULLISH CONTINUATION"),
        (df["bearish_continuation"], "BEARISH CONTINUATION"),
        (df["ema20_bull_cross"], "EMA20 BULLISH CROSS"),
        (df["ema20_bear_cross"], "EMA20 BEARISH CROSS"),
        (df["vwap_bull_cross"], "VWAP BULLISH CROSS"),
        (df["vwap_bear_cross"], "VWAP BEARISH CROSS"),
        (df["volume_spike"], "VOLUME SPIKE")
    ]
    for mask, label in rules:
        df.loc[mask & (df["price_action_event"] == ""), "price_action_event"] = label

    reversal_mask = df["reversal_pattern"].astype(str).str.len() > 0
    df.loc[reversal_mask, "price_action_event"] = df.loc[reversal_mask, "reversal_pattern"]
    return df


# ============================================================
# MULTI-FACTOR SCORE
# ============================================================




# ============================================================
# LATEST SUMMARY
# ============================================================

def get_latest_chart_signal(df):
    if df is None or df.empty:
        return {"price": None, "change_pct": None, "signal": "NO DATA", "score": 0, "event": "NO MAJOR EVENT", "reversal": "", "continuation": ""}
    row = df.iloc[-1]
    return {
        "price": row.get("close"),
        "change_pct": row.get("change_pct"),
        "signal": row.get("signal", "NEUTRAL"),
        "score": row.get("signal_score", 0),
        "event": row.get("price_action_event", "") or "NO MAJOR EVENT",
        "reversal": row.get("reversal_pattern", ""),
        "continuation": row.get("continuation_pattern", "")
    }


# ============================================================
# COMPLETE CHART DATASET
# ============================================================
# ============================================================
# MULTI-FACTOR SIGNAL SCORE
# ============================================================

def add_signal_score(df):

    if df.empty:
        return df

    df = df.copy()

    # --------------------------------------------------------
    # SCORE INITIALIZATION
    # --------------------------------------------------------

    score = pd.Series(
        0.0,
        index=df.index
    )

    # ========================================================
    # 1. EMA TREND ALIGNMENT
    # ========================================================

    for col in ["ema_9", "ema_20", "ema_50"]:

        if col in df.columns:

            score += np.where(
                df["close"] > df[col],
                1,
                np.where(
                    df["close"] < df[col],
                    -1,
                    0
                )
            )

    # --------------------------------------------------------
    # EMA 9 vs EMA 20 confirmation
    # --------------------------------------------------------

    if "ema_9" in df.columns and "ema_20" in df.columns:

        score += np.where(
            df["ema_9"] > df["ema_20"],
            1,
            np.where(
                df["ema_9"] < df["ema_20"],
                -1,
                0
            )
        )

    # ========================================================
    # 2. RSI
    # ========================================================

    if "rsi" in df.columns:

        score += np.where(
            df["rsi"] >= 60,
            2,
            np.where(
                df["rsi"] >= 55,
                1,
                np.where(
                    df["rsi"] <= 40,
                    -2,
                    np.where(
                        df["rsi"] <= 45,
                        -1,
                        0
                    )
                )
            )
        )

    # ========================================================
    # 3. MACD
    # ========================================================

    if "macd_hist" in df.columns:

        score += np.where(
            df["macd_hist"] > 0,
            1,
            np.where(
                df["macd_hist"] < 0,
                -1,
                0
            )
        )

    # ========================================================
    # 4. VWAP
    # ========================================================

    if "vwap" in df.columns:

        valid_vwap = df["vwap"].notna()

        score += np.where(
            valid_vwap & (df["close"] > df["vwap"]),
            1,
            np.where(
                valid_vwap & (df["close"] < df["vwap"]),
                -1,
                0
            )
        )

    # ========================================================
    # 5. SUPERTREND
    # ========================================================

    if "supertrend_direction" in df.columns:

        score += np.where(
            df["supertrend_direction"] == 1,
            2,
            np.where(
                df["supertrend_direction"] == -1,
                -2,
                0
            )
        )

    # ========================================================
    # 6. ADX TREND STRENGTH + DIRECTION
    # ========================================================

    if "adx" in df.columns:

        # Strong trend
        score += np.where(
            df["adx"] >= 25,
            np.where(
                df.get(
                    "plus_di",
                    pd.Series(np.nan, index=df.index)
                )
                >
                df.get(
                    "minus_di",
                    pd.Series(np.nan, index=df.index)
                ),
                2,
                np.where(
                    df.get(
                        "minus_di",
                        pd.Series(np.nan, index=df.index)
                    )
                    >
                    df.get(
                        "plus_di",
                        pd.Series(np.nan, index=df.index)
                    ),
                    -2,
                    0
                )
            ),
            0
        )

    # --------------------------------------------------------
    # ADX very strong confirmation
    # --------------------------------------------------------

    if "adx" in df.columns:

        score += np.where(
            (df["adx"] >= 40) &
            (df.get(
                "plus_di",
                pd.Series(np.nan, index=df.index)
            )
            >
            df.get(
                "minus_di",
                pd.Series(np.nan, index=df.index
            ))),
            1,
            np.where(
                (df["adx"] >= 40) &
                (df.get(
                    "minus_di",
                    pd.Series(np.nan, index=df.index)
                )
                >
                df.get(
                    "plus_di",
                    pd.Series(np.nan, index=df.index)
                )),
                -1,
                0
            )
        )

    # ========================================================
    # 7. BREAKOUT / BREAKDOWN
    # ========================================================

    if "resistance_breakout" in df.columns:

        score += np.where(
            df["resistance_breakout"],
            2,
            0
        )

    if "support_breakdown" in df.columns:

        score += np.where(
            df["support_breakdown"],
            -2,
            0
        )

    # ========================================================
    # 8. CONTINUATION PATTERNS
    # ========================================================

    if "bullish_continuation" in df.columns:

        score += np.where(
            df["bullish_continuation"],
            2,
            0
        )

    if "bearish_continuation" in df.columns:

        score += np.where(
            df["bearish_continuation"],
            -2,
            0
        )

    # ========================================================
    # 9. REVERSAL PATTERNS
    # ========================================================

    if "bullish_engulfing" in df.columns:
        score += np.where(
            df["bullish_engulfing"],
            2,
            0
        )

    if "bearish_engulfing" in df.columns:
        score += np.where(
            df["bearish_engulfing"],
            -2,
            0
        )

    if "hammer" in df.columns:
        score += np.where(
            df["hammer"],
            1,
            0
        )

    if "shooting_star" in df.columns:
        score += np.where(
            df["shooting_star"],
            -1,
            0
        )

    if "morning_star" in df.columns:
        score += np.where(
            df["morning_star"],
            2,
            0
        )

    if "evening_star" in df.columns:
        score += np.where(
            df["evening_star"],
            -2,
            0
        )

    if "double_bottom" in df.columns:
        score += np.where(
            df["double_bottom"],
            2,
            0
        )

    if "double_top" in df.columns:
        score += np.where(
            df["double_top"],
            -2,
            0
        )

    # ========================================================
    # 10. VOLUME CONFIRMATION
    # ========================================================

    if "volume_spike" in df.columns:

        # Volume spike confirms current directional bias
        bullish_context = (
            (df.get(
                "supertrend_direction",
                pd.Series(0, index=df.index)
            ) == 1)
            |
            (df["close"] > df.get(
                "vwap",
                pd.Series(np.nan, index=df.index)
            ))
        )

        bearish_context = (
            (df.get(
                "supertrend_direction",
                pd.Series(0, index=df.index)
            ) == -1)
            |
            (df["close"] < df.get(
                "vwap",
                pd.Series(np.nan, index=df.index)
            ))
        )

        score += np.where(
            df["volume_spike"] & bullish_context,
            1,
            np.where(
                df["volume_spike"] & bearish_context,
                -1,
                0
            )
        )

    # ========================================================
    # FINAL SCORE
    # ========================================================

    df["signal_score"] = score

    df["signal_strength"] = score.abs()

    # ========================================================
    # SIGNAL CLASSIFICATION
    # ========================================================

    df["signal"] = np.select(

        [
            score >= 10,
            score >= 6,
            score >= 3,
            score <= -10,
            score <= -6,
            score <= -3
        ],

        [
            "STRONG BUY",
            "BUY",
            "WEAK BUY",
            "STRONG SELL",
            "SELL",
            "WEAK SELL"
        ],

        default="NEUTRAL"
    )

    return df


def prepare_chart_data(interval="5m", days=5):

    df = load_nifty_candles(
        interval=interval,
        days=days
    )

    if df is None or df.empty:
        return pd.DataFrame()

    # ========================================================
    # BASIC PRICE / TECHNICAL FEATURES
    # ========================================================

    df = add_price_features(df)
    df = add_moving_averages(df)
    df = add_atr(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_bollinger_bands(df)
    df = add_vwap(df)

    # ========================================================
    # TREND ENGINE
    # ========================================================

    df = add_supertrend(df)
    df = add_adx(df)

    # ========================================================
    # MARKET STRUCTURE
    # ========================================================

    df = add_market_structure(df)

    # ========================================================
    # PATTERN ENGINE
    # ========================================================

    df = add_reversal_patterns(df)
    df = add_continuation_patterns(df)

    # ========================================================
    # PRICE ACTION EVENTS
    # ========================================================

    df = add_price_action_events(df)

    # ========================================================
    # FINAL MULTI-FACTOR SIGNAL SCORE
    # ========================================================

    df = add_signal_score(df)

    return df


# ============================================================
# MULTI-TIMEFRAME SIGNAL ENGINE
# ============================================================

def get_multi_timeframe_signal(
    timeframes=None,
    days_map=None
):
    """
    Build a multi-timeframe market signal using the
    existing chart engine.

    Returns:
        {
            "timeframes": {...},
            "overall_score": float,
            "overall_signal": str,
            "higher_tf": str,
            "medium_tf": str,
            "intraday_tf": str,
            "alignment": str
        }
    """

    if timeframes is None:
        timeframes = ["1D", "1H", "15m", "5m"]

    if days_map is None:
        days_map = {
            "1D": 365,
            "1H": 30,
            "15m": 10,
            "5m": 5
        }

    results = {}

    # --------------------------------------------------------
    # TIMEFRAME WEIGHTS
    # --------------------------------------------------------

    weights = {
        "1D": 3.0,
        "1H": 2.5,
        "15m": 1.5,
        "5m": 1.0
    }

    # --------------------------------------------------------
    # LOAD EACH TIMEFRAME
    # --------------------------------------------------------

    for timeframe in timeframes:

        try:

            df = prepare_chart_data(
                interval=timeframe,
                days=days_map.get(timeframe, 5)
            )

            if df is None or df.empty:

                results[timeframe] = {
                    "signal": "NO DATA",
                    "score": 0.0,
                    "price": None,
                    "adx": None,
                    "supertrend": "NO DATA",
                    "adx_direction": "NO DATA"
                }

                continue

            row = df.iloc[-1]

            score = float(
                row.get(
                    "signal_score",
                    0
                )
            )

            results[timeframe] = {

                "signal": str(
                    row.get(
                        "signal",
                        "NEUTRAL"
                    )
                ),

                "score": score,

                "price": row.get(
                    "close"
                ),

                "adx": row.get(
                    "adx"
                ),

                "supertrend": str(
                    row.get(
                        "supertrend_signal",
                        "NEUTRAL"
                    )
                ),

                "adx_direction": str(
                    row.get(
                        "adx_direction",
                        "NEUTRAL"
                    )
                ),

                "adx_strength": str(
                    row.get(
                        "adx_strength",
                        "WEAK"
                    )
                )
            }

        except Exception as e:

            results[timeframe] = {
                "signal": "ERROR",
                "score": 0.0,
                "price": None,
                "adx": None,
                "supertrend": "ERROR",
                "adx_direction": "ERROR",
                "adx_strength": "ERROR",
                "error": str(e)
            }

    # --------------------------------------------------------
    # WEIGHTED SCORE
    # --------------------------------------------------------

    weighted_score = 0.0
    total_weight = 0.0

    for timeframe, data in results.items():

        if data["signal"] in ["NO DATA", "ERROR"]:
            continue

        weight = weights.get(
            timeframe,
            1.0
        )

        weighted_score += (
            data["score"] * weight
        )

        total_weight += weight

    if total_weight > 0:

        overall_score = (
            weighted_score / total_weight
        )

    else:

        overall_score = 0.0

    # --------------------------------------------------------
    # OVERALL SIGNAL
    # --------------------------------------------------------

    if overall_score >= 8:

        overall_signal = "STRONG BUY"

    elif overall_score >= 4:

        overall_signal = "BUY"

    elif overall_score >= 2:

        overall_signal = "WEAK BUY"

    elif overall_score <= -8:

        overall_signal = "STRONG SELL"

    elif overall_score <= -4:

        overall_signal = "SELL"

    elif overall_score <= -2:

        overall_signal = "WEAK SELL"

    else:

        overall_signal = "NEUTRAL"

    # --------------------------------------------------------
    # TIMEFRAME GROUPS
    # --------------------------------------------------------

    higher_tf = results.get(
        "1D",
        {}
    ).get(
        "signal",
        "NO DATA"
    )

    medium_tf = results.get(
        "1H",
        {}
    ).get(
        "signal",
        "NO DATA"
    )

    intraday_tf = results.get(
        "15m",
        {}
    ).get(
        "signal",
        "NO DATA"
    )

    fast_tf = results.get(
        "5m",
        {}
    ).get(
        "signal",
        "NO DATA"
    )

    # --------------------------------------------------------
    # SIGNAL ALIGNMENT
    # --------------------------------------------------------

    valid_signals = [
        data["signal"]
        for data in results.values()
        if data["signal"]
        not in ["NO DATA", "ERROR"]
    ]

    bullish_count = sum(
        1
        for signal in valid_signals
        if "BUY" in signal
    )

    bearish_count = sum(
        1
        for signal in valid_signals
        if "SELL" in signal
    )

    neutral_count = sum(
        1
        for signal in valid_signals
        if signal == "NEUTRAL"
    )

    if bullish_count == len(valid_signals) and valid_signals:

        alignment = "FULL BULLISH ALIGNMENT"

    elif bearish_count == len(valid_signals) and valid_signals:

        alignment = "FULL BEARISH ALIGNMENT"

    elif bullish_count > bearish_count:

        alignment = "BULLISH BIAS"

    elif bearish_count > bullish_count:

        alignment = "BEARISH BIAS"

    else:

        alignment = "MIXED / NEUTRAL"

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {

        "timeframes": results,

        "overall_score": round(
            overall_score,
            2
        ),

        "overall_signal": overall_signal,

        "higher_tf": higher_tf,

        "medium_tf": medium_tf,

        "intraday_tf": intraday_tf,

        "fast_tf": fast_tf,

        "alignment": alignment,

        "bullish_count": bullish_count,

        "bearish_count": bearish_count,

        "neutral_count": neutral_count
    }


# ============================================================
# MULTI-TIMEFRAME MARKET REGIME
# ============================================================

def classify_multi_timeframe_regime(mtf_result):

    if not mtf_result:
        return {
            "regime": "NO DATA",
            "bias": "NEUTRAL",
            "description": "No multi-timeframe data available.",
            "risk": "UNKNOWN"
        }

    higher = mtf_result.get(
        "higher_tf",
        "NO DATA"
    )

    medium = mtf_result.get(
        "medium_tf",
        "NO DATA"
    )

    intraday = mtf_result.get(
        "intraday_tf",
        "NO DATA"
    )

    fast = mtf_result.get(
        "fast_tf",
        "NO DATA"
    )

    bullish_count = mtf_result.get(
        "bullish_count",
        0
    )

    bearish_count = mtf_result.get(
        "bearish_count",
        0
    )

    # --------------------------------------------------------
    # DIRECTION HELPERS
    # --------------------------------------------------------

    bullish_higher = (
        "BUY" in higher
        and "SELL" not in higher
    )

    bearish_higher = (
        "SELL" in higher
    )

    bullish_medium = (
        "BUY" in medium
        and "SELL" not in medium
    )

    bearish_medium = (
        "SELL" in medium
    )

    bullish_intraday = (
        "BUY" in intraday
        and "SELL" not in intraday
    )

    bearish_intraday = (
        "SELL" in intraday
    )

    bullish_fast = (
        "BUY" in fast
        and "SELL" not in fast
    )

    bearish_fast = (
        "SELL" in fast
    )

    # --------------------------------------------------------
    # FULL BULLISH TREND
    # --------------------------------------------------------

    if (
        bullish_higher
        and bullish_medium
        and bullish_intraday
        and bullish_fast
    ):

        return {
            "regime": "TRENDING BULLISH",
            "bias": "BULLISH",
            "description": (
                "Higher, medium and intraday "
                "timeframes are aligned bullish."
            ),
            "risk": "LOWER"
        }

    # --------------------------------------------------------
    # FULL BEARISH TREND
    # --------------------------------------------------------

    if (
        bearish_higher
        and bearish_medium
        and bearish_intraday
        and bearish_fast
    ):

        return {
            "regime": "TRENDING BEARISH",
            "bias": "BEARISH",
            "description": (
                "Higher, medium and intraday "
                "timeframes are aligned bearish."
            ),
            "risk": "LOWER"
        }

    # --------------------------------------------------------
    # BULLISH RECOVERY
    # --------------------------------------------------------

    if (
        bearish_higher
        and bearish_medium
        and bullish_intraday
        and bullish_fast
    ):

        return {
            "regime": "BULLISH RECOVERY",
            "bias": "SHORT-TERM BULLISH",
            "description": (
                "Intraday momentum is bullish "
                "against a bearish higher-timeframe trend."
            ),
            "risk": "HIGHER"
        }

    # --------------------------------------------------------
    # BEARISH PULLBACK
    # --------------------------------------------------------

    if (
        bullish_higher
        and bullish_medium
        and bearish_intraday
        and bearish_fast
    ):

        return {
            "regime": "BEARISH PULLBACK",
            "bias": "SHORT-TERM BEARISH",
            "description": (
                "Intraday momentum is bearish "
                "against a bullish higher-timeframe trend."
            ),
            "risk": "HIGHER"
        }

    # --------------------------------------------------------
    # HIGHER TF BULLISH / INTRADAY MIXED
    # --------------------------------------------------------

    if (
        bullish_higher
        and bullish_medium
        and bullish_count > bearish_count
    ):

        return {
            "regime": "BULLISH BIAS / MIXED",
            "bias": "BULLISH",
            "description": (
                "Higher timeframes remain bullish "
                "but intraday signals are not fully aligned."
            ),
            "risk": "MEDIUM"
        }

    # --------------------------------------------------------
    # HIGHER TF BEARISH / INTRADAY MIXED
    # --------------------------------------------------------

    if (
        bearish_higher
        and bearish_medium
        and bearish_count > bullish_count
    ):

        return {
            "regime": "BEARISH BIAS / MIXED",
            "bias": "BEARISH",
            "description": (
                "Higher timeframes remain bearish "
                "but intraday signals are not fully aligned."
            ),
            "risk": "MEDIUM"
        }

    # --------------------------------------------------------
    # MAJORITY BULLISH
    # --------------------------------------------------------

    if bullish_count > bearish_count:

        return {
            "regime": "MIXED / BULLISH BIAS",
            "bias": "BULLISH",
            "description": (
                "More timeframes are bullish, "
                "but complete alignment is absent."
            ),
            "risk": "MEDIUM"
        }

    # --------------------------------------------------------
    # MAJORITY BEARISH
    # --------------------------------------------------------

    if bearish_count > bullish_count:

        return {
            "regime": "MIXED / BEARISH BIAS",
            "bias": "BEARISH",
            "description": (
                "More timeframes are bearish, "
                "but complete alignment is absent."
            ),
            "risk": "MEDIUM"
        }

    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    return {
        "regime": "MIXED / NEUTRAL",
        "bias": "NEUTRAL",
        "description": (
            "Timeframes are conflicting "
            "with no dominant directional bias."
        ),
        "risk": "HIGHER"
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("==============================")
    print("NIFTY CHART ENGINE TEST")
    print("==============================")
    df = prepare_chart_data(interval="1minute", days=5)
    print("Rows:", len(df))
    print("Columns:", df.columns.tolist())
    if not df.empty:
        print("Latest signal:", get_latest_chart_signal(df))
        print(df.tail(5).to_string(index=False))
    print("Chart engine test complete.")


