import asyncio
from bot import TradingBot
from config import Config
from datetime import datetime, timedelta
import pytz
import MetaTrader5 as mt5
# Initialize bot with credentials from config
bot = TradingBot(Config.MT5_LOGIN, Config.MT5_PASSWORD, Config.MT5_SERVER)

async def main():
    # Attempt to connect the bot
    if not bot.connect():
        print("Failed to initialize trading bot.")
        raise Exception("Bot not initialized")
    i = 1
    print("account balance", mt5.account_info().equity, ": ", "profit", mt5.account_info().profit)
    #print(mt5.account_info())
    while True:
        # try:
            # Define timezone and calculate time range for data fetching
            timezone = pytz.timezone("Etc/UTC")
            end_time = datetime.now(tz=timezone)
            start_time = end_time - timedelta(minutes=3600)  # 34 hours ago
            
            # Fetch data for multiple markets
            
            #data_coroutines = await bot.fetch_multiple_data(Config.MARKETS_LIST, Config.TIME_FRAMES[0], start_time, end_time)
            #data_list = await asyncio.gather(*i)
            #print(data_coroutines)
            data_coroutines = await bot.fetch_data_for_multiple_markets(Config.MARKETS_LIST, start_time, end_time)
            # Generate signals for each market
            
            signals = await bot.process_multiple_signals(data_coroutines, Config.MARKETS_LIST)
            # print(signals)
            bot.close_position()
            for signal in signals:
                #print(signal)
                if signal is None:
                    continue
                bot.open_trade(signal)
                bot.process_close_trade(signal)
                #pint("postions", mt5.positions_total())
                print(bot.signal_toString(signal), i, "seconds")  # Print each signal
            #print("========================================================", i)
            i = i + 1
            #print("========================================================")


            # Wait for 60 seconds before fetching new data
            await asyncio.sleep(60)
        # except Exception as e:
        #     print("Error:", e)
        #     break


if __name__ == "__main__":
    try:
        asyncio.run(main())  # Run the main function using asyncio
        
    except KeyboardInterrupt:
        print("account balance", mt5.account_info().equity, ": ", "profit", mt5.account_info().profit)
        print("Shutting down bot...")
        bot.disconnect()  # Disconnect the bot on exit
        print("Bot disconnected.")
        pass
