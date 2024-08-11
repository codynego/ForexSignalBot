import asyncio
from bot import TradingBot
from config import Config
from datetime import datetime, timedelta
import pytz


bot = TradingBot(Config.MT5_LOGIN, Config.MT5_PASSWORD, Config.MT5_SERVER)

async def main():
    if not bot.connect():
        print("Failed to initialize trading bot.")
        raise Exception("Bot not initialized")
    
    
    while True:
        try:
            timezone = pytz.timezone("Etc/UTC")
            end_time = datetime.now(tz=timezone)
            start_time = end_time - timedelta(minutes=2040)
            data = await bot.fetch_data("Boom 1000 Index", Config.TIME_FRAMES[0], start_time, end_time)
            signal = await bot.generate_signal(data=data.head(14), symbol="Boom 1000 Index")
            print(bot.signal_toString(signal))
            await asyncio.sleep(60)
        except Exception as e:
            print("something went wrong: ")
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down bot...")
        bot.disconnect()
        print("Bot disconnected.")
        pass
