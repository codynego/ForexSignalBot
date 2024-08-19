from utils.indicators import Indicator
#from ResistanceSupportDectector.detector import generate_buy_signal
from ResistanceSupportDectector.detector import is_support_resistance, is_price_near_ma, is_bollinger_band_support_resistance, is_price_near_bollinger_band
import asyncio

class Strategy:
    @classmethod
    # def rsiStrategy(cls, data):
    #     if generate_buy_signal(data):
    #         return -1
    #     else:
    #         return 1
    #     # indicator = Indicator(data)
    #     # rsi = indicator.rsi(14)
    #     # ma = indicator.moving_average(10)
    #     # print('moving average',ma.tail(1))
    #     # rsi_value = rsi.tail(1).values[0]
    #     # #print(data['close'].tail(1))
    #     # if rsi_value > 30:
    #     #     return 1
    #     # elif rsi_value < 30:
    #     #     return -1
    #     # return 0


    @classmethod
    async def rsiStrategy(cls, df, ma_period=10, tolerance=0.02, breakout_threshold=0.015):
        """
        Generates a buy signal based on MA10 behavior and price proximity.

        Args:
            df: Pandas DataFrame containing price data with columns 'Close' and 'Date'.
            ma_period: Length of the moving average.
            tolerance: Percentage tolerance for considering price near MA.
            breakout_threshold: Percentage threshold for price breakout.

        Returns:
            True if a buy signal is generated, False otherwise.
        """

        indicator = Indicator(df)
        ma48 = indicator.moving_average(48)
        # check m0ving average 10 behavior
        ma10_behavior = await is_support_resistance(df, ma_period)
        price_near_ma10 = await is_price_near_ma(df, ma_period, tolerance)
        breakout_10 = df['close'].iloc[-1] > df['MA_short'].iloc[-1] * (1 + breakout_threshold)

        # check moving average 48 behavior

        ma48_period = 48
        ma48_behavior = await is_support_resistance(df, ma48_period)
        price_near_ma48 = await is_price_near_ma(df, ma48_period, tolerance)
        breakout_48 = df['close'].iloc[-1] > ma48.iloc[-1] * (1 + breakout_threshold)

        # check bolling band behavior
        #ma48_period = 48
        bb_behavior = await is_bollinger_band_support_resistance(df)
        price_near_bb = await is_price_near_bollinger_band(df)
        breakout_48 = df['close'].iloc[-1] > ma48.iloc[-1] * (1 + breakout_threshold)


        buy_signal = (
            (ma10_behavior == 'support' and price_near_ma10 and breakout_10) or
            (ma48_behavior == 'support' and price_near_ma48 and breakout_48) or
            (bb_behavior == 'support' and price_near_bb == 'lower_band')
    )
        return buy_signal
        # Improved price breakout condition
        # if ma_behavior == 'support' and \
        #     price_near_ma and \
        #         df['close'].iloc[-1] > df['MA'].iloc[-1] * (1 + breakout_threshold) or \
        #            ma48_behavior == "support" and \
        #             price_near_ma48 and breakout_48:
        #     return True
        # else:
        #     return 
        

    @classmethod
    async def process_multiple_timeframes(cls, dataframes, ma_period=10, tolerance=0.02, breakout_threshold=0.015):
        """
        Processes multiple timeframes to generate a buy signal.

        Args:
            data: Dictionary containing price data for multiple timeframes.
            ma_period: Length of the moving average.
            tolerance: Percentage tolerance for considering price near MA.
            breakout_threshold: Percentage threshold for price breakout.

        Returns:
            True if a buy signal is generated, False otherwise.
        """
        tasks = []
        for df in dataframes:
            tasks.append(asyncio.create_task(cls.rsiStrategy(df, ma_period, tolerance, breakout_threshold)))

        results = await asyncio.gather(*tasks)

        if all(result for result in results):
            return 1
        else:
            return -1

