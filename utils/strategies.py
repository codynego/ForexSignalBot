class Strategy:

    @classmethod
    def rsiStrategy(cls, rsi):
        # RSI strategy

        if rsi > 30:
            return True
        return False