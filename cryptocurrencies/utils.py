import numpy as np


def calculate_rsi(close_prices, period):
    """
    Calculate the Relative Strength Index (RSI) for a given period.
    Returns a dictionary containing the RSI, RS (Relative Strength), gains, losses, and interpretation.
    Handles infinite and out-of-range values for RS and RSI.
    """
    if len(close_prices) < period + 1:
        raise ValueError(
            f"Not enough data to calculate RSI for the period of {period} days.",
        )

    # Calculate the price changes (deltas)
    deltas = np.diff(close_prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    # Calculate the average gain and average loss for the given period
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    # RS calculation, handle division by zero if avg_loss is zero
    if avg_loss == 0:
        RS = float("inf")
        RSI = 100  # If avg_loss is zero, RSI is 100 (overbought)
    else:
        RS = avg_gain / avg_loss
        RSI = 100 - (100 / (1 + RS))

    # Handle the case when RS becomes infinite
    if np.isinf(RS):
        RS = "Infinity"

    # Ensure RSI stays between 0 and 100
    RSI = min(100, max(0, RSI))

    # Interpretation of RSI values
    interpretation = "Neutral"
    if RSI < 30:
        interpretation = "Oversold"
    elif RSI > 70:
        interpretation = "Overbought"

    return {
        "gains": gains.tolist(),
        "losses": losses.tolist(),
        "RS": RS,
        "RSI": RSI,
        "interpretation": interpretation,
    }
