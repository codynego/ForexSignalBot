
from dotenv import load_dotenv
import os
import MetaTrader5 as mt5

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

    MARKETS_LIST = ["Boom 1000 Index", "Crash 1000 Index", "Boom 500 Index", "Crash 500 Index"]
    TIME_FRAMES = [mt5.TIMEFRAME_M15, mt5.TIMEFRAME_M30, mt5.TIMEFRAME_H1]