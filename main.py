from config import Config
from utils.data_fetch import fetch_data
from utils.exceptions import InitializationError
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from utils.indicators import Indicator
import pytz


def main():
    bot = Config.bot_model()
    initialize = bot.connect()
    print(initialize)
    if not initialize:
        bot.disconnect()
        print ("bot not initialized")
        raise InitializationError("bot not initialized", 500)
    while True:
        timezone = pytz.timezone("Etc/UTC")
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=2040)
        data = bot.fetch_data("Boom 1000 Index", mt5.TIMEFRAME_M1, start_time, end_time)
        bot.apply_strategy(data)
        #print(data.head(30))
        #print(mt5.symbols_get())
        break
        


if __name__ == "__main__":
    main()