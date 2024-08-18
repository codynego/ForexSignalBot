import pandas as pd
import numpy as np
from utils.indicators import Indicator
import asyncio

async def is_support_resistance(df, ma_period=10):
    """
    Determines whether the moving average (MA) is acting as support, resistance, or neutral.

    Parameters:
    - df: DataFrame containing at least the 'close' price column.
    - ma_period: Length of the moving average.

    Returns:
    - 'support' if the MA is acting as support, 'resistance' if acting as resistance,
      or 'neutral' if neither.
    """

    # Calculate the Moving Average (MA)
    indicator = Indicator(df)
    #df['MA'] = df['close'].rolling(window=ma_period).mean()
    df['MA'] = indicator.moving_average(ma_period)

    # Calculate the slope of the MA (using the difference between the last two MAs)
    df['MA_slope'] = df['MA'].diff()

    # Set initial state as neutral
    support_resistance = 'neutral'

    # Determine if the price is above or below the MA
    if df['close'].iloc[-1] > df['MA'].iloc[-1]:
        # Price is above the MA, possible resistance
        if df['close'].iloc[-2] < df['MA'].iloc[-2]:
            support_resistance = 'resistance'

    elif df['close'].iloc[-1] < df['MA'].iloc[-1]:
        # Price is below the MA, possible support
        if df['close'].iloc[-2] > df['MA'].iloc[-2]:
            support_resistance = 'support'

    # Refine the determination by considering the slope of the MA
    if support_resistance == 'resistance' and df['MA_slope'].iloc[-1] > 0:
        # Price is above MA, but MA is sloping upward (indicating an uptrend)
        # More likely to be support in an uptrend
        support_resistance = 'neutral'

    elif support_resistance == 'support' and df['MA_slope'].iloc[-1] < 0:
        # Price is below MA, but MA is sloping downward (indicating a downtrend)
        # More likely to be resistance in a downtrend
        support_resistance = 'neutral'

    # Further refine by checking for bounces
    # Count the number of bounces off the MA in recent periods
    bounce_count = 0
    for i in range(-ma_period, -1):
        if (df['close'].iloc[i] > df['MA'].iloc[i] and df['close'].iloc[i-1] < df['MA'].iloc[i-1]) or \
           (df['close'].iloc[i] < df['MA'].iloc[i] and df['close'].iloc[i-1] > df['MA'].iloc[i-1]):
            bounce_count += 1

    # If the bounce count is high, it suggests a strong support/resistance level
    if bounce_count >= 2:
        if support_resistance == 'neutral' and df['close'].iloc[-1] > df['MA'].iloc[-1]:
            support_resistance = 'resistance'
        elif support_resistance == 'neutral' and df['close'].iloc[-1] < df['MA'].iloc[-1]:
            support_resistance = 'support'

    return support_resistance


async def is_price_near_ma(df, ma_period=10, tolerance=0.05):
  """
  Checks if the current price is within a tolerance of the MA.

  Args:
    df: Pandas DataFrame containing price data with columns 'close' and 'Date'.
    ma_period: Length of the moving average.
    tolerance: Percentage tolerance for considering price near MA.

  Returns:
    True if the price is within tolerance of the MA, False otherwise.
  """

  indicator = Indicator(df)
    #df['MA'] = df['close'].rolling(window=ma_period).mean()
  df['MA'] = indicator.moving_average(ma_period)
  last_price = df['close'].iloc[-1]
  last_ma = df['MA'].iloc[-1]
  return abs(last_price - last_ma) / last_ma <= tolerance

