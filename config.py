from bot import TradingBot
from dotenv import load_dotenv
import os

load_dotenv()

class Config:
# API SETTINGS
    API_KEY = "APIKEY"
    API_SECRET = ""


    #MT5 LOGINS
    MT5_LOGIN = int(os.environ['MT5_LOGIN'])
    MT5_PASSWORD = os.environ['MT5_PASSWORD']
    MT5_SERVER = os.environ['MT5_SERVER']
    MT5_PATH = ""

    @classmethod
    def bot_model(cls):
        bot = TradingBot(cls.MT5_LOGIN, cls.MT5_PASSWORD, cls.MT5_SERVER)
        return bot