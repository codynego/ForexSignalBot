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
    
    async def fetch_all_timeframes(self, market, start, end):
        if not self.connected:
            raise Exception("Not connected to MT5")
        data_tasks = [self.fetch_data(market, timeframe, start, end) for timeframe in Config.TIME_FRAMES]
        return await asyncio.gather(*data_tasks)
    
    import asyncio

    async def fetch_data_for_multiple_markets(self, markets, start, end):
        """Fetches data for multiple markets and timeframes concurrently.

        Args:
            markets: A list of market symbols.
            start: Start date for data retrieval.
            end: End date for data retrieval.
            timeframes: A list of timeframes.

        Returns:
            A dictionary of dataframes, where keys are market symbols and values are lists of dataframes (one for each timeframe).
        """

        data_tasks = [asyncio.create_task(self.fetch_all_timeframes(market, start, end)) for market in markets]
        return await asyncio.gather(*data_tasks)
            
    def apply_strategy(self, data, strategy):
        indicator = Indicator(data.head(14))
        calc = indicator.rsi()
        last_indicator_value = calc.tail(1).values[0]
        print(last_indicator_value)

    async def generate_signal(self, data, strategy="rsistrategy", symbol=None):
        for time_frame_data in data:
                if time_frame_data is None:
                    return None
                # else:
                #     #last_data = time_frame_data.tail(1)["close"].values[0]
        signal = {"symbol": symbol, "price": None, "type": None, "strength": None}

        if strategy == "rsistrategy":
            # stra = Strategy.rsiStrategy(data)
            stra = await Strategy.process_multiple_timeframes(data)
            if stra == 1:
                signal["type"] = "BUY"
            elif stra == -1:
                signal["type"] = "SELL"
            elif stra == 0:
                signal["type"] = "HOLD"
            else:
                return None

            # Check for duplicate signals
            # signal_key = (symbol, signal["type"])
            # if signal_key in self.signals_cache:
            #     return None  # Duplicate found

            # Save the signal to the database
            saved_signal = await self.save_to_database("Signal", symbol, signal)
                
            # Update cache
            # self.signals_cache[signal_key] = saved_signal
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
    
    def open_trade(self, signal):
        symbol = signal["symbol"]
        lot_size = 1.0

        if signal["type"] == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
        else:
            order_type = mt5.ORDER_TYPE_SELL
        
        #print(mt5.symbol_info_tick(symbol)._asdict()['ask'])
        price = signal["price"]
        if price is None:
            print("couldnt retrieve", symbol)
            self.disconnect()
        
        stop_loss = price - 0.0100
        take_profit = price + 0.0150

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "price": price,
            # "sl": stop_loss,
            # "tp": take_profit,  # Add take_profit to request
        }
        # print(mt5.positions_get())
        # print(mt5.account_info())
        result = mt5.order_send(request)
        #print("result",result)

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Order failed, retcode={result.retcode}, error_desc={result.retcode}")
        else:
            print(f"{signal["type"]} Order successfully placed for {symbol}!")
        
        #print(self.signals_cache)



    def close_position(self, signal=None):
        """
        Closes an open position based on the given signal.

        Args:
            signal (dict, optional): A dictionary containing signal information. Defaults to None.
        """

        positions = mt5.positions_get() if signal is None else mt5.positions_get(symbol=signal["symbol"])
        print(mt5.positions_total())
        if len(positions) == 0:
            print("No open positions")
        
        #print("all positions", positions)
        for pos in positions:
            # Implement your position selection logic here based on signal or other criteria
            # For example:
            # if not meets_closing_criteria(pos, signal):
            #     continue
            # print(pos)
            if pos is None:
                print("None")
                break
            #print("positions",mt5.symbol_info_tick(pos.symbol))
            point = mt5.symbol_info_tick(pos.symbol)._asdict()['ask'] if pos.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(pos.symbol)._asdict()['bid']
            deviation = 20
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": mt5.ORDER_TYPE_BUY if pos.type == mt5.ORDER_TYPE_SELL else mt5.ORDER_TYPE_SELL,
                "price": point,
                "deviation": deviation,
                "magic": 234000,
                "position": pos.ticket,
                "comment": "Python script close",
                "type_time": mt5.ORDER_TIME_GTC,
           
            }

            result = mt5.order_send(request)
            #print(result)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"order_send failed, retcode =", result.retcode)
            else:
                # print(mt5.positions_total())
                print(f"Close order successfully placed: {result.order}, profit = {pos.profit}")



    def process_close_trade(self, signal):
        #print(self.signals_cache)
        type = "SELL" if signal["type"] == "BUY" else "BUY"
        positions = mt5.positions_get(symbol=signal["symbol"])
        #print(positions)    
        sig_key = (signal['symbol'], signal["type"])
        for pos in positions:
            if pos._asdict()['type'] == 1 and signal['type'] == "BUY" and pos._asdict()['symbol'] == signal['symbol']:
                self.close_position(signal=signal)
                del self.signals_cache[sig_key]
            elif pos._asdict()['type'] == 1 and signal['type'] == "BUY" and pos._asdict()['symbol'] == signal['symbol']:
                self.close_position(signal=signal)
                del self.signals_cache[sig_key]
        

        #print("postions", mt5.positions_total())

        # if signal_key in self.signals_cache:
        #     self.close_position(signal=signal)
        # return None