from config import Config
from utils.data_fetch import fetch_data
from utils.exceptions import InitializationError
import MetaTrader5 as mt5
from datetime import datetime, timedelta


def main():
    bot = Config.bot_model()
    initialize = bot.connect()
    print(initialize)
    if not initialize:
        bot.disconnect()
        print ("bot not initialized")
        raise InitializationError("bot not initialized", 500)
    while True:
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=1440)
        data = bot.fetch_data("EURUSD", mt5.TIMEFRAME_M1, start_time, end_time)
        print(data.head(5))
        break
        


if __name__ == "__main__":
    main()