from ResistanceSupportDectector.aiStartegy import MyStrategy, combine_timeframe_signals
import asyncio
import numpy as np
from bot import TradingBot
from config import Config
from datetime import datetime, timedelta
import pytz

bot = TradingBot(Config.MT5_LOGIN, Config.MT5_PASSWORD, Config.MT5_SERVER)

class Optimize:

    def __init__(self, dataframes):
        self.df = dataframes
        self.m1_df = dataframes[0]
        self.m5_df = dataframes[1]
        self.m15_df = dataframes[2]
        self.weights = {"M1": 0.2, "M5": 0.3, "M15": 0.5}

        connect = bot.connect()
        if not connect:
            print("cant connet")


    async def calculate_combined_signal(self, weights=None):
        """
        Calculates the combined signal strength for the M1, M5, M15 timeframes using dynamic weights.
        
        Args:
        - m1_df: DataFrame for M1 timeframe.
        - m5_df: DataFrame for M5 timeframe.
        - m15_df: DataFrame for M15 timeframe.
        - weights: Dictionary of weights for each timeframe {'m1': 0.2, 'm5': 0.3, 'm15': 0.5}.
        
        Returns:
        - Combined signal strength based on weighted timeframes.
        """
        
        # Calculate individual signal strength

        if weights is None:
            weights = self.weights.values()
        

        tasks = []
        for df in self.df:
            startegy = MyStrategy(df)
            tasks.append(asyncio.create_task(startegy.run()))

        results = await asyncio.gather(*tasks)
        combined_strength, signal = await combine_timeframe_signals(results, weights)
        

        
        return float(combined_strength)

    async def optimize_weights(self):
        """
        Iteratively adjust the weights to find the optimal combination that provides the best accuracy.
        
        Args:
        - m1_df: DataFrame for M1 timeframe.
        - m5_df: DataFrame for M5 timeframe.
        - m15_df: DataFrame for M15 timeframe.
        
        Returns:
        - The optimal weights that give the highest signal strength accuracy.
        """
        
        best_weights = None
        best_accuracy = -1
        

        
        # Iterate through potential weights combinations (you can refine the granularity of steps)
        for m1_weight in np.arange(0, 1.1, 0.1):
            for m5_weight in np.arange(0, 1.1, 0.1):
                m15_weight = 1 - m1_weight - m5_weight  # The sum of weights should equal 1
                if m15_weight < 0:
                    continue
                
                # Calculate combined signal for this set of weights
                weights = {'m1': m1_weight, 'm5': m5_weight, 'm15': m15_weight}
                combined_signal = await self.calculate_combined_signal(weights.values())
                
                # Evaluate accuracy (this is a placeholder for your evaluation logic)
                accuracy = self.evaluate_accuracy(combined_signal)  
                
                # Keep track of the best weights
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_weights = weights
                    
        return best_weights




    def evaluate_accuracy(self, combined_signal, threshold=0.65, lookahead=5):
        """
        Evaluate accuracy of combined signal by comparing it to actual price movement.

        Args:
        - df: DataFrame containing price data.
        - combined_signal: Calculated signal strength (buy/sell strength).
        - threshold: Threshold to consider strong buy/sell signals.
        - lookahead: Number of candles to look ahead to evaluate if the signal was accurate.

        Returns:
        - Accuracy as a percentage of correct signals.
        """
        correct_signals = 0
        total_signals = 0
        df = self.df[2]

        for i in range(len(df) - lookahead):
            future_price = df['close'].iloc[i + lookahead]
            current_price = df['close'].iloc[i]

            # Buy signal
            if combined_signal > threshold:
                total_signals += 1
                if future_price > current_price:  # Price increases
                    correct_signals += 1

            # Sell signal
            elif combined_signal < (1 - threshold):
                total_signals += 1
                if future_price < current_price:  # Price decreases
                    correct_signals += 1

        if total_signals == 0:
            return 0  # Avoid division by zero

        accuracy = correct_signals / total_signals
        return accuracy
    
    def evaluate_spike_accuracy(self, combined_signal, spike_threshold=1.5, lookahead=5):
        """
        Evaluates the accuracy of detecting spikes in Boom/Crash markets.

        Args:
        - df: DataFrame containing price data.
        - combined_signal: Signal strength calculated.
        - spike_threshold: Price change threshold to consider as a spike.
        - lookahead: Number of candles to look ahead for spike detection.

        Returns:
        - Spike detection accuracy as a percentage.
        """
        correct_spikes = 0
        total_signals = 0
        df = self.df[2]

        for i in range(len(df) - lookahead):
            future_price = df['close'].iloc[i + lookahead]
            current_price = df['close'].iloc[i]

            price_change = (future_price - current_price) / current_price

            # Buy signal and upward spike
            if combined_signal > 0.65:
                total_signals += 1
                if price_change > spike_threshold:
                    correct_spikes += 1

            # Sell signal and downward spike
            elif combined_signal < 0.45:
                total_signals += 1
                if price_change < -spike_threshold:
                    correct_spikes += 1

        if total_signals == 0:
            return 0

        accuracy = correct_spikes / total_signals
        return accuracy
    

    def evaluate_profit(self, combined_signal, threshold=0.65, lookahead=10, profit_target=0.02):
        """
        Evaluate accuracy by checking if the trade based on the signal was profitable.

        Args:
        - df: DataFrame containing price data.
        - combined_signal: Calculated signal strength (buy/sell strength).
        - threshold: Threshold to consider strong buy/sell signals.
        - lookahead: Number of candles to evaluate the profit target.
        - profit_target: Percentage of price increase/decrease to consider as a profitable trade.

        Returns:
        - Profit accuracy as a percentage of profitable trades.
        """
        profitable_trades = 0
        total_trades = 0
        df = self.df

        for i in range(len(df) - lookahead):
            future_price = df['close'].iloc[i + lookahead]
            current_price = df['close'].iloc[i]

            # Buy signal
            if combined_signal > threshold:
                total_trades += 1
                if future_price > current_price * (1 + profit_target):  # Price increases by target
                    profitable_trades += 1

            # Sell signal
            elif combined_signal < (1 - threshold):
                total_trades += 1
                if future_price < current_price * (1 - profit_target):  # Price decreases by target
                    profitable_trades += 1

        if total_trades == 0:
            return 0  # Avoid division by zero

        profit_accuracy = profitable_trades / total_trades
        return profit_accuracy
    

    async def run(self):
        """
        Main function to run the trading signal bot.

        Args:
        - market: The market symbol (e.g., 'EURUSD').
        - start: Start date for historical data.
        - end: End date for historical data.
        """
        # Step 1: Fetch all data for different timeframes
        
        # # Step 2: Calculate signal strength for each timeframe
        # signals = self.calculate_signal_strength(all_data)

        # Step 3: Optimize weights based on signal accuracy
        optimized_weights = await self.optimize_weights()
        print("Optimized Weights:", optimized_weights)

        # Step 4: Combine signals from all timeframes using optimized weights
        combined_signal =  await self.calculate_combined_signal()
        print("Combined Signal Strength:", combined_signal)

        spike_accuracy = self.evaluate_spike_accuracy(combined_signal)
        print("Spike Detection Accuracy:", spike_accuracy)

        profit_accuracy = self.evaluate_profit(combined_signal)
        print("Profit Accuracy:", profit_accuracy)

        # Step 5: Evaluate performance (accuracy, profit, etc.)
        accuracy = self.evaluate_accuracy(combined_signal)  # Use M5 for example evaluation
        print("Signal Accuracy:", accuracy)

        # # Example exit strategy based on the combined signal
        # if combined_signal > 0.65:
        #     print("Buy Signal - Strong Buy")
        # elif combined_signal < 0.35:
        #     print("Sell Signal - Strong Sell")
        # else:
        #     print("Neutral Signal")



async def main():
    # Define the market, start date, and end date for historical data
    market = 'Boom 1000 Index'

    timezone = pytz.timezone("Etc/UTC")
    end_time = datetime.now(tz=timezone)
    start_time = end_time - timedelta(minutes=3600) 

    # Initialize the optimizer with historical data
    bot.connect()
    dataframes = await bot.fetch_all_timeframes(market, start_time, end_time)
    optimizer = Optimize(dataframes)
    await optimizer.run() # Run the optimizer

if __name__ == "__main__":
    asyncio.run(main())  # Run the main function using asyncio

