import asyncio
from bot import TradingBot
from config import Config
from datetime import datetime, timedelta
import pytz

# Initialize bot with credentials from config
bot = TradingBot(Config.MT5_LOGIN, Config.MT5_PASSWORD, Config.MT5_SERVER)

async def main():
    # Attempt to connect the bot
    if not bot.connect():
        print("Failed to initialize trading bot.")
        raise Exception("Bot not initialized")
    i = 1
    
    while True:
        try:
            # Define timezone and calculate time range for data fetching
            timezone = pytz.timezone("Etc/UTC")
            end_time = datetime.now(tz=timezone)
            start_time = end_time - timedelta(minutes=2040)  # 34 hours ago
            
            # Fetch data for multiple markets
            
            data_coroutines = await bot.fetch_multiple_data(Config.MARKETS_LIST, Config.TIME_FRAMES[0], start_time, end_time)
            #data_list = await asyncio.gather(*i)
            
            # Generate signals for each market
            
            signals = await bot.process_multiple_signals(data_coroutines, Config.MARKETS_LIST)
            for signal in signals:
                if signal is None:
                    continue
                print(bot.signal_toString(signal))  # Print each signal
            print("========================================================", i)
            i = i + 1
            #print("========================================================")

            # Wait for 60 seconds before fetching new data
            await asyncio.sleep(60)
        except Exception as e:
            print("Error:", e)
            break


if __name__ == "__main__":
    try:
        asyncio.run(main())  # Run the main function using asyncio
    except KeyboardInterrupt:
        print("Shutting down bot...")
        bot.disconnect()  # Disconnect the bot on exit
        print("Bot disconnected.")
        pass
