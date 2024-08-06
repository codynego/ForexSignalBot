from django.apps import AppConfig
import threading
from main import main as background_task


class TraderbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'traderbot'


    def ready(self):
        thread = threading.Thread(target=background_task)
        thread.daemon = True
        thread.start()
