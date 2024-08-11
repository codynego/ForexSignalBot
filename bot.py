import MetaTrader5 as mt5
import numpy as np
import pandas as pd
from utils.indicators import Indicator
from utils.strategies import Strategy
import asyncio
from config import Config
import os
import django
from asgiref.sync import sync_to_async


# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()
from traderbot.models import Market, Indicator as IndicatorModel, Signal

class TradingBot:
    def __init__(self, login, password, server):
        self.login = login
        self.password = password
        self.server = server
        self.connected = False
        self.signals_cache = {} 
    
    def connect(self):
        if not mt5.initialize():
            print("initialize() failed, error code =", mt5.last_error())
            mt5.shutdown()
            self.connected = False
            return self.connected
        authorized = mt5.login(self.login, password=self.password, server=self.server)
        self.connected = authorized
        return self.connected

    def disconnect(self):
        mt5.shutdown()
        self.connected = False

    async def fetch_data(self, symbol, timeframe, start, end):
        if not self.connected:
            raise Exception("Not connected to MT5")
        rates = mt5.copy_rates_range(symbol, timeframe, start, end)
        df = pd.DataFrame(rates)
        return df

    async def fetch_multiple_data(self, symbols, timeframe, start, end):
        if not self.connected:
            raise Exception("Not connected to MT5")
        data_tasks = [self.fetch_data(symbol, timeframe, start, end) for symbol in symbols]
        return await asyncio.gather(*data_tasks)
    
    async def fetch_all_timeframes(self, symbol, start, end):
        if not self.connected:
            raise Exception("Not connected to MT5")
        data_tasks = [self.fetch_data(symbol, timeframe, start, end) for timeframe in Config.TIME_FRAMES]
        return await asyncio.gather(*data_tasks)
            
    def apply_strategy(self, data, strategy):
        indicator = Indicator(data.head(14))
        calc = indicator.rsi()
        last_indicator_value = calc.tail(1).values[0]
        print(last_indicator_value)

    async def generate_signal(self, data, strategy="rsistrategy", symbol=None):
            last_data = data.tail(1)["close"].values[0]
            signal = {"symbol": symbol, "price": last_data, "type": None, "strength": None}

            if strategy == "rsistrategy":
                stra = Strategy.rsiStrategy(data)
                if stra == 1:
                    signal["type"] = "BUY"
                elif stra == -1:
                    signal["type"] = "SELL"
                elif stra == 0:
                    signal["type"] = "HOLD"
                else:
                    return None

                # Check for duplicate signals
                signal_key = (symbol, signal["type"])
                if signal_key in self.signals_cache:
                    return None  # Duplicate found

                # Save the signal to the database
                saved_signal = await self.save_to_database("Signal", symbol, signal)
                
                # Update cache
                self.signals_cache[signal_key] = saved_signal
                return signal
            

    async def process_multiple_signals(self, data_list, market_list):
            signals = await asyncio.gather(*(self.generate_signal(data, symbol=market) for data, market in zip(data_list, market_list)))
            return signals

    async def save_to_database(self, model, symbol, data):
        if model == "Market":
            market, created = await sync_to_async(Market.objects.get_or_create)(
                symbol=symbol, 
                defaults={
                    'open': data["open"], 
                    'high': data["high"], 
                    'low': data["low"], 
                    'close': data["close"], 
                    'volume': data["volume"]
                }
            )
            if created:
                await sync_to_async(market.save)()
            return market

        elif model == "Indicator":
            indicator, created = await sync_to_async(IndicatorModel.objects.get_or_create)(
                market=symbol, 
                defaults={
                    'rsi': data["rsi"], 
                    'macd': data["macd"], 
                    'bollinger_bands': data["bollinger_bands"], 
                    'moving_average': data["moving_average"]
                }
            )
            if created:
                await sync_to_async(indicator.save)()
            return indicator

        elif model == "Signal":
            signal, created = await sync_to_async(Signal.objects.get_or_create)(
                symbol=symbol, 
                price = data["price"],
                type = data["type"], 
                strength = data["strength"],
            )
            if created:
                await sync_to_async(signal.save)()
            return signal

    def signal_toString(self, signal):
        if signal is None:
            return None
        return f"Symbol: {signal['symbol']}, Price: {signal['price']}, Type: {signal['type']}, Strength: {signal['strength']}"
