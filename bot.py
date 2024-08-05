# bot.py

import MetaTrader5 as mt5
import numpy as np
import pandas as pd
from utils.indicators import Indicator

class TradingBot:
    def __init__(self, login, password, server):
        self.login = login
        self.password = password
        self.server = server
        self.connected = False
    
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

    def fetch_data(self, symbol, timeframe, start, end):
        if not self.connected:
            raise Exception("Not connected to MT5")
        rates = mt5.copy_rates_range(symbol, timeframe, start, end)
        df = pd.DataFrame(rates)
        return df

    def apply_strategy(self, data):
        indicator = Indicator(data.head(14))
        calc = indicator.rsi()
        last_indicator_value = calc.tail(1).values[0]
        print(calc)
        print(last_indicator_value)
