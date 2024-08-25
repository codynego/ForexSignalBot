import asyncio
from bot import TradingBot
from config import Config
from datetime import datetime, timedelta
import pytz
import MetaTrader5 as mt5
import threading
# Initialize bot with credentials from config
bot = TradingBot(Config.MT5_LOGIN, Config.MT5_PASSWORD, Config.MT5_SERVER)

async def main():
    # Attempt to connect the bot
    connect = bot.connect()
    try_count = 0
    while not connect:
        if try_count >= Config.CONNECTION_TIMEOUT:
            print("failed to connect!")
            raise Exception("Bot not initialized")

        print("Failed to initialize trading bot.")
        print("retrying in 3 seconds")
        await asyncio.sleep(3)

        print("trying to reconnect...")
        connect = bot.connect()
        
        # 
        
    print("bot connected")
    i = 1
    #print("account balance", mt5.account_info().equity, ": ", "profit", mt5.account_info().profit)
    #print(mt5.account_info())
    while True:
        # try:
            # Define timezone and calculate time range for data fetching
            print("fetching data...")
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
            #bot.close_position()
            catch_spikes = True
            all_tasks = []
            for signal in signals:
                #print(signal)
                if signal is None:
                    continue
                if signal["type"] != "HOLD":
                    print(bot.signal_toString(signal), i, "seconds")
                # tasks = asyncio.create_task(bot.open_trade(signal, catch_spikes=catch_spikes))
                # all_tasks.append(tasks)

                await bot.open_trade(signal, catch_spikes=True)
                bot.process_close_trade(signal)
                #pint("postions", mt5.positions_total())
                  # Print each signal
            await asyncio.gather(*all_tasks)
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
        print("account balance", mt5.account_info().equity, ": ", "profit", mt5.account_info().profit) # type: ignore
        print("Shutting down bot...")
        bot.disconnect()  # Disconnect the bot on exit
        print("Bot disconnected.")