# ============================================================
# NIFTY LIVE CANDLESTICK CHART
# ============================================================

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from nifty_candles import (
    get_nifty_candles,
    validate_candles,
)


# ============================================================
# CHART CONFIG
# ============================================================

CHART_HEIGHT = 650


# ============================================================
# LOAD DATA
# ============================================================

def load_chart_data(
    timeframe="5m",
    days=5,
):
    """
    Load NIFTY candle data for charting.
    """

    df = get_nifty_candles(
        timeframe=timeframe,
        days=days,
    )

    if df is None or df.empty:
        return None

    if not validate_candles(df):
        raise ValueError(
            "Invalid candle data received."
        )

    return df


# ============================================================
# CREATE CANDLESTICK CHART
# ============================================================

def create_nifty_chart(
    df,
    show_volume=True,
):
    """
    Create institutional-style NIFTY
    candlestick chart.
    """

    if df is None or df.empty:
        raise ValueError(
            "No candle data available."
        )

    # --------------------------------------------------------
    # Figure
    # --------------------------------------------------------

    if show_volume:

        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[
                0.78,
                0.22,
            ],
        )

    else:

        fig = go.Figure()

    # ========================================================
    # CANDLESTICK
    # ========================================================

    candle = go.Candlestick(

        x=df["timestamp"],

        open=df["open"],

        high=df["high"],

        low=df["low"],

        close=df["close"],

        name="NIFTY",

        increasing=dict(
            line=dict(
                width=1
            )
        ),

        decreasing=dict(
            line=dict(
                width=1
            )
        ),

        whiskerwidth=0.5,
    )

    if show_volume:

        fig.add_trace(
            candle,
            row=1,
            col=1,
        )

    else:

        fig.add_trace(
            candle
        )

    # ========================================================
    # VOLUME
    # ========================================================

    if show_volume:

        volume_colors = []

        for _, row in df.iterrows():

            if row["close"] >= row["open"]:
                volume_colors.append(
                    "rgba(0, 200, 120, 0.45)"
                )

            else:
                volume_colors.append(
                    "rgba(255, 80, 80, 0.45)"
                )

        volume = go.Bar(

            x=df["timestamp"],

            y=df["volume"],

            name="Volume",

            marker=dict(
                color=volume_colors
            ),

            hovertemplate=(
                "Volume: %{y:,.0f}"
                "<extra></extra>"
            ),
        )

        fig.add_trace(
            volume,
            row=2,
            col=1,
        )

    # ========================================================
    # LAYOUT
    # ========================================================

    fig.update_layout(

        height=CHART_HEIGHT,

        template="plotly_dark",

        paper_bgcolor="#07111f",

        plot_bgcolor="#07111f",

        margin=dict(
            l=45,
            r=20,
            t=40,
            b=35,
        ),

        hovermode="x unified",

        showlegend=False,

        xaxis_rangeslider_visible=False,

        dragmode="pan",

        font=dict(
            family="Arial",
            size=11,
        ),
    )

    # ========================================================
    # GRID
    # ========================================================

    fig.update_xaxes(

        showgrid=True,

        gridcolor="rgba(255,255,255,0.06)",

        zeroline=False,

        showspikes=True,

        spikemode="across",

        spikesnap="cursor",

        spikedash="dot",

        spikecolor="rgba(255,255,255,0.25)",
    )

    fig.update_yaxes(

        showgrid=True,

        gridcolor="rgba(255,255,255,0.06)",

        zeroline=False,

        fixedrange=False,
    )

    # ========================================================
    # VOLUME AXIS
    # ========================================================

    if show_volume:

        fig.update_yaxes(

            title_text="PRICE",

            row=1,

            col=1,

        )

        fig.update_yaxes(

            title_text="VOL",

            row=2,

            col=1,

        )

    # ========================================================
    # RANGE SELECTOR
    # ========================================================

    fig.update_xaxes(

        rangeslider_visible=False,

        rangeselector=dict(

            buttons=[
                dict(
                    count=1,
                    label="1D",
                    step="day",
                    stepmode="backward",
                ),

                dict(
                    count=5,
                    label="5D",
                    step="day",
                    stepmode="backward",
                ),

                dict(
                    count=1,
                    label="1M",
                    step="month",
                    stepmode="backward",
                ),

                dict(
                    count=3,
                    label="3M",
                    step="month",
                    stepmode="backward",
                ),

                dict(
                    step="all",
                    label="ALL",
                ),
            ],

            bgcolor="#101c2d",

            activecolor="#1f6feb",

            font=dict(
                color="white"
            ),
        )
    )

    return fig


# ============================================================
# QUICK TEST
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 60
    )

    print(
        "NIFTY CHART ENGINE TEST"
    )

    print(
        "=" * 60
    )

    df = load_chart_data(
        timeframe="5m",
        days=5,
    )

    print(
        "Rows:",
        len(df)
    )

    print(
        "Valid:",
        validate_candles(df)
    )

    fig = create_nifty_chart(
        df,
        show_volume=True,
    )

    fig.write_html(
        "nifty_chart_test.html"
    )

    print(
        "\nChart generated:"
    )

    print(
        "nifty_chart_test.html"
    )