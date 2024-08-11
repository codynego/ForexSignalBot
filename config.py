
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

    MARKETS_LIST = ["BOOM 1000 INDEX", "CRASH 1000 INDEX", "VOL 100 INDEX", "VOL 75 INDEX"]
    TIME_FRAMES = [mt5.TIMEFRAME_M1, mt5.TIMEFRAME_M5, mt5.TIMEFRAME_H1, mt5.TIMEFRAME_H4, mt5.TIMEFRAME_D1]