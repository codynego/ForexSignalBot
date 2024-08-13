from utils.indicators import Indicator

class RsDetector:
    def __init__(self, df):
        self.df = df


    def pivotCalc(self, i, j):
        mov = 1
        currentData = self.df.iloc[-1].start()
        prevData = self.df.iloc[-2].end()
        if currentData[mov-1] > prevData[mov-2]:
            return 0
        else:
            return 1

    def is_resistance(self, i, j):
        if self.pivotCalc(1, 0):
            if -+9+

    def is_support(self, df, i, j):
        pass


    
