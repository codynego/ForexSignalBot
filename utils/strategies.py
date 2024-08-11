from utils.indicators import Indicator

class Strategy:
    @classmethod
    def rsiStrategy(cls, data):
        indicator = Indicator(data)
        rsi = indicator.rsi()
        rsi_value = rsi.tail(1).values[0]
        if rsi_value > 30:
            return 1
        elif rsi_value < 30:
            return -1
        return 0
