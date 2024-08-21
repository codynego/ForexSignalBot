import pandas as pd
from ResistanceSupportDectector.detector import is_price_near_bollinger_band, is_price_near_ma, is_bollinger_band_support_resistance, is_support_resistance
from utils.indicators import Indicator



def detect_spike(df, window=20, threshold=1.5):
    """
    Detects spikes in the price data based on the size of the price movement compared to recent history.

    Args:
    - df: DataFrame containing price data with a 'close' column.
    - window: Number of periods to calculate the average volatility.
    - threshold: Multiplier to determine if the current price movement is a spike.

    Returns:
    - A list of indices where spikes were detected.
    """
    spikes = []
    
    # Calculate the recent volatility
    df['price_change'] = df['close'].diff()
    df['abs_change'] = df['price_change'].abs()
    df['rolling_volatility'] = df['abs_change'].rolling(window=window).mean()

    # Detect spikes
    for i in range(window, len(df)):
        current_change = df['price_change'].iloc[i]
        rolling_volatility = df['rolling_volatility'].iloc[i]
        if abs(current_change) > threshold * rolling_volatility:
            spikes.append(i)
    
    return spikes



def calculate_pivot_points(df):
    high = df['high'].iloc[-1]
    low = df['low'].iloc[-1]
    close = df['close'].iloc[-1]
    
    pivot = (high + low + close) / 3
    resistance1 = (2 * pivot) - low
    support1 = (2 * pivot) - high
    resistance2 = pivot + (high - low)
    support2 = pivot - (high - low)
    
    return {
        'pivot': pivot,
        'resistance_1': resistance1,
        'support_1': support1,
        'resistance_2': resistance2,
        'support_2': support2
    }


def detect_trend(df):
    short_ema = df['close'].ewm(span=50, adjust=False).mean()
    long_ema = df['close'].ewm(span=200, adjust=False).mean()
    
    if short_ema.iloc[-1] > long_ema.iloc[-1]:
        return 'uptrend'
    elif short_ema.iloc[-1] < long_ema.iloc[-1]:
        return 'downtrend'
    else:
        return 'sideways'


def calculate_signal_strength(trend, rsi_value, pivot_point_data, ma_proximity, bb_signal, ma_support_resistance, bb_support_resistance, spike_indices, current_index):
    """
    Calculate the strength of the buy/sell signal based on trend, RSI, proximity to pivot points,
    and support/resistance levels for MA and Bollinger Bands, including spike detection.

    Args:
    - trend: The current trend ('uptrend', 'downtrend', 'sideways')
    - rsi_value: The RSI value to determine overbought/oversold conditions.
    - pivot_point_data: Data on pivot points to check proximity to support/resistance.
    - ma_proximity: A boolean indicating whether price is near the moving average.
    - bb_signal: Bollinger Band signal ('upper_band', 'lower_band', or 'neutral')
    - ma_support_resistance: Whether MA is acting as support or resistance ('support', 'resistance', 'neutral')
    - bb_support_resistance: Whether Bollinger Bands are acting as support or resistance ('support', 'resistance', 'neutral')
    - spike_indices: List of indices where spikes were detected.
    - current_index: The index of the current price point for evaluating spike influence.

    Returns:
    - Signal strength as an integer between 0 and 100.
    """
    strength = 0

    # Base on trend direction
    if trend == 'uptrend':
        strength += 30
    elif trend == 'downtrend':
        strength += 30

    # Check RSI
    if rsi_value < 30:  # Oversold, potential buy signal
        strength += 20
    elif rsi_value > 70:  # Overbought, potential sell signal
        strength += 20

    # Check if price is near a moving average
    if ma_proximity:
        strength += 10

    # MA support/resistance
    if ma_support_resistance == 'support':
        strength += 10
    elif ma_support_resistance == 'resistance':
        strength += 10

    # Check Bollinger Band signals
    if bb_signal == 'upper_band':
        strength += 10
    elif bb_signal == 'lower_band':
        strength += 10

    # Bollinger Bands support/resistance
    if bb_support_resistance == 'support':
        strength += 10
    elif bb_support_resistance == 'resistance':
        strength += 10

    # Pivot point proximity
    if pivot_point_data['support_1'] <= strength <= pivot_point_data['resistance_1']:
        strength += 20

    # Check for spikes
    if current_index in spike_indices:
        strength += 20  # Increase strength if a spike is detected at the current index

    return min(strength, 100)  # Cap the strength at 100




class MyStrategy():
    def __init__(self, data):
        self.data = data
        bt = Indicator(self.data)
        # Initialization of indicators and price data
        self.ma = bt.moving_average(period=10)
        self.rsi = bt.rsi(period=14)
        self.df = self.data  # Placeholder for DataFrame with price data
        
    async def run(self):
        # 1. Calculate pivot points
        pivot_point_data = calculate_pivot_points(self.data)

        spike_indices = detect_spike(self.df, window=20, threshold=1.5)
        current_index = len(self.df) - 1
        
        # 2. Detect the current trend
        trend = detect_trend(self.df)
        
        # 3. Check RSI
        
        rsi_value = self.rsi.iloc[-1]
        
        # 4. Check if price is near MA
        ma_proximity = await is_price_near_ma(self.df, ma_period=10, tolerance=0.05)
        
        # 5. Check Bollinger Band signal
        bb_signal = await is_price_near_bollinger_band(self.df, period=20, std_dev=2, tolerance=0.02)

        bb_support_resistance = await is_bollinger_band_support_resistance(self.df)
        ma_support_resistance  = await is_support_resistance(self.df, 10)
        
        # 6. Calculate the signal strength
        signal_strength = calculate_signal_strength(
            trend,
            rsi_value,
            pivot_point_data,
            ma_proximity,
            bb_signal,
            ma_support_resistance,
            bb_support_resistance,
            spike_indices=spike_indices,
            current_index=current_index
        )
            
        
        # 7. Execute trade based on signal strength
        if signal_strength >= 60:
            # Strong buy signal
            return "BUY"
        elif signal_strength <= 40:
            # Strong sell signal
            return "SELL"



